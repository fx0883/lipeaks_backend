from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response

from common.schema.responses import common_error_responses
from we_rss.models import MemberTag
from we_rss.schema import (
    MEMBER_TAG_EXAMPLE,
    TAG_ID_PARAMETER,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    json_response,
    request_body,
    request_example,
    with_tenant_header,
)
from we_rss.serializers import MemberTagSerializer, MemberTagWriteSerializer
from we_rss.services.tag_service import TagService
from we_rss.views.base import WeRssTenantModelViewSet


class MemberTagViewSet(WeRssTenantModelViewSet):
    queryset = MemberTag.objects.all()
    serializer_class = MemberTagSerializer

    def get_queryset(self):
        return TagService.list_member_tags(
            tenant=self.request.user.tenant,
            member=self.request.user,
        )

    def get_serializer_class(self):
        if self.action in {"create", "update"}:
            return MemberTagWriteSerializer
        return MemberTagSerializer

    @extend_schema(
        operation_id="we_rss_tags_list",
        tags=[WE_RSS_TAG],
        summary="List current member tags",
        description=f"Return the current member's private tag library. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(),
        responses={
            200: json_response(
                MemberTagSerializer(many=True),
                "Tag list fetched successfully.",
                [MEMBER_TAG_EXAMPLE],
                example_name="Tag list response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def list(self, request, *args, **kwargs):
        return Response(MemberTagSerializer(self.get_queryset(), many=True).data)

    @extend_schema(
        operation_id="we_rss_tags_create",
        tags=[WE_RSS_TAG],
        summary="Create a private tag",
        description=f"Create one private tag owned by the current member. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(),
        request=request_body(
            MemberTagWriteSerializer,
            request_example(
                "Tag create request",
                {
                    "name": "AI",
                    "color": "#008000",
                    "description": "Interesting reads",
                    "sort_order": 10,
                    "is_pinned": True,
                },
                description="Create a new private tag for the current member.",
            ),
        ),
        responses={
            201: json_response(
                MemberTagSerializer,
                "Tag created successfully.",
                MEMBER_TAG_EXAMPLE,
                example_name="Tag create response",
                message="Operation succeeded",
                status_code=201,
            ),
            **common_error_responses,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = MemberTagWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tag = TagService.create_member_tag(
            tenant=request.user.tenant,
            member=request.user,
            data=serializer.validated_data,
        )
        return Response(MemberTagSerializer(tag).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id="we_rss_tags_retrieve",
        tags=[WE_RSS_TAG],
        summary="Retrieve a private tag",
        description=f"Return one private tag owned by the current member. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(TAG_ID_PARAMETER),
        responses={
            200: json_response(
                MemberTagSerializer,
                "Tag detail fetched successfully.",
                MEMBER_TAG_EXAMPLE,
                example_name="Tag detail response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return Response(MemberTagSerializer(self.get_object()).data)

    @extend_schema(
        operation_id="we_rss_tags_update",
        tags=[WE_RSS_TAG],
        summary="Update a private tag",
        description=f"Update one private tag owned by the current member. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(TAG_ID_PARAMETER),
        request=request_body(
            MemberTagWriteSerializer,
            request_example(
                "Tag update request",
                {
                    "name": "AI Updated",
                    "color": "#00AA00",
                    "description": "Updated description",
                    "sort_order": 5,
                    "is_pinned": False,
                },
                description="Update the selected private tag.",
            ),
        ),
        responses={
            200: json_response(
                MemberTagSerializer,
                "Tag updated successfully.",
                MEMBER_TAG_EXAMPLE,
                example_name="Tag update response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def update(self, request, *args, **kwargs):
        tag = self.get_object()
        serializer = MemberTagWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tag = TagService.update_member_tag(tag=tag, data=serializer.validated_data)
        return Response(MemberTagSerializer(tag).data)

    @extend_schema(
        operation_id="we_rss_tags_destroy",
        tags=[WE_RSS_TAG],
        summary="Delete a private tag",
        description=f"Hard-delete one private tag owned by the current member and remove all relations. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(TAG_ID_PARAMETER),
        responses={204: OpenApiResponse(description="Tag deleted"), **common_error_responses},
    )
    def destroy(self, request, *args, **kwargs):
        tag = self.get_object()
        TagService.delete_member_tag(tag=tag)
        return Response(status=status.HTTP_204_NO_CONTENT)
