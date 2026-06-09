import logging

from celery import shared_task
from django.utils import timezone

from we_rss.models import WechatArticle, WechatCredentialLoginSession, WechatFeed, WechatSyncTask
from we_rss.services.article_service import ArticleService, WechatArticleGateway
from we_rss.services.article_stats_service import ArticleStatsRefreshService
from we_rss.services.credential_service import CredentialService, WechatCredentialGateway
from we_rss.services.feed_service import FeedService, WechatFeedGateway
from we_rss.services.task_service import TaskService, dispatch_we_rss_task

logger = logging.getLogger(__name__)


def get_credential_gateway():
    return WechatCredentialGateway()


def get_feed_gateway():
    return WechatFeedGateway()


def get_article_gateway():
    return WechatArticleGateway()


def _apply_login_session_payload(login_session, payload):
    update_fields = []
    field_names = [
        "status",
        "qr_code_url",
        "qr_code_image",
        "scan_status",
        "token_snapshot",
        "cookie_snapshot",
        "error_message",
        "expired_at",
    ]
    for field_name in field_names:
        if field_name not in payload:
            continue
        setattr(login_session, field_name, payload[field_name])
        update_fields.append(field_name)
    if update_fields:
        login_session.save(update_fields=[*update_fields, "updated_at"])


def _mark_parent_run_after_batch_failure(*, parent_task, batch_task, feed, error):
    if parent_task is None or parent_task.status not in TaskService.ACTIVE_STATUSES:
        return

    parent_payload = dict(parent_task.result_payload or {})
    parent_payload.update(
        {
            "run_status": (
                WechatSyncTask.Status.PARTIAL_SUCCESS
                if int(parent_payload.get("batches_completed") or 0) > 0
                else WechatSyncTask.Status.FAILED
            ),
            "has_more": False,
            "current_batch_task_id": getattr(batch_task, "id", None) or parent_payload.get("current_batch_task_id"),
            "last_progress_at": timezone.now().isoformat(),
            "timeout_reason": "",
            "error": str(error),
            "batches_failed": int(parent_payload.get("batches_failed") or 0) + 1,
            "feed_id": feed.id,
        }
    )
    if parent_payload["run_status"] == WechatSyncTask.Status.PARTIAL_SUCCESS:
        TaskService.mark_partial_success(
            parent_task,
            message=f"Feed sync partially completed: {error}",
            result_payload=parent_payload,
        )
    else:
        TaskService.mark_failed(
            parent_task,
            message=f"Feed sync failed: {error}",
            result_payload=parent_payload,
        )


@shared_task(bind=True)
def run_credential_login_task(self, task_id):
    task = WechatSyncTask.objects.select_related("tenant", "created_by").get(pk=task_id)
    TaskService.mark_running(task, celery_task_id=self.request.id)
    login_session = WechatCredentialLoginSession.objects.select_related("credential", "tenant", "created_by").get(
        pk=task.target_id,
        tenant=task.tenant,
    )
    gateway = get_credential_gateway()
    try:
        def handle_status(update_payload):
            _apply_login_session_payload(login_session, update_payload)

        initialize_fn = getattr(gateway, "initialize_login_session", None)
        if initialize_fn is not None:
            try:
                init_payload = initialize_fn(login_session, on_status=handle_status)
            except TypeError as exc:
                if "on_status" not in str(exc):
                    raise
                init_payload = initialize_fn(login_session)
        else:
            init_payload = gateway.create_login_session()

        if init_payload:
            handle_status(init_payload)

        try:
            payload = gateway.wait_for_login(login_session, on_status=handle_status)
        except TypeError as exc:
            if "on_status" not in str(exc):
                raise
            payload = gateway.wait_for_login(login_session)
        _apply_login_session_payload(login_session, payload)

        if login_session.status == WechatCredentialLoginSession.Status.SUCCESS:
            credential = CredentialService.persist_credential_from_login_session(
                login_session=login_session,
                name=payload.get("credential_name"),
            )
            TaskService.mark_success(
                task,
                message="Credential login complete",
                result_payload={"credential_id": credential.id, "session_id": login_session.session_id},
            )
            return

        TaskService.mark_failed(
            task,
            message=payload.get("error_message") or "Credential login did not reach a success state.",
            result_payload={
                "session_id": login_session.session_id,
                "task_type": WechatSyncTask.TaskType.CREDENTIAL_LOGIN,
                "status": login_session.status,
                "error": payload.get("error_message", ""),
            },
        )
        return
    except Exception as exc:
        login_session.status = WechatCredentialLoginSession.Status.FAILED
        login_session.error_message = str(exc)
        login_session.save(update_fields=["status", "error_message", "updated_at"])
        TaskService.mark_failed(
            task,
            message=f"Credential login failed: {exc}",
            result_payload={
                "session_id": login_session.session_id,
                "task_type": WechatSyncTask.TaskType.CREDENTIAL_LOGIN,
                "status": WechatCredentialLoginSession.Status.FAILED,
                "error": str(exc),
            },
        )


