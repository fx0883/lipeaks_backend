from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from common.schema.responses import common_error_responses
from we_rss.models import MemberFeedTagRelation, MemberTag, WechatArticle, WechatFeed
from we_rss.querysets import tenant_queryset
from we_rss.schema import (
    ARTICLE_HTML_EXAMPLE,
    FEED_RSS_XML_EXAMPLE,
    RSS_ARTICLE_ID_PARAMETER,
    RSS_FEED_ID_PARAMETER,
    RSS_TAG_ID_PARAMETER,
    TAG_RSS_XML_EXAMPLE,
    TENANT_RSS_XML_EXAMPLE,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    html_response,
    with_tenant_header,
    xml_response,
)
from we_rss.services.rss_service import RssService
from we_rss.services.article_visibility_service import ArticleVisibilityService
from we_rss.views.base import WeRssTenantApiView


class TenantRssView(WeRssTenantApiView):

    @extend_schema(
        operation_id="we_rss_rss_tenant",
        tags=[WE_RSS_TAG],
        summary="Get tenant RSS",
        description=(
            "Return RSS XML for all articles currently visible to the authenticated member. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        responses={
            (200, "application/xml"): xml_response(
                "RSS XML for the current tenant.",
                TENANT_RSS_XML_EXAMPLE,
                example_name="Tenant RSS XML",
            ),
            **common_error_responses,
        },
    )
    def get(self, request):
        articles = ArticleVisibilityService.get_visible_article_queryset(
            tenant=request.user.tenant,
            member=request.user,
            queryset=tenant_queryset(WechatArticle.objects.select_related("feed"), request),
        )
        xml = RssService.build_tenant_rss(tenant=request.user.tenant, articles=articles)
        return HttpResponse(xml, content_type="application/xml")


class FeedRssView(WeRssTenantApiView):

    @extend_schema(
        operation_id="we_rss_rss_feed",
        tags=[WE_RSS_TAG],
        summary="Get feed RSS",
        description=(
            "Return RSS XML for one feed within the authenticated member's visible article scope. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(RSS_FEED_ID_PARAMETER),
        responses={
            (200, "application/xml"): xml_response(
                "RSS XML for one feed.",
                FEED_RSS_XML_EXAMPLE,
                example_name="Feed RSS XML",
            ),
            **common_error_responses,
        },
    )
    def get(self, request, feed_id):
        feed = get_object_or_404(tenant_queryset(WechatFeed.objects.all(), request), pk=feed_id)
        articles = ArticleVisibilityService.get_visible_article_queryset(
            tenant=request.user.tenant,
            member=request.user,
            queryset=tenant_queryset(WechatArticle.objects.select_related("feed").filter(feed=feed), request),
        )
        xml = RssService.build_feed_rss(feed=feed, articles=articles)
        return HttpResponse(xml, content_type="application/xml")


class TagRssView(WeRssTenantApiView):

    @extend_schema(
        operation_id="we_rss_rss_tag",
        tags=[WE_RSS_TAG],
        summary="Get tag RSS",
        description=(
            "Return RSS XML for one member-private tag using the current member's feed-tag relations. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(RSS_TAG_ID_PARAMETER),
        responses={
            (200, "application/xml"): xml_response(
                "RSS XML for one member-private tag.",
                TAG_RSS_XML_EXAMPLE,
                example_name="Tag RSS XML",
            ),
            **common_error_responses,
        },
    )
    def get(self, request, tag_id):
        tag = get_object_or_404(
            MemberTag.objects.filter(
                tenant=request.user.tenant,
                member=request.user,
            ),
            pk=tag_id,
        )
        related_feed_ids = MemberFeedTagRelation.objects.filter(
            tenant=request.user.tenant,
            member=request.user,
            tag=tag,
        ).values_list("feed_id", flat=True)
        articles = ArticleVisibilityService.get_visible_article_queryset(
            tenant=request.user.tenant,
            member=request.user,
            queryset=tenant_queryset(
                WechatArticle.objects.select_related("feed").filter(feed_id__in=related_feed_ids),
                request,
            ),
        )
        xml = RssService.build_tag_rss(tag=tag, articles=articles)
        return HttpResponse(xml, content_type="application/xml")


class ArticleContentView(WeRssTenantApiView):

    @extend_schema(
        operation_id="we_rss_rss_content",
        tags=[WE_RSS_TAG],
        summary="Get article Markdown",
        description=(
            "Return article Markdown for one article currently visible to the authenticated member. "
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(RSS_ARTICLE_ID_PARAMETER),
        responses={
            (200, "text/markdown"): html_response(
                "Markdown for one article.",
                ARTICLE_HTML_EXAMPLE,
                example_name="Article Markdown response",
            ),
            **common_error_responses,
        },
    )
    def get(self, request, article_id):
        article = get_object_or_404(
            ArticleVisibilityService.get_visible_article_queryset(
                tenant=request.user.tenant,
                member=request.user,
                queryset=tenant_queryset(WechatArticle.objects.all(), request),
            ),
            pk=article_id,
        )
        return HttpResponse(RssService.build_article_content(article=article), content_type="text/markdown")
