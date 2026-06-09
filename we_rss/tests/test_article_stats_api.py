from unittest.mock import patch

from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import MemberFeedSubscription, WechatArticle, WechatFeed


class ArticleStatsSyncApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )
        self.token = generate_jwt_token(self.member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        self.feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Tenant Feed",
            source_id="feed-1",
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )

    def _decode_stream(self, response):
        return b"".join(response.streaming_content).decode("utf-8")

    def test_refresh_by_url_streams_article_progress(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
            url="https://mp.weixin.qq.com/s/article-1?token=123",
        )

        with patch(
            "we_rss.views.article_stats_views.ArticleStatsRefreshService.refresh_article_stats_for_article"
        ) as refresh_mock:
            article.publish_time = parse_datetime("2026-04-05T02:13:00Z")
            article.read_num = 123
            refresh_mock.return_value = article
            response = self.client.post(
                "/api/v1/we-rss/article-stats/refresh-by-url/",
                {"url": "https://mp.weixin.qq.com/s/article-1"},
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )
            body = self._decode_stream(response)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertIn("text/event-stream", response["Content-Type"])
        self.assertIn("event: start", body)
        self.assertEqual(body.count("event: progress"), 1)
        self.assertIn("event: done", body)
        self.assertIn('"selector_type": "url"', body)
        self.assertIn(f'"article_id": {article.id}', body)
        self.assertIn('"read_num": 123', body)
        self.assertIn('"success_count": 1', body)
        refresh_mock.assert_called_once_with(article=article)

    def test_refresh_by_url_returns_404_when_article_missing(self):
        response = self.client.post(
            "/api/v1/we-rss/article-stats/refresh-by-url/",
            {"url": "https://mp.weixin.qq.com/s/missing"},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )

        self.assertEqual(response.status_code, 404)

    def test_refresh_by_url_returns_400_when_stats_runtime_returns_empty_payload(self):
        with patch(
            "we_rss.views.article_stats_views.ArticleStatsRefreshService.refresh_article_stats_for_article"
        ) as refresh_mock:
            refresh_mock.side_effect = ValidationError("WeChat stats refresh failed: no stats returned.")
            article = WechatArticle.objects.create(
                tenant=self.tenant,
                feed=self.feed,
                source_id="article-empty-stats",
                title="Tenant Article",
                url="https://mp.weixin.qq.com/s/article-1",
            )
            response = self.client.post(
                "/api/v1/we-rss/article-stats/refresh-by-url/",
                {"url": "https://mp.weixin.qq.com/s/article-1"},
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )
            body = self._decode_stream(response)

        self.assertEqual(response.status_code, 200)
        self.assertIn("event: progress", body)
        self.assertIn('"status": "failed"', body)
        self.assertIn("no stats returned", body)
        refresh_mock.assert_called_once_with(article=article)


class ArticleStatsBatchApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member_batch",
            email="tenant-member-batch@example.com",
            tenant=self.tenant,
        )
        self.token = generate_jwt_token(self.member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        self.feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Tenant Feed",
            source_id="feed-1",
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )

    def test_batch_refresh_rejects_multiple_selectors(self):
        response = self.client.post(
            "/api/v1/we-rss/article-stats/refresh/",
            {"article_ids": [1], "feed_id": 2},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )

        self.assertEqual(response.status_code, 400)

    def _decode_stream(self, response):
        return b"".join(response.streaming_content).decode("utf-8")

    def test_batch_refresh_streams_progress_for_each_feed_article(self):
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-stream-1",
            title="Stream Article 1",
            url="https://mp.weixin.qq.com/s/article-stream-1",
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-stream-2",
            title="Stream Article 2",
            url="https://mp.weixin.qq.com/s/article-stream-2",
        )

        def side_effect(*, article):
            article.read_num = 100 + article.id
            article.save(update_fields=["read_num", "updated_at"])
            return article

        with patch(
            "we_rss.views.article_stats_views.ArticleStatsRefreshService.refresh_article_stats_for_article"
        ) as refresh_mock:
            refresh_mock.side_effect = side_effect
            response = self.client.post(
                "/api/v1/we-rss/article-stats/refresh/",
                {"feed_id": self.feed.id},
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )
            body = self._decode_stream(response)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertIn("text/event-stream", response["Content-Type"])
        self.assertIn("event: start", body)
        self.assertEqual(body.count("event: progress"), 2)
        self.assertIn("event: done", body)
        self.assertIn(f'"article_id": {second_article.id}', body)
        self.assertIn(f'"article_id": {first_article.id}', body)
        self.assertIn('"success_count": 2', body)
        self.assertIn('"failed_count": 0', body)
        self.assertEqual(refresh_mock.call_count, 2)

    def test_batch_refresh_by_feed_skips_articles_marked_deleted(self):
        active_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-active",
            title="Active Article",
            url="https://mp.weixin.qq.com/s/article-active",
            status="active",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-deleted",
            title="Deleted Article",
            url="https://mp.weixin.qq.com/s/article-deleted",
            status="deleted",
        )

        with patch(
            "we_rss.views.article_stats_views.ArticleStatsRefreshService.refresh_article_stats_for_article"
        ) as refresh_mock:
            refresh_mock.return_value = active_article
            response = self.client.post(
                "/api/v1/we-rss/article-stats/refresh/",
                {"feed_id": self.feed.id},
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )
            body = self._decode_stream(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.count("event: progress"), 1)
        self.assertIn(f'"article_id": {active_article.id}', body)
        self.assertNotIn("article-deleted", body)
        refresh_mock.assert_called_once_with(article=active_article)

    def test_batch_refresh_streams_failed_article_and_continues(self):
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-stream-ok",
            title="Stream Article OK",
            url="https://mp.weixin.qq.com/s/article-stream-ok",
        )
        failed_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-stream-failed",
            title="Stream Article Failed",
            url="https://mp.weixin.qq.com/s/article-stream-failed",
        )

        def side_effect(*, article):
            if article.id == failed_article.id:
                raise ValidationError("stats blocked")
            article.read_num = 88
            article.save(update_fields=["read_num", "updated_at"])
            return article

        with patch(
            "we_rss.views.article_stats_views.ArticleStatsRefreshService.refresh_article_stats_for_article"
        ) as refresh_mock:
            refresh_mock.side_effect = side_effect
            response = self.client.post(
                "/api/v1/we-rss/article-stats/refresh/",
                {"article_ids": [first_article.id, failed_article.id]},
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )
            body = self._decode_stream(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.count("event: progress"), 2)
        self.assertIn('"status": "success"', body)
        self.assertIn('"status": "failed"', body)
        self.assertIn('"failed_count": 1', body)
        self.assertIn('"failed_articles"', body)
        self.assertIn("stats blocked", body)
