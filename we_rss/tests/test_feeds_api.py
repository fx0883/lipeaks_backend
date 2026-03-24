import json
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import WechatArticle, WechatCredential, WechatFeed, WechatSyncTask
from we_rss.services.feed_service import WechatFeedGateway


class FakeFeedGateway:
    def search_feeds(self, keyword, credential):
        return [
            {
                "source_id": "feed-1",
                "faker_id": "faker-1",
                "biz": "biz-1",
                "mp_name": f"{keyword} Feed",
                "mp_cover": "https://example.com/cover.png",
                "mp_intro": "Feed intro",
            }
        ]

    def sync_feed(self, feed, credential):
        return {
            "message": "Sync complete",
            "articles": [
                {
                    "source_id": "feed-article-1",
                    "title": "Synced Feed Article",
                    "description": "Feed article",
                    "content": "<p>Feed article</p>",
                    "url": "https://mp.weixin.qq.com/s/feed-article-1",
                }
            ],
            "result_payload": {
                "article_count": 2,
                "feed_id": feed.id,
            },
        }


class FakeGatewayResponse:
    def __init__(self, *, json_data=None, text="", status_code=200, headers=None, url=""):
        self._json_data = json_data
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}
        self.url = url

    def json(self):
        if self._json_data is None:
            raise ValueError("No JSON data configured")
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class FeedGatewayTests(TestCase):
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
            mp_name="Tenant Feed",
            source_id="feed-1",
            faker_id="fakeid-1",
            created_by=self.member,
            updated_by=self.member,
        )

    @patch("we_rss.services.feed_service.requests.Session")
    def test_search_feeds_maps_wechat_search_payload(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.return_value = FakeGatewayResponse(
            json_data={
                "base_resp": {"ret": 0},
                "list": [
                    {
                        "nickname": "Test MP",
                        "fakeid": "ZmFrZS1pZA==",
                        "signature": "Test intro",
                        "round_head_img": "https://example.com/avatar.png",
                    }
                ],
            }
        )

        results = WechatFeedGateway().search_feeds("test", self.credential)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["mp_name"], "Test MP")
        self.assertEqual(results[0]["faker_id"], "ZmFrZS1pZA==")
        self.assertEqual(results[0]["mp_intro"], "Test intro")

    @patch("we_rss.services.feed_service.requests.Session")
    def test_sync_feed_returns_parsed_articles(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps(
                        {
                            "publish_list": [
                                {
                                    "publish_info": json.dumps(
                                        {
                                            "appmsgex": [
                                                {
                                                    "aid": "article-1",
                                                    "title": "Synced Article",
                                                    "link": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                                    "digest": "Synced description",
                                                    "cover": "https://example.com/article-cover.png",
                                                    "create_time": 1710000000,
                                                }
                                            ]
                                        }
                                    )
                                }
                            ]
                        }
                    ),
                }
            ),
            FakeGatewayResponse(
                text="""
                <html>
                  <head>
                    <meta property="og:title" content="Synced Article" />
                    <meta property="og:description" content="Synced description" />
                    <meta property="twitter:image" content="https://example.com/article-cover.png" />
                  </head>
                  <body>
                    <div id="js_name">Tenant Feed</div>
                    <div id="publish_time">2026-03-20 12:00</div>
                    <div id="js_content"><p>Synced content</p></div>
                    <script>var biz = "Qkl6";</script>
                  </body>
                </html>
                """,
                headers={"Content-Type": "text/html"},
                url="https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway().sync_feed(self.feed, self.credential)

        self.assertEqual(payload["articles"][0]["source_id"], "article-1")
        self.assertEqual(payload["articles"][0]["title"], "Synced Article")
        self.assertEqual(payload["articles"][0]["content"], "<p>Synced content</p>")
        self.assertEqual(payload["articles"][0]["biz"], "Qkl6")
        self.assertEqual(payload["articles"][0]["article_type"], "newspic")

    @patch("we_rss.services.feed_service.requests.Session")
    def test_sync_feed_uses_source_id_when_faker_id_is_blank(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.return_value = FakeGatewayResponse(
            json_data={
                "base_resp": {"ret": 0},
                "publish_page": json.dumps({"publish_list": []}),
            }
        )
        self.feed.faker_id = ""
        self.feed.source_id = "fallback-fakeid"

        WechatFeedGateway().sync_feed(self.feed, self.credential)

        self.assertEqual(session.get.call_args.kwargs["params"]["fakeid"], "fallback-fakeid")

    @patch("we_rss.services.feed_service.requests.Session")
    def test_sync_feed_keeps_list_item_when_article_detail_page_is_abnormal(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps(
                        {
                            "publish_list": [
                                {
                                    "publish_info": json.dumps(
                                        {
                                            "appmsgex": [
                                                {
                                                    "aid": "article-1",
                                                    "title": "List Article Title",
                                                    "link": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                                    "digest": "List article description",
                                                    "cover": "https://example.com/article-cover.png",
                                                    "create_time": 1710000000,
                                                }
                                            ]
                                        }
                                    )
                                }
                            ]
                        }
                    ),
                }
            ),
            FakeGatewayResponse(
                text="upstream failure",
                status_code=500,
                headers={"Content-Type": "text/html"},
                url="https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway().sync_feed(self.feed, self.credential)

        self.assertEqual(len(payload["articles"]), 1)
        self.assertEqual(payload["articles"][0]["title"], "List Article Title")
        self.assertEqual(payload["articles"][0]["description"], "List article description")
        self.assertEqual(payload["articles"][0]["content"], "")
        self.assertEqual(payload["articles"][0]["pic_url"], "https://example.com/article-cover.png")
        self.assertEqual(payload["result_payload"]["fetched_count"], 1)
        self.assertEqual(payload["result_payload"]["detail_success_count"], 0)
        self.assertEqual(payload["result_payload"]["detail_failed_count"], 1)
        self.assertEqual(
            payload["result_payload"]["errors"][0]["url"],
            "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
        )

    @patch("we_rss.services.feed_service.requests.Session")
    def test_sync_feed_collects_appmsg_and_appmsgex_articles(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps(
                        {
                            "publish_list": [
                                {
                                    "publish_info": json.dumps(
                                        {
                                            "appmsg": {
                                                "aid": "article-main",
                                                "title": "Main Article",
                                                "link": "https://mp.weixin.qq.com/s/article-main?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                                "digest": "Main article description",
                                                "cover": "https://example.com/main-cover.png",
                                                "create_time": 1710000000,
                                            },
                                            "appmsgex": [
                                                {
                                                    "aid": "article-sub",
                                                    "title": "Sub Article",
                                                    "link": "https://mp.weixin.qq.com/s/article-sub?__biz=Qkl6&mid=1&idx=2&sn=def",
                                                    "digest": "Sub article description",
                                                    "cover": "https://example.com/sub-cover.png",
                                                    "create_time": 1710000100,
                                                }
                                            ],
                                        }
                                    )
                                }
                            ]
                        }
                    ),
                }
            ),
            FakeGatewayResponse(
                text="""
                <html>
                  <head><meta property="og:title" content="Main Article" /></head>
                  <body><div id="js_content"><p>Main content</p></div></body>
                </html>
                """,
                headers={"Content-Type": "text/html"},
                url="https://mp.weixin.qq.com/s/article-main?__biz=Qkl6&mid=1&idx=1&sn=abc",
            ),
            FakeGatewayResponse(
                text="""
                <html>
                  <head><meta property="og:title" content="Sub Article" /></head>
                  <body><div id="js_content"><p>Sub content</p></div></body>
                </html>
                """,
                headers={"Content-Type": "text/html"},
                url="https://mp.weixin.qq.com/s/article-sub?__biz=Qkl6&mid=1&idx=2&sn=def",
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway().sync_feed(self.feed, self.credential)

        self.assertEqual([item["source_id"] for item in payload["articles"]], ["article-main", "article-sub"])
        self.assertEqual([item["title"] for item in payload["articles"]], ["Main Article", "Sub Article"])
        self.assertEqual([item["article_type"] for item in payload["articles"]], ["news", "newspic"])

    @patch("we_rss.services.feed_service.requests.Session")
    def test_sync_feed_keeps_public_article_url_when_detail_redirect_contains_token(self, mock_session_cls):
        session = mock_session_cls.return_value
        public_url = "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc"
        redirected_url = f"{public_url}&token=123456"
        session.get.side_effect = [
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps(
                        {
                            "publish_list": [
                                {
                                    "publish_info": json.dumps(
                                        {
                                            "appmsg": {
                                                "aid": "article-1",
                                                "title": "Stable URL Article",
                                                "link": public_url,
                                                "digest": "Stable URL description",
                                                "cover": "https://example.com/article-cover.png",
                                                "create_time": 1710000000,
                                            }
                                        }
                                    )
                                }
                            ]
                        }
                    ),
                }
            ),
            FakeGatewayResponse(
                text="""
                <html>
                  <head>
                    <meta property="og:title" content="Stable URL Article" />
                  </head>
                  <body>
                    <div id="js_content"><p>Stable URL content</p></div>
                  </body>
                </html>
                """,
                headers={"Content-Type": "text/html"},
                url=redirected_url,
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway().sync_feed(self.feed, self.credential)

        self.assertEqual(payload["articles"][0]["url"], public_url)
        self.assertNotIn("token=", payload["articles"][0]["url"])

    @patch("we_rss.services.feed_service.requests.Session")
    def test_sync_feed_extracts_feed_metadata_from_article_detail(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps(
                        {
                            "publish_list": [
                                {
                                    "publish_info": json.dumps(
                                        {
                                            "appmsgex": [
                                                {
                                                    "aid": "article-1",
                                                    "title": "Synced Article",
                                                    "link": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                                    "digest": "Synced description",
                                                    "cover": "https://example.com/article-cover.png",
                                                    "create_time": 1710000000,
                                                }
                                            ]
                                        }
                                    )
                                }
                            ]
                        }
                    ),
                }
            ),
            FakeGatewayResponse(
                text="""
                <html>
                  <head>
                    <meta property="og:title" content="Synced Article" />
                  </head>
                  <body>
                    <div id="js_name">Updated Feed Name</div>
                    <div id="js_like_profile_bar">
                      <span class="wx_follow_avatar">
                        <img src="https://example.com/feed-avatar.png" />
                      </span>
                    </div>
                    <div id="js_content"><p>Synced content</p></div>
                    <script>var biz = "Qkl6";</script>
                  </body>
                </html>
                """,
                headers={"Content-Type": "text/html"},
                url="https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway().sync_feed(self.feed, self.credential)

        self.assertEqual(payload["feed_payload"]["biz"], "Qkl6")
        self.assertEqual(payload["feed_payload"]["mp_name"], "Updated Feed Name")
        self.assertEqual(payload["feed_payload"]["mp_cover"], "https://example.com/feed-avatar.png")


class FeedApiTests(APITestCase):
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

    def test_member_can_list_tenant_feeds(self):
        WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Tenant Feed",
            source_id="feed-1",
            created_by=self.member,
            updated_by=self.member,
        )
        other_member = Member.objects.create(
            username="other_member",
            email="other-member@example.com",
            tenant=self.other_tenant,
        )
        WechatFeed.objects.create(
            tenant=self.other_tenant,
            mp_name="Other Feed",
            source_id="feed-2",
            created_by=other_member,
            updated_by=other_member,
        )

        response = self.client.get("/api/v1/we-rss/feeds/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["mp_name"], "Tenant Feed")

    def test_member_can_create_and_update_feed(self):
        response = self.client.post(
            "/api/v1/we-rss/feeds/",
            {
                "mp_name": "Created Feed",
                "source_id": "feed-1",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        feed_id = response.data["data"]["id"]

        update_response = self.client.put(
            f"/api/v1/we-rss/feeds/{feed_id}/",
            {
                "mp_name": "Updated Feed",
                "source_id": "feed-1",
            },
            format="json",
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.data["data"]["mp_name"], "Updated Feed")

    def test_feed_search_requires_active_credential(self):
        response = self.client.get("/api/v1/we-rss/feeds/search/?keyword=test")

        self.assertEqual(response.status_code, 400)

    @patch("we_rss.views.feed_views.FeedApiGatewayMixin.get_gateway", return_value=FakeFeedGateway())
    def test_feed_search_uses_active_credential(self, _mock_gateway):
        WechatCredential.objects.create(
            tenant=self.tenant,
            name="Default Credential",
            status="active",
            token="token-1",
            cookie="cookie-1",
            is_default=True,
            created_by=self.member,
            updated_by=self.member,
        )

        response = self.client.get("/api/v1/we-rss/feeds/search/?keyword=test")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"][0]["mp_name"], "test Feed")

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeFeedGateway())
    def test_feed_sync_creates_task(self, _mock_gateway):
        credential = WechatCredential.objects.create(
            tenant=self.tenant,
            name="Default Credential",
            status="active",
            token="token-1",
            cookie="cookie-1",
            is_default=True,
            created_by=self.member,
            updated_by=self.member,
        )
        feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=credential,
            mp_name="Tenant Feed",
            source_id="feed-1",
            created_by=self.member,
            updated_by=self.member,
        )

        response = self.client.post(f"/api/v1/we-rss/feeds/{feed.id}/sync/")

        feed.refresh_from_db()
        task = WechatSyncTask.objects.get(id=response.data["data"]["id"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(task.status, "success")
        self.assertEqual(task.task_type, "feed_sync")
        self.assertIsNotNone(feed.last_synced_at)

    def test_member_can_clear_all_articles_under_a_feed(self):
        feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Tenant Feed",
            source_id="feed-1",
            created_by=self.member,
            updated_by=self.member,
        )
        other_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Other Feed",
            source_id="feed-2",
            created_by=self.member,
            updated_by=self.member,
        )
        other_member = Member.objects.create(
            username="other_feed_member",
            email="other-feed-member@example.com",
            tenant=self.other_tenant,
        )
        other_tenant_feed = WechatFeed.objects.create(
            tenant=self.other_tenant,
            mp_name="Other Tenant Feed",
            source_id="feed-3",
            created_by=other_member,
            updated_by=other_member,
        )

        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=feed,
            source_id="article-1",
            title="Article 1",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=feed,
            source_id="article-2",
            title="Article 2",
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=other_feed,
            source_id="article-3",
            title="Article 3",
        )
        WechatArticle.objects.create(
            tenant=self.other_tenant,
            feed=other_tenant_feed,
            source_id="article-4",
            title="Article 4",
        )

        response = self.client.delete(f"/api/v1/we-rss/feeds/{feed.id}/articles/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["feed_id"], feed.id)
        self.assertEqual(response.data["data"]["deleted_count"], 2)
        self.assertFalse(
            WechatArticle.original_objects.filter(tenant=self.tenant, feed=feed).exists()
        )
        self.assertTrue(
            WechatArticle.original_objects.filter(tenant=self.tenant, feed=other_feed).exists()
        )
        self.assertTrue(
            WechatArticle.original_objects.filter(tenant=self.other_tenant, feed=other_tenant_feed).exists()
        )

    def test_clear_feed_articles_returns_zero_when_feed_has_no_articles(self):
        feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Empty Feed",
            source_id="feed-empty",
            created_by=self.member,
            updated_by=self.member,
        )

        response = self.client.delete(f"/api/v1/we-rss/feeds/{feed.id}/articles/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["feed_id"], feed.id)
        self.assertEqual(response.data["data"]["deleted_count"], 0)
