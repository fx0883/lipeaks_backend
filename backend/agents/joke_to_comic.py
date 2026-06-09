from __future__ import annotations

from collections.abc import Sequence
from textwrap import dedent
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from backend.config import settings
from backend.models import (
    CharacterCandidate,
    ComicPlan,
    ComicPlanPanel,
    JokeToComicResponse,
    PromptPackFormat,
    PromptPackPanel,
)


PANEL_COUNT = 4
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1440
PAGE_LAYOUT = "2x2"
DEFAULT_ART_STYLE = "黑白喜剧漫画"
DEFAULT_ROLES = ["铺垫", "推进", "误导", "包袱"]
DEFAULT_NEGATIVE_PROMPT = (
    "低清晰度，模糊，脏灰对比，畸形人物，额外肢体，额外手指，坏手，扭曲面部，"
    "文字不可读，面板被裁切，分镜数量错误，构图松散，表情无力，水印，标志，签名，"
    "写实照片感，3D 渲染感"
)
DEFAULT_GENERATION_NOTES = [
    "四格中的人物外形、服装、道具和场景关键元素要保持一致。",
    "优先保证笑点节奏清晰，让最后一格的包袱读起来干脆明确。",
]

SYSTEM_PROMPT = dedent(
    """
    你是一名擅长把中文笑话改写成四格漫画脚本的喜剧编剧。
    输出要求：
    - 必须返回且只返回 4 格。
    - 每一格都必须包含 panel_number、role_in_joke、visual、dialogue、caption。
    - role_in_joke 要明确对应喜剧节奏，例如：铺垫、推进、误导、包袱。
    - visual 必须足够具体，能直接支持漫画画面设计。
    - story_summary 用 1 到 2 句话说明整体改编思路。
    - humor_explanation 用 1 到 2 句话解释笑点为什么成立。
    - art_style 保持简洁，适合黑白喜剧漫画。
    - 默认使用中文表达，避免输出英文提示词。
    """
).strip()


def normalize_model_name(raw_model_name: str) -> str:
    if ":" not in raw_model_name:
        return raw_model_name.strip()
    _, model_name = raw_model_name.split(":", 1)
    return model_name.strip()


def _build_agent() -> Agent[None, ComicPlan]:
    provider = OpenAIProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )
    model = OpenAIChatModel(
        normalize_model_name(settings.llm_model),
        provider=provider,
    )
    return Agent(
        model,
        output_type=ComicPlan,
        system_prompt=SYSTEM_PROMPT,
        retries=1,
    )


def _normalize_panel(panel: ComicPlanPanel, index: int) -> ComicPlanPanel:
    role = panel.role_in_joke.strip() or DEFAULT_ROLES[index]
    visual = panel.visual.strip() or "画面要能清楚读出笑点节奏，人物表演要夸张明确。"
    return ComicPlanPanel(
        panel_number=index + 1,
        role_in_joke=role,
        visual=visual,
        dialogue=panel.dialogue.strip(),
        caption=panel.caption.strip(),
    )


def _normalize_plan(plan: ComicPlan) -> ComicPlan:
    normalized_panels = [
        _normalize_panel(panel, index)
        for index, panel in enumerate(plan.panels[:PANEL_COUNT])
    ]

    while len(normalized_panels) < PANEL_COUNT:
        index = len(normalized_panels)
        normalized_panels.append(
            ComicPlanPanel(
                panel_number=index + 1,
                role_in_joke=DEFAULT_ROLES[index],
                visual="用夸张的漫画表演补齐这一格，让节奏清楚可读。",
                dialogue="",
                caption="",
            )
        )

    return ComicPlan(
        title=plan.title.strip() or "笑话四格提示词包",
        story_summary=plan.story_summary.strip()
        or "把原始笑话拆成四步递进的漫画节奏，最后一格集中完成反转和包袱。",
        humor_explanation=plan.humor_explanation.strip()
        or "笑点来自读者先顺着常规理解走，再在结尾被真正含义迅速翻转。",
        art_style=plan.art_style.strip() or DEFAULT_ART_STYLE,
        panels=normalized_panels,
    )


