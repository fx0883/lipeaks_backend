from django.http import StreamingHttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotAcceptable
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from image_prompt.schema import (
    ANALYZE_SERIES_CHARACTERS_REQUEST_EXAMPLE,
    JOKE_TO_COMIC_REQUEST_EXAMPLE,
    STREAMING_RESPONSE_DESCRIPTION,
    streaming_request,
    streaming_response,
)
from image_prompt.serializers import (
    AnalyzeSeriesCharactersRequestSerializer,
    JokeToComicRequestSerializer,
)
from image_prompt.services.joke_to_comic_service import JokeToComicService
from image_prompt.services.series_character_service import SeriesCharacterService
from image_prompt.services.sse import encode_sse_event


def _serialize_stream_result(result):
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result


class StreamingNegotiationAPIView(APIView):
    """
    Allow SSE clients to send `Accept: text/event-stream` while keeping
    pre-stream validation/auth errors on the existing JSON envelope.
    """

    def perform_content_negotiation(self, request, force=False):
        try:
            return super().perform_content_negotiation(request, force=force)
        except NotAcceptable:
            accept_header = request.META.get("HTTP_ACCEPT", "").lower()
            if "text/event-stream" not in accept_header:
                raise

            for renderer in self.get_renderers():
                if getattr(renderer, "media_type", "") == "application/json":
                    return renderer, renderer.media_type

            raise


class AnalyzeSeriesCharactersStreamView(StreamingNegotiationAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AnalyzeSeriesCharactersRequestSerializer

    @extend_schema(
        operation_id="image_prompt_analyze_series_characters",
        tags=["image-prompt"],
        summary="Analyze reusable series characters",
        description=STREAMING_RESPONSE_DESCRIPTION,
        request=streaming_request(
            AnalyzeSeriesCharactersRequestSerializer,
            name="Analyze series characters request",
            value=ANALYZE_SERIES_CHARACTERS_REQUEST_EXAMPLE,
            description="Submit one source story and an optional series name.",
        ),
        responses={(200, "text/event-stream"): streaming_response()},
    )
    def post(self, request, *args, **kwargs):
        serializer = AnalyzeSeriesCharactersRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def event_stream():
            yield encode_sse_event(
                "start",
                {"message": "Image prompt streaming started"},
            )

            try:
                for event in SeriesCharacterService.stream_analysis(
                    source_text=serializer.validated_data["source_text"],
                    series_name=serializer.validated_data.get("series_name", ""),
                ):
                    if event["event"] == "completed":
                        yield encode_sse_event(
                            "completed",
                            _serialize_stream_result(event["result"]),
                        )
                        continue

                    yield encode_sse_event(event["event"], event["payload"])
            except Exception as exc:
                yield encode_sse_event("error", {"message": str(exc)})

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        return response


class JokeToComicStreamView(StreamingNegotiationAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JokeToComicRequestSerializer

    @extend_schema(
        operation_id="image_prompt_joke_to_comic",
        tags=["image-prompt"],
        summary="Turn one joke into a comic prompt pack",
        description=STREAMING_RESPONSE_DESCRIPTION,
        request=streaming_request(
            JokeToComicRequestSerializer,
            name="Joke to comic request",
            value=JOKE_TO_COMIC_REQUEST_EXAMPLE,
            description="Submit one joke and optional locked character profiles.",
        ),
        responses={(200, "text/event-stream"): streaming_response()},
    )
    def post(self, request, *args, **kwargs):
        serializer = JokeToComicRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def event_stream():
            yield encode_sse_event(
                "start",
                {"message": "Image prompt streaming started"},
            )

            try:
                for event in JokeToComicService.stream_prompt_pack(
                    joke=serializer.validated_data["joke"],
                    confirmed_characters=serializer.validated_data.get(
                        "confirmed_characters",
                        [],
                    ),
                ):
                    if event["event"] == "completed":
                        yield encode_sse_event(
                            "completed",
                            _serialize_stream_result(event["result"]),
                        )
                        continue

                    yield encode_sse_event(event["event"], event["payload"])
            except Exception as exc:
                yield encode_sse_event("error", {"message": str(exc)})

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        return response
