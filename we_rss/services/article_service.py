import csv
import time
import requests
from urllib.parse import urlparse, urlunparse

from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError

from users.models import Member
from we_rss.models import (
    MemberFeedSubscription,
    WechatArticle,
    WechatFeed,
    WechatSyncTask,
)
from we_rss.services.article_visibility_service import ArticleVisibilityService
from we_rss.services.feed_service import FeedService
from we_rss.services.article_markdown_service import ArticleMarkdownService
from we_rss.services.member_article_state_service import MemberArticleStateService
from we_rss.services.task_service import TaskService, dispatch_we_rss_task
from we_rss.services.wechat_gateway import (
    build_wechat_session,
    extract_source_id_from_url,
    load_credential_cookies,
    normalize_wechat_article_url,
    parse_wechat_article_html,
)


ARTICLE_PAYLOAD_FIELDS = [
    "source_id",
    "article_type",
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

ARTICLE_EXPORT_COLUMNS = [
    ("article_id", lambda article: article.id),
    ("feed_id", lambda article: getattr(article, "feed_id", "") or ""),
    ("feed_name", lambda article: getattr(article.feed, "mp_name", "") if article.feed else ""),
    ("feed_source_id", lambda article: getattr(article.feed, "source_id", "") if article.feed else ""),
    ("source_id", lambda article: article.source_id),
    ("article_type", lambda article: article.article_type),
    ("title", lambda article: article.title),
    ("description", lambda article: article.description),
    ("content", lambda article: article.content),
    ("url", lambda article: article.url),
    ("pic_url", lambda article: article.pic_url),
    ("publish_time", lambda article: article.publish_time.isoformat() if article.publish_time else ""),
    ("status", lambda article: article.status),
    ("read_num", lambda article: article.read_num),
    ("like_num", lambda article: article.like_num),
    ("old_like_num", lambda article: article.old_like_num),
    ("share_num", lambda article: article.share_num),
    ("collect_num", lambda article: article.collect_num),
    ("comment_count", lambda article: article.comment_count),
    ("comment_reply_count", lambda article: article.comment_reply_count),
    ("comment_total_count", lambda article: article.comment_total_count),
    ("last_refreshed_at", lambda article: article.last_refreshed_at.isoformat() if article.last_refreshed_at else ""),
    ("created_at", lambda article: article.created_at.isoformat() if article.created_at else ""),
    ("updated_at", lambda article: article.updated_at.isoformat() if article.updated_at else ""),
]


def get_article_markdown_service():
    return ArticleMarkdownService()


class WechatArticleGateway:
    def import_article_by_url(self, url, credential):
        return self._fetch_article_payload(url=url, credential=credential)

    def refresh_article(self, article, credential):
        return self._fetch_article_payload(url=article.url, credential=credential)

    def _fetch_article_payload(self, *, url, credential):
        session = build_wechat_session(requests.Session)
        load_credential_cookies(session, credential.cookie)
        response = session.get(url, timeout=120)
        response.raise_for_status()
        normalized_request_url = normalize_wechat_article_url(url) or str(url or "").strip()
        normalized_response_url = normalize_wechat_article_url(response.url or normalized_request_url) or normalized_request_url
        payload = parse_wechat_article_html(response.text, normalized_response_url)
        payload_source_id = str(payload.get("source_id") or "").strip()
        response_source_id = extract_source_id_from_url(normalized_response_url)
        request_source_id = extract_source_id_from_url(normalized_request_url)
        payload["source_id"] = (
            payload_source_id
            or response_source_id
            or request_source_id
        )
        payload["url"] = normalized_response_url or normalized_request_url
        payload["status"] = payload.get("status", "active")
        return payload


class ArticleService:
    @staticmethod
    def _truncate_char_field(value, max_length):
        text = str(value or "").strip()
        if len(text) <= max_length:
            return text
        return text[:max_length]

    @staticmethod
    def build_search_query(search):
        words = str(search or "").replace("-", " ").replace("|", " ").split()
        if not words:
            return None

        query = Q()
        for word in words:
            query |= Q(title__icontains=word)
        return query

    @staticmethod
    def _normalize_payload(payload):
        normalized = {field: payload[field] for field in ARTICLE_PAYLOAD_FIELDS if field in payload}
        publish_time = payload.get("publish_time")
        if isinstance(publish_time, str):
            normalized["publish_time"] = parse_datetime(publish_time)
        elif publish_time is not None:
            normalized["publish_time"] = publish_time
        normalized["url"] = ArticleService._normalize_task_url(normalized.get("url"))
        return normalized

    @staticmethod
    def _normalize_task_url(url):
        normalized_url = normalize_wechat_article_url(url)
        if normalized_url:
            return normalized_url
        return str(url or "").strip()

    @staticmethod
    def _article_url_prefix(url):
        parsed = urlparse(url or "")
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    @staticmethod
    def _find_existing_article_by_url(*, tenant, url):
        normalized_url = ArticleService._normalize_task_url(url)
        if not normalized_url:
            return None

        prefix = ArticleService._article_url_prefix(normalized_url)
        if not prefix:
            return None

        candidates = WechatArticle.objects.filter(tenant=tenant, url__startswith=prefix).order_by("-id")
        for candidate in candidates:
            if ArticleService._normalize_task_url(candidate.url) == normalized_url:
                return candidate
        return None

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
    def _build_article_defaults(*, feed, payload):
        return {
            "feed": feed,
            "source_id": ArticleService._truncate_char_field(payload.get("source_id", ""), 100),
            "article_type": payload.get("article_type", WechatArticle.ArticleType.NEWS),
            "title": ArticleService._truncate_char_field(payload.get("title", ""), 255),
            "description": payload.get("description", ""),
            "url": ArticleService._normalize_task_url(payload.get("url")),
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
        }

    @staticmethod
    def _existing_article_needs_backfill(existing):
        return existing.publish_time is None

    @staticmethod
    def upsert_article_from_payload(*, tenant, feed, payload, actor=None):
        defaults = ArticleService._build_article_defaults(feed=feed, payload=payload)
        existing = ArticleService._find_existing_article_by_url(tenant=tenant, url=defaults["url"])

        if existing is None:
            create_kwargs = {
                "tenant": tenant,
                "content": "",
                **defaults,
            }
            article = WechatArticle.objects.create(**create_kwargs)
            return article, True

        if not ArticleService._existing_article_needs_backfill(existing):
            return existing, False

        for field, value in defaults.items():
            setattr(existing, field, value)
        existing.save()
        if existing.content:
            ArticleService.enqueue_markdown_refresh(article_id=existing.id)
        return existing, False

    @staticmethod
    def enqueue_markdown_refresh(*, article_id):
        from we_rss.tasks import run_article_markdown_refresh_task

        dispatch_we_rss_task(run_article_markdown_refresh_task, article_id)

    @staticmethod
    def refresh_article_markdown(*, article, markdown_service=None, sleep_seconds=0.2, sleep_func=None):
        markdown_service = markdown_service or get_article_markdown_service()
        sleep_func = sleep_func or time.sleep
        if sleep_seconds and sleep_seconds > 0:
            sleep_func(sleep_seconds)
        markdown_content = str(markdown_service.fetch_markdown_from_url(article.url)).strip()
        if not markdown_content:
            raise ValueError("Article markdown content is empty.")
        article.content = markdown_content
        article.save(update_fields=["content", "updated_at"])
        return markdown_content

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

        dispatch_we_rss_task(run_article_import_task, task.id)
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
            article, _created = ArticleService.upsert_article_from_payload(
                tenant=task.tenant,
                feed=feed,
                payload=payload,
                actor=task.created_by,
            )
            if task.created_by is not None:
                MemberFeedSubscription.objects.get_or_create(
                    tenant=task.tenant,
                    member=task.created_by,
                    feed=feed,
                )

        ArticleService.enqueue_markdown_refresh(article_id=article.id)
        return {
            "message": "Article import complete",
            "article_id": article.id,
            "feed_id": feed.id,
            "source_id": article.source_id,
            "url": article.url,
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

        dispatch_we_rss_task(run_article_refresh_task, task.id)
        return task

    @staticmethod
    def execute_refresh_task(*, article, updated_by, gateway):
        credential = ArticleService._resolve_credential(tenant=article.tenant, feed=article.feed)
        payload = ArticleService._normalize_payload(gateway.refresh_article(article, credential))
        normalized_content = str(payload.get("content") or "").strip()
        if payload.get("status") == "deleted" or normalized_content == "DELETED":
            raise ValidationError("Wechat article is unavailable or has been deleted.")
        if not normalized_content:
            raise ValidationError("Wechat article content is empty.")

        with transaction.atomic():
            for field, value in ArticleService._build_article_defaults(feed=article.feed, payload=payload).items():
                setattr(article, field, value)
            article.last_refreshed_at = timezone.now()
            article.save()

        ArticleService.enqueue_markdown_refresh(article_id=article.id)
        return {
            "message": "Article refresh complete",
            "article_id": article.id,
            "title": article.title,
            "updated_by_id": getattr(updated_by, "id", None),
            "url": article.url,
        }

    @staticmethod
    def set_favorite_status(*, article, member, is_favorite):
        MemberArticleStateService.set_favorite(
            article=article,
            member=member,
            is_favorite=is_favorite,
        )
        article.is_favorite = is_favorite
        return article

    @staticmethod
    def _dedupe_article_ids(article_ids):
        ordered_ids = []
        seen = set()
        for article_id in article_ids or []:
            if article_id in seen:
                continue
            seen.add(article_id)
            ordered_ids.append(article_id)
        return ordered_ids

    @staticmethod
    def _build_article_ids_export_queryset(*, tenant, member, article_ids):
        ordered_ids = ArticleService._dedupe_article_ids(article_ids)
        queryset = ArticleVisibilityService.get_visible_article_queryset(
            tenant=tenant,
            member=member,
            queryset=WechatArticle.objects.filter(tenant=tenant, id__in=ordered_ids).select_related("feed"),
        )
        existing_ids = set(queryset.values_list("id", flat=True))
        missing_ids = [article_id for article_id in ordered_ids if article_id not in existing_ids]
        if missing_ids:
            raise ValidationError({"article_ids": [f"Articles not found in current member scope: {missing_ids}"]})

        order_expression = Case(
            *[When(pk=article_id, then=Value(index)) for index, article_id in enumerate(ordered_ids)],
            output_field=IntegerField(),
        )
        return queryset.order_by(order_expression, "-id")

    @staticmethod
    def batch_delete_articles(*, tenant, member, article_ids):
        ordered_ids = ArticleService._dedupe_article_ids(article_ids)
        queryset = ArticleVisibilityService.get_tenant_visible_article_queryset(
            tenant=tenant,
            member=member,
            queryset=WechatArticle.objects.filter(tenant=tenant, id__in=ordered_ids),
        )
        existing_ids = set(queryset.values_list("id", flat=True))
        missing_ids = [article_id for article_id in ordered_ids if article_id not in existing_ids]
        if missing_ids:
            raise ValidationError({"article_ids": [f"Articles not found in current tenant/article scope: {missing_ids}"]})

        MemberArticleStateService.bulk_hide_articles(
            tenant=tenant,
            member=member,
            article_ids=ordered_ids,
        )

        return {
            "deleted_count": len(ordered_ids),
            "article_ids": ordered_ids,
        }

    @staticmethod
    def _build_member_export_queryset(*, tenant, member_id):
        member = Member.objects.filter(tenant=tenant, id=member_id).first()
        if member is None:
            raise ValidationError({"member_id": ["Member not found in current tenant."]})

        return (
            ArticleVisibilityService.get_visible_article_queryset(
                tenant=tenant,
                member=member,
                queryset=WechatArticle.objects.filter(tenant=tenant).select_related("feed"),
            )
            .order_by("feed__mp_name", "feed_id", "-publish_time", "-id")
        )

    @staticmethod
    def _build_feed_export_queryset(*, tenant, member, feed_id):
        feed = WechatFeed.objects.filter(tenant=tenant, id=feed_id).first()
        if feed is None:
            raise ValidationError({"feed_id": ["Feed not found in current tenant."]})

        return (
            ArticleVisibilityService.get_visible_article_queryset(
                tenant=tenant,
                member=member,
                queryset=WechatArticle.objects.filter(tenant=tenant, feed_id=feed_id).select_related("feed"),
            )
            .order_by("-publish_time", "-id")
        )

    @staticmethod
    def _build_export_queryset(*, tenant, member, article_ids=None, member_id=None, feed_id=None):
        if article_ids:
            return "article_ids", ArticleService._build_article_ids_export_queryset(
                tenant=tenant,
                member=member,
                article_ids=article_ids,
            )
        if member_id is not None:
            return "member", ArticleService._build_member_export_queryset(tenant=tenant, member_id=member_id)
        return "feed", ArticleService._build_feed_export_queryset(tenant=tenant, member=member, feed_id=feed_id)

    @staticmethod
    def _build_export_filename(*, mode, article_ids=None, member_id=None, feed_id=None):
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        if mode == "article_ids":
            scope = f"selected_{len(ArticleService._dedupe_article_ids(article_ids))}"
        elif mode == "member":
            scope = f"member_{member_id}"
        else:
            scope = f"feed_{feed_id}"
        return f"we_rss_articles_{scope}_{timestamp}.csv"

    @staticmethod
    def export_articles_csv(*, tenant, member, article_ids=None, member_id=None, feed_id=None):
        mode, queryset = ArticleService._build_export_queryset(
            tenant=tenant,
            member=member,
            article_ids=article_ids,
            member_id=member_id,
            feed_id=feed_id,
        )
        filename = ArticleService._build_export_filename(
            mode=mode,
            article_ids=article_ids,
            member_id=member_id,
            feed_id=feed_id,
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write("\ufeff")

        writer = csv.writer(response)
        writer.writerow([column for column, _getter in ARTICLE_EXPORT_COLUMNS])
        for article in queryset.iterator():
            writer.writerow([getter(article) for _column, getter in ARTICLE_EXPORT_COLUMNS])
        return response
