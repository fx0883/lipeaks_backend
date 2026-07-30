import json

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, OpenApiTypes, extend_schema
from django.http import StreamingHttpResponse
from rest_framework.response import Response

from common.schema.responses import common_error_responses
from we_rss.schema import (
    ARTICLE_EXAMPLE,
    ARTICLE_STATS_BATCH_REFRESH_REQUEST_ARTICLE_IDS_EXAMPLE,
    ARTICLE_STATS_BATCH_REFRESH_REQUEST_FEED_EXAMPLE,
    ARTICLE_STATS_BATCH_REFRESH_REQUEST_MEMBER_EXAMPLE,
    ARTICLE_STATS_REFRESH_BY_URL_REQUEST_EXAMPLE,
    ARTICLE_STATS_REFRESH_TASK_EXAMPLE,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    json_response,
    request_body,
    request_example,
    with_tenant_header,
)
from we_rss.serializers import (
    ArticleStatsBatchRefreshSerializer,
    ArticleStatsRefreshByUrlSerializer,
    WechatArticleSerializer,
)
from we_rss.services.article_stats_service import ArticleStatsRefreshService
from we_rss.renderers import EventStreamRenderer
from we_rss.views.base import WeRssTenantGenericViewSet


class ArticleStatsViewSet(WeRssTenantGenericViewSet):
    serializer_class = ArticleStatsRefreshByUrlSerializer
    renderer_classes = [EventStreamRenderer]

    def get_serializer_class(self):
        if self.action == "refresh":
            return ArticleStatsBatchRefreshSerializer
        return ArticleStatsRefreshByUrlSerializer

    @staticmethod
    def _encode_stream_event(event, payload):
        return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"

    def _build_stream_response(self, stream):
        response = StreamingHttpResponse(stream, content_type="text/event-stream; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    def _stream_article_stats_refresh(self, *, articles, selector_type, feed_id=None, member_id=None):
        def stream():
            total = len(articles)
            success_count = 0
            failed_count = 0
            refreshed_articles = []
            failed_articles = []

            yield self._encode_stream_event(
                "start",
                {
                    "selector_type": selector_type,
                    "feed_id": feed_id,
                    "member_id": member_id,
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
                    refreshed = ArticleStatsRefreshService.refresh_article_stats_for_article(article=article)
                    success_count += 1
                    payload = ArticleStatsRefreshService.build_article_log_payload(
                        article=refreshed,
                        index=index,
                        total=total,
                        status="success",
                    )
                    refreshed_articles.append(payload)
                except Exception as exc:
                    failed_count += 1
                    payload = ArticleStatsRefreshService.build_article_log_payload(
                        article=article,
                        index=index,
                        total=total,
                        status="failed",
                        error=str(exc),
                    )
                    failed_articles.append(payload)

                payload.update(
                    {
                        "selector_type": selector_type,
                        "feed_id": feed_id,
                        "member_id": member_id,
                        "success_count": success_count,
                        "failed_count": failed_count,
                    }
                )
                ArticleStatsRefreshService.log_refresh_progress(payload)
                yield self._encode_stream_event("progress", payload)

            yield self._encode_stream_event(
                "done",
                {
                    "selector_type": selector_type,
                    "feed_id": feed_id,
                    "member_id": member_id,
                    "total": total,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "progress": 100,
                    "status": "done",
                    "articles": refreshed_articles,
                    "failed_articles": failed_articles,
                },
            )

        return self._build_stream_response(stream())

    @extend_schema(
        operation_id="we_rss_article_stats_refresh_by_url",
        tags=[WE_RSS_TAG],
        summary="Refresh article stats by URL",
        description=(
            "Stream stats refresh progress for one existing member-visible article by its public WeChat URL. "
            "The response content type is `text/event-stream`. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        request=request_body(
            ArticleStatsRefreshByUrlSerializer,
            request_example(
                "Article stats refresh by URL request",
                ARTICLE_STATS_REFRESH_BY_URL_REQUEST_EXAMPLE,
                description="Refresh one existing article by its public WeChat URL.",
            ),
        ),
        responses={
            (200, "text/event-stream"): OpenApiResponse(
                response=OpenApiTypes.STR,
                description="Returns `text/event-stream` with `start`, `progress`, and `done` events.",
                examples=[
                    OpenApiExample(
                        "Article stats refresh stream example",
                        value=(
                            "event: progress\n"
                            'data: {"status":"success","title":"Example Article","read_num":128,'
                            '"success_count":1,"failed_count":0,"progress":100}\n\n'
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
    def refresh_by_url(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = ArticleStatsRefreshService.get_article_for_refresh_by_url(
            tenant=request.user.tenant,
            member=request.user,
            article_url=serializer.validated_data["url"],
        )
        return self._stream_article_stats_refresh(
            articles=[article],
            selector_type="url",
        )

    @extend_schema(
        operation_id="we_rss_article_stats_batch_refresh",
        tags=[WE_RSS_TAG],
        summary="Refresh article stats in batch",
        description=(
            "Stream article stats refresh progress for a selected article set, one feed, or all articles under "
            f"one member's subscribed feeds. Resolved articles always respect member-visible scope. "
            "The response content type is `text/event-stream`; each refreshed article emits one progress event. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        request=request_body(
            ArticleStatsBatchRefreshSerializer,
            request_example(
                "Article stats batch refresh by article ids request",
                ARTICLE_STATS_BATCH_REFRESH_REQUEST_ARTICLE_IDS_EXAMPLE,
                description="Refresh the selected article IDs asynchronously.",
            ),
            request_example(
                "Article stats batch refresh by feed request",
                ARTICLE_STATS_BATCH_REFRESH_REQUEST_FEED_EXAMPLE,
                description="Refresh all articles under one feed asynchronously.",
            ),
            request_example(
                "Article stats batch refresh by member request",
                ARTICLE_STATS_BATCH_REFRESH_REQUEST_MEMBER_EXAMPLE,
                description="Refresh all articles under feeds subscribed by one member asynchronously.",
            ),
        ),
        responses={
            (200, "text/event-stream"): OpenApiResponse(
                response=OpenApiTypes.STR,
                description="Returns `text/event-stream` with `start`, per-article `progress`, and `done` events.",
                examples=[
                    OpenApiExample(
                        "Article stats batch refresh stream example",
                        value=(
                            "event: start\n"
                            'data: {"selector_type":"article_ids","total":2,"status":"running"}\n\n'
                            "event: done\n"
                            'data: {"selector_type":"article_ids","total":2,"success_count":2,'
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
    def refresh(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        article_ids = serializer.validated_data.get("article_ids")
        feed_id = serializer.validated_data.get("feed_id")
        member_id = serializer.validated_data.get("member_id")
        window_days = serializer.validated_data.get("window_days")
        start_date = serializer.validated_data.get("start_date")
        end_date = serializer.validated_data.get("end_date")

        selector_type = ArticleStatsRefreshService.determine_selector_type(
            article_ids=article_ids,
            feed_id=feed_id,
            member_id=member_id,
        )
        articles = ArticleStatsRefreshService.get_articles_for_refresh(
            tenant=request.user.tenant,
            member=request.user,
            article_ids=article_ids,
            feed_id=feed_id,
            member_id=member_id,
            window_days=window_days,
            start_date=start_date,
            end_date=end_date,
        )

        return self._stream_article_stats_refresh(
            articles=articles,
            selector_type=selector_type,
            feed_id=feed_id,
            member_id=member_id,
        )
