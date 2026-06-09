from pydantic import BaseModel, Field


class CharacterCandidate(BaseModel):
    character_name: str = Field(min_length=1, max_length=80)
    series_role: str = Field(min_length=1, max_length=80)
    core_identity: str = Field(min_length=1, max_length=300)
    visual_profile: str = Field(min_length=1, max_length=300)
    personality_profile: str = Field(min_length=1, max_length=300)
    speech_style: str = Field(min_length=1, max_length=200)
    relationship_to_others: str = ""
    signature_elements: list[str] = Field(default_factory=list)
    character_prompt: str = Field(min_length=1, max_length=1000)
    confidence_reason: str = Field(min_length=1, max_length=300)


class AnalyzeSeriesCharactersResult(BaseModel):
    recommended_main_characters: list[CharacterCandidate] = Field(
        min_length=2,
        max_length=4,
    )
    temporary_characters: list[CharacterCandidate] = Field(default_factory=list)
    analysis_notes: list[str] = Field(min_length=1)


class ComicPlanPanel(BaseModel):
    panel_number: int = Field(ge=1, le=4)
    role_in_joke: str
    visual: str
    dialogue: str = ""
    caption: str = ""


class ComicPlan(BaseModel):
    title: str
    story_summary: str
    humor_explanation: str
    art_style: str = "black-and-white comedy manga"
    panels: list[ComicPlanPanel] = Field(min_length=4, max_length=4)


class PromptPackFormat(BaseModel):
    panel_count: int = Field(default=4)
    image_width: int = Field(default=1080)
    image_height: int = Field(default=1440)
    page_layout: str = Field(default="2x2")


class PromptPackPanel(BaseModel):
    panel_number: int = Field(ge=1, le=4)
    role_in_joke: str
    visual: str
    dialogue: str = ""
    caption: str = ""
    image_prompt: str


class JokeToComicResult(BaseModel):
    title: str
    source_joke: str
    format: PromptPackFormat
    story_summary: str
    humor_explanation: str
    negative_prompt: str
    generation_notes: list[str] = Field(min_length=1)
    panels: list[PromptPackPanel] = Field(min_length=4, max_length=4)
    page_prompt: str
