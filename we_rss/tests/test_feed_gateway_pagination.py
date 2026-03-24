import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch, call

from we_rss.services.feed_service import WechatFeedGateway
from we_rss.services.wechat_gateway import parse_publish_page_articles


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


class FeedGatewayPaginationTests(unittest.TestCase):
    def setUp(self):
        self.feed = SimpleNamespace(
            faker_id="fakeid-1",
            source_id="feed-1",
            mp_name="Tenant Feed",
            mp_cover="https://example.com/feed-cover.png",
        )
        self.credential = SimpleNamespace(
            token="token-123",
            cookie="slave_sid=sid-1; fingerprint=fp-1",
        )

    @staticmethod
    def _publish_payload(article_id, title, index):
        return FakeGatewayResponse(
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
                                                "aid": article_id,
                                                "title": title,
                                                "link": f"https://mp.weixin.qq.com/s/{article_id}?__biz=Qkl6&mid=1&idx={index}&sn=abc",
                                                "digest": f"{title} description",
                                                "cover": f"https://example.com/{article_id}.png",
                                                "create_time": 1710000000 + index,
                                            }
                                        ]
                                    }
                                )
                            }
                        ]
                    }
                ),
            }
        )

    @staticmethod
    def _article_payload(article_id, title, index):
        return FakeGatewayResponse(
            text=f"""
            <html>
              <head>
                <meta property="og:title" content="{title}" />
                <meta property="og:description" content="{title} description" />
                <meta property="twitter:image" content="https://example.com/{article_id}.png" />
              </head>
              <body>
                <div id="js_name">Tenant Feed</div>
                <div id="publish_time">2026-03-20 12:00</div>
                <div id="js_content"><p>{title} content</p></div>
                <script>var biz = "Qkl6";</script>
              </body>
            </html>
            """,
            headers={"Content-Type": "text/html"},
            url=f"https://mp.weixin.qq.com/s/{article_id}?__biz=Qkl6&mid=1&idx={index}&sn=abc",
        )

    @patch("we_rss.services.feed_service.requests.Session")
    def test_sync_feed_continues_paging_until_empty_page(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            self._publish_payload("article-1", "Article 1", 1),
            self._article_payload("article-1", "Article 1", 1),
            self._publish_payload("article-2", "Article 2", 2),
            self._article_payload("article-2", "Article 2", 2),
            self._publish_payload("article-3", "Article 3", 3),
            self._article_payload("article-3", "Article 3", 3),
            self._publish_payload("article-4", "Article 4", 4),
            self._article_payload("article-4", "Article 4", 4),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway(page_size=1).sync_feed(self.feed, self.credential)

        self.assertEqual(
            [item["source_id"] for item in payload["articles"]],
            ["article-1", "article-2", "article-3", "article-4"],
        )

    @patch("we_rss.services.feed_service.requests.Session")
    def test_sync_feed_sleeps_half_second_between_pages_and_article_details(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            self._publish_payload("article-1", "Article 1", 1),
            self._article_payload("article-1", "Article 1", 1),
            self._publish_payload("article-2", "Article 2", 2),
            self._article_payload("article-2", "Article 2", 2),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]
        sleep_mock = Mock()

        payload = WechatFeedGateway(page_size=1, sleep_seconds=0.5, sleep_func=sleep_mock).sync_feed(self.feed, self.credential)

        self.assertEqual([item["source_id"] for item in payload["articles"]], ["article-1", "article-2"])
        self.assertEqual(sleep_mock.call_args_list, [call(0.5), call(0.5), call(0.5)])


class ParsePublishPageArticlesTests(unittest.TestCase):
    def test_appmsgex_with_item_show_type_zero_maps_to_news(self):
        payload = {
            "publish_page": json.dumps(
                {
                    "publish_list": [
                        {
                            "publish_info": json.dumps(
                                {
                                    "appmsgex": [
                                        {
                                            "aid": "article-news",
                                            "title": "News Article",
                                            "item_show_type": 0,
                                        }
                                    ]
                                }
                            )
                        }
                    ]
                }
            )
        }

        articles = parse_publish_page_articles(payload)

        self.assertEqual([item["article_type"] for item in articles], ["news"])

    def test_appmsg_with_item_show_type_eight_maps_to_newspic(self):
        payload = {
            "publish_page": json.dumps(
                {
                    "publish_list": [
                        {
                            "publish_info": json.dumps(
                                {
                                    "appmsg": {
                                        "aid": "article-newspic",
                                        "title": "Newspic Article",
                                        "item_show_type": 8,
                                    }
                                }
                            )
                        }
                    ]
                }
            )
        }

        articles = parse_publish_page_articles(payload)

        self.assertEqual([item["article_type"] for item in articles], ["newspic"])
