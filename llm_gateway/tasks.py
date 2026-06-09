from celery import shared_task

from llm_gateway.repositories.runs import RunRepository
from llm_gateway.services.run_manager import RunManager


@shared_task(bind=True)
def execute_llm_run(self, run_id):
    request = getattr(self, "request", None)
    task_id = getattr(request, "id", "") if request else ""
    if task_id:
        run = RunRepository.get(run_id)
        run.celery_task_id = task_id
        run.save(update_fields=["celery_task_id", "updated_at"])
    return RunManager.execute_run(run_id)
