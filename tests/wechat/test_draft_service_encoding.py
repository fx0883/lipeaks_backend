import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from wechat.services import wechat as wechat_service


class WechatDraftEncodingTests(unittest.TestCase):
    @patch("wechat.services.wechat.requests.post")
    def test_add_draft_posts_utf8_json_without_unicode_escape(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"media_id": "draft-123"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        articles = [
            {
                "article_type": "news",
                "title": "明白了什么是",
                "author": "小峰峰",
                "content": "<p>正文</p>",
                "thumb_media_id": "thumb-123",
            }
        ]

        wechat_service.add_draft("token-123", articles)

        _, kwargs = mock_post.call_args
        self.assertNotIn("json", kwargs)
        self.assertIn("data", kwargs)
        payload = kwargs["data"]
        self.assertIsInstance(payload, bytes)
        self.assertIn("明白了什么是".encode("utf-8"), payload)
        self.assertIn("小峰峰".encode("utf-8"), payload)
        self.assertNotIn(b"\\u660e", payload)
        self.assertNotIn(b"\\u5c0f", payload)
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json; charset=utf-8")


if __name__ == "__main__":
    unittest.main()
