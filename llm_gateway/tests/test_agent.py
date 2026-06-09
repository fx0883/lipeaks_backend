from pathlib import Path
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from llm_gateway.orchestration.agent import LLMGatewayAgentService


class LLMGatewayAgentServiceTests(SimpleTestCase):
    @patch("llm_gateway.orchestration.agent.Agent")
    def test_builds_executor_instruction_for_wechat_search(self, agent_cls):
        fake_agent = Mock()
        fake_agent.run_sync.return_value.output = {
            "prompt": "Use the wechat-article-search skill only.",
            "selected_executor": "codex",
            "output_mode": "json",
        }
        agent_cls.return_value = fake_agent

        instruction = LLMGatewayAgentService.build_instruction(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills", "limit": 10},
            allowed_executors=["codex", "claude"],
            preferred_executor="codex",
        )

        self.assertEqual(instruction.selected_executor, "codex")
        self.assertIn("wechat-article-search", instruction.prompt)

    @override_settings(
        LLM_GATEWAY_AGENT_MODEL="openai:gpt-4.1-mini",
        LLM_GATEWAY_AGENT_BASE_URL="https://cc-switch.example.com/v1",
        LLM_GATEWAY_AGENT_API_KEY="provider-key",
    )
    @patch("llm_gateway.orchestration.agent.OpenAIProvider")
    @patch("llm_gateway.orchestration.agent.OpenAIChatModel")
    @patch("llm_gateway.orchestration.agent.Agent")
    def test_builds_agent_with_explicit_openai_compatible_provider_config(
        self,
        agent_cls,
        openai_chat_model_cls,
        openai_provider_cls,
    ):
        fake_agent = Mock()
        fake_agent.run_sync.return_value.output = {
            "prompt": "Use the wechat-article-search skill only.",
            "selected_executor": "codex",
            "output_mode": "json",
        }
        agent_cls.return_value = fake_agent

        fake_provider = Mock()
        fake_model = Mock()
        openai_provider_cls.return_value = fake_provider
        openai_chat_model_cls.return_value = fake_model

        LLMGatewayAgentService.build_instruction(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills", "limit": 10},
            allowed_executors=["codex", "claude"],
            preferred_executor="codex",
        )

        openai_provider_cls.assert_called_once_with(
            base_url="https://cc-switch.example.com/v1",
            api_key="provider-key",
        )
        openai_chat_model_cls.assert_called_once_with(
            "gpt-4.1-mini",
            provider=fake_provider,
        )
        self.assertEqual(agent_cls.call_args.args[0], fake_model)

    @patch("llm_gateway.orchestration.agent.SkillCatalogService")
    @patch("llm_gateway.orchestration.agent.Agent")
    def test_builds_deterministic_wechat_search_command_prompt(self, agent_cls, catalog_cls):
        fake_agent = Mock()
        fake_agent.run_sync.return_value.output = {
            "prompt": "ignored-by-deterministic-builder",
            "selected_executor": "codex",
            "output_mode": "json",
        }
        agent_cls.return_value = fake_agent

        fake_skill = Mock()
        fake_skill.skill_path = Path(r"C:\Users\Administrator\.agents\skills\wechat-article-search")
        catalog_cls.get_skill.return_value = fake_skill

        instruction = LLMGatewayAgentService.build_instruction(
            capability="wechat_article_search",
            input_payload={"query": "AI Agent", "limit": 3},
            allowed_executors=["codex", "claude"],
            preferred_executor="codex",
        )

        self.assertIn("Run this exact shell command verbatim with no changes:", instruction.prompt)
        self.assertIn("search_wechat.js", instruction.prompt)
        self.assertIn("\"AI Agent\"", instruction.prompt)
        self.assertIn("-n 3", instruction.prompt)

    @patch("llm_gateway.orchestration.agent.SkillCatalogService")
    @patch("llm_gateway.orchestration.agent.Agent")
    def test_builds_single_line_verbatim_command_for_codex_executor_prompt(self, agent_cls, catalog_cls):
        fake_agent = Mock()
        fake_agent.run_sync.return_value.output = {
            "prompt": "ignored-by-deterministic-builder",
            "selected_executor": "codex",
            "output_mode": "json",
        }
        agent_cls.return_value = fake_agent

        fake_skill = Mock()
        fake_skill.skill_path = Path(r"C:\Users\Administrator\.agents\skills\wechat-article-search")
        catalog_cls.get_skill.return_value = fake_skill

        instruction = LLMGatewayAgentService.build_instruction(
            capability="wechat_article_search",
            input_payload={"query": "skill", "limit": 5},
            allowed_executors=["codex"],
            preferred_executor="codex",
        )

        self.assertIn(
            'Run this exact shell command verbatim with no changes: node "C:\\Users\\Administrator\\.agents\\skills\\wechat-article-search\\scripts\\search_wechat.js" "skill" -n 5',
            instruction.prompt,
        )

    @patch("llm_gateway.orchestration.agent.SkillCatalogService")
    @patch("llm_gateway.orchestration.agent.Agent")
    def test_builds_markdown_format_instruction_with_baoyu_skill(self, agent_cls, catalog_cls):
        fake_agent = Mock()
        fake_agent.run_sync.return_value.output = {
            "prompt": "ignored",
            "selected_executor": "codex",
            "used_skill": "baoyu-format-markdown",
            "output_mode": "text",
        }
        agent_cls.return_value = fake_agent
        catalog_cls.get_skill.return_value = Mock()

        instruction = LLMGatewayAgentService.build_instruction(
            capability="markdown_format",
            input_payload={"content": "# Title\nBody", "mode": "gentle"},
            allowed_executors=["codex", "claude"],
            preferred_executor="codex",
        )

        self.assertEqual(instruction.selected_executor, "codex")
        self.assertEqual(instruction.used_skill, "baoyu-format-markdown")
        self.assertIn("Markdown", instruction.prompt)
        self.assertIn("gentle", instruction.prompt)
        self.assertIn("non-interactive mode", instruction.prompt)
        self.assertIn("Do not ask for more input", instruction.prompt)
        self.assertIn("Do not inspect repository files", instruction.prompt)

    @patch("llm_gateway.orchestration.agent.SkillCatalogService")
    @patch("llm_gateway.orchestration.agent.Agent")
    def test_builds_markdown_format_instruction_without_agent_round_trip(self, agent_cls, catalog_cls):
        catalog_cls.get_skill.return_value = Mock()

        instruction = LLMGatewayAgentService.build_instruction(
            capability="markdown_format",
            input_payload={"content": "# Title\nBody", "mode": "gentle"},
            allowed_executors=["codex", "claude"],
            preferred_executor="codex",
        )

        agent_cls.assert_not_called()
        self.assertEqual(instruction.selected_executor, "codex")
        self.assertEqual(instruction.used_skill, "baoyu-format-markdown")
        self.assertEqual(instruction.output_mode, "text")
        self.assertIn("Input content:", instruction.prompt)
