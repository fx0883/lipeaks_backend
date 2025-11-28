"""
Feedback System Utilities

This module contains utility functions including Redis health check and fallback mechanisms.
"""

import logging
from django.conf import settings
from django.core.cache import cache
from typing import Optional, Callable, Any
import re

logger = logging.getLogger(__name__)


class EmailValidator:
    """邮件地址验证工具"""
    
    # 更严格的邮件地址验证正则表达式
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # 常见的无效邮件地址模式
    INVALID_PATTERNS = [
        r'.*@example\.com$',           # 测试邮箱
        r'.*@test\.com$',              # 测试邮箱
        r'.*@localhost$',              # 本地测试
        r'^test@.*',                   # test开头
        r'^demo@.*',                   # demo开头
        r'.*@tempmail\..*',            # 临时邮箱
        r'.*@10minutemail\..*',        # 临时邮箱
        r'.*@guerrillamail\..*',       # 临时邮箱
        r'noreply@.*',                 # 无回复邮箱
        r'no-reply@.*',                # 无回复邮箱
    ]
    
    @classmethod
    def is_valid_email(cls, email: str) -> bool:
        """
        验证邮件地址是否有效
        
        Args:
            email: 要验证的邮件地址
            
        Returns:
            bool: 是否为有效邮件地址
        """
        if not email or not isinstance(email, str):
            return False
        
        # 去除前后空格
        email = email.strip().lower()
        
        if not email:
            return False
        
        # 基本格式验证
        if not cls.EMAIL_REGEX.match(email):
            return False
        
        # 检查是否包含无效模式
        for pattern in cls.INVALID_PATTERNS:
            if re.match(pattern, email, re.IGNORECASE):
                logger.warning(f"Email {email} matches invalid pattern: {pattern}")
                return False
        
        # 检查长度限制
        if len(email) > 254:  # RFC 5321 限制
            return False
        
        # 检查本地部分长度（@之前的部分）
        local_part = email.split('@')[0]
        if len(local_part) > 64:  # RFC 5321 限制
            return False
        
        return True
    
    @classmethod
    def validate_and_log(cls, email: str, context: str = "") -> bool:
        """
        验证邮件地址并记录日志
        
        Args:
            email: 要验证的邮件地址
            context: 上下文信息，用于日志记录
            
        Returns:
            bool: 是否为有效邮件地址
        """
        is_valid = cls.is_valid_email(email)
        
        if not is_valid:
            logger.warning(f"Invalid email address detected{context}: '{email}' - skipping email send")
        else:
            logger.debug(f"Email address validated{context}: '{email}'")
        
        return is_valid


class RedisHealthChecker:
    """Redis连接健康检查"""
    
    @staticmethod
    def is_celery_enabled() -> bool:
        """
        检查 Celery 是否启用
        
        Returns:
            bool: Celery 启用返回 True，否则返回 False
        """
        return getattr(settings, 'CELERY_ENABLED', True)
    
    @staticmethod
    def is_redis_available() -> bool:
        """
        检查Redis是否可用
        
        Returns:
            bool: Redis可用返回True，否则返回False
        """
        # 如果 Celery 被禁用，直接返回 False
        if not RedisHealthChecker.is_celery_enabled():
            logger.debug("Celery 已禁用，跳过 Redis 检查")
            return False
        
        try:
            # 尝试连接Redis
            from redis import Redis
            
            # 从Celery配置中获取Redis URL
            redis_url = getattr(settings, 'CELERY_BROKER_URL', None)
            
            if not redis_url or redis_url == 'django-db':
                # 使用数据库作为broker，不需要Redis
                return False
            
            # 尝试连接
            r = Redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            logger.debug("Redis连接正常")
            return True
            
        except ImportError:
            logger.warning("Redis 库未安装，将使用同步模式")
            return False
        except Exception as e:
            logger.warning(f"Redis连接失败: {str(e)}")
            return False
    
    @staticmethod
    def get_redis_status() -> dict:
        """
        获取Redis详细状态
        
        Returns:
            dict: Redis状态信息
        """
        try:
            from redis import Redis
            
            redis_url = getattr(settings, 'CELERY_BROKER_URL', None)
            if not redis_url or redis_url == 'django-db':
                return {
                    'available': False,
                    'mode': 'database',
                    'message': 'Using database as broker'
                }
            
            r = Redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            
            # 获取Redis信息
            info = r.info()
            
            return {
                'available': True,
                'mode': 'redis',
                'version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
                'uptime_days': info.get('uptime_in_days', 0)
            }
            
        except Exception as e:
            return {
                'available': False,
                'mode': 'redis',
                'error': str(e),
                'message': 'Redis connection failed'
            }


