#!/usr/bin/env python
"""
创建测试租户和租户管理员
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenants.models import Tenant, TenantQuota
from users.models import User

# 检查测试租户是否已存在
test_tenant = Tenant.objects.filter(name='测试租户').first()

if not test_tenant:
    print('创建测试租户...')
    test_tenant = Tenant.objects.create(
        name='测试租户',
        status='active',
        contact_name='测试联系人',
        contact_email='test@example.com',
        contact_phone='13800138000'
    )
    print(f'测试租户创建成功！ID: {test_tenant.id}')
else:
    print(f'测试租户已存在！ID: {test_tenant.id}')

# 检查配额是否存在，如果不存在则创建
tenant_quota = TenantQuota.objects.filter(tenant=test_tenant).first()
if not tenant_quota:
    print('创建租户配额...')
    tenant_quota = TenantQuota.objects.create(
        tenant=test_tenant,
        max_users=20,
        max_admins=5,
        max_storage_mb=2048,
        max_products=100
    )
    print(f'租户配额创建成功！ID: {tenant_quota.id}')
else:
    print(f'租户配额已存在！ID: {tenant_quota.id}')

# 检查租户管理员是否已存在
tenant_admin = User.objects.filter(username='tenant_admin').first()

if not tenant_admin:
    print('创建租户管理员...')
    tenant_admin = User.objects.create_user(
        username='tenant_admin',
        email='tenant_admin@example.com',
        password='Admin@123',
        is_staff=True,  # 允许访问admin站点
        is_admin=True,  # 租户管理员
        tenant=test_tenant
    )
    print(f'租户管理员创建成功！ID: {tenant_admin.id}')
else:
    print(f'租户管理员已存在！ID: {tenant_admin.id}')
    # 确保管理员与租户关联
    if tenant_admin.tenant != test_tenant:
        tenant_admin.tenant = test_tenant
        tenant_admin.save()
        print('更新租户管理员关联的租户')

# 检查普通用户是否已存在
tenant_user = User.objects.filter(username='tenant_user').first()

if not tenant_user:
    print('创建租户普通用户...')
    tenant_user = User.objects.create_user(
        username='tenant_user',
        email='tenant_user@example.com',
        password='User@123',
        is_staff=True,  # 允许访问admin站点
        is_admin=False,  # 普通用户
        is_member=True,
        tenant=test_tenant
    )
    print(f'租户普通用户创建成功！ID: {tenant_user.id}')
else:
    print(f'租户普通用户已存在！ID: {tenant_user.id}')
    # 确保用户与租户关联
    if tenant_user.tenant != test_tenant:
        tenant_user.tenant = test_tenant
        tenant_user.save()
        print('更新租户普通用户关联的租户')

print('\n测试用户信息:')
print(f'1. 超级管理员 - 用户名: admin, 密码: 您设置的密码')
print(f'2. 租户管理员 - 用户名: tenant_admin, 密码: Admin@123')
print(f'3. 租户普通用户 - 用户名: tenant_user, 密码: User@123')
print('\n请使用这些账户登录admin界面测试租户隔离功能') 