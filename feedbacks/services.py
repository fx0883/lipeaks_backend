"""
Feedback System Services

This module contains business logic services for the feedback system.
"""

from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import logging

from .models import (
    Feedback, FeedbackReply, FeedbackStatusHistory,
    EmailTemplate, FeedbackEmailLog
)
from .tasks import (
    send_feedback_reply_email,
    send_status_change_email,
    send_verification_email
)
from .utils import TaskExecutor, RedisHealthChecker

logger = logging.getLogger(__name__)


class EmailService:
    """Service for handling email operations"""
    
    @staticmethod
    def send_reply_notification(reply: FeedbackReply) -> Optional[dict]:
        """
        Send email notification for a feedback reply
        
        支持自动降级：Redis不可用时同步发送
        
        Args:
            reply: FeedbackReply instance
            
        Returns:
            dict: 任务执行结果 {'mode': 'async/sync/failed', ...}
        """
        try:
            # Don't send for internal notes
            if reply.is_internal_note:
                logger.info(f"Skipping email for internal note reply {reply.id}")
                return None
            
            # 使用TaskExecutor自动处理降级
            result = TaskExecutor.execute_task(
                send_feedback_reply_email,
                reply.id,
                fallback_to_sync=True
            )
            
            logger.info(f"Email task executed in {result.get('mode')} mode for reply {reply.id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send reply email for reply {reply.id}: {str(e)}")
            return {'mode': 'failed', 'error': str(e)}
    
    @staticmethod
    def send_status_notification(status_history: FeedbackStatusHistory) -> Optional[dict]:
        """
        Send email notification for status change
        
        支持自动降级：Redis不可用时同步发送
        
        Args:
            status_history: FeedbackStatusHistory instance
            
        Returns:
            dict: 任务执行结果
        """
        try:
            # Only send for significant status changes
            insignificant_changes = [
                ('submitted', 'reviewing'),  # Initial review
            ]
            
            change = (status_history.from_status, status_history.to_status)
            if change in insignificant_changes:
                logger.info(f"Skipping email for insignificant status change: {change}")
                return None
            
            # 使用TaskExecutor自动处理降级
            result = TaskExecutor.execute_task(
                send_status_change_email,
                status_history.id,
                fallback_to_sync=True
            )
            
            logger.info(f"Status email task executed in {result.get('mode')} mode")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send status email for history {status_history.id}: {str(e)}")
            return {'mode': 'failed', 'error': str(e)}
    
    @staticmethod
    def send_verification(feedback: Feedback) -> Optional[dict]:
        """
        Send email verification for anonymous feedback
        
        支持自动降级：Redis不可用时同步发送
        
        Args:
            feedback: Feedback instance
            
        Returns:
            dict: 任务执行结果
        """
        try:
            # Only for anonymous users
            if feedback.user or feedback.email_verified:
                logger.info(f"Skipping verification for feedback {feedback.id}")
                return None
            
            # 使用TaskExecutor自动处理降级
            result = TaskExecutor.execute_task(
                send_verification_email,
                feedback.id,
                fallback_to_sync=True
            )
            
            logger.info(f"Verification email task executed in {result.get('mode')} mode")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send verification email for feedback {feedback.id}: {str(e)}")
            return {'mode': 'failed', 'error': str(e)}
    
    @staticmethod
    def create_default_templates(tenant) -> Dict[str, EmailTemplate]:
        """
        Create default email templates for a tenant
        
        Args:
            tenant: Tenant instance
            
        Returns:
            Dictionary of created templates
        """
        templates = {}
        
        # Reply notification template
        templates['reply'] = EmailTemplate.objects.create(
            tenant=tenant,
            name="Feedback Reply Notification",
            template_type='reply',
            subject="Re: {feedback_title}",
            body_html="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .reply-box { background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #4CAF50; }
        .button { display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Reply to Your Feedback</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>You have received a new reply to your feedback: <strong>{feedback_title}</strong></p>
            
            <div class="reply-box">
                <p><strong>{reply_user} replied:</strong></p>
                <p>{reply_content}</p>
            </div>
            
            <p>Software: {software_name} {software_version}</p>
            
            <p style="text-align: center;">
                <a href="{view_url}" class="button">View Feedback</a>
            </p>
        </div>
        <div class="footer">
            <p>You received this email because you submitted feedback. 
            <a href="{unsubscribe_url}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
            """,
            body_text="""
New Reply to Your Feedback

Hello,

You have received a new reply to your feedback: {feedback_title}

{reply_user} replied:
{reply_content}

Software: {software_name} {software_version}

View feedback: {view_url}

You received this email because you submitted feedback.
Unsubscribe: {unsubscribe_url}
            """,
            variables={
                'feedback_title': 'Feedback title',
                'feedback_id': 'Feedback ID',
                'reply_content': 'Reply content',
                'reply_user': 'User who replied',
                'software_name': 'Software name',
                'software_version': 'Software version',
                'view_url': 'URL to view feedback',
                'unsubscribe_url': 'URL to unsubscribe'
            }
        )
        
        # Status change template
        templates['status_change'] = EmailTemplate.objects.create(
            tenant=tenant,
            name="Feedback Status Change Notification",
            template_type='status_change',
            subject="Feedback Status Updated: {feedback_title}",
            body_html="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #2196F3; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .status-box { background-color: white; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .old-status { color: #666; text-decoration: line-through; }
        .new-status { color: #2196F3; font-weight: bold; }
        .button { display: inline-block; padding: 10px 20px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Feedback Status Updated</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>The status of your feedback has been updated:</p>
            
            <h3>{feedback_title}</h3>
            
            <div class="status-box">
                <p>Status changed from <span class="old-status">{old_status}</span> to <span class="new-status">{new_status}</span></p>
                <p><strong>Changed by:</strong> {changed_by}</p>
                <p><strong>Reason:</strong> {change_reason}</p>
            </div>
            
            <p style="text-align: center;">
                <a href="{view_url}" class="button">View Feedback</a>
            </p>
        </div>
    </div>
</body>
</html>
            """,
            body_text="""
Feedback Status Updated

Hello,

The status of your feedback has been updated:

{feedback_title}

Status changed from {old_status} to {new_status}
Changed by: {changed_by}
Reason: {change_reason}

View feedback: {view_url}
            """,
            variables={
                'feedback_title': 'Feedback title',
                'feedback_id': 'Feedback ID',
                'old_status': 'Previous status',
                'new_status': 'New status',
                'changed_by': 'User who changed status',
                'change_reason': 'Reason for change',
                'software_name': 'Software name',
                'view_url': 'URL to view feedback'
            }
        )
        
        # Verification template
        templates['verification'] = EmailTemplate.objects.create(
            tenant=tenant,
            name="Email Verification",
            template_type='verification',
            subject="Verify your email for feedback submission",
            body_html="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #FF9800; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .button { display: inline-block; padding: 15px 30px; background-color: #FF9800; color: white; text-decoration: none; border-radius: 5px; font-size: 18px; }
        .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 20px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Email Verification Required</h1>
        </div>
        <div class="content">
            <p>Hello {contact_name},</p>
            <p>Thank you for submitting feedback for <strong>{software_name}</strong>.</p>
            
            <p>To receive updates about your feedback, please verify your email address:</p>
            
            <p style="text-align: center;">
                <a href="{verification_url}" class="button">Verify Email Address</a>
            </p>
            
            <div class="warning">
                <p><strong>Note:</strong> This verification link will expire in 24 hours.</p>
            </div>
            
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">{verification_url}</p>
            
            <p>Your feedback ID: #{feedback_id}</p>
        </div>
    </div>
</body>
</html>
            """,
            body_text="""
Email Verification Required

Hello {contact_name},

Thank you for submitting feedback for {software_name}.

To receive updates about your feedback, please verify your email address by clicking the link below:

{verification_url}

Note: This verification link will expire in 24 hours.

Your feedback ID: #{feedback_id}
            """,
            variables={
                'feedback_title': 'Feedback title',
                'feedback_id': 'Feedback ID',
                'software_name': 'Software name',
                'verification_url': 'Email verification URL',
                'contact_name': 'Contact name'
            }
        )
        
        logger.info(f"Created default email templates for tenant {tenant.name}")
        return templates


class FeedbackService:
    """Service for feedback operations"""
    
    @staticmethod
    @transaction.atomic
    def create_feedback(validated_data: Dict[str, Any], user=None, tenant=None) -> Feedback:
        """
        Create a new feedback with all necessary setup
        
        Args:
            validated_data: Validated feedback data
            user: User instance (optional)
            tenant: Tenant instance
            
        Returns:
            Created Feedback instance
        """
        # Create feedback
        feedback = Feedback.objects.create(
            **validated_data,
            user=user,
            tenant=tenant
        )
        
        # Send verification email for anonymous users
        if not user and feedback.contact_email:
            EmailService.send_verification(feedback)
        
        # Update software statistics
        if feedback.software:
            feedback.software.update_statistics()
        
        logger.info(f"Created feedback {feedback.id}")
        return feedback
    
    @staticmethod
    @transaction.atomic
    def change_status(feedback: Feedback, new_status: str, changed_by=None, reason: str = "") -> FeedbackStatusHistory:
        """
        Change feedback status with history tracking
        
        Args:
            feedback: Feedback instance
            new_status: New status value
            changed_by: User making the change
            reason: Reason for status change
            
        Returns:
            Created FeedbackStatusHistory instance
        """
        old_status = feedback.status
        
        # Create history record
        history = FeedbackStatusHistory.objects.create(
            feedback=feedback,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            reason=reason,
            tenant=feedback.tenant
        )
        
        # Update feedback
        feedback.status = new_status
        
        # Set resolved_at if changing to resolved
        if new_status == 'resolved' and not feedback.resolved_at:
            feedback.resolved_at = timezone.now()
        elif new_status != 'resolved':
            feedback.resolved_at = None
        
        feedback.save()
        
        # Send notification email
        EmailService.send_status_notification(history)
        
        # Update software statistics
        if feedback.software:
            feedback.software.update_statistics()
        
        logger.info(f"Changed feedback {feedback.id} status from {old_status} to {new_status}")
        return history
    
    @staticmethod
    @transaction.atomic
    def add_reply(feedback: Feedback, content: str, user, is_internal_note: bool = False) -> FeedbackReply:
        """
        Add a reply to feedback
        
        Args:
            feedback: Feedback instance
            content: Reply content
            user: User making the reply
            is_internal_note: Whether this is an internal note
            
        Returns:
            Created FeedbackReply instance
        """
        reply = FeedbackReply.objects.create(
            feedback=feedback,
            content=content,
            user=user,
            is_internal_note=is_internal_note,
            tenant=feedback.tenant
        )
        
        # Send notification email if not internal
        if not is_internal_note:
            EmailService.send_reply_notification(reply)
        
        logger.info(f"Added reply {reply.id} to feedback {feedback.id}")
        return reply
