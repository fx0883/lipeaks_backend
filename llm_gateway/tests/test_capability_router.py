from django.test import SimpleTestCase, override_settings

from llm_gateway.services.capability_router import CapabilityRouter


class CapabilityRouterTests(SimpleTestCase):
    @override_settings(
        LLM_GATEWAY_DEFAULT_EXECUTOR="codex",
        LLM_GATEWAY_FALLBACK_EXECUTOR="claude",
    )
    def test_wechat_article_search_prefers_codex(self):
        plan = CapabilityRouter.resolve(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills", "limit": 10},
        )
        self.assertEqual(plan.preferred_executor, "codex")
        self.assertIn("claude", plan.allowed_executors)
        self.assertEqual(plan.skill_hint, "wechat-article-search")

    @override_settings(LLM_GATEWAY_FALLBACK_EXECUTOR="")
    def test_wechat_article_search_filters_disabled_fallback_executor(self):
        plan = CapabilityRouter.resolve(
            capability="wechat_article_search",
            input_payload={"query": "AI Agent", "limit": 3},
        )

        self.assertEqual(plan.allowed_executors, ["codex"])

    @override_settings(
        LLM_GATEWAY_DEFAULT_EXECUTOR="codex",
        LLM_GATEWAY_FALLBACK_EXECUTOR="claude",
    )
    def test_markdown_format_prefers_codex_and_baoyu_skill(self):
        plan = CapabilityRouter.resolve(
            capability="markdown_format",
            input_payload={"content": "# Title\nBody", "mode": "gentle"},
        )

        self.assertEqual(plan.preferred_executor, "codex")
        self.assertIn("codex", plan.allowed_executors)
        self.assertEqual(plan.skill_hint, "baoyu-format-markdown")
