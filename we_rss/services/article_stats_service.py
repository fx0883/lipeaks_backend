import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from django.db.models import Case, IntegerField, Value, When
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import NotFound, ValidationError

from scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext import (
    collect_stats,
)
from users.models import Member
from we_rss.models import MemberFeedSubscription, WechatArticle, WechatFeed, WechatSyncTask
from we_rss.services.article_visibility_service import ArticleVisibilityService
from we_rss.services.task_service import TaskService, dispatch_we_rss_task
from we_rss.services.wechat_gateway import normalize_wechat_article_url

logger = logging.getLogger(__name__)

POC_STATS_FIELDS = (
    "read_num",
    "like_num",
    "old_like_num",
    "share_num",
    "collect_num",
    "comment_count",
    "comment_reply_count",
    "comment_total_count",
)
ARTICLE_STATS_UPDATE_FIELDS = (*POC_STATS_FIELDS, "publish_time")

POC_ROOT = Path(__file__).resolve().parents[2] / "scripts" / "lipeaks_viral_articles"
STATS_OUTPUT_DIR = POC_ROOT / "output" / "wechat-stats"
SESSION_FILE = STATS_OUTPUT_DIR / "session.json"
LIVE_LOG_FILE = STATS_OUTPUT_DIR / "proxy-live.log"


