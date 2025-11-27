"""
Celery Tasks for Feedback System

This module contains asynchronous tasks for email sending and other background operations.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from typing import Dict, List, Optional
import time

from .models import (
    Feedback, FeedbackReply, FeedbackEmailLog, 
    EmailTemplate, FeedbackStatusHistory,
    FeedbackNotificationConfig, FeedbackNotificationRecipient
)
from .utils import EmailValidator

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_feedback_reply_email(self, reply_id: int) -> Dict[str, any]:
    """
    Send email notification for feedback reply
    
    Args:
        reply_id: ID of the FeedbackReply instance
        
    Returns:
        Dictionary with task result
    """
    try:
        reply = FeedbackReply.objects.select_related(
            'feedback', 'feedback__software', 'user'
        ).get(pk=reply_id)
        
        feedback = reply.feedback
        
        # Don't send email for internal notes
        if reply.is_internal_note:
            logger.info(f"Skipping email for internal note reply {reply_id}")
            return {'status': 'skipped', 'reason': 'internal_note'}
        
        # Check if email notifications are enabled
        if not feedback.email_notification_enabled:
            logger.info(f"Email notifications disabled for feedback {feedback.id}")
            return {'status': 'skipped', 'reason': 'notifications_disabled'}
        
        # Check if email is verified for anonymous users
        if not feedback.user and not feedback.email_verified:
            logger.info(f"Email not verified for anonymous feedback {feedback.id}")
            return {'status': 'skipped', 'reason': 'email_not_verified'}
        
        # ✅ 新增：验证邮件地址格式
        if not EmailValidator.validate_and_log(feedback.contact_email, f" for reply {reply_id}"):
            return {'status': 'skipped', 'reason': 'invalid_email_address'}
        
        # Get email template
        template = EmailTemplate.objects.filter(
            tenant=feedback.tenant,
            template_type='reply',
            is_active=True
        ).first()
        
        if not template:
            logger.error(f"No active reply email template found for tenant {feedback.tenant_id}")
            raise Exception("No email template configured")
        
        # Prepare context for template
        context = {
            'feedback_title': feedback.title,
            'feedback_id': feedback.id,
            'reply_content': reply.content,
            'reply_user': reply.user.username if reply.user else 'Support Team',
            'software_name': feedback.application.name,
            'application_version': feedback.application_version.version if feedback.application_version else 'N/A',
            'view_url': f"{settings.FRONTEND_URL}/feedback/{feedback.id}",
            'unsubscribe_url': f"{settings.FRONTEND_URL}/feedback/{feedback.id}/unsubscribe",
        }
        
        # Render email content
        rendered = template.render(context)
        subject = rendered['subject']
        body_html = rendered['body_html']
        body_text = rendered['body_text']
        
        # Create email log entry
        email_log = FeedbackEmailLog.objects.create(
            feedback=feedback,
            email_type='reply',
            recipient=feedback.contact_email,
            subject=subject,
            content=body_html,
            status='sending',
            celery_task_id=self.request.id,
            tenant=feedback.tenant
        )
        
        try:
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[feedback.contact_email],
                reply_to=[feedback.application.contact_email] if feedback.application.contact_email else None
            )
            msg.attach_alternative(body_html, "text/html")
            msg.send()
            
            # Update email log
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save()
            
            # Update reply record
            reply.email_sent = True
            reply.email_sent_at = timezone.now()
            reply.save()
            
            logger.info(f"Successfully sent reply email for feedback {feedback.id}")
            return {
                'status': 'success',
                'email_log_id': email_log.id,
                'recipient': feedback.contact_email
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            email_log.status = 'failed'
            email_log.error_message = str(e)
            email_log.retry_count = self.request.retries
            email_log.save()
            
            reply.email_error = str(e)
            reply.email_retry_count = self.request.retries
            reply.save()
            
            # Retry the task
            raise self.retry(exc=e)
            
    except FeedbackReply.DoesNotExist:
        logger.error(f"FeedbackReply {reply_id} not found")
        return {'status': 'error', 'reason': 'reply_not_found'}
    except Exception as e:
        logger.error(f"Unexpected error in send_feedback_reply_email: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_status_change_email(self, status_history_id: int) -> Dict[str, any]:
    """
    Send email notification for feedback status change
    
    Args:
        status_history_id: ID of the FeedbackStatusHistory instance
        
    Returns:
        Dictionary with task result
    """
    try:
        history = FeedbackStatusHistory.objects.select_related(
            'feedback', 'feedback__software', 'changed_by'
        ).get(pk=status_history_id)
        
        feedback = history.feedback
        
        # Check if email notifications are enabled
        if not feedback.email_notification_enabled:
            logger.info(f"Email notifications disabled for feedback {feedback.id}")
            return {'status': 'skipped', 'reason': 'notifications_disabled'}
        
        # ✅ 新增：验证邮件地址格式
        if not EmailValidator.validate_and_log(feedback.contact_email, f" for status change {status_history_id}"):
            return {'status': 'skipped', 'reason': 'invalid_email_address'}
        
        # Get email template
        template = EmailTemplate.objects.filter(
            tenant=feedback.tenant,
            template_type='status_change',
            is_active=True
        ).first()
        
        if not template:
            logger.error(f"No active status change email template found for tenant {feedback.tenant_id}")
            raise Exception("No email template configured")
        
        # Prepare context
        context = {
            'feedback_title': feedback.title,
            'feedback_id': feedback.id,
            'old_status': history.get_from_status_display() if history.from_status else 'New',
            'new_status': history.get_to_status_display(),
            'changed_by': history.changed_by.username if history.changed_by else 'System',
            'change_reason': history.reason or 'Status updated',
            'software_name': feedback.application.name,
            'view_url': f"{settings.FRONTEND_URL}/feedback/{feedback.id}",
        }
        
        # Render email
        rendered = template.render(context)
        
        # Create email log
        email_log = FeedbackEmailLog.objects.create(
            feedback=feedback,
            email_type='status_change',
            recipient=feedback.contact_email,
            subject=rendered['subject'],
            content=rendered['body_html'],
            status='sending',
            celery_task_id=self.request.id,
            tenant=feedback.tenant
        )
        
        try:
            # Send email
            msg = EmailMultiAlternatives(
                subject=rendered['subject'],
                body=rendered['body_text'],
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[feedback.contact_email]
            )
            msg.attach_alternative(rendered['body_html'], "text/html")
            msg.send()
            
            # Update email log
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save()
            
            logger.info(f"Successfully sent status change email for feedback {feedback.id}")
            return {
                'status': 'success',
                'email_log_id': email_log.id,
                'recipient': feedback.contact_email
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            email_log.status = 'failed'
            email_log.error_message = str(e)
            email_log.retry_count = self.request.retries
            email_log.save()
            
            raise self.retry(exc=e)
            
    except FeedbackStatusHistory.DoesNotExist:
        logger.error(f"FeedbackStatusHistory {status_history_id} not found")
        return {'status': 'error', 'reason': 'history_not_found'}
    except Exception as e:
        logger.error(f"Unexpected error in send_status_change_email: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_verification_email(self, feedback_id: int) -> Dict[str, any]:
    """
    Send email verification for anonymous feedback
    
    Args:
        feedback_id: ID of the Feedback instance
        
    Returns:
        Dictionary with task result
    """
    try:
        feedback = Feedback.objects.select_related('software').get(pk=feedback_id)
        
        # Skip if already verified or has user
        if feedback.email_verified or feedback.user:
            logger.info(f"Skipping verification for feedback {feedback_id}")
            return {'status': 'skipped', 'reason': 'already_verified_or_has_user'}
        
        # ✅ 新增：验证邮件地址格式
        if not EmailValidator.validate_and_log(feedback.contact_email, f" for verification {feedback_id}"):
            return {'status': 'skipped', 'reason': 'invalid_email_address'}
        
        # Get email template
        template = EmailTemplate.objects.filter(
            tenant=feedback.tenant,
            template_type='verification',
            is_active=True
        ).first()
        
        if not template:
            # Use default template
            subject = "Verify your email for feedback submission"
            verification_url = f"{settings.FRONTEND_URL}/feedback/{feedback.id}/verify?token={feedback.email_verification_token}"
            body_html = f"""
            <h2>Email Verification Required</h2>
            <p>Thank you for submitting feedback for {feedback.application.name}.</p>
            <p>Please verify your email address to receive updates about your feedback:</p>
            <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>Or copy this link: {verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            """
            body_text = f"""
            Email Verification Required
            
            Thank you for submitting feedback for {feedback.application.name}.
            
            Please verify your email address by visiting:
            {verification_url}
            
            This link will expire in 24 hours.
            """
        else:
            # Use template
            context = {
                'feedback_title': feedback.title,
                'feedback_id': feedback.id,
                'software_name': feedback.application.name,
                'verification_url': f"{settings.FRONTEND_URL}/feedback/{feedback.id}/verify?token={feedback.email_verification_token}",
                'contact_name': feedback.contact_name or 'User',
            }
            rendered = template.render(context)
            subject = rendered['subject']
            body_html = rendered['body_html']
            body_text = rendered['body_text']
        
        # Create email log
        email_log = FeedbackEmailLog.objects.create(
            feedback=feedback,
            email_type='verification',
            recipient=feedback.contact_email,
            subject=subject,
            content=body_html,
            status='sending',
            celery_task_id=self.request.id,
            tenant=feedback.tenant
        )
        
        try:
            # Send email
            send_mail(
                subject=subject,
                message=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[feedback.contact_email],
                html_message=body_html,
                fail_silently=False
            )
            
            # Update email log
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save()
            
            # Update feedback
            feedback.email_verification_sent_at = timezone.now()
            feedback.save()
            
            logger.info(f"Successfully sent verification email for feedback {feedback.id}")
            return {
                'status': 'success',
                'email_log_id': email_log.id,
                'recipient': feedback.contact_email
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            email_log.status = 'failed'
            email_log.error_message = str(e)
            email_log.retry_count = self.request.retries
            email_log.save()
            
            raise self.retry(exc=e)
            
    except Feedback.DoesNotExist:
        logger.error(f"Feedback {feedback_id} not found")
        return {'status': 'error', 'reason': 'feedback_not_found'}
    except Exception as e:
        logger.error(f"Unexpected error in send_verification_email: {str(e)}")
        raise self.retry(exc=e)


@shared_task
def cleanup_old_email_logs(days: int = 90) -> Dict[str, int]:
    """
    Clean up old email logs
    
    Args:
        days: Number of days to keep logs (default: 90)
        
    Returns:
        Dictionary with cleanup statistics
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    # Delete old logs
    deleted_count = FeedbackEmailLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Deleted {deleted_count} email logs older than {days} days")
    
    return {
        'deleted_count': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task
def send_feedback_summary_email(tenant_id: int, recipient_email: str, period_days: int = 7) -> Dict[str, any]:
    """
    Send summary email of feedback activity
    
    Args:
        tenant_id: Tenant ID
        recipient_email: Email address to send summary to
        period_days: Number of days to include in summary
        
    Returns:
        Dictionary with task result
    """
    from django.db.models import Count, Q
    from .models import Tenant
    
    try:
        tenant = Tenant.objects.get(pk=tenant_id)
        cutoff_date = timezone.now() - timezone.timedelta(days=period_days)
        
        # Get feedback statistics
        feedbacks = Feedback.objects.filter(
            tenant=tenant,
            created_at__gte=cutoff_date
        )
        
        stats = {
            'total_new': feedbacks.count(),
            'by_type': dict(feedbacks.values_list('feedback_type').annotate(count=Count('id'))),
            'by_status': dict(feedbacks.values_list('status').annotate(count=Count('id'))),
            'resolved': feedbacks.filter(status='resolved').count(),
            'high_priority': feedbacks.filter(priority='high').count(),
        }
        
        # Get top feedbacks by votes
        top_feedbacks = feedbacks.order_by('-vote_count')[:5]
        
        # Prepare email content
        subject = f"Feedback Summary for {tenant.name} - Last {period_days} Days"
        
        body_html = f"""
        <h2>Feedback Summary Report</h2>
        <p>Period: Last {period_days} days</p>
        
        <h3>Overview</h3>
        <ul>
            <li>Total New Feedback: {stats['total_new']}</li>
            <li>Resolved: {stats['resolved']}</li>
            <li>High Priority: {stats['high_priority']}</li>
        </ul>
        
        <h3>By Type</h3>
        <ul>
            {''.join([f"<li>{type}: {count}</li>" for type, count in stats['by_type'].items()])}
        </ul>
        
        <h3>Top Voted Feedback</h3>
        <ol>
            {''.join([f"<li>{fb.title} ({fb.vote_count} votes)</li>" for fb in top_feedbacks])}
        </ol>
        """
        
        # Create email log
        email_log = FeedbackEmailLog.objects.create(
            email_type='summary',
            recipient=recipient_email,
            subject=subject,
            content=body_html,
            status='sending',
            tenant=tenant
        )
        
        try:
            # Send email
            send_mail(
                subject=subject,
                message="Please view this email in HTML format",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=body_html,
                fail_silently=False
            )
            
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save()
            
            return {'status': 'success', 'stats': stats}
            
        except Exception as e:
            email_log.status = 'failed'
            email_log.error_message = str(e)
            email_log.save()
            raise
            
    except Tenant.DoesNotExist:
        logger.error(f"Tenant {tenant_id} not found")
        return {'status': 'error', 'reason': 'tenant_not_found'}


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_new_feedback_notification(self, feedback_id: int) -> Dict[str, any]:
    """
    发送新反馈通知邮件到配置的接收者列表
    
    当用户提交新反馈后，系统会检查应用是否配置了通知，
    如果配置了且启用，则向所有活跃的接收者发送通知邮件。
    
    Args:
        feedback_id: Feedback实例的ID
        
    Returns:
        Dictionary with task result containing:
        - status: 'success' | 'skipped' | 'error'
        - sent_count: 成功发送的邮件数量
        - failed_count: 发送失败的邮件数量
        - recipients: 接收者列表
    """
    try:
        # 获取反馈及关联信息
        feedback = Feedback.objects.select_related(
            'application', 'tenant'
        ).get(pk=feedback_id, is_deleted=False)
        
        application = feedback.application
        if not application:
            logger.info(f"Feedback {feedback_id} has no associated application")
            return {'status': 'skipped', 'reason': 'no_application'}
        
        # 检查应用是否配置了通知
        try:
            config = FeedbackNotificationConfig.objects.get(
                application=application,
                is_deleted=False
            )
        except FeedbackNotificationConfig.DoesNotExist:
            logger.info(f"No notification config for application {application.id}")
            return {'status': 'skipped', 'reason': 'no_config'}
        
        # 检查通知是否启用
        if not config.is_enabled:
            logger.info(f"Notifications disabled for application {application.id}")
            return {'status': 'skipped', 'reason': 'notifications_disabled'}
        
        # 获取活跃的接收者
        recipients = config.get_active_recipients()
        if not recipients.exists():
            logger.info(f"No active recipients for application {application.id}")
            return {'status': 'skipped', 'reason': 'no_recipients'}
        
        # 获取邮件模板
        template = EmailTemplate.objects.filter(
            tenant=feedback.tenant,
            template_type='new_feedback',
            is_active=True
        ).first()
        
        # 准备模板上下文
        context = {
            'application_name': application.name,
            'feedback_title': feedback.title,
            'feedback_description': feedback.description[:500] + '...' if len(feedback.description) > 500 else feedback.description,
            'feedback_type': feedback.get_feedback_type_display(),
            'priority': feedback.get_priority_display(),
            'contact_name': feedback.contact_name or '匿名用户',
            'contact_email': feedback.contact_email or '未提供',
            'submitted_at': feedback.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'feedback_id': feedback.id,
            'view_url': f"{settings.FRONTEND_URL}/admin/feedbacks/{feedback.id}",
        }
        
        # 使用模板或默认内容
        if template:
            rendered = template.render(context)
            subject = rendered['subject']
            body_html = rendered['body_html']
            body_text = rendered['body_text']
        else:
            # 使用默认模板
            subject = f"[{application.name}] 新反馈: {feedback.title}"
            body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
        .label {{ font-weight: bold; color: #666; }}
        .button {{ display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📬 新反馈通知</h1>
        </div>
        <div class="content">
            <p>您好，</p>
            <p><strong>{context['application_name']}</strong> 收到了一条新的用户反馈：</p>
            
            <div class="info-box">
                <p><span class="label">标题：</span>{context['feedback_title']}</p>
                <p><span class="label">类型：</span>{context['feedback_type']}</p>
                <p><span class="label">优先级：</span>{context['priority']}</p>
                <p><span class="label">提交者：</span>{context['contact_name']} ({context['contact_email']})</p>
                <p><span class="label">提交时间：</span>{context['submitted_at']}</p>
            </div>
            
            <div class="info-box">
                <p><span class="label">反馈内容：</span></p>
                <p>{context['feedback_description']}</p>
            </div>
            
            <p style="text-align: center; margin-top: 20px;">
                <a href="{context['view_url']}" class="button">查看详情</a>
            </p>
        </div>
        <div class="footer">
            <p>此邮件由系统自动发送，请勿直接回复。</p>
            <p>反馈 ID: #{context['feedback_id']}</p>
        </div>
    </div>
</body>
</html>
            """
            body_text = f"""
新反馈通知

{context['application_name']} 收到了一条新的用户反馈：

标题：{context['feedback_title']}
类型：{context['feedback_type']}
优先级：{context['priority']}
提交者：{context['contact_name']} ({context['contact_email']})
提交时间：{context['submitted_at']}

反馈内容：
{context['feedback_description']}

查看详情：{context['view_url']}

反馈 ID: #{context['feedback_id']}
            """
        
        # 发送邮件到每个接收者
        sent_count = 0
        failed_count = 0
        recipient_results = []
        
        for recipient in recipients:
            # 验证邮箱
            if not EmailValidator.validate_and_log(recipient.email, f" for new feedback notification {feedback_id}"):
                failed_count += 1
                recipient_results.append({
                    'email': recipient.email,
                    'status': 'skipped',
                    'reason': 'invalid_email'
                })
                continue
            
            # 创建邮件日志
            email_log = FeedbackEmailLog.objects.create(
                feedback=feedback,
                email_type='new_feedback',
                recipient=recipient.email,
                subject=subject,
                content=body_html,
                status='sending',
                celery_task_id=self.request.id,
                tenant=feedback.tenant
            )
            
            try:
                # 发送邮件
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=body_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient.email]
                )
                msg.attach_alternative(body_html, "text/html")
                msg.send()
                
                # 更新日志
                email_log.status = 'sent'
                email_log.sent_at = timezone.now()
                email_log.save()
                
                sent_count += 1
                recipient_results.append({
                    'email': recipient.email,
                    'status': 'sent',
                    'email_log_id': email_log.id
                })
                
                logger.info(f"New feedback notification sent to {recipient.email} for feedback {feedback_id}")
                
            except Exception as e:
                logger.error(f"Failed to send notification to {recipient.email}: {str(e)}")
                email_log.status = 'failed'
                email_log.error_message = str(e)
                email_log.save()
                
                failed_count += 1
                recipient_results.append({
                    'email': recipient.email,
                    'status': 'failed',
                    'error': str(e)
                })
        
        logger.info(
            f"New feedback notification completed for feedback {feedback_id}: "
            f"sent={sent_count}, failed={failed_count}"
        )
        
        return {
            'status': 'success',
            'feedback_id': feedback_id,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'recipients': recipient_results
        }
        
    except Feedback.DoesNotExist:
        logger.error(f"Feedback {feedback_id} not found")
        return {'status': 'error', 'reason': 'feedback_not_found'}
    except Exception as e:
        logger.error(f"Unexpected error in send_new_feedback_notification: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=1, default_retry_delay=60)
def send_test_feedback_notification(self, config_id: int, test_email: str) -> Dict[str, any]:
    """
    发送测试通知邮件
    
    Args:
        config_id: FeedbackNotificationConfig实例的ID
        test_email: 测试邮箱地址
        
    Returns:
        Dictionary with task result
    """
    try:
        config = FeedbackNotificationConfig.objects.select_related(
            'application', 'tenant'
        ).get(pk=config_id, is_deleted=False)
        
        application = config.application
        
        # 验证邮箱
        if not EmailValidator.validate_and_log(test_email, f" for test notification"):
            return {'status': 'error', 'reason': 'invalid_email'}
        
        # 准备测试内容
        subject = f"[测试] {application.name} 反馈通知配置测试"
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .success {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 测试邮件</h1>
        </div>
        <div class="content">
            <div class="success">
                <h3>✅ 配置成功！</h3>
                <p>如果您收到这封邮件，说明 <strong>{application.name}</strong> 的反馈通知功能已正确配置。</p>
            </div>
            <p style="margin-top: 20px;">
                <strong>应用名称：</strong>{application.name}<br>
                <strong>应用代码：</strong>{application.code}<br>
                <strong>配置ID：</strong>{config.id}<br>
                <strong>测试时间：</strong>{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </div>
</body>
</html>
        """
        body_text = f"""
测试邮件

如果您收到这封邮件，说明 {application.name} 的反馈通知功能已正确配置。

应用名称：{application.name}
应用代码：{application.code}
配置ID：{config.id}
测试时间：{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # 创建邮件日志
        email_log = FeedbackEmailLog.objects.create(
            email_type='new_feedback',
            recipient=test_email,
            subject=subject,
            content=body_html,
            status='sending',
            celery_task_id=self.request.id,
            tenant=config.tenant
        )
        
        try:
            # 发送邮件
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[test_email]
            )
            msg.attach_alternative(body_html, "text/html")
            msg.send()
            
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save()
            
            logger.info(f"Test notification sent to {test_email} for config {config_id}")
            
            return {
                'status': 'success',
                'email_log_id': email_log.id,
                'recipient': test_email
            }
            
        except Exception as e:
            logger.error(f"Failed to send test notification: {str(e)}")
            email_log.status = 'failed'
            email_log.error_message = str(e)
            email_log.save()
            
            return {
                'status': 'error',
                'error': str(e)
            }
        
    except FeedbackNotificationConfig.DoesNotExist:
        logger.error(f"NotificationConfig {config_id} not found")
        return {'status': 'error', 'reason': 'config_not_found'}
    except Exception as e:
        logger.error(f"Unexpected error in send_test_feedback_notification: {str(e)}")
        raise self.retry(exc=e)
