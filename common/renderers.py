"""
标准响应渲染器模块，确保所有API返回统一格式
"""
import json
from rest_framework.renderers import JSONRenderer
from rest_framework.utils.serializer_helpers import ReturnList, ReturnDict
from rest_framework.response import Response
from rest_framework.status import is_success, is_client_error, is_server_error

class StandardJSONRenderer(JSONRenderer):
    """
    统一响应格式的JSON渲染器
    
    将所有API响应包装为以下格式：
    {
        "success": true/false,
        "code": 2000,
        "message": "操作成功/失败信息",
        "data": { ... }
    }
    """
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        渲染响应数据为标准格式的JSON
        
        Args:
            data: 原始响应数据
            accepted_media_type: 接受的媒体类型
            renderer_context: 渲染上下文
            
        Returns:
            bytes: 渲染后的JSON字节数据
        """
        if renderer_context is None:
            renderer_context = {}
            
        response = renderer_context.get('response')
        request = renderer_context.get('request')
        
        # 已处理过的标准格式响应直接返回
        if isinstance(data, dict) and all(k in data for k in ['success', 'code', 'message', 'data']):
            return super().render(data, accepted_media_type, renderer_context)
            
        # 获取响应状态码
        status_code = response.status_code if response else 200
        
        # 标准响应结构
        standard_response = {
            'success': is_success(status_code),
            'code': self._get_business_code(status_code, data),
            'message': self._get_message(status_code, data),
            'data': self._get_response_data(data, status_code)
        }
        
        # 调用父类渲染方法
        return super().render(standard_response, accepted_media_type, renderer_context)
    
    def _get_business_code(self, status_code, data):
        """获取业务状态码"""
        # 如果响应数据中包含code字段，优先使用
        if isinstance(data, dict) and 'code' in data:
            return data['code']
            
        # 根据HTTP状态码映射业务状态码
        if is_success(status_code):
            return 2000  # 成功
        elif status_code == 401:
            return 4001  # 认证失败
        elif status_code == 403:
            return 4003  # 权限不足
        elif status_code == 404:
            return 4004  # 资源不存在
        elif is_client_error(status_code):
            return 4000  # 客户端错误
        elif is_server_error(status_code):
            return 5000  # 服务器错误
        else:
            return status_code
    
    def _get_message(self, status_code, data):
        """获取响应消息"""
        # 如果响应数据中包含message字段，优先使用
        if isinstance(data, dict):
            if 'message' in data:
                return data['message']
            elif 'detail' in data:
                return data['detail']
                
        # 根据状态码返回默认消息
        if is_success(status_code):
            return '操作成功'
        elif status_code == 401:
            return '认证失败'
        elif status_code == 403:
            return '权限不足'
        elif status_code == 404:
            return '资源不存在'
        elif is_client_error(status_code):
            return '请求参数错误'
        elif is_server_error(status_code):
            return '服务器内部错误'
        else:
            return '未知错误'
    
    def _get_response_data(self, data, status_code):
        """获取响应数据体"""
        if data is None:
            return None
            
        # 处理列表和字典数据
        if isinstance(data, (ReturnList, list)):
            return data
        elif isinstance(data, (ReturnDict, dict)):
            # 检查是否为分页格式
            if 'pagination' in data and 'results' in data:
                # 保留分页格式，不做处理
                return data
            
            # 移除可能存在的消息字段，避免重复
            result = data.copy()
            for key in ['success', 'code', 'message', 'detail']:
                if key in result:
                    result.pop(key)
            return result
        else:
            return data 