class ArticleStatsRefreshService:
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
    def ensure_stats_runtime_ready():
        missing_paths = [path.name for path in (SESSION_FILE, LIVE_LOG_FILE) if not path.exists()]
        if missing_paths:
            raise ValidationError(
                f"WeChat article stats runtime is not ready. Missing: {', '.join(missing_paths)}."
            )

    @staticmethod
    def _normalize_url(url):
        normalized_url = normalize_wechat_article_url(url)
        if normalized_url:
            return normalized_url
        return str(url or "").strip()

    @staticmethod
    def _article_url_prefix(url):
        parsed = urlparse(url or "")
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    @classmethod
    def _resolve_collectable_article_url(cls, *, article):
        normalized_url = cls._normalize_url(article.url)
        if normalized_url:
            return normalized_url
        raise ValidationError("Article URL is required for stats refresh.")

    @classmethod
    def _find_existing_article_by_url(cls, *, tenant, article_url, queryset=None):
        normalized_url = cls._normalize_url(article_url)
        if not normalized_url:
            return None

        prefix = cls._article_url_prefix(normalized_url)
        if not prefix:
            return None

        candidates = (queryset or WechatArticle.objects.all()).filter(
            tenant=tenant,
            url__startswith=prefix,
        ).order_by("-id")
        for candidate in candidates:
            if cls._normalize_url(candidate.url) == normalized_url:
                return candidate
        return None

    @staticmethod
    def _build_stats_updates(payload):
        updates = {}
        for field in ARTICLE_STATS_UPDATE_FIELDS:
            value = payload.get(field)
            if value is not None:
                if field == "publish_time" and isinstance(value, str):
                    parsed_value = parse_datetime(value)
                    if parsed_value is not None:
                        value = parsed_value
                updates[field] = value
        return updates

    @classmethod
    def _ensure_stats_payload_has_updates(cls, payload):
        if any(payload.get(field) is not None for field in POC_STATS_FIELDS):
            return

        message = "WeChat stats refresh failed: no stats returned."
        collector_error = str(payload.get("comment_reply_count_error") or "").strip()
        if collector_error:
            message = f"{message} Collector error: {collector_error}."
        raise ValidationError(message)

    @classmethod
    def _resolve_selected_article_ids(cls, *, tenant, member, article_ids):
        ordered_ids = cls._dedupe_article_ids(article_ids)
        if not ordered_ids:
            return []

        queryset = ArticleVisibilityService.get_visible_article_queryset(
            tenant=tenant,
            member=member,
            queryset=WechatArticle.objects.filter(tenant=tenant, id__in=ordered_ids),
        )
        existing_ids = set(queryset.values_list("id", flat=True))
        missing_ids = [article_id for article_id in ordered_ids if article_id not in existing_ids]
        if missing_ids:
            raise ValidationError({"article_ids": [f"Articles not found in current member scope: {missing_ids}"]})

        order_expression = Case(
            *[When(pk=article_id, then=Value(index)) for index, article_id in enumerate(ordered_ids)],
            output_field=IntegerField(),
        )
        return list(
            ArticleVisibilityService.get_visible_article_queryset(
                tenant=tenant,
                member=member,
                queryset=WechatArticle.objects.filter(tenant=tenant, id__in=ordered_ids),
            )
            .order_by(order_expression)
            .values_list("id", flat=True)
        )

    @staticmethod
    def _resolve_feed_article_ids(*, tenant, member, feed_id):
        feed = WechatFeed.objects.filter(tenant=tenant, id=feed_id).first()
        if feed is None:
            raise ValidationError({"feed_id": ["Feed not found in current tenant."]})

        return list(
            ArticleVisibilityService.get_tenant_visible_article_queryset(
                tenant=tenant,
                member=member,
                queryset=WechatArticle.objects.filter(tenant=tenant, feed_id=feed_id).exclude(status="deleted"),
            )
            .order_by(*WechatArticle._meta.ordering)
            .values_list("id", flat=True)
        )

    @staticmethod
    def _resolve_member_article_ids(*, tenant, member_id):
        member = Member.objects.filter(tenant=tenant, id=member_id).first()
        if member is None:
            raise ValidationError({"member_id": ["Member not found in current tenant."]})

        feed_ids = MemberFeedSubscription.objects.filter(
            tenant=tenant,
            member_id=member_id,
        ).values_list("feed_id", flat=True)
        return list(
            ArticleVisibilityService.get_visible_article_queryset(
                tenant=tenant,
                member=member,
                queryset=WechatArticle.objects.filter(tenant=tenant, feed_id__in=feed_ids),
            )
            .order_by(*WechatArticle._meta.ordering)
            .values_list("id", flat=True)
        )

    @classmethod
    def resolve_article_ids(cls, *, tenant, member, article_ids=None, feed_id=None, member_id=None):
        selectors = [
            bool(article_ids),
            feed_id is not None,
            member_id is not None,
        ]
        if sum(selectors) != 1:
            raise ValidationError("Provide exactly one of article_ids, feed_id, or member_id.")

        if article_ids:
            return cls._resolve_selected_article_ids(tenant=tenant, member=member, article_ids=article_ids)
        if feed_id is not None:
            return cls._resolve_feed_article_ids(tenant=tenant, member=member, feed_id=feed_id)
        return cls._resolve_member_article_ids(tenant=tenant, member_id=member_id)

    @classmethod
    def get_articles_for_refresh(cls, *, tenant, member, article_ids=None, feed_id=None, member_id=None):
        resolved_article_ids = cls.resolve_article_ids(
            tenant=tenant,
            member=member,
            article_ids=article_ids,
            feed_id=feed_id,
            member_id=member_id,
        )
        if not resolved_article_ids:
            return []

        article_map = {
            article.id: article
            for article in WechatArticle.objects.select_related("feed", "tenant").filter(
                tenant=tenant,
                id__in=resolved_article_ids,
            )
        }
        return [article_map[article_id] for article_id in resolved_article_ids if article_id in article_map]

    @staticmethod
    def build_article_log_payload(*, article, index, total, status, error=""):
        progress = 100 if total <= 0 else round(index * 100 / total, 2)
        return {
            "index": index,
            "total": total,
            "progress": progress,
            "status": status,
            "article_id": article.id,
            "source_id": article.source_id,
            "title": article.title,
            "url": article.url,
            "read_num": article.read_num,
            "like_num": article.like_num,
            "old_like_num": article.old_like_num,
            "share_num": article.share_num,
            "collect_num": article.collect_num,
            "comment_count": article.comment_count,
            "comment_reply_count": article.comment_reply_count,
            "comment_total_count": article.comment_total_count,
            "last_refreshed_at": article.last_refreshed_at.isoformat() if article.last_refreshed_at else None,
            "error": error,
        }

    @staticmethod
    def log_refresh_progress(payload):
        message = (
            "We RSS article stats refresh progress: "
            f"{payload.get('index')}/{payload.get('total')} "
            f"{payload.get('status')} "
            f"article_id={payload.get('article_id')} "
            f"source_id={payload.get('source_id')} "
            f"title={payload.get('title')} "
            f"url={payload.get('url')} "
            f"error={payload.get('error') or ''}"
        )
        logger.info(message)
        try:
            print(message)
        except (OSError, UnicodeEncodeError):
            logger.warning("We RSS article stats refresh stdout print skipped.")

    @classmethod
    def resolve_task_article_ids(cls, *, tenant, member, request_payload):
        payload = request_payload or {}
        selector_type = payload.get("selector_type") or "article_ids"
        if member is None:
            raise ValidationError("Task creator is required to resolve article stats refresh scope.")

        if selector_type == "feed_id":
            return cls.resolve_article_ids(
                tenant=tenant,
                member=member,
                feed_id=payload.get("feed_id"),
            )
        if selector_type == "member_id":
            return cls.resolve_article_ids(
                tenant=tenant,
                member=member,
                member_id=payload.get("member_id"),
            )
        return cls.resolve_article_ids(
            tenant=tenant,
            member=member,
            article_ids=payload.get("article_ids") or [],
        )

    @staticmethod
    def determine_selector_type(*, article_ids=None, feed_id=None, member_id=None):
        if article_ids:
            return "article_ids"
        if feed_id is not None:
            return "feed_id"
        return "member_id"

    @staticmethod
    def _build_task_key(*, article_ids=None, feed_id=None, member_id=None):
        if feed_id is not None:
            scope = f"feed:{feed_id}"
        elif member_id is not None:
            scope = f"member:{member_id}"
        else:
            digest = hashlib.sha1(",".join(str(article_id) for article_id in article_ids or []).encode("utf-8")).hexdigest()
            scope = f"article_ids:{digest}"
        return f"article_stats_refresh:{scope}"

    @classmethod
    def get_article_for_refresh_by_url(cls, *, tenant, member, article_url):
        visible_queryset = ArticleVisibilityService.get_visible_article_queryset(
            tenant=tenant,
            member=member,
            queryset=WechatArticle.objects.filter(tenant=tenant),
        )
        article = cls._find_existing_article_by_url(
            tenant=tenant,
            article_url=article_url,
            queryset=visible_queryset,
        )
        if article is None:
            raise NotFound("Article not found.")
        return article

    @classmethod
    def refresh_article_stats_by_url(cls, *, tenant, member, article_url):
        article = cls.get_article_for_refresh_by_url(
            tenant=tenant,
            member=member,
            article_url=article_url,
        )
        return cls.refresh_article_stats_for_article(article=article)

    @classmethod
    def refresh_article_stats_for_article(cls, *, article):
        cls.ensure_stats_runtime_ready()
        collectable_url = cls._resolve_collectable_article_url(article=article)
        try:
            result = collect_stats(
                article_url=collectable_url,
                session_file=SESSION_FILE,
                live_log_file=LIVE_LOG_FILE,
            )
        except RuntimeError as exc:
            raise ValidationError(str(exc)) from exc
        cls._ensure_stats_payload_has_updates(result)
        updates = cls._build_stats_updates(result)

        with transaction.atomic():
            for field, value in updates.items():
                setattr(article, field, value)
            article.last_refreshed_at = timezone.now()
            article.save(update_fields=[*updates.keys(), "last_refreshed_at", "updated_at"])

        return article

    @classmethod
    def enqueue_batch_refresh(cls, *, tenant, created_by, article_ids=None, feed_id=None, member_id=None):
        selector_type = cls.determine_selector_type(
            article_ids=article_ids,
            feed_id=feed_id,
            member_id=member_id,
        )
        resolved_article_ids = cls.resolve_article_ids(
            tenant=tenant,
            member=created_by,
            article_ids=article_ids,
            feed_id=feed_id,
            member_id=member_id,
        )
        task_key = cls._build_task_key(
            article_ids=resolved_article_ids,
            feed_id=feed_id,
            member_id=member_id,
        )
        active_task = TaskService.find_active_task(
            tenant=tenant,
            task_type=WechatSyncTask.TaskType.ARTICLE_STATS_REFRESH,
            task_key=task_key,
        )
        if active_task is not None:
            return active_task

        task = TaskService.create_task(
            tenant=tenant,
            task_type=WechatSyncTask.TaskType.ARTICLE_STATS_REFRESH,
            created_by=created_by,
            target_type="article_stats",
            task_key=task_key,
            message="Article stats refresh task created.",
            request_payload={
                "selector_type": selector_type,
                "article_ids": resolved_article_ids,
                "feed_id": feed_id,
                "member_id": member_id,
            },
        )
        from we_rss.tasks import run_article_stats_refresh_task

        dispatch_we_rss_task(run_article_stats_refresh_task, task.id)
        return task
