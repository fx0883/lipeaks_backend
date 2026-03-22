from django.test import SimpleTestCase
from django.urls import resolve
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member


class WeRssUrlRegistrationTest(SimpleTestCase):
    def test_we_rss_urls_are_registered(self):
        match = resolve("/api/v1/we-rss/credentials/")
        self.assertEqual(match.namespace, "we-rss")

    def test_we_rss_json_endpoints_resolve_to_viewsets(self):
        credential_match = resolve("/api/v1/we-rss/credentials/")
        feed_match = resolve("/api/v1/we-rss/feeds/")
        article_match = resolve("/api/v1/we-rss/articles/")

        self.assertEqual(credential_match.func.cls.__name__, "CredentialViewSet")
        self.assertEqual(feed_match.func.cls.__name__, "FeedViewSet")
        self.assertEqual(article_match.func.cls.__name__, "ArticleViewSet")


class WeRssPermissionTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )
        self.member_without_tenant = Member.objects.create(
            username="orphan_member",
            email="orphan-member@example.com",
        )
        self.member_token = generate_jwt_token(self.member)["access_token"]
        self.member_without_tenant_token = generate_jwt_token(self.member_without_tenant)["access_token"]

    def test_rejects_unauthenticated_request(self):
        response = self.client.get("/api/v1/we-rss/credentials/")
        self.assertEqual(response.status_code, 400)

    def test_rejects_member_without_tenant(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.member_without_tenant_token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        response = self.client.get("/api/v1/we-rss/credentials/")
        self.assertEqual(response.status_code, 403)

    def test_rejects_member_request_without_x_tenant_id_header(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.member_token}")

        response = self.client.get("/api/v1/we-rss/credentials/")

        self.assertEqual(response.status_code, 400)

    def test_rejects_member_request_with_mismatched_x_tenant_id_header(self):
        other_tenant = Tenant.objects.create(name="Tenant B", code="tenant_b")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.member_token}",
            HTTP_X_TENANT_ID=str(other_tenant.id),
        )

        response = self.client.get("/api/v1/we-rss/credentials/")

        self.assertEqual(response.status_code, 403)
