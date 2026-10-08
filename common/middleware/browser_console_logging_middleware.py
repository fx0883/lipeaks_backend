"""
浏览器控制台日志中间件
将API请求处理过程中的日志输出到浏览器控制台，方便前端调试
"""
import json
import logging
import threading
import time
import traceback
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# 创建线程本地存储，确保并发请求下日志互不干扰
_log_thread_local = threading.local()

def _get_thread_logs():
    return getattr(_log_thread_local, 'logs', None)

def _set_thread_logs(logs):
    _log_thread_local.logs = logs

def _clear_thread_logs():
    if hasattr(_log_thread_local, 'logs'):
        del _log_thread_local.logs


class BrowserConsoleLoggingMiddleware(MiddlewareMixin):
    """
    浏览器控制台日志中间件
    
    将API请求处理过程中的日志输出到浏览器控制台，方便前端调试
    严格只在DEBUG模式下生效，通过在响应头中添加特殊的X-Debug-Log头来传递日志信息
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
        # 创建线程安全的自定义日志处理器
        self.handler = BrowserConsoleLogHandler()
        self.handler.setLevel(logging.DEBUG)
        
        # 添加处理器到根日志记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(self.handler)
        
        logger.info("浏览器控制台日志中间件已初始化 (线程安全版)")
    
    def _should_log_to_browser(self, request):
        """
        判断是否应该将日志输出到浏览器控制台
        
        安全约束：
        1. 仅在 settings.DEBUG 为 True 时允许；
        2. 仅处理 /api/ 开头的请求；
        3. 请求头包含 X-Debug-Log: true。
        """
        if not getattr(settings, 'DEBUG', False):
            return False
        
        if not request.path.startswith('/api/'):
            return False
        
        return request.headers.get('X-Debug-Log') == 'true'
    
    def process_request(self, request):
        """
        处理请求前的操作
        """
        # 非DEBUG模式直接跳过
        if not getattr(settings, 'DEBUG', False):
            request.should_log_to_browser = False
            _clear_thread_logs()
            return None

        request.should_log_to_browser = self._should_log_to_browser(request)
        
        if request.should_log_to_browser:
            # 初始化当前线程的日志列表
            thread_logs = []
            _set_thread_logs(thread_logs)
            request._browser_logs = thread_logs
            
            # 记录请求信息
            user_info = "未登录"
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = f"{request.user.username} (ID: {request.user.id})"
                if hasattr(request.user, 'is_super_admin'):
                    user_info += f", 超级管理员: {request.user.is_super_admin}"
                if hasattr(request.user, 'is_admin'):
                    user_info += f", 管理员: {request.user.is_admin}"
                if hasattr(request.user, 'tenant') and request.user.tenant:
                    user_info += f", 租户: {request.user.tenant.name} (ID: {request.user.tenant.id})"
            
            # 安全脱敏请求头（避免在控制台暴露真实 Authorization / Cookie）
            safe_headers = {}
            for k, v in request.headers.items():
                if k.lower() in ('authorization', 'cookie', 'set-cookie', 'x-api-key', 'proxy-authorization'):
                    safe_headers[k] = '******'
                else:
                    safe_headers[k] = v

            thread_logs.append({
                'level': 'info',
                'message': f"API请求: {request.method} {request.path}",
                'timestamp': time.time(),
                'user': user_info,
                'headers': safe_headers
            })
        else:
            _clear_thread_logs()
        
        return None
    
    def process_response(self, request, response):
        """
        处理响应前的操作
        """
        # 如果不需要记录日志，直接返回响应并清理线程
        if not getattr(settings, 'DEBUG', False) or not getattr(request, 'should_log_to_browser', False):
            _clear_thread_logs()
            return response
        
        logs = _get_thread_logs() or []
        
        # 添加请求处理结果日志
        status_level = 'info' if response.status_code < 400 else 'error'
        logs.append({
            'level': status_level,
            'message': f"API响应: 状态码 {response.status_code}",
            'timestamp': time.time(),
            'status_code': response.status_code
        })
        
        # 如果是错误响应，尝试提取错误信息
        if response.status_code >= 400:
            try:
                if 'application/json' in response.get('Content-Type', ''):
                    error_data = json.loads(response.content.decode('utf-8'))
                    if isinstance(error_data, dict) and 'detail' in error_data:
                        logs.append({
                            'level': 'error',
                            'message': f"错误详情: {error_data['detail']}",
                            'timestamp': time.time(),
                            'error_detail': error_data['detail']
                        })
                elif 'text/html' in response.get('Content-Type', ''):
                    content = response.content.decode('utf-8')
                    import re
                    title_match = re.search(r'<title>(.*?)</title>', content)
                    if title_match:
                        error_title = title_match.group(1).strip()
                        logs.append({
                            'level': 'error',
                            'message': f"错误页面: {error_title}",
                            'timestamp': time.time(),
                            'error_title': error_title
                        })
            except Exception as e:
                logger.error(f"提取错误信息失败: {str(e)}")
        
        # 如果是JSON响应，将日志添加到响应中
        if hasattr(response, 'content') and 'application/json' in response.get('Content-Type', ''):
            try:
                original_content = json.loads(response.content.decode('utf-8'))
                if isinstance(original_content, dict):
                    original_content['debug_logs'] = logs
                    response.content = json.dumps(original_content).encode('utf-8')
                    response['Content-Length'] = len(response.content)
            except Exception as e:
                logger.error(f"将日志添加到响应内容时出错: {str(e)}")
        
        # 添加响应头
        try:
            logs_json = json.dumps(logs)
            if len(logs_json) > 1000:
                logs_json = logs_json[:997] + '...'
            response['X-Debug-Logs-JSON'] = logs_json
        except Exception as e:
            logger.error(f"添加日志到响应头时出错: {str(e)}")
        
        response['X-Debug-Log-Count'] = len(logs)
        if response.status_code >= 400 or 'application/json' not in response.get('Content-Type', ''):
            response['X-Debug-Log-Available'] = 'true'
        
        # 清理当前线程日志上下文
        _clear_thread_logs()
        return response

    def process_exception(self, request, exception):
        """
        发生未捕获异常时记录到日志中
        """
        if getattr(settings, 'DEBUG', False) and getattr(request, 'should_log_to_browser', False):
            logs = _get_thread_logs()
            if logs is not None:
                logs.append({
                    'level': 'error',
                    'message': f"未捕获异常: {str(exception)}",
                    'timestamp': time.time(),
                    'exception': {
                        'type': type(exception).__name__,
                        'message': str(exception),
                        'traceback': traceback.format_exc()
                    }
                })
        return None


class BrowserConsoleLogHandler(logging.Handler):
    """
    自定义日志处理器，将日志安全存储到当前线程绑定的logs列表中
    """
    
    def emit(self, record):
        """
        发出日志记录
        """
        logs = _get_thread_logs()
        if logs is None:
            # 当前线程未开启浏览器控制台日志
            return
            
        try:
            log_entry = {
                'level': record.levelname.lower(),
                'message': self.format(record),
                'timestamp': time.time(),
                'logger': record.name,
                'module': record.module,
                'line': record.lineno
            }
            
            if record.exc_info:
                log_entry['exception'] = {
                    'type': record.exc_info[0].__name__,
                    'message': str(record.exc_info[1]),
                    'traceback': traceback.format_exception(*record.exc_info)
                }
            
            logs.append(log_entry)
        except Exception:
            # 确保日志处理器自身绝对不抛异常
            pass