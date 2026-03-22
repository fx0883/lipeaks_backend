import requests

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from we_rss.models import WechatArticle, WechatCredential, WechatFeed, WechatSyncTask
from we_rss.services.task_service import TaskService
from we_rss.services.wechat_gateway import (
    build_wechat_session,
    load_credential_cookies,
    parse_publish_page_articles,
    parse_wechat_article_html,
)


class WechatFeedGateway:
    def __init__(self, *, session_factory=None, page_size=5, max_pages=3, timeout=15):
        self.session_factory = session_factory or requests.Session
        self.page_size = page_size
        self.max_pages = max_pages
        self.timeout = timeout

    def _resolve_fakeid(self, feed):
        return feed.faker_id or feed.source_id or ""

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
        for page_index in range(self.max_pages):
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
                parsed_article = {}
                resolved_article_url = article_url
                try:
                    article_response = session.get(article_url, timeout=self.timeout)
                    article_response.raise_for_status()
                    resolved_article_url = article_response.url or article_url
                    parsed_article = parse_wechat_article_html(article_response.text, resolved_article_url)
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
                            "url": article_url,
                            "error": str(exc),
                        }
                    )
                    parsed_article = {}
                articles.append(
                    {
                        "source_id": source_id or parsed_article.get("source_id") or "",
                        "title": parsed_article.get("title") or item.get("title") or "",
                        "description": parsed_article.get("description") or item.get("digest") or "",
                        "content": parsed_article.get("content", ""),
                        "url": resolved_article_url,
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

        run_feed_sync_task.delay(task.id)
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
