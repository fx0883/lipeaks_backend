from django.db.models import Exists, OuterRef
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.schema.responses import common_error_responses
from we_rss.models import MemberArticleFavorite, WechatArticle, WechatSyncTask
from we_rss.schema import (
    ARTICLE_EXAMPLE,
    ARTICLE_FAVORITE_ONLY_PARAMETER,
    ARTICLE_ID_PARAMETER,
    ARTICLE_IMPORT_TASK_EXAMPLE,
    ARTICLE_IMPORT_TASK_FAILED_EXAMPLE,
    ARTICLE_REFRESH_TASK_EXAMPLE,
    ARTICLE_REFRESH_TASK_FAILED_EXAMPLE,
    ARTICLE_SEARCH_PARAMETER,
    MEMBER_TAG_EXAMPLE,
    ARTICLE_TYPE_PARAMETER,
    FEED_SYNC_TASK_EXAMPLE,
    FEED_SYNC_TASK_FAILED_EXAMPLE,
    TAG_IDS_PARAMETER,
    TAG_RELATION_WRITE_EXAMPLE,
    TASK_ID_PARAMETER,
    TASK_STATUS_PARAMETER,
    TASK_TARGET_ID_PARAMETER,
    TASK_TARGET_TYPE_PARAMETER,
    TASK_TYPE_PARAMETER,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    json_response,
    request_body,
    request_example,
    success_example,
    with_tenant_header,
)
from we_rss.serializers import (
    ArticleFavoriteUpdateSerializer,
    ArticleImportSerializer,
    MemberTagSerializer,
    TagRelationWriteSerializer,
    WechatArticleSerializer,
    WechatSyncTaskSerializer,
)
from we_rss.services.article_service import ArticleService, WechatArticleGateway
from we_rss.services.tag_service import TagService
from we_rss.views.base import WeRssTenantGenericViewSet, WeRssTenantModelViewSet


class ArticleApiGatewayMixin:
    def get_gateway(self):
        return WechatArticleGateway()


