import json
from datetime import datetime, timezone as datetime_timezone

from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from django.http import Http404
from django.http import StreamingHttpResponse
from django.db.models import DateTimeField, IntegerField, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.pagination import StandardResultsSetPagination
from common.schema.responses import common_error_responses
from we_rss.models import WechatArticle, WechatSyncTask
from we_rss.schema import (
    ARTICLE_BATCH_DELETE_REQUEST_EXAMPLE,
    ARTICLE_BATCH_DELETE_RESPONSE_EXAMPLE,
    ARTICLE_EXAMPLE,
    ARTICLE_PUBLIC_SEARCH_LIMIT_PARAMETER,
    ARTICLE_PUBLIC_SEARCH_QUERY_PARAMETER,
    ARTICLE_FEED_ID_PARAMETER,
    ARTICLE_EXPORT_CSV_EXAMPLE,
    ARTICLE_FAVORITE_ONLY_PARAMETER,
    ARTICLE_ID_PARAMETER,
    ARTICLE_EXPORT_REQUEST_ARTICLE_IDS_EXAMPLE,
    ARTICLE_EXPORT_REQUEST_MEMBER_EXAMPLE,
    ARTICLE_EXPORT_REQUEST_FEED_EXAMPLE,
    ARTICLE_IMPORT_TASK_EXAMPLE,
    ARTICLE_IMPORT_TASK_FAILED_EXAMPLE,
    ARTICLE_REFRESH_TASK_EXAMPLE,
    ARTICLE_REFRESH_TASK_FAILED_EXAMPLE,
    ARTICLE_SEARCH_PARAMETER,
    ARTICLE_SORT_BY_PARAMETER,
    ARTICLE_SORT_ORDER_PARAMETER,
    WECHAT_ARTICLE_SEARCH_RESPONSE_EXAMPLE,
    MEMBER_TAG_EXAMPLE,
    ARTICLE_TYPE_PARAMETER,
    FEED_CONTENT_REFRESH_TASK_EXAMPLE,
    FEED_SYNC_TASK_FAILED_EXAMPLE,
    FEED_SYNC_TASK_PARTIAL_SUCCESS_EXAMPLE,
    FEED_SYNC_TASK_EXAMPLE,
    FEED_SYNC_TASK_SUCCESS_EXAMPLE,
    FEED_SYNC_TASK_TIMED_OUT_EXAMPLE,
    TAG_IDS_PARAMETER,
    TAG_RELATION_WRITE_EXAMPLE,
    TASK_ID_PARAMETER,
    TASK_STATUS_PARAMETER,
    TASK_TARGET_ID_PARAMETER,
    TASK_TARGET_TYPE_PARAMETER,
    TASK_TYPE_PARAMETER,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    csv_response,
    json_response,
    request_body,
    request_example,
    success_example,
    with_tenant_header,
)
from we_rss.serializers import (
    ArticleBatchDeleteResponseSerializer,
    ArticleBatchDeleteSerializer,
    ArticleExportSerializer,
    ArticleFavoriteUpdateSerializer,
    ArticleImportSerializer,
    MemberTagSerializer,
    TagRelationWriteSerializer,
    WechatArticleSearchQuerySerializer,
    WechatArticleSearchResponseSerializer,
    WechatArticleSerializer,
    WechatSyncTaskSerializer,
)
from we_rss.renderers import EventStreamRenderer
from we_rss.services.article_search_service import ArticleSearchService
from we_rss.services.article_service import ArticleService, WechatArticleGateway, get_article_markdown_service
from we_rss.services.article_visibility_service import ArticleVisibilityService
from we_rss.services.feed_service import FeedService
from we_rss.services.member_article_state_service import MemberArticleStateService
from we_rss.services.tag_service import TagService
from we_rss.views.base import WeRssTenantGenericViewSet, WeRssTenantModelViewSet


class ArticleApiGatewayMixin:
    def get_gateway(self):
        return WechatArticleGateway()


