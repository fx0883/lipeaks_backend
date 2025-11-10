#!/usr/bin/env python3
import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import Member
from cms.models import Article
from tenants.models import Tenant

print("=" * 60)
print("测试Member创建文章")
print("=" * 60)

try:
    # 获取测试Member
    member = Member.objects.get(username='test_member')
    tenant = member.tenant
    
    print(f"测试用户: {member.username}")
    print(f"用户类型: {type(member)}")
    print(f"租户: {tenant.name}")
    
    # 创建文章
    article = Article.objects.create(
        title="测试文章标题",
        content="这是测试文章内容",
        content_type="markdown",
        status="draft",
        author=member,
        tenant=tenant
    )
    
    print(f"\n✅ 文章创建成功!")
    print(f"   文章ID: {article.id}")
    print(f"   文章标题: {article.title}")
    print(f"   作者: {article.author}")
    print(f"   作者类型: {article.author_type}")
    print(f"   是否Member作者: {article.is_author_member}")
    
except Exception as e:
    print(f"\n❌ 创建失败: {e}")
    print("\n详细错误:")
    traceback.print_exc()
