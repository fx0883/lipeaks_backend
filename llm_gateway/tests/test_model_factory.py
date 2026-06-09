from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from llm_gateway.services.model_factory import LLMGatewayModelFactory


class LLMGatewayModelFactoryTests(SimpleTestCase):
    @override_settings(
        LLM_GATEWAY_AGENT_MODEL="openai:gpt-5.4",
        LLM_GATEWAY_AGENT_BASE_URL="",
        LLM_GATEWAY_AGENT_API_KEY="",
    )
    def test_returns_model_name_when_provider_override_is_empty(self):
        self.assertEqual(LLMGatewayModelFactory.build_model(), "openai:gpt-5.4")

    @override_settings(
        LLM_GATEWAY_AGENT_MODEL="openai:gpt-5.4",
        LLM_GATEWAY_AGENT_BASE_URL="https://example.com/v1",
        LLM_GATEWAY_AGENT_API_KEY="secret",
    )
    @patch("llm_gateway.services.model_factory.OpenAIProvider")
    @patch("llm_gateway.services.model_factory.OpenAIChatModel")
    def test_builds_openai_compatible_model_when_provider_override_exists(
        self,
        chat_model_cls,
        provider_cls,
    ):
        provider = Mock()
        model = Mock()
        provider_cls.return_value = provider
        chat_model_cls.return_value = model

        result = LLMGatewayModelFactory.build_model()

        self.assertIs(result, model)
        provider_cls.assert_called_once_with(
            base_url="https://example.com/v1",
            api_key="secret",
        )
        chat_model_cls.assert_called_once_with("gpt-5.4", provider=provider)