class ArticleViewSet(ArticleApiGatewayMixin, WeRssTenantModelViewSet):
    queryset = WechatArticle.objects.select_related("feed")
    serializer_class = WechatArticleSerializer
    pagination_class = StandardResultsSetPagination
    ARTICLE_LIST_SORT_FIELDS = {
        "read_num": IntegerField(),
        "publish_time": DateTimeField(),
        "old_like_num": IntegerField(),
        "collect_num": IntegerField(),
        "share_num": IntegerField(),
        "comment_total_count": IntegerField(),
    }
    ARTICLE_LIST_EARLIEST_PUBLISH_TIME = datetime(1970, 1, 1, tzinfo=datetime_timezone.utc)

    @staticmethod
    def _encode_stream_event(event, payload):
        return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"

    @staticmethod
    def _build_stream_response(stream):
        response = StreamingHttpResponse(stream, content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    def get_renderers(self):
        if getattr(self, "action", None) == "refresh":
            return [EventStreamRenderer()]
        return super().get_renderers()

    def _get_feed_id_filter(self):
        feed_id = self.request.query_params.get("feed_id", "").strip()
        if not feed_id:
            return None
        try:
            return int(feed_id)
        except (TypeError, ValueError):
            raise ValidationError({"feed_id": ["A valid integer is required."]})

    @classmethod
    def _get_supported_sort_fields_message(cls):
        return f"Supported values are: {', '.join(cls.ARTICLE_LIST_SORT_FIELDS.keys())}."

    def _apply_article_list_sorting(self, queryset):
        sort_by = self.request.query_params.get("sort_by", "").strip()
        if not sort_by:
            return queryset.order_by("-publish_time", "-id")

        output_field = self.ARTICLE_LIST_SORT_FIELDS.get(sort_by)
        if output_field is None:
            raise ValidationError({"sort_by": [self._get_supported_sort_fields_message()]})

        sort_order = self.request.query_params.get("sort_order", "desc").strip().lower() or "desc"
        if sort_order not in {"asc", "desc"}:
            raise ValidationError({"sort_order": ["Supported values are: asc, desc."]})

        default_value = self.ARTICLE_LIST_EARLIEST_PUBLISH_TIME if sort_by == "publish_time" else 0
        sort_expression = Coalesce(sort_by, Value(default_value), output_field=output_field)
        if sort_order == "desc":
            sort_expression = sort_expression.desc()
            tie_breakers = ("-publish_time", "-id")
        else:
            sort_expression = sort_expression.asc()
            tie_breakers = ("publish_time", "id")
        return queryset.order_by(sort_expression, *tie_breakers)

    def get_queryset(self):
        base_queryset = super().get_queryset().select_related("feed")
        feed_id = self._get_feed_id_filter()
        if feed_id is None:
            queryset = ArticleVisibilityService.get_visible_article_queryset(
                tenant=self.request.user.tenant,
                member=self.request.user,
                queryset=base_queryset,
            )
        else:
            queryset = ArticleVisibilityService.get_tenant_visible_article_queryset(
                tenant=self.request.user.tenant,
                member=self.request.user,
                queryset=base_queryset.filter(feed_id=feed_id),
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

        return self._apply_article_list_sorting(queryset)

    def get_object(self):
        article = ArticleVisibilityService.get_tenant_visible_article(
            tenant=self.request.user.tenant,
            member=self.request.user,
            article_id=self.kwargs[self.lookup_field],
            queryset=super().get_queryset().select_related("feed"),
        )
        if article is None:
            raise Http404
        return article

    def get_serializer_class(self):
        if self.action == "search":
            return WechatArticleSearchResponseSerializer
        if self.action == "import_by_url":
            return ArticleImportSerializer
        if self.action == "batch_delete":
            return ArticleBatchDeleteSerializer
        if self.action == "export":
            return ArticleExportSerializer
        if self.action == "update_favorite":
            return ArticleFavoriteUpdateSerializer
        if self.action in {"attach_tags", "detach_tags"}:
            return TagRelationWriteSerializer
        if self.action == "list_tags":
            return MemberTagSerializer
        return WechatArticleSerializer

    @extend_schema(
        operation_id="we_rss_articles_list",
        tags=[WE_RSS_TAG],
        summary="List visible articles",
        description=(
            "Return WeChat articles currently visible to the authenticated member. "
            "Without `feed_id`, the list is limited to subscribed feeds. "
            "With `feed_id`, the list returns all tenant articles under that feed except the current member's hidden "
            "articles. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(
            ARTICLE_TYPE_PARAMETER,
            ARTICLE_SEARCH_PARAMETER,
            ARTICLE_FAVORITE_ONLY_PARAMETER,
            ARTICLE_FEED_ID_PARAMETER,
            TAG_IDS_PARAMETER,
            ARTICLE_SORT_BY_PARAMETER,
            ARTICLE_SORT_ORDER_PARAMETER,
        ),
        responses={
            200: json_response(
                inline_serializer(
                    name="WeRssArticleListData",
                    fields={
                        "pagination": inline_serializer(
                            name="WeRssArticleListPagination",
                            fields={
                                "count": serializers.IntegerField(),
                                "next": serializers.CharField(allow_null=True),
                                "previous": serializers.CharField(allow_null=True),
                                "page_size": serializers.IntegerField(),
                                "current_page": serializers.IntegerField(),
                                "total_pages": serializers.IntegerField(),
                            },
                        ),
                        "results": WechatArticleSerializer(many=True),
                    },
                ),
                "Article list fetched successfully.",
                {
                    "pagination": {
                        "count": 1,
                        "next": None,
                        "previous": None,
                        "page_size": 10,
                        "current_page": 1,
                        "total_pages": 1,
                    },
                    "results": [ARTICLE_EXAMPLE],
                },
                example_name="Article list response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = WechatArticleSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = WechatArticleSerializer(queryset, many=True)
        return Response(
            {
                "pagination": {
                    "count": queryset.count(),
                    "next": None,
                    "previous": None,
                    "page_size": queryset.count(),
                    "current_page": 1,
                    "total_pages": 1,
                },
                "results": serializer.data,
            }
        )

    @extend_schema(
        operation_id="we_rss_articles_search",
        tags=[WE_RSS_TAG],
        summary="Search public WeChat articles",
        description=(
            "Search public WeChat articles through the native Sogou Weixin search service. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(
            ARTICLE_PUBLIC_SEARCH_QUERY_PARAMETER,
            ARTICLE_PUBLIC_SEARCH_LIMIT_PARAMETER,
        ),
        responses={
            200: json_response(
                WechatArticleSearchResponseSerializer,
                "Public article search completed successfully.",
                WECHAT_ARTICLE_SEARCH_RESPONSE_EXAMPLE,
                example_name="Article search response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=False, methods=["get"])
    def search(self, request, *args, **kwargs):
        serializer = WechatArticleSearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        result = ArticleSearchService.search_wechat_articles(
            query=serializer.validated_data["query"],
            limit=serializer.validated_data["limit"],
        )
        return Response(WechatArticleSearchResponseSerializer(result).data)

    @extend_schema(
        operation_id="we_rss_articles_retrieve",
        tags=[WE_RSS_TAG],
        summary="Retrieve one article",
        description=(
            "Return one tenant article unless the current member has hidden it. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
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
        summary="Hide one article",
        description=(
            "Hide one article from the authenticated member without deleting the shared article record. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        responses={204: OpenApiResponse(description="Article deleted"), **common_error_responses},
    )
    def destroy(self, request, *args, **kwargs):
        article = self.get_object()
        MemberArticleStateService.set_hidden(
            article=article,
            member=request.user,
            is_hidden=True,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        operation_id="we_rss_articles_batch_delete",
        tags=[WE_RSS_TAG],
        summary="Batch hide articles",
        description=(
            "Hide multiple articles from the authenticated member in one request. "
            "The request fails when any article ID is outside the current tenant scope or already hidden from the "
            "current member's accessible article scope. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        request=request_body(
            ArticleBatchDeleteSerializer,
            request_example(
                "Article batch delete request",
                ARTICLE_BATCH_DELETE_REQUEST_EXAMPLE,
                description="Hide the selected article IDs in the same order sent by the frontend.",
            ),
        ),
        responses={
            200: json_response(
                ArticleBatchDeleteResponseSerializer,
                "Articles hidden successfully.",
                ARTICLE_BATCH_DELETE_RESPONSE_EXAMPLE,
                example_name="Article batch delete response",
                message="Operation succeeded",
            ),
            **common_error_responses,
        },
    )
    @action(detail=False, methods=["post"], url_path="batch-delete")
    def batch_delete(self, request, *args, **kwargs):
        serializer = ArticleBatchDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ArticleService.batch_delete_articles(
            tenant=request.user.tenant,
            member=request.user,
            article_ids=serializer.validated_data["article_ids"],
        )
        return Response(result)

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
        summary="Refresh article Markdown content",
        description=(
            "Stream Markdown content refresh progress for one tenant article unless the current member has hidden it. "
            "The response content type is `text/event-stream`. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(ARTICLE_ID_PARAMETER),
        request=None,
        responses={
            200: None,
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"])
    def refresh(self, request, *args, **kwargs):
        article = self.get_object()

        def stream():
            yield self._encode_stream_event(
                "start",
                {
                    "article_id": article.id,
                    "feed_id": article.feed_id,
                    "title": article.title,
                    "url": article.url,
                    "status": "running",
                    "total": 1,
                    "success_count": 0,
                    "failed_count": 0,
                    "progress": 0,
                },
            )
            try:
                markdown_content = ArticleService.refresh_article_markdown(
                    article=article,
                    markdown_service=get_article_markdown_service(),
                    sleep_seconds=0,
                )
                article.refresh_from_db()
                yield self._encode_stream_event(
                    "done",
                    {
                        "article_id": article.id,
                        "feed_id": article.feed_id,
                        "title": article.title,
                        "url": article.url,
                        "status": "done",
                        "total": 1,
                        "success_count": 1,
                        "failed_count": 0,
                        "progress": 100,
                        "markdown_length": len(markdown_content),
                    },
                )
            except Exception as exc:
                yield self._encode_stream_event(
                    "error",
                    {
                        "article_id": article.id,
                        "feed_id": article.feed_id,
                        "title": article.title,
                        "url": article.url,
                        "status": "failed",
                        "total": 1,
                        "success_count": 0,
                        "failed_count": 1,
                        "progress": 100,
                        "error": str(exc),
                    },
                )

        return self._build_stream_response(stream())

    @extend_schema(
        operation_id="we_rss_articles_export",
        tags=[WE_RSS_TAG],
        summary="Export articles as CSV",
        description=(
            "Export articles as one CSV file. Selectors are resolved in this order: `article_ids`, `member_id`, "
            f"then `feed_id`. Export results always respect the resolved member-visible article scope. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        request=request_body(
            ArticleExportSerializer,
            request_example(
                "Article export by article ids request",
                ARTICLE_EXPORT_REQUEST_ARTICLE_IDS_EXAMPLE,
                description="Export the selected article IDs in the same order sent by the frontend.",
            ),
            request_example(
                "Article export by member request",
                ARTICLE_EXPORT_REQUEST_MEMBER_EXAMPLE,
                description="Export all articles under feeds subscribed by the selected member.",
            ),
            request_example(
                "Article export by feed request",
                ARTICLE_EXPORT_REQUEST_FEED_EXAMPLE,
                description="Export all articles under one feed.",
            ),
        ),
        responses={
            (200, "text/csv"): csv_response(
                "CSV export file.",
                ARTICLE_EXPORT_CSV_EXAMPLE,
                example_name="Article export CSV response",
            ),
            **common_error_responses,
        },
    )
    @action(detail=False, methods=["post"], url_path="export")
    def export(self, request, *args, **kwargs):
        serializer = ArticleExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return ArticleService.export_articles_csv(
            tenant=request.user.tenant,
            member=request.user,
            article_ids=serializer.validated_data.get("article_ids"),
            member_id=serializer.validated_data.get("member_id"),
            feed_id=serializer.validated_data.get("feed_id"),
        )

    @extend_schema(
        operation_id="we_rss_articles_update_favorite",
        tags=[WE_RSS_TAG],
        summary="Update article favorite status",
        description=(
            "Mark or unmark one tenant article as favorite for the current member unless the article has been hidden "
            f"by the same member. {WE_RSS_AUTH_DESCRIPTION}"
        ),
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
        description=(
            "Return the current member's private tags attached to one tenant article unless the article has been "
            f"hidden by the same member. {WE_RSS_AUTH_DESCRIPTION}"
        ),
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
        description=(
            "Attach one or more existing member tags to one tenant article unless the article has been hidden by the "
            f"same member. {WE_RSS_AUTH_DESCRIPTION}"
        ),
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
        description=(
            "Detach one or more existing member tags from one tenant article unless the article has been hidden by "
            f"the same member. {WE_RSS_AUTH_DESCRIPTION}"
        ),
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
        description=(
            "Return status, payload, and results for one sync task. For feed sync, the frontend "
            "should poll the parent `feed_sync_run` task every 5 seconds and append a new batch "
            "or refresh the article list exactly once only when "
            "`result_payload.latest_completed_batch.batch_no` changes. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(TASK_ID_PARAMETER),
        responses={
            200: json_response(
                WechatSyncTaskSerializer,
                "Task detail fetched successfully.",
                FEED_SYNC_TASK_SUCCESS_EXAMPLE,
                example_name="Task detail response",
                message="Operation succeeded",
                examples=[
                    success_example(
                        "Feed sync task success response",
                        FEED_SYNC_TASK_SUCCESS_EXAMPLE,
                        message="Operation succeeded",
                    ),
                    success_example(
                        "Feed sync task failed response",
                        FEED_SYNC_TASK_FAILED_EXAMPLE,
                        message="Operation succeeded",
                    ),
                    success_example(
                        "Feed sync task timed out response",
                        FEED_SYNC_TASK_TIMED_OUT_EXAMPLE,
                        message="Operation succeeded",
                    ),
                    success_example(
                        "Feed sync task partial success response",
                        FEED_SYNC_TASK_PARTIAL_SUCCESS_EXAMPLE,
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
                    success_example(
                        "Feed content refresh task response",
                        FEED_CONTENT_REFRESH_TASK_EXAMPLE,
                        message="Operation succeeded",
                    ),
                ],
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        task = FeedService.refresh_parent_run_task_for_polling(task=task)
        return Response(WechatSyncTaskSerializer(task).data)
