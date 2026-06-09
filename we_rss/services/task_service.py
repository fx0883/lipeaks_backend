import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from django.conf import settings
from django.db import close_old_connections
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from we_rss.models import WechatSyncTask


logger = logging.getLogger(__name__)
_task_executor = ThreadPoolExecutor(max_workers=4)


def _should_run_task_inline_on_submit_error(exc):
    if isinstance(exc, RuntimeError):
        error_message = str(exc)
        return (
            "cannot schedule new futures after shutdown" in error_message
            or "cannot schedule new futures after interpreter shutdown" in error_message
        )

    if isinstance(exc, OSError):
        return exc.errno == 22 and str(exc).strip() == "[Errno 22] Invalid argument"

    return False


def _run_task_inline(task_func, *args, **kwargs):
    if hasattr(task_func, "apply"):
        return task_func.apply(args=args, kwargs=kwargs)
    if hasattr(task_func, "run"):
        return task_func.run(*args, **kwargs)
    return task_func(*args, **kwargs)


def _run_task_in_background(task_func, *args, **kwargs):
    close_old_connections()
    try:
        _run_task_inline(task_func, *args, **kwargs)
    except Exception:
        logger.exception("We RSS background task execution failed.")
    finally:
        close_old_connections()


def dispatch_we_rss_task(task_func, *args, **kwargs):
    if not getattr(settings, "CELERY_ENABLED", True):
        try:
            return _task_executor.submit(_run_task_in_background, task_func, *args, **kwargs)
        except (RuntimeError, OSError) as exc:
            if not _should_run_task_inline_on_submit_error(exc):
                raise
            logger.warning(
                "We RSS background executor is shutting down; running task inline instead.",
                extra={"task_func": getattr(task_func, "__name__", str(task_func))},
            )
            return _run_task_inline(task_func, *args, **kwargs)

    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        _run_task_inline(task_func, *args, **kwargs)
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
        result_payload=None,
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
            result_payload=result_payload,
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

    @staticmethod
    def mark_partial_success(task, *, message="", result_payload=None):
        task.status = WechatSyncTask.Status.PARTIAL_SUCCESS
        task.message = message or task.message
        task.result_payload = result_payload
        task.finished_at = timezone.now()
        task.save(update_fields=["status", "message", "result_payload", "finished_at", "updated_at"])
        return task

    @staticmethod
    def mark_timed_out(task, *, message="", result_payload=None):
        task.status = WechatSyncTask.Status.TIMED_OUT
        task.message = message or task.message
        task.result_payload = result_payload
        task.finished_at = timezone.now()
        task.save(update_fields=["status", "message", "result_payload", "finished_at", "updated_at"])
        return task

    @staticmethod
    def get_last_progress_at(task):
        payload = task.result_payload or {}
        raw_value = payload.get("last_progress_at")
        if isinstance(raw_value, str):
            parsed_value = parse_datetime(raw_value)
            if parsed_value is not None:
                return parsed_value
        return task.started_at or task.updated_at or task.created_at

    @staticmethod
    def is_task_stale(task, *, stale_after_seconds):
        last_progress_at = TaskService.get_last_progress_at(task)
        if last_progress_at is None:
            return False
        return timezone.now() >= last_progress_at + timedelta(seconds=stale_after_seconds)
