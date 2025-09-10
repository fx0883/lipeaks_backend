"""
标准化错误响应构建器

统一构建租户中间件的错误响应格式，消除代码重复
"""
import time
import logging
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger(__name__)


class TenantErrorResponseBuilder:
    """
    租户相关错误响应构建器
    
    提供标准化的错误响应格式，支持调试日志
    """
    
    # 错误代码常量
    ERROR_CODES = {
        'TENANT_ID_REQUIRED': 4001,
        'TENANT_NOT_FOUND': 4002, 
        'TENANT_ACCESS_DENIED': 4003,
        'INVALID_TENANT_ID_FORMAT': 4004,
        'USER_NOT_ASSOCIATED_WITH_TENANT': 4005,
        'SUPER_ADMIN_TENANT_ID_REQUIRED': 4006,
    }
    
    # 错误消息模板
    ERROR_MESSAGES = {
        'TENANT_ID_REQUIRED': "未提供租户ID，无法访问CMS资源",
        'TENANT_NOT_FOUND': "指定的租户ID不存在: {tenant_id}",
        'TENANT_ACCESS_DENIED': "无法访问其他租户的资源",
        'INVALID_TENANT_ID_FORMAT': "无效的{source}租户ID格式: {tenant_id}，租户ID必须是整数",
        'USER_NOT_ASSOCIATED_WITH_TENANT': "用户未关联租户，无法执行修改操作",
        'SUPER_ADMIN_TENANT_ID_REQUIRED': "超级管理员需要通过X-Tenant-ID请求头指定租户ID，即使是GET请求也需要",
    }
    
    @classmethod
    def build_error_response(cls, error_type, request=None, **kwargs):
        """
        构建标准错误响应
        
        Args:
            error_type: 错误类型，必须在ERROR_CODES中定义
            request: HTTP请求对象，用于构建调试信息
            **kwargs: 错误消息格式化参数
        
        Returns:
            JsonResponse: 标准化的错误响应
        """
        if error_type not in cls.ERROR_CODES:
            raise ValueError(f"未知的错误类型: {error_type}")
            
        error_code = cls.ERROR_CODES[error_type]
        error_message = cls.ERROR_MESSAGES[error_type].format(**kwargs)
        
        # 构建基础响应
        error_response = {
            "success": False,
            "code": error_code,
            "message": error_message,
            "data": None
        }
        
        # 如果请求头中包含X-Debug-Log，则添加调试信息
        if request and request.headers.get('X-Debug-Log') == 'true':
            debug_log = cls._build_debug_log(error_type, request, **kwargs)
            error_response["debug_logs"] = [debug_log]
        
        # 确定HTTP状态码
        http_status = cls._get_http_status(error_type)
        
        logger.warning(f"租户错误响应: {error_type} - {error_message}")
        
        return JsonResponse(error_response, status=http_status)
    
    @classmethod
    def _build_debug_log(cls, error_type, request, **kwargs):
        """
        构建调试日志信息
        
        Args:
            error_type: 错误类型
            request: HTTP请求对象
            **kwargs: 额外的调试信息
        
        Returns:
            dict: 调试日志字典
        """
        debug_log = {
            "level": "error",
            "message": f"[租户中间件] {cls.ERROR_MESSAGES[error_type].format(**kwargs)}",
            "timestamp": time.time(),
            "path": request.path,
            "method": request.method,
        }
        
        # 添加用户信息（如果可用）
        if hasattr(request, 'user') and request.user.is_authenticated:
            debug_log.update({
                "user": request.user.username,
                "is_super_admin": getattr(request.user, 'is_super_admin', False),
            })
        else:
            debug_log["user"] = "anonymous"
            
        # 添加特定错误类型的额外信息
        if error_type == 'TENANT_ACCESS_DENIED':
            debug_log.update({
                "user_tenant_id": kwargs.get('user_tenant_id'),
                "header_tenant_id": kwargs.get('header_tenant_id'),
            })
        elif error_type == 'TENANT_NOT_FOUND':
            debug_log.update({
                "tenant_id": kwargs.get('tenant_id'),
                "is_super_admin": getattr(request.user, 'is_super_admin', False) if hasattr(request, 'user') else False,
            })
        
        return debug_log
    
    @classmethod
    def _get_http_status(cls, error_type):
        """
        根据错误类型确定HTTP状态码
        
        Args:
            error_type: 错误类型
        
        Returns:
            int: HTTP状态码
        """
        status_mapping = {
            'TENANT_ID_REQUIRED': status.HTTP_400_BAD_REQUEST,
            'TENANT_NOT_FOUND': status.HTTP_400_BAD_REQUEST,
            'TENANT_ACCESS_DENIED': status.HTTP_403_FORBIDDEN,
            'INVALID_TENANT_ID_FORMAT': status.HTTP_400_BAD_REQUEST,
            'USER_NOT_ASSOCIATED_WITH_TENANT': status.HTTP_403_FORBIDDEN,
            'SUPER_ADMIN_TENANT_ID_REQUIRED': status.HTTP_400_BAD_REQUEST,
        }
        
        return status_mapping.get(error_type, status.HTTP_400_BAD_REQUEST)


class TenantErrorTypes:
    """
    租户错误类型常量类，提供IDE自动补全支持
    """
    TENANT_ID_REQUIRED = 'TENANT_ID_REQUIRED'
    TENANT_NOT_FOUND = 'TENANT_NOT_FOUND'  
    TENANT_ACCESS_DENIED = 'TENANT_ACCESS_DENIED'
    INVALID_TENANT_ID_FORMAT = 'INVALID_TENANT_ID_FORMAT'
    USER_NOT_ASSOCIATED_WITH_TENANT = 'USER_NOT_ASSOCIATED_WITH_TENANT'
    SUPER_ADMIN_TENANT_ID_REQUIRED = 'SUPER_ADMIN_TENANT_ID_REQUIRED'
