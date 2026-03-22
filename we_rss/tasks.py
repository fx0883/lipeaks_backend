from celery import shared_task

from we_rss.models import WechatArticle, WechatCredentialLoginSession, WechatFeed, WechatSyncTask
from we_rss.services.article_service import ArticleService, WechatArticleGateway
from we_rss.services.credential_service import CredentialService, WechatCredentialGateway
from we_rss.services.feed_service import FeedService, WechatFeedGateway
from we_rss.services.task_service import TaskService


def get_credential_gateway():
    return WechatCredentialGateway()


def get_feed_gateway():
    return WechatFeedGateway()


def get_article_gateway():
    return WechatArticleGateway()


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
            login_session.status = update_payload.get("status", login_session.status)
            login_session.scan_status = update_payload.get("scan_status", login_session.scan_status)
            login_session.error_message = update_payload.get("error_message", login_session.error_message)
            login_session.token_snapshot = update_payload.get("token_snapshot", login_session.token_snapshot)
            login_session.cookie_snapshot = update_payload.get("cookie_snapshot", login_session.cookie_snapshot)
            login_session.save()

        try:
            payload = gateway.wait_for_login(login_session, on_status=handle_status)
        except TypeError as exc:
            if "on_status" not in str(exc):
                raise
            payload = gateway.wait_for_login(login_session)
        login_session.status = payload.get("status", login_session.status)
        login_session.scan_status = payload.get("scan_status", login_session.scan_status)
        login_session.token_snapshot = payload.get("token_snapshot", login_session.token_snapshot)
        login_session.cookie_snapshot = payload.get("cookie_snapshot", login_session.cookie_snapshot)
        login_session.error_message = payload.get("error_message", login_session.error_message)
        login_session.save()

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
