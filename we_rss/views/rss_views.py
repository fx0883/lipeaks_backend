from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from common.schema.responses import common_error_responses
from we_rss.models import WechatArticle, WechatFeed
from we_rss.querysets import tenant_queryset
from we_rss.schema import (
    ARTICLE_HTML_EXAMPLE,
    FEED_RSS_XML_EXAMPLE,
    RSS_ARTICLE_ID_PARAMETER,
    RSS_FEED_ID_PARAMETER,
    TENANT_RSS_XML_EXAMPLE,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    html_response,
    with_tenant_header,
    xml_response,
)
from we_rss.services.rss_service import RssService
from we_rss.views.base import WeRssTenantApiView


class TenantRssView(WeRssTenantApiView):

    @extend_schema(
        operation_id="we_rss_rss_tenant",
        tags=[WE_RSS_TAG],
        summary="获取当前租户的聚合 RSS",
        description=f"输出当前 tenant 下全部公众号文章的聚合 RSS XML。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(),
        responses={
            (200, "application/xml"): xml_response(
                "当前租户的 RSS XML。",
                TENANT_RSS_XML_EXAMPLE,
                example_name="Tenant RSS XML",
            ),
            **common_error_responses,
        },
    )
    def get(self, request):
        articles = tenant_queryset(WechatArticle.objects.select_related("feed"), request)
        xml = RssService.build_tenant_rss(tenant=request.user.tenant, articles=articles)
        return HttpResponse(xml, content_type="application/xml")


class FeedRssView(WeRssTenantApiView):

    @extend_schema(
        operation_id="we_rss_rss_feed",
        tags=[WE_RSS_TAG],
        summary="获取单个公众号的 RSS",
        description=f"按公众号 ID 输出该公众号下文章的 RSS XML。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(RSS_FEED_ID_PARAMETER),
        responses={
            (200, "application/xml"): xml_response(
                "单个公众号的 RSS XML。",
                FEED_RSS_XML_EXAMPLE,
                example_name="Feed RSS XML",
            ),
            **common_error_responses,
        },
    )
    def get(self, request, feed_id):
        feed = get_object_or_404(tenant_queryset(WechatFeed.objects.all(), request), pk=feed_id)
        articles = tenant_queryset(WechatArticle.objects.filter(feed=feed), request)
        xml = RssService.build_feed_rss(feed=feed, articles=articles)
        return HttpResponse(xml, content_type="application/xml")


class ArticleContentView(WeRssTenantApiView):

    @extend_schema(
        operation_id="we_rss_rss_content",
        tags=[WE_RSS_TAG],
        summary="获取文章正文 HTML",
        description=f"输出单篇公众号文章的正文 HTML，用于 RSS 阅读器或外部阅读页渲染。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(RSS_ARTICLE_ID_PARAMETER),
        responses={
            (200, "text/html"): html_response(
                "文章正文 HTML。",
                ARTICLE_HTML_EXAMPLE,
                example_name="Article HTML response",
            ),
            **common_error_responses,
        },
    )
    def get(self, request, article_id):
        article = get_object_or_404(tenant_queryset(WechatArticle.objects.all(), request), pk=article_id)
        return HttpResponse(RssService.build_article_content(article=article), content_type="text/html")
