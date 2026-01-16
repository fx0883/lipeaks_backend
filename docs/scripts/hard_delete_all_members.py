#!/usr/bin/env python
"""
Member 数据硬删除脚本

功能说明：
1. 彻底删除所有 Member 用户及其关联数据（硬删除）
2. 强制清理所有软删除的数据（is_deleted=True）
3. 解决因软删除数据导致的级联删除约束冲突问题

特别注意：
- 此脚本会绕过 TenantManager 的软删除过滤，直接操作数据库底层数据
- 能够清理常规 Django admin 或 shell 无法看到的软删除残留数据

使用方法：
    # 交互式执行（需要确认）
    python docs/scripts/hard_delete_all_members.py

    # 强制执行（无需确认，适合脚本调用）
    python docs/scripts/hard_delete_all_members.py --force

警告：
此操作不可逆！数据一旦删除无法恢复！
仅建议在开发/测试环境重置数据时使用。
"""

import logging
import os
import sys
import argparse
import django

# 设置 Django 环境
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import transaction, connection

logger = logging.getLogger(__name__)


def confirm_execution(force=False):
    """确认执行"""
    if force:
        print("⚠️  强制执行模式：跳过确认")
        return True

    print("\n" + "=" * 60)
    print("⚠️  警告：此脚本将永久删除所有 Member 用户及其关联数据！")
    print("=" * 60)
    print("\n此操作不可逆，请确保已备份数据库！\n")
    
    confirmation = input("请输入 'DELETE ALL MEMBERS' 确认执行：")
    if confirmation != "DELETE ALL MEMBERS":
        print("操作已取消。")
        return False
    return True


def get_manager(model_class):
    """获取全量数据管理器（绕过软删除过滤）"""
    if hasattr(model_class, 'original_objects'):
        return model_class.original_objects
    return model_class.objects


def hard_delete_wechat_users():
    """删除所有微信用户绑定"""
    try:
        from wechat.models import WechatUser
        manager = get_manager(WechatUser)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            print(f"✅ 删除 {count} 条 WechatUser 记录")
        return count
    except Exception as e:
        print(f"❌ 删除 WechatUser 失败: {e}")
        return 0


def hard_delete_check_system():
    """删除打卡系统相关数据"""
    deleted = {}
    try:
        from check_system.models import CheckRecord, Task, CheckinCycle
        
        # 先删除 CheckRecord（依赖 Task）
        manager = get_manager(CheckRecord)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['CheckRecord'] = count
            print(f"✅ 删除 {count} 条 CheckRecord 记录")
        
        # 删除 Task（依赖 CheckinCycle）
        manager = get_manager(Task)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['Task'] = count
            print(f"✅ 删除 {count} 条 Task 记录")
        
        # 删除 CheckinCycle
        manager = get_manager(CheckinCycle)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['CheckinCycle'] = count
            print(f"✅ 删除 {count} 条 CheckinCycle 记录")
            
    except Exception as e:
        print(f"❌ 删除 check_system 数据失败: {e}")
    
    return deleted


def hard_delete_cms_data():
    """删除 CMS 相关数据（仅 Member 创建的）"""
    deleted = {}
    try:
        from cms.models import Article, Comment, OperationLog
        
        # 删除 Member 的文章评论（包括软删除的）
        manager = get_manager(Comment)
        count = manager.filter(member__isnull=False).count()
        if count > 0:
            manager.filter(member__isnull=False).delete()
            deleted['Comment'] = count
            print(f"✅ 删除 {count} 条 Comment 记录（Member创建）")
        
        # 删除 Member 的操作日志
        manager = get_manager(OperationLog)
        count = manager.filter(member__isnull=False).count()
        if count > 0:
            manager.filter(member__isnull=False).delete()
            deleted['OperationLog'] = count
            print(f"✅ 删除 {count} 条 OperationLog 记录（Member创建）")
        
        # 删除 Member 的文章
        manager = get_manager(Article)
        count = manager.filter(member__isnull=False).count()
        if count > 0:
            manager.filter(member__isnull=False).delete()
            deleted['Article'] = count
            print(f"✅ 删除 {count} 条 Article 记录（Member创建）")
            
    except Exception as e:
        print(f"❌ 删除 cms 数据失败: {e}")
    
    return deleted


