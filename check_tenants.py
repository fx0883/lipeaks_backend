#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenants.models import Tenant
from users.models import Member

print("=" * 60)
print("系统租户和用户信息")
print("=" * 60)

# 获取租户信息
tenants = Tenant.objects.all()[:5]
print("\n租户列表:")
for tenant in tenants:
    print(f"  ID={tenant.id}, Code={tenant.code}, Name={tenant.name}")

# 获取Member用户
members = Member.objects.all()[:5]
print("\nMember用户列表:")
for member in members:
    print(f"  ID={member.id}, Username={member.username}, Tenant={member.tenant_id}")

# 检查是否有测试用户
test_members = Member.objects.filter(username__icontains='test')[:3]
if test_members:
    print("\n测试用户:")
    for member in test_members:
        print(f"  Username={member.username}, Password=(需要重置), Tenant={member.tenant_id}")
else:
    print("\n⚠ 没有找到测试用户")
    print("建议创建测试用户用于API测试")
