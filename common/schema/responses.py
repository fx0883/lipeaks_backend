"""
API通用响应定义
"""
from drf_spectacular.utils import OpenApiResponse

# 定义通用错误响应
common_error_responses = {
    400: OpenApiResponse(description="输入数据验证错误"),
    401: OpenApiResponse(description="未认证或认证失败"),
    403: OpenApiResponse(description="没有权限执行该操作"),
    404: OpenApiResponse(description="请求的资源不存在"),
    500: OpenApiResponse(description="服务器内部错误"),
} 