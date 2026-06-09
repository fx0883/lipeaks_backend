from django.urls import path

from image_prompt.views import (
    AnalyzeSeriesCharactersStreamView,
    JokeToComicStreamView,
)


app_name = "image-prompt"


urlpatterns = [
    path(
        "analyze-series-characters/",
        AnalyzeSeriesCharactersStreamView.as_view(),
        name="analyze-series-characters",
    ),
    path(
        "joke-to-comic/",
        JokeToComicStreamView.as_view(),
        name="joke-to-comic",
    ),
]
