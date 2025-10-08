from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from users.models import Member, PasswordResetToken
from tenants.models import Tenant


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    FRONTEND_URL='http://frontend.test'
)
class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Tenants
        self.tenant_a = Tenant.objects.create(name="Tenant A", code="ta", status="active")
        self.tenant_b = Tenant.objects.create(name="Tenant B", code="tb", status="active")

        # Members with same email across tenants (ambiguity)
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
            is_active=True,
            is_deleted=False,
        )
        self.sub_account.set_password("SubPass123!")
        self.sub_account.save()

        # URLs
        self.url_request = reverse("auth:password-reset-request")
        self.url_verify = reverse("auth:password-reset-verify")
        self.url_confirm = reverse("auth:password-reset-confirm")

    def test_member_request_with_header_creates_token(self):
        before = PasswordResetToken.objects.count()
        resp = self.client.post(
            self.url_request,
            {
                "email": "ma@example.com",
                "account_type": "member",
            },
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))
        after = PasswordResetToken.objects.count()
        self.assertEqual(after, before + 1)
        token = PasswordResetToken.objects.latest('created_at')
        self.assertIsNone(token.user)
        self.assertEqual(token.member_id, self.member_ta.id)
        self.assertFalse(token.is_used)

    def test_member_request_without_header_returns_4001(self):
        # account_type=member 但无 Header -> 4001
        before = PasswordResetToken.objects.count()
        resp = self.client.post(
            self.url_request,
            {
                "email": "member.same@example.com",
                "account_type": "member",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data.get("success"))
        self.assertEqual(resp.data.get("code"), 4001)
        after = PasswordResetToken.objects.count()
        self.assertEqual(after, before)

    def test_member_request_with_header_resolves_ambiguity_and_creates_token(self):
        before = PasswordResetToken.objects.count()
        resp = self.client.post(
            self.url_request,
            {
                "email": "member.same@example.com",
                "account_type": "member",
            },
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_b.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))
        after = PasswordResetToken.objects.count()
        self.assertEqual(after, before + 1)

    def test_sub_account_cannot_request_reset(self):
        before = PasswordResetToken.objects.count()
        resp = self.client.post(
            self.url_request,
            {
                "email": "sub@example.com",
                "account_type": "member",
            },
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))
        after = PasswordResetToken.objects.count()
        self.assertEqual(after, before)

    def test_user_request_with_header_forbidden_4001(self):
        # 管理员/超管请求阶段禁止携带 Header
        before = PasswordResetToken.objects.count()
        resp = self.client.post(
            self.url_request,
            {
                "email": "admin@example.com",
                "account_type": "user",
            },
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data.get("success"))
        self.assertEqual(resp.data.get("code"), 4001)
        after = PasswordResetToken.objects.count()
        self.assertEqual(after, before)

    def test_user_request_without_header_returns_200(self):
        before = PasswordResetToken.objects.count()
        resp = self.client.post(
            self.url_request,
            {
                "email": "admin@example.com",
                "account_type": "user",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))
        after = PasswordResetToken.objects.count()
        self.assertEqual(after, before)

    def test_unspecified_account_type_with_header_treated_as_member(self):
        before = PasswordResetToken.objects.count()
        resp = self.client.post(
            self.url_request,
            {
                "email": "ma@example.com",
            },
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))
        after = PasswordResetToken.objects.count()
        self.assertEqual(after, before + 1)

    def test_verify_invalid_token(self):
        resp = self.client.post(self.url_verify, {"token": "invalid"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data.get("success"))
        self.assertEqual(resp.data.get("message"), "无效的重置令牌")

    def test_verify_expired_token(self):
        expired = PasswordResetToken.objects.create(
            member=self.member_ta,
            token="expiredtoken",
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        resp = self.client.post(self.url_verify, {"token": expired.token}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data.get("success"))
        self.assertEqual(resp.data.get("message"), "重置令牌已过期")

    def test_confirm_invalid_token(self):
        resp = self.client.post(
            self.url_confirm,
            {
                "token": "invalid",
                "new_password": "NewStrong123!",
                "confirm_password": "NewStrong123!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data.get("success"))

    def test_confirm_expired_token(self):
        expired = PasswordResetToken.objects.create(
            member=self.member_ta,
            token="expired2",
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        resp = self.client.post(
            self.url_confirm,
            {
                "token": expired.token,
                "new_password": "NewStrong123!",
                "confirm_password": "NewStrong123!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data.get("success"))
        # serializer should include token error
        self.assertIn("token", resp.data.get("data", {}))

    def test_confirm_password_strength_enforced(self):
        # create valid token
        valid = PasswordResetToken.objects.create(
            member=self.member_ta,
            token="validweak",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        resp = self.client.post(
            self.url_confirm,
            {
                "token": valid.token,
                "new_password": "123",  # weak password
                "confirm_password": "123",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data.get("success"))
        # new_password field validation errors
        self.assertIn("new_password", resp.data.get("data", {}))

    def test_confirm_success_updates_password_and_marks_token_used(self):
        valid = PasswordResetToken.objects.create(
            member=self.member_ta,
            token="validsuccess",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        resp = self.client.post(
            self.url_confirm,
            {
                "token": valid.token,
                "new_password": "NewStrong123!",
                "confirm_password": "NewStrong123!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))
        # token should be marked used
        valid.refresh_from_db()
        self.assertTrue(valid.is_used)
        # password should be updated
        self.member_ta.refresh_from_db()
        self.assertTrue(self.member_ta.check_password("NewStrong123!"))
