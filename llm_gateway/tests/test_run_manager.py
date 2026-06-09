from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from llm_gateway.services.run_manager import RunManager


class RunManagerTests(TestCase):
    @patch("llm_gateway.services.run_manager.LLMGatewayAgentService")
    @patch("llm_gateway.services.run_manager.CodexExecutor")
    def test_executes_run_with_codex_first(self, codex_cls, agent_cls):
        agent_cls.build_instruction.return_value = Mock(
            selected_executor="codex",
            prompt="Use the wechat-article-search skill only.",
            used_skill="wechat-article-search",
        )
        codex_cls.return_value.run.return_value = Mock(
            stdout='{"items": [], "total": 0}',
            stderr="",
            exit_code=0,
            executor_name="codex",
        )

        run = RunManager.create_run(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills", "limit": 10},
        )
        completed = RunManager.execute_run(run.id)
        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.selected_executor, "codex")

    @override_settings(LLM_GATEWAY_FALLBACK_EXECUTOR="")
    def test_does_not_fallback_to_claude_when_fallback_executor_disabled(self):
        should_fallback = RunManager._should_fallback(
            selected_executor="codex",
            allowed_executors=["codex", "claude"],
        )

        self.assertFalse(should_fallback)
