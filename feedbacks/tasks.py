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
    EmailTemplate, FeedbackStatusHistory
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
            'software_name': feedback.software.name,
            'software_version': feedback.software_version.version if feedback.software_version else 'N/A',
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
                reply_to=[feedback.software.contact_email] if feedback.software.contact_email else None
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
            'software_name': feedback.software.name,
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
            <p>Thank you for submitting feedback for {feedback.software.name}.</p>
            <p>Please verify your email address to receive updates about your feedback:</p>
            <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>Or copy this link: {verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            """
            body_text = f"""
            Email Verification Required
            
            Thank you for submitting feedback for {feedback.software.name}.
            
            Please verify your email address by visiting:
            {verification_url}
            
            This link will expire in 24 hours.
            """
        else:
            # Use template
            context = {
                'feedback_title': feedback.title,
                'feedback_id': feedback.id,
                'software_name': feedback.software.name,
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
