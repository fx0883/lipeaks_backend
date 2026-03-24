from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.schema.responses import common_error_responses
from we_rss.models import WechatArticle, WechatSyncTask
from we_rss.schema import (
    ARTICLE_EXAMPLE,
    ARTICLE_ID_PARAMETER,
    ARTICLE_IMPORT_TASK_FAILED_EXAMPLE,
    ARTICLE_IMPORT_TASK_EXAMPLE,
    ARTICLE_REFRESH_TASK_FAILED_EXAMPLE,
    ARTICLE_REFRESH_TASK_EXAMPLE,
    ARTICLE_TYPE_PARAMETER,
    CREDENTIAL_LOGIN_TASK_FAILED_EXAMPLE,
    FEED_SYNC_TASK_EXAMPLE,
    FEED_SYNC_TASK_FAILED_EXAMPLE,
    TASK_ID_PARAMETER,
    TASK_STATUS_PARAMETER,
    TASK_TARGET_ID_PARAMETER,
    TASK_TARGET_TYPE_PARAMETER,
    TASK_TYPE_PARAMETER,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    json_response,
    request_body,
    success_example,
    request_example,
    with_tenant_header,
)
from we_rss.serializers import (
    ArticleFavoriteUpdateSerializer,
    ArticleImportSerializer,
    ArticleReadUpdateSerializer,
    WechatArticleSerializer,
    WechatSyncTaskSerializer,
)
from we_rss.services.article_service import ArticleService, WechatArticleGateway
from we_rss.views.base import WeRssTenantGenericViewSet, WeRssTenantModelViewSet


class ArticleApiGatewayMixin:
    def get_gateway(self):
        return WechatArticleGateway()