def hard_delete_interactions():
    """删除互动数据"""
    deleted = {}
    try:
        from interactions.models import MemberLike, MemberFollow, ArticleLike
        
        manager = get_manager(ArticleLike)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['ArticleLike'] = count
            print(f"✅ 删除 {count} 条 ArticleLike 记录")
        
        manager = get_manager(MemberLike)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['MemberLike'] = count
            print(f"✅ 删除 {count} 条 MemberLike 记录")
        
        manager = get_manager(MemberFollow)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['MemberFollow'] = count
            print(f"✅ 删除 {count} 条 MemberFollow 记录")
            
    except Exception as e:
        print(f"❌ 删除 interactions 数据失败: {e}")
    
    return deleted


def hard_delete_notifications():
    """删除通知数据"""
    deleted = {}
    try:
        from notifications.models import NotificationRecipient
        
        manager = get_manager(NotificationRecipient)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['NotificationRecipient'] = count
            print(f"✅ 删除 {count} 条 NotificationRecipient 记录")
            
    except Exception as e:
        print(f"❌ 删除 notifications 数据失败: {e}")
    
    return deleted


def hard_delete_licenses():
    """删除许可证分配数据"""
    deleted = {}
    try:
        from licenses.models import LicenseAssignment
        
        manager = get_manager(LicenseAssignment)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['LicenseAssignment'] = count
            print(f"✅ 删除 {count} 条 LicenseAssignment 记录")
            
    except Exception as e:
        print(f"❌ 删除 licenses 数据失败: {e}")
    
    return deleted


def hard_delete_customers():
    """删除客户联系人关系"""
    deleted = {}
    try:
        from customers.models import CustomerMemberRelation
        
        manager = get_manager(CustomerMemberRelation)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['CustomerMemberRelation'] = count
            print(f"✅ 删除 {count} 条 CustomerMemberRelation 记录")
            
    except Exception as e:
        print(f"❌ 删除 customers 数据失败: {e}")
    
    return deleted


def hard_delete_points():
    """删除积分系统数据"""
    deleted = {}
    try:
        from points.models import TenantUserProfile, TenantUserPoints, TenantUserTypeTag
        
        manager = get_manager(TenantUserTypeTag)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['TenantUserTypeTag'] = count
            print(f"✅ 删除 {count} 条 TenantUserTypeTag 记录")
        
        manager = get_manager(TenantUserPoints)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['TenantUserPoints'] = count
            print(f"✅ 删除 {count} 条 TenantUserPoints 记录")
        
        manager = get_manager(TenantUserProfile)
        count = manager.all().count()
        if count > 0:
            manager.all().delete()
            deleted['TenantUserProfile'] = count
            print(f"✅ 删除 {count} 条 TenantUserProfile 记录")
            
    except Exception as e:
        print(f"❌ 删除 points 数据失败: {e}")
    
    return deleted


def hard_delete_password_reset_tokens():
    """删除密码重置令牌"""
    deleted = {}
    try:
        from users.models import PasswordResetToken
        
        manager = get_manager(PasswordResetToken)
        count = manager.filter(member__isnull=False).count()
        if count > 0:
            manager.filter(member__isnull=False).delete()
            deleted['PasswordResetToken'] = count
            print(f"✅ 删除 {count} 条 PasswordResetToken 记录")
            
    except Exception as e:
        print(f"❌ 删除 PasswordResetToken 失败: {e}")
    
    return deleted


