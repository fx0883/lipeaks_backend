"""
Feedback System Services

This module contains business logic services for the feedback system.
"""

from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import time

from .models import (
    Feedback, FeedbackReply, FeedbackStatusHistory,
    EmailTemplate, FeedbackEmailLog,
    FeedbackNotificationConfig, FeedbackNotificationRecipient
)
from .tasks import (
    send_feedback_reply_email,
    send_status_change_email,
    send_verification_email,
    send_new_feedback_notification,
    send_test_feedback_notification
)
from .utils import TaskExecutor, RedisHealthChecker, EmailValidator

logger = logging.getLogger(__name__)


class EmailThreadPoolManager:
    """邮件发送线程池管理器 - 单例模式"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 配置线程池
        self.max_workers = getattr(settings, 'EMAIL_THREAD_POOL_SIZE', 3)
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix='email-sender'
        )
        self._initialized = True
        logger.info(f"Email thread pool initialized with {self.max_workers} workers")
    
    def submit_email_task(self, task_func, *args, **kwargs):
        """提交邮件任务到线程池"""
        try:
            future = self.executor.submit(task_func, *args, **kwargs)
            logger.debug(f"Email task {task_func.__name__} submitted to thread pool")
            return future
        except Exception as e:
            logger.error(f"Failed to submit email task {task_func.__name__}: {str(e)}")
            return None
    
    def shutdown(self, wait=True):
        """关闭线程池"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=wait)
            logger.info("Email thread pool shutdown")


def _process_email_in_background(email_type: str, target_id: int, context: str = ""):
    """
    后台邮件处理函数 - 在线程中执行
    
    Args:
        email_type: 邮件类型 ('reply', 'status_change', 'verification')
        target_id: 目标对象ID
        context: 上下文信息用于日志
    """
    logger.info(f"Background email processing started: {email_type} #{target_id}{context}")
    
    try:
        # 根据邮件类型获取相关对象和邮件地址
        if email_type == 'reply':
            reply = FeedbackReply.objects.select_related('feedback').get(pk=target_id)
            email = reply.feedback.contact_email
            context_info = f" for reply {target_id}"
        elif email_type == 'status_change':
            history = FeedbackStatusHistory.objects.select_related('feedback').get(pk=target_id)
            email = history.feedback.contact_email
            context_info = f" for status change {target_id}"
        elif email_type == 'verification':
            feedback = Feedback.objects.get(pk=target_id)
            email = feedback.contact_email
            context_info = f" for verification {target_id}"
        else:
            logger.error(f"Unknown email type: {email_type}")
            return
        
        # 邮件地址验证
        if not EmailValidator.validate_and_log(email, context_info):
            logger.info(f"Email sending skipped due to invalid address: {email_type} #{target_id}")
            return
        
        # 执行邮件发送任务
        task_map = {
            'reply': send_feedback_reply_email,
            'status_change': send_status_change_email,
            'verification': send_verification_email,
        }
        
        task_func = task_map[email_type]
        
        # 尝试异步执行，失败则记录错误
        result = TaskExecutor.execute_task(
            task_func,
            target_id,
            fallback_to_sync=False  # 不使用同步降级
        )
        
        if result.get('mode') == 'failed':
            logger.error(f"Email task failed: {email_type} #{target_id} - {result.get('error')}")
        else:
            logger.info(f"Email task submitted: {email_type} #{target_id} - mode: {result.get('mode')}")
            
    except Exception as e:
        logger.error(f"Background email processing error: {email_type} #{target_id} - {str(e)}")


# 获取线程池管理器实例
_email_thread_pool = EmailThreadPoolManager()


