"""
Tenants 模型单元测试
覆盖 Tenant 与 TenantQuota 的核心方法、条件唯一约束、软删除与配额边界
"""
from django.db import IntegrityError, transaction
from django.test import TestCase

from tenants.models import Tenant, TenantQuota
from users.models import User


class TenantModelTests(TestCase):
    """Tenant 与 TenantQuota 模型单元测试"""

    def test_tenant_save_auto_code(self):
        """验证保存新租户时若未传 code，自动将 name 转为小写加下划线"""
        tenant = Tenant.objects.create(name="My Super Tenant")
        self.assertEqual(tenant.code, "my_super_tenant")

        # 显式传入 code 时应保持不变
        custom_tenant = Tenant.objects.create(name="Another Tenant", code="custom_code_01")
        self.assertEqual(custom_tenant.code, "custom_code_01")

    def test_tenant_save_auto_quota(self):
        """验证新建租户自动创建关联的默认 TenantQuota 记录"""
        tenant = Tenant.objects.create(name="Quota Auto Tenant")
        self.assertTrue(TenantQuota.objects.filter(tenant=tenant).exists())
        quota = tenant.quota
        self.assertEqual(quota.max_users, 10)
        self.assertEqual(quota.max_admins, 2)
        self.assertEqual(quota.max_storage_mb, 1024)
        self.assertEqual(quota.max_products, 100)
        self.assertEqual(quota.current_storage_used_mb, 0)

    def test_tenant_soft_delete_and_is_active(self):
        """验证 soft_delete 方法将状态置为 deleted、is_deleted 置为 True，且 is_active 为 False"""
        tenant = Tenant.objects.create(name="Soft Delete Tenant")
        self.assertTrue(tenant.is_active)

        tenant.soft_delete()
        tenant.refresh_from_db()
        self.assertEqual(tenant.status, "deleted")
        self.assertTrue(tenant.is_deleted)
        self.assertFalse(tenant.is_active)

    def test_tenant_conditional_unique_name(self):
        """验证未删除状态下同名租户触发 IntegrityError，软删除后允许创建同名活跃租户"""
        tenant1 = Tenant.objects.create(name="Alpha Corp", code="alpha_1")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Tenant.objects.create(name="Alpha Corp", code="alpha_2")

        # 软删除后允许同名创建
        tenant1.soft_delete()
        tenant2 = Tenant.objects.create(name="Alpha Corp", code="alpha_2")
        self.assertIsNotNone(tenant2.pk)
        self.assertNotEqual(tenant1.pk, tenant2.pk)
        self.assertFalse(tenant2.is_deleted)

    def test_tenant_conditional_unique_code(self):
        """验证未删除状态下同 code 租户触发 IntegrityError，软删除后允许创建同 code 活跃租户"""
        tenant1 = Tenant.objects.create(name="Beta One", code="shared_code")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Tenant.objects.create(name="Beta Two", code="shared_code")

        # 软删除后允许同 code 创建
        tenant1.soft_delete()
        tenant2 = Tenant.objects.create(name="Beta Two", code="shared_code")
        self.assertIsNotNone(tenant2.pk)
        self.assertEqual(tenant2.code, "shared_code")

    def test_tenant_ensure_quota_self_healing(self):
        """验证当租户配额记录意外缺失时，ensure_quota 能够自动重建默认配额"""
        tenant = Tenant.objects.create(name="Self Heal Tenant")
        TenantQuota.objects.filter(tenant=tenant).delete()

        # 清除缓存的反向一对一关联后调用 ensure_quota
        tenant = Tenant.objects.get(pk=tenant.pk)
        healed_quota = tenant.ensure_quota()
        self.assertIsNotNone(healed_quota.pk)
        self.assertEqual(healed_quota.max_users, 10)
        self.assertEqual(healed_quota.max_admins, 2)

    def test_quota_can_add_user_limit(self):
        """验证超出 max_users 时 can_add_user(is_admin=False) 返回 False"""
        tenant = Tenant.objects.create(name="User Limit Tenant")
        quota = tenant.quota
        quota.max_users = 2
        quota.max_admins = 2
        quota.save()

        self.assertTrue(quota.can_add_user(is_admin=False))
        User.objects.create(username="u1", email="u1@test.com", tenant=tenant, is_admin=False)
        self.assertTrue(quota.can_add_user(is_admin=False))
        User.objects.create(username="u2", email="u2@test.com", tenant=tenant, is_admin=False)

        # 达到上限 2
        self.assertFalse(quota.can_add_user(is_admin=False))

    def test_quota_can_add_admin_limit(self):
        """验证超出 max_admins 时 can_add_user(is_admin=True) 返回 False"""
        tenant = Tenant.objects.create(name="Admin Limit Tenant")
        quota = tenant.quota
        quota.max_users = 10
        quota.max_admins = 1
        quota.save()

        self.assertTrue(quota.can_add_user(is_admin=True))
        User.objects.create(username="adm1", email="adm1@test.com", tenant=tenant, is_admin=True)

        # 管理员已达上限 1，但普通用户仍可添加
        self.assertFalse(quota.can_add_user(is_admin=True))
        self.assertTrue(quota.can_add_user(is_admin=False))

    def test_quota_storage_usage_and_check(self):
        """验证 update_storage_usage 与 can_use_storage 的容量边界计算"""
        tenant = Tenant.objects.create(name="Storage Tenant")
        quota = tenant.quota  # 默认 max_storage_mb = 1024

        self.assertTrue(quota.can_use_storage(500))
        quota.update_storage_usage(800)
        quota.refresh_from_db()
        self.assertEqual(quota.current_storage_used_mb, 800)

        # 剩余 224MB
        self.assertTrue(quota.can_use_storage(224))
        self.assertFalse(quota.can_use_storage(225))

    def test_quota_usage_percentage_and_zero_division(self):
        """验证 get_usage_percentage 计算准确度及 max=0 时的零除保护"""
        tenant = Tenant.objects.create(name="Percentage Tenant")
        quota = tenant.quota
        quota.max_users = 4
        quota.max_admins = 2
        quota.max_storage_mb = 1000
        quota.current_storage_used_mb = 250
        quota.save()

        User.objects.create(username="p_adm", email="padm@test.com", tenant=tenant, is_admin=True)
        self.assertEqual(quota.get_usage_percentage("users"), 25.0)
        self.assertEqual(quota.get_usage_percentage("admins"), 50.0)
        self.assertEqual(quota.get_usage_percentage("storage"), 25.0)
        self.assertEqual(quota.get_usage_percentage("products"), 0.0)
        self.assertEqual(quota.get_usage_percentage("invalid_type"), 0)

        # 零除保护：当最大配额设为 0 时安全返回 0
        quota.max_users = 0
        quota.max_admins = 0
        quota.max_storage_mb = 0
        quota.max_products = 0
        quota.save()

        self.assertEqual(quota.get_usage_percentage("users"), 0)
        self.assertEqual(quota.get_usage_percentage("admins"), 0)
        self.assertEqual(quota.get_usage_percentage("storage"), 0)
        self.assertEqual(quota.get_usage_percentage("products"), 0)
