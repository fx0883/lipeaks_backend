"""
用户相关信号处理器

实现 Member 软删除时的级联处理：
- 当 Member 被软删除时，自动处理所有关联数据
"""
import logging
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='users.Member')
def cascade_soft_delete_on_member(sender, instance, **kwargs):
    """
    Member 软删除时级联处理关联数据
    
    处理策略：
    - WechatUser: 硬删除（允许微信用户重新注册）
    - 子账号 Member: 级联软删除
    - 其他模型: 软删除（设置 is_deleted=True）
    """
    # 只在软删除时触发（is_deleted 从 False 变为 True）
    if not instance.is_deleted:
        return
    
    # 检查是否是新创建的已删除状态（不太可能，但为了安全）
    if kwargs.get('created', False):
        return
    
    member_id = instance.id
    member_username = instance.username
    
    logger.info(f"开始级联软删除 Member {member_username} (ID: {member_id}) 的关联数据")
    
    # 1. WechatUser - 硬删除（允许微信用户重新绑定其他账号）
    try:
        from wechat.models import WechatUser
        deleted_count = WechatUser.objects.filter(member_id=member_id).delete()[0]
        if deleted_count:
            logger.info(f"硬删除 {deleted_count} 条 WechatUser 记录")
    except Exception as e:
        logger.error(f"删除 WechatUser 失败: {e}")
    
    # 2. 子账号 - 级联软删除
    try:
        from users.models import Member
        sub_accounts = Member.objects.filter(parent_id=member_id, is_deleted=False)
        for sub_account in sub_accounts:
            sub_account.soft_delete()
            logger.info(f"级联软删除子账号: {sub_account.username}")
    except Exception as e:
        logger.error(f"软删除子账号失败: {e}")
    
    # 3. CheckinCycle（打卡周期）
    try:
        from check_system.models import CheckinCycle
        updated = CheckinCycle.objects.filter(
            member_id=member_id, 
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 CheckinCycle 记录")
    except Exception as e:
        logger.error(f"软删除 CheckinCycle 失败: {e}")
    
    # 4. Task（任务）
    try:
        from check_system.models import Task
        updated = Task.objects.filter(
            member_id=member_id,
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 Task 记录")
    except Exception as e:
        logger.error(f"软删除 Task 失败: {e}")
    
    # 5. CheckRecord（打卡记录）
    try:
        from check_system.models import CheckRecord
        updated = CheckRecord.objects.filter(
            member_id=member_id,
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 CheckRecord 记录")
    except Exception as e:
        logger.error(f"软删除 CheckRecord 失败: {e}")
    
    # 6. Article（文章）- 作者是该 Member
    try:
        from cms.models import Article
        updated = Article.objects.filter(
            member_id=member_id,
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 Article 记录")
    except Exception as e:
        logger.error(f"软删除 Article 失败: {e}")
    
    # 7. NotificationRecipient（通知接收者）
    try:
        from notifications.models import NotificationRecipient
        updated = NotificationRecipient.objects.filter(
            member_id=member_id,
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 NotificationRecipient 记录")
    except Exception as e:
        logger.error(f"软删除 NotificationRecipient 失败: {e}")
    
    # 8. MemberLike（用户点赞）- 发起者或被点赞者
    try:
        from interactions.models import MemberLike
        updated = MemberLike.objects.filter(
            is_deleted=False
        ).filter(
            models.Q(from_member_id=member_id) | models.Q(to_member_id=member_id)
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 MemberLike 记录")
    except Exception as e:
        logger.error(f"软删除 MemberLike 失败: {e}")
    
    # 9. MemberFollow（用户关注）- 关注者或被关注者
    try:
        from interactions.models import MemberFollow
        updated = MemberFollow.objects.filter(
            is_deleted=False
        ).filter(
            models.Q(follower_id=member_id) | models.Q(following_id=member_id)
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 MemberFollow 记录")
    except Exception as e:
        logger.error(f"软删除 MemberFollow 失败: {e}")
    
    # 10. ArticleLike（文章点赞）
    try:
        from interactions.models import ArticleLike
        updated = ArticleLike.objects.filter(
            from_member_id=member_id,
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 ArticleLike 记录")
    except Exception as e:
        logger.error(f"软删除 ArticleLike 失败: {e}")
    
    # 11. CustomerMemberRelation（客户联系人关系）
    try:
        from customers.models import CustomerMemberRelation
        updated = CustomerMemberRelation.objects.filter(
            member_id=member_id,
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 CustomerMemberRelation 记录")
    except Exception as e:
        logger.error(f"软删除 CustomerMemberRelation 失败: {e}")
    
    # 12. LicenseAssignment（许可证分配）
    try:
        from licenses.models import LicenseAssignment
        updated = LicenseAssignment.objects.filter(
            member_id=member_id,
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 LicenseAssignment 记录")
    except Exception as e:
        logger.error(f"软删除 LicenseAssignment 失败: {e}")
    
    # 13. TenantUserProfile / TenantUserPoints / TenantUserTypeTag（积分系统）
    try:
        from points.models import TenantUserProfile, TenantUserPoints, TenantUserTypeTag
        
        updated = TenantUserProfile.objects.filter(
            member_id=member_id,
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 TenantUserProfile 记录")
        
        updated = TenantUserPoints.objects.filter(
            member_id=member_id,
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 TenantUserPoints 记录")
        
        updated = TenantUserTypeTag.objects.filter(
            member_id=member_id,
            is_deleted=False
        ).update(is_deleted=True)
        if updated:
            logger.info(f"软删除 {updated} 条 TenantUserTypeTag 记录")
    except Exception as e:
        logger.error(f"软删除 Points 相关记录失败: {e}")
    
    logger.info(f"完成 Member {member_username} (ID: {member_id}) 的级联软删除")
