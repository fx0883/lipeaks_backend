"""
浏览器控制台日志中间件
将API请求处理过程中的日志输出到浏览器控制台，方便前端调试
"""
import json
import logging
import time
import traceback
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class BrowserConsoleLoggingMiddleware(MiddlewareMixin):
    """
    浏览器控制台日志中间件
    
    将API请求处理过程中的日志输出到浏览器控制台，方便前端调试
    只在DEBUG模式下生效，通过在响应头中添加特殊的X-Debug-Log头来传递日志信息
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        self.logs = []
        
        # 创建一个自定义的日志处理器，将日志存储到self.logs中
        self.handler = BrowserConsoleLogHandler(self)
        
        # 设置日志处理器的级别
        self.handler.setLevel(logging.DEBUG)
        
        # 添加处理器到根日志记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(self.handler)
        
        logger.info("浏览器控制台日志中间件已初始化")
    
    def _should_log_to_browser(self, request):
        """
        判断是否应该将日志输出到浏览器控制台
        
        Args:
            request: HTTP请求对象
        
        Returns:
            布尔值，指示是否应该输出日志
        """
        # 只处理API请求
        if not request.path.startswith('/api/'):
            return False
        
        # 检查请求头中是否包含X-Debug-Log
        return request.headers.get('X-Debug-Log') == 'true'
    
    def process_request(self, request):
        """
        处理请求前的操作
        
        Args:
            request: HTTP请求对象
        """
        logger.info(f"[进入中间件] BrowserConsoleLoggingMiddleware - 处理请求: {request.path}")
        # 清空之前的日志
        self.logs = []
        
        # 在请求对象上设置标志，表示是否应该记录日志
        request.should_log_to_browser = self._should_log_to_browser(request)
        
        if request.should_log_to_browser:
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
            
            self.logs.append({
                'level': 'info',
                'message': f"API请求: {request.method} {request.path}",
                'timestamp': time.time(),
                'user': user_info,
                'headers': dict(request.headers.items())
            })
        
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
        # 如果不需要记录日志，直接返回响应
        if not hasattr(request, 'should_log_to_browser') or not request.should_log_to_browser:
            return response
        
        # 添加请求处理结果日志
        status_level = 'info' if response.status_code < 400 else 'error'
        self.logs.append({
            'level': status_level,
            'message': f"API响应: 状态码 {response.status_code}",
            'timestamp': time.time(),
            'status_code': response.status_code
        })
        
        # 如果是错误响应，尝试提取错误信息
        if response.status_code >= 400:
            try:
                # 尝试解析JSON错误响应
                if 'application/json' in response.get('Content-Type', ''):
                    error_data = json.loads(response.content.decode('utf-8'))
                    if isinstance(error_data, dict) and 'detail' in error_data:
                        self.logs.append({
                            'level': 'error',
                            'message': f"错误详情: {error_data['detail']}",
                            'timestamp': time.time(),
                            'error_detail': error_data['detail']
                        })
                # 如果是HTML错误页面，尝试提取错误标题
                elif 'text/html' in response.get('Content-Type', ''):
                    content = response.content.decode('utf-8')
                    import re
                    title_match = re.search(r'<title>(.*?)</title>', content)
                    if title_match:
                        error_title = title_match.group(1).strip()
                        self.logs.append({
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
                # 解析原始JSON响应
                original_content = json.loads(response.content.decode('utf-8'))
                
                # 添加日志信息
                if isinstance(original_content, dict):
                    # 如果原始内容是字典，添加debug_logs字段
                    original_content['debug_logs'] = self.logs
                    
                    # 重新编码响应
                    response.content = json.dumps(original_content).encode('utf-8')
                    
                    # 更新Content-Length头
                    response['Content-Length'] = len(response.content)
            except Exception as e:
                logger.error(f"添加浏览器日志到响应时出错: {str(e)}")
                # 尝试记录错误响应内容
                try:
                    error_content = response.content.decode('utf-8')
                    self.logs.append({
                        'level': 'error',
                        'message': f"解析响应内容失败: {str(e)}",
                        'timestamp': time.time(),
                        'response_content': error_content[:500]  # 只记录前500个字符，避免日志过大
                    })
                except Exception:
                    pass
        # 对于HTML错误响应，添加日志到响应头
        elif hasattr(response, 'content') and 'text/html' in response.get('Content-Type', '') and response.status_code >= 400:
            # 将日志序列化为JSON字符串，并添加到响应头
            try:
                logs_json = json.dumps(self.logs)
                # 由于HTTP头不能太长，我们只取前1000个字符
                if len(logs_json) > 1000:
                    logs_json = logs_json[:997] + '...'
                response['X-Debug-Logs-JSON'] = logs_json
            except Exception as e:
                logger.error(f"添加日志到响应头时出错: {str(e)}")
        
        # 添加X-Debug-Log-Count头，表示日志数量
        response['X-Debug-Log-Count'] = len(self.logs)
        
        # 对于非JSON响应或错误响应，添加X-Debug-Log-Available头
        if response.status_code >= 400 or 'application/json' not in response.get('Content-Type', ''):
            response['X-Debug-Log-Available'] = 'true'
        
        return response

class BrowserConsoleLogHandler(logging.Handler):
    """
    自定义日志处理器，将日志存储到中间件的logs列表中
    """
    
    def __init__(self, middleware):
        super().__init__()
        self.middleware = middleware
    
    def emit(self, record):
        """
        发出日志记录
        
        Args:
            record: 日志记录对象
        """
        # 只有在请求处理过程中才记录日志
        try:
            log_entry = {
                'level': record.levelname.lower(),
                'message': self.format(record),
                'timestamp': time.time(),
                'logger': record.name,
                'module': record.module,
                'line': record.lineno
            }
            
            # 如果有异常信息，添加到日志中
            if record.exc_info:
                log_entry['exception'] = {
                    'type': record.exc_info[0].__name__,
                    'message': str(record.exc_info[1]),
                    'traceback': traceback.format_exception(*record.exc_info)
                }
            
            self.middleware.logs.append(log_entry)
        except Exception as e:
            # 确保日志处理器不会引发异常
            pass 