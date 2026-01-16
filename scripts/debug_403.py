#!/usr/bin/env python3
"""
调试脚本：验证文章797和Member用户的权限问题
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from cms.models import Article, Comment
from users.models import Member
from django.contrib.auth import get_user_model

AdminUser = get_user_model()

def check_article():
    """检查文章797的详细信息"""
    print("=" * 80)
    print("检查文章 797")
    print("=" * 80)
    
    try:
        article = Article.objects.get(id=797)
        print(f"✅ 文章存在")
        print(f"  - ID: {article.id}")
        print(f"  - 标题: {article.title}")
        print(f"  - 租户ID: {article.tenant_id}")
        print(f"  - 租户: {article.tenant}")
        print(f"  - 允许评论: {article.allow_comment}")
        print(f"  - 状态: {article.status}")
        
        # 用租户过滤
        article_with_tenant = Article.objects.filter(id=797, tenant_id=3).first()
        if article_with_tenant:
            print(f"✅ 文章797属于租户3")
        else:
            print(f"❌ 文章797不属于租户3")
            
    except Article.DoesNotExist:
        print("❌ 文章797不存在")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    print()

def check_member():
    """检查Member用户"""
    print("=" * 80)
    print("检查 Member 用户 test_member_001")
    print("=" * 80)
    
    try:
        member = Member.objects.get(username='test_member_001')
        print(f"✅ Member用户存在")
        print(f"  - ID: {member.id}")
        print(f"  - 用户名: {member.username}")
        print(f"  - 是否认证: {member.is_authenticated}")
        print(f"  - 有tenant属性: {hasattr(member, 'tenant')}")
        
        if hasattr(member, 'tenant'):
            print(f"  - tenant值: {member.tenant}")
            print(f"  - tenant类型: {type(member.tenant)}")
            if member.tenant:
                print(f"  - tenant ID: {member.tenant.id}")
            else:
                print(f"  - tenant为None")
        
        # 检查Member模型的类型
        print(f"  - Member类型: {type(member)}")
        print(f"  - Member.__class__: {member.__class__}")
        print(f"  - isinstance(member, Member): {isinstance(member, Member)}")
        
    except Member.DoesNotExist:
        print("❌ Member用户不存在")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    print()

def check_permission_logic():
    """模拟权限检查逻辑"""
    print("=" * 80)
    print("模拟权限检查逻辑")
    print("=" * 80)
    
    try:
        member = Member.objects.get(username='test_member_001')
        article = Article.objects.get(id=797)
        
        # 模拟请求数据
        tenant_id = 3
        article_id = 797
        
        print(f"模拟请求:")
        print(f"  - tenant_id: {tenant_id}")
        print(f"  - article_id: {article_id}")
        print(f"  - 用户: {member.username}")
        print()
        
        # 检查1: 用户是否认证
        if not member.is_authenticated:
            print("❌ 检查1失败: 用户未认证")
            return
        print("✅ 检查1通过: 用户已认证")
        
        # 检查2: Member用户是否有租户绑定
        if isinstance(member, Member):
            if not hasattr(member, 'tenant') or not member.tenant:
                print("❌ 检查2失败: Member用户未关联租户")
                return
        print("✅ 检查2通过: Member用户有租户绑定")
        
        # 检查3: 文章是否存在于指定租户
        try:
            article_check = Article.objects.get(id=article_id, tenant_id=tenant_id)
            print(f"✅ 检查3通过: 文章{article_id}存在于租户{tenant_id}")
        except Article.DoesNotExist:
            print(f"❌ 检查3失败: 文章{article_id}不存在于租户{tenant_id}")
            return
        
        # 检查4: 文章是否允许评论
        if not article_check.allow_comment:
            print("❌ 检查4失败: 文章不允许评论")
            return
        print("✅ 检查4通过: 文章允许评论")
        
        print()
        print("🎉 所有权限检查都应该通过！")
        
    except Exception as e:
        print(f"❌ 模拟失败: {e}")
        import traceback
        traceback.print_exc()
    print()

def check_parent_permission():
    """检查父类权限"""
    print("=" * 80)
    print("检查父类 CMSBasePermission")
    print("=" * 80)
    
    # 读取 permissions.py 文件
    perm_file = '/Users/fengxuan/Documents/Github/lipeaks_backend/cms/permissions.py'
    try:
        with open(perm_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查 CommentPermission 类定义
        if 'class CommentPermission' in content:
            # 找到类定义行
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'class CommentPermission' in line:
                    print(f"Line {i+1}: {line}")
                    # 检查继承
                    if 'CMSBasePermission' in line:
                        print("✅ CommentPermission 继承自 CMSBasePermission")
                    break
        
        # 检查 has_permission 方法的返回语句
        if 'return super().has_permission(request, view)' in content:
            print("✅ 找到 super().has_permission() 调用")
            print("   这意味着会调用父类 CMSBasePermission.has_permission()")
            
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
    print()

if __name__ == '__main__':
    check_article()
    check_member()
    check_permission_logic()
    check_parent_permission()
