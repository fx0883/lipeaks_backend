from dataclasses import dataclass

from llm_gateway.executors.process import ProcessRunner


@dataclass(frozen=True)
class ExecutorRunResult:
    stdout: str
    stderr: str
    exit_code: int
    executor_name: str
    duration_ms: int


class BaseExecutor:
    executor_name = ""
    command_setting_name = ""

    @classmethod
    def run(cls, *, prompt, timeout_seconds, cwd=None, schema_path=None, output_path=None):
        result = ProcessRunner.run(
            cls.build_command(
                prompt=prompt,
                schema_path=schema_path,
                output_path=output_path,
            ),
            timeout_seconds=timeout_seconds,
            cwd=cwd,
        )
        return ExecutorRunResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            executor_name=cls.executor_name,
            duration_ms=result.duration_ms,
        )

