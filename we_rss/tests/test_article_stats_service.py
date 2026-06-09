from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import NotFound, ValidationError

from tenants.models import Tenant
from users.models import Member
from we_rss.models import MemberArticleState, MemberFeedSubscription, WechatArticle, WechatCredential, WechatFeed
from we_rss.services.article_stats_service import (
    LIVE_LOG_FILE,
    SESSION_FILE,
    ArticleStatsRefreshService,
)


class ArticleStatsRefreshServiceTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )
        self.credential = WechatCredential.objects.create(
            tenant=self.tenant,
            name="Default Credential",
            status="active",
            token="token-1",
            cookie="cookie-1",
            is_default=True,
            created_by=self.member,
            updated_by=self.member,
        )
        self.feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Tenant Feed",
            source_id="feed-1",
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )

    def test_refresh_by_url_updates_existing_article_stats(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Existing",
            url="https://mp.weixin.qq.com/s/article-1?token=123",
        )

        with patch.object(ArticleStatsRefreshService, "ensure_stats_runtime_ready"):
            with patch(
                "we_rss.services.article_stats_service.collect_stats",
                return_value={
                    "read_num": 9,
                    "publish_time": "2026-04-05T02:13:00Z",
                    "comment_count": 3,
                    "comment_reply_count": 1,
                    "comment_total_count": 4,
                },
            ):
                refreshed = ArticleStatsRefreshService.refresh_article_stats_by_url(
                    tenant=self.tenant,
                    member=self.member,
                    article_url="https://mp.weixin.qq.com/s/article-1",
                )

        article.refresh_from_db()
        self.assertEqual(refreshed.id, article.id)
        self.assertEqual(article.read_num, 9)
        self.assertEqual(article.publish_time, parse_datetime("2026-04-05T02:13:00Z"))
        self.assertEqual(article.comment_count, 3)
        self.assertEqual(article.comment_reply_count, 1)
        self.assertEqual(article.comment_total_count, 4)
        self.assertIsNotNone(article.last_refreshed_at)

    def test_refresh_by_url_rejects_missing_article(self):
        with self.assertRaisesMessage(NotFound, "Article not found"):
            ArticleStatsRefreshService.refresh_article_stats_by_url(
                tenant=self.tenant,
                member=self.member,
                article_url="https://mp.weixin.qq.com/s/missing",
            )

    def test_refresh_by_url_rejects_unready_stats_runtime(self):
        with patch.object(Path, "exists", return_value=False):
            with self.assertRaisesMessage(ValidationError, "not ready"):
                ArticleStatsRefreshService.ensure_stats_runtime_ready()

    def test_refresh_does_not_modify_non_stats_fields(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-2",
            title="Original title",
            description="Original description",
            content="Original content",
            url="https://mp.weixin.qq.com/s/article-2",
        )

        with patch.object(ArticleStatsRefreshService, "ensure_stats_runtime_ready"):
            with patch(
                "we_rss.services.article_stats_service.collect_stats",
                return_value={
                    "title": "Wrong title",
                    "description": "Wrong description",
                    "content": "Wrong content",
                    "read_num": 100,
                    "comment_count": 7,
                    "comment_reply_count": 2,
                    "comment_total_count": 9,
                },
            ):
                ArticleStatsRefreshService.refresh_article_stats_for_article(article=article)

        article.refresh_from_db()
        self.assertEqual(article.title, "Original title")
        self.assertEqual(article.description, "Original description")
        self.assertEqual(article.content, "Original content")
        self.assertEqual(article.read_num, 100)
        self.assertEqual(article.comment_count, 7)
        self.assertEqual(article.comment_reply_count, 2)
        self.assertEqual(article.comment_total_count, 9)

    def test_refresh_uses_existing_short_url_before_collecting_stats(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="2247486397_1",
            title="Short URL Article",
            url="https://mp.weixin.qq.com/s/article-short",
        )

        with patch.object(ArticleStatsRefreshService, "ensure_stats_runtime_ready"):
            with patch(
                "we_rss.services.article_stats_service.collect_stats",
                return_value={
                    "read_num": 42,
                    "comment_count": 4,
                    "comment_reply_count": 2,
                    "comment_total_count": 6,
                },
            ) as collect_mock:
                refreshed = ArticleStatsRefreshService.refresh_article_stats_for_article(article=article)

        article.refresh_from_db()
        self.assertEqual(refreshed.id, article.id)
        self.assertEqual(article.url, "https://mp.weixin.qq.com/s/article-short")
        self.assertEqual(article.read_num, 42)
        collect_mock.assert_called_once_with(
            article_url="https://mp.weixin.qq.com/s/article-short",
            session_file=SESSION_FILE,
            live_log_file=LIVE_LOG_FILE,
        )

    def test_refresh_uses_existing_article_url_without_scanning_feed_pages(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="2247486398_1",
            title="Existing URL Article",
            url="https://mp.weixin.qq.com/s/article-existing-url",
        )

        with patch.object(ArticleStatsRefreshService, "ensure_stats_runtime_ready"):
            with patch(
                "we_rss.services.article_stats_service.collect_stats",
                return_value={
                    "read_num": 43,
                    "comment_count": 4,
                    "comment_reply_count": 2,
                    "comment_total_count": 6,
                },
            ) as collect_mock:
                ArticleStatsRefreshService.refresh_article_stats_for_article(article=article)

        article.refresh_from_db()
        self.assertEqual(article.read_num, 43)
        collect_mock.assert_called_once_with(
            article_url="https://mp.weixin.qq.com/s/article-existing-url",
            session_file=SESSION_FILE,
            live_log_file=LIVE_LOG_FILE,
        )

    def test_refresh_falls_back_to_existing_url_without_attempting_resolution(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-fallback",
            title="Fallback Article",
            url="https://mp.weixin.qq.com/s/article-fallback",
        )

        with patch.object(ArticleStatsRefreshService, "ensure_stats_runtime_ready"):
            with patch(
                "we_rss.services.article_stats_service.collect_stats",
                return_value={
                    "read_num": 18,
                    "comment_count": 5,
                    "comment_reply_count": 2,
                    "comment_total_count": 7,
                },
            ) as collect_mock:
                refreshed = ArticleStatsRefreshService.refresh_article_stats_for_article(article=article)

        article.refresh_from_db()
        self.assertEqual(refreshed.id, article.id)
        self.assertEqual(article.url, "https://mp.weixin.qq.com/s/article-fallback")
        self.assertEqual(article.read_num, 18)
        self.assertEqual(article.comment_count, 5)
        self.assertEqual(article.comment_reply_count, 2)
        self.assertEqual(article.comment_total_count, 7)
        collect_mock.assert_called_once_with(
            article_url="https://mp.weixin.qq.com/s/article-fallback",
            session_file=SESSION_FILE,
            live_log_file=LIVE_LOG_FILE,
        )

    def test_refresh_rejects_article_without_url_without_scanning_feed_pages(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="2247486400_1",
            title="Missing URL Article",
            url="",
        )

        with patch.object(ArticleStatsRefreshService, "ensure_stats_runtime_ready"):
            with patch(
                "we_rss.services.article_stats_service.collect_stats",
                side_effect=AssertionError("stats collection should not run without an article URL"),
            ) as collect_mock:
                with self.assertRaisesMessage(ValidationError, "Article URL is required"):
                    ArticleStatsRefreshService.refresh_article_stats_for_article(article=article)

        collect_mock.assert_not_called()

    def test_refresh_rejects_empty_stats_payload_without_updating_article(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-empty-stats",
            title="Empty Stats Article",
            url="https://mp.weixin.qq.com/s/article-empty-stats",
        )

        with patch.object(ArticleStatsRefreshService, "ensure_stats_runtime_ready"):
            with patch(
                "we_rss.services.article_stats_service.collect_stats",
                return_value={
                    "read_num": None,
                    "like_num": None,
                    "old_like_num": None,
                    "share_num": None,
                    "collect_num": None,
                    "comment_count": None,
                    "comment_reply_count": None,
                    "comment_total_count": None,
                    "comment_reply_count_error": "no session",
                },
            ):
                with self.assertRaisesMessage(ValidationError, "no stats returned"):
                    ArticleStatsRefreshService.refresh_article_stats_for_article(article=article)

        article.refresh_from_db()
        self.assertIsNone(article.read_num)
        self.assertIsNone(article.comment_count)
        self.assertIsNone(article.last_refreshed_at)

    def test_resolve_article_ids_selector_deduplicates_and_keeps_tenant_scope(self):
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-a",
            url="https://mp.weixin.qq.com/s/article-a",
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-b",
            url="https://mp.weixin.qq.com/s/article-b",
        )
        other_tenant = Tenant.objects.create(name="Tenant B", code="tenant_b")
        other_feed = WechatFeed.objects.create(
            tenant=other_tenant,
            mp_name="Other Feed",
            source_id="other-feed",
        )
        other_article = WechatArticle.objects.create(
            tenant=other_tenant,
            feed=other_feed,
            source_id="article-c",
            url="https://mp.weixin.qq.com/s/article-c",
        )

        article_ids = ArticleStatsRefreshService.resolve_article_ids(
            tenant=self.tenant,
            member=self.member,
            article_ids=[second_article.id, first_article.id, second_article.id],
        )

        self.assertEqual(article_ids, [second_article.id, first_article.id])

    def test_resolve_article_ids_selector_rejects_missing_or_cross_tenant_articles(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-in-tenant",
            url="https://mp.weixin.qq.com/s/article-in-tenant",
        )
        other_tenant = Tenant.objects.create(name="Tenant B", code="tenant_b")
        other_feed = WechatFeed.objects.create(
            tenant=other_tenant,
            mp_name="Other Feed",
            source_id="other-feed",
        )
        other_article = WechatArticle.objects.create(
            tenant=other_tenant,
            feed=other_feed,
            source_id="article-outside-tenant",
            url="https://mp.weixin.qq.com/s/article-outside-tenant",
        )

        with self.assertRaises(ValidationError) as exc_info:
            ArticleStatsRefreshService.resolve_article_ids(
                tenant=self.tenant,
                member=self.member,
                article_ids=[article.id, other_article.id, 999999],
            )

        self.assertIn("article_ids", exc_info.exception.detail)

    def test_resolve_member_selector_collects_articles_from_subscribed_feeds(self):
        second_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Second Feed",
            source_id="feed-2",
        )
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-a",
            url="https://mp.weixin.qq.com/s/article-a",
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=second_feed,
            source_id="article-b",
            url="https://mp.weixin.qq.com/s/article-b",
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=second_feed,
        )

        article_ids = ArticleStatsRefreshService.resolve_article_ids(
            tenant=self.tenant,
            member=self.member,
            member_id=self.member.id,
        )

        self.assertEqual(article_ids, [second_article.id, first_article.id])

    def test_resolve_article_ids_excludes_hidden_articles_for_current_member(self):
        visible_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-visible",
            url="https://mp.weixin.qq.com/s/article-visible",
        )
        hidden_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-hidden",
            url="https://mp.weixin.qq.com/s/article-hidden",
        )
        MemberArticleState.objects.create(
            tenant=self.tenant,
            member=self.member,
            article=hidden_article,
            is_hidden=True,
        )

        article_ids = ArticleStatsRefreshService.resolve_article_ids(
            tenant=self.tenant,
            member=self.member,
            feed_id=self.feed.id,
        )

        self.assertEqual(article_ids, [visible_article.id])

    def test_refresh_rejects_empty_stats_payload_without_updating_article(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-empty-stats",
            title="Empty Stats Article",
            url="https://mp.weixin.qq.com/s/article-empty-stats",
        )

        with patch.object(ArticleStatsRefreshService, "ensure_stats_runtime_ready"):
            with patch(
                "we_rss.services.article_stats_service.collect_stats",
                return_value={
                    "read_num": None,
                    "like_num": None,
                    "old_like_num": None,
                    "share_num": None,
                    "collect_num": None,
                    "comment_count": None,
                    "comment_reply_count": None,
                    "comment_total_count": None,
                    "comment_reply_count_error": "no session",
                },
            ):
                with self.assertRaisesMessage(ValidationError, "no stats returned"):
                    ArticleStatsRefreshService.refresh_article_stats_for_article(article=article)

        article.refresh_from_db()
        self.assertEqual(article.read_num, 0)
        self.assertEqual(article.comment_count, 0)
        self.assertIsNone(article.last_refreshed_at)

    def test_resolve_member_selector_collects_articles_from_subscribed_feeds(self):
        second_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Second Feed",
            source_id="feed-2",
        )
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-a",
            url="https://mp.weixin.qq.com/s/article-a",
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=second_feed,
            source_id="article-b",
            url="https://mp.weixin.qq.com/s/article-b",
        )
        MemberFeedSubscription.objects.get_or_create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=second_feed,
        )

        article_ids = ArticleStatsRefreshService.resolve_article_ids(
            tenant=self.tenant,
            member=self.member,
            member_id=self.member.id,
        )

        self.assertEqual(article_ids, [second_article.id, first_article.id])
