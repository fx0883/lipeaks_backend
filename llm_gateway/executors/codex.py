import re

from django.conf import settings

from llm_gateway.executors.base import BaseExecutor, ExecutorRunResult
from llm_gateway.executors.process import ProcessRunner


class CodexExecutor(BaseExecutor):
    executor_name = "codex"
    DETERMINISTIC_COMMAND_PREFIX = "Run this exact shell command verbatim with no changes: "
    DETERMINISTIC_WECHAT_COMMAND_PATTERN = re.compile(r'^node "([^"]+)" "(.*)" -n (\d+)$')

    @classmethod
    def build_command(cls, *, prompt, schema_path=None, output_path=None, prompt_via_stdin=False):
        command = [
            settings.LLM_GATEWAY_CODEX_BIN,
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "--skip-git-repo-check",
        ]
        if schema_path:
            command.extend(["--output-schema", schema_path])
        if output_path:
            command.extend(["--output-last-message", output_path])
        command.append("-" if prompt_via_stdin else prompt)
        return command

    @classmethod
    def _extract_direct_command(cls, prompt):
        if not prompt.startswith(cls.DETERMINISTIC_COMMAND_PREFIX):
            return None

        command_line = prompt[len(cls.DETERMINISTIC_COMMAND_PREFIX):].splitlines()[0].strip()
        match = cls.DETERMINISTIC_WECHAT_COMMAND_PATTERN.fullmatch(command_line)
        if not match:
            return None

        script_path, query, limit = match.groups()
        return ["node", script_path, query, "-n", limit]

    @classmethod
    def run(cls, *, prompt, timeout_seconds, cwd=None, schema_path=None, output_path=None):
        direct_command = cls._extract_direct_command(prompt)
        if direct_command is None:
            result = ProcessRunner.run(
                cls.build_command(
                    prompt=prompt,
                    schema_path=schema_path,
                    output_path=output_path,
                    prompt_via_stdin=True,
                ),
                timeout_seconds=timeout_seconds,
                cwd=cwd,
                input_text=prompt,
            )
            return ExecutorRunResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
                executor_name=cls.executor_name,
                duration_ms=result.duration_ms,
            )

        result = ProcessRunner.run(
            direct_command,
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
