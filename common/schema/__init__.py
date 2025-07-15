"""
Schema相关配置和扩展
"""
# 导出common_error_responses
from .responses import common_error_responses 

# 导出通用参数
from .parameters import (
    common_search_parameter, 
    tenant_status_parameter, 
    common_pagination_parameters,
    user_status_parameter,
    user_admin_parameter
)

# 导入JWT认证扩展，确保它被注册到drf-spectacular
from .spectacular_extensions import JWTAuthenticationScheme

# 添加api_schema装饰器函数
from functools import wraps
from drf_spectacular.utils import extend_schema

def api_schema(summary=None, description=None, request_body=None, responses=None, examples=None, tags=None, parameters=None):
    """
    API Schema装饰器，简化extend_schema的使用
    
    Args:
        summary: API摘要
        description: API详细描述
        request_body: 请求体序列化器
        responses: 响应定义字典
        examples: 请求和响应示例列表
        tags: 标签列表
        parameters: API参数列表
    """
    # 保持与extend_schema兼容
    request_param = request_body
    
    @wraps(extend_schema)
    def decorator(func):
        return extend_schema(
            summary=summary,
            description=description,
            request=request_param,  # 使用request而不是request_body
            responses=responses,
            examples=examples,
            tags=tags,
            parameters=parameters
        )(func)
    return decorator 