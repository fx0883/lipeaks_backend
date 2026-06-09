from textwrap import dedent

from image_prompt.schemas import AnalyzeSeriesCharactersResult, CharacterCandidate
from llm_gateway.services.direct_model import (
    DirectModelDeltaEvent,
    DirectModelResultEvent,
    DirectModelService,
)


TOOLING_ROLE_HINTS = {
    "前台",
    "服务员",
    "路人",
    "保安",
    "客户",
    "同事",
    "老板",
    "店员",
}
TOOLING_REASON_HINTS = ("一次性", "临时角色", "工具角色")

SYSTEM_PROMPT = dedent(
    """
    你是一个中文系列漫画角色策划助手。
    任务是从用户提供的首篇文本中，提取适合长期复用的系列核心角色，
    同时把一次性、工具型、路人型角色放入 temporary_characters。
    输出必须是结构化 JSON，并且所有字段都使用中文表达。
    """
).strip()


class SeriesCharacterAnalysisError(RuntimeError):
    """Raised when a valid reusable character roster cannot be produced."""


class SeriesCharacterService:
    @staticmethod
    def _build_user_prompt(source_text, series_name=""):
        return dedent(
            f"""
            请根据下面这段故事文本分析系列主角候选，并区分临时角色。

            系列名：{series_name.strip() or "未命名系列"}
            故事文本：
            {source_text.strip()}

            重点要求：
            1. 优先保留适合长期复用的核心角色。
            2. 不要把一次性工具角色、路人、服务型角色放进核心主角。
            3. 如文本明显更适合双主角结构，优先保留两个最强核心角色。
            4. 输出完整角色卡，包括身份、外观、性格、说话方式和角色提示词。
            """
        ).strip()

    @staticmethod
    def _is_temporary_candidate(candidate: CharacterCandidate) -> bool:
        return (
            candidate.character_name.strip() in TOOLING_ROLE_HINTS
            or candidate.series_role.strip() == "临时角色"
            or any(hint in candidate.confidence_reason for hint in TOOLING_REASON_HINTS)
            or any(hint in candidate.character_name for hint in TOOLING_ROLE_HINTS)
        )

    @staticmethod
    def _dedupe_candidates(candidates):
        deduped = []
        seen_names = set()

        for candidate in candidates:
            normalized_name = candidate.character_name.strip()
            if not normalized_name or normalized_name in seen_names:
                continue
            deduped.append(candidate.model_copy(update={"character_name": normalized_name}))
            seen_names.add(normalized_name)

        return deduped

    @staticmethod
    def finalize_result(raw_result, *, source_text, series_name=""):
        del source_text

        recommended = SeriesCharacterService._dedupe_candidates(
            raw_result.recommended_main_characters
        )
        temporary = SeriesCharacterService._dedupe_candidates(
            raw_result.temporary_characters
        )

        moved_to_temporary = [
            candidate
            for candidate in recommended
            if SeriesCharacterService._is_temporary_candidate(candidate)
        ]
        recommended = [
            candidate
            for candidate in recommended
            if not SeriesCharacterService._is_temporary_candidate(candidate)
        ]

        existing_names = {candidate.character_name for candidate in temporary}
        for candidate in moved_to_temporary:
            if candidate.character_name not in existing_names:
                temporary.append(candidate)
                existing_names.add(candidate.character_name)

        if len(recommended) < 2:
            raise SeriesCharacterAnalysisError("至少需要保留两个可复用的核心角色。")

        analysis_notes = list(raw_result.analysis_notes or [])
        if moved_to_temporary:
            moved_names = "、".join(candidate.character_name for candidate in moved_to_temporary)
            analysis_notes.append(f"已将工具型或一次性角色移入临时角色区：{moved_names}。")
        analysis_notes.append("默认优先保留两个最稳定的核心角色。")
        if series_name.strip():
            analysis_notes.append(f"本次分析按《{series_name.strip()}》首篇设定处理。")

        return AnalyzeSeriesCharactersResult(
            recommended_main_characters=recommended[:2],
            temporary_characters=temporary,
            analysis_notes=analysis_notes or ["已完成系列角色分析。"],
        )

    @staticmethod
    def stream_analysis(*, source_text, series_name=""):
        yield {
            "event": "progress",
            "payload": {
                "stage": "analyzing_characters",
                "message": "正在分析系列角色结构",
            },
        }

        for event in DirectModelService.stream_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=SeriesCharacterService._build_user_prompt(
                source_text,
                series_name,
            ),
            output_schema=AnalyzeSeriesCharactersResult,
            requested_by_app="image_prompt",
        ):
            if isinstance(event, DirectModelDeltaEvent):
                yield {
                    "event": "delta",
                    "payload": {"text": event.text},
                }
                continue

            if isinstance(event, DirectModelResultEvent):
                final_result = SeriesCharacterService.finalize_result(
                    event.output,
                    source_text=source_text,
                    series_name=series_name,
                )
                yield {
                    "event": "completed",
                    "result": final_result,
                }
