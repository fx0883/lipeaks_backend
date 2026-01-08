"""
通知系统数据模型

包含两个核心模型：
- Notification: 通知主表，存储通知内容
- NotificationRecipient: 通知接收者映射表，记录通知与成员的多对多关系及阅读状态
"""
import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from common.models import BaseModel

logger = logging.getLogger(__name__)


class Notification(BaseModel):
    """
    通知模型
    
    支持三种通知范围：
    - tenant: 面向租户，发布时自动发送给租户下所有 Member
    - application: 面向应用，关联具体应用，发布时自动发送给租户下所有 Member
    - members: 面向特定成员，发布前手动选择接收者
    """
    
    # === 通知范围 ===
    SCOPE_CHOICES = [
        ('tenant', '面向租户'),
        ('application', '面向应用'),
        ('members', '面向特定成员'),
    ]
    scope = models.CharField(
        _("通知范围"),
        max_length=20,
        choices=SCOPE_CHOICES,
        default='tenant',
        db_index=True,
        help_text="tenant=租户下所有成员, application=关联应用, members=指定成员"
    )
    
    # === 关联应用 (scope=application 时必填) ===
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_("关联应用"),
        help_text="仅当 scope=application 时需要填写"
    )
    
    # === 通知内容 ===
    title = models.CharField(
        _("通知标题"),
        max_length=200
    )
    content = models.TextField(
        _("通知内容"),
        help_text="支持富文本/Markdown"
    )
    
    # === 通知类型 ===
    TYPE_CHOICES = [
        ('info', '信息通知'),
        ('warning', '警告通知'),
        ('error', '错误通知'),
        ('update', '更新通知'),
        ('announcement', '公告'),
    ]
    notification_type = models.CharField(
        _("通知类型"),
        max_length=20,
        choices=TYPE_CHOICES,
        default='info',
        db_index=True
    )
    
    # === 优先级 ===
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    priority = models.CharField(
        _("优先级"),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        db_index=True
    )
    
    # === 邮件发送 ===
    send_email = models.BooleanField(
        _("是否发送邮件"),
        default=False,
        help_text="发布时是否同时发送邮件通知"
    )
    email_sent_at = models.DateTimeField(
        _("邮件发送时间"),
        null=True,
        blank=True
    )
    
    # === 状态 ===
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]
    status = models.CharField(
        _("状态"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    published_at = models.DateTimeField(
        _("发布时间"),
        null=True,
        blank=True
    )
    
    # === 创建者 ===
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_notifications',
        verbose_name=_("创建者")
    )
    
    class Meta:
        db_table = 'notification'
        verbose_name = _('通知')
        verbose_name_plural = _('通知')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'scope']),
            models.Index(fields=['tenant', 'application']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_scope_display()})"
    
    def clean(self):
        """模型验证"""
        super().clean()
        
        # scope=application 时，application 必填
        if self.scope == 'application' and not self.application:
            raise ValidationError({
                'application': _('当通知范围为"面向应用"时，必须选择一个应用')
            })
        
        # scope 不是 application 时，application 必须为空
        if self.scope != 'application' and self.application:
            raise ValidationError({
                'application': _('当通知范围不是"面向应用"时，不能选择应用')
            })
    
    def save(self, *args, **kwargs):
        """保存前验证"""
        self.clean()
        super().save(*args, **kwargs)
    
    def get_recipient_count(self):
        """获取接收者数量"""
        return self.recipients.count()
    
    def get_read_count(self):
        """获取已读数量"""
        return self.recipients.filter(is_read=True).count()
    
    def get_unread_count(self):
        """获取未读数量"""
        return self.recipients.filter(is_read=False).count()


class NotificationRecipient(BaseModel):
    """
    通知接收者映射表
    
    记录通知与成员的多对多关系，同时存储阅读状态
    """
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='recipients',
        verbose_name=_("通知")
    )
    member = models.ForeignKey(
        'users.Member',
        on_delete=models.CASCADE,
        related_name='notification_recipients',
        verbose_name=_("成员")
    )
    is_read = models.BooleanField(
        _("是否已读"),
        default=False,
        db_index=True
    )
    read_at = models.DateTimeField(
        _("阅读时间"),
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'notification_recipient'
        verbose_name = _('通知接收者')
        verbose_name_plural = _('通知接收者')
        ordering = ['-created_at']
        unique_together = [['notification', 'member']]
        indexes = [
            models.Index(fields=['member', 'is_read']),
            models.Index(fields=['notification', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.notification.title} -> {self.member.username}"
    
    def mark_as_read(self):
        """标记为已读"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
            logger.info(f"通知 {self.notification_id} 已被成员 {self.member_id} 标记为已读")