class TaskExecutor:
    """
    任务执行器 - 支持异步/同步自动降级
    
    当 CELERY_ENABLED=False 或 Redis 不可用时，自动降级到同步执行。
    对于 bind=True 的 Celery 任务，使用 task.run() 方法正确调用。
    """
    
    @staticmethod
    def execute_task(
        task_func: Callable,
        *args,
        fallback_to_sync: bool = True,
        **kwargs
    ) -> Any:
        """
        执行任务，自动降级到同步执行
        
        Args:
            task_func: Celery任务函数
            *args: 任务参数
            fallback_to_sync: 是否在Redis不可用时降级到同步执行
            **kwargs: 任务关键字参数
            
        Returns:
            任务执行结果或任务ID
        """
        task_name = getattr(task_func, '__name__', str(task_func))
        
        # 检查是否应该使用异步模式
        use_async = RedisHealthChecker.is_celery_enabled() and RedisHealthChecker.is_redis_available()
        
        if use_async:
            try:
                logger.info(f"异步执行任务: {task_name}")
                result = task_func.delay(*args, **kwargs)
                return {'mode': 'async', 'task_id': result.id}
            except Exception as e:
                logger.warning(f"异步执行失败: {str(e)}")
                if not fallback_to_sync:
                    return {'mode': 'failed', 'error': str(e)}
                # 继续尝试同步执行
        
        # 同步执行（Celery 禁用、Redis 不可用、或异步失败后降级）
        if fallback_to_sync or not use_async:
            logger.info(f"同步执行任务: {task_name}")
            try:
                # 对于 Celery 任务，使用 .run() 方法正确调用（处理 bind=True 的情况）
                if hasattr(task_func, 'run'):
                    result = task_func.run(*args, **kwargs)
                else:
                    result = task_func(*args, **kwargs)
                return {'mode': 'sync', 'result': result}
            except Exception as sync_error:
                logger.error(f"同步执行失败: {str(sync_error)}")
                return {'mode': 'failed', 'error': str(sync_error)}
        
        return {'mode': 'failed', 'error': 'No execution mode available'}


def safe_async_task(task_func: Callable, *args, **kwargs):
    """
    安全的异步任务执行装饰器
    
    自动处理Redis不可用的情况，降级到同步执行
    """
    return TaskExecutor.execute_task(task_func, *args, **kwargs)


class EmailFallbackHandler:
    """邮件发送降级处理器"""
    
    @staticmethod
    def send_email_with_fallback(
        subject: str,
        message: str,
        recipient_list: list,
        html_message: str = None,
        from_email: str = None
    ) -> dict:
        """
        发送邮件，支持降级处理
        
        Args:
            subject: 邮件主题
            message: 纯文本内容
            recipient_list: 收件人列表
            html_message: HTML内容
            from_email: 发件人
            
        Returns:
            dict: 发送结果
        """
        from django.core.mail import send_mail
        from django.conf import settings
        
        try:
            if from_email is None:
                from_email = settings.DEFAULT_FROM_EMAIL
            
            # 尝试发送邮件
            count = send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False
            )
            
            return {
                'success': True,
                'count': count,
                'mode': 'direct'
            }
            
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            
            # 记录到数据库，稍后重试
            try:
                from .models import FeedbackEmailLog
                FeedbackEmailLog.objects.create(
                    email_type='reply',
                    recipient=recipient_list[0] if recipient_list else '',
                    subject=subject,
                    content=html_message or message,
                    status='failed',
                    error_message=str(e)
                )
            except:
                pass
            
            return {
                'success': False,
                'error': str(e),
                'mode': 'failed'
            }

