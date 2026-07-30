import json
import time
from datetime import timezone as datetime_timezone
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import (
    MemberArticleState,
    MemberArticleTagRelation,
    MemberFeedSubscription,
    MemberFeedTagRelation,
    MemberTag,
    WechatArticle,
    WechatCredential,
    WechatFeed,
    WechatSyncTask,
)
from we_rss.services.feed_service import FeedService, WechatFeedGateway


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
    def test_collect_feed_batch_marks_deleted_articles_from_detail_page(self, mock_session_cls):
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
                                                "aid": "article-deleted",
                                                "title": "Deleted List Title",
                                                "link": "https://mp.weixin.qq.com/s/article-deleted?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                                "digest": "Deleted list description",
                                                "cover": "https://example.com/deleted-cover.png",
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
                text="<html><body>The content has been deleted by the author.</body></html>",
                headers={"Content-Type": "text/html"},
                url="https://mp.weixin.qq.com/s/article-deleted?__biz=Qkl6&mid=1&idx=1&sn=abc",
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway().collect_feed_batch(
            self.feed,
            self.credential,
            begin=0,
            batch_size=20,
        )

        self.assertEqual(payload["articles"][0]["source_id"], "article-deleted")
        self.assertEqual(payload["articles"][0]["title"], "Deleted List Title")
        self.assertEqual(payload["articles"][0]["content"], "DELETED")
        self.assertEqual(payload["articles"][0]["status"], "deleted")

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
    def test_sync_feed_extracts_publish_time_from_article_script_when_publish_node_is_empty(self, mock_session_cls):
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
                                                "aid": "article-1",
                                                "title": "Script Publish Time Article",
                                                "link": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                                "digest": "Script publish time description",
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
                    <meta property="og:title" content="Script Publish Time Article" />
                  </head>
                  <body>
                    <div id="publish_time"></div>
                    <div id="js_content"><p>Content</p></div>
                    <script>
                      var biz = "Qkl6";
                      var oriCreateTime = '1775355233';
                      var createTime = '2026-04-05 10:13';
                    </script>
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

        self.assertEqual(
            payload["articles"][0]["publish_time"].astimezone(datetime_timezone.utc).isoformat(),
            "2026-04-05T02:13:00+00:00",
        )

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
    def test_sync_feed_prefers_canonical_detail_url_over_short_list_url(self, mock_session_cls):
        session = mock_session_cls.return_value
        short_url = "https://mp.weixin.qq.com/s/article-short"
        canonical_url = "https://mp.weixin.qq.com/s?__biz=Qkl6&mid=1&idx=1&sn=abc"
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
                                                "title": "Canonical URL Article",
                                                "link": short_url,
                                                "digest": "Canonical URL description",
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
                    <meta property="og:title" content="Canonical URL Article" />
                  </head>
                  <body>
                    <div id="js_content"><p>Canonical URL content</p></div>
                  </body>
                </html>
                """,
                headers={"Content-Type": "text/html"},
                url=canonical_url,
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway().sync_feed(self.feed, self.credential)

        self.assertEqual(payload["articles"][0]["url"], canonical_url)
        self.assertEqual(payload["articles"][0]["source_id"], "article-1")

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

    def test_member_can_subscribe_to_feed_without_affecting_other_members(self):
        feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Tenant Feed",
            source_id="feed-1",
            created_by=self.member,
            updated_by=self.member,
        )
        other_member = Member.objects.create(
            username="other_member_same_tenant",
            email="other-member-same-tenant@example.com",
            tenant=self.tenant,
        )

        subscribe_response = self.client.post(
            "/api/v1/we-rss/feeds/subscribe/",
            {
                "source_id": feed.source_id,
                "mp_name": feed.mp_name,
            },
            format="json",
        )
        list_response = self.client.get("/api/v1/we-rss/feeds/")

        self.assertEqual(subscribe_response.status_code, 200)
        self.assertTrue(list_response.data["data"][0]["is_subscribed"])

        other_token = generate_jwt_token(other_member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {other_token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        other_list_response = self.client.get("/api/v1/we-rss/feeds/")

        self.assertEqual(other_list_response.status_code, 200)
        self.assertFalse(other_list_response.data["data"][0]["is_subscribed"])

    def test_member_can_subscribe_from_search_payload_when_feed_not_yet_saved(self):
        response = self.client.post(
            "/api/v1/we-rss/feeds/subscribe/",
            {
                "source_id": "feed-search-1",
                "faker_id": "faker-search-1",
                "biz": "biz-search-1",
                "mp_name": "Search Feed",
                "mp_cover": "https://example.com/search-feed.png",
                "mp_intro": "Search intro",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["mp_name"], "Search Feed")
        self.assertTrue(response.data["data"]["is_subscribed"])
        self.assertTrue(WechatFeed.objects.filter(tenant=self.tenant, source_id="feed-search-1").exists())

    def test_member_can_filter_feeds_by_subscribed_only(self):
        subscribed_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Subscribed Feed",
            source_id="feed-subscribed",
            created_by=self.member,
            updated_by=self.member,
        )
        WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Unsubscribed Feed",
            source_id="feed-unsubscribed",
            created_by=self.member,
            updated_by=self.member,
        )

        subscribe_response = self.client.post(
            "/api/v1/we-rss/feeds/subscribe/",
            {
                "source_id": subscribed_feed.source_id,
                "mp_name": subscribed_feed.mp_name,
            },
            format="json",
        )
        filtered_response = self.client.get("/api/v1/we-rss/feeds/?subscribed_only=true")

        self.assertEqual(subscribe_response.status_code, 200)
        self.assertEqual(filtered_response.status_code, 200)
        self.assertEqual([item["source_id"] for item in filtered_response.data["data"]], ["feed-subscribed"])

    def test_member_can_unsubscribe_feed(self):
        feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Tenant Feed",
            source_id="feed-1",
            created_by=self.member,
            updated_by=self.member,
        )
        self.client.post(
            "/api/v1/we-rss/feeds/subscribe/",
            {
                "source_id": feed.source_id,
                "mp_name": feed.mp_name,
            },
            format="json",
        )

        unsubscribe_response = self.client.delete(f"/api/v1/we-rss/feeds/{feed.id}/subscribe/")
        list_response = self.client.get("/api/v1/we-rss/feeds/")

        self.assertEqual(unsubscribe_response.status_code, 204)
        self.assertFalse(list_response.data["data"][0]["is_subscribed"])

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

    def test_delete_feed_removes_feed_articles_and_related_relations(self):
        feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Delete Feed",
            source_id="feed-delete-1",
            created_by=self.member,
            updated_by=self.member,
        )
        other_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Keep Feed",
            source_id="feed-keep-1",
            created_by=self.member,
            updated_by=self.member,
        )
        self.client.post(
            "/api/v1/we-rss/feeds/subscribe/",
            {
                "source_id": feed.source_id,
                "mp_name": feed.mp_name,
            },
            format="json",
        )
        tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Cleanup Tag",
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            feed=feed,
        )
        target_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=feed,
            source_id="delete-article-1",
            title="Delete me",
            url="https://mp.weixin.qq.com/s/delete-article-1",
        )
        other_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=other_feed,
            source_id="keep-article-1",
            title="Keep me",
            url="https://mp.weixin.qq.com/s/keep-article-1",
        )
        MemberArticleState.objects.create(
            tenant=self.tenant,
            member=self.member,
            article=target_article,
            is_favorite=True,
        )
        MemberArticleTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            article=target_article,
        )

        response = self.client.delete(f"/api/v1/we-rss/feeds/{feed.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(WechatFeed.objects.filter(id=feed.id).exists())
        self.assertFalse(WechatArticle.objects.filter(id=target_article.id).exists())
        self.assertFalse(MemberArticleState.objects.filter(article_id=target_article.id).exists())
        self.assertFalse(MemberArticleTagRelation.objects.filter(article_id=target_article.id).exists())
        self.assertFalse(MemberFeedSubscription.objects.filter(feed_id=feed.id).exists())
        self.assertFalse(MemberFeedTagRelation.objects.filter(feed_id=feed.id).exists())
        self.assertTrue(WechatFeed.objects.filter(id=other_feed.id).exists())
        self.assertTrue(WechatArticle.objects.filter(id=other_article.id).exists())

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

    def _decode_stream(self, response):
        return b"".join(response.streaming_content).decode("utf-8")

    def _decode_sse_events(self, response):
        body = self._decode_stream(response)
        events = []
        for chunk in body.split("\n\n"):
            chunk = chunk.strip()
            if not chunk:
                continue
            event_name = ""
            payload_lines = []
            for line in chunk.splitlines():
                if line.startswith("event:"):
                    event_name = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    payload_lines.append(line.split(":", 1)[1].strip())
            payload = json.loads("\n".join(payload_lines)) if payload_lines else None
            events.append({"event": event_name, "data": payload})
        return events

    def _create_feed_sync_batch_feed(self, *, source_id, mp_name):
        credential = WechatCredential.objects.create(
            tenant=self.tenant,
            name=f"Credential for {source_id}",
            status="active",
            token=f"token-{source_id}",
            cookie=f"cookie-{source_id}",
            is_default=False,
            created_by=self.member,
            updated_by=self.member,
        )
        return WechatFeed.objects.create(
            tenant=self.tenant,
            credential=credential,
            mp_name=mp_name,
            source_id=source_id,
            created_by=self.member,
            updated_by=self.member,
        )

    @patch("we_rss.views.feed_views.FeedApiGatewayMixin.get_gateway")
    def test_feed_sync_streams_batches(self, mock_gateway):
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
        mock_gateway.return_value.collect_feed_batch.return_value = {
            "articles": [
                {
                    "source_id": "feed-stream-article-1",
                    "article_type": "news",
                    "title": "Feed Stream Article",
                    "description": "Synced description",
                    "content": "<p>Synced content</p>",
                    "url": "https://mp.weixin.qq.com/s/feed-stream-article-1",
                    "pic_url": "https://example.com/feed-stream-article-1.png",
                    "status": "active",
                }
            ],
            "feed_payload": {
                "biz": "Qkl6",
                "mp_name": "Synced Feed Name",
                "mp_cover": "https://example.com/feed-avatar.png",
            },
            "failed_articles": [],
            "has_more": False,
            "next_begin": 1,
            "detail_success_count": 1,
            "detail_failed_count": 0,
        }

        response = self.client.post(
            f"/api/v1/we-rss/feeds/{feed.id}/sync/",
            HTTP_ACCEPT="text/event-stream",
        )
        body = self._decode_stream(response)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertIn("text/event-stream", response["Content-Type"])
        self.assertIn("event: start", body)
        self.assertIn("event: batch", body)
        self.assertIn("event: done", body)
        self.assertIn('"sync_scope": "full"', body)
        self.assertIn('"articles_synced": 1', body)
        self.assertIn('"source_id": "feed-stream-article-1"', body)
        self.assertFalse(WechatSyncTask.objects.filter(task_type="feed_sync_run", target_id=feed.id).exists())
        self.assertTrue(WechatArticle.objects.filter(feed=feed, source_id="feed-stream-article-1").exists())

    @patch("we_rss.views.feed_views.FeedApiGatewayMixin.get_gateway")
    def test_feed_sync_stream_excludes_deleted_articles_from_success_payload(self, mock_gateway):
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
            source_id="feed-deleted-stream-1",
            created_by=self.member,
            updated_by=self.member,
        )
        mock_gateway.return_value.collect_feed_batch.return_value = {
            "articles": [
                {
                    "source_id": "feed-stream-active-1",
                    "article_type": "news",
                    "title": "Feed Stream Active",
                    "description": "Active description",
                    "content": "<p>Active content</p>",
                    "url": "https://mp.weixin.qq.com/s/feed-stream-active-1",
                    "pic_url": "https://example.com/feed-stream-active-1.png",
                    "status": "active",
                },
                {
                    "source_id": "feed-stream-deleted-1",
                    "article_type": "news",
                    "title": "Feed Stream Deleted",
                    "description": "Deleted description",
                    "content": "DELETED",
                    "url": "https://mp.weixin.qq.com/s/feed-stream-deleted-1",
                    "pic_url": "https://example.com/feed-stream-deleted-1.png",
                    "status": "deleted",
                },
            ],
            "feed_payload": {},
            "failed_articles": [],
            "has_more": False,
            "next_begin": 2,
            "detail_success_count": 2,
            "detail_failed_count": 0,
        }

        response = self.client.post(
            f"/api/v1/we-rss/feeds/{feed.id}/sync/",
            HTTP_ACCEPT="text/event-stream",
        )
        body = self._decode_stream(response)

        self.assertEqual(response.status_code, 200)
        self.assertIn('"articles_synced": 1', body)
        self.assertIn('"article_count": 1', body)
        self.assertIn('"source_id": "feed-stream-active-1"', body)
        self.assertIn('"failed_articles"', body)
        self.assertIn("feed-stream-deleted-1", body)
        self.assertIn("Wechat article is unavailable or has been deleted.", body)
        self.assertTrue(WechatArticle.objects.filter(feed=feed, source_id="feed-stream-active-1").exists())
        self.assertFalse(WechatArticle.objects.filter(feed=feed, source_id="feed-stream-deleted-1").exists())

    @patch("we_rss.views.feed_views.FeedApiGatewayMixin.get_gateway")
    def test_feed_sync_accepts_refresh_markdown_request(self, mock_gateway):
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
            source_id="feed-refresh-markdown-1",
            created_by=self.member,
            updated_by=self.member,
        )
        mock_gateway.return_value.collect_feed_batch.return_value = {
            "articles": [],
            "feed_payload": {},
            "failed_articles": [],
            "has_more": False,
            "next_begin": 0,
            "detail_success_count": 0,
            "detail_failed_count": 0,
        }

        response = self.client.post(
            f"/api/v1/we-rss/feeds/{feed.id}/sync/",
            {"refresh_markdown": True},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        body = self._decode_stream(response)

        self.assertEqual(response.status_code, 200)
        self.assertIn('"refresh_markdown": true', body)

    @patch("we_rss.views.feed_views.FeedApiGatewayMixin.get_gateway")
    def test_feed_sync_accepts_latest_scope_request(self, mock_gateway):
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
            source_id="feed-latest-1",
            created_by=self.member,
            updated_by=self.member,
        )
        mock_gateway.return_value.collect_feed_batch.return_value = {
            "articles": [],
            "feed_payload": {},
            "failed_articles": [],
            "has_more": False,
            "next_begin": 0,
            "detail_success_count": 0,
            "detail_failed_count": 0,
        }

        response = self.client.post(
            f"/api/v1/we-rss/feeds/{feed.id}/sync/",
            {"sync_scope": "latest"},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        body = self._decode_stream(response)

        self.assertEqual(response.status_code, 200)
        self.assertIn('"sync_scope": "latest"', body)
        self.assertIn('"window_days": null', body)

    @patch("we_rss.views.feed_views.FeedApiGatewayMixin.get_gateway")
    def test_feed_sync_accepts_window_scope_request(self, mock_gateway):
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
            source_id="feed-window-1",
            created_by=self.member,
            updated_by=self.member,
        )
        mock_gateway.return_value.collect_feed_batch.return_value = {
            "articles": [],
            "feed_payload": {},
            "failed_articles": [],
            "has_more": False,
            "next_begin": 0,
            "detail_success_count": 0,
            "detail_failed_count": 0,
        }

        response = self.client.post(
            f"/api/v1/we-rss/feeds/{feed.id}/sync/",
            {"sync_scope": "window", "window_days": 7},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        body = self._decode_stream(response)

        self.assertEqual(response.status_code, 200)
        self.assertIn('"sync_scope": "window"', body)
        self.assertIn('"window_days": 7', body)
        self.assertIn("event: batch", body)
        self.assertIn("event: done", body)

    def test_feed_content_refresh_streams_article_markdown_progress(self):
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
            source_id="feed-content-refresh-1",
            created_by=self.member,
            updated_by=self.member,
        )
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=feed,
            source_id="feed-content-article-1",
            title="First Article",
            url="https://mp.weixin.qq.com/s/feed-content-article-1",
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=feed,
            source_id="feed-content-article-2",
            title="Second Article",
            url="https://mp.weixin.qq.com/s/feed-content-article-2",
        )

        def markdown_side_effect(url):
            if url.endswith("feed-content-article-2"):
                raise RuntimeError("markdown blocked")
            return f"# Markdown for {url}"

        with patch("we_rss.views.feed_views.get_article_markdown_service") as service_factory:
            service_factory.return_value.fetch_markdown_from_url.side_effect = markdown_side_effect
            response = self.client.post(
                f"/api/v1/we-rss/feeds/{feed.id}/refresh-content/",
                HTTP_ACCEPT="text/event-stream",
            )

        body = self._decode_stream(response)
        first_article.refresh_from_db()
        second_article.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response["Content-Type"])
        self.assertIn("event: start", body)
        self.assertIn("event: progress", body)
        self.assertIn("event: done", body)
        self.assertIn('"total": 2', body)
        self.assertIn('"success_count": 1', body)
        self.assertIn('"failed_count": 1', body)
        self.assertIn("markdown blocked", body)
        self.assertEqual(first_article.content, "# Markdown for https://mp.weixin.qq.com/s/feed-content-article-1")
        self.assertEqual(second_article.content, "")

    def test_feed_sync_rejects_invalid_sync_scope(self):
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
            source_id="feed-invalid-scope-1",
            created_by=self.member,
            updated_by=self.member,
        )

        response = self.client.post(
            f"/api/v1/we-rss/feeds/{feed.id}/sync/",
            {"sync_scope": "invalid"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("sync_scope", response.data["data"])

    def test_feed_sync_requires_window_days_for_window_scope(self):
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
            source_id="feed-window-required-1",
            created_by=self.member,
            updated_by=self.member,
        )

        response = self.client.post(
            f"/api/v1/we-rss/feeds/{feed.id}/sync/",
            {"sync_scope": "window"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("window_days", response.data["data"])

    def test_feed_sync_rejects_window_days_out_of_range(self):
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
            source_id="feed-window-range-1",
            created_by=self.member,
            updated_by=self.member,
        )

        too_small_response = self.client.post(
            f"/api/v1/we-rss/feeds/{feed.id}/sync/",
            {"sync_scope": "window", "window_days": 0},
            format="json",
        )
        too_large_response = self.client.post(
            f"/api/v1/we-rss/feeds/{feed.id}/sync/",
            {"sync_scope": "window", "window_days": 181},
            format="json",
        )

        self.assertEqual(too_small_response.status_code, 400)
        self.assertIn("window_days", too_small_response.data["data"])
        self.assertEqual(too_large_response.status_code, 400)
        self.assertIn("window_days", too_large_response.data["data"])

    def test_feed_sync_rejects_window_days_for_non_window_scope(self):
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
            source_id="feed-window-extra-1",
            created_by=self.member,
            updated_by=self.member,
        )

        response = self.client.post(
            f"/api/v1/we-rss/feeds/{feed.id}/sync/",
            {"sync_scope": "latest", "window_days": 7},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("window_days", response.data["data"])

    def test_feed_sync_batch_requires_feed_ids(self):
        response = self.client.post(
            "/api/v1/we-rss/feeds/sync-batch/",
            {"sync_scope": "full"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("feed_ids", response.data["data"])

    def test_feed_sync_batch_requires_window_days_for_window_scope(self):
        response = self.client.post(
            "/api/v1/we-rss/feeds/sync-batch/",
            {"feed_ids": [1], "sync_scope": "window"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("window_days", response.data["data"])

    def test_feed_sync_batch_rejects_more_than_200_feed_ids(self):
        response = self.client.post(
            "/api/v1/we-rss/feeds/sync-batch/",
            {"feed_ids": list(range(1, 202)), "sync_scope": "full"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("feed_ids", response.data["data"])

    @patch.object(FeedService, "execute_sync_batch_inline")
    def test_feed_sync_batch_deduplicates_feed_ids_and_preserves_order(self, mock_execute_sync_batch_inline):
        first_feed = self._create_feed_sync_batch_feed(source_id="batch-feed-1", mp_name="Batch Feed 1")
        second_feed = self._create_feed_sync_batch_feed(source_id="batch-feed-2", mp_name="Batch Feed 2")
        third_feed = self._create_feed_sync_batch_feed(source_id="batch-feed-3", mp_name="Batch Feed 3")
        observed_feed_ids = []

        def execute_side_effect(**kwargs):
            observed_feed_ids.append(kwargs["feed"].id)
            return {
                "batch_no": kwargs["batch_no"],
                "begin": kwargs["begin"],
                "end": kwargs["begin"] + 1,
                "has_more": False,
                "next_begin": kwargs["begin"] + 1,
                "article_count": 1,
                "article_ids": [kwargs["feed"].id * 10],
                "articles": [],
                "failed_articles": [],
                "detail_success_count": 1,
                "detail_failed_count": 0,
            }

        mock_execute_sync_batch_inline.side_effect = execute_side_effect

        response = self.client.post(
            "/api/v1/we-rss/feeds/sync-batch/",
            {
                "feed_ids": [first_feed.id, second_feed.id, first_feed.id, third_feed.id],
                "sync_scope": "window",
                "window_days": 7,
            },
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        events = self._decode_sse_events(response)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(observed_feed_ids, [first_feed.id, second_feed.id, third_feed.id])
        self.assertEqual(events[0]["event"], "start")
        self.assertEqual(events[0]["data"]["queued_feed_ids"], [first_feed.id, second_feed.id, third_feed.id])
        self.assertEqual(events[-1]["event"], "done")
        self.assertEqual(events[-1]["data"]["total_feeds"], 3)

    @patch.object(FeedService, "execute_sync_batch_inline")
    def test_feed_sync_batch_streams_events_in_serial_order(self, mock_execute_sync_batch_inline):
        first_feed = self._create_feed_sync_batch_feed(source_id="serial-feed-1", mp_name="Serial Feed 1")
        second_feed = self._create_feed_sync_batch_feed(source_id="serial-feed-2", mp_name="Serial Feed 2")

        def execute_side_effect(**kwargs):
            return {
                "batch_no": kwargs["batch_no"],
                "begin": kwargs["begin"],
                "end": kwargs["begin"] + 1,
                "has_more": False,
                "next_begin": kwargs["begin"] + 1,
                "article_count": 1,
                "article_ids": [kwargs["feed"].id * 100],
                "articles": [],
                "failed_articles": [],
                "detail_success_count": 1,
                "detail_failed_count": 0,
            }

        mock_execute_sync_batch_inline.side_effect = execute_side_effect

        response = self.client.post(
            "/api/v1/we-rss/feeds/sync-batch/",
            {"feed_ids": [first_feed.id, second_feed.id], "sync_scope": "full"},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        events = self._decode_sse_events(response)

        self.assertEqual(
            [event["event"] for event in events],
            ["start", "feed_start", "feed_batch", "feed_done", "feed_start", "feed_batch", "feed_done", "done"],
        )
        self.assertEqual(events[1]["data"]["feed_id"], first_feed.id)
        self.assertEqual(events[4]["data"]["feed_id"], second_feed.id)
        self.assertEqual(events[-1]["data"]["completed_feeds"], 2)

    @patch.object(FeedService, "execute_sync_batch_inline")
    def test_feed_sync_batch_continues_after_single_feed_failure_and_reports_done_results(
        self,
        mock_execute_sync_batch_inline,
    ):
        first_feed = self._create_feed_sync_batch_feed(source_id="continue-feed-1", mp_name="Continue Feed 1")
        third_feed = self._create_feed_sync_batch_feed(source_id="continue-feed-3", mp_name="Continue Feed 3")
        missing_feed_id = 999999

        def execute_side_effect(**kwargs):
            if kwargs["feed"].id == first_feed.id:
                return {
                    "batch_no": 1,
                    "begin": 0,
                    "end": 10,
                    "has_more": False,
                    "next_begin": 10,
                    "article_count": 2,
                    "article_ids": [101, 102],
                    "articles": [],
                    "failed_articles": [],
                    "detail_success_count": 2,
                    "detail_failed_count": 1,
                }
            if kwargs["feed"].id == third_feed.id:
                return {
                    "batch_no": 1,
                    "begin": 0,
                    "end": 5,
                    "has_more": False,
                    "next_begin": 5,
                    "article_count": 1,
                    "article_ids": [301],
                    "articles": [],
                    "failed_articles": [],
                    "detail_success_count": 1,
                    "detail_failed_count": 0,
                }
            raise AssertionError("Unexpected feed execution")

        mock_execute_sync_batch_inline.side_effect = execute_side_effect

        response = self.client.post(
            "/api/v1/we-rss/feeds/sync-batch/",
            {
                "feed_ids": [first_feed.id, missing_feed_id, third_feed.id],
                "sync_scope": "window",
                "window_days": 7,
                "continue_on_error": True,
            },
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        events = self._decode_sse_events(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([event["event"] for event in events].count("feed_done"), 3)
        failed_feed_done = [event for event in events if event["event"] == "feed_done" and event["data"]["feed_id"] == missing_feed_id][0]
        self.assertEqual(failed_feed_done["data"]["status"], "failed")
        self.assertEqual(failed_feed_done["data"]["error"], "feed not found")
        self.assertEqual(events[-1]["event"], "done")
        self.assertEqual(events[-1]["data"]["success_feeds"], 2)
        self.assertEqual(events[-1]["data"]["failed_feeds"], 1)
        self.assertEqual(
            events[-1]["data"]["results"],
            [
                {"feed_id": first_feed.id, "status": "success", "articles_synced": 2, "articles_failed": 1},
                {"feed_id": missing_feed_id, "status": "failed", "error": "feed not found"},
                {"feed_id": third_feed.id, "status": "success", "articles_synced": 1, "articles_failed": 0},
            ],
        )

    @patch.object(FeedService, "execute_sync_batch_inline")
    def test_feed_sync_batch_stops_after_single_feed_failure_when_continue_on_error_false(
        self,
        mock_execute_sync_batch_inline,
    ):
        first_feed = self._create_feed_sync_batch_feed(source_id="stop-feed-1", mp_name="Stop Feed 1")
        second_feed = self._create_feed_sync_batch_feed(source_id="stop-feed-2", mp_name="Stop Feed 2")

        def execute_side_effect(**kwargs):
            if kwargs["feed"].id == first_feed.id:
                raise RuntimeError("batch failed")
            raise AssertionError("The second feed should not be executed")

        mock_execute_sync_batch_inline.side_effect = execute_side_effect

        response = self.client.post(
            "/api/v1/we-rss/feeds/sync-batch/",
            {
                "feed_ids": [first_feed.id, second_feed.id],
                "sync_scope": "full",
                "continue_on_error": False,
            },
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        events = self._decode_sse_events(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([event["event"] for event in events], ["start", "feed_start", "feed_done", "error"])
        self.assertEqual(events[2]["data"]["status"], "failed")
        self.assertEqual(events[2]["data"]["error"], "batch failed")
        self.assertEqual(events[3]["data"]["status"], "failed")
        self.assertEqual(events[3]["data"]["error"], "batch sync aborted after feed failure")

    @patch.object(FeedService, "BATCH_STREAM_HEARTBEAT_INTERVAL_SECONDS", 0.01)
    @patch.object(FeedService, "execute_sync_batch_inline")
    def test_feed_sync_batch_emits_heartbeat_while_waiting_for_long_batch(self, mock_execute_sync_batch_inline):
        feed = self._create_feed_sync_batch_feed(source_id="heartbeat-feed-1", mp_name="Heartbeat Feed 1")

        def execute_side_effect(**kwargs):
            time.sleep(0.05)
            return {
                "batch_no": kwargs["batch_no"],
                "begin": kwargs["begin"],
                "end": kwargs["begin"] + 1,
                "has_more": False,
                "next_begin": kwargs["begin"] + 1,
                "article_count": 1,
                "article_ids": [901],
                "articles": [],
                "failed_articles": [],
                "detail_success_count": 1,
                "detail_failed_count": 0,
            }

        mock_execute_sync_batch_inline.side_effect = execute_side_effect

        response = self.client.post(
            "/api/v1/we-rss/feeds/sync-batch/",
            {"feed_ids": [feed.id], "sync_scope": "full"},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        events = self._decode_sse_events(response)

        heartbeat_events = [event for event in events if event["event"] == "heartbeat"]
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(heartbeat_events), 1)
        self.assertEqual(heartbeat_events[0]["data"]["current_feed_id"], feed.id)
        self.assertEqual(events[-1]["event"], "done")

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


class FeedTagFilterApiTests(APITestCase):
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
        self.feed_with_both_tags = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Feed With Both Tags",
            source_id="feed-both",
            created_by=self.member,
            updated_by=self.member,
        )
        self.feed_with_one_tag = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Feed With One Tag",
            source_id="feed-one",
            created_by=self.member,
            updated_by=self.member,
        )
        self.feed_with_other_member_tag = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Other Member Tagged Feed",
            source_id="feed-other",
            created_by=self.member,
            updated_by=self.member,
        )
        for feed in (
            self.feed_with_both_tags,
            self.feed_with_one_tag,
            self.feed_with_other_member_tag,
        ):
            MemberFeedSubscription.objects.create(
                tenant=self.tenant,
                member=self.member,
                feed=feed,
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
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag_one,
            feed=self.feed_with_both_tags,
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag_two,
            feed=self.feed_with_both_tags,
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag_one,
            feed=self.feed_with_one_tag,
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.other_member,
            tag=other_member_tag,
            feed=self.feed_with_other_member_tag,
        )

    def test_feed_list_filters_by_all_requested_tag_ids(self):
        response = self.client.get(
            f"/api/v1/we-rss/feeds/?tag_ids={self.tag_one.id},{self.tag_two.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["data"]],
            [self.feed_with_both_tags.id],
        )

    def test_feed_list_tag_filter_only_uses_current_member_relations(self):
        response = self.client.get(f"/api/v1/we-rss/feeds/?tag_ids={self.tag_one.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item["id"] for item in response.data["data"]},
            {self.feed_with_both_tags.id, self.feed_with_one_tag.id},
        )
