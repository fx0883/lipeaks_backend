"""
API通用参数定义
"""
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes

# 定义通用搜索参数
common_search_parameter = OpenApiParameter(
    name='search',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description='通用搜索参数，可用于搜索多个字段',
    required=False
)

# 定义租户状态参数
tenant_status_parameter = OpenApiParameter(
    name='status',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description='租户状态过滤参数',
    required=False,
    enum=['active', 'inactive', 'all']
)

# 定义分页参数
common_pagination_parameters = [
    OpenApiParameter(
        name='page',
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description='页码（从1开始）',
        required=False,
        default=1
    ),
    OpenApiParameter(
        name='page_size',
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description='每页条数',
        required=False,
        default=10
    )
]

# 定义用户状态参数
user_status_parameter = OpenApiParameter(
    name='status',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description='用户状态过滤参数',
    required=False,
    enum=['active', 'inactive', 'suspended']
)

# 定义用户管理员角色参数
user_admin_parameter = OpenApiParameter(
    name='is_admin',
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    description='是否为管理员用户',
    required=False
)