@shared_task(bind=True)
def run_feed_sync_task(self, task_id):
    task = WechatSyncTask.objects.select_related("tenant", "created_by").get(pk=task_id)
    TaskService.mark_running(task, celery_task_id=self.request.id)
    feed = WechatFeed.objects.select_related("credential", "tenant").get(pk=task.target_id, tenant=task.tenant)
    gateway = get_feed_gateway()
    try:
        result = FeedService.execute_sync(feed=feed, updated_by=task.created_by, gateway=gateway)
        TaskService.mark_success(task, message=result.get("message", "Feed sync complete"), result_payload=result)
    except Exception as exc:
        TaskService.mark_failed(
            task,
            message=f"Feed sync failed: {exc}",
            result_payload={
                "feed_id": feed.id,
                "task_type": WechatSyncTask.TaskType.FEED_SYNC,
                "error": str(exc),
            },
        )


@shared_task(bind=True)
def run_feed_sync_batch_task(self, task_id):
    task = WechatSyncTask.objects.select_related("tenant", "created_by").get(pk=task_id)
    TaskService.mark_running(task, celery_task_id=self.request.id)
    parent_task_id = ((task.request_payload or {}).get("parent_task_id"))
    parent_task = None
    if parent_task_id is not None:
        parent_task = WechatSyncTask.objects.select_related("tenant", "created_by").filter(
            pk=parent_task_id,
            tenant=task.tenant,
        ).first()
    feed = WechatFeed.objects.select_related("credential", "tenant").get(pk=task.target_id, tenant=task.tenant)
    gateway = get_feed_gateway()
    try:
        result = FeedService.execute_sync_batch(
            task=task,
            parent_task=parent_task,
            feed=feed,
            updated_by=task.created_by,
            gateway=gateway,
        )
        next_batch_task_id = result.pop("next_batch_task_id", None)
        TaskService.mark_success(task, message=result.get("message", "Feed sync batch complete"), result_payload=result)
        if next_batch_task_id is not None:
            try:
                dispatch_we_rss_task(run_feed_sync_batch_task, next_batch_task_id)
            except Exception as exc:
                next_task = WechatSyncTask.objects.filter(
                    pk=next_batch_task_id,
                    tenant=task.tenant,
                ).first()
                if next_task is not None and next_task.status in TaskService.ACTIVE_STATUSES:
                    TaskService.mark_failed(
                        next_task,
                        message=f"Feed sync batch dispatch failed: {exc}",
                        result_payload={
                            "task_type": WechatSyncTask.TaskType.FEED_SYNC_BATCH,
                            "feed_id": feed.id,
                            "parent_task_id": parent_task_id,
                            "error": str(exc),
                        },
                    )
                _mark_parent_run_after_batch_failure(
                    parent_task=parent_task,
                    batch_task=next_task,
                    feed=feed,
                    error=exc,
                )
    except TimeoutError as exc:
        TaskService.mark_timed_out(
            task,
            message=f"Feed sync batch timed out: {exc}",
            result_payload={
                "task_type": WechatSyncTask.TaskType.FEED_SYNC_BATCH,
                "feed_id": feed.id,
                "parent_task_id": parent_task_id,
                "error": str(exc),
            },
        )
        if parent_task is not None and parent_task.status in TaskService.ACTIVE_STATUSES:
            parent_payload = dict(parent_task.result_payload or {})
            parent_payload["current_batch_task_id"] = task.id
            parent_payload["last_progress_at"] = timezone.now().isoformat()
            parent_payload["timeout_reason"] = "batch_timeout"
            parent_payload["batches_failed"] = int(parent_payload.get("batches_failed") or 0) + 1
            parent_payload["feed_id"] = feed.id
            if int(parent_payload.get("batches_completed") or 0) > 0:
                parent_payload["run_status"] = WechatSyncTask.Status.PARTIAL_SUCCESS
                TaskService.mark_partial_success(
                    parent_task,
                    message="Feed sync partially completed before timing out.",
                    result_payload=parent_payload,
                )
            else:
                parent_payload["run_status"] = WechatSyncTask.Status.TIMED_OUT
                TaskService.mark_timed_out(
                    parent_task,
                    message="Feed sync timed out before any batch completed.",
                    result_payload=parent_payload,
                )
    except Exception as exc:
        TaskService.mark_failed(
            task,
            message=f"Feed sync batch failed: {exc}",
            result_payload={
                "task_type": WechatSyncTask.TaskType.FEED_SYNC_BATCH,
                "feed_id": feed.id,
                "parent_task_id": parent_task_id,
                "error": str(exc),
            },
        )
        _mark_parent_run_after_batch_failure(
            parent_task=parent_task,
            batch_task=task,
            feed=feed,
            error=exc,
        )


