from pydantic import BaseModel, Field, field_validator


class WechatArticleSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)


class MarkdownFormatRequest(BaseModel):
    content: str = Field(min_length=1)
    mode: str = Field(default="gentle")

    @field_validator("content")
    @classmethod
    def validate_content(cls, value):
        value = str(value or "").strip()
        if not value:
            raise ValueError("Content must not be blank.")
        return value

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value):
        value = str(value or "").strip() or "gentle"
        if value != "gentle":
            raise ValueError("Only gentle mode is supported.")
        return value
