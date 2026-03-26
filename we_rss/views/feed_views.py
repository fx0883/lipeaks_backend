from django.db.models import Exists, OuterRef
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.schema.responses import common_error_responses
from we_rss.models import MemberFeedSubscription, WechatFeed
from we_rss.schema import (
    FEED_ARTICLE_CLEAR_EXAMPLE,
    FEED_EXAMPLE,
    FEED_ID_PARAMETER,
    FEED_SEARCH_EXAMPLE,
    FEED_SUBSCRIBED_ONLY_PARAMETER,
    FEED_SYNC_TASK_EXAMPLE,
    FEED_SYNC_TASK_FAILED_EXAMPLE,
    KEYWORD_PARAMETER,
    MEMBER_TAG_EXAMPLE,
    TAG_IDS_PARAMETER,
    TAG_RELATION_WRITE_EXAMPLE,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    json_response,
    request_body,
    request_example,
    success_example,
    with_tenant_header,
)
from we_rss.serializers import (
    FeedArticleClearResponseSerializer,
    FeedSearchResultSerializer,
    FeedSubscriptionWriteSerializer,
    FeedWriteSerializer,
    MemberTagSerializer,
    TagRelationWriteSerializer,
    WechatFeedSerializer,
    WechatSyncTaskSerializer,
)
from we_rss.services.feed_service import FeedService, WechatFeedGateway
from we_rss.services.tag_service import TagService
from we_rss.views.base import WeRssTenantModelViewSet


class FeedApiGatewayMixin:
    def get_gateway(self):
        return WechatFeedGateway()


