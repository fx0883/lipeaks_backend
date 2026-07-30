import csv
import io
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import (
    MemberArticleState,
    MemberFeedSubscription,
    MemberArticleTagRelation,
    MemberTag,
    WechatArticle,
    WechatCredential,
    WechatFeed,
    WechatSyncTask,
)
from we_rss.services.article_search_service import ArticleSearchService
from we_rss.services.article_service import WechatArticleGateway


class FakeArticleGateway:
    def import_article_by_url(self, url, credential):
        return {
            "source_id": "article-imported-1",
            "article_type": "news",
            "title": "Imported Article",
            "description": "Imported description",
            "content": "<p>Imported content</p>",
            "url": url,
            "pic_url": "https://example.com/imported.png",
            "publish_time": "2026-03-20T12:00:00Z",
            "read_num": 12,
            "like_num": 8,
            "old_like_num": 3,
            "share_num": 2,
            "collect_num": 4,
            "comment_count": 5,
            "comment_reply_count": 6,
            "comment_total_count": 11,
        }

    def refresh_article(self, article, credential):
        return {
            "article_type": "newspic",
            "title": f"{article.title} Refreshed",
            "description": "Refreshed description",
            "content": "<p>Refreshed content</p>",
            "url": article.url or "https://mp.weixin.qq.com/s/refreshed",
            "pic_url": "https://example.com/refreshed.png",
            "publish_time": "2026-03-21T12:00:00Z",
            "read_num": 101,
            "like_num": 51,
            "old_like_num": 21,
            "share_num": 11,
            "collect_num": 9,
            "comment_count": 7,
            "comment_reply_count": 8,
            "comment_total_count": 15,
        }


class GatewayArticleResponse:
    def __init__(self, *, text="", status_code=200, headers=None, url=""):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class ArticleGatewayTests(TestCase):
    ARTICLE_HTML = """
    <html>
      <head>
        <meta property="og:title" content="Imported Article" />
        <meta property="og:description" content="Imported description" />
        <meta property="twitter:image" content="https://example.com/imported.png" />
      </head>
      <body>
        <div id="js_name">Imported MP</div>
        <div id="publish_time">2026-03-20 12:00</div>
        <div id="js_content"><p>Imported content</p></div>
        <script>
          var biz = "Qkl6";
          var comment_id = "12345";
        </script>
      </body>
    </html>
    """

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
            token="token-123",
            cookie="slave_sid=sid-1; fingerprint=fp-1",
            is_default=True,
            created_by=self.member,
            updated_by=self.member,
        )
        self.feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Imported MP",
            source_id="feed-1",
            faker_id="fakeid-1",
            created_by=self.member,
            updated_by=self.member,
        )
        self.article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Old Title",
            url="https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
        )

    @patch("we_rss.services.article_service.requests.Session")
    def test_import_article_by_url_extracts_public_article_fields(self, mock_session_cls):
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=self.ARTICLE_HTML,
            headers={"Content-Type": "text/html"},
            url="https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
        )

        payload = WechatArticleGateway().import_article_by_url(
            "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
            self.credential,
        )

        self.assertEqual(payload["title"], "Imported Article")
        self.assertEqual(payload["description"], "Imported description")
        self.assertEqual(payload["content"], "<p>Imported content</p>")
        self.assertEqual(payload["biz"], "Qkl6")
        self.assertEqual(payload["source_id"], "article-1")
        self.assertEqual(payload["article_type"], "news")

    @patch("we_rss.services.article_service.requests.Session")
    def test_import_article_by_url_marks_non_first_idx_as_newspic(self, mock_session_cls):
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=self.ARTICLE_HTML,
            headers={"Content-Type": "text/html"},
            url="https://mp.weixin.qq.com/s/article-2?__biz=Qkl6&mid=1&idx=2&sn=abc",
        )

        payload = WechatArticleGateway().import_article_by_url(
            "https://mp.weixin.qq.com/s/article-2?__biz=Qkl6&mid=1&idx=2&sn=abc",
            self.credential,
        )

        self.assertEqual(payload["article_type"], "newspic")

    @patch("we_rss.services.article_service.requests.Session")
    def test_import_article_by_url_keeps_public_url_when_response_redirect_contains_token(self, mock_session_cls):
        public_url = "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc"
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=self.ARTICLE_HTML,
            headers={"Content-Type": "text/html"},
            url=f"{public_url}&token=123456",
        )

        payload = WechatArticleGateway().import_article_by_url(public_url, self.credential)

        self.assertEqual(payload["url"], public_url)
        self.assertEqual(payload["source_id"], "article-1")
        self.assertNotIn("token=", payload["url"])

    @patch("we_rss.services.article_service.requests.Session")
    def test_import_article_by_url_prefers_canonical_response_url_over_short_request_url(self, mock_session_cls):
        short_url = "https://mp.weixin.qq.com/s/article-1-short"
        canonical_url = "https://mp.weixin.qq.com/s?__biz=Qkl6&mid=1&idx=1&sn=abc"
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=self.ARTICLE_HTML,
            headers={"Content-Type": "text/html"},
            url=canonical_url,
        )

        payload = WechatArticleGateway().import_article_by_url(short_url, self.credential)

        self.assertEqual(payload["url"], canonical_url)
        self.assertEqual(payload["source_id"], "article-1-short")

    @patch("we_rss.services.article_service.requests.Session")
    def test_refresh_article_returns_updated_public_article_fields(self, mock_session_cls):
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=self.ARTICLE_HTML.replace("Imported Article", "Refreshed Article"),
            headers={"Content-Type": "text/html"},
            url=self.article.url,
        )

        payload = WechatArticleGateway().refresh_article(self.article, self.credential)

        self.assertEqual(payload["title"], "Refreshed Article")
        self.assertEqual(payload["description"], "Imported description")
        self.assertEqual(payload["content"], "<p>Imported content</p>")
        self.assertEqual(payload["biz"], "Qkl6")

    @patch("we_rss.services.article_service.requests.Session")
    def test_refresh_article_keeps_stored_public_url_when_response_redirect_contains_token(self, mock_session_cls):
        public_url = "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc"
        self.article.url = public_url
        self.article.save(update_fields=["url", "updated_at"])
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=self.ARTICLE_HTML.replace("Imported Article", "Refreshed Article"),
            headers={"Content-Type": "text/html"},
            url=f"{public_url}&token=123456",
        )

        payload = WechatArticleGateway().refresh_article(self.article, self.credential)

        self.assertEqual(payload["url"], public_url)
        self.assertNotIn("token=", payload["url"])

    @patch("we_rss.services.article_service.requests.Session")
    def test_import_article_by_url_builds_summary_and_parses_chinese_publish_time(self, mock_session_cls):
        html = """
        <html>
          <head>
            <meta property="og:title" content="Summary Article" />
            <meta property="twitter:image" content="https://example.com/summary.png" />
          </head>
          <body>
            <div id="js_name">Summary MP</div>
            <div id="publish_time">3月4日</div>
            <div id="js_content">
              <p>第一段内容。</p>
              <p>第二段内容。</p>
            </div>
            <script>
              window.__biz="Qkl6";
            </script>
          </body>
        </html>
        """
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=html,
            headers={"Content-Type": "text/html"},
            url="https://mp.weixin.qq.com/s/summary-article?__biz=Qkl6&mid=1&idx=1&sn=abc",
        )

        payload = WechatArticleGateway().import_article_by_url(
            "https://mp.weixin.qq.com/s/summary-article?__biz=Qkl6&mid=1&idx=1&sn=abc",
            self.credential,
        )

        self.assertEqual(payload["description"], "第一段内容。 第二段内容。")
        self.assertIsNotNone(payload["publish_time"])
        self.assertEqual(payload["publish_time"].month, 3)
        self.assertEqual(payload["publish_time"].day, 4)
        self.assertEqual(payload["biz"], "Qkl6")

    @patch("we_rss.services.article_service.requests.Session")
    def test_refresh_article_marks_deleted_article_payload(self, mock_session_cls):
        html = """
        <html>
          <body>
            <div id="js_content">该内容已被发布者删除</div>
          </body>
        </html>
        """
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=html,
            headers={"Content-Type": "text/html"},
            url=self.article.url,
        )

        payload = WechatArticleGateway().refresh_article(self.article, self.credential)

        self.assertEqual(payload["status"], "deleted")
        self.assertEqual(payload["content"], "DELETED")

    @patch("we_rss.services.article_service.requests.Session")
    def test_import_article_by_url_rejects_environment_abnormal_page(self, mock_session_cls):
        html = """
        <html>
          <body>
            当前环境异常，完成验证后即可继续访问
          </body>
        </html>
        """
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=html,
            headers={"Content-Type": "text/html"},
            url="https://mp.weixin.qq.com/s/environment-abnormal?__biz=Qkl6&mid=1&idx=1&sn=abc",
        )

        with self.assertRaisesMessage(Exception, "当前环境异常，完成验证后即可继续访问"):
            WechatArticleGateway().import_article_by_url(
                "https://mp.weixin.qq.com/s/environment-abnormal?__biz=Qkl6&mid=1&idx=1&sn=abc",
                self.credential,
            )


    @patch("we_rss.services.article_service.requests.Session")
    def test_import_article_by_url_builds_summary_and_parses_chinese_publish_time(self, mock_session_cls):
        html = """
        <html>
          <head>
            <meta property="og:title" content="Summary Article" />
            <meta property="twitter:image" content="https://example.com/summary.png" />
          </head>
          <body>
            <div id="js_name">Summary MP</div>
            <div id="publish_time">2026-03-04 10:00</div>
            <div id="js_content">
              <p>First paragraph.</p>
              <p>Second paragraph.</p>
            </div>
            <script>
              window.__biz="Qkl6";
            </script>
          </body>
        </html>
        """
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=html,
            headers={"Content-Type": "text/html"},
            url="https://mp.weixin.qq.com/s/summary-article?__biz=Qkl6&mid=1&idx=1&sn=abc",
        )

        payload = WechatArticleGateway().import_article_by_url(
            "https://mp.weixin.qq.com/s/summary-article?__biz=Qkl6&mid=1&idx=1&sn=abc",
            self.credential,
        )

        self.assertEqual(payload["description"], "First paragraph. Second paragraph.")
        self.assertIsNotNone(payload["publish_time"])
        self.assertEqual(payload["publish_time"].month, 3)
        self.assertEqual(payload["publish_time"].day, 4)
        self.assertEqual(payload["biz"], "Qkl6")


