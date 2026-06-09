from django.apps import apps
from django.conf import settings
from django.test import TestCase


class LLMGatewayBootstrapTests(TestCase):
    def test_llm_gateway_is_registered_with_defaults(self):
        self.assertTrue(apps.is_installed("llm_gateway"))
        self.assertEqual(settings.LLM_GATEWAY_DEFAULT_EXECUTOR, "codex")
        self.assertEqual(settings.LLM_GATEWAY_FALLBACK_EXECUTOR, "claude")
        self.assertEqual(settings.LLM_GATEWAY_AGENT_BASE_URL, "")
        self.assertEqual(settings.LLM_GATEWAY_AGENT_API_KEY, "")
        self.assertIn(
            r"C:\Users\Administrator\.agents\skills",
            settings.LLM_GATEWAY_SKILL_DIRS,
        )
