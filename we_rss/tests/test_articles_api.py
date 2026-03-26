from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import (
    MemberArticleTagRelation,
    MemberTag,
    WechatArticle,
    WechatCredential,
    WechatFeed,
    WechatSyncTask,
)
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
        self.assertEqual(response.data["data"][0]["article_type"], "news")

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
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["source_id"], "article-newspic")
        self.assertEqual(response.data["data"][0]["article_type"], "newspic")

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
        self.assertEqual([item["source_id"] for item in response.data["data"]], ["article-title-match"])

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
            {item["source_id"] for item in response.data["data"]},
            {"article-alpha", "article-beta", "article-gamma"},
        )

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
        self.assertEqual(article.article_type, "news")
        self.assertEqual(article.comment_total_count, 11)

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
        self.assertEqual(article.article_type, "newspic")

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
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {other_token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        other_member_response = self.client.get("/api/v1/we-rss/articles/")

        self.assertEqual(other_member_response.status_code, 200)
        self.assertFalse(other_member_response.data["data"][0]["is_favorite"])

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
        self.assertEqual([item["source_id"] for item in filtered_response.data["data"]], ["article-favorite"])


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
            [item["id"] for item in response.data["data"]],
            [self.article_with_both_tags.id],
        )

    def test_article_list_tag_filter_only_uses_current_member_relations(self):
        response = self.client.get(f"/api/v1/we-rss/articles/?tag_ids={self.tag_one.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item["id"] for item in response.data["data"]},
            {self.article_with_both_tags.id, self.article_with_one_tag.id},
        )
