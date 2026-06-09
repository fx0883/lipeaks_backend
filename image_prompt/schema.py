from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiRequest, OpenApiResponse


ANALYZE_SERIES_CHARACTERS_REQUEST_EXAMPLE = {
    "source_text": "深夜加班的产品经理和工程师又因为一个需求吵了起来。",
    "series_name": "办公室连载",
}

JOKE_TO_COMIC_REQUEST_EXAMPLE = {
    "joke": "产品经理说这个需求很简单，工程师看完文档后沉默了三分钟。",
    "confirmed_characters": [],
}

STREAMING_RESPONSE_DESCRIPTION = (
    "Returns `text/event-stream`. The final structured business payload is sent in "
    "the `completed` SSE event."
)

STREAMING_RESPONSE_EXAMPLE = (
    "event: start\n"
    'data: {"message":"Image prompt streaming started"}\n\n'
    "event: completed\n"
    'data: {"analysis_notes":["done"]}\n\n'
)


def streaming_request(serializer_class, *, name, value, description):
    return OpenApiRequest(
        request=serializer_class,
        examples=[
            OpenApiExample(
                name=name,
                value=value,
                request_only=True,
                description=description,
            )
        ],
    )


def streaming_response():
    return OpenApiResponse(
        response=OpenApiTypes.STR,
        description=STREAMING_RESPONSE_DESCRIPTION,
        examples=[
            OpenApiExample(
                name="Streaming response example",
                value=STREAMING_RESPONSE_EXAMPLE,
                response_only=True,
                media_type="text/event-stream",
            )
        ],
    )
