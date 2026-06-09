from dataclasses import dataclass

from llm_gateway.services.model_factory import LLMGatewayModelFactory

try:
    from pydantic_ai import Agent
except ImportError:  # pragma: no cover - exercised indirectly through mocks in tests
    class Agent:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ImportError("pydantic-ai is required to stream direct model calls")


class DirectModelError(RuntimeError):
    """Base error for direct model streaming failures."""


class DirectModelConfigurationError(DirectModelError):
    """Raised when the direct model path cannot be configured."""


class DirectModelProviderError(DirectModelError):
    """Raised when the provider fails during direct model execution."""


@dataclass(frozen=True)
class DirectModelDeltaEvent:
    text: str


@dataclass(frozen=True)
class DirectModelResultEvent:
    output: object


class DirectModelService:
    @staticmethod
    def stream_structured(
        *,
        system_prompt,
        user_prompt,
        output_schema,
        requested_by_app,
        model_settings=None,
    ):
        try:
            model = LLMGatewayModelFactory.build_model()
            agent = Agent(
                model,
                output_type=output_schema,
                system_prompt=system_prompt,
                retries=1,
            )
        except Exception as exc:
            raise DirectModelConfigurationError(str(exc)) from exc

        try:
            streamed_result = agent.run_stream_sync(
                user_prompt,
                model_settings=model_settings,
            )
            if output_schema is str:
                for delta in streamed_result.stream_text(delta=True, debounce_by=None):
                    if delta:
                        yield DirectModelDeltaEvent(text=delta)
            yield DirectModelResultEvent(output=streamed_result.get_output())
        except DirectModelError:
            raise
        except Exception as exc:
            app_label = f" for {requested_by_app}" if requested_by_app else ""
            raise DirectModelProviderError(f"Direct model streaming failed{app_label}: {exc}") from exc