def hard_delete_all_members():
    """删除所有 Member 用户"""
    try:
        from users.models import Member
        
        # 使用 original_objects 获取包括软删除的所有 Member
        manager = get_manager(Member)
        count = manager.all().count()
        
        if count > 0:
            # 尝试直接删除所有 Member
            # 注意：由于 Article 等模型可能有 SET_NULL 约束，如果前面的 clean 失败，这里可能会报错
            manager.all().delete()
            print(f"✅ 删除 {count} 条 Member 记录")
        else:
             print("ℹ️  没有发现 Member 记录")
        return count
    except Exception as e:
        print(f"❌ 删除 Member 失败: {e}")
        # 如果是约束错误，尝试打印更多信息
        if 'constraint' in str(e).lower():
             print("💡 提示：存在数据一致性约束错误，可能是因为某些关联数据（如评论）没有被彻底清理。")
        return 0


def clean_soft_deleted_data():
    """清理所有软删除的数据"""
    print("\n" + "=" * 60)
    print("清理软删除的数据 (is_deleted=True)")
    print("=" * 60)
    
    # 这里我们只清理剩余的可能漏网的软删除数据
    # 因为前面的 hard_delete_xxx 应该已经处理了所有关联数据
    
    models_to_clean = [
        ('check_system.CheckRecord', 'check_system.models', 'CheckRecord'),
        ('check_system.Task', 'check_system.models', 'Task'),
        ('check_system.CheckinCycle', 'check_system.models', 'CheckinCycle'),
        ('check_system.TaskCategory', 'check_system.models', 'TaskCategory'),
        ('cms.Article', 'cms.models', 'Article'),
        ('cms.Category', 'cms.models', 'Category'),
        ('notifications.NotificationRecipient', 'notifications.models', 'NotificationRecipient'),
        ('customers.Customer', 'customers.models', 'Customer'),
        ('customers.CustomerMemberRelation', 'customers.models', 'CustomerMemberRelation'),
        ('tenants.Tenant', 'tenants.models', 'Tenant'),
        ('users.Member', 'users.models', 'Member'),
        ('users.User', 'users.models', 'User'),
    ]
    
    total_deleted = 0
    
    for label, module_path, class_name in models_to_clean:
        try:
            module = __import__(module_path, fromlist=[class_name])
            model_class = getattr(module, class_name)
            
            manager = get_manager(model_class)
            
            if hasattr(model_class, 'is_deleted'):
                count = manager.filter(is_deleted=True).count()
                if count > 0:
                    manager.filter(is_deleted=True).delete()
                    print(f"✅ 清理 {count} 条软删除的 {label} 记录")
                    total_deleted += count
        except Exception as e:
            print(f"⚠️  清理 {label} 时出错: {e}")
    
    print(f"\n共清理 {total_deleted} 条软删除记录")
    return total_deleted


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='硬删除所有 Member 用户及其关联数据')
    parser.add_argument('--force', action='store_true', help='强制执行，跳过确认')
    args = parser.parse_args()

    # 确认执行
    if not confirm_execution(force=args.force):
        return
    
    print("\n" + "=" * 60)
    print("开始硬删除所有 Member 及关联数据...")
    print("=" * 60 + "\n")
    
    # 按依赖顺序删除（先删除依赖其他表的数据）
    
    print("【1/10】删除微信用户绑定...")
    hard_delete_wechat_users()
    
    print("\n【2/10】删除打卡系统数据...")
    hard_delete_check_system()
    
    print("\n【3/10】删除 CMS 数据...")
    hard_delete_cms_data()
    
    print("\n【4/10】删除互动数据...")
    hard_delete_interactions()
    
    print("\n【5/10】删除通知数据...")
    hard_delete_notifications()
    
    print("\n【6/10】删除许可证分配...")
    hard_delete_licenses()
    
    print("\n【7/10】删除客户联系人关系...")
    hard_delete_customers()
    
    print("\n【8/10】删除积分系统数据...")
    hard_delete_points()
    
    print("\n【9/10】删除密码重置令牌...")
    hard_delete_password_reset_tokens()
    
    print("\n【10/10】删除所有 Member 用户...")
    hard_delete_all_members()
    
    # 清理软删除的数据
    clean_soft_deleted_data()
    
    print("\n" + "=" * 60)
    print("✅ 所有 Member 及关联数据已删除完成！")
    print("=" * 60 + "\n")


# 执行主函数
if __name__ == "__main__":
    main()
