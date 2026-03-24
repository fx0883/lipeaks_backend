import logging
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from we_rss.models import WechatSyncTask


logger = logging.getLogger(__name__)
_task_executor = ThreadPoolExecutor(max_workers=4)


def _run_task_in_background(task_func, *args, **kwargs):
    close_old_connections()
    try:
        if hasattr(task_func, "apply"):
            task_func.apply(args=args, kwargs=kwargs)
            return
        if hasattr(task_func, "run"):
            task_func.run(*args, **kwargs)
            return
        task_func(*args, **kwargs)
    except Exception:
        logger.exception("We RSS background task execution failed.")
    finally:
        close_old_connections()


def dispatch_we_rss_task(task_func, *args, **kwargs):
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        _run_task_in_background(task_func, *args, **kwargs)
        return None
    if getattr(settings, "CELERY_ENABLED", True):
        return task_func.delay(*args, **kwargs)
    return _task_executor.submit(_run_task_in_background, task_func, *args, **kwargs)


class TaskService:
    ACTIVE_STATUSES = [WechatSyncTask.Status.PENDING, WechatSyncTask.Status.RUNNING]

    @staticmethod
    def find_active_task(*, tenant, task_type, target_type="", target_id=None, task_key=""):
        queryset = WechatSyncTask.objects.filter(
            tenant=tenant,
            task_type=task_type,
            status__in=TaskService.ACTIVE_STATUSES,
        )
        if task_key:
            queryset = queryset.filter(task_key=task_key)
        else:
            queryset = queryset.filter(target_type=target_type)
            if target_id is not None:
                queryset = queryset.filter(target_id=target_id)
        return queryset.order_by("-created_at").first()

    @staticmethod
    def create_task(
        *,
        tenant,
        task_type,
        created_by,
        target_type="",
        target_id=None,
        task_key="",
        message="Task created.",
        request_payload=None,
    ):
        return WechatSyncTask.objects.create(
            tenant=tenant,
            task_type=task_type,
            status=WechatSyncTask.Status.PENDING,
            target_type=target_type,
            target_id=target_id,
            task_key=task_key,
            message=message,
            request_payload=request_payload,
            created_by=created_by,
        )

    @staticmethod
    def mark_running(task, *, celery_task_id=""):
        task.status = WechatSyncTask.Status.RUNNING
        task.started_at = task.started_at or timezone.now()
        if celery_task_id:
            task.celery_task_id = celery_task_id
        task.save(update_fields=["status", "started_at", "celery_task_id", "updated_at"])
        return task

    @staticmethod
    def mark_success(task, *, message="", result_payload=None, target_id=None):
        task.status = WechatSyncTask.Status.SUCCESS
        task.message = message or task.message
        task.result_payload = result_payload
        if target_id is not None:
            task.target_id = target_id
        task.finished_at = timezone.now()
        task.save(update_fields=["status", "message", "result_payload", "target_id", "finished_at", "updated_at"])
        return task

    @staticmethod
    def mark_failed(task, *, message="", result_payload=None):
        task.status = WechatSyncTask.Status.FAILED
        task.message = message or task.message
        task.result_payload = result_payload
        task.finished_at = timezone.now()
        task.save(update_fields=["status", "message", "result_payload", "finished_at", "updated_at"])
        return task
