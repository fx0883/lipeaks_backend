from django.conf import settings

from llm_gateway.executors.claude import ClaudeExecutor
from llm_gateway.executors.codex import CodexExecutor
from llm_gateway.orchestration.agent import LLMGatewayAgentService
from llm_gateway.repositories.events import EventRepository
from llm_gateway.repositories.runs import RunRepository
from llm_gateway.services.capability_router import CapabilityRouter
from llm_gateway.services.normalizer import ResultNormalizer


class RunManager:
    @staticmethod
    def create_run(*, capability, input_payload, requested_by_app=""):
        plan = CapabilityRouter.resolve(capability=capability, input_payload=input_payload)
        return RunRepository.create_run(
            capability=capability,
            input_payload=plan.input_payload,
            preferred_executor=plan.preferred_executor,
            requested_by_app=requested_by_app,
        )

    @staticmethod
    def execute_run(run_id):
        run = RunRepository.get(run_id)
        plan = CapabilityRouter.resolve(capability=run.capability, input_payload=run.input_payload)
        instruction = LLMGatewayAgentService.build_instruction(
            capability=run.capability,
            input_payload=run.input_payload,
            allowed_executors=plan.allowed_executors,
            preferred_executor=plan.preferred_executor,
        )

        RunRepository.mark_running(run, selected_executor=instruction.selected_executor)
        EventRepository.append(run, "run.started", {"executor": instruction.selected_executor})

        try:
            execution_result = RunManager._run_executor(
                executor_name=instruction.selected_executor,
                prompt=instruction.prompt,
                timeout_seconds=plan.timeout_seconds,
            )
        except Exception as exc:
            if RunManager._should_fallback(
                selected_executor=instruction.selected_executor,
                allowed_executors=plan.allowed_executors,
            ):
                execution_result = RunManager._run_executor(
                    executor_name="claude",
                    prompt=instruction.prompt,
                    timeout_seconds=plan.timeout_seconds,
                )
                run.selected_executor = "claude"
                run.save(update_fields=["selected_executor", "updated_at"])
            else:
                EventRepository.append(run, "run.failed", {"message": str(exc)})
                return RunRepository.mark_failed(run, error_message=str(exc))

        if execution_result.stdout:
            EventRepository.append(run, "executor.stdout", {"chunk": execution_result.stdout})
        if execution_result.stderr:
            EventRepository.append(run, "executor.stderr", {"chunk": execution_result.stderr})

        if execution_result.exit_code != 0:
            EventRepository.append(
                run,
                "run.failed",
                {"exit_code": execution_result.exit_code, "stderr": execution_result.stderr},
            )
            return RunRepository.mark_failed(
                run,
                error_message=execution_result.stderr or "Executor failed",
                exit_code=execution_result.exit_code,
            )

        normalized = ResultNormalizer.normalize(
            capability=run.capability,
            raw_stdout=execution_result.stdout,
            executor_name=execution_result.executor_name,
            used_skill=instruction.used_skill,
        )
        EventRepository.append(run, "run.completed", {"executor": execution_result.executor_name})
        return RunRepository.mark_completed(
            run,
            result_payload=normalized,
            exit_code=execution_result.exit_code,
        )

    @staticmethod
    def run_capability(*, capability, input_payload, requested_by_app=""):
        from llm_gateway.tasks import execute_llm_run

        run = RunManager.create_run(
            capability=capability,
            input_payload=input_payload,
            requested_by_app=requested_by_app,
        )

        if not getattr(settings, "CELERY_ENABLED", True):
            execute_llm_run.run(run.id)
        elif getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
            execute_llm_run.delay(run.id)
        else:
            async_result = execute_llm_run.delay(run.id)
            async_result.get(disable_sync_subtasks=False)

        return RunRepository.get(run.id).result_payload

    @staticmethod
    def _run_executor(*, executor_name, prompt, timeout_seconds):
        executor = RunManager._executor_for(executor_name)
        return executor.run(prompt=prompt, timeout_seconds=timeout_seconds)

    @staticmethod
    def _executor_for(executor_name):
        if executor_name == "codex":
            return CodexExecutor()
        if executor_name == "claude":
            return ClaudeExecutor()
        raise ValueError(f"Unsupported executor: {executor_name}")

    @staticmethod
    def _should_fallback(*, selected_executor, allowed_executors):
        fallback_executor = getattr(settings, "LLM_GATEWAY_FALLBACK_EXECUTOR", "")
        if not fallback_executor:
            return False
        return selected_executor == "codex" and fallback_executor in allowed_executors