def _fallback_plan_from_joke(joke: str) -> ComicPlan:
    joke_preview = joke.strip()[:120] or "一个发生在日常场景里的误会笑话。"
    return ComicPlan(
        title="笑话四格提示词包",
        story_summary="把笑话改写成四格误会喜剧：先交代背景，再抬高预期，接着制造误导，最后揭晓真正含义。",
        humor_explanation="笑点来自角色双方对同一句话的理解不一致，最后一格把误会瞬间说破。",
        art_style=DEFAULT_ART_STYLE,
        panels=[
            ComicPlanPanel(
                panel_number=1,
                role_in_joke="铺垫",
                visual=f"先把笑话发生的场景和人物关系交代清楚，用表情和道具埋下误会伏笔：{joke_preview}",
                dialogue="",
                caption="先建立一个看似正常的期待。",
            ),
            ComicPlanPanel(
                panel_number=2,
                role_in_joke="推进",
                visual="其中一人抛出关键问题，场面一下子认真起来，所有人都在等答案。",
                dialogue="你到底是怎么个情况？",
                caption="把读者注意力推到关键点上。",
            ),
            ComicPlanPanel(
                panel_number=3,
                role_in_joke="误导",
                visual="主角非常自信地回答，对方开始按最体面的方向理解这句话，误会迅速膨胀。",
                dialogue="当然有，而且还不止一个。",
                caption="让误会达到最高点。",
            ),
            ComicPlanPanel(
                panel_number=4,
                role_in_joke="包袱",
                visual="用一个一眼看懂的视觉揭示说明真正含义，旁人表情瞬间僵住或爆笑。",
                dialogue="我说的是仓库，不是房子。",
                caption="真相一出，包袱落地。",
            ),
        ],
    )


def generate_comic_plan(joke: str) -> tuple[ComicPlan, bool]:
    if settings.llm_base_url and settings.llm_api_key:
        try:
            prompt = dedent(
                f"""
                请把下面这段笑话改写成一个适合单页四格漫画的结构化脚本。
                笑话：
                {joke.strip()}

                要求：
                - 全部使用中文输出
                - 画面节奏清晰
                - 每一格都能支持漫画分镜
                - 最后一格包袱要落得明确
                """
            ).strip()
            result = _build_agent().run_sync(prompt)
            return _normalize_plan(result.output), False
        except Exception:
            pass

    return _fallback_plan_from_joke(joke), True


def _dialogue_instruction(dialogue: str) -> str:
    if not dialogue:
        return "这一格以视觉叙事为主，不要强行补充额外对话。"
    return f"对话请自然放进清晰可读的对话气泡中，内容是：{dialogue}"


def _caption_instruction(caption: str) -> str:
    if not caption:
        return "如无必要，不要额外加入旁白框。"
    return f"如果需要旁白框或说明文字，请使用这句简短中文：{caption}"


def _normalize_confirmed_characters(
    confirmed_characters: Sequence[CharacterCandidate | dict[str, Any]] | None,
) -> list[CharacterCandidate]:
    if not confirmed_characters:
        return []

    return [
        item
        if isinstance(item, CharacterCandidate)
        else CharacterCandidate.model_validate(item)
        for item in confirmed_characters
    ]


def _build_character_context(confirmed_characters: Sequence[CharacterCandidate]) -> str:
    if not confirmed_characters:
        return ""

    lines = [
        (
            f"- {item.character_name}：{item.core_identity}；外观：{item.visual_profile}；"
            f"性格：{item.personality_profile}；说话风格：{item.speech_style}"
        )
        for item in confirmed_characters
    ]
    return "已确认系列主角：\n" + "\n".join(lines)


def build_panel_prompt(
    *,
    title: str,
    panel: ComicPlanPanel,
    art_style: str,
    character_context: str = "",
) -> str:
    character_block = (
        f"{character_context}\n角色一致性要求：如本格出现系列主角，必须延续其已确认的人设。\n"
        if character_context
        else ""
    )
    return dedent(
        f"""
        请绘制一张已经完成的单格漫画插图，作品标题是《{title}》。
        输出尺寸必须明确为 {IMAGE_WIDTH}x{IMAGE_HEIGHT}，竖构图，适合作为四格漫画中的单独一格。
        这是第 {panel.panel_number} 格，共 {PANEL_COUNT} 格，这一格在笑话中的作用是：{panel.role_in_joke}。
        画面内容要求：{panel.visual}
        {character_block}{_dialogue_instruction(panel.dialogue)}
        {_caption_instruction(panel.caption)}
        人物表情要夸张清楚，肢体表演要服务笑点，构图要一眼就能读懂。
        画风要求：{art_style}，干净利落的墨线，清晰黑白层次，漫画网点质感，强表情，高完成度，可直接用于生图。
        """
    ).strip()


