"""
测试租户名称显示功能
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenants.models import Tenant

def test_tenant_names():
    """
    测试租户名称显示
    """
    print("=== 测试租户名称显示 ===")
    
    # 获取所有租户
    tenants = Tenant.objects.filter(is_deleted=False).order_by('name')
    print(f"系统中的租户数量: {tenants.count()}")
    
    for tenant in tenants:
        print(f"租户ID: {tenant.id}")
        print(f"租户名称: '{tenant.name}'")
        print(f"名称长度: {len(tenant.name)} 字符")
        print(f"名称编码: {tenant.name.encode('utf-8')}")
        print(f"是否包含特殊字符: {any(ord(c) > 127 for c in tenant.name)}")
        print("-" * 40)
    
    # 检查是否有空名称
    empty_names = tenants.filter(name__isnull=True) | tenants.filter(name='')
    if empty_names.exists():
        print("⚠️  发现空名称的租户:")
        for tenant in empty_names:
            print(f"  - 租户ID: {tenant.id}, 名称: '{tenant.name}'")
    
    # 检查名称长度
    long_names = tenants.filter(name__length__gt=50)
    if long_names.exists():
        print("⚠️  发现名称过长的租户:")
        for tenant in long_names:
            print(f"  - 租户ID: {tenant.id}, 名称: '{tenant.name}' (长度: {len(tenant.name)})")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_tenant_names()
