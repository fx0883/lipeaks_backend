from unittest.mock import patch

from django.test import TestCase

from llm_gateway.services.gateway import LLMGatewayService


class LLMGatewayServiceTests(TestCase):
    @patch("llm_gateway.services.gateway.RunManager")
    def test_search_wechat_articles_hides_skill_details(self, run_manager):
        run_manager.run_capability.return_value = {
            "items": [{"title": "A", "url": "https://example.com"}],
            "total": 1,
            "executor": "codex",
            "used_skill": "wechat-article-search",
        }

        result = LLMGatewayService.search_wechat_articles(
            query="Claude Code skills",
            limit=10,
            requested_by_app="wechat",
        )

        self.assertEqual(result["total"], 1)
        self.assertNotIn("used_skill", result)

    @patch("llm_gateway.services.gateway.RunManager")
    def test_search_wechat_articles_returns_empty_result_when_run_failed(self, run_manager):
        run_manager.run_capability.return_value = None

        result = LLMGatewayService.search_wechat_articles(
            query="AI Agent",
            limit=3,
            requested_by_app="wechat",
        )

        self.assertEqual(result["query"], "AI Agent")
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["items"], [])

    @patch("llm_gateway.services.gateway.RunManager")
    def test_format_markdown_defaults_to_gentle_mode(self, run_manager):
        run_manager.run_capability.return_value = {
            "formatted_markdown": "# Title\n\nBody",
            "executor": "codex",
            "used_skill": "baoyu-format-markdown",
            "raw_text": "# Title\n\nBody",
        }

        result = LLMGatewayService.format_markdown(
            content="# Title\nBody",
            requested_by_app="we_rss",
        )

        self.assertEqual(result["formatted_markdown"], "# Title\n\nBody")

    @patch("llm_gateway.services.gateway.RunManager")
    def test_format_markdown_hides_skill_details(self, run_manager):
        run_manager.run_capability.return_value = {
            "formatted_markdown": "# Title\n\nBody",
            "executor": "codex",
            "used_skill": "baoyu-format-markdown",
            "raw_text": "# Title\n\nBody",
        }

        result = LLMGatewayService.format_markdown(
            content="# Title\nBody",
            mode="gentle",
            requested_by_app="we_rss",
        )

        self.assertEqual(result["executor"], "codex")
        self.assertNotIn("used_skill", result)
        self.assertNotIn("raw_text", result)
