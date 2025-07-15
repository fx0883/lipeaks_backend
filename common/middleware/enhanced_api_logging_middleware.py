"""
增强的API日志中间件
提供更全面的API请求和响应日志记录功能
"""
import json
import logging
import time
import traceback
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.db.models import F

logger = logging.getLogger(__name__)

class EnhancedAPILoggingMiddleware(MiddlewareMixin):
    """
    增强型API日志中间件
    记录API请求和响应的详细信息，并提供性能监控功能
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
            
        # 不记录健康检查请求
        if request.path.startswith('/api/v1/health/'):
            return False
        
        return True
    
    def _get_request_body(self, request):
        """
        安全地获取请求体内容
        
        Args:
            request: HTTP请求对象
        
        Returns:
            字典或None: 请求体内容
        """
        if not request.body:
            return None
            
        content_type = request.content_type.lower() if request.content_type else ''
        
        try:
            if 'application/json' in content_type:
                return json.loads(request.body.decode('utf-8'))
            elif 'multipart/form-data' in content_type:
                # 不记录文件内容，只记录文件名
                files_info = {}
                if request.FILES:
                    for key, file_obj in request.FILES.items():
                        files_info[key] = {
                            'name': file_obj.name,
                            'size': file_obj.size,
                            'content_type': file_obj.content_type
                        }
                return {
                    'form': dict(request.POST.items()),
                    'files': files_info
                }
            elif 'application/x-www-form-urlencoded' in content_type:
                return dict(request.POST.items())
            else:
                # 其他内容类型，尝试记录为字符串
                return {'raw': request.body.decode('utf-8', errors='replace')[:1000]}
        except Exception as e:
            logger.warning(f"无法解析请求体: {str(e)}")
            return {'error': f"无法解析请求体: {str(e)}"}
    
    def _get_response_body(self, response):
        """
        安全地获取响应体内容
        
        Args:
            response: HTTP响应对象
        
        Returns:
            字典或字符串: 响应体内容
        """
        try:
            if hasattr(response, 'data'):
                # DRF响应
                return response.data
            elif hasattr(response, 'content'):
                # 标准Django响应
                content_type = response.get('Content-Type', '')
                if content_type and 'application/json' in content_type.lower():
                    return json.loads(response.content.decode('utf-8'))
                else:
                    # 非JSON响应，返回内容类型
                    return {'content_type': content_type}
            return None
        except Exception as e:
            logger.warning(f"无法解析响应体: {str(e)}")
            return {'error': f"无法解析响应体: {str(e)}"}
    
    def _get_client_ip(self, request):
        """
        获取客户端IP地址
        
        Args:
            request: HTTP请求对象
        
        Returns:
            字符串: 客户端IP地址
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _get_user_info(self, request):
        """
        获取用户信息
        
        Args:
            request: HTTP请求对象
            
        Returns:
            字典: 用户信息
        """
        user_info = {
            'authenticated': False,
            'id': None,
            'username': None,
            'is_admin': False,
            'is_super_admin': False,
            'tenant_id': None
        }
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info.update({
                'authenticated': True,
                'id': request.user.id,
                'username': request.user.username,
                'is_admin': getattr(request.user, 'is_admin', False),
                'is_super_admin': getattr(request.user, 'is_super_admin', False),
            })
            
            if hasattr(request.user, 'tenant') and request.user.tenant:
                user_info['tenant_id'] = request.user.tenant.id
                
        return user_info
    
    def _get_view_info(self, request):
        """
        获取视图信息
        
        Args:
            request: HTTP请求对象
            
        Returns:
            字典: 视图信息
        """
        try:
            resolver_match = resolve(request.path_info)
            return {
                'view_name': resolver_match.view_name,
                'url_name': resolver_match.url_name,
                'app_name': resolver_match.app_name,
                'namespace': resolver_match.namespace,
                'kwargs': resolver_match.kwargs
            }
        except Exception:
            return {
                'view_name': 'unknown',
                'error': 'Cannot resolve view'
            }
    
    def _save_log(self, log_data):
        """
        保存日志记录
        
        Args:
            log_data: 日志数据
            
        Returns:
            None
        """
        try:
            from common.models import APILog
            
            # 提取需要的字段来创建APILog记录
            log_entry = APILog(
                user_id=log_data.get('user_id'),
                tenant_id=log_data.get('tenant_id'),
                request_method=log_data.get('request_method'),
                request_path=log_data.get('request_path'),
                view_name=log_data.get('view_info', {}).get('view_name'),
                status_code=log_data.get('status_code'),
                response_time=log_data.get('response_time'),
                ip_address=log_data.get('ip_address'),
                user_agent=log_data.get('user_agent'),
                request_body=log_data.get('request_body'),
                query_params=log_data.get('query_params'),
                response_body=log_data.get('response_body'),
                error_message=log_data.get('error_message')
            )
            log_entry.save()
            
        except Exception as e:
            # 记录失败不应该影响正常流程
            logger.error(f"保存API日志失败: {str(e)}")
            logger.error(traceback.format_exc())
    
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
        request.api_log_start_datetime = datetime.now()
        
        # 记录请求信息
        request.api_log_data = {
            'request_method': request.method,
            'request_path': request.path,
            'query_params': dict(request.GET.items()),
            'request_body': self._get_request_body(request),
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'view_info': self._get_view_info(request),
            'timestamp': request.api_log_start_datetime.isoformat(),
        }
        
        # 记录用户信息
        user_info = self._get_user_info(request)
        request.api_log_data.update(user_info)
        
        if user_info['authenticated']:
            request.api_log_data['user_id'] = user_info['id']
            request.api_log_data['tenant_id'] = user_info['tenant_id']
        
        # 记录请求日志
        logger.info(f"API请求: {request.method} {request.path} - 用户: {user_info.get('username', '未登录')}")
        
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
        
        # 获取状态类型和错误信息
        status_code = response.status_code
        status_type = 'success' if 200 <= status_code < 400 else 'error'
        error_message = None
        
        if status_type == 'error':
            response_body = self._get_response_body(response)
            if isinstance(response_body, dict):
                error_message = response_body.get('message') or response_body.get('detail')
        
        # 构造日志数据
        log_data = {
            **request.api_log_data,
            'status_code': status_code,
            'status_type': status_type,
            'response_time': response_time,
            'error_message': error_message,
            'response_body': self._get_response_body(response),
        }
        
        # 异步记录日志到数据库
        self._save_log(log_data)
        
        # 打印日志
        log_message = (
            f"{log_data['request_method']} {log_data['request_path']} - "
            f"{status_code} - {response_time}ms"
        )
        
        if status_type == 'success':
            logger.info(log_message)
        else:
            logger.warning(f"{log_message} - {error_message or '错误'}")
        
        # 性能监控 - 记录慢请求
        if response_time > 1000:  # 超过1秒的请求
            logger.warning(f"慢请求: {log_message}")
        
        return response
        
    def process_exception(self, request, exception):
        """
        处理视图异常
        
        Args:
            request: HTTP请求对象
            exception: 异常对象
            
        Returns:
            None (让其他中间件或异常处理器处理)
        """
        if not hasattr(request, 'api_log_start_time') or not self._should_log(request):
            return None
            
        # 记录异常信息
        logger.error(f"API异常: {request.method} {request.path} - {str(exception)}")
        logger.error(traceback.format_exc())
        
        # 在请求对象上记录异常信息，便于后续处理
        request.api_log_exception = {
            'message': str(exception),
            'traceback': traceback.format_exc()
        }
        
        return None
