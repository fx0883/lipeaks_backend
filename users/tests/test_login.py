from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User, Member
from tenants.models import Tenant


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Tenants
        self.tenant_a = Tenant.objects.create(name="Tenant A", code="ta", status="active")
        self.tenant_b = Tenant.objects.create(name="Tenant B", code="tb", status="active")
        self.suspended_tenant = Tenant.objects.create(name="Suspended", code="ts", status="suspended")

        # Admin (no tenant, super admin-like)
        self.admin = User.objects.create(
            username="admin_user",
            email="admin@example.com",
            is_admin=True,
            is_super_admin=True,
            is_active=True,
            is_deleted=False,
        )
        self.admin.set_password("AdminPass123!")
        self.admin.save()

        # Tenant admin (should still not require tenant to login)
        self.tenant_admin = User.objects.create(
            username="tenant_admin",
            email="tadmin@example.com",
            is_admin=True,
            is_super_admin=False,
            is_active=True,
            is_deleted=False,
            tenant=self.tenant_a,
        )
        self.tenant_admin.set_password("AdminPass123!")
        self.tenant_admin.save()

        # Members in different tenants with same email/username for ambiguity
        self.member_a = Member.objects.create(
            username="member_same",
            email="member.same@example.com",
            tenant=self.tenant_a,
            is_active=True,
            is_deleted=False,
        )
        self.member_a.set_password("MemberPass123!")
        self.member_a.save()

        self.member_b = Member.objects.create(
            username="member_same",
            email="member.same@example.com",
            tenant=self.tenant_b,
            is_active=True,
            is_deleted=False,
        )
        self.member_b.set_password("MemberPass123!")
        self.member_b.save()

        # A normal member in tenant A for positive tests
        self.member_ta = Member.objects.create(
            username="m_a",
            email="ma@example.com",
            tenant=self.tenant_a,
            is_active=True,
            is_deleted=False,
        )
        self.member_ta.set_password("GoodPass123!")
        self.member_ta.save()

        # Sub-account under member_ta
        self.sub_account = Member.objects.create(
            username="sub_m",
            email="sub@example.com",
            tenant=self.tenant_a,
            parent=self.member_ta,
            is_active=True,  # even if active, login should be forbidden
            is_deleted=False,
        )
        self.sub_account.set_password("SubPass123!")
        self.sub_account.save()

        # Member under suspended tenant
        self.member_suspended = Member.objects.create(
            username="s_member",
            email="s@example.com",
            tenant=self.suspended_tenant,
            is_active=True,
            is_deleted=False,
        )
        self.member_suspended.set_password("Suspended123!")
        self.member_suspended.save()

        self.url = reverse("auth:login")  # resolves to /api/v1/auth/login/

    def test_admin_login_by_username(self):
        resp = self.client.post(self.url, {"username": "admin_user", "password": "AdminPass123!"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))
        self.assertIn("token", resp.data.get("data", {}))

    def test_admin_login_by_email(self):
        resp = self.client.post(self.url, {"username": "admin@example.com", "password": "AdminPass123!"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))

    def test_member_login_with_tenant_id_in_body(self):
        # 改为仅使用 Header；body 中的 tenant_id 不再支持
        resp = self.client.post(
            self.url,
            {"username": "ma@example.com", "password": "GoodPass123!"},
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))

    def test_member_login_with_x_tenant_id_header(self):
        resp = self.client.post(
            self.url,
            {"username": "ma@example.com", "password": "GoodPass123!"},
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))

    def test_ambiguity_requires_tenant_header(self):
        # 成员登录无 Header 一律 4001（成员必须使用 Header）
        resp = self.client.post(
            self.url,
            {"username": "member.same@example.com", "password": "MemberPass123!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data.get("success"))
        self.assertEqual(resp.data.get("code"), 4001)

    def test_sub_account_cannot_login(self):
        resp = self.client.post(
            self.url,
            {"username": "sub@example.com", "password": "SubPass123!"},
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(resp.data.get("success"))
        self.assertEqual(resp.data.get("message"), "子账号不允许登录")

    def test_member_tenant_status_enforced(self):
        # suspended tenant member should not login
        resp = self.client.post(
            self.url,
            {"username": "s@example.com", "password": "Suspended123!"},
            format="json",
            HTTP_X_TENANT_ID=str(self.suspended_tenant.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(resp.data.get("success"))
        self.assertEqual(resp.data.get("message"), "所属租户已被禁用或暂停")

    def test_admin_login_with_header_forbidden(self):
        # 管理员/超管携带 Header 登录 -> 4001
        resp = self.client.post(
            self.url,
            {"username": "admin_user", "password": "AdminPass123!"},
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data.get("success"))
        self.assertEqual(resp.data.get("code"), 4001)

    def test_member_login_without_header_forbidden(self):
        # 成员无 Header 登录 -> 4001
        resp = self.client.post(
            self.url,
            {"username": "ma@example.com", "password": "GoodPass123!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data.get("success"))
        self.assertEqual(resp.data.get("code"), 4001)
