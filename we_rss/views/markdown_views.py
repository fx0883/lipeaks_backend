from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from common.schema.responses import common_error_responses
from we_rss.schema import (
    MARKDOWN_FORMAT_REQUEST_EXAMPLE,
    MARKDOWN_FORMAT_RESPONSE_EXAMPLE,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    json_response,
    request_body,
    request_example,
    with_tenant_header,
)
from we_rss.serializers import MarkdownFormatRequestSerializer, MarkdownFormatResponseSerializer
from we_rss.services.markdown_format_service import MarkdownFormatService
from we_rss.views.base import WeRssTenantGenericViewSet


class MarkdownFormatViewSet(WeRssTenantGenericViewSet):
    serializer_class = MarkdownFormatResponseSerializer

    @extend_schema(
        operation_id="we_rss_markdown_format",
        tags=[WE_RSS_TAG],
        summary="Format Markdown or plain text",
        description=(
            "Format Markdown or plain text through the internal `llm_gateway` markdown formatter. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        request=request_body(
            MarkdownFormatRequestSerializer,
            request_example(
                "Markdown format request",
                MARKDOWN_FORMAT_REQUEST_EXAMPLE,
                description="Format one Markdown or plain-text string with gentle cleanup.",
            ),
        ),
        responses={
            200: json_response(
                MarkdownFormatResponseSerializer,
                "Markdown formatted successfully.",
                MARKDOWN_FORMAT_RESPONSE_EXAMPLE,
                example_name="Markdown format response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = MarkdownFormatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = MarkdownFormatService.format_content(
                content=serializer.validated_data["content"],
                mode=serializer.validated_data["mode"],
            )
        except Exception as exc:
            raise APIException(str(exc)) from exc

        return Response(MarkdownFormatResponseSerializer(result).data, status=status.HTTP_200_OK)
