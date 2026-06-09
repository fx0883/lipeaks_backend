from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response

from common.schema.responses import common_error_responses
from we_rss.schema import (
    MEMBER_ID_QUERY_PARAMETER,
    SEO_KEYWORD_DELETE_EXAMPLE,
    SEO_KEYWORD_EXAMPLE,
    SEO_KEYWORD_ID_PARAMETER,
    SEO_KEYWORD_SEARCH_PARAMETER,
    SEO_KEYWORD_TAG_ID_PARAMETER,
    SEO_KEYWORD_WRITE_EXAMPLE,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    json_response,
    request_body,
    request_example,
    with_tenant_header,
)
from we_rss.serializers import (
    SeoKeywordDeleteSerializer,
    SeoKeywordQuerySerializer,
    SeoKeywordSerializer,
    SeoKeywordWriteSerializer,
)
from we_rss.services.seo_keyword_service import SeoKeywordService
from we_rss.views.base import WeRssTenantGenericViewSet


class MemberSeoKeywordViewSet(WeRssTenantGenericViewSet):
    serializer_class = SeoKeywordSerializer

    def get_serializer_class(self):
        if self.action in {"create", "update"}:
            return SeoKeywordWriteSerializer
        if self.action == "destroy":
            return SeoKeywordDeleteSerializer
        if self.action in {"list", "retrieve"}:
            return SeoKeywordQuerySerializer
        return SeoKeywordSerializer

    @extend_schema(
        operation_id="we_rss_seo_keywords_list",
        tags=[WE_RSS_TAG],
        summary="List member SEO keywords",
        description=f"Return the selected member's SEO keyword library. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(
            MEMBER_ID_QUERY_PARAMETER,
            SEO_KEYWORD_SEARCH_PARAMETER,
            SEO_KEYWORD_TAG_ID_PARAMETER,
        ),
        responses={
            200: json_response(
                SeoKeywordSerializer(many=True),
                "SEO keyword list fetched successfully.",
                [SEO_KEYWORD_EXAMPLE],
                example_name="SEO keyword list response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def list(self, request, *args, **kwargs):
        serializer = SeoKeywordQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        keywords = SeoKeywordService.list_keywords(
            tenant=request.user.tenant,
            actor=request.user,
            member_id=serializer.validated_data["member_id"],
            search=serializer.validated_data.get("search"),
            tag_id=serializer.validated_data.get("tag_id"),
        )
        return Response(SeoKeywordSerializer(keywords, many=True).data)

    @extend_schema(
        operation_id="we_rss_seo_keywords_create",
        tags=[WE_RSS_TAG],
        summary="Create a member SEO keyword",
        description=f"Create one SEO keyword under an explicit member scope. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(),
        request=request_body(
            SeoKeywordWriteSerializer,
            request_example(
                "SEO keyword create request",
                SEO_KEYWORD_WRITE_EXAMPLE,
                description="Create one SEO keyword and optionally link it to tags.",
            ),
        ),
        responses={
            201: json_response(
                SeoKeywordSerializer,
                "SEO keyword created successfully.",
                SEO_KEYWORD_EXAMPLE,
                example_name="SEO keyword create response",
                message="Operation succeeded",
                status_code=201,
            ),
            **common_error_responses,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = SeoKeywordWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        keyword = SeoKeywordService.create_keyword(
            tenant=request.user.tenant,
            actor=request.user,
            member_id=serializer.validated_data["member_id"],
            keyword=serializer.validated_data["keyword"],
            search_index=serializer.validated_data["search_index"],
            tag_ids=serializer.validated_data.get("tag_ids", []),
        )
        return Response(SeoKeywordSerializer(keyword).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id="we_rss_seo_keywords_retrieve",
        tags=[WE_RSS_TAG],
        summary="Retrieve a member SEO keyword",
        description=f"Return one SEO keyword under an explicit member scope. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(
            SEO_KEYWORD_ID_PARAMETER,
            MEMBER_ID_QUERY_PARAMETER,
        ),
        responses={
            200: json_response(
                SeoKeywordSerializer,
                "SEO keyword detail fetched successfully.",
                SEO_KEYWORD_EXAMPLE,
                example_name="SEO keyword detail response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = SeoKeywordQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        keyword = SeoKeywordService.get_keyword(
            tenant=request.user.tenant,
            actor=request.user,
            member_id=serializer.validated_data["member_id"],
            keyword_id=pk,
        )
        return Response(SeoKeywordSerializer(keyword).data)

    @extend_schema(
        operation_id="we_rss_seo_keywords_update",
        tags=[WE_RSS_TAG],
        summary="Update a member SEO keyword",
        description=f"Update one SEO keyword and replace all linked tags. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(SEO_KEYWORD_ID_PARAMETER),
        request=request_body(
            SeoKeywordWriteSerializer,
            request_example(
                "SEO keyword update request",
                {
                    **SEO_KEYWORD_WRITE_EXAMPLE,
                    "keyword": "weight loss menu",
                    "search_index": 7200,
                    "tag_ids": [2],
                },
                description="Update one SEO keyword and replace its linked tags.",
            ),
        ),
        responses={
            200: json_response(
                SeoKeywordSerializer,
                "SEO keyword updated successfully.",
                {
                    **SEO_KEYWORD_EXAMPLE,
                    "keyword": "weight loss menu",
                    "search_index": 7200,
                    "tag_ids": [2],
                    "tags": [SEO_KEYWORD_EXAMPLE["tags"][1]],
                },
                example_name="SEO keyword update response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def update(self, request, pk=None, *args, **kwargs):
        serializer = SeoKeywordWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        keyword = SeoKeywordService.update_keyword(
            tenant=request.user.tenant,
            actor=request.user,
            member_id=serializer.validated_data["member_id"],
            keyword_id=pk,
            keyword=serializer.validated_data["keyword"],
            search_index=serializer.validated_data["search_index"],
            tag_ids=serializer.validated_data.get("tag_ids", []),
        )
        return Response(SeoKeywordSerializer(keyword).data)

    @extend_schema(
        operation_id="we_rss_seo_keywords_destroy",
        tags=[WE_RSS_TAG],
        summary="Delete a member SEO keyword",
        description=f"Hard-delete one SEO keyword under an explicit member scope. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(SEO_KEYWORD_ID_PARAMETER),
        request=request_body(
            SeoKeywordDeleteSerializer,
            request_example(
                "SEO keyword delete request",
                SEO_KEYWORD_DELETE_EXAMPLE,
                description="Delete one SEO keyword inside the selected member scope.",
            ),
        ),
        responses={204: OpenApiResponse(description="SEO keyword deleted"), **common_error_responses},
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        serializer = SeoKeywordDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        SeoKeywordService.delete_keyword(
            tenant=request.user.tenant,
            actor=request.user,
            member_id=serializer.validated_data["member_id"],
            keyword_id=pk,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