class FeedViewSet(FeedApiGatewayMixin, WeRssTenantModelViewSet):
    queryset = WechatFeed.objects.all()
    serializer_class = WechatFeedSerializer

    def get_queryset(self):
        subscription_exists = MemberFeedSubscription.objects.filter(
            tenant_id=self.get_tenant_id(),
            member=self.request.user,
            feed_id=OuterRef("pk"),
        )
        queryset = (
            super()
            .get_queryset()
            .annotate(is_subscribed=Exists(subscription_exists))
            .order_by("-updated_at", "-id")
        )
        subscribed_only = self.request.query_params.get("subscribed_only", "").strip().lower()
        if subscribed_only in {"1", "true", "yes"}:
            queryset = queryset.filter(is_subscribed=True)
        tag_ids = TagService.parse_tag_ids(self.request.query_params.get("tag_ids"))
        queryset = TagService.filter_feed_queryset_by_tag_ids(
            queryset=queryset,
            tenant=self.request.user.tenant,
            member=self.request.user,
            tag_ids=tag_ids,
        )
        return queryset

    def get_serializer_class(self):
        if self.action in {"create", "update"}:
            return FeedWriteSerializer
        if self.action == "search":
            return FeedSearchResultSerializer
        if self.action == "clear_articles":
            return FeedArticleClearResponseSerializer
        if self.action == "sync":
            return WechatSyncTaskSerializer
        if self.action == "subscribe":
            return FeedSubscriptionWriteSerializer
        if self.action in {"attach_tags", "detach_tags"}:
            return TagRelationWriteSerializer
        if self.action == "list_tags":
            return MemberTagSerializer
        return WechatFeedSerializer

    @extend_schema(
        operation_id="we_rss_feeds_list",
        tags=[WE_RSS_TAG],
        summary="List tenant feeds",
        description=f"Return saved WeChat feeds for the current tenant. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_SUBSCRIBED_ONLY_PARAMETER, TAG_IDS_PARAMETER),
        responses={
            200: json_response(
                WechatFeedSerializer(many=True),
                "Feed list fetched successfully.",
                [FEED_EXAMPLE],
                example_name="Feed list response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def list(self, request, *args, **kwargs):
        serializer = WechatFeedSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @extend_schema(
        operation_id="we_rss_feeds_create",
        tags=[WE_RSS_TAG],
        summary="Create feed",
        description=f"Create one tenant-scoped WeChat feed record. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(),
        request=request_body(
            FeedWriteSerializer,
            request_example(
                "Feed create request",
                {
                    "credential_id": 1,
                    "source_id": "gh_abcdef123456",
                    "faker_id": "MzA5NzQ1Mjg2NA==",
                    "biz": "MzA5NzQ1Mjg2NA==",
                    "mp_name": "AI Daily",
                    "mp_cover": "https://example.com/feed-cover.png",
                    "mp_intro": "Daily updates from the AI team.",
                    "status": "active",
                    "is_featured": False,
                },
                description="Create a feed record in the current tenant.",
            ),
        ),
        responses={
            201: json_response(
                WechatFeedSerializer,
                "Feed created successfully.",
                FEED_EXAMPLE,
                example_name="Feed create response",
                message="Operation succeeded",
                status_code=201,
            ),
            **common_error_responses,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = FeedWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feed = FeedService.create_feed(tenant=request.user.tenant, created_by=request.user, data=serializer.validated_data)
        return Response(WechatFeedSerializer(feed).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id="we_rss_feeds_retrieve",
        tags=[WE_RSS_TAG],
        summary="Retrieve one feed",
        description=f"Return one feed record in the current tenant. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        responses={
            200: json_response(
                WechatFeedSerializer,
                "Feed detail fetched successfully.",
                FEED_EXAMPLE,
                example_name="Feed detail response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return Response(WechatFeedSerializer(self.get_object()).data)

    @extend_schema(
        operation_id="we_rss_feeds_update",
        tags=[WE_RSS_TAG],
        summary="Update feed",
        description=f"Update feed metadata within the current tenant. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        request=request_body(
            FeedWriteSerializer,
            request_example(
                "Feed update request",
                {
                    "credential_id": 1,
                    "source_id": "gh_abcdef123456",
                    "faker_id": "MzA5NzQ1Mjg2NA==",
                    "biz": "MzA5NzQ1Mjg2NA==",
                    "mp_name": "AI Daily Updated",
                    "mp_cover": "https://example.com/feed-cover.png",
                    "mp_intro": "Updated introduction.",
                    "status": "active",
                    "is_featured": True,
                },
                description="Update feed metadata.",
            ),
        ),
        responses={
            200: json_response(
                WechatFeedSerializer,
                "Feed updated successfully.",
                FEED_EXAMPLE,
                example_name="Feed update response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def update(self, request, *args, **kwargs):
        feed = self.get_object()
        serializer = FeedWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feed = FeedService.update_feed(feed=feed, updated_by=request.user, data=serializer.validated_data)
        return Response(WechatFeedSerializer(feed).data)

    @extend_schema(
        operation_id="we_rss_feeds_destroy",
        tags=[WE_RSS_TAG],
        summary="Delete feed",
        description=f"Delete one feed record in the current tenant. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        responses={204: OpenApiResponse(description="Feed deleted"), **common_error_responses},
    )
    def destroy(self, request, *args, **kwargs):
        feed = self.get_object()
        feed.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        operation_id="we_rss_feeds_clear_articles",
        tags=[WE_RSS_TAG],
        summary="Clear feed articles",
        description=f"Delete all article records that belong to one feed in the current tenant. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        request=None,
        responses={
            200: json_response(
                FeedArticleClearResponseSerializer,
                "Feed articles cleared.",
                FEED_ARTICLE_CLEAR_EXAMPLE,
                example_name="Feed clear articles response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["delete"], url_path="articles")
    def clear_articles(self, request, *args, **kwargs):
        feed = self.get_object()
        result = FeedService.clear_articles(feed=feed)
        return Response(result)

    @extend_schema(
        operation_id="we_rss_feeds_search",
        tags=[WE_RSS_TAG],
        summary="Search WeChat feeds",
        description=f"Use the active credential to search public accounts on WeChat. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(KEYWORD_PARAMETER),
        responses={
            200: json_response(
                FeedSearchResultSerializer(many=True),
                "Feed search completed successfully.",
                [FEED_SEARCH_EXAMPLE],
                example_name="Feed search response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=False, methods=["get"])
    def search(self, request, *args, **kwargs):
        keyword = request.query_params.get("keyword", "").strip()
        if not keyword:
            raise ValidationError({"keyword": ["This field is required."]})

        results = FeedService.search_feeds(
            tenant=request.user.tenant,
            keyword=keyword,
            gateway=self.get_gateway(),
        )
        return Response(FeedSearchResultSerializer(results, many=True).data)

    @extend_schema(
        operation_id="we_rss_feeds_subscribe",
        tags=[WE_RSS_TAG],
        summary="Subscribe current member to a feed",
        description=(
            "Create or reuse a tenant feed from a search result payload, then create a subscription for the current "
            f"member. {WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        request=request_body(
            FeedSubscriptionWriteSerializer,
            request_example(
                "Feed subscribe request",
                {
                    "source_id": "gh_search_1",
                    "faker_id": "MzI3NjQ4NTY=",
                    "biz": "MzI3NjQ4NTY=",
                    "mp_name": "AI Weekly",
                    "mp_cover": "https://example.com/search-cover.png",
                    "mp_intro": "Weekly insights about AI products.",
                },
                description="Subscribe the current member using a feed search result payload.",
            ),
        ),
        responses={
            200: json_response(
                WechatFeedSerializer,
                "Feed subscribed successfully.",
                {**FEED_EXAMPLE, "is_subscribed": True},
                example_name="Feed subscribe response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=False, methods=["post"], url_path="subscribe")
    def subscribe(self, request, *args, **kwargs):
        serializer = FeedSubscriptionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feed = FeedService.subscribe_member(
            tenant=request.user.tenant,
            member=request.user,
            data=serializer.validated_data,
        )
        return Response(WechatFeedSerializer(feed).data)

    @extend_schema(
        operation_id="we_rss_feeds_unsubscribe",
        tags=[WE_RSS_TAG],
        summary="Unsubscribe current member from a feed",
        description=f"Delete the current member's subscription to one feed. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        request=None,
        responses={204: OpenApiResponse(description="Feed unsubscribed"), **common_error_responses},
    )
    @action(detail=True, methods=["delete"], url_path="subscribe")
    def unsubscribe(self, request, *args, **kwargs):
        feed = self.get_object()
        FeedService.unsubscribe_member(feed=feed, member=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        operation_id="we_rss_feeds_tags_list",
        tags=[WE_RSS_TAG],
        summary="List current member tags on a feed",
        description=f"Return the current member's private tags attached to one feed. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        responses={
            200: json_response(
                MemberTagSerializer(many=True),
                "Feed tags fetched successfully.",
                [MEMBER_TAG_EXAMPLE],
                example_name="Feed tags response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["get"], url_path="tags")
    def list_tags(self, request, *args, **kwargs):
        feed = self.get_object()
        tags = TagService.list_feed_tags(feed=feed, member=request.user)
        return Response(MemberTagSerializer(tags, many=True).data)

    @extend_schema(
        operation_id="we_rss_feeds_tags_attach",
        tags=[WE_RSS_TAG],
        summary="Attach existing tags to a feed",
        description=f"Attach one or more existing member tags to a subscribed feed. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        request=request_body(
            TagRelationWriteSerializer,
            request_example(
                "Feed tag attach request",
                TAG_RELATION_WRITE_EXAMPLE,
                description="Attach the listed tag IDs to the selected feed.",
            ),
        ),
        responses={
            200: json_response(
                MemberTagSerializer(many=True),
                "Feed tags updated successfully.",
                [MEMBER_TAG_EXAMPLE],
                example_name="Feed tag attach response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"], url_path="tags/attach")
    def attach_tags(self, request, *args, **kwargs):
        feed = self.get_object()
        serializer = TagRelationWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tags = TagService.attach_tags_to_feed(
            feed=feed,
            member=request.user,
            tag_ids=serializer.validated_data["tag_ids"],
        )
        return Response(MemberTagSerializer(tags, many=True).data)

    @extend_schema(
        operation_id="we_rss_feeds_tags_detach",
        tags=[WE_RSS_TAG],
        summary="Detach tags from a feed",
        description=f"Detach one or more existing member tags from a subscribed feed. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        request=request_body(
            TagRelationWriteSerializer,
            request_example(
                "Feed tag detach request",
                TAG_RELATION_WRITE_EXAMPLE,
                description="Detach the listed tag IDs from the selected feed.",
            ),
        ),
        responses={
            200: json_response(
                MemberTagSerializer(many=True),
                "Feed tags updated successfully.",
                [MEMBER_TAG_EXAMPLE],
                example_name="Feed tag detach response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"], url_path="tags/detach")
    def detach_tags(self, request, *args, **kwargs):
        feed = self.get_object()
        serializer = TagRelationWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tags = TagService.detach_tags_from_feed(
            feed=feed,
            member=request.user,
            tag_ids=serializer.validated_data["tag_ids"],
        )
        return Response(MemberTagSerializer(tags, many=True).data)

    @extend_schema(
        operation_id="we_rss_feeds_sync",
        tags=[WE_RSS_TAG],
        summary="Sync feed articles",
        description=f"Create or reuse a sync task for one feed and fetch its WeChat articles. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        request=None,
        responses={
            200: json_response(
                WechatSyncTaskSerializer,
                "Feed sync task created.",
                FEED_SYNC_TASK_EXAMPLE,
                example_name="Feed sync response",
                message="Operation succeeded",
                examples=[
                    success_example(
                        "Feed sync success response",
                        FEED_SYNC_TASK_EXAMPLE,
                        message="Operation succeeded",
                    ),
                    success_example(
                        "Feed sync failed task response",
                        FEED_SYNC_TASK_FAILED_EXAMPLE,
                        message="Operation succeeded",
                    ),
                ],
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"])
    def sync(self, request, *args, **kwargs):
        feed = self.get_object()
        task = FeedService.sync_feed(feed=feed, created_by=request.user)
        return Response(WechatSyncTaskSerializer(task).data)
