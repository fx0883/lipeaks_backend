"""
Adversarial Security Test Suite for SEC-01 (Privilege Escalation & Registration Bypass)
Challenger 1 Empirical Verification Harness.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from tenants.models import Tenant, TenantQuota
from users.models import User, Member
from users.serializers import RegisterSerializer


class Sec01AdversarialChallengeTests(TestCase):
    """
    SEC-01 对抗攻击实证测试套件
    挑战目标：
    1. 模拟未认证用户调用注册接口，传入各类提权参数 (is_admin, is_staff, is_superuser, is_super_admin, is_tenant_admin, tenant_id, X-Tenant-ID)
    2. 验证注册后用户绝不能获得 is_admin=True, is_staff=True, is_tenant_admin=True，且不得绑定到租户
    3. 验证 ORM 创建用户与显式设置 is_admin=False 时，User.save() 绝不强行提权
    """

    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="VictimCorp", code="victimcorp", status="active")
        self.quota = self.tenant.ensure_quota()

    def test_01_standard_registration_defaults_to_non_admin(self):
        """标准注册：创建的用户必须是非管理员 (is_admin=False, is_staff=False, is_tenant_admin=False, tenant=None)"""
        data = {
            "username": "attacker_normal",
            "email": "normal@adversary.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
        }
        self.client.post("/api/v1/auth/register/", data, format="json")
        
        user = User.objects.get(username="attacker_normal")
        self.assertFalse(user.is_admin, "user.is_admin MUST be False")
        self.assertFalse(user.is_staff, "user.is_staff MUST be False")
        self.assertFalse(user.is_superuser, "user.is_superuser MUST be False")
        self.assertFalse(user.is_super_admin, "user.is_super_admin MUST be False")
        self.assertFalse(user.is_tenant_admin, "user.is_tenant_admin MUST be False")
        self.assertIsNone(user.tenant, "user.tenant MUST be None")

    def test_02_inject_is_admin_true_in_body(self):
        """对抗注入：攻击者在注册 Payload 中注入 is_admin=True"""
        data = {
            "username": "attacker_admin_flag",
            "email": "adminflag@adversary.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "is_admin": True,
        }
        self.client.post("/api/v1/auth/register/", data, format="json")

        user = User.objects.get(username="attacker_admin_flag")
        self.assertFalse(user.is_admin, "is_admin injection MUST be rejected/stripped")
        self.assertFalse(user.is_staff, "user.is_staff MUST remain False")
        self.assertFalse(user.is_tenant_admin, "user.is_tenant_admin MUST remain False")

    def test_03_inject_is_staff_true_in_body(self):
        """对抗注入：攻击者在注册 Payload 中注入 is_staff=True"""
        data = {
            "username": "attacker_staff_flag",
            "email": "staffflag@adversary.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "is_staff": True,
        }
        self.client.post("/api/v1/auth/register/", data, format="json")

        user = User.objects.get(username="attacker_staff_flag")
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff, "is_staff injection MUST be rejected/stripped")
        self.assertFalse(user.is_tenant_admin)

    def test_04_inject_is_superuser_and_super_admin_in_body(self):
        """对抗注入：攻击者在注册 Payload 中注入 is_superuser=True, is_super_admin=True"""
        data = {
            "username": "attacker_super_flags",
            "email": "superflags@adversary.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "is_superuser": True,
            "is_super_admin": True,
        }
        self.client.post("/api/v1/auth/register/", data, format="json")

        user = User.objects.get(username="attacker_super_flags")
        self.assertFalse(user.is_superuser, "is_superuser MUST remain False")
        self.assertFalse(user.is_super_admin, "is_super_admin MUST remain False")
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff)

    def test_05_inject_is_tenant_admin_in_body(self):
        """对抗注入：攻击者在注册 Payload 中注入 is_tenant_admin=True"""
        data = {
            "username": "attacker_tenant_admin_prop",
            "email": "tenantadminprop@adversary.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "is_tenant_admin": True,
        }
        self.client.post("/api/v1/auth/register/", data, format="json")

        user = User.objects.get(username="attacker_tenant_admin_prop")
        self.assertFalse(user.is_tenant_admin, "is_tenant_admin MUST remain False")
        self.assertFalse(user.is_admin)

    def test_06_inject_tenant_id_in_body(self):
        """对抗注入：攻击者在注册 Payload 中试图绑定目标租户 tenant_id"""
        data = {
            "username": "attacker_tenant_bound",
            "email": "tenantbound@adversary.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "tenant_id": self.tenant.id,
        }
        self.client.post("/api/v1/auth/register/", data, format="json")

        user = User.objects.get(username="attacker_tenant_bound")
        self.assertIsNone(user.tenant, "tenant_id injection in body MUST be dropped")
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_tenant_admin)

    def test_07_inject_tenant_header_forbidden(self):
        """对抗注入：攻击者在注册接口携带 X-Tenant-ID Header 试图建立租户绑定"""
        data = {
            "username": "attacker_header_tenant",
            "email": "headertenant@adversary.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
        }
        # 携带 X-Tenant-ID 请求头
        response = self.client.post(
            "/api/v1/auth/register/",
            data,
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant.id)
        )
        # 应被 RegisterSerializer.validate 拦截（报 400 / 4001）
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="attacker_header_tenant").exists())

    def test_08_orm_user_save_preserves_is_admin_false(self):
        """ORM对抗：通过 User.objects.create(is_admin=False) 创建用户，save() 绝不强行提权"""
        user = User.objects.create(
            username="orm_user_low",
            email="low@test.com",
            is_admin=False
        )
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_tenant_admin)
        self.assertEqual(user.display_role, "普通用户")

        # 再次触发 save()
        user.first_name = "Alice"
        user.save()
        user.refresh_from_db()
        self.assertFalse(user.is_admin, "user.save() MUST NOT override is_admin to True")
        self.assertFalse(user.is_staff, "user.save() MUST NOT override is_staff to True")
        self.assertFalse(user.is_tenant_admin)

    def test_09_orm_user_with_tenant_and_is_admin_false(self):
        """ORM对抗：用户绑定租户但 is_admin=False 时，save() 绝不视为租户管理员"""
        user = User.objects.create(
            username="orm_tenant_low",
            email="tenant_low@test.com",
            tenant=self.tenant,
            is_admin=False
        )
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_tenant_admin, "Non-admin tenant user MUST NOT be tenant admin")
        self.assertEqual(user.display_role, "普通用户")

    def test_10_member_model_is_staff_strictly_false(self):
        """Member 模型防御：任何 Member 实例 is_staff 强制为 False"""
        member = Member.objects.create(
            username="test_member_safe",
            email="member@test.com",
            tenant=self.tenant,
            is_staff=True  # 尝试强设
        )
        self.assertFalse(member.is_staff, "Member.save() MUST enforce is_staff=False")

    def test_11_register_serializer_direct_strips_all_privileges(self):
        """序列化器直接攻击：向 RegisterSerializer 传入包含所有提权字段的字典"""
        malicious_input = {
            "username": "serializer_hacker",
            "email": "hacker@evil.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "is_admin": True,
            "is_staff": True,
            "is_superuser": True,
            "is_super_admin": True,
            "is_tenant_admin": True,
            "tenant_id": self.tenant.id,
        }
        serializer = RegisterSerializer(data=malicious_input)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # 验证 validated_data 中不存在提权字段与 tenant_id
        self.assertNotIn("tenant_id", serializer.validated_data)
        self.assertNotIn("is_admin", serializer.validated_data)
        self.assertNotIn("is_staff", serializer.validated_data)

        user = serializer.save()
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_super_admin)
        self.assertFalse(user.is_tenant_admin)
        self.assertIsNone(user.tenant)

    def test_12_orm_create_user_with_is_admin_false_and_tenant(self):
        """ORM对抗：通过 User.objects.create_user 指定 is_admin=False 和 tenant"""
        user = User.objects.create_user(
            username="orm_cu_user",
            email="cu@evil.com",
            password="Password123!",
            tenant=self.tenant,
            is_admin=False
        )
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_tenant_admin)

        # 多次更新与保存
        user.nick_name = "Nickname"
        user.save()
        user.refresh_from_db()
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_tenant_admin)