class ArticleViewSet(ArticleApiGatewayMixin, WeRssTenantModelViewSet):
    queryset = WechatArticle.objects.select_related("feed")
    serializer_class = WechatArticleSerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related("feed").order_by("-publish_time", "-id")
        article_type = self.request.query_params.get("article_type", "").strip()
        if article_type:
            valid_types = {WechatArticle.ArticleType.NEWS, WechatArticle.ArticleType.NEWSPIC}
            if article_type not in valid_types:
                raise ValidationError({"article_type": ["Supported values are: news, newspic."]})
            queryset = queryset.filter(article_type=article_type)
        return queryset

    def get_serializer_class(self):
        if self.action == "import_by_url":
            return ArticleImportSerializer
        if self.action == "update_read":
            return ArticleReadUpdateSerializer
        if self.action == "update_favorite":
            return ArticleFavoriteUpdateSerializer
        if self.action == "refresh":
            return WechatSyncTaskSerializer
        return WechatArticleSerializer

    @extend_schema(
        operation_id="we_rss_articles_list",
        tags=[WE_RSS_TAG],
        summary="列出当前租户的公众号文章",
        description=f"返回当前 tenant 下已保存的公众号文章列表。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(ARTICLE_TYPE_PARAMETER),
        responses={
            200: json_response(
                WechatArticleSerializer(many=True),
                "文章列表获取成功。",
                [ARTICLE_EXAMPLE],
                example_name="Article list response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    def list(self, request, *args, **kwargs):
        serializer = WechatArticleSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @extend_schema(
        operation_id="we_rss_articles_retrieve",
        tags=[WE_RSS_TAG],
        summary="获取单篇公众号文章",
        description=f"按 ID 返回当前 tenant 内的公众号文章详情。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        responses={
            200: json_response(
                WechatArticleSerializer,
                "文章详情获取成功。",
                ARTICLE_EXAMPLE,
                example_name="Article detail response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return Response(WechatArticleSerializer(self.get_object()).data)

    @extend_schema(
        operation_id="we_rss_articles_destroy",
        tags=[WE_RSS_TAG],
        summary="删除公众号文章",
        description=f"删除当前 tenant 内的文章记录，不影响其他文章数据。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        responses={204: OpenApiResponse(description="Article deleted"), **common_error_responses},
    )
    def destroy(self, request, *args, **kwargs):
        article = self.get_object()
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        operation_id="we_rss_articles_import_by_url",
        tags=[WE_RSS_TAG],
        summary="按微信文章 URL 导入文章",
        description=(
            "根据公开微信文章 URL 创建导入任务，后台真实抓取正文与统计字段，"
            f"并自动绑定到当前 tenant 的 featured feed。{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        request=request_body(
            ArticleImportSerializer,
            request_example(
                "Article import request",
                {"url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc"},
                description="通过微信文章 URL 创建导入任务。",
            )
        ),
        responses={
            200: json_response(
                WechatSyncTaskSerializer,
                "文章导入任务已创建。",
                ARTICLE_IMPORT_TASK_EXAMPLE,
                example_name="Article import response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    @action(detail=False, methods=["post"], url_path="import-by-url")
    def import_by_url(self, request, *args, **kwargs):
        serializer = ArticleImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = ArticleService.import_article_by_url(
            tenant=request.user.tenant,
            created_by=request.user,
            url=serializer.validated_data["url"],
        )
        return Response(WechatSyncTaskSerializer(task).data)

    @extend_schema(
        operation_id="we_rss_articles_refresh",
        tags=[WE_RSS_TAG],
        summary="刷新文章正文和统计快照",
        description=(
            "为指定文章创建刷新任务，重新抓取正文内容、发布时间和阅读互动统计。"
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        request=None,
        responses={
            200: json_response(
                WechatSyncTaskSerializer,
                "文章刷新任务已创建。",
                ARTICLE_REFRESH_TASK_EXAMPLE,
                example_name="Article refresh response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"])
    def refresh(self, request, *args, **kwargs):
        article = self.get_object()
        task = ArticleService.refresh_article(article=article, created_by=request.user)
        return Response(WechatSyncTaskSerializer(task).data)

    @extend_schema(
        operation_id="we_rss_articles_update_read",
        tags=[WE_RSS_TAG],
        summary="更新文章已读状态",
        description=f"在当前 tenant 内标记文章是否已读。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        request=request_body(
            ArticleReadUpdateSerializer,
            request_example(
                "Article read update request",
                {"is_read": True},
                description="将文章标记为已读。",
            )
        ),
        responses={
            200: json_response(
                WechatArticleSerializer,
                "文章已读状态更新成功。",
                {**ARTICLE_EXAMPLE, "is_read": True},
                example_name="Article read update response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["put"], url_path="read")
    def update_read(self, request, *args, **kwargs):
        article = self.get_object()
        serializer = ArticleReadUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = ArticleService.set_read_status(article=article, is_read=serializer.validated_data["is_read"])
        return Response(WechatArticleSerializer(article).data)

    @extend_schema(
        operation_id="we_rss_articles_update_favorite",
        tags=[WE_RSS_TAG],
        summary="更新文章收藏状态",
        description=f"在当前 tenant 内标记文章是否收藏。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        request=request_body(
            ArticleFavoriteUpdateSerializer,
            request_example(
                "Article favorite update request",
                {"is_favorite": True},
                description="将文章标记为收藏。",
            )
        ),
        responses={
            200: json_response(
                WechatArticleSerializer,
                "文章收藏状态更新成功。",
                {**ARTICLE_EXAMPLE, "is_favorite": True},
                example_name="Article favorite update response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["put"], url_path="favorite")
    def update_favorite(self, request, *args, **kwargs):
        article = self.get_object()
        serializer = ArticleFavoriteUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = ArticleService.set_favorite_status(
            article=article,
            is_favorite=serializer.validated_data["is_favorite"],
        )
        return Response(WechatArticleSerializer(article).data)


class SyncTaskViewSet(ArticleApiGatewayMixin, WeRssTenantGenericViewSet):
    queryset = WechatSyncTask.objects.all()
    serializer_class = WechatSyncTaskSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "task_id"

    def get_queryset(self):
        queryset = WechatSyncTask.objects.filter(tenant_id=self.get_tenant_id()).order_by("-created_at")
        for field in ("task_type", "status", "target_type"):
            value = self.request.query_params.get(field, "").strip()
            if value:
                queryset = queryset.filter(**{field: value})
        target_id = self.request.query_params.get("target_id", "").strip()
        if target_id:
            queryset = queryset.filter(target_id=target_id)
        return queryset

    @extend_schema(
        operation_id="we_rss_tasks_list",
        tags=[WE_RSS_TAG],
        summary="查询同步任务列表",
        description=f"返回当前 tenant 下的同步任务列表，支持按任务类型、状态、目标类型和目标 ID 过滤。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(
            TASK_TYPE_PARAMETER,
            TASK_STATUS_PARAMETER,
            TASK_TARGET_TYPE_PARAMETER,
            TASK_TARGET_ID_PARAMETER,
        ),
        responses={
            200: json_response(
                WechatSyncTaskSerializer(many=True),
                "同步任务列表获取成功。",
                [FEED_SYNC_TASK_EXAMPLE, ARTICLE_IMPORT_TASK_FAILED_EXAMPLE],
                example_name="Task list response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    def list(self, request, *args, **kwargs):
        return Response(WechatSyncTaskSerializer(self.get_queryset(), many=True).data)

    @extend_schema(
        operation_id="we_rss_tasks_retrieve",
        tags=[WE_RSS_TAG],
        summary="查询同步任务详情",
        description=f"按任务 ID 返回后台同步任务的状态、请求载荷与执行结果。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(TASK_ID_PARAMETER),
        responses={
            200: json_response(
                WechatSyncTaskSerializer,
                "同步任务详情获取成功。",
                FEED_SYNC_TASK_EXAMPLE,
                example_name="Task detail response",
                message="操作成功",
                examples=[
                    success_example(
                        "Feed sync task success response",
                        FEED_SYNC_TASK_EXAMPLE,
                        message="操作成功",
                    ),
                    success_example(
                        "Feed sync task failed response",
                        FEED_SYNC_TASK_FAILED_EXAMPLE,
                        message="操作成功",
                    ),
                    success_example(
                        "Article import task response",
                        ARTICLE_IMPORT_TASK_EXAMPLE,
                        message="操作成功",
                    ),
                    success_example(
                        "Article refresh task response",
                        ARTICLE_REFRESH_TASK_EXAMPLE,
                        message="操作成功",
                    ),
                    success_example(
                        "Credential login task failed response",
                        CREDENTIAL_LOGIN_TASK_FAILED_EXAMPLE,
                        message="操作成功",
                    ),
                    success_example(
                        "Article import task failed response",
                        ARTICLE_IMPORT_TASK_FAILED_EXAMPLE,
                        message="操作成功",
                    ),
                    success_example(
                        "Article refresh task failed response",
                        ARTICLE_REFRESH_TASK_FAILED_EXAMPLE,
                        message="操作成功",
                    ),
                ],
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return Response(WechatSyncTaskSerializer(self.get_object()).data)
