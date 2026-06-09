from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member


class WeRssAuthScopeTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.other_tenant = Tenant.objects.create(name="Tenant B", code="tenant_b")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )
        self.token = generate_jwt_token(self.member)["access_token"]

    def test_we_rss_requires_x_tenant_id_header(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        response = self.client.get("/api/v1/we-rss/tags/")

        self.assertEqual(response.status_code, 400)

    def test_we_rss_rejects_mismatched_tenant_header(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
            HTTP_X_TENANT_ID=str(self.other_tenant.id),
        )

        response = self.client.get("/api/v1/we-rss/tags/")

        self.assertEqual(response.status_code, 403)

