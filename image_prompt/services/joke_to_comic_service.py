from collections.abc import Sequence
from textwrap import dedent

from image_prompt.schemas import (
    CharacterCandidate,
    ComicPlan,
    ComicPlanPanel,
    JokeToComicResult,
    PromptPackFormat,
    PromptPackPanel,
)
from llm_gateway.services.direct_model import (
    DirectModelDeltaEvent,
    DirectModelResultEvent,
    DirectModelService,
)


PANEL_COUNT = 4
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1440
PAGE_LAYOUT = "2x2"
DEFAULT_ART_STYLE = "黑白喜剧漫画"
DEFAULT_PANEL_ROLES = ["铺垫", "推进", "误导", "包袱"]
DEFAULT_NEGATIVE_PROMPT = (
    "低清晰度，模糊，脏灰对比，畸形人物，额外肢体，额外手指，坏手，扭曲面部，"
    "文字不可读，面板被裁切，分镜数量错误，构图松散，表情无力，水印，标志，签名，"
    "写实照片感，3D 渲染感"
)
DEFAULT_GENERATION_NOTES = [
    "四格中的人物外形、服装、道具和场景关键元素要保持一致。",
    "优先保证笑点节奏清晰，让最后一格的包袱落点明确。",
]
SYSTEM_PROMPT = dedent(
    """
    你是一名擅长把中文笑话改写成四格漫画脚本的喜剧编剧。
    输出必须严格是四格结构化结果，每一格都要能直接支持漫画绘制。
    """
).strip()