class ArticleViewSet(ArticleApiGatewayMixin, WeRssTenantModelViewSet):
    queryset = WechatArticle.objects.select_related("feed")
    serializer_class = WechatArticleSerializer

    def get_queryset(self):
        favorite_exists = MemberArticleFavorite.objects.filter(
            tenant_id=self.get_tenant_id(),
            member=self.request.user,
            article_id=OuterRef("pk"),
        )
        queryset = (
            super()
            .get_queryset()
            .select_related("feed")
            .annotate(is_favorite=Exists(favorite_exists))
            .order_by("-publish_time", "-id")
        )

        article_type = self.request.query_params.get("article_type", "").strip()
        if article_type:
            valid_types = {WechatArticle.ArticleType.NEWS, WechatArticle.ArticleType.NEWSPIC}
            if article_type not in valid_types:
                raise ValidationError({"article_type": ["Supported values are: news, newspic."]})
            queryset = queryset.filter(article_type=article_type)

        search = self.request.query_params.get("search", "").strip()
        search_query = ArticleService.build_search_query(search)
        if search_query is not None:
            queryset = queryset.filter(search_query)

        favorite_only = self.request.query_params.get("favorite_only", "").strip().lower()
        if favorite_only in {"1", "true", "yes"}:
            queryset = queryset.filter(is_favorite=True)

        tag_ids = TagService.parse_tag_ids(self.request.query_params.get("tag_ids"))
        queryset = TagService.filter_article_queryset_by_tag_ids(
            queryset=queryset,
            tenant=self.request.user.tenant,
            member=self.request.user,
            tag_ids=tag_ids,
        )

        return queryset

    def get_serializer_class(self):
        if self.action == "import_by_url":
            return ArticleImportSerializer
        if self.action == "update_favorite":
            return ArticleFavoriteUpdateSerializer
        if self.action == "refresh":
            return WechatSyncTaskSerializer
        if self.action in {"attach_tags", "detach_tags"}:
            return TagRelationWriteSerializer
        if self.action == "list_tags":
            return MemberTagSerializer
        return WechatArticleSerializer

    @extend_schema(
        operation_id="we_rss_articles_list",
        tags=[WE_RSS_TAG],
        summary="List tenant articles",
        description=f"Return the saved WeChat articles for the current tenant. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(
            ARTICLE_TYPE_PARAMETER,
            ARTICLE_SEARCH_PARAMETER,
            ARTICLE_FAVORITE_ONLY_PARAMETER,
            TAG_IDS_PARAMETER,
        ),
        responses={
            200: json_response(
                WechatArticleSerializer(many=True),
                "Article list fetched successfully.",
                [ARTICLE_EXAMPLE],
                example_name="Article list response",
                message="Operation succeeded",
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
        summary="Retrieve one article",
        description=f"Return the details of one tenant-scoped WeChat article. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        responses={
            200: json_response(
                WechatArticleSerializer,
                "Article detail fetched successfully.",
                ARTICLE_EXAMPLE,
                example_name="Article detail response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return Response(WechatArticleSerializer(self.get_object()).data)

    @extend_schema(
        operation_id="we_rss_articles_destroy",
        tags=[WE_RSS_TAG],
        summary="Delete one article",
        description=f"Delete an article record within the current tenant. {WE_RSS_AUTH_DESCRIPTION}",
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
        summary="Import article by URL",
        description=(
            "Create an import task from a public WeChat article URL and bind the result to the current tenant's "
            f"featured feed. {WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        request=request_body(
            ArticleImportSerializer,
            request_example(
                "Article import request",
                {"url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc"},
                description="Create an import task from a public WeChat article URL.",
            ),
        ),
        responses={
            200: json_response(
                WechatSyncTaskSerializer,
                "Article import task created.",
                ARTICLE_IMPORT_TASK_EXAMPLE,
                example_name="Article import response",
                message="Operation succeeded",
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
        summary="Refresh article content",
        description=(
            "Create a task to re-fetch article content, publish time, and engagement metrics for one article. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        request=None,
        responses={
            200: json_response(
                WechatSyncTaskSerializer,
                "Article refresh task created.",
                ARTICLE_REFRESH_TASK_EXAMPLE,
                example_name="Article refresh response",
                message="Operation succeeded",
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
        operation_id="we_rss_articles_update_favorite",
        tags=[WE_RSS_TAG],
        summary="Update article favorite status",
        description=f"Mark or unmark an article as favorite for the current member. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        request=request_body(
            ArticleFavoriteUpdateSerializer,
            request_example(
                "Article favorite update request",
                {"is_favorite": True},
                description="Favorite the selected article for the current member.",
            ),
        ),
        responses={
            200: json_response(
                WechatArticleSerializer,
                "Article favorite status updated.",
                {**ARTICLE_EXAMPLE, "is_favorite": True},
                example_name="Article favorite update response",
                message="Operation succeeded",
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
            member=request.user,
            is_favorite=serializer.validated_data["is_favorite"],
        )
        return Response(WechatArticleSerializer(article).data)

    @extend_schema(
        operation_id="we_rss_articles_tags_list",
        tags=[WE_RSS_TAG],
        summary="List current member tags on an article",
        description=f"Return the current member's private tags attached to one article. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        responses={
            200: json_response(
                MemberTagSerializer(many=True),
                "Article tags fetched successfully.",
                [MEMBER_TAG_EXAMPLE],
                example_name="Article tags response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["get"], url_path="tags")
    def list_tags(self, request, *args, **kwargs):
        article = self.get_object()
        tags = TagService.list_article_tags(article=article, member=request.user)
        return Response(MemberTagSerializer(tags, many=True).data)

    @extend_schema(
        operation_id="we_rss_articles_tags_attach",
        tags=[WE_RSS_TAG],
        summary="Attach existing tags to an article",
        description=f"Attach one or more existing member tags to an article in the current tenant. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        request=request_body(
            TagRelationWriteSerializer,
            request_example(
                "Article tag attach request",
                TAG_RELATION_WRITE_EXAMPLE,
                description="Attach the listed tag IDs to the selected article.",
            ),
        ),
        responses={
            200: json_response(
                MemberTagSerializer(many=True),
                "Article tags updated successfully.",
                [MEMBER_TAG_EXAMPLE],
                example_name="Article tag attach response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"], url_path="tags/attach")
    def attach_tags(self, request, *args, **kwargs):
        article = self.get_object()
        serializer = TagRelationWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tags = TagService.attach_tags_to_article(
            article=article,
            member=request.user,
            tag_ids=serializer.validated_data["tag_ids"],
        )
        return Response(MemberTagSerializer(tags, many=True).data)

    @extend_schema(
        operation_id="we_rss_articles_tags_detach",
        tags=[WE_RSS_TAG],
        summary="Detach tags from an article",
        description=f"Detach one or more existing member tags from an article in the current tenant. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        request=request_body(
            TagRelationWriteSerializer,
            request_example(
                "Article tag detach request",
                TAG_RELATION_WRITE_EXAMPLE,
                description="Detach the listed tag IDs from the selected article.",
            ),
        ),
        responses={
            200: json_response(
                MemberTagSerializer(many=True),
                "Article tags updated successfully.",
                [MEMBER_TAG_EXAMPLE],
                example_name="Article tag detach response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"], url_path="tags/detach")
    def detach_tags(self, request, *args, **kwargs):
        article = self.get_object()
        serializer = TagRelationWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tags = TagService.detach_tags_from_article(
            article=article,
            member=request.user,
            tag_ids=serializer.validated_data["tag_ids"],
        )
        return Response(MemberTagSerializer(tags, many=True).data)


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
        summary="List sync tasks",
        description=f"Return sync tasks for the current tenant with optional filters. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(
            TASK_TYPE_PARAMETER,
            TASK_STATUS_PARAMETER,
            TASK_TARGET_TYPE_PARAMETER,
            TASK_TARGET_ID_PARAMETER,
        ),
        responses={
            200: json_response(
                WechatSyncTaskSerializer(many=True),
                "Task list fetched successfully.",
                [FEED_SYNC_TASK_EXAMPLE, ARTICLE_IMPORT_TASK_FAILED_EXAMPLE],
                example_name="Task list response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def list(self, request, *args, **kwargs):
        return Response(WechatSyncTaskSerializer(self.get_queryset(), many=True).data)

    @extend_schema(
        operation_id="we_rss_tasks_retrieve",
        tags=[WE_RSS_TAG],
        summary="Retrieve sync task detail",
        description=f"Return status, payload, and results for one sync task. {WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(TASK_ID_PARAMETER),
        responses={
            200: json_response(
                WechatSyncTaskSerializer,
                "Task detail fetched successfully.",
                FEED_SYNC_TASK_EXAMPLE,
                example_name="Task detail response",
                message="Operation succeeded",
                examples=[
                    success_example(
                        "Feed sync task success response",
                        FEED_SYNC_TASK_EXAMPLE,
                        message="Operation succeeded",
                    ),
                    success_example(
                        "Feed sync task failed response",
                        FEED_SYNC_TASK_FAILED_EXAMPLE,
                        message="Operation succeeded",
                    ),
                    success_example(
                        "Article import task response",
                        ARTICLE_IMPORT_TASK_EXAMPLE,
                        message="Operation succeeded",
                    ),
                    success_example(
                        "Article refresh task response",
                        ARTICLE_REFRESH_TASK_EXAMPLE,
                        message="Operation succeeded",
                    ),
                    success_example(
                        "Article refresh task failed response",
                        ARTICLE_REFRESH_TASK_FAILED_EXAMPLE,
                        message="Operation succeeded",
                    ),
                ],
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return Response(WechatSyncTaskSerializer(self.get_object()).data)
