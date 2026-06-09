from django.db import models


class ExecutorType(models.TextChoices):
    CODEX = "codex", "Codex"
    CLAUDE = "claude", "Claude"


class RunStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    TIMED_OUT = "timed_out", "Timed Out"

