from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import WechatArticle, WechatCredential, WechatFeed, WechatSyncTask
from we_rss.services.article_service import WechatArticleGateway


class FakeArticleGateway:
    def import_article_by_url(self, url, credential):
        return {
            "source_id": "article-imported-1",
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
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["title"], "Tenant Article")

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
        self.assertFalse(WechatArticle.objects.filter(id=article.id).exists())

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
        self.assertEqual(article.comment_total_count, 11)

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeArticleGateway())
    def test_refresh_updates_statistics_snapshot(self, _mock_gateway):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
            url="https://mp.weixin.qq.com/s/article-1",
        )

        response = self.client.post(f"/api/v1/we-rss/articles/{article.id}/refresh/")

        article.refresh_from_db()
        task = WechatSyncTask.objects.get(id=response.data["data"]["id"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(task.task_type, "article_refresh")
        self.assertEqual(task.status, "success")
        self.assertEqual(article.read_num, 101)
        self.assertEqual(article.comment_total_count, 15)
        self.assertIsNotNone(article.last_refreshed_at)
        self.assertEqual(article.title, "Tenant Article Refreshed")

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

    def test_member_can_list_tasks_with_filters(self):
        success_task = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync",
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

        response = self.client.get("/api/v1/we-rss/tasks/?task_type=feed_sync&status=success")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["id"], success_task.id)

    def test_member_can_mark_article_read_and_favorite(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
        )

        read_response = self.client.put(
            f"/api/v1/we-rss/articles/{article.id}/read/",
            {"is_read": True},
            format="json",
        )
        favorite_response = self.client.put(
            f"/api/v1/we-rss/articles/{article.id}/favorite/",
            {"is_favorite": True},
            format="json",
        )

        article.refresh_from_db()

        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(favorite_response.status_code, 200)
        self.assertTrue(article.is_read)
        self.assertTrue(article.is_favorite)
