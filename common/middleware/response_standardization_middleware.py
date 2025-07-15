"""
统一响应格式中间件
确保所有API响应遵循一致的格式规范
"""
import json
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework.response import Response
from rest_framework.status import is_success

class ResponseStandardizationMiddleware(MiddlewareMixin):
    """
    统一响应格式中间件
    确保所有API响应都符合标准格式:
    {
        "success": true/false,
        "code": 2000,
        "message": "操作成功/失败信息",
        "data": { ... }
    }
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
    
    def _should_process(self, request, response):
        """
        判断是否应该处理该响应
        """
        # 只处理API请求
        if not request.path.startswith('/api/'):
            return False
        
        # 不处理静态资源
        if request.path.startswith(('/static/', '/media/')):
            return False
            
        # 不处理API文档
        if request.path.startswith(('/api/v1/schema/', '/api/v1/docs/', '/api/v1/redoc/')):
            return False
            
        # 已经是标准格式的响应不再处理
        if hasattr(response, 'data') and isinstance(response.data, dict):
            if all(k in response.data for k in ['success', 'code', 'message', 'data']):
                return False
                
        # 只处理JSON或REST响应
        if isinstance(response, (JsonResponse, Response)):
            return True
            
        if hasattr(response, 'content_type') and response.content_type == 'application/json':
            return True
            
        return False
    
    def _get_business_code(self, status_code):
        """获取业务状态码"""
        if is_success(status_code):
            return 2000  # 成功
        elif status_code == 401:
            return 4001  # 认证失败
        elif status_code == 403:
            return 4003  # 权限不足
        elif status_code == 404:
            return 4004  # 资源不存在
        elif 400 <= status_code < 500:
            return 4000  # 客户端错误
        elif 500 <= status_code < 600:
            return 5000  # 服务器错误
        else:
            return status_code
    
    def _get_default_message(self, status_code):
        """获取默认消息"""
        if is_success(status_code):
            return '操作成功'
        elif status_code == 401:
            return '认证失败'
        elif status_code == 403:
            return '权限不足'
        elif status_code == 404:
            return '资源不存在'
        elif 400 <= status_code < 500:
            return '请求参数错误'
        elif 500 <= status_code < 600:
            return '服务器内部错误'
        else:
            return '未知错误'
    
    def process_response(self, request, response):
        """
        处理响应
        将非标准格式的API响应转换为标准格式
        """
        if not self._should_process(request, response):
            return response
            
        # 获取原始响应数据
        original_data = None
        if isinstance(response, Response):
            original_data = response.data
        elif isinstance(response, JsonResponse):
            original_data = json.loads(response.content.decode('utf-8'))
        elif hasattr(response, 'content'):
            try:
                original_data = json.loads(response.content.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return response  # 无法解析的内容不处理
                
        if original_data is None:
            return response
            
        # 构建标准响应
        is_successful = is_success(response.status_code)
        
        # 检查是否是分页结果
        if isinstance(original_data, dict) and 'count' in original_data and 'results' in original_data:
            data = original_data
            message = self._get_default_message(response.status_code)
        else:
            data = original_data
            message = self._get_default_message(response.status_code)
        
        # 处理已经部分符合标准的响应
        if isinstance(original_data, dict):
            if 'message' in original_data:
                message = original_data.pop('message')
            elif 'detail' in original_data:
                message = original_data.pop('detail')
                
            if 'data' in original_data:
                data = original_data.pop('data')
        
        standard_data = {
            'success': is_successful,
            'code': self._get_business_code(response.status_code),
            'message': message,
            'data': data
        }
        
        # 创建新的响应
        if isinstance(response, Response):
            response.data = standard_data
            return response
        else:
            new_content = json.dumps(standard_data, ensure_ascii=False).encode('utf-8')
            new_response = HttpResponse(
                content=new_content,
                content_type='application/json',
                status=response.status_code
            )
            
            # 复制原始响应的headers
            for header, value in response.items():
                if header.lower() != 'content-length':  # 忽略内容长度，因为已更改
                    new_response[header] = value
                    
            return new_response
