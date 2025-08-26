from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from users.models import Member
from tenants.models import Tenant


class MemberSelfUpdateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create tenant and member
        self.tenant = Tenant.objects.create(name="Tenant X", code="tx", status="active")
        self.member = Member.objects.create(
            username="self_user",
            email="self@example.com",
            tenant=self.tenant,
            is_active=True,
            is_deleted=False,
            nick_name="Old Nick",
            phone="13800000000",
        )
        self.member.set_password("SelfPass123!")
        self.member.save()
        # Authenticate as this member
        self.client.force_authenticate(user=self.member)
        self.url = "/api/v1/members/me/"

    def test_update_nick_name_and_phone_success(self):
        payload = {"nick_name": "New Nick", "phone": "13900000000"}
        resp = self.client.put(self.url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))
        data = resp.data.get("data", {})
        self.assertEqual(data.get("nick_name"), "New Nick")
        self.assertEqual(data.get("phone"), "13900000000")

    def test_cannot_update_username(self):
        resp = self.client.put(self.url, {"username": "newuser"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # Detail message comes from CurrentMemberView protection
        self.assertEqual(resp.data.get("detail"), "不允许修改 username 字段")

    def test_cannot_update_email(self):
        resp = self.client.put(self.url, {"email": "new@example.com"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("detail"), "不允许修改 email 字段")
