#!/usr/bin/env python3
"""创建测试数据"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenants.models import Tenant
from users.models import Member
from django.contrib.auth.hashers import make_password

print("=" * 60)
print("创建测试数据")
print("=" * 60)

# 1. 确保有测试租户
tenant, created = Tenant.objects.get_or_create(
    code='test_tenant',
    defaults={
        'name': '测试租户',
        'is_active': True
    }
)
if created:
    print(f"\n✓ 创建测试租户: ID={tenant.id}, Code={tenant.code}")
else:
    print(f"\n✓ 测试租户已存在: ID={tenant.id}, Code={tenant.code}")

# 2. 创建或更新测试Member用户
test_member, created = Member.objects.get_or_create(
    username='test_member',
    defaults={
        'email': 'test_member@example.com',
        'tenant': tenant,
        'is_active': True,
        'password': make_password('Test123456')
    }
)

if not created:
    # 更新密码
    test_member.password = make_password('Test123456')
    test_member.is_active = True
    test_member.tenant = tenant
    test_member.save()
    print(f"✓ 更新测试Member用户: {test_member.username}")
else:
    print(f"✓ 创建测试Member用户: {test_member.username}")

print(f"\n" + "=" * 60)
print("测试数据创建完成！")
print("=" * 60)
print(f"\n测试用户信息:")
print(f"  用户名: test_member")
print(f"  密码: Test123456")
print(f"  租户ID: {tenant.id}")
print(f"  租户Code: {tenant.code}")
print(f"\n登录测试:")
print(f"  POST /api/v1/auth/login/")
print(f"  Headers: X-Tenant-ID: {tenant.id}")
print(f"  Body: {{'username': 'test_member', 'password': 'Test123456'}}")