@shared_task(bind=True)
def run_article_import_task(self, task_id):
    task = WechatSyncTask.objects.select_related("tenant", "created_by").get(pk=task_id)
    TaskService.mark_running(task, celery_task_id=self.request.id)
    gateway = get_article_gateway()
    try:
        result = ArticleService.execute_import_task(task=task, gateway=gateway)
        TaskService.mark_success(
            task,
            message=result.get("message", "Article import complete"),
            result_payload=result,
            target_id=result.get("article_id"),
        )
    except Exception as exc:
        TaskService.mark_failed(
            task,
            message=f"Article import failed: {exc}",
            result_payload={
                "task_type": WechatSyncTask.TaskType.ARTICLE_IMPORT,
                "url": ((task.request_payload or {}).get("url") or ""),
                "error": str(exc),
            },
        )


@shared_task(bind=True)
def run_article_refresh_task(self, task_id):
    task = WechatSyncTask.objects.select_related("tenant", "created_by").get(pk=task_id)
    TaskService.mark_running(task, celery_task_id=self.request.id)
    article = WechatArticle.objects.select_related("feed", "tenant").get(pk=task.target_id, tenant=task.tenant)
    gateway = get_article_gateway()
    try:
        result = ArticleService.execute_refresh_task(article=article, updated_by=task.created_by, gateway=gateway)
        TaskService.mark_success(task, message=result.get("message", "Article refresh complete"), result_payload=result)
    except Exception as exc:
        TaskService.mark_failed(
            task,
            message=f"Article refresh failed: {exc}",
            result_payload={
                "task_type": WechatSyncTask.TaskType.ARTICLE_REFRESH,
                "article_id": article.id,
                "error": str(exc),
            },
        )


