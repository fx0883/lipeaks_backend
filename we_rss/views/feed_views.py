import json
from datetime import timedelta

from django.db.models import Exists, OuterRef
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, OpenApiTypes, extend_schema
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.schema.responses import common_error_responses
from we_rss.models import MemberFeedSubscription, WechatArticle, WechatFeed
from we_rss.schema import (
    FEED_ARTICLE_CLEAR_EXAMPLE,
    FEED_EXAMPLE,
    FEED_ID_PARAMETER,
    FEED_SEARCH_EXAMPLE,
    FEED_SYNC_TASK_FAILED_EXAMPLE,
    FEED_SUBSCRIBED_ONLY_PARAMETER,
    FEED_SYNC_TASK_EXAMPLE,
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
    FeedSyncBatchRequestSerializer,
    FeedSyncRequestSerializer,
    FeedSearchResultSerializer,
    FeedSubscriptionWriteSerializer,
    FeedWriteSerializer,
    MemberTagSerializer,
    TagRelationWriteSerializer,
    WechatFeedSerializer,
)
from we_rss.renderers import EventStreamRenderer
from we_rss.services.article_service import ArticleService, get_article_markdown_service
from we_rss.services.feed_service import FeedService, WechatFeedGateway
from we_rss.services.tag_service import TagService
from we_rss.views.base import WeRssTenantModelViewSet


class FeedApiGatewayMixin:
    def get_gateway(self):
        return WechatFeedGateway()


