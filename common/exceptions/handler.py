"""
全局异常处理器

统一处理所有API异常，转换为标准响应格式
"""
import logging
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    NotAuthenticated,
    AuthenticationFailed,
    PermissionDenied as DRFPermissionDenied,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .base import BusinessException
from .tenant import TenantException
from .error_codes import ERROR_CODE_TO_STRING

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    自定义全局异常处理器
    
    按照以下优先级处理异常：
    1. BusinessException 及其子类 - 业务异常
    2. ValidationError - 数据验证异常
    3. DRF内置异常 - 认证、权限等
    4. Django内置异常 - Http404, PermissionDenied等
    5. Python原生异常 - ValueError, TypeError等
    6. 未知异常 - 捕获所有其他异常
    
    Args:
        exc: 异常实例
        context: 上下文信息，包含 view, request 等
    
    Returns:
        Response: 标准格式的错误响应
    """
    # 获取请求对象（用于日志记录）
    request = context.get('request')
    view = context.get('view')
    
    # 跳过OpenAPI schema端点，使用DRF默认异常处理
    if request and request.path in ['/api/v1/schema/', '/api/v1/schema']:
        return drf_exception_handler(exc, context)
    
    # 1. 处理BusinessException及其子类（我们的业务异常）
    if isinstance(exc, BusinessException):
        return _handle_business_exception(exc, request, view)
    
    # 2. 调用DRF默认异常处理器
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        # DRF成功处理了异常，转换为我们的标准格式
        return _format_drf_response(response, exc, request, view)
    
    # 3. 处理DRF未处理的异常
    return _handle_unhandled_exception(exc, request, view)


def _handle_business_exception(exc, request, view):
    """
    处理BusinessException及其子类
    
    Args:
        exc: BusinessException实例
        request: HTTP请求对象
        view: 视图对象
    
    Returns:
        Response: 标准格式的错误响应
    """
    # 获取异常详情
    business_code = exc.business_code or 4000
    error_code = exc.error_code or 'BUSINESS_ERROR'
    detail = str(exc.detail) if hasattr(exc, 'detail') else str(exc)
    http_status = exc.status_code if hasattr(exc, 'status_code') else 400
    
    # 记录日志
    log_level = _get_log_level_for_status(http_status)
    log_message = f'Business exception: {exc.__class__.__name__} - {detail}'
    
    if log_level == 'warning':
        logger.warning(log_message, extra={
            'error_code': error_code,
            'business_code': business_code,
            'user': getattr(request, 'user', None),
            'path': getattr(request, 'path', None),
            'extra_context': exc.extra if hasattr(exc, 'extra') else {}
        })
    elif log_level == 'error':
        logger.error(log_message, extra={
            'error_code': error_code,
            'business_code': business_code,
            'user': getattr(request, 'user', None),
            'path': getattr(request, 'path', None),
            'extra_context': exc.extra if hasattr(exc, 'extra') else {}
        }, exc_info=True)
    
    # 构建响应
    response_data = {
        'success': False,
        'code': business_code,
        'message': detail,
        'data': None,
        'error_code': error_code
    }
    
    return Response(response_data, status=http_status)


def _format_drf_response(response, exc, request, view):
    """
    格式化DRF异常响应为标准格式
    
    Args:
        response: DRF的Response对象
        exc: 异常实例
        request: HTTP请求对象
        view: 视图对象
    
    Returns:
        Response: 标准格式的错误响应
    """
    http_status = response.status_code
    
    # 确定业务错误码
    business_code = _get_business_code_for_status(http_status)
    
    # 确定错误标识符
    error_code = _get_error_code_for_exception(exc, http_status)
    
    # 提取错误消息
    message = _extract_error_message(response.data, exc, http_status)
    
    # 处理ValidationError的特殊情况
    data = None
    if isinstance(exc, ValidationError) and isinstance(response.data, dict):
        # 验证错误时，将字段错误信息放到data中
        data = response.data
        if 'detail' in data:
            data.pop('detail')  # 移除detail，因为已经在message中
    
    # 记录日志
    log_level = _get_log_level_for_status(http_status)
    log_message = f'DRF exception: {exc.__class__.__name__} - {message}'
    
    if log_level == 'info':
        logger.info(log_message, extra={
            'error_code': error_code,
            'business_code': business_code,
            'user': getattr(request, 'user', None),
            'path': getattr(request, 'path', None),
        })
    elif log_level == 'warning':
        logger.warning(log_message, extra={
            'error_code': error_code,
            'business_code': business_code,
            'user': getattr(request, 'user', None),
            'path': getattr(request, 'path', None),
        })
    
    # 构建标准响应
    response_data = {
        'success': False,
        'code': business_code,
        'message': message,
        'data': data,
        'error_code': error_code
    }
    
    response.data = response_data
    return response


def _handle_unhandled_exception(exc, request, view):
    """
    处理DRF未处理的异常（通常是系统异常）
    
    Args:
        exc: 异常实例
        request: HTTP请求对象
        view: 视图对象
    
    Returns:
        Response: 标准格式的错误响应
    """
    # 记录严重错误（包含堆栈信息）
    logger.error(
        f'Unhandled exception: {exc.__class__.__name__} - {str(exc)}',
        extra={
            'user': getattr(request, 'user', None),
            'path': getattr(request, 'path', None),
            'view': view.__class__.__name__ if view else None,
        },
        exc_info=True  # 包含完整堆栈信息
    )
    
    # 构建响应（不暴露系统错误详情）
    response_data = {
        'success': False,
        'code': 5000,
        'message': '服务器内部错误',
        'data': None,
        'error_code': 'INTERNAL_SERVER_ERROR'
    }
    
    return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_business_code_for_status(http_status):
    """
    根据HTTP状态码获取业务错误码
    
    Args:
        http_status: HTTP状态码
    
    Returns:
        int: 业务错误码
    """
    # 常见HTTP状态码到业务错误码的映射
    status_code_map = {
        400: 4000,  # Bad Request
        401: 4001,  # Unauthorized
        403: 4003,  # Forbidden
        404: 4004,  # Not Found
        405: 4005,  # Method Not Allowed
        406: 4006,  # Not Acceptable
        415: 4015,  # Unsupported Media Type
        429: 4029,  # Too Many Requests
        500: 5000,  # Internal Server Error
        501: 5001,  # Not Implemented
        502: 5002,  # Bad Gateway
        503: 5003,  # Service Unavailable
    }
    
    return status_code_map.get(http_status, http_status)


def _get_error_code_for_exception(exc, http_status):
    """
    根据异常类型和HTTP状态码获取错误标识符
    
    Args:
        exc: 异常实例
        http_status: HTTP状态码
    
    Returns:
        str: 错误标识符
    """
    # 特定异常类型的错误码
    if isinstance(exc, NotAuthenticated):
        return 'AUTH_NOT_AUTHENTICATED'
    elif isinstance(exc, AuthenticationFailed):
        return 'AUTH_AUTHENTICATION_FAILED'
    elif isinstance(exc, (DRFPermissionDenied, DjangoPermissionDenied)):
        return 'AUTH_PERMISSION_DENIED'
    elif isinstance(exc, Http404):
        return 'NOT_FOUND'
    elif isinstance(exc, ValidationError):
        return 'VALIDATION_ERROR'
    elif isinstance(exc, APIException):
        # 其他DRF异常，使用default_code
        return getattr(exc, 'default_code', 'API_ERROR').upper()
    
    # 根据HTTP状态码推断
    business_code = _get_business_code_for_status(http_status)
    return ERROR_CODE_TO_STRING.get(business_code, 'UNKNOWN_ERROR')


def _extract_error_message(response_data, exc, http_status):
    """
    从响应数据或异常中提取错误消息
    
    Args:
        response_data: DRF响应数据
        exc: 异常实例
        http_status: HTTP状态码
    
    Returns:
        str: 错误消息
    """
    # 尝试从响应数据中提取
    if isinstance(response_data, dict):
        if 'detail' in response_data:
            detail = response_data['detail']
            if isinstance(detail, str):
                return detail
            elif isinstance(detail, list) and detail:
                return str(detail[0])
        elif 'message' in response_data:
            return response_data['message']
    
    # 尝试从异常中提取
    if hasattr(exc, 'detail'):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        elif isinstance(detail, dict):
            return '数据验证失败'
        elif isinstance(detail, list) and detail:
            return str(detail[0])
    
    # 使用默认消息
    return _get_default_message_for_status(http_status)


def _get_default_message_for_status(http_status):
    """
    获取HTTP状态码的默认错误消息
    
    Args:
        http_status: HTTP状态码
    
    Returns:
        str: 默认错误消息
    """
    default_messages = {
        400: '请求参数错误',
        401: '认证失败，请登录',
        403: '您没有执行该操作的权限',
        404: '请求的资源不存在',
        405: '不支持的请求方法',
        406: '无法生成客户端可接受的响应',
        415: '不支持的媒体类型',
        429: '请求过于频繁，请稍后重试',
        500: '服务器内部错误',
        501: '功能未实现',
        502: '网关错误',
        503: '服务暂时不可用',
    }
    
    return default_messages.get(http_status, '操作失败')


def _get_log_level_for_status(http_status):
    """
    根据HTTP状态码确定日志级别
    
    Args:
        http_status: HTTP状态码
    
    Returns:
        str: 日志级别 ('info', 'warning', 'error')
    """
    if http_status < 400:
        return 'info'
    elif 400 <= http_status < 500:
        # 客户端错误，使用warning级别（除了401/403使用info）
        if http_status in (401, 403):
            return 'info'
        return 'warning'
    else:
        # 服务器错误，使用error级别
        return 'error'

