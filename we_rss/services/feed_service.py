import time

import requests

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
    load_credential_cookies,
    normalize_wechat_article_url,
    parse_publish_page_articles,
    parse_wechat_article_html,
)


class WechatFeedGateway:
    def __init__(self, *, session_factory=None, page_size=5, max_pages=None, timeout=15, sleep_seconds=0.5, sleep_func=None):
        self.session_factory = session_factory or requests.Session
        self.page_size = page_size
        self.max_pages = max_pages
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds
        self.sleep_func = sleep_func or time.sleep

    def _resolve_fakeid(self, feed):
        return feed.faker_id or feed.source_id or ""

    def _throttle(self):
        if self.sleep_seconds and self.sleep_seconds > 0:
            self.sleep_func(self.sleep_seconds)

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

    def sync_feed(self, feed, credential):
        session = build_wechat_session(self.session_factory)
        load_credential_cookies(session, credential.cookie)
        articles = []
        seen_source_ids = set()
        feed_payload = {}
        sync_errors = []
        page_index = 0
        has_requested_article_detail = False
        while self.max_pages is None or page_index < self.max_pages:
            if page_index > 0:
                self._throttle()
            response = session.get(
                "https://mp.weixin.qq.com/cgi-bin/appmsgpublish",
                params={
                    "sub": "list",
                    "sub_action": "list_ex",
                    "begin": page_index * self.page_size,
                    "count": self.page_size,
                    "fakeid": self._resolve_fakeid(feed),
                    "token": credential.token,
                    "lang": "zh_CN",
                    "f": "json",
                    "ajax": 1,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if (payload.get("base_resp") or {}).get("ret") != 0:
                raise ValidationError("WeChat feed sync failed.")

            page_articles = parse_publish_page_articles(payload)
            if not page_articles:
                break

            for item in page_articles:
                source_id = str(item.get("aid") or "")
                if source_id and source_id in seen_source_ids:
                    continue
                article_url = item.get("link", "")
                stable_article_url = normalize_wechat_article_url(article_url) or article_url
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
                        "url": stable_article_url or parse_article_url,
                        "pic_url": parsed_article.get("pic_url") or item.get("cover") or "",
                        "publish_time": parsed_article.get("publish_time") or timezone.datetime.fromtimestamp(
                            item.get("create_time", 0),
                            tz=timezone.get_current_timezone(),
                        ),
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
                if source_id:
                    seen_source_ids.add(source_id)
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


class FeedService:
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
    def sync_feed(*, feed, created_by):
        active_task = TaskService.find_active_task(
            tenant=feed.tenant,
            task_type=WechatSyncTask.TaskType.FEED_SYNC,
            target_type="feed",
            target_id=feed.id,
        )
        if active_task is not None:
            return active_task

        task = TaskService.create_task(
            tenant=feed.tenant,
            task_type=WechatSyncTask.TaskType.FEED_SYNC,
            created_by=created_by,
            target_type="feed",
            target_id=feed.id,
            message="Feed sync task created.",
            request_payload={"feed_id": feed.id},
        )
        from we_rss.tasks import run_feed_sync_task

        dispatch_we_rss_task(run_feed_sync_task, task.id)
        return task

    @staticmethod
    def _upsert_articles(*, feed, articles):
        synced_ids = []
        for payload in articles:
            article, _created = WechatArticle.objects.update_or_create(
                tenant=feed.tenant,
                source_id=payload.get("source_id", ""),
                defaults={
                    "feed": feed,
                    "article_type": payload.get("article_type", WechatArticle.ArticleType.NEWS),
                    "title": payload.get("title", ""),
                    "description": payload.get("description", ""),
                    "content": payload.get("content", ""),
                    "url": payload.get("url", ""),
                    "pic_url": payload.get("pic_url", ""),
                    "publish_time": payload.get("publish_time"),
                    "status": payload.get("status", "active"),
                    "read_num": payload.get("read_num", 0),
                    "like_num": payload.get("like_num", 0),
                    "old_like_num": payload.get("old_like_num", 0),
                    "share_num": payload.get("share_num", 0),
                    "collect_num": payload.get("collect_num", 0),
                    "comment_count": payload.get("comment_count", 0),
                    "comment_reply_count": payload.get("comment_reply_count", 0),
                    "comment_total_count": payload.get("comment_total_count", 0),
                },
            )
            synced_ids.append(article.id)
        return synced_ids

    @staticmethod
    def execute_sync(*, feed, updated_by, gateway):
        credential = feed.credential or FeedService.get_active_credential(tenant=feed.tenant)
        if credential is None:
            raise ValidationError("Active credential required.")

        now = timezone.now()
        result = gateway.sync_feed(feed, credential)
        synced_article_ids = FeedService._upsert_articles(feed=feed, articles=result.get("articles", []))
        feed_payload = result.get("feed_payload") or {}
        gateway_result_payload = result.get("result_payload") or {}

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

        return {
            "message": result.get("message", "Feed sync complete"),
            "feed_id": feed.id,
            "article_ids": synced_article_ids,
            "article_count": len(synced_article_ids),
            "detail_success_count": gateway_result_payload.get("detail_success_count", len(synced_article_ids)),
            "detail_failed_count": gateway_result_payload.get("detail_failed_count", 0),
            "failed_articles": gateway_result_payload.get("errors", []),
            "result_payload": gateway_result_payload,
        }
