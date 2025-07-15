"""
异常处理模块
"""
import logging
import traceback
from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError, NotAuthenticated, AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

# 自定义错误码
ERROR_CODES = {
    # 客户端错误 (4xxx)
    'ValidationError': 4000,
    'NotAuthenticated': 4001,
    'AuthenticationFailed': 4002,
    'PermissionDenied': 4003,
    'NotFound': 4004,
    'MethodNotAllowed': 4005,
    'NotAcceptable': 4006,
    'UnsupportedMediaType': 4015,
    'Throttled': 4029,
    
    # 租户相关错误 (41xx)
    'TenantNotFound': 4100,
    'TenantInactive': 4101,
    'QuotaExceeded': 4110,
    
    # 服务器错误 (5xxx)
    'APIException': 5000,
    'ServerError': 5001,
    'DatabaseError': 5002,
}

def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    """
    # 首先调用REST framework的默认异常处理
    response = exception_handler(exc, context)
    
    if response is not None:
        # 自定义格式化响应
        data = {
            'success': False,
            'code': response.status_code,
            'message': str(exc),
            'data': None
        }
        
        # 如果状态码在400-499之间，则是客户端错误
        if 400 <= response.status_code < 500:
            # 根据不同类型的异常，给出不同的错误码
            if response.status_code == 401:  # 未认证
                data['code'] = 4001
                data['message'] = '认证失败，请登录'
            elif response.status_code == 403:  # 权限不足
                data['code'] = 4003
                data['message'] = '您没有执行该操作的权限'
            elif response.status_code == 404:  # 资源不存在
                data['code'] = 4004
                data['message'] = '请求的资源不存在'
            elif response.status_code == 400:  # 请求错误
                data['code'] = 4000
                if hasattr(exc, 'detail'):
                    data['message'] = str(exc.detail)
                    data['errors'] = exc.detail
            else:
                data['code'] = 4000 + response.status_code % 1000
        else:
            # 服务器错误
            data['code'] = 5000
            data['message'] = '服务器内部错误'
        
        response.data = data
    
    # 处理自定义异常
    elif isinstance(exc, QuotaExceeded):
        response = Response(
            {
                'success': False,
                'code': 4029,
                'message': str(exc) or '配额超限',
                'data': None
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    return response


# 自定义异常类

class TenantNotFound(APIException):
    """租户不存在异常"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = '租户不存在'
    default_code = 'tenant_not_found'


class TenantInactive(APIException):
    """租户未激活异常"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '租户未激活或已被禁用'
    default_code = 'tenant_inactive'


class QuotaExceeded(Exception):
    """配额超限异常"""
    pass


class APIException(APIException):
    """服务器错误异常"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '服务器内部错误'
    default_code = 'server_error' 