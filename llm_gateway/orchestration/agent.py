from pathlib import Path

from django.conf import settings
from pydantic import BaseModel

from llm_gateway.orchestration.prompts import (
    build_executor_system_prompt,
    build_markdown_format_executor_prompt,
    build_wechat_search_executor_prompt,
    build_wechat_search_prompt,
)
from llm_gateway.services.catalog import SkillCatalogService

try:
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider
except ImportError:  # pragma: no cover - exercised indirectly through mocks in tests
    class Agent:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ImportError("pydantic-ai is required to use LLMGatewayAgentService")

    class OpenAIProvider:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ImportError("pydantic-ai openai provider is required to use LLMGatewayAgentService")

    class OpenAIChatModel:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ImportError("pydantic-ai openai model support is required to use LLMGatewayAgentService")


class ExecutorInstruction(BaseModel):
    prompt: str
    selected_executor: str
    used_skill: str = "wechat-article-search"
    output_mode: str = "json"


class LLMGatewayAgentService:
    @staticmethod
    def _select_executor(*, allowed_executors, preferred_executor):
        if preferred_executor in allowed_executors:
            return preferred_executor
        if allowed_executors:
            return allowed_executors[0]
        raise ValueError("No allowed executors configured.")

    @staticmethod
    def _resolve_skill_script_path(skill_name):
        skill = SkillCatalogService.get_skill(skill_name)
        if skill is None:
            raise ValueError(f"Required skill is not available: {skill_name}")

        script_path = Path(skill.skill_path) / "scripts" / "search_wechat.js"
        if not script_path.exists():
            raise ValueError(f"Required skill script is not available: {script_path}")
        return script_path

    @staticmethod
    def _resolve_skill(skill_name):
        skill = SkillCatalogService.get_skill(skill_name)
        if skill is None:
            raise ValueError(f"Required skill is not available: {skill_name}")
        return skill

    @staticmethod
    def _build_deterministic_executor_prompt(*, capability, input_payload, used_skill):
        if capability == "wechat_article_search":
            script_path = LLMGatewayAgentService._resolve_skill_script_path(used_skill)
            return build_wechat_search_executor_prompt(
                script_path=script_path,
                query=input_payload["query"],
                limit=input_payload.get("limit", 10),
            )

        if capability == "markdown_format":
            LLMGatewayAgentService._resolve_skill(used_skill)
            return build_markdown_format_executor_prompt(
                content=input_payload["content"],
                mode=input_payload.get("mode", "gentle"),
            )

        raise ValueError(f"Unsupported capability: {capability}")

    @staticmethod
    def _resolve_agent_model():
        model_name = str(settings.LLM_GATEWAY_AGENT_MODEL).strip()
        base_url = str(getattr(settings, "LLM_GATEWAY_AGENT_BASE_URL", "") or "").strip()
        api_key = str(getattr(settings, "LLM_GATEWAY_AGENT_API_KEY", "") or "").strip()

        if not base_url and not api_key:
            return model_name

        normalized_model_name = model_name.split(":", 1)[1] if ":" in model_name else model_name
        provider = OpenAIProvider(
            base_url=base_url or None,
            api_key=api_key or None,
        )
        return OpenAIChatModel(
            normalized_model_name,
            provider=provider,
        )

    @staticmethod
    def build_instruction(*, capability, input_payload, allowed_executors, preferred_executor):
        if capability == "wechat_article_search":
            prompt = build_wechat_search_prompt(
                query=input_payload["query"],
                limit=input_payload.get("limit", 10),
                allowed_executors=allowed_executors,
                preferred_executor=preferred_executor,
            )
            default_skill = "wechat-article-search"
            default_output_mode = "json"
        elif capability == "markdown_format":
            # Markdown formatting already has a fixed skill and deterministic prompt,
            # so we can skip the extra orchestration model round-trip.
            selected_executor = LLMGatewayAgentService._select_executor(
                allowed_executors=allowed_executors,
                preferred_executor=preferred_executor,
            )
            used_skill = "baoyu-format-markdown"
            prompt = LLMGatewayAgentService._build_deterministic_executor_prompt(
                capability=capability,
                input_payload=input_payload,
                used_skill=used_skill,
            )
            return ExecutorInstruction(
                prompt=prompt,
                selected_executor=selected_executor,
                used_skill=used_skill,
                output_mode="text",
            )
        else:
            raise ValueError(f"Unsupported capability: {capability}")

        agent = Agent(
            LLMGatewayAgentService._resolve_agent_model(),
            output_type=ExecutorInstruction,
            instructions=build_executor_system_prompt(),
        )
        result = agent.run_sync(prompt)
        instruction = ExecutorInstruction.model_validate(result.output)

        if instruction.selected_executor not in allowed_executors:
            instruction = instruction.model_copy(update={"selected_executor": preferred_executor})

        if not instruction.used_skill:
            instruction = instruction.model_copy(update={"used_skill": default_skill})

        if not instruction.output_mode:
            instruction = instruction.model_copy(update={"output_mode": default_output_mode})

        instruction = instruction.model_copy(
            update={
                "prompt": LLMGatewayAgentService._build_deterministic_executor_prompt(
                    capability=capability,
                    input_payload=input_payload,
                    used_skill=instruction.used_skill,
                )
            }
        )

        return instruction
