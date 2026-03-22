import requests

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError

from we_rss.models import WechatArticle, WechatFeed, WechatSyncTask
from we_rss.services.feed_service import FeedService
from we_rss.services.task_service import TaskService
from we_rss.services.wechat_gateway import (
    build_wechat_session,
    extract_source_id_from_url,
    load_credential_cookies,
    parse_wechat_article_html,
)


ARTICLE_PAYLOAD_FIELDS = [
    "source_id",
    "title",
    "description",
    "content",
    "url",
    "pic_url",
    "status",
    "read_num",
    "like_num",
    "old_like_num",
    "share_num",
    "collect_num",
    "comment_count",
    "comment_reply_count",
    "comment_total_count",
]


class WechatArticleGateway:
    def import_article_by_url(self, url, credential):
        return self._fetch_article_payload(url=url, credential=credential)

    def refresh_article(self, article, credential):
        return self._fetch_article_payload(url=article.url, credential=credential)

    def _fetch_article_payload(self, *, url, credential):
        session = build_wechat_session(requests.Session)
        load_credential_cookies(session, credential.cookie)
        response = session.get(url, timeout=15)
        response.raise_for_status()
        payload = parse_wechat_article_html(response.text, response.url or url)
        payload["source_id"] = payload.get("source_id") or extract_source_id_from_url(response.url or url)
        payload["status"] = payload.get("status", "active")
        return payload


class ArticleService:
    @staticmethod
    def _normalize_payload(payload):
        normalized = {field: payload[field] for field in ARTICLE_PAYLOAD_FIELDS if field in payload}
        publish_time = payload.get("publish_time")
        if isinstance(publish_time, str):
            normalized["publish_time"] = parse_datetime(publish_time)
        elif publish_time is not None:
            normalized["publish_time"] = publish_time
        return normalized

    @staticmethod
    def _normalize_task_url(url):
        return str(url or "").strip()

    @staticmethod
    def _get_or_create_featured_feed(*, tenant, credential, member):
        defaults = {
            "credential": credential,
            "source_id": "",
            "mp_name": "Imported Articles",
            "is_featured": True,
            "created_by": member,
            "updated_by": member,
        }
        feed, created = WechatFeed.objects.get_or_create(
            tenant=tenant,
            is_featured=True,
            defaults=defaults,
        )
        if not created:
            if credential is not None and feed.credential_id is None:
                feed.credential = credential
            feed.updated_by = member
            feed.save()
        return feed

    @staticmethod
    def _resolve_credential(*, tenant, feed=None):
        if feed is not None and feed.credential_id:
            return feed.credential
        credential = FeedService.get_active_credential(tenant=tenant)
        if credential is None:
            raise ValidationError("Active credential required.")
        return credential

    @staticmethod
    def import_article_by_url(*, tenant, created_by, url):
        normalized_url = ArticleService._normalize_task_url(url)
        active_task = TaskService.find_active_task(
            tenant=tenant,
            task_type=WechatSyncTask.TaskType.ARTICLE_IMPORT,
            task_key=f"article_import:{normalized_url}",
        )
        if active_task is not None:
            return active_task

        task = TaskService.create_task(
            tenant=tenant,
            task_type=WechatSyncTask.TaskType.ARTICLE_IMPORT,
            created_by=created_by,
            target_type="article",
            task_key=f"article_import:{normalized_url}",
            message="Article import task created.",
            request_payload={"url": normalized_url},
        )
        from we_rss.tasks import run_article_import_task

        run_article_import_task.delay(task.id)
        return task

    @staticmethod
    def execute_import_task(*, task, gateway):
        normalized_url = ArticleService._normalize_task_url((task.request_payload or {}).get("url"))
        credential = ArticleService._resolve_credential(tenant=task.tenant)
        payload = ArticleService._normalize_payload(gateway.import_article_by_url(normalized_url, credential))
        normalized_content = str(payload.get("content") or "").strip()
        if payload.get("status") == "deleted" or normalized_content == "DELETED":
            raise ValidationError("Wechat article is unavailable or has been deleted.")
        if not normalized_content:
            raise ValidationError("Wechat article content is empty.")
        feed = ArticleService._get_or_create_featured_feed(tenant=task.tenant, credential=credential, member=task.created_by)

        with transaction.atomic():
            article, _created = WechatArticle.objects.update_or_create(
                tenant=task.tenant,
                source_id=payload.get("source_id", ""),
                defaults={
                    "feed": feed,
                    **payload,
                },
            )

        return {
            "message": "Article import complete",
            "article_id": article.id,
            "feed_id": feed.id,
            "source_id": article.source_id,
        }

    @staticmethod
    def refresh_article(*, article, created_by):
        active_task = TaskService.find_active_task(
            tenant=article.tenant,
            task_type=WechatSyncTask.TaskType.ARTICLE_REFRESH,
            target_type="article",
            target_id=article.id,
        )
        if active_task is not None:
            return active_task

        task = TaskService.create_task(
            tenant=article.tenant,
            task_type=WechatSyncTask.TaskType.ARTICLE_REFRESH,
            created_by=created_by,
            target_type="article",
            target_id=article.id,
            message="Article refresh task created.",
            request_payload={"article_id": article.id},
        )
        from we_rss.tasks import run_article_refresh_task

        run_article_refresh_task.delay(task.id)
        return task

    @staticmethod
    def execute_refresh_task(*, article, updated_by, gateway):
        credential = ArticleService._resolve_credential(tenant=article.tenant, feed=article.feed)
        payload = ArticleService._normalize_payload(gateway.refresh_article(article, credential))

        with transaction.atomic():
            for field, value in payload.items():
                setattr(article, field, value)
            article.last_refreshed_at = timezone.now()
            article.save()

        return {
            "message": "Article refresh complete",
            "article_id": article.id,
            "title": article.title,
            "updated_by_id": getattr(updated_by, "id", None),
        }

    @staticmethod
    def set_read_status(*, article, is_read):
        article.is_read = is_read
        article.save(update_fields=["is_read", "updated_at"])
        return article

    @staticmethod
    def set_favorite_status(*, article, is_favorite):
        article.is_favorite = is_favorite
        article.save(update_fields=["is_favorite", "updated_at"])
        return article
