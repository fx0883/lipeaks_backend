from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.agents.joke_to_comic import build_prompt_pack
from backend.agents.series_characters import (
    SeriesCharacterAnalysisUnavailableError,
    analyze_series_characters,
)
from backend.config import settings
from backend.models import (
    AnalyzeSeriesCharactersRequest,
    AnalyzeSeriesCharactersResponse,
    JokeToComicRequest,
    JokeToComicResponse,
)


app = FastAPI(title="AIMangaStudio Quick API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/analyze-series-characters",
    response_model=AnalyzeSeriesCharactersResponse,
)
def analyze_series_characters_route(
    payload: AnalyzeSeriesCharactersRequest,
) -> AnalyzeSeriesCharactersResponse:
    try:
        return analyze_series_characters(payload.source_text, payload.series_name)
    except SeriesCharacterAnalysisUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/joke-to-comic", response_model=JokeToComicResponse)
def joke_to_comic(payload: JokeToComicRequest) -> JokeToComicResponse:
    return build_prompt_pack(payload.joke, payload.confirmed_characters)
