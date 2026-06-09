import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch, call

import requests
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from we_rss.services.feed_service import WechatFeedGateway
from we_rss.services.wechat_gateway import build_wechat_session, parse_publish_page_articles


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

    @staticmethod
    def _article_payload_without_publish_time(article_id, title, index):
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
                <div id="js_content"><p>{title} content</p></div>
                <script>var biz = "Qkl6";</script>
              </body>
            </html>
            """,
            headers={"Content-Type": "text/html"},
            url=f"https://mp.weixin.qq.com/s/{article_id}?__biz=Qkl6&mid=1&idx={index}&sn=abc",
        )

    def _build_publish_and_article_side_effects(self, *, total):
        responses = []
        for index in range(1, total + 1):
            article_id = f"article-{index}"
            title = f"Article {index}"
            responses.append(self._publish_payload(article_id, title, index))
        responses.append(
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            )
            )
        return responses

    @staticmethod
    def _multi_article_publish_payload(*, records):
        publish_list = []
        for record in records:
            appmsg = record.get("appmsg")
            appmsgex = record.get("appmsgex") or []
            publish_list.append(
                {
                    "publish_info": json.dumps(
                        {
                            "appmsg": appmsg,
                            "appmsgex": appmsgex,
                        }
                    )
                }
            )
        return FakeGatewayResponse(
            json_data={
                "base_resp": {"ret": 0},
                "publish_page": json.dumps({"publish_list": publish_list}),
            }
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

    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_returns_at_most_twenty_articles(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = self._build_publish_and_article_side_effects(total=23)

        payload = WechatFeedGateway(page_size=1).collect_feed_batch(
            self.feed,
            self.credential,
            begin=0,
            batch_size=20,
            deadline_at=None,
        )

        self.assertEqual(len(payload["articles"]), 20)
        self.assertTrue(payload["has_more"])
        self.assertEqual(payload["next_begin"], 20)

    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_returns_terminal_page_when_publish_list_is_exhausted(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = self._build_publish_and_article_side_effects(total=7)

        payload = WechatFeedGateway(page_size=1).collect_feed_batch(
            self.feed,
            self.credential,
            begin=0,
            batch_size=20,
            deadline_at=None,
        )

        self.assertEqual(len(payload["articles"]), 7)
        self.assertFalse(payload["has_more"])
        self.assertEqual(payload["next_begin"], 7)

    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_advances_begin_by_publish_record_count(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            self._multi_article_publish_payload(
                records=[
                    {
                        "appmsg": {
                            "aid": "main-1",
                            "title": "Main 1",
                            "link": "https://mp.weixin.qq.com/s/main-1?__biz=Qkl6&mid=1&idx=1&sn=main1",
                            "digest": "Main 1 description",
                            "cover": "https://example.com/main-1.png",
                            "create_time": 1710000001,
                            "item_show_type": 0,
                        },
                        "appmsgex": [
                            {
                                "aid": "sub-1",
                                "title": "Sub 1",
                                "link": "https://mp.weixin.qq.com/s/sub-1?__biz=Qkl6&mid=1&idx=2&sn=sub1",
                                "digest": "Sub 1 description",
                                "cover": "https://example.com/sub-1.png",
                                "create_time": 1710000002,
                                "item_show_type": 8,
                            }
                        ],
                    }
                ]
            ),
            self._article_payload("main-1", "Main 1", 1),
            self._article_payload("sub-1", "Sub 1", 2),
            self._multi_article_publish_payload(
                records=[
                    {
                        "appmsg": {
                            "aid": "main-2",
                            "title": "Main 2",
                            "link": "https://mp.weixin.qq.com/s/main-2?__biz=Qkl6&mid=2&idx=1&sn=main2",
                            "digest": "Main 2 description",
                            "cover": "https://example.com/main-2.png",
                            "create_time": 1710000003,
                            "item_show_type": 0,
                        },
                        "appmsgex": [
                            {
                                "aid": "sub-2",
                                "title": "Sub 2",
                                "link": "https://mp.weixin.qq.com/s/sub-2?__biz=Qkl6&mid=2&idx=2&sn=sub2",
                                "digest": "Sub 2 description",
                                "cover": "https://example.com/sub-2.png",
                                "create_time": 1710000004,
                                "item_show_type": 8,
                            }
                        ],
                    }
                ]
            ),
            self._article_payload("main-2", "Main 2", 1),
            self._article_payload("sub-2", "Sub 2", 2),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway(page_size=1).collect_feed_batch(
            self.feed,
            self.credential,
            begin=0,
            batch_size=10,
            deadline_at=None,
        )

        publish_request_begins = [
            call.kwargs["params"]["begin"]
            for call in session.get.call_args_list
            if call.kwargs.get("params", {}).get("sub_action") == "list_ex"
        ]

        self.assertEqual(
            [item["source_id"] for item in payload["articles"]],
            ["main-1", "sub-1", "main-2", "sub-2"],
        )
        self.assertEqual(publish_request_begins, [0, 1, 2])

    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_prefers_update_time_when_detail_publish_time_missing(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            self._multi_article_publish_payload(
                records=[
                    {
                        "appmsgex": [
                            {
                                "aid": "article-1",
                                "title": "Article 1",
                                "link": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                "digest": "Article 1 description",
                                "cover": "https://example.com/article-1.png",
                                "create_time": 1710000000,
                                "update_time": 1710003600,
                                "item_show_type": 0,
                            }
                        ]
                    }
                ]
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway(page_size=1, sleep_seconds=0, sleep_func=Mock()).collect_feed_batch(
            self.feed,
            self.credential,
            begin=0,
            batch_size=20,
            deadline_at=None,
        )

        self.assertEqual(
            payload["articles"][0]["publish_time"],
            timezone.datetime.fromtimestamp(1710003600, tz=timezone.get_current_timezone()),
        )

    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_raises_clear_error_for_non_json_publish_payload(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.return_value = FakeGatewayResponse(
            text="<html><body>frequency control</body></html>",
            headers={"Content-Type": "text/html"},
        )

        with self.assertRaises(ValidationError) as context:
            WechatFeedGateway(page_size=1, sleep_seconds=0, sleep_func=Mock()).collect_feed_batch(
                self.feed,
                self.credential,
                begin=0,
                batch_size=20,
                deadline_at=None,
            )

        self.assertIn("non-JSON response", str(context.exception))

    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_raises_frequency_control_error_for_ret_200013(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.return_value = FakeGatewayResponse(
            json_data={
                "base_resp": {
                    "ret": 200013,
                    "err_msg": "frequency control",
                },
                "publish_page": json.dumps({"publish_list": []}),
            }
        )

        with self.assertRaises(ValidationError) as context:
            WechatFeedGateway(page_size=1, sleep_seconds=0, sleep_func=Mock()).collect_feed_batch(
                self.feed,
                self.credential,
                begin=40,
                batch_size=20,
                deadline_at=None,
            )

        self.assertIn("frequency control", str(context.exception).lower())

    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_retries_list_requests_with_dedicated_publish_timeout(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            requests.ReadTimeout("publish timeout"),
            self._multi_article_publish_payload(
                records=[
                    {
                        "appmsgex": [
                            {
                                "aid": "article-1",
                                "title": "Article 1",
                                "link": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                "digest": "Article 1 description",
                                "cover": "https://example.com/article-1.png",
                                "create_time": 1710000000,
                                "update_time": 1710003600,
                                "item_show_type": 0,
                            }
                        ]
                    }
                ]
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        payload = WechatFeedGateway(
            page_size=1,
            timeout=120,
            publish_timeout=30,
            sleep_seconds=0,
            sleep_func=Mock(),
        ).collect_feed_batch(
            self.feed,
            self.credential,
            begin=0,
            batch_size=20,
            deadline_at=None,
        )

        publish_calls = [
            call
            for call in session.get.call_args_list
            if call.kwargs.get("params", {}).get("sub_action") == "list_ex"
        ]

        self.assertEqual(len(payload["articles"]), 1)
        self.assertEqual(len(publish_calls), 3)
        self.assertEqual([call.kwargs["timeout"] for call in publish_calls], [30, 30, 30])

    @patch("we_rss.services.feed_service.print")
    @patch("we_rss.services.feed_service.logger")
    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_logs_each_page_payload(self, mock_session_cls, mock_logger, mock_print):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            self._multi_article_publish_payload(
                records=[
                    {
                        "appmsgex": [
                            {
                                "aid": "article-1",
                                "title": "Article 1",
                                "link": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                "digest": "Article 1 description",
                                "cover": "https://example.com/article-1.png",
                                "create_time": 1710000000,
                                "update_time": 1710003600,
                                "item_show_type": 0,
                            }
                        ]
                    }
                ]
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        WechatFeedGateway(page_size=1, sleep_seconds=0, sleep_func=Mock()).collect_feed_batch(
            self.feed,
            self.credential,
            begin=0,
            batch_size=20,
            deadline_at=None,
        )

        logged_message = mock_logger.info.call_args.args[0]
        self.assertIn("We RSS feed sync page fetched:", logged_message)
        self.assertIn("\"begin\": 0", logged_message)
        self.assertIn("\"title\": \"Article 1\"", logged_message)
        self.assertEqual(mock_print.call_args.args[0], logged_message)

    @patch("we_rss.services.feed_service.print")
    @patch("we_rss.services.feed_service.logger")
    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_keeps_running_when_stdout_print_is_unavailable(
        self,
        mock_session_cls,
        mock_logger,
        mock_print,
    ):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            self._multi_article_publish_payload(
                records=[
                    {
                        "appmsgex": [
                            {
                                "aid": "article-1",
                                "title": "Article 1",
                                "link": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                "digest": "Article 1 description",
                                "cover": "https://example.com/article-1.png",
                                "create_time": 1710000000,
                                "update_time": 1710003600,
                                "item_show_type": 0,
                            }
                        ]
                    }
                ]
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]
        mock_print.side_effect = OSError(22, "Invalid argument")

        payload = WechatFeedGateway(page_size=1, sleep_seconds=0, sleep_func=Mock()).collect_feed_batch(
            self.feed,
            self.credential,
            begin=0,
            batch_size=20,
            deadline_at=None,
        )

        self.assertEqual(len(payload["articles"]), 1)
        self.assertEqual(payload["articles"][0]["source_id"], "article-1")
        mock_logger.info.assert_called()
        mock_logger.warning.assert_called_once()

    @patch("we_rss.services.feed_service.print")
    @patch("we_rss.services.feed_service.logger")
    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_keeps_running_when_stdout_print_has_encoding_error(
        self,
        mock_session_cls,
        mock_logger,
        mock_print,
    ):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            self._multi_article_publish_payload(
                records=[
                    {
                        "appmsgex": [
                            {
                                "aid": "article-1",
                                "title": "Article 1\u200b",
                                "link": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                "digest": "Article 1 description",
                                "cover": "https://example.com/article-1.png",
                                "create_time": 1710000000,
                                "update_time": 1710003600,
                                "item_show_type": 0,
                            }
                        ]
                    }
                ]
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]
        mock_print.side_effect = UnicodeEncodeError("gbk", "\u200b", 0, 1, "illegal multibyte sequence")

        payload = WechatFeedGateway(page_size=1, sleep_seconds=0, sleep_func=Mock()).collect_feed_batch(
            self.feed,
            self.credential,
            begin=0,
            batch_size=20,
            deadline_at=None,
        )

        self.assertEqual(len(payload["articles"]), 1)
        self.assertEqual(payload["articles"][0]["source_id"], "article-1")
        mock_logger.info.assert_called()
        mock_logger.warning.assert_called_once()

    @patch("we_rss.services.feed_service.requests.Session")
    def test_collect_feed_batch_writes_page_payload_to_log_file(self, mock_session_cls):
        session = mock_session_cls.return_value
        session.get.side_effect = [
            self._multi_article_publish_payload(
                records=[
                    {
                        "appmsgex": [
                            {
                                "aid": "article-1",
                                "title": "Article 1",
                                "link": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                                "digest": "Article 1 description",
                                "cover": "https://example.com/article-1.png",
                                "create_time": 1710000000,
                                "update_time": 1710003600,
                                "item_show_type": 0,
                            }
                        ]
                    }
                ]
            ),
            FakeGatewayResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "publish_page": json.dumps({"publish_list": []}),
                }
            ),
        ]

        with TemporaryDirectory() as temp_dir:
            with patch("we_rss.services.feed_service.settings.LOGS_DIR", temp_dir):
                WechatFeedGateway(page_size=1, sleep_seconds=0, sleep_func=Mock()).collect_feed_batch(
                    self.feed,
                    self.credential,
                    begin=0,
                    batch_size=20,
                    deadline_at=None,
                )

            content = Path(temp_dir, "we_rss_feed_sync_pages.log").read_text(encoding="utf-8")

        self.assertIn("\"begin\": 0", content)
        self.assertIn("\"title\": \"Article 1\"", content)


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


class BuildWechatSessionTests(unittest.TestCase):
    def test_build_wechat_session_uses_mobile_wechat_headers(self):
        session = build_wechat_session()

        self.assertIn("MicroMessenger", session.headers["User-Agent"])
        self.assertIn("iPhone", session.headers["User-Agent"])
        self.assertEqual(
            session.headers["Accept"],
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        )
        self.assertEqual(session.headers["Accept-Language"], "zh-CN,zh;q=0.9,en;q=0.8")
        self.assertEqual(session.headers["Referer"], "https://mp.weixin.qq.com/")