class JokeToComicService:
    @staticmethod
    def _normalize_confirmed_characters(
        confirmed_characters: Sequence[CharacterCandidate | dict] | None,
    ):
        if not confirmed_characters:
            return []

        return [
            item if isinstance(item, CharacterCandidate) else CharacterCandidate.model_validate(item)
            for item in confirmed_characters
        ]

    @staticmethod
    def _build_character_context(confirmed_characters):
        if not confirmed_characters:
            return ""

        lines = [
            (
                f"- {item.character_name}：{item.core_identity}；"
                f"外形：{item.visual_profile}；"
                f"性格：{item.personality_profile}；"
                f"说话方式：{item.speech_style}"
            )
            for item in confirmed_characters
        ]
        return "已确认角色：\n" + "\n".join(lines)

    @staticmethod
    def _normalize_plan(plan):
        normalized_panels = []
        for index, panel in enumerate(plan.panels[:PANEL_COUNT]):
            normalized_panels.append(
                ComicPlanPanel(
                    panel_number=index + 1,
                    role_in_joke=panel.role_in_joke.strip() or DEFAULT_PANEL_ROLES[index],
                    visual=panel.visual.strip() or "用夸张漫画表演强化笑点。",
                    dialogue=panel.dialogue.strip(),
                    caption=panel.caption.strip(),
                )
            )

        while len(normalized_panels) < PANEL_COUNT:
            index = len(normalized_panels)
            normalized_panels.append(
                ComicPlanPanel(
                    panel_number=index + 1,
                    role_in_joke=DEFAULT_PANEL_ROLES[index],
                    visual="补齐这一格，让笑点节奏完整清晰。",
                    dialogue="",
                    caption="",
                )
            )

        return ComicPlan(
            title=plan.title.strip() or "笑话四格提示词包",
            story_summary=plan.story_summary.strip() or "将原始笑话改写成四格误会喜剧。",
            humor_explanation=plan.humor_explanation.strip() or "笑点来自预期和真相的反差。",
            art_style=plan.art_style.strip() or DEFAULT_ART_STYLE,
            panels=normalized_panels,
        )

    @staticmethod
    def _fallback_plan_from_joke(joke):
        preview = joke.strip()[:120] or "一个发生在日常场景里的误会笑话。"
        return ComicPlan(
            title="笑话四格提示词包",
            story_summary="把笑话拆成铺垫、推进、误导、包袱四步节奏。",
            humor_explanation="通过最后一格揭晓真实含义，形成反转。",
            art_style=DEFAULT_ART_STYLE,
            panels=[
                ComicPlanPanel(panel_number=1, role_in_joke="铺垫", visual=f"建立场景与人物关系：{preview}"),
                ComicPlanPanel(panel_number=2, role_in_joke="推进", visual="把冲突推向关键问题。"),
                ComicPlanPanel(panel_number=3, role_in_joke="误导", visual="让误会进一步升级。"),
                ComicPlanPanel(panel_number=4, role_in_joke="包袱", visual="用明确画面揭晓真实含义。"),
            ],
        )

    @staticmethod
    def _build_panel_prompt(*, title, panel, art_style, character_context=""):
        character_block = (
            f"{character_context}\n如本格出现已确认角色，必须保持人设一致。\n"
            if character_context
            else ""
        )
        dialogue_line = (
            f"对话请自然放进对话气泡：{panel.dialogue}"
            if panel.dialogue
            else "这格以视觉叙事为主，不强行补额外对白。"
        )
        caption_line = (
            f"旁白或说明文字：{panel.caption}"
            if panel.caption
            else "如无必要，不额外加入旁白框。"
        )
        return dedent(
            f"""
            请绘制一张已完成的单格漫画插图，作品标题是《{title}》。
            输出尺寸必须明确为 {IMAGE_WIDTH}x{IMAGE_HEIGHT}，竖构图，适合作为四格漫画中的单独一格。
            这是第 {panel.panel_number} 格，共 {PANEL_COUNT} 格，这一格在笑话里的作用是：{panel.role_in_joke}。
            画面内容要求：{panel.visual}
            {character_block}{dialogue_line}
            {caption_line}
            人物表情要夸张清晰，肢体表演要服务笑点，构图要一眼就能读懂。
            画风要求：{art_style}，干净墨线，黑白分明，高完成度，可直接用于生图。
            """
        ).strip()

    @staticmethod
    def _build_page_prompt(*, title, panels, art_style, character_context=""):
        panel_lines = "\n".join(
            f"- 第 {panel.panel_number} 格（{panel.role_in_joke}）：{panel.visual}"
            for panel in panels
        )
        character_block = (
            f"{character_context}\n如已确认角色在本篇出现，请在四格中保持人设和语气一致。\n"
            if character_context
            else ""
        )
        return dedent(
            f"""
            请绘制一整页四格漫画，作品标题是《{title}》。
            整页必须包含且只包含 {PANEL_COUNT} 格，并且使用 {PAGE_LAYOUT} 排版，也就是 2x2 四宫格布局。
            整页需要完整呈现铺垫、推进、误导、包袱这四个笑点节奏，人物和道具在四格之间保持连续一致。
            四格内容如下：
            {panel_lines}
            {character_block}对话和旁白都要自然落在对应分镜中，但优先保证阅读顺畅与包袱落点明确。
            画风要求：{art_style}，黑白喜剧漫画，分镜清晰，整页完成度高。
            """
        ).strip()

    @staticmethod
    def build_result_from_plan(*, joke, plan, confirmed_characters, used_fallback):
        normalized_characters = JokeToComicService._normalize_confirmed_characters(
            confirmed_characters
        )
        normalized_plan = JokeToComicService._normalize_plan(plan)
        character_context = JokeToComicService._build_character_context(normalized_characters)

        panels = [
            PromptPackPanel(
                panel_number=panel.panel_number,
                role_in_joke=panel.role_in_joke,
                visual=panel.visual,
                dialogue=panel.dialogue,
                caption=panel.caption,
                image_prompt=JokeToComicService._build_panel_prompt(
                    title=normalized_plan.title,
                    panel=panel,
                    art_style=normalized_plan.art_style,
                    character_context=character_context,
                ),
            )
            for panel in normalized_plan.panels
        ]

        generation_notes = list(DEFAULT_GENERATION_NOTES)
        if normalized_characters:
            names = "、".join(item.character_name for item in normalized_characters)
            generation_notes.append(f"已注入确认角色设定：{names}。")
        if used_fallback:
            generation_notes.append("当前使用了 fallback 四格方案，建议在生图前再检查笑点是否贴合原笑话。")

        return JokeToComicResult(
            title=normalized_plan.title,
            source_joke=joke.strip(),
            format=PromptPackFormat(),
            story_summary=normalized_plan.story_summary,
            humor_explanation=normalized_plan.humor_explanation,
            negative_prompt=DEFAULT_NEGATIVE_PROMPT,
            generation_notes=generation_notes,
            panels=panels,
            page_prompt=JokeToComicService._build_page_prompt(
                title=normalized_plan.title,
                panels=normalized_plan.panels,
                art_style=normalized_plan.art_style,
                character_context=character_context,
            ),
        )

    @staticmethod
    def build_fallback_result(joke, *, confirmed_characters):
        return JokeToComicService.build_result_from_plan(
            joke=joke,
            plan=JokeToComicService._fallback_plan_from_joke(joke),
            confirmed_characters=confirmed_characters,
            used_fallback=True,
        )

    @staticmethod
    def _build_user_prompt(joke, confirmed_characters):
        character_context = JokeToComicService._build_character_context(confirmed_characters)
        return dedent(
            f"""
            请把下面这段笑话改写成适合单页四格漫画的结构化脚本。

            笑话：
            {joke.strip()}

            {character_context}
            要求：
            1. 必须输出四格。
            2. 每格都包含角色作用、画面、对白和旁白。
            3. 最后一格要让包袱明确落地。
            """
        ).strip()

    @staticmethod
    def stream_prompt_pack(*, joke, confirmed_characters=None):
        normalized_characters = JokeToComicService._normalize_confirmed_characters(
            confirmed_characters
        )
        yield {
            "event": "progress",
            "payload": {
                "stage": "planning_comic",
                "message": "正在规划四格漫画脚本",
            },
        }

        try:
            for event in DirectModelService.stream_structured(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=JokeToComicService._build_user_prompt(
                    joke,
                    normalized_characters,
                ),
                output_schema=ComicPlan,
                requested_by_app="image_prompt",
            ):
                if isinstance(event, DirectModelDeltaEvent):
                    yield {"event": "delta", "payload": {"text": event.text}}
                    continue

                if isinstance(event, DirectModelResultEvent):
                    yield {
                        "event": "completed",
                        "result": JokeToComicService.build_result_from_plan(
                            joke=joke,
                            plan=event.output,
                            confirmed_characters=normalized_characters,
                            used_fallback=False,
                        ),
                    }
                    return
        except Exception:
            pass

        yield {
            "event": "completed",
            "result": JokeToComicService.build_fallback_result(
                joke,
                confirmed_characters=normalized_characters,
            ),
        }
