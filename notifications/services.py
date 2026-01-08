"""
通知系统服务层
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

logger = logging.getLogger(__name__)

# 线程池用于异步发送邮件
_email_executor = ThreadPoolExecutor(max_workers=3)


def send_notification_email(notification_id: int):
    """
    发送通知邮件
    
    根据配置决定使用 Celery 还是线程池异步发送
    """
    celery_enabled = getattr(settings, 'CELERY_ENABLED', False)
    
    if celery_enabled:
        # 使用 Celery 异步任务
        from .tasks import send_notification_email_task
        send_notification_email_task.delay(notification_id)
    else:
        # 使用线程池异步发送
        _email_executor.submit(_send_notification_email_sync, notification_id)


def _send_notification_email_sync(notification_id: int):
    """
    同步发送通知邮件（内部使用）
    """
    from .models import Notification, NotificationRecipient
    
    try:
        notification = Notification.objects.select_related('tenant').get(
            id=notification_id,
            is_deleted=False
        )
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return
    
    # 获取所有接收者的邮箱
    recipients = NotificationRecipient.objects.filter(
        notification=notification,
        is_deleted=False
    ).select_related('member').values_list('member__email', flat=True)
    
    valid_emails = [email for email in recipients if email]
    
    if not valid_emails:
        logger.info(f"Notification {notification_id} has no valid recipient emails")
        return
    
    # 准备邮件内容
    subject = f"[{notification.get_notification_type_display()}] {notification.title}"
    
    # 尝试使用模板，如果没有则使用简单格式
    try:
        html_message = render_to_string('notifications/email/notification.html', {
            'notification': notification,
            'tenant': notification.tenant,
        })
        plain_message = strip_tags(html_message)
    except Exception:
        # 模板不存在，使用简单格式
        plain_message = f"""
{notification.title}

{notification.content}

---
此邮件由系统自动发送，请勿回复。
"""
        html_message = f"""
<html>
<body>
<h2>{notification.title}</h2>
<div style="margin: 20px 0;">
{notification.content.replace(chr(10), '<br>')}
</div>
<hr>
<p style="color: #666; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</body>
</html>
"""
    
    # 发送邮件
    success_count = 0
    fail_count = 0
    
    for email in valid_emails:
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            fail_count += 1
    
    # 更新邮件发送时间
    notification.email_sent_at = timezone.now()
    notification.save(update_fields=['email_sent_at', 'updated_at'])
    
    logger.info(
        f"Notification {notification_id} email sent: "
        f"success={success_count}, fail={fail_count}"
    )


def get_member_unread_count(member) -> int:
    """
    获取成员的未读通知数量
    """
    from .models import NotificationRecipient
    
    return NotificationRecipient.objects.filter(
        member=member,
        is_read=False,
        is_deleted=False,
        notification__status='published',
        notification__is_deleted=False
    ).count()


def mark_notification_as_read(recipient_id: int, member) -> bool:
    """
    标记通知为已读
    """
    from .models import NotificationRecipient
    
    try:
        recipient = NotificationRecipient.objects.get(
            id=recipient_id,
            member=member,
            is_deleted=False
        )
        
        if not recipient.is_read:
            recipient.is_read = True
            recipient.read_at = timezone.now()
            recipient.save(update_fields=['is_read', 'read_at', 'updated_at'])
        
        return True
    except NotificationRecipient.DoesNotExist:
        return False


def mark_all_as_read(member) -> int:
    """
    标记成员的所有通知为已读
    返回更新的数量
    """
    from .models import NotificationRecipient
    
    return NotificationRecipient.objects.filter(
        member=member,
        is_read=False,
        is_deleted=False,
        notification__status='published',
        notification__is_deleted=False
    ).update(
        is_read=True,
        read_at=timezone.now(),
        updated_at=timezone.now()
    )
