"""
Feedback System Middleware

This module contains middleware for monitoring and fallback mechanisms.
"""

import logging
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from .utils import RedisHealthChecker

logger = logging.getLogger(__name__)


class RedisMonitoringMiddleware(MiddlewareMixin):
    """
    Redis监控中间件
    
    定期检查Redis连接状态，并在响应头中添加系统状态信息
    """
    
    CACHE_KEY = 'feedback_system_redis_status'
    CHECK_INTERVAL = 60  # 60秒检查一次
    
    def process_request(self, request):
        """
        在请求处理前检查Redis状态
        """
        # 只在特定路径下检查
        if not request.path.startswith('/api/v1/feedbacks/'):
            return None
        
        # 从缓存获取上次检查结果（避免每次请求都检查）
        try:
            cached_status = cache.get(self.CACHE_KEY)
            
            if cached_status is None:
                # 执行检查
                is_available = RedisHealthChecker.is_redis_available()
                
                # 缓存结果
                try:
                    cache.set(self.CACHE_KEY, is_available, self.CHECK_INTERVAL)
                except:
                    # 如果缓存失败（Redis不可用），直接设置请求属性
                    pass
                
                request.redis_available = is_available
            else:
                request.redis_available = cached_status
                
        except Exception as e:
            logger.warning(f"Redis status check failed: {str(e)}")
            request.redis_available = False
        
        return None
    
    def process_response(self, request, response):
        """
        在响应中添加系统状态头
        """
        # 只在API路径下添加
        if request.path.startswith('/api/v1/feedbacks/'):
            redis_available = getattr(request, 'redis_available', False)
            
            # 添加自定义响应头
            response['X-System-Mode'] = 'async' if redis_available else 'sync'
            response['X-Redis-Status'] = 'available' if redis_available else 'unavailable'
            
            # 如果Redis不可用，添加警告头
            if not redis_available:
                response['X-System-Warning'] = 'Redis unavailable, running in synchronous mode'
        
        return response


class EmailFallbackMiddleware(MiddlewareMixin):
    """
    邮件降级中间件
    
    在Redis不可用时，在响应中添加提示信息
    """
    
    def process_response(self, request, response):
        """
        如果在同步模式下处理了邮件任务，添加提示
        """
        if hasattr(request, 'email_sent_sync'):
            # 标记此请求中有邮件同步发送
            response['X-Email-Mode'] = 'synchronous'
            response['X-Email-Latency-Warning'] = 'true'
            
            logger.info(f"Email sent synchronously during request to {request.path}")
        
        return response
