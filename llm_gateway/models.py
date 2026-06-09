from django.db import models

from llm_gateway.domain.enums import ExecutorType, RunStatus


class LLMRun(models.Model):
    capability = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=RunStatus.choices,
        default=RunStatus.PENDING,
    )
    preferred_executor = models.CharField(
        max_length=20,
        choices=ExecutorType.choices,
        default=ExecutorType.CODEX,
    )
    selected_executor = models.CharField(
        max_length=20,
        choices=ExecutorType.choices,
        blank=True,
        default="",
    )
    input_payload = models.JSONField()
    result_payload = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    exit_code = models.IntegerField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    requested_by_app = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, db_index=True)

    class Meta:
        db_table = "llm_gateway_run"
        ordering = ["-created_at"]


class LLMRunEvent(models.Model):
    run = models.ForeignKey(
        "llm_gateway.LLMRun",
        on_delete=models.CASCADE,
        related_name="events",
    )
    sequence = models.PositiveIntegerField()
    event_type = models.CharField(max_length=50)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, db_index=True)

    class Meta:
        db_table = "llm_gateway_run_event"
        ordering = ["sequence", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["run", "sequence"],
                name="llm_gateway_run_event_unique_sequence",
            ),
        ]
        indexes = [
            models.Index(fields=["run", "sequence"]),
            models.Index(fields=["event_type"]),
        ]

