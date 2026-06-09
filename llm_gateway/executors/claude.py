from pathlib import Path

from django.conf import settings

from llm_gateway.executors.base import BaseExecutor


class ClaudeExecutor(BaseExecutor):
    executor_name = "claude"

    @classmethod
    def build_command(cls, *, prompt, schema_path=None, output_path=None):
        command = [
            settings.LLM_GATEWAY_CLAUDE_BIN,
            "-p",
            "--output-format",
            "json",
            "--no-session-persistence",
        ]
        if schema_path:
            command.extend(["--json-schema", cls._schema_argument(schema_path)])
        command.append(prompt)
        return command

    @staticmethod
    def _schema_argument(schema_path):
        path = Path(schema_path)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return schema_path
