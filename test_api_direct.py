#!/usr/bin/env python3
import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory
from users.models import Member
from cms.member_article_views import MemberArticleViewSet
from rest_framework.test import force_authenticate

print("=" * 60)
print("直接测试MemberArticleViewSet.create")
print("=" * 60)

try:
    # 获取测试用户
    member = Member.objects.get(username='test_member')
    print(f"测试用户: {member.username}")
    print(f"租户: {member.tenant.name}")
    
    # 创建请求
    factory = RequestFactory()
    request = factory.post('/api/v1/cms/member/articles/', {
        'title': '测试文章',
        'content': '测试内容',
        'content_type': 'markdown',
        'status': 'draft'
    }, content_type='application/json')
    
    # 认证
    force_authenticate(request, user=member)
    
    # 调用ViewSet
    view = MemberArticleViewSet.as_view({'post': 'create'})
    response = view(request)
    
    print(f"\n状态码: {response.status_code}")
    print(f"响应: {response.data}")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    print("\n详细堆栈:")
    traceback.print_exc()
