from pydantic import BaseModel, Field


class RunEventPayload(BaseModel):
    event_type: str
    payload: dict = Field(default_factory=dict)
    sequence: int | None = None

