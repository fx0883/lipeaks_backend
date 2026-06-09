from dataclasses import dataclass

from django.conf import settings
from pydantic import BaseModel

from llm_gateway.schemas.requests import MarkdownFormatRequest, WechatArticleSearchRequest
from llm_gateway.schemas.results import MarkdownFormatResult, WechatArticleSearchResult


@dataclass(frozen=True)
class ExecutionPlan:
    capability: str
    input_payload: dict
    allowed_executors: list[str]
    preferred_executor: str
    streaming_enabled: bool
    timeout_seconds: int
    skill_hint: str
    result_schema: type[BaseModel]


class CapabilityRouter:
    @staticmethod
    def resolve(*, capability, input_payload):
        preferred_executor = settings.LLM_GATEWAY_DEFAULT_EXECUTOR
        fallback_executor = settings.LLM_GATEWAY_FALLBACK_EXECUTOR
        allowed_executors = [executor for executor in [preferred_executor, fallback_executor] if executor]

        if capability == "wechat_article_search":
            request = WechatArticleSearchRequest.model_validate(input_payload)
            return ExecutionPlan(
                capability=capability,
                input_payload=request.model_dump(),
                allowed_executors=allowed_executors,
                preferred_executor=preferred_executor,
                streaming_enabled=True,
                timeout_seconds=settings.LLM_GATEWAY_EXECUTION_TIMEOUT_SECONDS,
                skill_hint="wechat-article-search",
                result_schema=WechatArticleSearchResult,
            )

        if capability == "markdown_format":
            request = MarkdownFormatRequest.model_validate(input_payload)
            return ExecutionPlan(
                capability=capability,
                input_payload=request.model_dump(),
                allowed_executors=allowed_executors,
                preferred_executor=preferred_executor,
                streaming_enabled=False,
                timeout_seconds=settings.LLM_GATEWAY_EXECUTION_TIMEOUT_SECONDS,
                skill_hint="baoyu-format-markdown",
                result_schema=MarkdownFormatResult,
            )

        raise ValueError(f"Unsupported capability: {capability}")
