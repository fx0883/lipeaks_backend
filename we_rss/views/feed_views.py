from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.schema.responses import common_error_responses
from we_rss.models import WechatFeed
from we_rss.schema import (
    FEED_EXAMPLE,
    FEED_ARTICLE_CLEAR_EXAMPLE,
    FEED_ID_PARAMETER,
    FEED_SEARCH_EXAMPLE,
    FEED_SYNC_TASK_EXAMPLE,
    FEED_SYNC_TASK_FAILED_EXAMPLE,
    KEYWORD_PARAMETER,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    json_response,
    request_body,
    success_example,
    request_example,
    with_tenant_header,
)
from we_rss.serializers import (
    FeedArticleClearResponseSerializer,
    FeedSearchResultSerializer,
    FeedWriteSerializer,
    WechatFeedSerializer,
    WechatSyncTaskSerializer,
)
from we_rss.services.feed_service import FeedService, WechatFeedGateway
from we_rss.views.base import WeRssTenantModelViewSet


class FeedApiGatewayMixin:
    def get_gateway(self):
        return WechatFeedGateway()


class FeedViewSet(FeedApiGatewayMixin, WeRssTenantModelViewSet):
    queryset = WechatFeed.objects.all()
    serializer_class = WechatFeedSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("-updated_at", "-id")

    def get_serializer_class(self):
        if self.action in {"create", "update"}:
            return FeedWriteSerializer
        if self.action == "search":
            return FeedSearchResultSerializer
        if self.action == "clear_articles":
            return FeedArticleClearResponseSerializer
        if self.action == "sync":
            return WechatSyncTaskSerializer
        return WechatFeedSerializer

    @extend_schema(
        operation_id="we_rss_feeds_list",
        tags=[WE_RSS_TAG],
        summary="列出当前租户的公众号",
        description=f"返回当前 tenant 下已保存的微信公众号列表。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(),
        responses={
            200: json_response(
                WechatFeedSerializer(many=True),
                "公众号列表获取成功。",
                [FEED_EXAMPLE],
                example_name="Feed list response",
                message="操作成功",
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
        summary="创建公众号记录",
        description=(
            "手动创建一个公众号记录，可预先绑定默认凭证或标记为 featured，"
            f"供后续同步与文章导入使用。{WE_RSS_AUTH_DESCRIPTION}"
        ),
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
                description="创建一个 tenant 共享的公众号记录。",
            )
        ),
        responses={
            201: json_response(
                WechatFeedSerializer,
                "公众号创建成功。",
                FEED_EXAMPLE,
                example_name="Feed create response",
                message="操作成功",
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
        summary="获取单个公众号",
        description=f"按 ID 返回当前 tenant 内的公众号详情。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        responses={
            200: json_response(
                WechatFeedSerializer,
                "公众号详情获取成功。",
                FEED_EXAMPLE,
                example_name="Feed detail response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return Response(WechatFeedSerializer(self.get_object()).data)

    @extend_schema(
        operation_id="we_rss_feeds_update",
        tags=[WE_RSS_TAG],
        summary="更新公众号记录",
        description=f"更新当前 tenant 内已有公众号的元数据。{WE_RSS_AUTH_DESCRIPTION}",
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
                description="更新公众号名称、简介和 featured 状态。",
            )
        ),
        responses={
            200: json_response(
                WechatFeedSerializer,
                "公众号更新成功。",
                FEED_EXAMPLE,
                example_name="Feed update response",
                message="操作成功",
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
        summary="删除公众号记录",
        description=f"删除当前 tenant 内的公众号记录，删除后不再参与 RSS 和同步。{WE_RSS_AUTH_DESCRIPTION}",
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
        summary="清空公众号下全部文章",
        description=(
            "永久删除当前 tenant 内指定公众号下的全部文章数据库记录。"
            "该操作只影响当前 feed 关联文章，不会删除 feed 本身。"
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        request=None,
        responses={
            200: json_response(
                FeedArticleClearResponseSerializer,
                "公众号文章已清空。",
                FEED_ARTICLE_CLEAR_EXAMPLE,
                example_name="Feed clear articles response",
                message="操作成功",
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
        summary="搜索微信平台公众号",
        description=(
            "使用当前 tenant 的默认有效凭证在微信平台搜索公众号候选列表。"
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(KEYWORD_PARAMETER),
        responses={
            200: json_response(
                FeedSearchResultSerializer(many=True),
                "公众号搜索成功。",
                [FEED_SEARCH_EXAMPLE],
                example_name="Feed search response",
                message="操作成功",
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
        operation_id="we_rss_feeds_sync",
        tags=[WE_RSS_TAG],
        summary="触发公众号文章同步",
        description=(
            "为指定公众号创建或复用同步任务，后台会真实抓取公众号文章并 upsert 到 `WechatArticle`。"
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        request=None,
        responses={
            200: json_response(
                WechatSyncTaskSerializer,
                "公众号同步任务已创建。",
                FEED_SYNC_TASK_EXAMPLE,
                example_name="Feed sync response",
                message="操作成功",
                examples=[
                    success_example(
                        "Feed sync success response",
                        FEED_SYNC_TASK_EXAMPLE,
                        message="操作成功",
                    ),
                    success_example(
                        "Feed sync failed task response",
                        FEED_SYNC_TASK_FAILED_EXAMPLE,
                        message="操作成功",
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
