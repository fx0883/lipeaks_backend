"""
测试CMS租户过滤器功能
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from tenants.models import Tenant
from cms.models import Category, Article

User = get_user_model()

def test_tenant_filter():
    """
    测试租户过滤器功能
    """
    print("=== 测试CMS租户过滤器功能 ===")
    
    # 获取所有租户
    tenants = Tenant.objects.filter(is_deleted=False)
    print(f"系统中的租户数量: {tenants.count()}")
    
    for tenant in tenants:
        print(f"租户: {tenant.name} (ID: {tenant.id})")
        
        # 获取该租户的分类数量
        categories = Category.objects.filter(tenant=tenant)
        print(f"  - 分类数量: {categories.count()}")
        
        # 获取该租户的文章数量
        articles = Article.objects.filter(tenant=tenant)
        print(f"  - 文章数量: {articles.count()}")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_tenant_filter()