def _process_new_feedback_notification(feedback_id: int, context: str = ""):
    """
    后台处理新反馈通知 - 在线程中执行
    
    Args:
        feedback_id: Feedback实例的ID
        context: 上下文信息用于日志
    """
    logger.info(f"Background new feedback notification started: #{feedback_id}{context}")
    
    try:
        # 执行 Celery 任务（Redis 不可用时降级到同步执行）
        result = TaskExecutor.execute_task(
            send_new_feedback_notification,
            feedback_id,
            fallback_to_sync=True
        )
        
        if result.get('mode') == 'failed':
            logger.error(f"New feedback notification task failed: #{feedback_id} - {result.get('error')}")
        else:
            logger.info(f"New feedback notification task submitted: #{feedback_id} - mode: {result.get('mode')}")
            
    except Exception as e:
        logger.error(f"Background new feedback notification error: #{feedback_id} - {str(e)}")


class EmailService:
    """Service for handling email operations"""
    
    @staticmethod
    def send_reply_notification(reply: FeedbackReply) -> Optional[dict]:
        """
        Send email notification for a feedback reply
        
        当 CELERY_ENABLED=False 时（如 cPanel 环境），直接同步执行。
        否则使用后台线程池，API立即返回。
        
        Args:
            reply: FeedbackReply instance
            
        Returns:
            dict: 提交结果 {'status': 'submitted/skipped', ...}
        """
        try:
            # Don't send for internal notes
            if reply.is_internal_note:
                logger.info(f"Skipping email for internal note reply {reply.id}")
                return {'status': 'skipped', 'reason': 'internal_note'}
            
            # 检查是否禁用了 Celery（如 cPanel 环境）
            celery_enabled = getattr(settings, 'CELERY_ENABLED', True)
            
            if not celery_enabled:
                # cPanel 模式：直接同步执行
                logger.info(f"Sync mode: executing reply notification directly for reply {reply.id}")
                _process_email_in_background('reply', reply.id, " (sync mode)")
                return {'status': 'completed', 'mode': 'sync'}
            
            # 正常模式：提交到后台线程池，API立即返回
            future = _email_thread_pool.submit_email_task(
                _process_email_in_background,
                'reply',
                reply.id,
                f" from API thread {threading.current_thread().name}"
            )
            
            if future:
                logger.info(f"Reply email task submitted to thread pool: reply {reply.id}")
                return {'status': 'submitted', 'mode': 'thread_pool'}
            else:
                logger.error(f"Failed to submit reply email task: reply {reply.id}")
                return {'status': 'failed', 'reason': 'thread_pool_submit_failed'}
            
        except Exception as e:
            logger.error(f"Failed to submit reply email task for reply {reply.id}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    @staticmethod
    def send_status_notification(status_history: FeedbackStatusHistory) -> Optional[dict]:
        """
        Send email notification for status change
        
        当 CELERY_ENABLED=False 时（如 cPanel 环境），直接同步执行。
        否则使用后台线程池，API立即返回。
        
        Args:
            status_history: FeedbackStatusHistory instance
            
        Returns:
            dict: 提交结果 {'status': 'submitted/skipped', ...}
        """
        try:
            # Only send for significant status changes
            insignificant_changes = [
                ('submitted', 'reviewing'),  # Initial review
            ]
            
            change = (status_history.from_status, status_history.to_status)
            if change in insignificant_changes:
                logger.info(f"Skipping email for insignificant status change: {change}")
                return {'status': 'skipped', 'reason': 'insignificant_change'}
            
            # 检查是否禁用了 Celery（如 cPanel 环境）
            celery_enabled = getattr(settings, 'CELERY_ENABLED', True)
            
            if not celery_enabled:
                # cPanel 模式：直接同步执行
                logger.info(f"Sync mode: executing status notification directly for history {status_history.id}")
                _process_email_in_background('status_change', status_history.id, " (sync mode)")
                return {'status': 'completed', 'mode': 'sync'}
            
            # 正常模式：提交到后台线程池，API立即返回
            future = _email_thread_pool.submit_email_task(
                _process_email_in_background,
                'status_change',
                status_history.id,
                f" from API thread {threading.current_thread().name}"
            )
            
            if future:
                logger.info(f"Status email task submitted to thread pool: history {status_history.id}")
                return {'status': 'submitted', 'mode': 'thread_pool'}
            else:
                logger.error(f"Failed to submit status email task: history {status_history.id}")
                return {'status': 'failed', 'reason': 'thread_pool_submit_failed'}
            
        except Exception as e:
            logger.error(f"Failed to submit status email task for history {status_history.id}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    @staticmethod
    def send_verification(feedback: Feedback) -> Optional[dict]:
        """
        Send email verification for anonymous feedback
        
        当 CELERY_ENABLED=False 时（如 cPanel 环境），直接同步执行。
        否则使用后台线程池，API立即返回。
        
        Args:
            feedback: Feedback instance
            
        Returns:
            dict: 提交结果 {'status': 'submitted/skipped', ...}
        """
        try:
            # Only for anonymous users
            if feedback.user or feedback.email_verified:
                logger.info(f"Skipping verification for feedback {feedback.id}")
                return {'status': 'skipped', 'reason': 'already_verified_or_has_user'}
            
            # 检查是否禁用了 Celery（如 cPanel 环境）
            celery_enabled = getattr(settings, 'CELERY_ENABLED', True)
            
            if not celery_enabled:
                # cPanel 模式：直接同步执行
                logger.info(f"Sync mode: executing verification directly for feedback {feedback.id}")
                _process_email_in_background('verification', feedback.id, " (sync mode)")
                return {'status': 'completed', 'mode': 'sync'}
            
            # 正常模式：提交到后台线程池，API立即返回
            future = _email_thread_pool.submit_email_task(
                _process_email_in_background,
                'verification',
                feedback.id,
                f" from API thread {threading.current_thread().name}"
            )
            
            if future:
                logger.info(f"Verification email task submitted to thread pool: feedback {feedback.id}")
                return {'status': 'submitted', 'mode': 'thread_pool'}
            else:
                logger.error(f"Failed to submit verification email task: feedback {feedback.id}")
                return {'status': 'failed', 'reason': 'thread_pool_submit_failed'}
            
        except Exception as e:
            logger.error(f"Failed to submit verification email task for feedback {feedback.id}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    @staticmethod
    def send_new_feedback_notification(feedback: Feedback) -> Optional[dict]:
        """
        发送新反馈通知到配置的接收者
        
        当用户提交新反馈后调用此方法，会检查应用是否配置了通知，
        如果配置了则提交任务到后台线程池处理。
        
        当 CELERY_ENABLED=False 时（如 cPanel 环境），直接同步执行，绕过线程池。
        
        Args:
            feedback: Feedback instance
            
        Returns:
            dict: 提交结果 {'status': 'submitted/skipped', ...}
        """
        try:
            # 检查是否有关联应用
            if not feedback.application:
                logger.info(f"Feedback {feedback.id} has no application, skipping notification")
                return {'status': 'skipped', 'reason': 'no_application'}
            
            # 检查应用是否配置了通知
            try:
                config = FeedbackNotificationConfig.objects.get(
                    application=feedback.application,
                    is_deleted=False
                )
                if not config.is_enabled:
                    logger.info(f"Notifications disabled for application {feedback.application.id}")
                    return {'status': 'skipped', 'reason': 'notifications_disabled'}
            except FeedbackNotificationConfig.DoesNotExist:
                logger.info(f"No notification config for application {feedback.application.id}")
                return {'status': 'skipped', 'reason': 'no_config'}
            
            # 检查是否禁用了 Celery（如 cPanel 环境）
            # 禁用时直接同步执行，绕过线程池（cPanel 可能限制后台线程）
            celery_enabled = getattr(settings, 'CELERY_ENABLED', True)
            
            if not celery_enabled:
                # cPanel 模式：直接同步执行
                logger.info(f"Sync mode: executing new feedback notification directly for feedback {feedback.id}")
                _process_new_feedback_notification(feedback.id, " (sync mode)")
                return {'status': 'completed', 'mode': 'sync'}
            
            # 正常模式：提交到后台线程池
            future = _email_thread_pool.submit_email_task(
                _process_new_feedback_notification,
                feedback.id,
                f" from API thread {threading.current_thread().name}"
            )
            
            if future:
                logger.info(f"New feedback notification task submitted: feedback {feedback.id}")
                return {'status': 'submitted', 'mode': 'thread_pool'}
            else:
                logger.error(f"Failed to submit new feedback notification task: feedback {feedback.id}")
                return {'status': 'failed', 'reason': 'thread_pool_submit_failed'}
            
        except Exception as e:
            logger.error(f"Failed to submit new feedback notification for feedback {feedback.id}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    @staticmethod
    def send_test_notification(config: FeedbackNotificationConfig, test_email: str) -> dict:
        """
        发送测试通知邮件
        
        用于验证邮件配置是否正确。
        
        Args:
            config: FeedbackNotificationConfig instance
            test_email: 测试邮箱地址
            
        Returns:
            dict: 发送结果
        """
        try:
            # 直接调用 Celery 任务（同步执行以获取结果）
            result = send_test_feedback_notification.apply(
                args=[config.id, test_email]
            )
            return result.get(timeout=30)
        except Exception as e:
            logger.error(f"Failed to send test notification: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
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
            
            <p>Software: {software_name} {application_version}</p>
            
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

Software: {software_name} {application_version}

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
                'application_version': 'Software version',
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
        
        # New feedback notification template
        templates['new_feedback'] = EmailTemplate.objects.create(
            tenant=tenant,
            name="New Feedback Notification",
            template_type='new_feedback',
            subject="[{application_name}] 新反馈: {feedback_title}",
            body_html="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .info-box { background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }
        .label { font-weight: bold; color: #666; }
        .button { display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📬 新反馈通知</h1>
        </div>
        <div class="content">
            <p>您好，</p>
            <p><strong>{application_name}</strong> 收到了一条新的用户反馈：</p>
            
            <div class="info-box">
                <p><span class="label">标题：</span>{feedback_title}</p>
                <p><span class="label">类型：</span>{feedback_type}</p>
                <p><span class="label">优先级：</span>{priority}</p>
                <p><span class="label">提交者：</span>{contact_name} ({contact_email})</p>
                <p><span class="label">提交时间：</span>{submitted_at}</p>
            </div>
            
            <div class="info-box">
                <p><span class="label">反馈内容：</span></p>
                <p>{feedback_description}</p>
            </div>
            
            <p style="text-align: center; margin-top: 20px;">
                <a href="{view_url}" class="button">查看详情</a>
            </p>
        </div>
        <div class="footer">
            <p>此邮件由系统自动发送，请勿直接回复。</p>
            <p>反馈 ID: #{feedback_id}</p>
        </div>
    </div>
</body>
</html>
            """,
            body_text="""
新反馈通知

{application_name} 收到了一条新的用户反馈：

标题：{feedback_title}
类型：{feedback_type}
优先级：{priority}
提交者：{contact_name} ({contact_email})
提交时间：{submitted_at}

反馈内容：
{feedback_description}

查看详情：{view_url}

反馈 ID: #{feedback_id}
            """,
            variables={
                'application_name': 'Application name',
                'feedback_title': 'Feedback title',
                'feedback_description': 'Feedback description',
                'feedback_type': 'Feedback type',
                'priority': 'Priority',
                'contact_name': 'Submitter name',
                'contact_email': 'Submitter email',
                'submitted_at': 'Submission time',
                'feedback_id': 'Feedback ID',
                'view_url': 'URL to view feedback'
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
        if feedback.application:
            feedback.application.update_statistics()
        
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
        if feedback.application:
            feedback.application.update_statistics()
        
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