@shared_task(bind=True)
def run_feed_content_refresh_task(self, task_id):
    task = WechatSyncTask.objects.select_related("tenant", "created_by").get(pk=task_id)
    TaskService.mark_running(task, celery_task_id=self.request.id)
    requested_article_ids = list(dict.fromkeys((task.request_payload or {}).get("article_ids") or []))
    feed_id = (task.request_payload or {}).get("feed_id")
    try:
        article_map = {
            article.id: article
            for article in WechatArticle.objects.select_related("feed", "tenant").filter(
                tenant=task.tenant,
                id__in=requested_article_ids,
            )
        }
        success_count = 0
        failed_articles = []

        for article_id in requested_article_ids:
            article = article_map.get(article_id)
            if article is None:
                failed_articles.append(
                    {
                        "article_id": article_id,
                        "url": "",
                        "error": "Article not found.",
                    }
                )
                continue

            try:
                markdown_content = ArticleService.refresh_article_markdown(article=article)
                if not markdown_content:
                    raise ValueError("Wechat article markdown content is empty.")
                success_count += 1
            except Exception as exc:
                failed_articles.append(
                    {
                        "article_id": article.id,
                        "url": article.url,
                        "error": str(exc),
                    }
                )

        TaskService.mark_success(
            task,
            message="Feed content refresh complete",
            result_payload={
                "task_type": WechatSyncTask.TaskType.FEED_CONTENT_REFRESH,
                "feed_id": feed_id,
                "requested_count": len(requested_article_ids),
                "success_count": success_count,
                "failed_count": len(failed_articles),
                "article_ids": requested_article_ids,
                "failed_articles": failed_articles,
            },
        )
    except Exception as exc:
        TaskService.mark_failed(
            task,
            message=f"Feed content refresh failed: {exc}",
            result_payload={
                "task_type": WechatSyncTask.TaskType.FEED_CONTENT_REFRESH,
                "feed_id": feed_id,
                "article_ids": requested_article_ids,
                "error": str(exc),
            },
        )


@shared_task(bind=True)
def run_article_stats_refresh_task(self, task_id):
    task = WechatSyncTask.objects.select_related("tenant", "created_by").get(pk=task_id)
    TaskService.mark_running(task, celery_task_id=self.request.id)
    request_payload = task.request_payload or {}
    selector_type = request_payload.get("selector_type") or "article_ids"
    try:
        requested_article_ids = ArticleStatsRefreshService.resolve_task_article_ids(
            tenant=task.tenant,
            member=task.created_by,
            request_payload=request_payload,
        )
        article_map = {
            article.id: article
            for article in WechatArticle.objects.select_related("feed", "tenant").filter(
                tenant=task.tenant,
                id__in=requested_article_ids,
            )
        }
        success_count = 0
        failed_articles = []

        for article_id in requested_article_ids:
            article = article_map.get(article_id)
            if article is None:
                failed_articles.append(
                    {
                        "article_id": article_id,
                        "url": "",
                        "error": "Article not found.",
                    }
                )
                continue

            try:
                ArticleStatsRefreshService.refresh_article_stats_for_article(article=article)
                success_count += 1
            except Exception as exc:
                failed_articles.append(
                    {
                        "article_id": article.id,
                        "url": article.url,
                        "error": str(exc),
                    }
                )

        TaskService.mark_success(
            task,
            message="Article stats refresh complete",
            result_payload={
                "task_type": WechatSyncTask.TaskType.ARTICLE_STATS_REFRESH,
                "selector_type": selector_type,
                "requested_count": len(requested_article_ids),
                "success_count": success_count,
                "failed_count": len(failed_articles),
                "article_ids": requested_article_ids,
                "failed_articles": failed_articles,
            },
        )
    except Exception as exc:
        TaskService.mark_failed(
            task,
            message=f"Article stats refresh failed: {exc}",
            result_payload={
                "task_type": WechatSyncTask.TaskType.ARTICLE_STATS_REFRESH,
                "selector_type": selector_type,
                "article_ids": request_payload.get("article_ids") or [],
                "error": str(exc),
            },
        )


@shared_task
def run_article_markdown_refresh_task(article_id):
    article = WechatArticle.objects.select_related("feed", "tenant").filter(pk=article_id).first()
    if article is None:
        return None
    try:
        return ArticleService.refresh_article_markdown(article=article)
    except ValueError as exc:
        logger.warning("We RSS article markdown refresh skipped: %s", exc, extra={"article_id": article_id})
        return None
    except Exception:
        logger.exception("We RSS article markdown refresh failed.", extra={"article_id": article_id})
        return None