class FeedViewSet(FeedApiGatewayMixin, WeRssTenantModelViewSet):
    queryset = WechatFeed.objects.all()
    serializer_class = WechatFeedSerializer

    def get_renderers(self):
        if getattr(self, "action", None) in {"sync", "sync_batch", "refresh_content"}:
            return [EventStreamRenderer()]
        return super().get_renderers()

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
            return FeedSyncRequestSerializer
        if self.action == "sync_batch":
            return FeedSyncBatchRequestSerializer
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
        description=(
            "Delete one feed record in the current tenant, and cascade delete all articles "
            f"under that feed together with their related member relations. {WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        responses={204: OpenApiResponse(description="Feed deleted"), **common_error_responses},
    )
    def destroy(self, request, *args, **kwargs):
        feed = self.get_object()
        FeedService.delete_feed(feed=feed)
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
        operation_id="we_rss_feeds_refresh_content",
        tags=[WE_RSS_TAG],
        summary="Refresh feed article markdown content",
        description=(
            "Stream Markdown content refresh progress for all articles under one feed. "
            "The response content type is `text/event-stream`; each article emits one progress event. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        request=None,
        responses={
            (200, "text/event-stream"): OpenApiResponse(
                response=OpenApiTypes.STR,
                description=(
                    "Returns `text/event-stream`. The stream starts with `start`, then emits one `progress` "
                    "event for each refreshed article, and finishes with `done`."
                ),
                examples=[
                    OpenApiExample(
                        "Feed content refresh stream example",
                        value=(
                            "event: start\n"
                            'data: {"feed_id":11,"feed_name":"Example Feed","total":2,'
                            '"success_count":0,"failed_count":0,"progress":0,"status":"running"}\n\n'
                            "event: progress\n"
                            'data: {"feed_id":11,"article_id":101,"status":"success",'
                            '"progress":50,"success_count":1,"failed_count":0,"markdown_length":2048}\n\n'
                            "event: done\n"
                            'data: {"feed_id":11,"total":2,"success_count":2,'
                            '"failed_count":0,"progress":100,"status":"done"}\n\n'
                        ),
                        response_only=True,
                        media_type="text/event-stream",
                        status_codes=[200],
                    ),
                ],
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"], url_path="refresh-content")
    def refresh_content(self, request, *args, **kwargs):
        feed = self.get_object()
        markdown_service = get_article_markdown_service()

        def encode_event(event, payload):
            return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"

        def stream():
            articles = list(
                WechatArticle.objects.filter(
                    tenant=feed.tenant,
                    feed=feed,
                )
                .select_related("feed", "tenant")
                .order_by("id")
            )
            total = len(articles)
            success_count = 0
            failed_count = 0
            refreshed_articles = []
            failed_articles = []

            yield encode_event(
                "start",
                {
                    "feed_id": feed.id,
                    "feed_name": feed.mp_name,
                    "article_ids": [article.id for article in articles],
                    "total": total,
                    "success_count": 0,
                    "failed_count": 0,
                    "progress": 0,
                    "status": "running",
                },
            )

            for index, article in enumerate(articles, start=1):
                try:
                    markdown_content = ArticleService.refresh_article_markdown(
                        article=article,
                        markdown_service=markdown_service,
                        sleep_seconds=0,
                    )
                    success_count += 1
                    payload = {
                        "feed_id": feed.id,
                        "feed_name": feed.mp_name,
                        "article_id": article.id,
                        "title": article.title,
                        "url": article.url,
                        "index": index,
                        "total": total,
                        "status": "success",
                        "progress": int(index * 100 / total) if total else 100,
                        "success_count": success_count,
                        "failed_count": failed_count,
                        "markdown_length": len(markdown_content),
                    }
                    refreshed_articles.append(payload)
                except Exception as exc:
                    failed_count += 1
                    payload = {
                        "feed_id": feed.id,
                        "feed_name": feed.mp_name,
                        "article_id": article.id,
                        "title": article.title,
                        "url": article.url,
                        "index": index,
                        "total": total,
                        "status": "failed",
                        "progress": int(index * 100 / total) if total else 100,
                        "success_count": success_count,
                        "failed_count": failed_count,
                        "error": str(exc),
                    }
                    failed_articles.append(payload)

                yield encode_event("progress", payload)

            yield encode_event(
                "done",
                {
                    "feed_id": feed.id,
                    "feed_name": feed.mp_name,
                    "article_ids": [article.id for article in articles],
                    "total": total,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "progress": 100,
                    "status": "done",
                    "articles": refreshed_articles,
                    "failed_articles": failed_articles,
                },
            )

        response = StreamingHttpResponse(stream(), content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    @extend_schema(
        operation_id="we_rss_feeds_sync",
        tags=[WE_RSS_TAG],
        summary="Sync feed articles",
        description=(
            "Stream feed sync progress for one feed. The response content type is `text/event-stream`; "
            f"each completed batch emits one batch event. {WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(FEED_ID_PARAMETER),
        request=request_body(
            FeedSyncRequestSerializer,
            request_example(
                "Feed sync full request",
                {"sync_scope": "full", "refresh_markdown": False},
                description="Run a full feed sync from the beginning.",
            ),
            request_example(
                "Feed sync latest request",
                {"sync_scope": "latest", "refresh_markdown": False},
                description="Sync only until a normalized article URL already exists, then stop.",
            ),
            request_example(
                "Feed sync window request",
                {"sync_scope": "window", "window_days": 7, "refresh_markdown": False},
                description="Sync only articles from the last N days, then stop at the first older article.",
            ),
            request_example(
                "Feed sync with markdown refresh request",
                {"sync_scope": "full", "refresh_markdown": True},
                description="Run a full feed sync and refresh Markdown content for synced articles.",
            ),
        ),
        responses={
            (200, "text/event-stream"): OpenApiResponse(
                response=OpenApiTypes.STR,
                description=(
                    "Returns `text/event-stream`. The stream starts with `start`, then emits one `batch` "
                    "event for each completed sync batch, and finishes with `done` or `error`."
                ),
                examples=[
                    OpenApiExample(
                        "Feed sync stream example",
                        value=(
                            "event: start\n"
                            'data: {"feed_id":11,"status":"running","sync_scope":"full",'
                            '"batch_size":20,"batches_completed":0,"articles_synced":0}\n\n'
                            "event: batch\n"
                            'data: {"feed_id":11,"status":"success","batch_no":1,'
                            '"articles_synced":10,"articles_failed":0,"has_more":false}\n\n'
                            "event: done\n"
                            'data: {"feed_id":11,"status":"done","batches_completed":1,'
                            '"articles_synced":10,"articles_failed":0,"has_more":false}\n\n'
                        ),
                        response_only=True,
                        media_type="text/event-stream",
                        status_codes=[200],
                    ),
                ],
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"])
    def sync(self, request, *args, **kwargs):
        feed = self.get_object()
        serializer = FeedSyncRequestSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        sync_scope = serializer.validated_data["sync_scope"]
        window_days = serializer.validated_data.get("window_days")
        refresh_markdown = serializer.validated_data["refresh_markdown"]

        def encode_event(event, payload):
            return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"

        def stream():
            batch_size = FeedService.BATCH_SIZE
            batch_no = 1
            begin = 0
            batches_completed = 0
            articles_synced = 0
            articles_failed = 0
            article_ids = []
            failed_articles = []
            run_deadline = timezone.now() + timedelta(seconds=FeedService.RUN_TIMEOUT_SECONDS)

            yield encode_event(
                "start",
                {
                    "feed_id": feed.id,
                    "feed_name": feed.mp_name,
                    "sync_scope": sync_scope,
                    "window_days": window_days,
                    "refresh_markdown": refresh_markdown,
                    "batch_size": batch_size,
                    "status": "running",
                    "batches_completed": 0,
                    "articles_synced": 0,
                    "articles_failed": 0,
                    "next_begin": begin,
                    "has_more": True,
                },
            )

            try:
                while True:
                    batch_result = FeedService.execute_sync_batch_inline(
                        feed=feed,
                        updated_by=request.user,
                        gateway=self.get_gateway(),
                        batch_no=batch_no,
                        begin=begin,
                        batch_size=batch_size,
                        sync_scope=sync_scope,
                        window_days=window_days,
                        refresh_markdown=refresh_markdown,
                        run_deadline=run_deadline,
                    )
                    batches_completed += 1
                    article_ids = list(dict.fromkeys([*article_ids, *(batch_result.get("article_ids") or [])]))
                    articles_synced = len(article_ids)
                    articles_failed += int(batch_result.get("detail_failed_count") or 0)
                    failed_articles.extend(batch_result.get("failed_articles") or [])

                    payload = FeedService.build_feed_sync_progress_payload(
                        feed=feed,
                        batch_result=batch_result,
                        sync_scope=sync_scope,
                        window_days=window_days,
                        refresh_markdown=refresh_markdown,
                        batches_completed=batches_completed,
                        articles_synced=articles_synced,
                        articles_failed=articles_failed,
                    )
                    FeedService.log_feed_sync_progress(payload)
                    yield encode_event("batch", payload)

                    if not batch_result.get("has_more", False):
                        stop_reason = batch_result.get("stop_reason", "")
                        yield encode_event(
                            "done",
                            {
                                "feed_id": feed.id,
                                "feed_name": feed.mp_name,
                                "sync_scope": sync_scope,
                                "window_days": window_days,
                                "refresh_markdown": refresh_markdown,
                                "status": "done",
                                "batches_completed": batches_completed,
                                "articles_synced": articles_synced,
                                "articles_failed": articles_failed,
                                "article_ids": article_ids,
                                "failed_articles": failed_articles,
                                "next_begin": batch_result.get("next_begin"),
                                "has_more": False,
                                "stop_reason": stop_reason,
                                "stop_article_url": batch_result.get("stop_article_url", ""),
                                "stop_article_source_id": batch_result.get("stop_article_source_id", ""),
                                "stop_publish_time": batch_result.get("stop_publish_time"),
                            },
                        )
                        break

                    begin = int(batch_result.get("next_begin") or begin)
                    batch_no += 1
            except Exception as exc:
                error_payload = {
                    "feed_id": feed.id,
                    "feed_name": feed.mp_name,
                    "sync_scope": sync_scope,
                    "window_days": window_days,
                    "refresh_markdown": refresh_markdown,
                    "status": "failed",
                    "batches_completed": batches_completed,
                    "articles_synced": articles_synced,
                    "articles_failed": articles_failed,
                    "article_ids": article_ids,
                    "failed_articles": failed_articles,
                    "next_begin": begin,
                    "error": str(exc),
                }
                FeedService.log_feed_sync_progress(error_payload)
                yield encode_event("error", error_payload)

        response = StreamingHttpResponse(stream(), content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    @extend_schema(
        operation_id="we_rss_feeds_sync_batch",
        tags=[WE_RSS_TAG],
        summary="Sync multiple feeds serially",
        description=(
            "Stream serial batch feed sync progress. The response content type is `text/event-stream`; "
            "the backend executes the provided feed IDs in order and emits batch-level progress events. "
            "Events include `start`, `feed_start`, `feed_batch`, `feed_done`, `done`, `error`, and "
            "`heartbeat`. `feed_ids` are deduplicated while preserving first-seen order. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        request=request_body(
            FeedSyncBatchRequestSerializer,
            request_example(
                "Feed sync batch window request",
                {
                    "feed_ids": [11, 22, 33],
                    "sync_scope": "window",
                    "window_days": 7,
                    "refresh_markdown": False,
                    "continue_on_error": True,
                },
                description="Run a serial batch sync for the provided feed IDs.",
            ),
            request_example(
                "Feed sync batch latest request",
                {
                    "feed_ids": [20, 21, 22],
                    "sync_scope": "latest",
                    "refresh_markdown": False,
                    "continue_on_error": False,
                },
                description="Stop the whole batch immediately after the first failed feed.",
            ),
        ),
        responses={
            200: OpenApiResponse(
                description=(
                    "Returns `text/event-stream`. The stream starts with `start`, then emits `feed_start`, "
                    "`feed_batch`, `feed_done`, optional `heartbeat`, and finally `done` or `error`."
                ),
                examples=[
                    OpenApiExample(
                        "Batch sync success stream example",
                        value=(
                            "event: start\n"
                            'data: {"batch_task_id":12345,"status":"running","sync_scope":"window",'
                            '"window_days":7,"refresh_markdown":false,"continue_on_error":true,'
                            '"total_feeds":3,"queued_feed_ids":[11,22,33],"completed_feeds":0,'
                            '"success_feeds":0,"failed_feeds":0}\n\n'
                            "event: feed_start\n"
                            'data: {"batch_task_id":12345,"status":"running","feed_id":11,'
                            '"feed_index":1,"total_feeds":3,"completed_feeds":0,'
                            '"success_feeds":0,"failed_feeds":0}\n\n'
                            "event: feed_batch\n"
                            'data: {"batch_task_id":12345,"status":"running","feed_id":11,'
                            '"feed_index":1,"total_feeds":3,"completed_feeds":0,'
                            '"success_feeds":0,"failed_feeds":0,"batch_no":1,"batch_size":20,'
                            '"articles_synced":10,"articles_failed":0,"has_more":true,'
                            '"next_begin":20,"detail_success_count":10,"detail_failed_count":0}\n\n'
                            "event: feed_done\n"
                            'data: {"batch_task_id":12345,"status":"success","feed_id":11,'
                            '"feed_index":1,"total_feeds":3,"completed_feeds":1,'
                            '"success_feeds":1,"failed_feeds":0,"articles_synced":23,'
                            '"articles_failed":1,"detail_success_count":23,"detail_failed_count":1}\n\n'
                            "event: done\n"
                            'data: {"batch_task_id":12345,"status":"done","sync_scope":"window",'
                            '"window_days":7,"refresh_markdown":false,"continue_on_error":true,'
                            '"total_feeds":3,"completed_feeds":3,"success_feeds":2,"failed_feeds":1,'
                            '"results":[{"feed_id":11,"status":"success","articles_synced":23,'
                            '"articles_failed":1},{"feed_id":22,"status":"failed","error":"feed not found"},'
                            '{"feed_id":33,"status":"success","articles_synced":8,"articles_failed":0}]}\n\n'
                        ),
                        response_only=True,
                        media_type="text/event-stream",
                        status_codes=[200],
                    ),
                    OpenApiExample(
                        "Batch sync heartbeat stream example",
                        value=(
                            "event: heartbeat\n"
                            'data: {"batch_task_id":12345,"status":"running","current_feed_id":11,'
                            '"completed_feeds":0,"success_feeds":0,"failed_feeds":0,'
                            '"timestamp":"2026-05-13T12:00:00Z"}\n\n'
                        ),
                        response_only=True,
                        media_type="text/event-stream",
                        status_codes=[200],
                    ),
                    OpenApiExample(
                        "Batch sync aborted stream example",
                        value=(
                            "event: feed_done\n"
                            'data: {"batch_task_id":12345,"status":"failed","feed_id":22,'
                            '"feed_index":2,"total_feeds":3,"completed_feeds":2,'
                            '"success_feeds":1,"failed_feeds":1,"articles_synced":0,'
                            '"articles_failed":0,"error":"feed not found"}\n\n'
                            "event: error\n"
                            'data: {"batch_task_id":12345,"status":"failed",'
                            '"error":"batch sync aborted after feed failure"}\n\n'
                        ),
                        response_only=True,
                        media_type="text/event-stream",
                        status_codes=[200],
                    ),
                ],
            ),
            **common_error_responses,
        },
    )
    @action(detail=False, methods=["post"], url_path="sync-batch")
    def sync_batch(self, request, *args, **kwargs):
        serializer = FeedSyncBatchRequestSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)

        batch_task, event_stream_factory = FeedService.sync_feed_batch(
            tenant=request.user.tenant,
            created_by=request.user,
            gateway=self.get_gateway(),
            feed_ids=serializer.validated_data["feed_ids"],
            sync_scope=serializer.validated_data["sync_scope"],
            window_days=serializer.validated_data.get("window_days"),
            refresh_markdown=serializer.validated_data["refresh_markdown"],
            continue_on_error=serializer.validated_data["continue_on_error"],
        )

        def encode_event(event, payload):
            return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"

        def stream():
            try:
                for item in event_stream_factory():
                    yield encode_event(item["event"], item["data"])
            except Exception:
                yield encode_event(
                    "error",
                    {
                        "batch_task_id": batch_task.id,
                        "status": "failed",
                        "error": "batch sync initialization failed",
                    },
                )

        response = StreamingHttpResponse(stream(), content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
