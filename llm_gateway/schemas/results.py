from pydantic import BaseModel, Field


class WechatArticleItem(BaseModel):
    title: str = ""
    url: str


class WechatArticleSearchResult(BaseModel):
    items: list[WechatArticleItem] = Field(default_factory=list)
    total: int = 0
    query: str = ""
    executor: str = ""
    used_skill: str = ""
    raw_text: str | None = None


class MarkdownFormatResult(BaseModel):
    formatted_markdown: str
    executor: str = ""
    used_skill: str = ""
    raw_text: str | None = None
