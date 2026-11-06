"""
应用管理员人员管理拦截与序列化器 TDD 测试
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from applications.models import Application, UserApplication
from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member, User
from users.serializers import UserCreateSerializer, UserSerializer


class AppAdminPersonnelRestrictionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Personnel Tenant", code="personnel_tenant")
        quota = self.tenant.ensure_quota()
        quota.max_admins = 20
        quota.save()

        self.app1 = Application.objects.create(tenant=self.tenant, name="App 1", code="app1")
        self.app2 = Application.objects.create(tenant=self.tenant, name="App 2", code="app2")

        # 租户主管理员
        self.owner = User.objects.create_user(
            username="owner_user",
            email="owner@test.com",
            password="Password123!",
            tenant=self.tenant,
            is_admin=True,
            admin_type="tenant_owner",
        )

        # 应用管理员
        self.app_admin = User.objects.create_user(
            username="app_admin_user",
            email="app_admin@test.com",
            password="Password123!",
            tenant=self.tenant,
            is_admin=True,
            admin_type="app_admin",
        )
        UserApplication.objects.create(
            tenant=self.tenant,
            user=self.app_admin,
            application=self.app1,
        )

        # 普通成员
        self.member = Member.objects.create(
            tenant=self.tenant,
            username="member1",
            email="member1@test.com",
        )

        self.owner_token = generate_jwt_token(self.owner)
        self.app_admin_token = generate_jwt_token(self.app_admin)

    def test_user_serializer_exposes_admin_type_and_managed_applications(self):
        """UserSerializer 应正确输出 admin_type 和 managed_applications"""
        serializer = UserSerializer(self.app_admin)
        data = serializer.data
        self.assertEqual(data["admin_type"], "app_admin")
        self.assertEqual(data["role"], "应用管理员")
        self.assertEqual(len(data["managed_applications"]), 1)
        self.assertEqual(data["managed_applications"][0]["id"], self.app1.id)
        self.assertEqual(data["managed_applications"][0]["code"], "app1")

    def test_user_create_serializer_with_application_ids(self):
        """主管理员通过 UserCreateSerializer 创建应用管理员并指定 application_ids"""
        payload = {
            "username": "new_app_admin",
            "email": "new_app@test.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "tenant_id": self.tenant.id,
            "is_admin": True,
            "admin_type": "app_admin",
            "application_ids": [self.app1.id, self.app2.id],
        }
        serializer = UserCreateSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        new_user = serializer.save()

        self.assertEqual(new_user.admin_type, "app_admin")
        self.assertTrue(new_user.is_app_admin)
        managed_ids = new_user.get_managed_app_ids()
        self.assertEqual(set(managed_ids), {self.app1.id, self.app2.id})

    def test_app_admin_forbidden_from_admin_user_list(self):
        """应用管理员调用管理员列表接口返回 403 Forbidden"""
        self.client.force_authenticate(user=self.app_admin)
        response = self.client.get("/api/v1/admin-users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_allowed_for_admin_user_list(self):
        """租户主管理员可以正常访问管理员列表接口"""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get("/api/v1/admin-users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_app_admin_forbidden_from_member_admin_list(self):
        """应用管理员调用成员管理列表接口返回 403 Forbidden"""
        self.client.force_authenticate(user=self.app_admin)
        response = self.client.get("/api/v1/admin/members/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