class ArticleSearchServiceTests(TestCase):
    @patch("we_rss.services.article_search_service.SogouArticleSearchService.search_wechat_articles")
    def test_article_search_service_repairs_mojibake_emoji_from_native_search_service(self, search_mock):
        search_mock.return_value = {
            "items": [
                {
                    "title": "AI Agent \u7039\u70b4\u57ac \u9983\u6b8c",
                    "url": "https://mp.weixin.qq.com/s/agent-1",
                }
            ],
            "total": 1,
            "query": "AI Agent",
            "executor": "codex",
            "raw_text": '{"items": [{"title": "AI Agent \\u7039\\u70b4\\u57ac \\u9983\\u6b8c", "url": "https://mp.weixin.qq.com/s/agent-1"}]}',
        }

        result = ArticleSearchService.search_wechat_articles(query="AI Agent", limit=3)

        self.assertEqual(
            result,
            {
                "query": "AI Agent",
                "total": 1,
                "items": [
                    {
                        "title": "AI Agent \u5b9e\u6218 \U0001f680",
                        "url": "https://mp.weixin.qq.com/s/agent-1",
                    }
                ],
            },
        )
        search_mock.assert_called_once_with(
            query="AI Agent",
            limit=3,
        )

    @patch("we_rss.services.article_search_service.SogouArticleSearchService.search_wechat_articles")
    def test_article_search_service_preserves_full_public_article_fields(self, search_mock):
        search_mock.return_value = {
            "items": [
                {
                    "title": "Skill article",
                    "url": "https://mp.weixin.qq.com/s/skill-1",
                    "summary": "Summary text",
                    "datetime": "2026-04-10 10:00:00",
                    "date_text": "2026年04月10日",
                    "date_description": "今天",
                    "source": "OpenAI",
                }
            ],
            "total": 1,
            "query": "skill",
            "executor": "codex",
            "raw_text": '{"items": [{"title": "Skill article"}]}',
        }

        result = ArticleSearchService.search_wechat_articles(query="skill", limit=3)

        self.assertEqual(
            result,
            {
                "query": "skill",
                "total": 1,
                "items": [
                    {
                        "title": "Skill article",
                        "url": "https://mp.weixin.qq.com/s/skill-1",
                        "summary": "Summary text",
                        "datetime": "2026-04-10 10:00:00",
                        "date_text": "2026年04月10日",
                        "date_description": "今天",
                        "source": "OpenAI",
                    }
                ],
            },
        )


class ArticleApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.other_tenant = Tenant.objects.create(name="Tenant B", code="tenant_b")
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
            created_by=self.member,
            updated_by=self.member,
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )

    def _article_results(self, response):
        return response.data["data"]["results"]

    def _article_pagination(self, response):
        return response.data["data"]["pagination"]

    def _parse_csv_rows(self, response):
        content = response.content.decode("utf-8-sig")
        return list(csv.DictReader(io.StringIO(content)))

    def test_member_can_list_tenant_articles(self):
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
        )
        other_member = Member.objects.create(
            username="other_member",
            email="other-member@example.com",
            tenant=self.other_tenant,
        )
        other_feed = WechatFeed.objects.create(
            tenant=self.other_tenant,
            mp_name="Other Feed",
            source_id="feed-2",
            created_by=other_member,
            updated_by=other_member,
        )
        WechatArticle.objects.create(
            tenant=self.other_tenant,
            feed=other_feed,
            source_id="article-2",
            title="Other Article",
        )

        response = self.client.get("/api/v1/we-rss/articles/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self._article_results(response)), 1)
        self.assertEqual(self._article_results(response)[0]["title"], "Tenant Article")
        self.assertEqual(self._article_results(response)[0]["article_type"], "news")

    def test_member_only_sees_articles_from_subscribed_feeds(self):
        subscribed_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-subscribed",
            title="Subscribed Article",
        )
        unsubscribed_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Unsubscribed Feed",
            source_id="feed-unsubscribed",
            created_by=self.member,
            updated_by=self.member,
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=unsubscribed_feed,
            source_id="article-unsubscribed",
            title="Unsubscribed Article",
        )

        response = self.client.get("/api/v1/we-rss/articles/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in self._article_results(response)],
            [subscribed_article.id],
        )

    def test_member_can_filter_articles_by_article_type(self):
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-news",
            title="News Article",
            article_type="news",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-newspic",
            title="Newspic Article",
            article_type="newspic",
        )

        response = self.client.get("/api/v1/we-rss/articles/?article_type=newspic")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self._article_results(response)), 1)
        self.assertEqual(self._article_results(response)[0]["source_id"], "article-newspic")
        self.assertEqual(self._article_results(response)[0]["article_type"], "newspic")

    def test_member_can_filter_articles_by_feed_id(self):
        matching_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-feed-match",
            title="Matching Feed Article",
        )
        other_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Other Feed",
            source_id="feed-2",
            created_by=self.member,
            updated_by=self.member,
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=other_feed,
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=other_feed,
            source_id="article-feed-other",
            title="Other Feed Article",
        )

        response = self.client.get(f"/api/v1/we-rss/articles/?feed_id={self.feed.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in self._article_results(response)], [matching_article.id])

    def test_article_list_applies_page_and_page_size(self):
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-page-1",
            title="Article Page 1",
            publish_time=timezone.now() - timedelta(days=3),
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-page-2",
            title="Article Page 2",
            publish_time=timezone.now() - timedelta(days=2),
        )
        third_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-page-3",
            title="Article Page 3",
            publish_time=timezone.now() - timedelta(days=1),
        )

        response = self.client.get("/api/v1/we-rss/articles/?page=2&page_size=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in self._article_results(response)],
            [first_article.id],
        )
        self.assertEqual(self._article_pagination(response)["count"], 3)
        self.assertEqual(self._article_pagination(response)["page_size"], 2)
        self.assertEqual(self._article_pagination(response)["current_page"], 2)
        self.assertEqual(self._article_pagination(response)["total_pages"], 2)

    def test_member_feed_id_filter_still_respects_visible_scope(self):
        unsubscribed_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Unsubscribed Feed",
            source_id="feed-unsubscribed",
            created_by=self.member,
            updated_by=self.member,
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=unsubscribed_feed,
            source_id="article-unsubscribed",
            title="Hidden From Member",
        )

        response = self.client.get(f"/api/v1/we-rss/articles/?feed_id={unsubscribed_feed.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["source_id"] for item in self._article_results(response)], ["article-unsubscribed"])

    def test_member_can_get_unsubscribed_feed_article_detail_when_not_hidden(self):
        unsubscribed_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Unsubscribed Feed",
            source_id="feed-detail-unsubscribed",
            created_by=self.member,
            updated_by=self.member,
        )
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=unsubscribed_feed,
            source_id="article-detail-unsubscribed",
            title="Unsubscribed Feed Detail",
        )

        response = self.client.get(f"/api/v1/we-rss/articles/{article.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["source_id"], "article-detail-unsubscribed")

    def test_hidden_unsubscribed_feed_article_detail_returns_404(self):
        unsubscribed_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Unsubscribed Feed",
            source_id="feed-hidden-unsubscribed",
            created_by=self.member,
            updated_by=self.member,
        )
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=unsubscribed_feed,
            source_id="article-hidden-unsubscribed",
            title="Hidden Unsubscribed Feed Detail",
        )
        MemberArticleState.objects.create(
            tenant=self.tenant,
            member=self.member,
            article=article,
            is_hidden=True,
        )

        response = self.client.get(f"/api/v1/we-rss/articles/{article.id}/")

        self.assertEqual(response.status_code, 404)

    def test_article_list_rejects_invalid_feed_id(self):
        response = self.client.get("/api/v1/we-rss/articles/?feed_id=abc")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["data"]["feed_id"], ["A valid integer is required."])

    def test_member_can_sort_visible_articles_by_read_num_desc(self):
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-read-low",
            title="Low Read Article",
            read_num=8,
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-read-high",
            title="High Read Article",
            read_num=42,
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-read-zero",
            title="Zero Read Article",
        )

        response = self.client.get("/api/v1/we-rss/articles/?sort_by=read_num&sort_order=desc")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["source_id"] for item in self._article_results(response)],
            ["article-read-high", "article-read-low", "article-read-zero"],
        )

    def test_member_can_sort_publish_time_desc_with_null_publish_time_last(self):
        old_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-publish-old",
            title="Old Publish Article",
            publish_time=timezone.now() - timedelta(days=2),
        )
        new_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-publish-new",
            title="New Publish Article",
            publish_time=timezone.now() - timedelta(days=1),
        )
        no_publish_time_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-publish-null",
            title="No Publish Time Article",
            publish_time=None,
        )

        response = self.client.get("/api/v1/we-rss/articles/?sort_by=publish_time&sort_order=desc")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in self._article_results(response)],
            [new_article.id, old_article.id, no_publish_time_article.id],
        )

    def test_member_can_sort_articles_ascending(self):
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-collect-high",
            title="High Collect Article",
            collect_num=30,
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-collect-low",
            title="Low Collect Article",
            collect_num=3,
        )

        response = self.client.get("/api/v1/we-rss/articles/?sort_by=collect_num&sort_order=asc")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["source_id"] for item in self._article_results(response)],
            ["article-collect-low", "article-collect-high"],
        )

    def test_article_sorting_combines_with_feed_filter_and_visibility(self):
        target_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Target Sort Feed",
            source_id="feed-sort-target",
            created_by=self.member,
            updated_by=self.member,
        )
        other_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Other Sort Feed",
            source_id="feed-sort-other",
            created_by=self.member,
            updated_by=self.member,
        )
        target_low = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=target_feed,
            source_id="article-target-low",
            title="Target Low Share",
            share_num=2,
        )
        target_high = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=target_feed,
            source_id="article-target-high",
            title="Target High Share",
            share_num=9,
        )
        hidden_high = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=target_feed,
            source_id="article-target-hidden",
            title="Target Hidden Share",
            share_num=99,
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=other_feed,
            source_id="article-other-high",
            title="Other High Share",
            share_num=88,
        )
        MemberArticleState.objects.create(
            tenant=self.tenant,
            member=self.member,
            article=hidden_high,
            is_hidden=True,
        )

        response = self.client.get(
            f"/api/v1/we-rss/articles/?feed_id={target_feed.id}&sort_by=share_num&sort_order=desc"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in self._article_results(response)],
            [target_high.id, target_low.id],
        )

    def test_article_sorting_combines_with_favorite_filter(self):
        favorite_low = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-favorite-low",
            title="Favorite Low Comments",
            comment_total_count=1,
        )
        favorite_high = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-favorite-high",
            title="Favorite High Comments",
            comment_total_count=7,
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-not-favorite-high",
            title="Not Favorite High Comments",
            comment_total_count=99,
        )
        MemberArticleState.objects.create(
            tenant=self.tenant,
            member=self.member,
            article=favorite_low,
            is_favorite=True,
        )
        MemberArticleState.objects.create(
            tenant=self.tenant,
            member=self.member,
            article=favorite_high,
            is_favorite=True,
        )

        response = self.client.get(
            "/api/v1/we-rss/articles/?favorite_only=true&sort_by=comment_total_count&sort_order=desc"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in self._article_results(response)],
            [favorite_high.id, favorite_low.id],
        )

    def test_article_list_rejects_invalid_sort_by_with_supported_fields(self):
        response = self.client.get("/api/v1/we-rss/articles/?sort_by=title")

        self.assertEqual(response.status_code, 400)
        self.assertIn("sort_by", response.data["data"])
        self.assertIn("Supported values are:", response.data["data"]["sort_by"][0])
        self.assertIn("read_num", response.data["data"]["sort_by"][0])
        self.assertIn("comment_total_count", response.data["data"]["sort_by"][0])

    def test_article_list_rejects_invalid_sort_order(self):
        response = self.client.get("/api/v1/we-rss/articles/?sort_by=read_num&sort_order=newest")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["data"]["sort_order"], ["Supported values are: asc, desc."])

    def test_article_list_filters_by_publish_time_start(self):
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-early",
            title="Early",
            publish_time=datetime(2026, 6, 23, 10, 0, tzinfo=datetime_timezone.utc),
        )
        article_late = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-late",
            title="Late",
            publish_time=datetime(2026, 6, 25, 10, 0, tzinfo=datetime_timezone.utc),
        )

        response = self.client.get("/api/v1/we-rss/articles/?publish_time_start=2026-06-24T00:00:00Z")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in self._article_results(response)], [article_late.id])

        # Test date format
        response_date = self.client.get("/api/v1/we-rss/articles/?publish_time_start=2026-06-24")
        self.assertEqual(response_date.status_code, 200)
        self.assertEqual([item["id"] for item in self._article_results(response_date)], [article_late.id])

    def test_article_list_filters_by_publish_time_end(self):
        article_early = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-early",
            title="Early",
            publish_time=datetime(2026, 6, 23, 10, 0, tzinfo=datetime_timezone.utc),
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-late",
            title="Late",
            publish_time=datetime(2026, 6, 25, 10, 0, tzinfo=datetime_timezone.utc),
        )

        response = self.client.get("/api/v1/we-rss/articles/?publish_time_end=2026-06-24T00:00:00Z")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in self._article_results(response)], [article_early.id])

        # Test date format
        response_date = self.client.get("/api/v1/we-rss/articles/?publish_time_end=2026-06-24")
        self.assertEqual(response_date.status_code, 200)
        self.assertEqual([item["id"] for item in self._article_results(response_date)], [article_early.id])

    def test_article_list_rejects_invalid_publish_time_format(self):
        response = self.client.get("/api/v1/we-rss/articles/?publish_time_start=invalid-date")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["data"]["publish_time_start"],
            ["A valid ISO 8601 datetime or YYYY-MM-DD date is required."],
        )

        response_end = self.client.get("/api/v1/we-rss/articles/?publish_time_end=invalid-date")
        self.assertEqual(response_end.status_code, 400)
        self.assertEqual(
            response_end.data["data"]["publish_time_end"],
            ["A valid ISO 8601 datetime or YYYY-MM-DD date is required."],
        )

    def test_member_can_search_articles_by_title_only(self):
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-title-match",
            title="Alpha Launch Brief",
            description="Unrelated description",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-description-only",
            title="Different Title",
            description="Alpha appears only in description",
        )

        response = self.client.get("/api/v1/we-rss/articles/?search=Alpha")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["source_id"] for item in self._article_results(response)], ["article-title-match"])

    def test_member_article_search_uses_we_mp_rss_keyword_split_rules(self):
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-alpha",
            title="Alpha Launch Brief",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-beta",
            title="Beta Launch Brief",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-gamma",
            title="Gamma Launch Brief",
        )

        response = self.client.get("/api/v1/we-rss/articles/?search=Alpha|Beta-Gamma")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item["source_id"] for item in self._article_results(response)},
            {"article-alpha", "article-beta", "article-gamma"},
        )

    @patch("we_rss.views.article_views.ArticleSearchService.search_wechat_articles")
    def test_member_can_search_public_wechat_articles_via_native_search_service(self, search_mock):
        search_mock.return_value = {
            "items": [
                {
                    "title": "AI Agent 实战",
                    "url": "https://mp.weixin.qq.com/s/agent-1",
                }
            ],
            "total": 1,
            "query": "AI Agent",
            "executor": "codex",
            "raw_text": '{"items": [{"title": "AI Agent 实战", "url": "https://mp.weixin.qq.com/s/agent-1"}]}',
        }

        response = self.client.get("/api/v1/we-rss/articles/search/?query=AI%20Agent&limit=3")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["query"], "AI Agent")
        self.assertEqual(response.data["data"]["total"], 1)
        self.assertEqual(
            response.data["data"]["items"],
            [
                {
                    "title": "AI Agent 实战",
                    "url": "https://mp.weixin.qq.com/s/agent-1",
                }
            ],
        )
        self.assertNotIn("executor", response.data["data"])
        self.assertNotIn("raw_text", response.data["data"])
        search_mock.assert_called_once_with(
            query="AI Agent",
            limit=3,
        )

    @patch("we_rss.views.article_views.ArticleSearchService.search_wechat_articles")
    def test_member_public_wechat_article_search_returns_full_article_fields(self, search_mock):
        search_mock.return_value = {
            "items": [
                {
                    "title": "Skill article",
                    "url": "https://mp.weixin.qq.com/s/skill-1",
                    "summary": "Summary text",
                    "datetime": "2026-04-10 10:00:00",
                    "date_text": "2026年04月10日",
                    "date_description": "今天",
                    "source": "OpenAI",
                }
            ],
            "total": 1,
            "query": "skill",
        }

        response = self.client.get("/api/v1/we-rss/articles/search/?query=skill&limit=3")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"]["items"][0],
            {
                "title": "Skill article",
                "url": "https://mp.weixin.qq.com/s/skill-1",
                "summary": "Summary text",
                "datetime": "2026-04-10 10:00:00",
                "date_text": "2026年04月10日",
                "date_description": "今天",
                "source": "OpenAI",
            },
        )

    def test_public_wechat_article_search_requires_query(self):
        response = self.client.get("/api/v1/we-rss/articles/search/")

        self.assertEqual(response.status_code, 400)
        self.assertIn("query", response.data["data"])

    def test_member_can_get_and_delete_article(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
        )

        detail_response = self.client.get(f"/api/v1/we-rss/articles/{article.id}/")
        delete_response = self.client.delete(f"/api/v1/we-rss/articles/{article.id}/")

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["data"]["title"], "Tenant Article")
        self.assertEqual(delete_response.status_code, 204)
        self.assertTrue(WechatArticle.objects.filter(id=article.id).exists())
        self.assertTrue(
            MemberArticleState.objects.filter(
                tenant=self.tenant,
                member=self.member,
                article=article,
                is_hidden=True,
            ).exists()
        )
        hidden_detail_response = self.client.get(f"/api/v1/we-rss/articles/{article.id}/")
        self.assertEqual(hidden_detail_response.status_code, 404)

    def test_member_can_batch_delete_articles_by_ids(self):
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-batch-delete-1",
            title="Batch Delete Article 1",
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-batch-delete-2",
            title="Batch Delete Article 2",
        )
        tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Batch Delete Tag",
        )
        MemberArticleState.objects.create(
            tenant=self.tenant,
            member=self.member,
            article=first_article,
            is_favorite=True,
        )
        MemberArticleTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            article=second_article,
        )
        other_member = Member.objects.create(
            username="other_tenant_member",
            email="other-tenant-member@example.com",
            tenant=self.other_tenant,
        )
        other_feed = WechatFeed.objects.create(
            tenant=self.other_tenant,
            mp_name="Other Tenant Feed",
            source_id="other-feed-batch-delete",
            created_by=other_member,
            updated_by=other_member,
        )
        other_article = WechatArticle.objects.create(
            tenant=self.other_tenant,
            feed=other_feed,
            source_id="other-tenant-article",
            title="Other Tenant Article",
        )

        response = self.client.post(
            "/api/v1/we-rss/articles/batch-delete/",
            {"article_ids": [second_article.id, first_article.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["deleted_count"], 2)
        self.assertEqual(response.data["data"]["article_ids"], [second_article.id, first_article.id])
        self.assertTrue(WechatArticle.objects.filter(id=first_article.id).exists())
        self.assertTrue(WechatArticle.objects.filter(id=second_article.id).exists())
        self.assertTrue(
            MemberArticleState.objects.filter(
                tenant=self.tenant,
                member=self.member,
                article=first_article,
                is_hidden=True,
                is_favorite=True,
            ).exists()
        )
        self.assertTrue(
            MemberArticleState.objects.filter(
                tenant=self.tenant,
                member=self.member,
                article=second_article,
                is_hidden=True,
            ).exists()
        )
        self.assertTrue(MemberArticleTagRelation.objects.filter(article_id=second_article.id).exists())
        self.assertTrue(WechatArticle.objects.filter(id=other_article.id).exists())

    def test_member_can_batch_delete_unsubscribed_feed_articles_by_ids(self):
        unsubscribed_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Unsubscribed Feed",
            source_id="feed-batch-delete-unsubscribed",
            created_by=self.member,
            updated_by=self.member,
        )
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=unsubscribed_feed,
            source_id="article-batch-delete-unsubscribed",
            title="Batch Delete Unsubscribed Feed Article",
        )

        response = self.client.post(
            "/api/v1/we-rss/articles/batch-delete/",
            {"article_ids": [article.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["article_ids"], [article.id])
        self.assertTrue(
            MemberArticleState.objects.filter(
                tenant=self.tenant,
                member=self.member,
                article=article,
                is_hidden=True,
            ).exists()
        )

    def test_batch_delete_articles_rejects_ids_outside_current_tenant(self):
        valid_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-batch-delete-valid",
            title="Batch Delete Valid Article",
        )
        other_member = Member.objects.create(
            username="batch_delete_other_tenant_member",
            email="batch-delete-other@example.com",
            tenant=self.other_tenant,
        )
        other_feed = WechatFeed.objects.create(
            tenant=self.other_tenant,
            mp_name="Other Tenant Feed",
            source_id="other-feed-batch-delete-invalid",
            created_by=other_member,
            updated_by=other_member,
        )
        foreign_article = WechatArticle.objects.create(
            tenant=self.other_tenant,
            feed=other_feed,
            source_id="article-batch-delete-foreign",
            title="Foreign Article",
        )

        response = self.client.post(
            "/api/v1/we-rss/articles/batch-delete/",
            {"article_ids": [valid_article.id, foreign_article.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("article_ids", response.data["data"])
        self.assertTrue(WechatArticle.objects.filter(id=valid_article.id).exists())
        self.assertTrue(WechatArticle.objects.filter(id=foreign_article.id).exists())

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeArticleGateway())
    def test_import_by_url_creates_featured_article(self, _mock_gateway):
        response = self.client.post(
            "/api/v1/we-rss/articles/import-by-url/",
            {"url": "https://mp.weixin.qq.com/s/imported"},
            format="json",
        )

        task = WechatSyncTask.objects.get(id=response.data["data"]["id"])
        article = WechatArticle.objects.get(source_id="article-imported-1")
        featured_feed = WechatFeed.objects.get(id=article.feed_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(task.task_type, "article_import")
        self.assertEqual(task.status, "success")
        self.assertTrue(featured_feed.is_featured)
        self.assertEqual(featured_feed.tenant, self.tenant)
        self.assertEqual(article.title, "Imported Article")
        self.assertEqual(article.article_type, "news")
        self.assertEqual(article.comment_total_count, 11)
        self.assertTrue(
            MemberFeedSubscription.objects.filter(
                tenant=self.tenant,
                member=self.member,
                feed=featured_feed,
            ).exists()
        )

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeArticleGateway())
    def test_import_by_url_normalizes_task_key_and_request_url(self, _mock_gateway):
        tokenized_url = "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc&token=123456"

        response = self.client.post(
            "/api/v1/we-rss/articles/import-by-url/",
            {"url": tokenized_url},
            format="json",
        )

        task = WechatSyncTask.objects.get(id=response.data["data"]["id"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            task.task_key,
            "article_import:https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
        )
        self.assertEqual(
            task.request_payload["url"],
            "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
        )

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeArticleGateway())
    def test_refresh_streams_markdown_content_update(self, _mock_gateway):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
            url="https://mp.weixin.qq.com/s/article-1",
        )

        with patch("we_rss.views.article_views.get_article_markdown_service") as service_factory:
            service_factory.return_value.fetch_markdown_from_url.return_value = "# Refreshed markdown"
            response = self.client.post(
                f"/api/v1/we-rss/articles/{article.id}/refresh/",
                HTTP_ACCEPT="text/event-stream",
            )

        body = b"".join(response.streaming_content).decode("utf-8")
        article.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response["Content-Type"])
        self.assertIn("event: start", body)
        self.assertIn("event: done", body)
        self.assertIn('"article_id": %s' % article.id, body)
        self.assertIn('"status": "done"', body)
        self.assertEqual(article.content, "# Refreshed markdown")

    def test_member_can_get_task_detail(self):
        task = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="article_import",
            status="success",
            target_type="article",
            target_id=1,
            created_by=self.member,
        )

        response = self.client.get(f"/api/v1/we-rss/tasks/{task.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["id"], task.id)

    def test_task_detail_marks_stale_feed_sync_run_as_partial_success_when_batch_stops_making_progress(self):
        parent = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync_run",
            status="running",
            target_type="feed",
            target_id=self.feed.id,
            message="Feed sync is running.",
            created_by=self.member,
            started_at=timezone.now() - timedelta(minutes=20),
            result_payload={
                "run_status": "running",
                "feed_id": self.feed.id,
                "batch_size": 20,
                "poll_after_seconds": 5,
                "has_more": True,
                "next_begin": 40,
                "batches_completed": 2,
                "batches_failed": 0,
                "articles_synced": 40,
                "articles_failed": 0,
                "article_ids": [1, 2, 3],
                "current_batch_task_id": None,
                "latest_completed_batch": {
                    "batch_no": 2,
                },
                "last_progress_at": (timezone.now() - timedelta(minutes=10)).isoformat(),
                "timeout_reason": "",
            },
        )
        batch = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync_batch",
            status="running",
            target_type="feed",
            target_id=self.feed.id,
            message="Feed sync batch task created.",
            created_by=self.member,
            started_at=timezone.now() - timedelta(minutes=9),
            request_payload={
                "parent_task_id": parent.id,
                "feed_id": self.feed.id,
                "batch_no": 3,
                "begin": 40,
                "batch_size": 20,
            },
        )
        parent.result_payload["current_batch_task_id"] = batch.id
        parent.save(update_fields=["result_payload", "updated_at"])
        batch.save(update_fields=["started_at", "updated_at"])

        response = self.client.get(f"/api/v1/we-rss/tasks/{parent.id}/")

        parent.refresh_from_db()
        batch.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["status"], "partial_success")
        self.assertEqual(response.data["data"]["result_payload"]["run_status"], "partial_success")
        self.assertEqual(response.data["data"]["result_payload"]["timeout_reason"], "batch_timeout")
        self.assertEqual(batch.status, "timed_out")

    def test_member_can_list_tasks_with_filters(self):
        success_task = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync_run",
            status="success",
            target_type="feed",
            target_id=1,
            created_by=self.member,
        )
        WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="article_refresh",
            status="failed",
            target_type="article",
            target_id=2,
            created_by=self.member,
        )

        response = self.client.get("/api/v1/we-rss/tasks/?task_type=feed_sync_run&status=success")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["id"], success_task.id)

    def test_member_can_favorite_article_without_affecting_other_members(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
        )
        other_member = Member.objects.create(
            username="second_member",
            email="second-member@example.com",
            tenant=self.tenant,
        )

        favorite_response = self.client.put(
            f"/api/v1/we-rss/articles/{article.id}/favorite/",
            {"is_favorite": True},
            format="json",
        )

        self.assertEqual(favorite_response.status_code, 200)
        self.assertTrue(favorite_response.data["data"]["is_favorite"])

        other_token = generate_jwt_token(other_member)["access_token"]
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=other_member,
            feed=self.feed,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {other_token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        other_member_response = self.client.get("/api/v1/we-rss/articles/")

        self.assertEqual(other_member_response.status_code, 200)
        self.assertFalse(self._article_results(other_member_response)[0]["is_favorite"])

    def test_member_can_favorite_unsubscribed_feed_article(self):
        unsubscribed_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Unsubscribed Feed",
            source_id="feed-favorite-unsubscribed",
            created_by=self.member,
            updated_by=self.member,
        )
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=unsubscribed_feed,
            source_id="article-favorite-unsubscribed",
            title="Favorite Unsubscribed Feed Article",
        )

        response = self.client.put(
            f"/api/v1/we-rss/articles/{article.id}/favorite/",
            {"is_favorite": True},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_favorite"])

    def test_member_can_filter_articles_by_favorite_only(self):
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-favorite",
            title="Favorite Article",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-regular",
            title="Regular Article",
        )

        favorite_response = self.client.put(
            f"/api/v1/we-rss/articles/{first_article.id}/favorite/",
            {"is_favorite": True},
            format="json",
        )
        filtered_response = self.client.get("/api/v1/we-rss/articles/?favorite_only=true")

        self.assertEqual(favorite_response.status_code, 200)
        self.assertEqual(filtered_response.status_code, 200)
        self.assertEqual([item["source_id"] for item in self._article_results(filtered_response)], ["article-favorite"])

    def test_hidden_article_is_excluded_from_favorite_only_results(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-hidden-favorite",
            title="Hidden Favorite Article",
        )

        favorite_response = self.client.put(
            f"/api/v1/we-rss/articles/{article.id}/favorite/",
            {"is_favorite": True},
            format="json",
        )
        delete_response = self.client.delete(f"/api/v1/we-rss/articles/{article.id}/")
        filtered_response = self.client.get("/api/v1/we-rss/articles/?favorite_only=true")

        self.assertEqual(favorite_response.status_code, 200)
        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(filtered_response.status_code, 200)
        self.assertEqual(self._article_results(filtered_response), [])

    def test_hidden_article_does_not_affect_other_subscribed_member(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-hidden-isolated",
            title="Hidden Isolated Article",
        )
        other_member = Member.objects.create(
            username="hidden_second_member",
            email="hidden-second-member@example.com",
            tenant=self.tenant,
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=other_member,
            feed=self.feed,
        )

        delete_response = self.client.delete(f"/api/v1/we-rss/articles/{article.id}/")

        self.assertEqual(delete_response.status_code, 204)

        other_token = generate_jwt_token(other_member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {other_token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        other_member_response = self.client.get("/api/v1/we-rss/articles/")

        self.assertEqual(other_member_response.status_code, 200)
        self.assertEqual(
            [item["source_id"] for item in self._article_results(other_member_response)],
            ["article-hidden-isolated"],
        )

    def test_article_export_can_export_selected_article_ids_as_csv_in_request_order(self):
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-export-1",
            title="First Exported Article",
            content="# First",
            url="https://mp.weixin.qq.com/s/article-export-1",
            read_num=11,
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-export-2",
            title="Second Exported Article",
            content="# Second",
            url="https://mp.weixin.qq.com/s/article-export-2",
            read_num=22,
        )

        response = self.client.post(
            "/api/v1/we-rss/articles/export/",
            {"article_ids": [second_article.id, first_article.id]},
            format="json",
        )

        rows = self._parse_csv_rows(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertEqual([int(row["article_id"]) for row in rows], [second_article.id, first_article.id])
        self.assertEqual([row["title"] for row in rows], ["Second Exported Article", "First Exported Article"])
        self.assertEqual([row["feed_name"] for row in rows], ["Tenant Feed", "Tenant Feed"])

    def test_article_export_exposes_content_disposition_header_for_cors_downloads(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-export-cors",
            title="CORS Export Article",
            content="# Export",
            url="https://mp.weixin.qq.com/s/article-export-cors",
        )

        response = self.client.post(
            "/api/v1/we-rss/articles/export/",
            {"article_ids": [article.id]},
            format="json",
            HTTP_ORIGIN="http://localhost:3000",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertIn("content-disposition", response["Access-Control-Expose-Headers"].lower())

    def test_article_export_can_export_subscribed_member_articles_grouped_by_feed(self):
        member_feed_alpha = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Alpha Feed",
            source_id="feed-alpha",
            created_by=self.member,
            updated_by=self.member,
        )
        member_feed_beta = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Beta Feed",
            source_id="feed-beta",
            created_by=self.member,
            updated_by=self.member,
        )
        other_member = Member.objects.create(
            username="member_export_other",
            email="member-export-other@example.com",
            tenant=self.tenant,
        )
        unsubscribed_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Gamma Feed",
            source_id="feed-gamma",
            created_by=self.member,
            updated_by=self.member,
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=member_feed_beta,
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=member_feed_alpha,
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=other_member,
            feed=unsubscribed_feed,
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=member_feed_alpha,
            source_id="alpha-1",
            title="Alpha Article 1",
            url="https://mp.weixin.qq.com/s/alpha-1",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=member_feed_beta,
            source_id="beta-1",
            title="Beta Article 1",
            url="https://mp.weixin.qq.com/s/beta-1",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=unsubscribed_feed,
            source_id="gamma-1",
            title="Gamma Article 1",
            url="https://mp.weixin.qq.com/s/gamma-1",
        )

        response = self.client.post(
            "/api/v1/we-rss/articles/export/",
            {"member_id": self.member.id},
            format="json",
        )

        rows = self._parse_csv_rows(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [(row["feed_name"], row["source_id"]) for row in rows],
            [("Alpha Feed", "alpha-1"), ("Beta Feed", "beta-1")],
        )

    def test_article_export_can_export_all_articles_under_one_feed(self):
        target_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Export Feed",
            source_id="feed-export",
            created_by=self.member,
            updated_by=self.member,
        )
        other_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Other Feed",
            source_id="feed-other",
            created_by=self.member,
            updated_by=self.member,
        )
        export_article_one = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=target_feed,
            source_id="feed-export-1",
            title="Export Feed Article 1",
            url="https://mp.weixin.qq.com/s/feed-export-1",
        )
        export_article_two = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=target_feed,
            source_id="feed-export-2",
            title="Export Feed Article 2",
            url="https://mp.weixin.qq.com/s/feed-export-2",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=other_feed,
            source_id="feed-other-1",
            title="Other Feed Article",
            url="https://mp.weixin.qq.com/s/feed-other-1",
        )

        response = self.client.post(
            "/api/v1/we-rss/articles/export/",
            {"feed_id": target_feed.id},
            format="json",
        )

        rows = self._parse_csv_rows(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {int(row["article_id"]) for row in rows},
            {export_article_one.id, export_article_two.id},
        )
        self.assertEqual({row["feed_name"] for row in rows}, {"Export Feed"})

    @patch("we_rss.services.article_service.requests.Session")
    def test_import_article_by_url_builds_summary_and_parses_chinese_publish_time(self, mock_session_cls):
        html = """
        <html>
          <head>
            <meta property="og:title" content="Summary Article" />
            <meta property="twitter:image" content="https://example.com/summary.png" />
          </head>
          <body>
            <div id="js_name">Summary MP</div>
            <div id="publish_time">2026-03-04 10:00</div>
            <div id="js_content">
              <p>First paragraph.</p>
              <p>Second paragraph.</p>
            </div>
            <script>
              window.__biz="Qkl6";
            </script>
          </body>
        </html>
        """
        mock_session_cls.return_value.get.return_value = GatewayArticleResponse(
            text=html,
            headers={"Content-Type": "text/html"},
            url="https://mp.weixin.qq.com/s/summary-article?__biz=Qkl6&mid=1&idx=1&sn=abc",
        )

        payload = WechatArticleGateway().import_article_by_url(
            "https://mp.weixin.qq.com/s/summary-article?__biz=Qkl6&mid=1&idx=1&sn=abc",
            self.credential,
        )

        self.assertEqual(payload["description"], "First paragraph. Second paragraph.")
        self.assertIsNotNone(payload["publish_time"])
        self.assertEqual(payload["publish_time"].month, 3)
        self.assertEqual(payload["publish_time"].day, 4)
        self.assertEqual(payload["biz"], "Qkl6")

    def test_task_detail_marks_stale_feed_sync_run_as_partial_success_when_batch_stops_making_progress(self):
        parent = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync_run",
            status="running",
            target_type="feed",
            target_id=self.feed.id,
            message="Feed sync is running.",
            created_by=self.member,
            started_at=timezone.now() - timedelta(minutes=170),
            result_payload={
                "run_status": "running",
                "feed_id": self.feed.id,
                "batch_size": 20,
                "poll_after_seconds": 5,
                "has_more": True,
                "next_begin": 40,
                "batches_completed": 2,
                "batches_failed": 0,
                "articles_synced": 40,
                "articles_failed": 0,
                "article_ids": [1, 2, 3],
                "current_batch_task_id": None,
                "latest_completed_batch": {
                    "batch_no": 2,
                },
                "last_progress_at": (timezone.now() - timedelta(minutes=160)).isoformat(),
                "timeout_reason": "",
            },
        )
        batch = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync_batch",
            status="running",
            target_type="feed",
            target_id=self.feed.id,
            message="Feed sync batch task created.",
            created_by=self.member,
            started_at=timezone.now() - timedelta(minutes=155),
            request_payload={
                "parent_task_id": parent.id,
                "feed_id": self.feed.id,
                "batch_no": 3,
                "begin": 40,
                "batch_size": 20,
            },
        )
        parent.result_payload["current_batch_task_id"] = batch.id
        parent.save(update_fields=["result_payload", "updated_at"])
        batch.save(update_fields=["started_at", "updated_at"])

        response = self.client.get(f"/api/v1/we-rss/tasks/{parent.id}/")

        parent.refresh_from_db()
        batch.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["status"], "partial_success")
        self.assertEqual(response.data["data"]["result_payload"]["run_status"], "partial_success")
        self.assertEqual(response.data["data"]["result_payload"]["timeout_reason"], "batch_timeout")
        self.assertEqual(batch.status, "timed_out")

    def test_article_export_can_export_all_articles_under_one_feed(self):
        target_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Export Feed",
            source_id="feed-export",
            created_by=self.member,
            updated_by=self.member,
        )
        other_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Other Feed",
            source_id="feed-other",
            created_by=self.member,
            updated_by=self.member,
        )
        export_article_one = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=target_feed,
            source_id="feed-export-1",
            title="Export Feed Article 1",
            url="https://mp.weixin.qq.com/s/feed-export-1",
        )
        export_article_two = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=target_feed,
            source_id="feed-export-2",
            title="Export Feed Article 2",
            url="https://mp.weixin.qq.com/s/feed-export-2",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=other_feed,
            source_id="feed-other-1",
            title="Other Feed Article",
            url="https://mp.weixin.qq.com/s/feed-other-1",
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=target_feed,
        )

        response = self.client.post(
            "/api/v1/we-rss/articles/export/",
            {"feed_id": target_feed.id},
            format="json",
        )

        rows = self._parse_csv_rows(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {int(row["article_id"]) for row in rows},
            {export_article_one.id, export_article_two.id},
        )
        self.assertEqual({row["feed_name"] for row in rows}, {"Export Feed"})


class ArticleTagFilterApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )
        self.other_member = Member.objects.create(
            username="other_member",
            email="other-member@example.com",
            tenant=self.tenant,
        )
        token = generate_jwt_token(self.member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        self.feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Tenant Feed",
            source_id="feed-1",
            created_by=self.member,
            updated_by=self.member,
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )
        self.article_with_both_tags = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-both",
            title="Article With Both Tags",
        )
        self.article_with_one_tag = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-one",
            title="Article With One Tag",
        )
        self.article_with_other_member_tag = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-other",
            title="Other Member Tagged Article",
        )
        self.tag_one = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="AI",
        )
        self.tag_two = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Digest",
        )
        other_member_tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.other_member,
            name="Other Member Tag",
        )
        MemberArticleTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag_one,
            article=self.article_with_both_tags,
        )
        MemberArticleTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag_two,
            article=self.article_with_both_tags,
        )
        MemberArticleTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag_one,
            article=self.article_with_one_tag,
        )
        MemberArticleTagRelation.objects.create(
            tenant=self.tenant,
            member=self.other_member,
            tag=other_member_tag,
            article=self.article_with_other_member_tag,
        )

    def test_article_list_filters_by_all_requested_tag_ids(self):
        response = self.client.get(
            f"/api/v1/we-rss/articles/?tag_ids={self.tag_one.id},{self.tag_two.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["data"]["results"]],
            [self.article_with_both_tags.id],
        )

    def test_article_list_tag_filter_only_uses_current_member_relations(self):
        response = self.client.get(f"/api/v1/we-rss/articles/?tag_ids={self.tag_one.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item["id"] for item in response.data["data"]["results"]},
            {self.article_with_both_tags.id, self.article_with_one_tag.id},
        )
