import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import timedelta
from pathlib import Path

import requests

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from we_rss.models import (
    MemberFeedSubscription,
    MemberFeedTagRelation,
    WechatArticle,
    WechatCredential,
    WechatFeed,
    WechatSyncTask,
)
from we_rss.services.task_service import TaskService, dispatch_we_rss_task
from we_rss.services.wechat_gateway import (
    build_wechat_session,
    extract_source_id_from_url,
    get_publish_page_records,
    load_credential_cookies,
    normalize_wechat_article_url,
    parse_publish_page_articles,
    parse_wechat_article_html,
)

logger = logging.getLogger(__name__)


class WechatFeedGateway:
    DEFAULT_TIMEOUT = 120
    DEFAULT_PUBLISH_TIMEOUT = 30

    def __init__(
        self,
        *,
        session_factory=None,
        page_size=5,
        max_pages=None,
        timeout=DEFAULT_TIMEOUT,
        publish_timeout=DEFAULT_PUBLISH_TIMEOUT,
        sleep_seconds=1.5,
        sleep_func=None,
    ):
        self.session_factory = session_factory or requests.Session
        self.page_size = page_size
        self.max_pages = max_pages
        self.timeout = timeout
        self.publish_timeout = publish_timeout
        self.sleep_seconds = sleep_seconds
        self.sleep_func = sleep_func or time.sleep

    def _resolve_fakeid(self, feed):
        return feed.faker_id or feed.source_id or ""

    def _throttle(self):
        if self.sleep_seconds and self.sleep_seconds > 0:
            self.sleep_func(self.sleep_seconds)

    def _raise_if_deadline_exceeded(self, deadline_at):
        if deadline_at is None:
            return
        if timezone.now() >= deadline_at:
            raise TimeoutError("Feed sync batch timed out.")

    def _build_publish_params(self, *, feed, credential, begin):
        return {
            "sub": "list",
            "sub_action": "list_ex",
            "begin": begin,
            "count": self.page_size,
            "fakeid": self._resolve_fakeid(feed),
            "token": credential.token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": 1,
        }

    def _raise_for_non_json_publish_response(self, response):
        body = str(getattr(response, "text", "") or "").strip()
        lowered_body = body.lower()

        if "frequency control" in lowered_body or "too frequent" in lowered_body:
            raise ValidationError(
                "WeChat feed sync returned a non-JSON response, likely due to frequency control."
            )
        if "login" in lowered_body or "二维码" in body or "扫码" in body:
            raise ValidationError(
                "WeChat feed sync returned a non-JSON response, likely because the session expired."
            )
        if "环境异常" in body:
            raise ValidationError(
                "WeChat feed sync returned a non-JSON response because the environment was flagged as abnormal."
            )
        if not body:
            raise ValidationError(
                "WeChat feed sync returned an empty non-JSON response, likely due to frequency control or an expired session."
            )
        raise ValidationError(
            "WeChat feed sync returned a non-JSON response, likely due to frequency control or an expired session."
        )

    def _parse_publish_response(self, response):
        try:
            return response.json()
        except ValueError:
            self._raise_for_non_json_publish_response(response)

    def _raise_for_publish_payload_error(self, payload, *, begin):
        base_resp = payload.get("base_resp") or {}
        ret = int(base_resp.get("ret") or 0)
        if ret == 0:
            return

        err_msg = str(base_resp.get("err_msg") or "").strip()
        if ret == 200013:
            raise ValidationError(
                f"WeChat frequency control triggered while loading feed list at begin={begin}."
            )
        if ret == 200003:
            raise ValidationError(
                f"WeChat session invalid or expired while loading feed list at begin={begin}."
            )
        if err_msg:
            raise ValidationError(f"WeChat feed sync failed: {err_msg} ({ret}).")
        raise ValidationError(f"WeChat feed sync failed with ret={ret} at begin={begin}.")

    def _fetch_publish_payload(self, *, session, feed, credential, begin):
        response = session.get(
            "https://mp.weixin.qq.com/cgi-bin/appmsgpublish",
            params=self._build_publish_params(feed=feed, credential=credential, begin=begin),
            timeout=self.publish_timeout,
        )
        response.raise_for_status()
        payload = self._parse_publish_response(response)
        self._raise_for_publish_payload_error(payload, begin=begin)
        return payload

    def _extract_publish_page_data(self, payload):
        publish_records = get_publish_page_records(payload)
        page_articles = parse_publish_page_articles(payload)
        return publish_records, page_articles

    def _fetch_publish_page_data(self, *, session, feed, credential, begin, max_attempts=3):
        last_exc = None
        for attempt in range(max_attempts):
            try:
                payload = self._fetch_publish_payload(
                    session=session,
                    feed=feed,
                    credential=credential,
                    begin=begin,
                )
                publish_records, page_articles = self._extract_publish_page_data(payload)
                return payload, publish_records, page_articles
            except (requests.RequestException, TypeError, ValueError, json.JSONDecodeError) as exc:
                last_exc = exc
                if attempt == max_attempts - 1:
                    raise
                self._throttle()
        raise last_exc

    def _log_publish_page(self, *, feed, begin, publish_records, page_articles):
        page_payload = {
            "feed_id": getattr(feed, "id", None),
            "feed_name": getattr(feed, "mp_name", ""),
            "begin": begin,
            "publish_record_count": len(publish_records or []),
            "article_count": len(page_articles or []),
            "articles": [
                {
                    "source_id": str(item.get("aid") or ""),
                    "title": str(item.get("title") or ""),
                    "url": str(item.get("link") or ""),
                    "create_time": item.get("create_time"),
                    "update_time": item.get("update_time"),
                    "article_type": item.get("article_type"),
                }
                for item in (page_articles or [])
            ],
        }
        message = f"We RSS feed sync page fetched: {json.dumps(page_payload, ensure_ascii=False, default=str)}"
        logger.info(message)
        logs_dir = Path(getattr(settings, "LOGS_DIR", Path(settings.BASE_DIR) / "logs"))
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / "we_rss_feed_sync_pages.log"
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(f"{message}\n")
        try:
            print(message)
        except (OSError, UnicodeEncodeError) as exc:
            logger.warning(
                "We RSS feed sync page stdout print skipped: %s",
                exc,
                extra={
                    "feed_id": getattr(feed, "id", None),
                    "begin": begin,
                },
            )

    def _resolve_item_publish_time(self, item, parsed_article):
        parsed_publish_time = parsed_article.get("publish_time")
        if parsed_publish_time is not None:
            return parsed_publish_time

        raw_publish_time = item.get("update_time")
        if raw_publish_time in (None, ""):
            raw_publish_time = item.get("create_time")

        if raw_publish_time in (None, ""):
            return None

        return timezone.datetime.fromtimestamp(
            raw_publish_time,
            tz=timezone.get_current_timezone(),
        )

    def search_feeds(self, keyword, credential):
        session = build_wechat_session(self.session_factory)
        load_credential_cookies(session, credential.cookie)
        response = session.get(
            "https://mp.weixin.qq.com/cgi-bin/searchbiz",
            params={
                "action": "search_biz",
                "begin": 0,
                "count": 10,
                "query": keyword,
                "token": credential.token,
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if (payload.get("base_resp") or {}).get("ret") != 0:
            raise ValidationError("WeChat feed search failed.")
        return [
            {
                "source_id": item.get("fakeid", ""),
                "faker_id": item.get("fakeid", ""),
                "biz": item.get("biz", ""),
                "mp_name": item.get("nickname") or item.get("username") or "",
                "mp_cover": item.get("round_head_img") or item.get("headimgurl") or "",
                "mp_intro": item.get("signature") or item.get("alias") or "",
            }
            for item in payload.get("list") or []
        ]

    def collect_feed_batch(self, feed, credential, *, begin=0, batch_size=20, deadline_at=None):
        session = build_wechat_session(self.session_factory)
        load_credential_cookies(session, credential.cookie)
        articles = []
        seen_urls = set()
        feed_payload = {}
        sync_errors = []
        current_begin = begin
        has_requested_article_detail = False

        while self.max_pages is None or current_begin < self.max_pages * self.page_size:
            self._raise_if_deadline_exceeded(deadline_at)
            if current_begin > begin:
                self._throttle()
            payload, publish_records, page_articles = self._fetch_publish_page_data(
                session=session,
                feed=feed,
                credential=credential,
                begin=current_begin,
            )
            if not publish_records:
                break
            self._log_publish_page(
                feed=feed,
                begin=current_begin,
                publish_records=publish_records,
                page_articles=page_articles,
            )
            current_begin += len(publish_records)

            for item in page_articles:
                article_url = item.get("link", "")
                stable_article_url = normalize_wechat_article_url(article_url) or article_url
                if stable_article_url and stable_article_url in seen_urls:
                    continue

                source_id = str(item.get("aid") or "")
                parsed_article = {}
                parse_article_url = stable_article_url
                try:
                    self._raise_if_deadline_exceeded(deadline_at)
                    if has_requested_article_detail:
                        self._throttle()
                    has_requested_article_detail = True
                    article_response = session.get(article_url, timeout=self.timeout)
                    article_response.raise_for_status()
                    parse_article_url = (
                        normalize_wechat_article_url(article_response.url or stable_article_url) or stable_article_url
                    )
                    parsed_article = parse_wechat_article_html(article_response.text, parse_article_url)
                    if not feed_payload:
                        feed_payload = {
                            "biz": parsed_article.get("biz", ""),
                            "mp_name": parsed_article.get("mp_name") or feed.mp_name,
                            "mp_cover": parsed_article.get("mp_cover") or feed.mp_cover,
                        }
                except Exception as exc:
                    sync_errors.append(
                        {
                            "source_id": source_id or "",
                            "url": stable_article_url,
                            "error": str(exc),
                        }
                    )
                    if not feed_payload:
                        feed_payload = {
                            "biz": "",
                            "mp_name": feed.mp_name,
                            "mp_cover": feed.mp_cover,
                        }

                articles.append(
                    {
                        "source_id": source_id or parsed_article.get("source_id") or "",
                        "article_type": item.get("article_type")
                        or parsed_article.get("article_type", WechatArticle.ArticleType.NEWS),
                        "title": parsed_article.get("title") or item.get("title") or "",
                        "description": parsed_article.get("description") or item.get("digest") or "",
                        "content": parsed_article.get("content", ""),
                        "url": parse_article_url or stable_article_url,
                        "pic_url": parsed_article.get("pic_url") or item.get("cover") or "",
                        "publish_time": self._resolve_item_publish_time(item, parsed_article),
                        "status": parsed_article.get("status", "active"),
                        "read_num": parsed_article.get("read_num", 0),
                        "like_num": parsed_article.get("like_num", 0),
                        "old_like_num": parsed_article.get("old_like_num", 0),
                        "share_num": parsed_article.get("share_num", 0),
                        "collect_num": parsed_article.get("collect_num", 0),
                        "comment_count": parsed_article.get("comment_count", 0),
                        "comment_reply_count": parsed_article.get("comment_reply_count", 0),
                        "comment_total_count": parsed_article.get("comment_total_count", 0),
                        "biz": parsed_article.get("biz", ""),
                    }
                )
                if stable_article_url:
                    seen_urls.add(stable_article_url)
                if len(articles) >= batch_size:
                    return {
                        "articles": articles,
                        "feed_payload": feed_payload,
                        "failed_articles": [],
                        "has_more": True,
                        "next_begin": current_begin,
                        "detail_success_count": len(articles) - len(sync_errors),
                        "detail_failed_count": len(sync_errors),
                        "errors": sync_errors,
                    }

        return {
            "articles": articles,
            "feed_payload": feed_payload,
            "failed_articles": [],
            "has_more": False,
            "next_begin": current_begin,
            "detail_success_count": len(articles) - len(sync_errors),
            "detail_failed_count": len(sync_errors),
            "errors": sync_errors,
        }

    def sync_feed(self, feed, credential):
        session = build_wechat_session(self.session_factory)
        load_credential_cookies(session, credential.cookie)
        articles = []
        seen_urls = set()
        feed_payload = {}
        sync_errors = []
        page_index = 0
        has_requested_article_detail = False
        while self.max_pages is None or page_index < self.max_pages:
            if page_index > 0:
                self._throttle()
            payload, publish_records, page_articles = self._fetch_publish_page_data(
                session=session,
                feed=feed,
                credential=credential,
                begin=page_index * self.page_size,
            )
            if not page_articles:
                break
            self._log_publish_page(
                feed=feed,
                begin=page_index * self.page_size,
                publish_records=publish_records,
                page_articles=page_articles,
            )

            for item in page_articles:
                article_url = item.get("link", "")
                stable_article_url = normalize_wechat_article_url(article_url) or article_url
                if stable_article_url and stable_article_url in seen_urls:
                    continue
                source_id = str(item.get("aid") or "")
                parsed_article = {}
                parse_article_url = stable_article_url
                try:
                    if has_requested_article_detail:
                        self._throttle()
                    has_requested_article_detail = True
                    article_response = session.get(article_url, timeout=self.timeout)
                    article_response.raise_for_status()
                    parse_article_url = normalize_wechat_article_url(article_response.url or stable_article_url) or stable_article_url
                    parsed_article = parse_wechat_article_html(article_response.text, parse_article_url)
                    if not feed_payload:
                        feed_payload = {
                            "biz": parsed_article.get("biz", ""),
                            "mp_name": parsed_article.get("mp_name") or feed.mp_name,
                            "mp_cover": parsed_article.get("mp_cover") or feed.mp_cover,
                        }
                except Exception as exc:
                    sync_errors.append(
                        {
                            "source_id": source_id or "",
                            "url": stable_article_url,
                            "error": str(exc),
                        }
                    )
                    parsed_article = {}
                articles.append(
                    {
                        "source_id": source_id or parsed_article.get("source_id") or "",
                        "article_type": item.get("article_type")
                        or parsed_article.get("article_type", WechatArticle.ArticleType.NEWS),
                        "title": parsed_article.get("title") or item.get("title") or "",
                        "description": parsed_article.get("description") or item.get("digest") or "",
                        "content": parsed_article.get("content", ""),
                        "url": parse_article_url or stable_article_url,
                        "pic_url": parsed_article.get("pic_url") or item.get("cover") or "",
                        "publish_time": self._resolve_item_publish_time(item, parsed_article),
                        "status": parsed_article.get("status", "active"),
                        "read_num": parsed_article.get("read_num", 0),
                        "like_num": parsed_article.get("like_num", 0),
                        "old_like_num": parsed_article.get("old_like_num", 0),
                        "share_num": parsed_article.get("share_num", 0),
                        "collect_num": parsed_article.get("collect_num", 0),
                        "comment_count": parsed_article.get("comment_count", 0),
                        "comment_reply_count": parsed_article.get("comment_reply_count", 0),
                        "comment_total_count": parsed_article.get("comment_total_count", 0),
                        "biz": parsed_article.get("biz", ""),
                    }
                )
                if stable_article_url:
                    seen_urls.add(stable_article_url)
            page_index += 1

        return {
            "message": "Feed sync complete",
            "articles": articles,
            "feed_payload": feed_payload,
            "result_payload": {
                "fetched_count": len(articles),
                "detail_success_count": len(articles) - len(sync_errors),
                "detail_failed_count": len(sync_errors),
                "errors": sync_errors,
            },
        }

    def resolve_article_url(self, article, credential):
        session = build_wechat_session(self.session_factory)
        load_credential_cookies(session, credential.cookie)
        target_source_id = str(getattr(article, "source_id", "") or "").strip()
        target_title = str(getattr(article, "title", "") or "").strip()
        page_index = 0

        while self.max_pages is None or page_index < self.max_pages:
            if page_index > 0:
                self._throttle()
            payload, publish_records, page_articles = self._fetch_publish_page_data(
                session=session,
                feed=article.feed,
                credential=credential,
                begin=page_index * self.page_size,
            )
            if not page_articles:
                break
            self._log_publish_page(
                feed=article.feed,
                begin=page_index * self.page_size,
                publish_records=publish_records,
                page_articles=page_articles,
            )

            for item in page_articles:
                candidate_url = normalize_wechat_article_url(item.get("link")) or str(item.get("link") or "").strip()
                if not candidate_url:
                    continue

                candidate_source_id = str(item.get("aid") or "").strip()
                candidate_title = str(item.get("title") or "").strip()

                if target_source_id and candidate_source_id == target_source_id:
                    return candidate_url
                if not target_source_id and target_title and candidate_title == target_title:
                    return candidate_url

            page_index += 1

        return ""


class FeedService:
    SYNC_SCOPE_FULL = "full"
    SYNC_SCOPE_LATEST = "latest"
    SYNC_SCOPE_WINDOW = "window"
    BATCH_SIZE = 20
    POLL_AFTER_SECONDS = 5
    BATCH_TIMEOUT_SECONDS = 9000
    RUN_TIMEOUT_SECONDS = 9000
    STALE_AFTER_SECONDS = 9300
    BATCH_STREAM_HEARTBEAT_INTERVAL_SECONDS = 12

    @staticmethod
    def _find_existing_feed(*, tenant, data):
        for field in ("source_id", "faker_id", "biz"):
            value = str(data.get(field) or "").strip()
            if value:
                existing = WechatFeed.objects.filter(tenant=tenant, **{field: value}).first()
                if existing is not None:
                    return existing
        return None

    @staticmethod
    def _apply_subscription_feed_data(*, feed, member, data):
        changed = False
        for field in ("source_id", "faker_id", "biz", "mp_name", "mp_cover", "mp_intro"):
            value = str(data.get(field) or "").strip()
            if value and getattr(feed, field) != value:
                setattr(feed, field, value)
                changed = True

        if changed:
            feed.updated_by = member
            feed.save()
        return feed

    @staticmethod
    def get_active_credential(*, tenant, credential_id=None):
        queryset = WechatCredential.objects.filter(tenant=tenant, status=WechatCredential.Status.ACTIVE)
        if credential_id is not None:
            return queryset.filter(pk=credential_id).first()
        return queryset.filter(is_default=True).first() or queryset.first()

    @staticmethod
    def create_feed(*, tenant, created_by, data):
        credential = None
        credential_id = data.pop("credential_id", None)
        if credential_id is not None:
            credential = WechatCredential.objects.filter(tenant=tenant, pk=credential_id).first()
        return WechatFeed.objects.create(
            tenant=tenant,
            credential=credential,
            created_by=created_by,
            updated_by=created_by,
            **data,
        )

    @staticmethod
    def update_feed(*, feed, updated_by, data):
        credential_id = data.pop("credential_id", None)
        if credential_id is not None:
            feed.credential = WechatCredential.objects.filter(tenant=feed.tenant, pk=credential_id).first()
        for field, value in data.items():
            setattr(feed, field, value)
        feed.updated_by = updated_by
        feed.save()
        return feed

    @staticmethod
    def search_feeds(*, tenant, keyword, gateway, credential_id=None):
        credential = FeedService.get_active_credential(tenant=tenant, credential_id=credential_id)
        if credential is None:
            raise ValidationError("Active credential required.")
        return gateway.search_feeds(keyword, credential)

    @staticmethod
    def subscribe_member(*, tenant, member, data):
        feed = FeedService._find_existing_feed(tenant=tenant, data=data)
        if feed is None:
            feed = WechatFeed.objects.create(
                tenant=tenant,
                source_id=str(data.get("source_id") or "").strip(),
                faker_id=str(data.get("faker_id") or "").strip(),
                biz=str(data.get("biz") or "").strip(),
                mp_name=str(data.get("mp_name") or "").strip(),
                mp_cover=str(data.get("mp_cover") or "").strip(),
                mp_intro=str(data.get("mp_intro") or "").strip(),
                created_by=member,
                updated_by=member,
            )
        else:
            feed = FeedService._apply_subscription_feed_data(feed=feed, member=member, data=data)

        MemberFeedSubscription.objects.get_or_create(
            tenant=tenant,
            member=member,
            feed=feed,
        )
        feed.is_subscribed = True
        return feed

    @staticmethod
    def unsubscribe_member(*, feed, member):
        MemberFeedTagRelation.objects.filter(
            tenant=feed.tenant,
            member=member,
            feed=feed,
        ).delete()
        MemberFeedSubscription.objects.filter(
            tenant=feed.tenant,
            member=member,
            feed=feed,
        ).delete()
        feed.is_subscribed = False
        return feed

    @staticmethod
    def clear_articles(*, feed):
        deleted_count, _detail = WechatArticle.original_objects.filter(
            tenant=feed.tenant,
            feed=feed,
        ).delete()
        return {
            "feed_id": feed.id,
            "deleted_count": deleted_count,
        }

    @staticmethod
    def refresh_feed_content(*, feed, created_by):
        task_key = f"feed_content_refresh:{feed.id}"
        active_task = TaskService.find_active_task(
            tenant=feed.tenant,
            task_type=WechatSyncTask.TaskType.FEED_CONTENT_REFRESH,
            task_key=task_key,
        )
        if active_task is not None:
            return active_task

        article_ids = list(
            WechatArticle.objects.filter(
                tenant=feed.tenant,
                feed=feed,
            )
            .order_by(*WechatArticle._meta.ordering)
            .values_list("id", flat=True)
        )
        task = TaskService.create_task(
            tenant=feed.tenant,
            task_type=WechatSyncTask.TaskType.FEED_CONTENT_REFRESH,
            created_by=created_by,
            target_type="feed",
            target_id=feed.id,
            task_key=task_key,
            message="Feed content refresh task created.",
            request_payload={
                "feed_id": feed.id,
                "article_ids": article_ids,
            },
        )
        from we_rss.tasks import run_feed_content_refresh_task

        dispatch_we_rss_task(run_feed_content_refresh_task, task.id)
        return task

    @staticmethod
    def delete_feed(*, feed):
        with transaction.atomic():
            WechatArticle.original_objects.filter(
                tenant=feed.tenant,
                feed=feed,
            ).delete()
            feed.delete()

    @staticmethod
    def _build_parent_run_payload(
        *,
        feed_id,
        current_batch_task_id=None,
        sync_scope=SYNC_SCOPE_FULL,
        window_days=None,
        refresh_markdown=False,
    ):
        return {
            "run_status": WechatSyncTask.Status.RUNNING,
            "feed_id": feed_id,
            "batch_size": FeedService.BATCH_SIZE,
            "poll_after_seconds": FeedService.POLL_AFTER_SECONDS,
            "sync_scope": sync_scope,
            "window_days": window_days,
            "refresh_markdown": refresh_markdown,
            "has_more": True,
            "next_begin": 0,
            "batches_completed": 0,
            "batches_failed": 0,
            "articles_synced": 0,
            "articles_failed": 0,
            "article_ids": [],
            "current_batch_task_id": current_batch_task_id,
            "latest_completed_batch": None,
            "last_progress_at": None,
            "timeout_reason": "",
            "stop_reason": "",
            "stop_article_url": "",
            "stop_article_source_id": "",
            "stop_publish_time": None,
        }

    @staticmethod
    def _build_first_batch_request(*, parent_task_id, feed_id, sync_scope, window_days, refresh_markdown):
        return {
            "parent_task_id": parent_task_id,
            "feed_id": feed_id,
            "batch_no": 1,
            "begin": 0,
            "batch_size": FeedService.BATCH_SIZE,
            "sync_scope": sync_scope,
            "window_days": window_days,
            "refresh_markdown": refresh_markdown,
        }

    @staticmethod
    def _build_batch_request(
        *,
        parent_task_id,
        feed_id,
        batch_no,
        begin,
        batch_size,
        sync_scope,
        window_days,
        refresh_markdown,
    ):
        return {
            "parent_task_id": parent_task_id,
            "feed_id": feed_id,
            "batch_no": batch_no,
            "begin": begin,
            "batch_size": batch_size,
            "sync_scope": sync_scope,
            "window_days": window_days,
            "refresh_markdown": refresh_markdown,
        }

    @staticmethod
    def _timeout_obsolete_feed_sync_tasks(*, feed):
        active_tasks = WechatSyncTask.objects.filter(
            tenant=feed.tenant,
            target_type="feed",
            target_id=feed.id,
            status__in=TaskService.ACTIVE_STATUSES,
            task_type__in=[
                WechatSyncTask.TaskType.FEED_SYNC,
                WechatSyncTask.TaskType.FEED_SYNC_RUN,
            ],
        ).order_by("-created_at")

        for task in active_tasks:
            if task.task_type == WechatSyncTask.TaskType.FEED_SYNC:
                payload = dict(task.result_payload or {})
                payload["run_status"] = WechatSyncTask.Status.TIMED_OUT
                payload["timeout_reason"] = "legacy_task_replaced"
                payload["last_progress_at"] = timezone.now().isoformat()
                TaskService.mark_timed_out(
                    task,
                    message="Legacy feed sync task timed out and was replaced by a batched sync run.",
                    result_payload=payload,
                )
                continue

            if TaskService.is_task_stale(task, stale_after_seconds=FeedService.STALE_AFTER_SECONDS):
                payload = dict(task.result_payload or {})
                payload["run_status"] = WechatSyncTask.Status.TIMED_OUT
                payload["timeout_reason"] = "stale_task"
                payload["last_progress_at"] = timezone.now().isoformat()
                TaskService.mark_timed_out(
                    task,
                    message="Feed sync task timed out because it stopped making progress.",
                    result_payload=payload,
                )

        active_batch_tasks = WechatSyncTask.objects.filter(
            tenant=feed.tenant,
            target_type="feed",
            target_id=feed.id,
            status__in=TaskService.ACTIVE_STATUSES,
            task_type=WechatSyncTask.TaskType.FEED_SYNC_BATCH,
        ).order_by("-created_at")

        for task in active_batch_tasks:
            request_payload = task.request_payload or {}
            parent_task_id = request_payload.get("parent_task_id")
            parent_task = None
            if parent_task_id is not None:
                parent_task = WechatSyncTask.objects.filter(
                    tenant=feed.tenant,
                    pk=parent_task_id,
                ).first()

            parent_is_active = parent_task is not None and parent_task.status in TaskService.ACTIVE_STATUSES
            batch_is_stale = TaskService.is_task_stale(
                task,
                stale_after_seconds=FeedService.BATCH_TIMEOUT_SECONDS,
            )

            if parent_is_active and not batch_is_stale:
                continue

            if parent_is_active:
                timeout_reason = "stale_batch"
                timeout_message = "Feed sync batch task timed out because it stopped making progress."
            else:
                timeout_reason = "orphan_batch"
                timeout_message = "Feed sync batch task timed out because its parent task is no longer active."

            TaskService.mark_timed_out(
                task,
                message=timeout_message,
                result_payload={
                    "task_type": WechatSyncTask.TaskType.FEED_SYNC_BATCH,
                    "feed_id": feed.id,
                    "parent_task_id": parent_task_id,
                    "timeout_reason": timeout_reason,
                },
            )

    @staticmethod
    def _mark_parent_run_stale_during_polling(*, parent_task, batch_task=None, timeout_reason):
        parent_payload = dict(
            parent_task.result_payload or FeedService._build_parent_run_payload(feed_id=parent_task.target_id)
        )
        parent_payload["current_batch_task_id"] = (
            getattr(batch_task, "id", None) or parent_payload.get("current_batch_task_id")
        )
        parent_payload["last_progress_at"] = timezone.now().isoformat()
        parent_payload["timeout_reason"] = timeout_reason
        parent_payload["feed_id"] = parent_task.target_id
        parent_payload["batches_failed"] = int(parent_payload.get("batches_failed") or 0) + 1

        if int(parent_payload.get("batches_completed") or 0) > 0:
            parent_payload["run_status"] = WechatSyncTask.Status.PARTIAL_SUCCESS
            TaskService.mark_partial_success(
                parent_task,
                message="Feed sync partially completed before timing out.",
                result_payload=parent_payload,
            )
            return parent_task

        parent_payload["run_status"] = WechatSyncTask.Status.TIMED_OUT
        TaskService.mark_timed_out(
            parent_task,
            message="Feed sync timed out before any batch completed.",
            result_payload=parent_payload,
        )
        return parent_task

    @staticmethod
    def refresh_parent_run_task_for_polling(*, task):
        if task.task_type != WechatSyncTask.TaskType.FEED_SYNC_RUN:
            return task
        if task.status not in TaskService.ACTIVE_STATUSES:
            return task

        payload = dict(task.result_payload or FeedService._build_parent_run_payload(feed_id=task.target_id))
        current_batch_task_id = payload.get("current_batch_task_id")
        batch_task = None
        if current_batch_task_id:
            batch_task = WechatSyncTask.objects.filter(
                tenant=task.tenant,
                id=current_batch_task_id,
            ).first()

        if (
            batch_task is not None
            and batch_task.status in TaskService.ACTIVE_STATUSES
            and TaskService.is_task_stale(batch_task, stale_after_seconds=FeedService.BATCH_TIMEOUT_SECONDS)
        ):
            TaskService.mark_timed_out(
                batch_task,
                message="Feed sync batch timed out because it stopped making progress.",
                result_payload={
                    "task_type": WechatSyncTask.TaskType.FEED_SYNC_BATCH,
                    "feed_id": task.target_id,
                    "parent_task_id": task.id,
                    "error": "Feed sync batch timed out because it stopped making progress.",
                },
            )
            return FeedService._mark_parent_run_stale_during_polling(
                parent_task=task,
                batch_task=batch_task,
                timeout_reason="batch_timeout",
            )

        if TaskService.is_task_stale(task, stale_after_seconds=FeedService.STALE_AFTER_SECONDS):
            return FeedService._mark_parent_run_stale_during_polling(
                parent_task=task,
                batch_task=batch_task,
                timeout_reason="stale_task",
            )

        return task

    @staticmethod
    def _enqueue_batch_task(*, parent_task, created_by, feed_id, batch_no, begin, batch_size):
        return TaskService.create_task(
            tenant=parent_task.tenant,
            task_type=WechatSyncTask.TaskType.FEED_SYNC_BATCH,
            created_by=created_by,
            target_type="feed",
            target_id=feed_id,
            message="Feed sync batch task created.",
            request_payload=FeedService._build_batch_request(
                parent_task_id=parent_task.id,
                feed_id=feed_id,
                batch_no=batch_no,
                begin=begin,
                batch_size=batch_size,
                sync_scope=(parent_task.request_payload or {}).get("sync_scope", FeedService.SYNC_SCOPE_FULL),
                window_days=(parent_task.request_payload or {}).get("window_days"),
                refresh_markdown=bool((parent_task.request_payload or {}).get("refresh_markdown", False)),
            ),
        )

    @staticmethod
    def _find_existing_article_by_normalized_url(*, tenant, article_url):
        from we_rss.services.article_service import ArticleService

        return ArticleService._find_existing_article_by_url(tenant=tenant, url=article_url)

    @staticmethod
    def _existing_article_needs_latest_backfill(*, existing_article, incoming_article):
        if existing_article is None:
            return False

        if getattr(existing_article, "publish_time", None) is None:
            return True

        incoming_source_id = str((incoming_article or {}).get("source_id") or "").strip()
        existing_source_id = str(getattr(existing_article, "source_id", "") or "").strip()
        existing_url_source_id = extract_source_id_from_url(getattr(existing_article, "url", ""))

        if incoming_source_id and existing_source_id and existing_source_id != incoming_source_id:
            if existing_source_id == existing_url_source_id:
                return True

        return False

    @staticmethod
    def _build_scope_stop_payload(*, stop_reason, article):
        publish_time = article.get("publish_time")
        return {
            "stop_reason": stop_reason,
            "stop_article_url": str(article.get("url") or "").strip(),
            "stop_article_source_id": str(article.get("source_id") or "").strip(),
            "stop_publish_time": publish_time.isoformat() if publish_time else None,
        }

    @staticmethod
    def _apply_sync_scope_to_batch(*, tenant, sync_scope, window_days, articles):
        scoped_articles = []
        stop_payload = None

        if sync_scope == FeedService.SYNC_SCOPE_LATEST:
            for article in articles:
                existing = FeedService._find_existing_article_by_normalized_url(
                    tenant=tenant,
                    article_url=article.get("url"),
                )
                if existing is not None and FeedService._existing_article_needs_latest_backfill(
                    existing_article=existing,
                    incoming_article=article,
                ):
                    scoped_articles.append(article)
                    continue
                if existing is not None:
                    stop_payload = FeedService._build_scope_stop_payload(
                        stop_reason="existing_article_detected",
                        article=article,
                    )
                    break
                scoped_articles.append(article)
            return {
                "articles": scoped_articles,
                "stop_payload": stop_payload,
                "stop_sync": stop_payload is not None,
            }

        if sync_scope == FeedService.SYNC_SCOPE_WINDOW:
            cutoff = timezone.now() - timedelta(days=int(window_days or 0))
            for article in articles:
                publish_time = article.get("publish_time")
                if publish_time is not None and publish_time < cutoff:
                    stop_payload = FeedService._build_scope_stop_payload(
                        stop_reason="window_boundary_reached",
                        article=article,
                    )
                    break
                scoped_articles.append(article)
            return {
                "articles": scoped_articles,
                "stop_payload": stop_payload,
                "stop_sync": stop_payload is not None,
            }

        return {
            "articles": list(articles),
            "stop_payload": None,
            "stop_sync": False,
        }

    @staticmethod
    def _apply_feed_sync_updates(*, feed, feed_payload, updated_by):
        now = timezone.now()
        feed.sync_time = now
        feed.update_time = now
        feed.last_synced_at = now
        if feed_payload.get("biz"):
            feed.biz = feed_payload["biz"]
        if feed_payload.get("mp_name"):
            feed.mp_name = feed_payload["mp_name"]
        if feed_payload.get("mp_cover"):
            feed.mp_cover = feed_payload["mp_cover"]
        feed.updated_by = updated_by
        feed.save()

    @staticmethod
    def _build_batch_article_summaries(*, article_ids):
        article_map = {
            article.id: article
            for article in WechatArticle.objects.filter(id__in=article_ids).order_by("-publish_time", "-id")
        }
        summaries = []
        for article_id in article_ids:
            article = article_map.get(article_id)
            if article is None:
                continue
            summaries.append(
                {
                    "id": article.id,
                    "source_id": article.source_id,
                    "title": article.title,
                    "url": article.url,
                    "publish_time": article.publish_time.isoformat() if article.publish_time else None,
                    "pic_url": article.pic_url,
                    "status": article.status,
                }
            )
        return summaries

    @staticmethod
    def _is_unavailable_article_payload(payload):
        status = str(payload.get("status") or "active").strip().lower()
        normalized_content = str(payload.get("content") or "").strip().upper()
        return status == "deleted" or normalized_content == "DELETED"

    @staticmethod
    def _build_unavailable_article_error(payload):
        return {
            "source_id": str(payload.get("source_id") or "").strip(),
            "url": str(payload.get("url") or "").strip(),
            "error": "Wechat article is unavailable or has been deleted.",
        }

    @staticmethod
    def _upsert_articles(*, feed, articles, updated_by=None, refresh_markdown=False):
        from we_rss.services.article_service import ArticleService

        synced_ids = []
        failed_articles = []
        for payload in articles:
            if FeedService._is_unavailable_article_payload(payload):
                failed_articles.append(FeedService._build_unavailable_article_error(payload))
                continue
            article, _created = ArticleService.upsert_article_from_payload(
                tenant=feed.tenant,
                feed=feed,
                payload=payload,
                actor=updated_by,
            )
            if refresh_markdown:
                ArticleService.enqueue_markdown_refresh(article_id=article.id)
            synced_ids.append(article.id)
        return {
            "article_ids": synced_ids,
            "failed_articles": failed_articles,
        }

    @staticmethod
    def execute_sync_batch_inline(
        *,
        feed,
        updated_by,
        gateway,
        batch_no,
        begin,
        batch_size,
        sync_scope,
        window_days=None,
        refresh_markdown=False,
        run_deadline=None,
    ):
        credential = feed.credential or FeedService.get_active_credential(tenant=feed.tenant)
        if credential is None:
            raise ValidationError("Active credential required.")

        now = timezone.now()
        batch_deadline = now + timedelta(seconds=FeedService.BATCH_TIMEOUT_SECONDS)
        if run_deadline is not None:
            if now >= run_deadline:
                raise TimeoutError("Feed sync run timed out.")
            batch_deadline = min(batch_deadline, run_deadline)

        batch_result = gateway.collect_feed_batch(
            feed,
            credential,
            begin=begin,
            batch_size=batch_size,
            deadline_at=batch_deadline,
        )
        scope_result = FeedService._apply_sync_scope_to_batch(
            tenant=feed.tenant,
            sync_scope=sync_scope,
            window_days=window_days,
            articles=batch_result.get("articles", []),
        )
        scoped_articles = scope_result["articles"]
        persistence_result = FeedService._upsert_articles(
            feed=feed,
            articles=scoped_articles,
            updated_by=updated_by,
            refresh_markdown=refresh_markdown,
        )
        synced_article_ids = persistence_result["article_ids"]
        combined_failed_articles = [
            *(batch_result.get("failed_articles", []) or []),
            *persistence_result["failed_articles"],
        ]
        detail_failed_count = int(batch_result.get("detail_failed_count") or 0) + len(
            persistence_result["failed_articles"]
        )
        FeedService._apply_feed_sync_updates(
            feed=feed,
            feed_payload=batch_result.get("feed_payload") or {},
            updated_by=updated_by,
        )
        has_more = False if scope_result["stop_sync"] else bool(batch_result.get("has_more", False))
        next_begin = batch_result.get("next_begin", begin)
        article_summaries = FeedService._build_batch_article_summaries(article_ids=synced_article_ids)

        result = {
            "batch_no": batch_no,
            "begin": begin,
            "end": next_begin,
            "has_more": has_more,
            "next_begin": next_begin,
            "article_count": len(synced_article_ids),
            "article_ids": synced_article_ids,
            "articles": article_summaries,
            "failed_articles": combined_failed_articles,
            "detail_success_count": len(synced_article_ids),
            "detail_failed_count": detail_failed_count,
            "raw_article_count": len(batch_result.get("articles", []) or []),
            "stop_sync": scope_result["stop_sync"],
        }
        if scope_result["stop_payload"] is not None:
            result.update(scope_result["stop_payload"])
        return result

    @staticmethod
    def build_feed_sync_progress_payload(
        *,
        feed,
        batch_result,
        sync_scope,
        window_days,
        refresh_markdown,
        batches_completed,
        articles_synced,
        articles_failed,
        status="success",
        error="",
    ):
        return {
            "feed_id": feed.id,
            "feed_name": feed.mp_name,
            "sync_scope": sync_scope,
            "window_days": window_days,
            "refresh_markdown": refresh_markdown,
            "batch_no": batch_result.get("batch_no"),
            "begin": batch_result.get("begin"),
            "end": batch_result.get("end"),
            "has_more": batch_result.get("has_more", False),
            "next_begin": batch_result.get("next_begin"),
            "article_count": batch_result.get("article_count", 0),
            "article_ids": batch_result.get("article_ids", []),
            "articles": batch_result.get("articles", []),
            "failed_articles": batch_result.get("failed_articles", []),
            "detail_success_count": batch_result.get("detail_success_count", 0),
            "detail_failed_count": batch_result.get("detail_failed_count", 0),
            "batches_completed": batches_completed,
            "articles_synced": articles_synced,
            "articles_failed": articles_failed,
            "stop_reason": batch_result.get("stop_reason", ""),
            "stop_article_url": batch_result.get("stop_article_url", ""),
            "stop_article_source_id": batch_result.get("stop_article_source_id", ""),
            "stop_publish_time": batch_result.get("stop_publish_time"),
            "status": status,
            "error": error,
        }

    @staticmethod
    def dedupe_feed_ids(feed_ids):
        deduped_feed_ids = []
        seen_feed_ids = set()
        for feed_id in feed_ids:
            if feed_id in seen_feed_ids:
                continue
            seen_feed_ids.add(feed_id)
            deduped_feed_ids.append(feed_id)
        return deduped_feed_ids

    @staticmethod
    def _build_feed_sync_batch_state_payload(
        *,
        queued_feed_ids,
        sync_scope,
        window_days,
        refresh_markdown,
        continue_on_error,
        total_feeds,
        completed_feeds=0,
        success_feeds=0,
        failed_feeds=0,
        results=None,
        current_feed_id=None,
    ):
        return {
            "queued_feed_ids": queued_feed_ids,
            "sync_scope": sync_scope,
            "window_days": window_days,
            "refresh_markdown": refresh_markdown,
            "continue_on_error": continue_on_error,
            "total_feeds": total_feeds,
            "completed_feeds": completed_feeds,
            "success_feeds": success_feeds,
            "failed_feeds": failed_feeds,
            "results": results or [],
            "current_feed_id": current_feed_id,
        }

    @staticmethod
    def sync_feed_batch(
        *,
        tenant,
        created_by,
        gateway,
        feed_ids,
        sync_scope,
        window_days=None,
        refresh_markdown=False,
        continue_on_error=True,
    ):
        queued_feed_ids = FeedService.dedupe_feed_ids(feed_ids)
        batch_task = TaskService.create_task(
            tenant=tenant,
            task_type=WechatSyncTask.TaskType.FEED_SYNC_RUN,
            created_by=created_by,
            target_type="feed_sync_batch",
            message="Feed sync batch task created.",
            request_payload={
                "feed_ids": queued_feed_ids,
                "sync_scope": sync_scope,
                "window_days": window_days,
                "refresh_markdown": refresh_markdown,
                "continue_on_error": continue_on_error,
            },
            result_payload=FeedService._build_feed_sync_batch_state_payload(
                queued_feed_ids=queued_feed_ids,
                sync_scope=sync_scope,
                window_days=window_days,
                refresh_markdown=refresh_markdown,
                continue_on_error=continue_on_error,
                total_feeds=len(queued_feed_ids),
            ),
        )
        TaskService.mark_running(batch_task)

        feeds_by_id = {
            feed.id: feed
            for feed in WechatFeed.objects.filter(tenant=tenant, id__in=queued_feed_ids).select_related("credential")
        }

        def update_batch_state(*, completed_feeds, success_feeds, failed_feeds, results, current_feed_id):
            batch_task.result_payload = FeedService._build_feed_sync_batch_state_payload(
                queued_feed_ids=queued_feed_ids,
                sync_scope=sync_scope,
                window_days=window_days,
                refresh_markdown=refresh_markdown,
                continue_on_error=continue_on_error,
                total_feeds=len(queued_feed_ids),
                completed_feeds=completed_feeds,
                success_feeds=success_feeds,
                failed_feeds=failed_feeds,
                results=results,
                current_feed_id=current_feed_id,
            )
            batch_task.save(update_fields=["result_payload", "updated_at"])

        def stream():
            completed_feeds = 0
            success_feeds = 0
            failed_feeds = 0
            results = []
            run_deadline = timezone.now() + timedelta(seconds=FeedService.RUN_TIMEOUT_SECONDS)

            yield {
                "event": "start",
                "data": {
                    "batch_task_id": batch_task.id,
                    "status": "running",
                    "sync_scope": sync_scope,
                    "window_days": window_days,
                    "refresh_markdown": refresh_markdown,
                    "continue_on_error": continue_on_error,
                    "total_feeds": len(queued_feed_ids),
                    "queued_feed_ids": queued_feed_ids,
                    "completed_feeds": completed_feeds,
                    "success_feeds": success_feeds,
                    "failed_feeds": failed_feeds,
                },
            }

            for index, feed_id in enumerate(queued_feed_ids, start=1):
                update_batch_state(
                    completed_feeds=completed_feeds,
                    success_feeds=success_feeds,
                    failed_feeds=failed_feeds,
                    results=results,
                    current_feed_id=feed_id,
                )
                yield {
                    "event": "feed_start",
                    "data": {
                        "batch_task_id": batch_task.id,
                        "status": "running",
                        "feed_id": feed_id,
                        "feed_index": index,
                        "total_feeds": len(queued_feed_ids),
                        "completed_feeds": completed_feeds,
                        "success_feeds": success_feeds,
                        "failed_feeds": failed_feeds,
                    },
                }

                feed = feeds_by_id.get(feed_id)
                if feed is None:
                    completed_feeds += 1
                    failed_feeds += 1
                    results.append({"feed_id": feed_id, "status": "failed", "error": "feed not found"})
                    update_batch_state(
                        completed_feeds=completed_feeds,
                        success_feeds=success_feeds,
                        failed_feeds=failed_feeds,
                        results=results,
                        current_feed_id=feed_id,
                    )
                    yield {
                        "event": "feed_done",
                        "data": {
                            "batch_task_id": batch_task.id,
                            "status": "failed",
                            "feed_id": feed_id,
                            "feed_index": index,
                            "total_feeds": len(queued_feed_ids),
                            "completed_feeds": completed_feeds,
                            "success_feeds": success_feeds,
                            "failed_feeds": failed_feeds,
                            "articles_synced": 0,
                            "articles_failed": 0,
                            "error": "feed not found",
                        },
                    }
                    if not continue_on_error:
                        TaskService.mark_failed(
                            batch_task,
                            message="Feed sync batch aborted after feed failure.",
                            result_payload=batch_task.result_payload,
                        )
                        yield {
                            "event": "error",
                            "data": {
                                "batch_task_id": batch_task.id,
                                "status": "failed",
                                "error": "batch sync aborted after feed failure",
                            },
                        }
                        return
                    continue

                feed_batch_no = 1
                begin = 0
                feed_article_ids = []
                feed_failed_count = 0
                final_feed_done_event = None

                try:
                    while True:
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(
                                FeedService.execute_sync_batch_inline,
                                feed=feed,
                                updated_by=created_by,
                                gateway=gateway,
                                batch_no=feed_batch_no,
                                begin=begin,
                                batch_size=FeedService.BATCH_SIZE,
                                sync_scope=sync_scope,
                                window_days=window_days,
                                refresh_markdown=refresh_markdown,
                                run_deadline=run_deadline,
                            )
                            while True:
                                try:
                                    batch_result = future.result(
                                        timeout=FeedService.BATCH_STREAM_HEARTBEAT_INTERVAL_SECONDS
                                    )
                                    break
                                except FutureTimeoutError:
                                    yield {
                                        "event": "heartbeat",
                                        "data": {
                                            "batch_task_id": batch_task.id,
                                            "status": "running",
                                            "current_feed_id": feed.id,
                                            "completed_feeds": completed_feeds,
                                            "success_feeds": success_feeds,
                                            "failed_feeds": failed_feeds,
                                            "timestamp": timezone.now().isoformat(),
                                        },
                                    }
                        if feed_batch_no == 1 and not feed_article_ids:
                            pass
                        prior_feed_failed_count = feed_failed_count
                        feed_article_ids = list(
                            dict.fromkeys([*feed_article_ids, *(batch_result.get("article_ids") or [])])
                        )
                        feed_failed_count += int(batch_result.get("detail_failed_count") or 0)
                        yield {
                            "event": "feed_batch",
                            "data": {
                                "batch_task_id": batch_task.id,
                                "status": "running",
                                "feed_id": feed.id,
                                "feed_index": index,
                                "total_feeds": len(queued_feed_ids),
                                "completed_feeds": completed_feeds,
                                "success_feeds": success_feeds,
                                "failed_feeds": failed_feeds,
                                "batch_no": batch_result.get("batch_no"),
                                "batch_size": FeedService.BATCH_SIZE,
                                "articles_synced": len(feed_article_ids),
                                "articles_failed": prior_feed_failed_count
                                + int(batch_result.get("detail_failed_count") or 0),
                                "has_more": batch_result.get("has_more", False),
                                "next_begin": batch_result.get("next_begin"),
                                "detail_success_count": batch_result.get("detail_success_count", 0),
                                "detail_failed_count": batch_result.get("detail_failed_count", 0),
                            },
                        }
                        if not batch_result.get("has_more", False):
                            completed_feeds += 1
                            success_feeds += 1
                            results.append(
                                {
                                    "feed_id": feed.id,
                                    "status": "success",
                                    "articles_synced": len(feed_article_ids),
                                    "articles_failed": feed_failed_count,
                                }
                            )
                            final_feed_done_event = {
                                "event": "feed_done",
                                "data": {
                                    "batch_task_id": batch_task.id,
                                    "status": "success",
                                    "feed_id": feed.id,
                                    "feed_index": index,
                                    "total_feeds": len(queued_feed_ids),
                                    "completed_feeds": completed_feeds,
                                    "success_feeds": success_feeds,
                                    "failed_feeds": failed_feeds,
                                    "articles_synced": len(feed_article_ids),
                                    "articles_failed": feed_failed_count,
                                    "detail_success_count": len(feed_article_ids),
                                    "detail_failed_count": feed_failed_count,
                                },
                            }
                            break
                        begin = int(batch_result.get("next_begin") or begin)
                        feed_batch_no += 1
                except Exception as exc:
                    completed_feeds += 1
                    failed_feeds += 1
                    results.append({"feed_id": feed.id, "status": "failed", "error": str(exc)})
                    final_feed_done_event = {
                        "event": "feed_done",
                        "data": {
                            "batch_task_id": batch_task.id,
                            "status": "failed",
                            "feed_id": feed.id,
                            "feed_index": index,
                            "total_feeds": len(queued_feed_ids),
                            "completed_feeds": completed_feeds,
                            "success_feeds": success_feeds,
                            "failed_feeds": failed_feeds,
                            "articles_synced": len(feed_article_ids),
                            "articles_failed": feed_failed_count,
                            "error": str(exc),
                        },
                    }

                update_batch_state(
                    completed_feeds=completed_feeds,
                    success_feeds=success_feeds,
                    failed_feeds=failed_feeds,
                    results=results,
                    current_feed_id=feed_id,
                )
                yield final_feed_done_event

                if final_feed_done_event["data"]["status"] == "failed" and not continue_on_error:
                    TaskService.mark_failed(
                        batch_task,
                        message="Feed sync batch aborted after feed failure.",
                        result_payload=batch_task.result_payload,
                    )
                    yield {
                        "event": "error",
                        "data": {
                            "batch_task_id": batch_task.id,
                            "status": "failed",
                            "error": "batch sync aborted after feed failure",
                        },
                    }
                    return

            TaskService.mark_success(
                batch_task,
                message="Feed sync batch complete.",
                result_payload=FeedService._build_feed_sync_batch_state_payload(
                    queued_feed_ids=queued_feed_ids,
                    sync_scope=sync_scope,
                    window_days=window_days,
                    refresh_markdown=refresh_markdown,
                    continue_on_error=continue_on_error,
                    total_feeds=len(queued_feed_ids),
                    completed_feeds=completed_feeds,
                    success_feeds=success_feeds,
                    failed_feeds=failed_feeds,
                    results=results,
                    current_feed_id=None,
                ),
            )
            yield {
                "event": "done",
                "data": {
                    "batch_task_id": batch_task.id,
                    "status": "done",
                    "sync_scope": sync_scope,
                    "window_days": window_days,
                    "refresh_markdown": refresh_markdown,
                    "continue_on_error": continue_on_error,
                    "total_feeds": len(queued_feed_ids),
                    "completed_feeds": completed_feeds,
                    "success_feeds": success_feeds,
                    "failed_feeds": failed_feeds,
                    "results": results,
                },
            }

        return batch_task, stream

    @staticmethod
    def log_feed_sync_progress(payload):
        message = (
            "We RSS feed sync progress: "
            f"feed_id={payload.get('feed_id')} "
            f"batch={payload.get('batch_no')} "
            f"status={payload.get('status')} "
            f"articles={payload.get('article_count')} "
            f"synced_total={payload.get('articles_synced')} "
            f"failed_total={payload.get('articles_failed')} "
            f"has_more={payload.get('has_more')} "
            f"next_begin={payload.get('next_begin')} "
            f"error={payload.get('error') or ''}"
        )
        logger.info(message)
        try:
            print(message)
        except (OSError, UnicodeEncodeError):
            logger.warning("We RSS feed sync stdout print skipped.")

    @staticmethod
    def sync_feed(*, feed, created_by, sync_scope=SYNC_SCOPE_FULL, window_days=None, refresh_markdown=False):
        active_task = TaskService.find_active_task(
            tenant=feed.tenant,
            task_type=WechatSyncTask.TaskType.FEED_SYNC_RUN,
            target_type="feed",
            target_id=feed.id,
        )
        if active_task is not None and not TaskService.is_task_stale(
            active_task,
            stale_after_seconds=FeedService.STALE_AFTER_SECONDS,
        ):
            if active_task.message != "A feed sync task is already running.":
                active_task.message = "A feed sync task is already running."
                active_task.save(update_fields=["message", "updated_at"])
            return active_task

        FeedService._timeout_obsolete_feed_sync_tasks(feed=feed)

        task = TaskService.create_task(
            tenant=feed.tenant,
            task_type=WechatSyncTask.TaskType.FEED_SYNC_RUN,
            created_by=created_by,
            target_type="feed",
            target_id=feed.id,
            message="Feed sync task created.",
            request_payload={
                "feed_id": feed.id,
                "batch_size": FeedService.BATCH_SIZE,
                "poll_after_seconds": FeedService.POLL_AFTER_SECONDS,
                "sync_scope": sync_scope,
                "window_days": window_days,
                "refresh_markdown": refresh_markdown,
            },
            result_payload=FeedService._build_parent_run_payload(
                feed_id=feed.id,
                sync_scope=sync_scope,
                window_days=window_days,
                refresh_markdown=refresh_markdown,
            ),
        )
        TaskService.mark_running(task)

        batch_task = TaskService.create_task(
            tenant=feed.tenant,
            task_type=WechatSyncTask.TaskType.FEED_SYNC_BATCH,
            created_by=created_by,
            target_type="feed",
            target_id=feed.id,
            message="Feed sync batch task created.",
            request_payload=FeedService._build_first_batch_request(
                parent_task_id=task.id,
                feed_id=feed.id,
                sync_scope=sync_scope,
                window_days=window_days,
                refresh_markdown=refresh_markdown,
            ),
        )
        task.result_payload = FeedService._build_parent_run_payload(
            feed_id=feed.id,
            current_batch_task_id=batch_task.id,
            sync_scope=sync_scope,
            window_days=window_days,
            refresh_markdown=refresh_markdown,
        )
        task.save(update_fields=["result_payload", "updated_at"])
        from we_rss.tasks import run_feed_sync_batch_task

        dispatch_we_rss_task(run_feed_sync_batch_task, batch_task.id)
        return task

    @staticmethod
    def execute_sync_batch(*, task, parent_task, feed, updated_by, gateway):
        if parent_task is None:
            raise ValidationError("Parent feed sync task required.")
        if parent_task.status not in TaskService.ACTIVE_STATUSES:
            raise ValidationError("Parent feed sync task is no longer active.")

        credential = feed.credential or FeedService.get_active_credential(tenant=feed.tenant)
        if credential is None:
            raise ValidationError("Active credential required.")

        request_payload = task.request_payload or {}
        batch_no = int(request_payload.get("batch_no") or 1)
        begin = int(request_payload.get("begin") or 0)
        batch_size = int(request_payload.get("batch_size") or FeedService.BATCH_SIZE)
        sync_scope = request_payload.get("sync_scope") or FeedService.SYNC_SCOPE_FULL
        window_days = request_payload.get("window_days")
        refresh_markdown = bool(request_payload.get("refresh_markdown", False))
        run_started_at = parent_task.started_at or timezone.now()
        run_deadline = run_started_at + timedelta(seconds=FeedService.RUN_TIMEOUT_SECONDS)
        now = timezone.now()
        if now >= run_deadline:
            raise TimeoutError("Feed sync run timed out.")

        batch_deadline = min(
            now + timedelta(seconds=FeedService.BATCH_TIMEOUT_SECONDS),
            run_deadline,
        )
        batch_result = gateway.collect_feed_batch(
            feed,
            credential,
            begin=begin,
            batch_size=batch_size,
            deadline_at=batch_deadline,
        )
        scope_result = FeedService._apply_sync_scope_to_batch(
            tenant=feed.tenant,
            sync_scope=sync_scope,
            window_days=window_days,
            articles=batch_result.get("articles", []),
        )
        scoped_articles = scope_result["articles"]
        persistence_result = FeedService._upsert_articles(
            feed=feed,
            articles=scoped_articles,
            updated_by=updated_by,
            refresh_markdown=refresh_markdown,
        )
        synced_article_ids = persistence_result["article_ids"]
        combined_failed_articles = [
            *(batch_result.get("failed_articles", []) or []),
            *persistence_result["failed_articles"],
        ]
        detail_failed_count = int(batch_result.get("detail_failed_count") or 0) + len(
            persistence_result["failed_articles"]
        )
        FeedService._apply_feed_sync_updates(
            feed=feed,
            feed_payload=batch_result.get("feed_payload") or {},
            updated_by=updated_by,
        )

        finished_at = timezone.now()
        latest_completed_batch = {
            "batch_no": batch_no,
            "begin": begin,
            "end": batch_result.get("next_begin", begin),
            "has_more": False if scope_result["stop_sync"] else batch_result.get("has_more", False),
            "article_count": len(synced_article_ids),
            "article_ids": synced_article_ids,
            "articles": FeedService._build_batch_article_summaries(article_ids=synced_article_ids),
            "failed_articles": combined_failed_articles,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "finished_at": finished_at.isoformat(),
        }
        parent_payload = dict(parent_task.result_payload or FeedService._build_parent_run_payload(feed_id=feed.id))
        parent_payload["batches_completed"] = int(parent_payload.get("batches_completed") or 0) + 1
        parent_payload["articles_failed"] = int(parent_payload.get("articles_failed") or 0) + detail_failed_count
        cumulative_article_ids = list(dict.fromkeys([*(parent_payload.get("article_ids") or []), *synced_article_ids]))
        parent_payload["article_ids"] = cumulative_article_ids
        parent_payload["articles_synced"] = len(cumulative_article_ids)
        parent_payload["has_more"] = False if scope_result["stop_sync"] else batch_result.get("has_more", False)
        parent_payload["next_begin"] = batch_result.get("next_begin", begin)
        parent_payload["latest_completed_batch"] = latest_completed_batch
        parent_payload["last_progress_at"] = finished_at.isoformat()
        parent_payload["timeout_reason"] = ""
        parent_payload["sync_scope"] = sync_scope
        parent_payload["window_days"] = window_days
        parent_payload["refresh_markdown"] = refresh_markdown
        if scope_result["stop_payload"] is not None:
            parent_payload.update(scope_result["stop_payload"])
        else:
            parent_payload["stop_reason"] = ""
            parent_payload["stop_article_url"] = ""
            parent_payload["stop_article_source_id"] = ""
            parent_payload["stop_publish_time"] = None

        child_result = {
            "parent_task_id": parent_task.id,
            "batch_no": batch_no,
            "has_more": False if scope_result["stop_sync"] else batch_result.get("has_more", False),
            "next_begin": batch_result.get("next_begin", begin),
            "article_count": len(synced_article_ids),
            "article_ids": synced_article_ids,
            "articles": latest_completed_batch["articles"],
            "failed_articles": combined_failed_articles,
            "next_batch_task_id": None,
        }

        if not scope_result["stop_sync"] and batch_result.get("has_more", False):
            next_task = FeedService._enqueue_batch_task(
                parent_task=parent_task,
                created_by=updated_by,
                feed_id=feed.id,
                batch_no=batch_no + 1,
                begin=batch_result.get("next_begin", begin),
                batch_size=batch_size,
            )
            parent_payload["current_batch_task_id"] = next_task.id
            parent_payload["run_status"] = WechatSyncTask.Status.RUNNING
            parent_task.message = "Feed sync is running."
            parent_task.result_payload = parent_payload
            parent_task.save(update_fields=["message", "result_payload", "updated_at"])
            child_result["next_batch_task_id"] = next_task.id
            return child_result

        parent_payload["current_batch_task_id"] = None
        parent_payload["run_status"] = WechatSyncTask.Status.SUCCESS
        TaskService.mark_success(
            parent_task,
            message="Feed sync complete",
            result_payload=parent_payload,
        )
        return child_result

    @staticmethod
    def execute_sync(*, feed, updated_by, gateway):
        credential = feed.credential or FeedService.get_active_credential(tenant=feed.tenant)
        if credential is None:
            raise ValidationError("Active credential required.")

        now = timezone.now()
        result = gateway.sync_feed(feed, credential)
        persistence_result = FeedService._upsert_articles(
            feed=feed,
            articles=result.get("articles", []),
            updated_by=updated_by,
        )
        synced_article_ids = persistence_result["article_ids"]
        feed_payload = result.get("feed_payload") or {}
        gateway_result_payload = result.get("result_payload") or {}
        combined_failed_articles = [
            *(gateway_result_payload.get("errors", []) or []),
            *persistence_result["failed_articles"],
        ]
        detail_failed_count = int(gateway_result_payload.get("detail_failed_count", 0) or 0) + len(
            persistence_result["failed_articles"]
        )

        FeedService._apply_feed_sync_updates(feed=feed, feed_payload=feed_payload, updated_by=updated_by)

        return {
            "message": result.get("message", "Feed sync complete"),
            "feed_id": feed.id,
            "article_ids": synced_article_ids,
            "article_count": len(synced_article_ids),
            "detail_success_count": len(synced_article_ids),
            "detail_failed_count": detail_failed_count,
            "failed_articles": combined_failed_articles,
            "result_payload": gateway_result_payload,
        }
