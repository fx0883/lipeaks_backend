"""
OpenAPI 文档配置和通用响应示例
"""
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, OpenApiParameter, extend_schema

# 通用错误响应
common_error_responses = {
    400: OpenApiResponse(
        description="请求参数错误",
        examples=[
            OpenApiExample(
                name="参数错误示例",
                value={
                    "success": False,
                    "code": 4000,
                    "message": "请求参数错误",
                    "data": {
                        "field": ["错误信息"]
                    }
                }
            )
        ]
    ),
    401: OpenApiResponse(
        description="未授权访问",
        examples=[
            OpenApiExample(
                name="未授权示例",
                value={
                    "success": False,
                    "code": 4001,
                    "message": "未授权访问，请先登录",
                    "data": None
                }
            )
        ]
    ),
    403: OpenApiResponse(
        description="权限不足",
        examples=[
            OpenApiExample(
                name="权限不足示例",
                value={
                    "success": False,
                    "code": 4003,
                    "message": "权限不足，无法执行该操作",
                    "data": None
                }
            )
        ]
    ),
    404: OpenApiResponse(
        description="资源不存在",
        examples=[
            OpenApiExample(
                name="资源不存在示例",
                value={
                    "success": False,
                    "code": 4004,
                    "message": "请求的资源不存在",
                    "data": None
                }
            )
        ]
    ),
    500: OpenApiResponse(
        description="服务器错误",
        examples=[
            OpenApiExample(
                name="服务器错误示例",
                value={
                    "success": False,
                    "code": 5000,
                    "message": "服务器内部错误",
                    "data": None
                }
            )
        ]
    )
}

# 通用搜索参数
common_search_parameter = OpenApiParameter(
    name='search',
    description='搜索关键词',
    required=False,
    type=str
)

# 通用分页参数
common_pagination_parameters = [
    OpenApiParameter(
        name='page',
        description='页码（从1开始）',
        required=False,
        type=int,
        default=1
    ),
    OpenApiParameter(
        name='page_size',
        description='每页记录数',
        required=False,
        type=int,
        default=10
    )
]

# 租户状态参数
tenant_status_parameter = OpenApiParameter(
    name='status',
    description='租户状态 (active/suspended/deleted)',
    required=False,
    type=str,
    enum=['active', 'suspended', 'deleted']
)

# 用户状态参数
user_status_parameter = OpenApiParameter(
    name='status',
    description='用户状态 (active/suspended/inactive)',
    required=False,
    type=str,
    enum=['active', 'suspended', 'inactive']
)

# 用户管理员角色参数
user_admin_parameter = OpenApiParameter(
    name='is_admin',
    description='是否只显示管理员用户',
    required=False,
    type=bool
)

# 创建API文档的模板函数
def api_schema(
    summary,
    description,
    request_body=None,
    responses=None,
    parameters=None,
    examples=None,
    tags=None
):
    """
    创建API文档的通用模板
    
    Args:
        summary: API概要
        description: API详细描述
        request_body: 请求体schema
        responses: 响应schema
        parameters: 请求参数列表
        examples: 请求和响应示例
        tags: API标签
    
    Returns:
        装饰器函数
    """
    # 合并错误响应
    all_responses = responses.copy() if responses else {}
    all_responses.update(common_error_responses)
    
    return extend_schema(
        summary=summary,
        description=description,
        request=request_body,
        responses=all_responses,
        parameters=parameters,
        examples=examples,
        tags=tags
    ) 