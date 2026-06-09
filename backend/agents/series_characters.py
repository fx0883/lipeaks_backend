from __future__ import annotations

import re
from textwrap import dedent

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from backend.config import settings
from backend.models import AnalyzeSeriesCharactersResponse, CharacterCandidate


TOOLING_ROLE_HINTS = {"前台", "服务员", "路人", "保安", "客户", "同事", "老板", "店员"}

SYSTEM_PROMPT = dedent(
    """
    你是一个中文系列漫画角色策划助手。
    任务是从用户提供的第一篇文案里，提取适合长期复用的系列主角候选，并把一次性功能角色单独归类。

    输出要求：
    - 全部使用中文。
    - recommended_main_characters 里优先给出最值得长期复用的核心主角候选。
    - temporary_characters 里放只服务当前文案、一次性工具位、路人或功能型角色。
    - 每个角色都必须写清楚角色身份、外观、性格、说话风格、关系、标志元素和完整角色提示词。
    - confidence_reason 必须解释为什么推荐这个角色进入系列，或者为什么它只是临时角色。
    - 不要输出空字段。
    - 如果文本里最明显的是双人关系，优先围绕双主角结构组织结果。
    """
).strip()


class SeriesCharacterAnalysisUnavailableError(RuntimeError):
    """Raised when series character analysis cannot run without a configured LLM."""


def _normalize_model_name(raw_model_name: str) -> str:
    if ":" not in raw_model_name:
        return raw_model_name.strip()
    _, model_name = raw_model_name.split(":", 1)
    return model_name.strip()


def _build_agent() -> Agent[None, AnalyzeSeriesCharactersResponse]:
    provider = OpenAIProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )
    model = OpenAIChatModel(
        _normalize_model_name(settings.llm_model),
        provider=provider,
    )
    return Agent(
        model,
        output_type=AnalyzeSeriesCharactersResponse,
        system_prompt=SYSTEM_PROMPT,
        retries=1,
    )


def _should_use_llm() -> bool:
    return bool(settings.llm_base_url and settings.llm_api_key)


def is_temporary_candidate(candidate: CharacterCandidate) -> bool:
    return (
        candidate.character_name in TOOLING_ROLE_HINTS
        or candidate.series_role == "临时角色"
        or "一次性" in candidate.confidence_reason
        or "临时角色" in candidate.confidence_reason
        or "工具角色" in candidate.confidence_reason
        or bool(re.search(r"(前台|店员|路人|服务员|保安|客户|同事|老板)", candidate.character_name))
    )


def _dedupe_candidates(candidates: list[CharacterCandidate]) -> list[CharacterCandidate]:
    deduped: list[CharacterCandidate] = []
    seen_names: set[str] = set()

    for candidate in candidates:
        normalized_name = candidate.character_name.strip()
        if not normalized_name or normalized_name in seen_names:
            continue
        deduped.append(candidate)
        seen_names.add(normalized_name)

    return deduped


def _finalize_analysis_result(
    raw_result: AnalyzeSeriesCharactersResponse,
    source_text: str,
    series_name: str = "",
) -> AnalyzeSeriesCharactersResponse:
    del source_text  # reserved for future tightening without changing the signature

    recommended = _dedupe_candidates(raw_result.recommended_main_characters)
    temporary = _dedupe_candidates(raw_result.temporary_characters)

    moved_to_temporary = [candidate for candidate in recommended if is_temporary_candidate(candidate)]
    recommended = [candidate for candidate in recommended if not is_temporary_candidate(candidate)]

    if moved_to_temporary:
        existing_names = {candidate.character_name for candidate in temporary}
        for candidate in moved_to_temporary:
            if candidate.character_name not in existing_names:
                temporary.append(candidate)
                existing_names.add(candidate.character_name)

    if len(recommended) < 2:
        raise SeriesCharacterAnalysisUnavailableError(
            "LLM 已返回结果，但可复用的核心主角少于 2 个，当前无法稳定完成系列主角分析。"
        )

    analysis_notes = list(raw_result.analysis_notes)
    if not analysis_notes:
        analysis_notes.append("LLM 已完成首话角色分析。")
    if moved_to_temporary:
        moved_names = "、".join(candidate.character_name for candidate in moved_to_temporary)
        analysis_notes.append(f"已将更像工具位的角色移入临时角色区：{moved_names}。")
    analysis_notes.append("默认优先保留 2 个核心主角进入首话确认流程。")
    if series_name.strip():
        analysis_notes.append(f"本次按系列《{series_name.strip()}》的首话启动模式处理。")

    return AnalyzeSeriesCharactersResponse(
        recommended_main_characters=recommended[:2],
        temporary_characters=temporary,
        analysis_notes=analysis_notes,
    )


def _run_llm_character_analysis(
    source_text: str,
    series_name: str = "",
) -> AnalyzeSeriesCharactersResponse:
    prompt = dedent(
        f"""
        请根据下面这段首话文案，提取系列主角候选并区分临时角色。

        系列名：{series_name.strip() or "未命名系列"}
        首话文案：
        {source_text.strip()}

        要求：
        - 优先找出最适合长期复用的主角。
        - 如果文案更像双人关系喜剧，优先围绕 2 个核心主角输出。
        - 不要把一次性服务角色、路人、工具位直接放进核心主角。
        - 给出结构化角色卡和完整角色提示词。
        """
    ).strip()
    result = _build_agent().run_sync(prompt)
    return result.output


def analyze_series_characters(
    source_text: str,
    series_name: str = "",
) -> AnalyzeSeriesCharactersResponse:
    if not _should_use_llm():
        raise SeriesCharacterAnalysisUnavailableError(
            "系列主角分析依赖 LLM。当前未配置 LLM 网关，无法分析角色候选。"
        )

    try:
        raw_result = _run_llm_character_analysis(source_text, series_name)
    except Exception as exc:  # pragma: no cover - specific provider failures vary
        raise SeriesCharacterAnalysisUnavailableError(
            f"LLM 系列主角分析失败：{exc}"
        ) from exc

    return _finalize_analysis_result(raw_result, source_text, series_name)