def build_page_prompt(
    *,
    title: str,
    panels: list[ComicPlanPanel],
    art_style: str,
    character_context: str = "",
) -> str:
    panel_lines = "\n".join(
        f"- 第 {panel.panel_number} 格（{panel.role_in_joke}）：{panel.visual}"
        for panel in panels
    )
    character_block = (
        f"{character_context}\n如已确认系列主角出现在本篇，请在四格中保持其人设和语气一致。\n"
        if character_context
        else ""
    )
    return dedent(
        f"""
        请绘制一整页四格漫画，作品标题是《{title}》。
        整页必须包含且只包含 {PANEL_COUNT} 格，并且使用 {PAGE_LAYOUT} 排版，也就是 2x2 四宫格布局，按从左到右、从上到下的顺序阅读。
        整页需要完整呈现铺垫、推进、误导、包袱这四个笑点节奏，人物与道具在四格之间保持连续一致。
        四格内容如下：
        {panel_lines}
        {character_block}对话和旁白都要自然地放进对应分镜，但优先保证整页阅读顺畅、节奏清晰、包袱落点明确。
        画风要求：{art_style}，黑白喜剧漫画，干净墨线，夸张表情，分镜清楚，整页完成度高，可直接用于漫画生图。
        """
    ).strip()


def _build_generation_notes(
    used_fallback: bool,
    confirmed_characters: Sequence[CharacterCandidate],
) -> list[str]:
    notes = list(DEFAULT_GENERATION_NOTES)
    if confirmed_characters:
        names = "、".join(item.character_name for item in confirmed_characters)
        notes.append(f"本篇已确认系列主角：{names}，生成提示词时已注入角色设定。")
    if used_fallback:
        notes.append("当前使用的是后备脚本，请在投喂图像模型前再检查一次措辞和笑点是否贴合你的原始笑话。")
    return notes


def _build_prompt_pack_from_plan(
    *,
    joke: str,
    plan: ComicPlan,
    used_fallback: bool,
    confirmed_characters: Sequence[CharacterCandidate],
) -> JokeToComicResponse:
    character_context = _build_character_context(confirmed_characters)
    prompt_panels = [
        PromptPackPanel(
            panel_number=panel.panel_number,
            role_in_joke=panel.role_in_joke,
            visual=panel.visual,
            dialogue=panel.dialogue,
            caption=panel.caption,
            image_prompt=build_panel_prompt(
                title=plan.title,
                panel=panel,
                art_style=plan.art_style,
                character_context=character_context,
            ),
        )
        for panel in plan.panels
    ]

    response = JokeToComicResponse(
        title=plan.title,
        source_joke=joke.strip(),
        format=PromptPackFormat(),
        story_summary=plan.story_summary,
        humor_explanation=plan.humor_explanation,
        negative_prompt=DEFAULT_NEGATIVE_PROMPT,
        generation_notes=_build_generation_notes(used_fallback, confirmed_characters),
        panels=prompt_panels,
        page_prompt=build_page_prompt(
            title=plan.title,
            panels=plan.panels,
            art_style=plan.art_style,
            character_context=character_context,
        ),
    )
    _validate_prompt_pack(response)
    return response


def _validate_prompt_pack(response: JokeToComicResponse) -> None:
    if response.format.panel_count != PANEL_COUNT:
        raise ValueError("panel_count 必须固定为 4")
    if len(response.panels) != PANEL_COUNT:
        raise ValueError("必须且只能返回 4 个分镜")
    if not response.page_prompt.strip():
        raise ValueError("page_prompt 不能为空")

    for panel in response.panels:
        if not panel.image_prompt.strip():
            raise ValueError(f"第 {panel.panel_number} 格缺少 image_prompt")
        if f"{IMAGE_WIDTH}x{IMAGE_HEIGHT}" not in panel.image_prompt:
            raise ValueError(
                f"第 {panel.panel_number} 格的 image_prompt 必须包含 {IMAGE_WIDTH}x{IMAGE_HEIGHT}"
            )


def build_prompt_pack(
    joke: str,
    confirmed_characters: Sequence[CharacterCandidate | dict[str, Any]] | None = None,
) -> JokeToComicResponse:
    plan, used_fallback = generate_comic_plan(joke)
    normalized_characters = _normalize_confirmed_characters(confirmed_characters)
    return _build_prompt_pack_from_plan(
        joke=joke,
        plan=plan,
        used_fallback=used_fallback,
        confirmed_characters=normalized_characters,
    )
