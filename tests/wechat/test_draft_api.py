import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Member


class WechatDraftServiceTests(TestCase):
    def tearDown(self):
        cache.clear()
        super().tearDown()

    def _write_config(self, directory, accounts):
        config_path = Path(directory) / "wechat_config.json"
        config_path.write_text(
            json.dumps({"account": accounts}, ensure_ascii=False),
            encoding="utf-8",
        )
        return config_path

    def test_load_wechat_accounts_reads_configured_accounts(self):
        from wechat.services import wechat as wechat_service

        with TemporaryDirectory() as temp_dir:
            config_path = self._write_config(
                temp_dir,
                [
                    {
                        "name": "公众号A",
                        "author": "default-author",
                        "WECHAT_APPID": "wx123",
                        "WECHAT_SECRET": "secret123",
                    },
                    {
                        "name": "公众号B",
                        "WECHAT_APPID": "wx456",
                        "WECHAT_SECRET": "secret456",
                    },
                ],
            )

            with override_settings(WECHAT_CONFIG_PATH=str(config_path)):
                accounts = wechat_service.load_wechat_accounts()

        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0]["name"], "公众号A")
        self.assertEqual(accounts[0]["author"], "default-author")
        self.assertEqual(accounts[0]["WECHAT_APPID"], "wx123")
        self.assertEqual(accounts[1]["WECHAT_SECRET"], "secret456")

    @patch("wechat.services.wechat.requests.get")
    def test_get_access_token_uses_cache_per_appid(self, mock_get):
        from wechat.services import wechat as wechat_service

        cache.clear()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "token-123",
            "expires_in": 7200,
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        first_token = wechat_service.get_access_token("wx123", "secret123")
        second_token = wechat_service.get_access_token("wx123", "secret123")

        self.assertEqual(first_token, "token-123")
        self.assertEqual(second_token, "token-123")
        mock_get.assert_called_once()

    def test_upload_permanent_image_file_rejects_unsupported_extension(self):
        from wechat.services import wechat as wechat_service

        uploaded_file = SimpleUploadedFile(
            "invalid.gif",
            b"gif-bytes",
            content_type="image/gif",
        )

        with self.assertRaises(wechat_service.WechatValidationError) as context:
            wechat_service.upload_permanent_image_file("token-123", uploaded_file)

        self.assertIn(".jpg", str(context.exception))
        self.assertIn(".png", str(context.exception))

    def test_upload_article_image_file_rejects_unsupported_extension(self):
        from wechat.services import wechat as wechat_service

        uploaded_file = SimpleUploadedFile(
            "invalid.gif",
            b"gif-bytes",
            content_type="image/gif",
        )

        with self.assertRaises(wechat_service.WechatValidationError) as context:
            wechat_service.upload_article_image_file("token-123", uploaded_file)

        self.assertIn(".jpg", str(context.exception))
        self.assertIn(".png", str(context.exception))


