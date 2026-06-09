import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Member


class WechatDraftAuthorDefaultsTests(APITestCase):
    def setUp(self):
        self.member = Member.objects.create(
            username="wechat-draft-author-member",
            email="wechat-draft-author@example.com",
        )
        self.client.force_authenticate(user=self.member)
        self.accounts_url = "/api/v1/wechat/accounts/"
        self.draft_add_url = "/api/v1/wechat/draft/add/"

    def _write_config(self, directory, accounts):
        config_path = Path(directory) / "wechat_config.json"
        config_path.write_text(
            json.dumps({"account": accounts}, ensure_ascii=False),
            encoding="utf-8",
        )
        return config_path

    def test_accounts_endpoint_returns_author_field(self):
        with TemporaryDirectory() as temp_dir:
            config_path = self._write_config(
                temp_dir,
                [
                    {
                        "name": "Public Account A",
                        "author": "default-author",
                        "WECHAT_APPID": "wx123",
                        "WECHAT_SECRET": "secret123",
                    }
                ],
            )

            with override_settings(WECHAT_CONFIG_PATH=str(config_path)):
                response = self.client.get(self.accounts_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["data"],
            [{"name": "Public Account A", "author": "default-author", "appid": "wx123"}],
        )

    @patch("wechat.views.add_draft")
    @patch("wechat.views.get_access_token")
    @patch("wechat.views.get_wechat_account_by_appid")
    def test_draft_add_defaults_author_from_account_config_for_news_articles(
        self,
        mock_get_account,
        mock_get_token,
        mock_add_draft,
    ):
        mock_get_account.return_value = {
            "name": "Public Account A",
            "author": "default-author",
            "WECHAT_APPID": "wx123",
            "WECHAT_SECRET": "secret123",
        }
        mock_get_token.return_value = "token-123"
        mock_add_draft.return_value = {"media_id": "draft-news-123"}

        response = self.client.post(
            self.draft_add_url,
            {
                "account_appid": "wx123",
                "articles": [
                    {
                        "article_type": "news",
                        "title": "News title",
                        "content": "<p>content</p>",
                        "thumb_media_id": "thumb-media-id",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        create_args, _ = mock_add_draft.call_args
        self.assertEqual(create_args[1][0]["author"], "default-author")


class WechatDraftAuthorSchemaTests(SimpleTestCase):
    def _resolve_schema(self, schema, schema_or_ref):
        if "$ref" not in schema_or_ref:
            return schema_or_ref

        ref = schema_or_ref["$ref"]
        prefix = "#/components/schemas/"
        return schema["components"]["schemas"][ref.removeprefix(prefix)]

    def test_accounts_schema_exposes_author_field(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        accounts_operation = schema["paths"]["/api/v1/wechat/accounts/"]["get"]
        accounts_response_schema = self._resolve_schema(
            schema,
            accounts_operation["responses"]["200"]["content"]["application/json"]["schema"],
        )
        account_item_schema = self._resolve_schema(
            schema,
            accounts_response_schema["properties"]["data"]["items"],
        )

        self.assertIn("author", account_item_schema["properties"])
