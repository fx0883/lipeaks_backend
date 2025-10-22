"""
Feedback System Utilities

This module contains utility functions including Redis health check and fallback mechanisms.
"""

import logging
from django.conf import settings
from django.core.cache import cache
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


class RedisHealthChecker:
    """Redis连接健康检查"""
    
    @staticmethod
    def is_redis_available() -> bool:
        """
        检查Redis是否可用
        
        Returns:
            bool: Redis可用返回True，否则返回False
        """
        try:
            # 尝试连接Redis
            from redis import Redis
            from django.conf import settings
            
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
        try:
            # 首先尝试异步执行
            if RedisHealthChecker.is_redis_available():
                logger.info(f"异步执行任务: {task_func.__name__}")
                result = task_func.delay(*args, **kwargs)
                return {'mode': 'async', 'task_id': result.id}
            else:
                raise Exception("Redis not available")
                
        except Exception as e:
            logger.warning(f"异步执行失败: {str(e)}")
            
            if fallback_to_sync:
                # 降级到同步执行
                logger.info(f"降级到同步执行: {task_func.__name__}")
                try:
                    # 直接调用任务函数（不通过Celery）
                    result = task_func(*args, **kwargs)
                    return {'mode': 'sync', 'result': result}
                except Exception as sync_error:
                    logger.error(f"同步执行也失败: {str(sync_error)}")
                    return {'mode': 'failed', 'error': str(sync_error)}
            else:
                logger.error(f"任务执行失败，未启用降级: {task_func.__name__}")
                return {'mode': 'failed', 'error': str(e)}


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

