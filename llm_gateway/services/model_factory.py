from django.conf import settings

try:
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider
except ImportError:  # pragma: no cover - exercised indirectly through mocks in tests
    class OpenAIProvider:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ImportError("pydantic-ai openai provider is required to build direct models")

    class OpenAIChatModel:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ImportError("pydantic-ai openai model support is required to build direct models")


class LLMGatewayModelFactory:
    @staticmethod
    def build_model():
        model_name = str(settings.LLM_GATEWAY_AGENT_MODEL).strip()
        base_url = str(getattr(settings, "LLM_GATEWAY_AGENT_BASE_URL", "") or "").strip()
        api_key = str(getattr(settings, "LLM_GATEWAY_AGENT_API_KEY", "") or "").strip()

        if not base_url and not api_key:
            return model_name

        normalized_model_name = model_name.split(":", 1)[1] if ":" in model_name else model_name
        provider = OpenAIProvider(
            base_url=base_url,
            api_key=api_key,
        )
        return OpenAIChatModel(normalized_model_name, provider=provider)
