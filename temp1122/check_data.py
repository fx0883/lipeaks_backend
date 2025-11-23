#!/usr/bin/env python
"""检查数据库中的租户和用户数据"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenants.models import Tenant
from users.models import Member
from applications.models import Application

print("=" * 60)
print("数据库数据检查")
print("=" * 60)

# 检查租户
tenant_count = Tenant.objects.count()
print(f"\n租户总数: {tenant_count}")
if tenant_count > 0:
    for tenant in Tenant.objects.all()[:5]:
        print(f"  - Tenant {tenant.id}: {tenant.name} (code: {tenant.code})")

# 检查用户
member_count = Member.objects.count()
print(f"\n用户总数: {member_count}")
if member_count > 0:
    for member in Member.objects.all()[:5]:
        print(f"  - User {member.id}: {member.username} (tenant: {member.tenant_id}, staff: {member.is_staff})")

# 检查应用
app_count = Application.objects.count()
print(f"\n应用总数: {app_count}")
if app_count > 0:
    for app in Application.objects.all()[:5]:
        print(f"  - App {app.id}: {app.name} (tenant: {app.tenant_id})")

print("\n" + "=" * 60)
