"""
DEFECT-ARCH-01 回归测试
验证多租户 Member 用户名跨租户同名隔离与租户内唯一性约束
"""
from django.test import TestCase
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from tenants.models import Tenant
from users.models import Member
from users.serializers import SubAccountCreateSerializer


class MemberTenantUniquenessTests(TestCase):
    """测试多租户 Member 唯一性与子账号创建序列化器隔离"""

    def setUp(self):
        self.tenant_a = Tenant.objects.create(name="Tenant Alpha", code="alpha", status="active")
        self.tenant_b = Tenant.objects.create(name="Tenant Beta", code="beta", status="active")
        self.factory = APIRequestFactory()

    def test_cross_tenant_same_username_allowed(self):
        """不同租户允许创建相同 username 的 Member"""
        member_a = Member.objects.create_user(
            username="same_user",
            email="user_a@example.com",
            password="Password123!",
            tenant=self.tenant_a
        )
        self.assertIsNotNone(member_a.pk)

        # 租户 B 创建相同 username
        member_b = Member.objects.create_user(
            username="same_user",
            email="user_b@example.com",
            password="Password123!",
            tenant=self.tenant_b
        )
        self.assertIsNotNone(member_b.pk)
        self.assertEqual(member_a.username, member_b.username)
        self.assertNotEqual(member_a.tenant, member_b.tenant)

    def test_same_tenant_same_username_rejected(self):
        """同一租户不允许创建相同 username 的 Member (触发唯一约束)"""
        Member.objects.create_user(
            username="unique_user",
            email="user1@example.com",
            password="Password123!",
            tenant=self.tenant_a
        )

        with self.assertRaises(IntegrityError):
            Member.objects.create_user(
                username="unique_user",
                email="user2@example.com",
                password="Password123!",
                tenant=self.tenant_a
            )

    def test_sub_account_serializer_tenant_scoped_validation(self):
        """子账号序列化器校验限定在当前租户内"""
        # 父账号在租户 A
        parent_a = Member.objects.create_user(
            username="parent_a",
            email="parent_a@example.com",
            password="Password123!",
            tenant=self.tenant_a
        )
        # 租户 B 下已有一个 sub_test 账号
        Member.objects.create_user(
            username="sub_test",
            email="sub_b@example.com",
            password="Password123!",
            tenant=self.tenant_b
        )

        # 租户 A 的父账号尝试在租户 A 创建同名 sub_test 子账号，应当被允许通过序列化校验
        request = self.factory.post("/api/v1/users/sub-accounts/")
        request.user = parent_a

        serializer = SubAccountCreateSerializer(
            data={"username": "sub_test", "email": "sub_a@example.com"},
            context={"request": request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        sub_a = serializer.save()
        self.assertEqual(sub_a.tenant, self.tenant_a)
        self.assertEqual(sub_a.parent, parent_a)

        # 再次在租户 A 创建相同的 sub_test，应被序列化器拒绝
        serializer_dup = SubAccountCreateSerializer(
            data={"username": "sub_test", "email": "sub_a2@example.com"},
            context={"request": request}
        )
        self.assertFalse(serializer_dup.is_valid())
        self.assertIn("username", serializer_dup.errors)
