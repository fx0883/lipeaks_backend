"""
UserApplication 模型与 User.admin_type 单元测试
"""
from django.db import IntegrityError
from django.test import TestCase

from applications.models import Application, UserApplication
from tenants.models import Tenant
from users.models import User


class UserApplicationModelTests(TestCase):
    """验证 UserApplication 模型及 User 扩展方法"""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", code="test_tenant")
        quota = self.tenant.ensure_quota()
        quota.max_admins = 10
        quota.save()

        self.app1 = Application.objects.create(
            tenant=self.tenant, name="App 1", code="app_1"
        )
        self.app2 = Application.objects.create(
            tenant=self.tenant, name="App 2", code="app_2"
        )
        self.owner = User.objects.create(
            username="tenant_owner_user",
            email="owner@test.com",
            tenant=self.tenant,
            is_admin=True,
            admin_type="tenant_owner",
        )
        self.app_admin = User.objects.create(
            username="app_admin_user",
            email="app_admin@test.com",
            tenant=self.tenant,
            is_admin=True,
            admin_type="app_admin",
        )

    def test_default_admin_type_is_tenant_owner(self):
        """默认管理员创建时 admin_type 为 tenant_owner"""
        default_user = User.objects.create(
            username="default_user",
            email="default@test.com",
            tenant=self.tenant,
            is_admin=True,
        )
        self.assertEqual(default_user.admin_type, "tenant_owner")
        self.assertTrue(default_user.is_tenant_owner)
        self.assertFalse(default_user.is_app_admin)
        self.assertIsNone(default_user.get_managed_app_ids())

    def test_app_admin_flags(self):
        """验证应用管理员的标志与初始管辖应用为空列表"""
        self.assertFalse(self.app_admin.is_tenant_owner)
        self.assertTrue(self.app_admin.is_app_admin)
        self.assertEqual(self.app_admin.get_managed_app_ids(), [])

    def test_user_application_creation_and_scoping(self):
        """验证创建 UserApplication 绑定后，get_managed_app_ids 能正确返回对应应用 ID"""
        UserApplication.objects.create(
            tenant=self.tenant,
            user=self.app_admin,
            application=self.app1,
            role="admin",
        )
        UserApplication.objects.create(
            tenant=self.tenant,
            user=self.app_admin,
            application=self.app2,
            role="admin",
        )

        managed_ids = self.app_admin.get_managed_app_ids()
        self.assertIn(self.app1.id, managed_ids)
        self.assertIn(self.app2.id, managed_ids)
        self.assertEqual(len(managed_ids), 2)

    def test_user_application_unique_together(self):
        """验证同一个用户对同一应用不能重复创建绑定"""
        UserApplication.objects.create(
            tenant=self.tenant,
            user=self.app_admin,
            application=self.app1,
        )
        with self.assertRaises(IntegrityError):
            UserApplication.objects.create(
                tenant=self.tenant,
                user=self.app_admin,
                application=self.app1,
            )
