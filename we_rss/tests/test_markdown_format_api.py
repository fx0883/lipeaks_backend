from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member


class MarkdownFormatApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
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

    def test_rejects_blank_content(self):
        response = self.client.post(
            reverse("we-rss:markdown-format"),
            {"content": "   ", "mode": "gentle"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content", response.data["data"])

    def test_rejects_unsupported_mode(self):
        response = self.client.post(
            reverse("we-rss:markdown-format"),
            {"content": "# Title", "mode": "rewrite"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mode", response.data["data"])

    @patch("we_rss.views.markdown_views.MarkdownFormatService.format_content")
    def test_formats_markdown_text(self, format_mock):
        format_mock.return_value = {
            "formatted_markdown": "# Title\n\nBody",
            "mode": "gentle",
            "executor": "codex",
        }

        response = self.client.post(
            reverse("we-rss:markdown-format"),
            {"content": "# Title\nBody", "mode": "gentle"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["formatted_markdown"], "# Title\n\nBody")
        self.assertEqual(response.data["data"]["mode"], "gentle")
        self.assertEqual(response.data["data"]["executor"], "codex")

    @patch("we_rss.views.markdown_views.MarkdownFormatService.format_content")
    def test_returns_server_error_when_gateway_fails(self, format_mock):
        format_mock.side_effect = RuntimeError("executor failed")

        response = self.client.post(
            reverse("we-rss:markdown-format"),
            {"content": "# Title\nBody", "mode": "gentle"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
