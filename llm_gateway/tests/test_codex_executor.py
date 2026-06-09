from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from llm_gateway.executors.codex import CodexExecutor
from llm_gateway.executors.process import ProcessRunResult


class CodexExecutorTests(SimpleTestCase):
    @override_settings(LLM_GATEWAY_CODEX_BIN="codex")
    def test_builds_codex_exec_command(self):
        command = CodexExecutor.build_command(
            prompt="Use the wechat-article-search skill only.",
            schema_path="C:/tmp/schema.json",
            output_path="C:/tmp/result.json",
        )
        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", command)
        self.assertIn("--output-schema", command)

    @override_settings(LLM_GATEWAY_CODEX_BIN="codex")
    def test_builds_codex_exec_command_with_stdin_prompt(self):
        command = CodexExecutor.build_command(
            prompt="Format this content",
            prompt_via_stdin=True,
        )

        self.assertEqual(command[-1], "-")

    @patch("llm_gateway.executors.codex.ProcessRunner.run")
    def test_runs_deterministic_wechat_search_command_directly(self, process_run):
        process_run.return_value = ProcessRunResult(
            stdout='{"query":"skill","total":1,"articles":[{"title":"Skill","url":"https://example.com"}]}',
            stderr="",
            exit_code=0,
            duration_ms=123,
        )

        result = CodexExecutor.run(
            prompt=(
                'Run this exact shell command verbatim with no changes: '
                'node "C:\\Users\\Administrator\\.agents\\skills\\wechat-article-search\\scripts\\search_wechat.js" "skill" -n 5\n\n'
                "After the command completes, print only the command stdout with no markdown fences "
                "and no extra commentary."
            ),
            timeout_seconds=30,
        )

        process_run.assert_called_once_with(
            [
                "node",
                r"C:\Users\Administrator\.agents\skills\wechat-article-search\scripts\search_wechat.js",
                "skill",
                "-n",
                "5",
            ],
            timeout_seconds=30,
            cwd=None,
        )
        self.assertEqual(result.executor_name, "codex")
        self.assertEqual(result.exit_code, 0)

    @patch("llm_gateway.executors.codex.ProcessRunner.run")
    @override_settings(LLM_GATEWAY_CODEX_BIN="codex")
    def test_runs_non_deterministic_prompt_via_stdin(self, process_run):
        process_run.return_value = ProcessRunResult(
            stdout="# Title\n\nBody",
            stderr="",
            exit_code=0,
            duration_ms=321,
        )

        result = CodexExecutor.run(
            prompt="Format markdown content",
            timeout_seconds=30,
        )

        process_run.assert_called_once_with(
            [
                "codex",
                "exec",
                "--dangerously-bypass-approvals-and-sandbox",
                "--skip-git-repo-check",
                "-",
            ],
            timeout_seconds=30,
            cwd=None,
            input_text="Format markdown content",
        )
        self.assertEqual(result.stdout, "# Title\n\nBody")
        self.assertEqual(result.executor_name, "codex")
