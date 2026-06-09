from django.utils import timezone

from llm_gateway.domain.enums import RunStatus
from llm_gateway.models import LLMRun


class RunRepository:
    @staticmethod
    def create_run(
        *,
        capability,
        input_payload,
        preferred_executor="codex",
        requested_by_app="",
    ):
        return LLMRun.objects.create(
            capability=capability,
            input_payload=input_payload,
            preferred_executor=preferred_executor,
            requested_by_app=requested_by_app,
        )

    @staticmethod
    def get(run_id):
        return LLMRun.objects.get(pk=run_id)

    @staticmethod
    def mark_running(run, *, selected_executor="", celery_task_id=""):
        run.status = RunStatus.RUNNING
        run.started_at = run.started_at or timezone.now()
        if selected_executor:
            run.selected_executor = selected_executor
        if celery_task_id:
            run.celery_task_id = celery_task_id
        run.save(update_fields=["status", "started_at", "selected_executor", "celery_task_id", "updated_at"])
        return run

    @staticmethod
    def mark_completed(run, *, result_payload=None, exit_code=None):
        run.status = RunStatus.COMPLETED
        run.result_payload = result_payload
        run.exit_code = exit_code
        run.finished_at = timezone.now()
        run.duration_ms = RunRepository._calculate_duration_ms(run)
        run.save(update_fields=["status", "result_payload", "exit_code", "finished_at", "duration_ms", "updated_at"])
        return run

    @staticmethod
    def mark_failed(run, *, error_message="", result_payload=None, exit_code=None):
        run.status = RunStatus.FAILED
        run.error_message = error_message
        run.result_payload = result_payload
        run.exit_code = exit_code
        run.finished_at = timezone.now()
        run.duration_ms = RunRepository._calculate_duration_ms(run)
        run.save(
            update_fields=[
                "status",
                "error_message",
                "result_payload",
                "exit_code",
                "finished_at",
                "duration_ms",
                "updated_at",
            ]
        )
        return run

    @staticmethod
    def mark_cancelled(run, *, error_message=""):
        run.status = RunStatus.CANCELLED
        run.error_message = error_message
        run.finished_at = timezone.now()
        run.duration_ms = RunRepository._calculate_duration_ms(run)
        run.save(update_fields=["status", "error_message", "finished_at", "duration_ms", "updated_at"])
        return run

    @staticmethod
    def mark_timed_out(run, *, error_message=""):
        run.status = RunStatus.TIMED_OUT
        run.error_message = error_message
        run.finished_at = timezone.now()
        run.duration_ms = RunRepository._calculate_duration_ms(run)
        run.save(update_fields=["status", "error_message", "finished_at", "duration_ms", "updated_at"])
        return run

    @staticmethod
    def _calculate_duration_ms(run):
        if run.started_at is None or run.finished_at is None:
            return None
        duration = run.finished_at - run.started_at
        return int(duration.total_seconds() * 1000)