class WechatDraftApiTests(APITestCase):
    def setUp(self):
        self.member = Member.objects.create(
            username="wechat-draft-member",
            email="wechat-draft@example.com",
        )
        self.client.force_authenticate(user=self.member)
        self.accounts_url = "/api/v1/wechat/accounts/"
        self.uploadimg_url = "/api/v1/wechat/media/uploadimg/"
        self.add_material_url = "/api/v1/wechat/material/add-material/"
        self.draft_add_url = "/api/v1/wechat/draft/add/"

    @patch("wechat.views.upload_article_image_file")
    @patch("wechat.views.get_access_token")
    @patch("wechat.views.get_wechat_account_by_appid")
    def test_uploadimg_returns_image_url(
        self,
        mock_get_account,
        mock_get_token,
        mock_upload_article_image,
    ):
        mock_get_account.return_value = {
            "name": "公众号A",
            "WECHAT_APPID": "wx123",
            "WECHAT_SECRET": "secret123",
        }
        mock_get_token.return_value = "token-123"
        mock_upload_article_image.return_value = "https://mmbiz.qpic.cn/image-one"

        image_file = SimpleUploadedFile("inline-1.png", b"fake-png", content_type="image/png")

        response = self.client.post(
            self.uploadimg_url,
            {
                "account_appid": "wx123",
                "media": image_file,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["account_appid"], "wx123")
        self.assertEqual(response.data["data"]["account_name"], "公众号A")
        self.assertEqual(response.data["data"]["url"], "https://mmbiz.qpic.cn/image-one")

    def test_uploadimg_requires_media(self):
        response = self.client.post(
            self.uploadimg_url,
            {
                "account_appid": "wx123",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("media", response.data["data"])

    @patch("wechat.views.add_permanent_material_file")
    @patch("wechat.views.get_access_token")
    @patch("wechat.views.get_wechat_account_by_appid")
    def test_add_material_returns_media_id_and_url(
        self,
        mock_get_account,
        mock_get_token,
        mock_add_permanent_material_file,
    ):
        mock_get_account.return_value = {
            "name": "公众号A",
            "WECHAT_APPID": "wx123",
            "WECHAT_SECRET": "secret123",
        }
        mock_get_token.return_value = "token-123"
        mock_add_permanent_material_file.return_value = {
            "media_id": "image-media-1",
            "url": "https://mmbiz.qpic.cn/material-image",
        }

        image_file = SimpleUploadedFile("cover.png", b"fake-png", content_type="image/png")

        response = self.client.post(
            self.add_material_url,
            {
                "account_appid": "wx123",
                "type": "image",
                "media": image_file,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["type"], "image")
        self.assertEqual(response.data["data"]["media_id"], "image-media-1")
        self.assertEqual(
            response.data["data"]["url"],
            "https://mmbiz.qpic.cn/material-image",
        )

    def test_add_material_rejects_unsupported_type(self):
        image_file = SimpleUploadedFile("cover.png", b"fake-png", content_type="image/png")

        response = self.client.post(
            self.add_material_url,
            {
                "account_appid": "wx123",
                "type": "video",
                "media": image_file,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("type", response.data["data"])

    @patch("wechat.views.add_draft")
    @patch("wechat.views.get_access_token")
    @patch("wechat.views.get_wechat_account_by_appid")
    def test_draft_add_returns_draft_media_id(
        self,
        mock_get_account,
        mock_get_token,
        mock_add_draft,
    ):
        mock_get_account.return_value = {
            "name": "公众号A",
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
                        "title": "文章标题",
                        "author": "作者甲",
                        "digest": "文章摘要",
                        "content": "<p>正文内容</p>",
                        "content_source_url": "https://example.com/source-article",
                        "thumb_media_id": "thumb-media-id",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["draft_media_id"], "draft-news-123")
        create_args, _ = mock_add_draft.call_args
        self.assertEqual(create_args[1][0]["title"], "文章标题")
        self.assertEqual(create_args[1][0]["thumb_media_id"], "thumb-media-id")

    def test_draft_add_requires_articles(self):
        response = self.client.post(
            self.draft_add_url,
            {
                "account_appid": "wx123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("articles", response.data["data"])

    def test_old_convenience_endpoints_are_removed(self):
        old_paths = [
            "/api/v1/wechat/draft/newspic/",
            "/api/v1/wechat/draft/newspic-upload/",
            "/api/v1/wechat/draft/news/",
            "/api/v1/wechat/draft/news-upload/",
        ]

        for path in old_paths:
            response = self.client.post(path, {}, format="json")
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, msg=path)


class WechatDraftSchemaTests(TestCase):
    def _resolve_schema(self, schema, schema_or_ref):
        if "$ref" not in schema_or_ref:
            return schema_or_ref

        ref = schema_or_ref["$ref"]
        prefix = "#/components/schemas/"
        self.assertTrue(ref.startswith(prefix), msg=ref)
        return schema["components"]["schemas"][ref.removeprefix(prefix)]

    def test_schema_includes_only_new_wechat_draft_endpoints(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        self.assertIn("/api/v1/wechat/accounts/", schema["paths"])
        self.assertIn("/api/v1/wechat/media/uploadimg/", schema["paths"])
        self.assertIn("/api/v1/wechat/material/add-material/", schema["paths"])
        self.assertIn("/api/v1/wechat/draft/add/", schema["paths"])

        self.assertNotIn("/api/v1/wechat/draft/newspic/", schema["paths"])
        self.assertNotIn("/api/v1/wechat/draft/newspic-upload/", schema["paths"])
        self.assertNotIn("/api/v1/wechat/draft/news/", schema["paths"])
        self.assertNotIn("/api/v1/wechat/draft/news-upload/", schema["paths"])

        uploadimg_operation = schema["paths"]["/api/v1/wechat/media/uploadimg/"]["post"]
        add_material_operation = schema["paths"]["/api/v1/wechat/material/add-material/"]["post"]
        draft_add_operation = schema["paths"]["/api/v1/wechat/draft/add/"]["post"]

        self.assertTrue(uploadimg_operation["summary"])
        self.assertTrue(add_material_operation["summary"])
        self.assertTrue(draft_add_operation["summary"])

        uploadimg_request_schema = self._resolve_schema(
            schema,
            uploadimg_operation["requestBody"]["content"]["multipart/form-data"]["schema"],
        )
        self.assertIn("account_appid", uploadimg_request_schema["properties"])
        self.assertIn("media", uploadimg_request_schema["properties"])

        add_material_request_schema = self._resolve_schema(
            schema,
            add_material_operation["requestBody"]["content"]["multipart/form-data"]["schema"],
        )
        self.assertIn("account_appid", add_material_request_schema["properties"])
        self.assertIn("type", add_material_request_schema["properties"])
        self.assertIn("media", add_material_request_schema["properties"])

        draft_add_request_schema = self._resolve_schema(
            schema,
            draft_add_operation["requestBody"]["content"]["application/json"]["schema"],
        )
        self.assertIn("account_appid", draft_add_request_schema["properties"])
        self.assertIn("articles", draft_add_request_schema["properties"])
