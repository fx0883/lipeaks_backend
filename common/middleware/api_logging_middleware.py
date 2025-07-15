"""
API日志记录中间件
用于自动记录API请求的日志信息
"""
import json
import logging
import time
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve

logger = logging.getLogger(__name__)

class APILoggingMiddleware(MiddlewareMixin):
    """
    API日志记录中间件
    自动记录API请求的时间、路径、方法、状态码等信息
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
    
    def _should_log(self, request):
        """
        判断是否应该记录该请求的日志
        
        Args:
            request: HTTP请求对象
        
        Returns:
            布尔值，指示是否应该记录日志
        """
        # 只记录API请求的日志
        if not request.path.startswith('/api/'):
            return False
        
        # 不记录静态文件请求
        if request.path.startswith(('/static/', '/media/')):
            return False
        
        # 不记录API文档请求
        if request.path.startswith(('/api/v1/schema/', '/api/v1/docs/', '/api/v1/redoc/')):
            return False
        
        return True
    
    def process_request(self, request):
        """
        处理请求前的操作
        
        Args:
            request: HTTP请求对象
        """
        if not self._should_log(request):
            return None
        
        # 记录请求开始时间
        request.api_log_start_time = time.time()
        
        # 记录请求信息
        request.api_log_data = {
            'request_method': request.method,
            'request_path': request.path,
            'query_params': dict(request.GET.items()),
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # 尝试获取请求体
        try:
            if request.body and request.content_type == 'application/json':
                request.api_log_data['request_body'] = json.loads(request.body)
            else:
                request.api_log_data['request_body'] = None
        except Exception as e:
            logger.warning(f"无法解析请求体: {str(e)}")
            request.api_log_data['request_body'] = None
        
        return None
    
    def process_response(self, request, response):
        """
        处理响应前的操作
        
        Args:
            request: HTTP请求对象
            response: HTTP响应对象
        
        Returns:
            HTTP响应对象
        """
        if not hasattr(request, 'api_log_start_time') or not self._should_log(request):
            return response
        
        # 计算响应时间
        response_time = int((time.time() - request.api_log_start_time) * 1000)  # 毫秒
        
        # 获取状态类型
        status_type = 'success' if 200 <= response.status_code < 400 else 'error'
        
        # 获取错误信息
        error_message = None
        if status_type == 'error' and hasattr(response, 'data') and response.data:
            try:
                if isinstance(response.data, dict) and 'message' in response.data:
                    error_message = response.data['message']
                elif isinstance(response.data, str):
                    error_message = response.data
            except Exception as e:
                logger.warning(f"无法获取错误信息: {str(e)}")
        
        # 构造日志数据
        log_data = {
            **request.api_log_data,
            'status_code': response.status_code,
            'response_time': response_time,
            'status_type': status_type,
            'error_message': error_message,
        }
        
        # 获取当前用户和租户
        if hasattr(request, 'user') and request.user.is_authenticated:
            log_data['user'] = request.user
            log_data['tenant'] = getattr(request.user, 'tenant', None)
        
        # 异步记录日志到数据库
        self._save_log(log_data)
        
        # 打印日志
        log_message = (
            f"{log_data['request_method']} {log_data['request_path']} - "
            f"{log_data['status_code']} - {log_data['response_time']}ms"
        )
        
        if status_type == 'success':
            logger.info(log_message)
        else:
            logger.warning(f"{log_message} - {error_message}")
        
        return response
    
    def _get_client_ip(self, request):
        """
        获取客户端IP地址
        
        Args:
            request: HTTP请求对象
        
        Returns:
            客户端IP地址
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # 可能有多个IP，取第一个
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _save_log(self, log_data):
        """
        保存日志到数据库
        
        Args:
            log_data: 日志数据
        """
        try:
            # 导入在此处导入以避免循环导入
            from common.models import APILog
            
            user = log_data.pop('user', None)
            tenant = log_data.pop('tenant', None)
            
            # 创建API日志记录
            APILog.objects.create(
                user=user,
                tenant=tenant,
                **log_data
            )
        except Exception as e:
            logger.exception(f"保存API日志失败: {str(e)}") 