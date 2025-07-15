from drf_spectacular.utils import OpenApiResponse, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

# 租户趋势图响应模式
tenant_trend_responses = {
    200: OpenApiResponse(
        description="租户趋势数据获取成功",
        examples=[
            OpenApiExample(
                name="租户趋势示例",
                value={
                    "code": 200,
                    "message": "success",
                    "data": {
                        "chart_type": "line",
                        "title": "租户数量趋势",
                        "description": "系统内租户总数随时间的变化趋势",
                        "labels": ["2023-01", "2023-02", "2023-03"],
                        "datasets": [
                            {
                                "label": "租户总数",
                                "data": [10, 15, 22],
                                "color": "#3366cc"
                            }
                        ],
                        "summary": {
                            "total": 22,
                            "growth_rate": 15.5,
                            "average_monthly_growth": 8.2
                        }
                    }
                }
            )
        ]
    ),
    403: OpenApiResponse(description="权限不足"),
    500: OpenApiResponse(description="服务器错误")
}

# 租户状态分布响应模式
tenant_status_distribution_responses = {
    200: OpenApiResponse(
        description="租户状态分布数据获取成功",
        examples=[
            OpenApiExample(
                name="租户状态分布示例",
                value={
                    "code": 200,
                    "message": "success",
                    "data": {
                        "chart_type": "pie",
                        "title": "租户状态分布",
                        "description": "不同状态的租户占比",
                        "labels": ["活跃", "暂停", "已删除"],
                        "datasets": [
                            {
                                "label": "租户数量",
                                "data": [45, 12, 8],
                                "colors": ["#36A2EB", "#FFCE56", "#FF6384"]
                            }
                        ],
                        "summary": {
                            "total": 65,
                            "active_percentage": 69.2,
                            "suspended_percentage": 18.5,
                            "deleted_percentage": 12.3
                        }
                    }
                }
            )
        ]
    ),
    403: OpenApiResponse(description="权限不足"),
    500: OpenApiResponse(description="服务器错误")
}

# 租户创建速率响应模式
tenant_creation_rate_responses = {
    200: OpenApiResponse(
        description="租户创建速率数据获取成功",
        examples=[
            OpenApiExample(
                name="租户创建速率示例",
                value={
                    "code": 200,
                    "message": "success",
                    "data": {
                        "chart_type": "bar",
                        "title": "租户创建速率",
                        "description": "每月新增租户数量",
                        "labels": ["2023-01", "2023-02", "2023-03"],
                        "datasets": [
                            {
                                "label": "新增租户",
                                "data": [5, 8, 12],
                                "color": "#4BC0C0"
                            }
                        ],
                        "summary": {
                            "total_new": 25,
                            "avg_monthly": 8.3,
                            "max_monthly": 12,
                            "growth_trend": "上升"
                        }
                    }
                }
            )
        ]
    ),
    403: OpenApiResponse(description="权限不足"),
    500: OpenApiResponse(description="服务器错误")
}

# 用户统计图表相关的参数和响应模式

# 用户总量与增长趋势响应模式
user_growth_trend_responses = {
    200: OpenApiResponse(
        description="用户总量与增长趋势数据获取成功",
        examples=[
            OpenApiExample(
                name="用户总量与增长趋势示例",
                value={
                    "code": 200,
                    "message": "success",
                    "data": {
                        "chart_type": "line",
                        "title": "用户总量与增长趋势",
                        "description": "系统内所有用户数量的时间序列图",
                        "labels": ["2023-01", "2023-02", "2023-03"],
                        "datasets": [
                            {
                                "label": "用户总数",
                                "data": [100, 150, 220],
                                "color": "#3366cc"
                            },
                            {
                                "label": "新增用户数",
                                "data": [100, 50, 70],
                                "color": "#dc3912"
                            }
                        ],
                        "summary": {
                            "total_users": 220,
                            "growth_rate": 120,
                            "average_monthly_growth": 40
                        }
                    }
                }
            )
        ]
    ),
    403: OpenApiResponse(description="权限不足"),
    500: OpenApiResponse(description="服务器错误")
}

# 用户角色分布响应模式
user_role_distribution_responses = {
    200: OpenApiResponse(
        description="用户角色分布数据获取成功",
        examples=[
            OpenApiExample(
                name="用户角色分布示例",
                value={
                    "code": 200,
                    "message": "success",
                    "data": {
                        "chart_type": "pie",
                        "title": "用户角色分布",
                        "description": "超级管理员、租户管理员、普通用户的比例",
                        "labels": ["超级管理员", "租户管理员", "普通用户"],
                        "datasets": [
                            {
                                "data": [5, 25, 70],
                                "colors": ["#9C27B0", "#2196F3", "#4CAF50"]
                            }
                        ],
                        "summary": {
                            "total_users": 100,
                            "super_admin_percentage": 5,
                            "tenant_admin_percentage": 25,
                            "regular_user_percentage": 70
                        }
                    }
                }
            )
        ]
    ),
    403: OpenApiResponse(description="权限不足"),
    500: OpenApiResponse(description="服务器错误")
}

# 活跃用户统计响应模式
active_users_responses = {
    200: OpenApiResponse(
        description="活跃用户统计数据获取成功",
        examples=[
            OpenApiExample(
                name="活跃用户统计示例",
                value={
                    "code": 200,
                    "message": "success",
                    "data": {
                        "chart_type": "line",
                        "title": "活跃用户统计",
                        "description": "按日/周/月统计的活跃用户数量",
                        "labels": ["2023-01-01", "2023-01-02", "2023-01-03"],
                        "datasets": [
                            {
                                "label": "活跃用户数",
                                "data": [45, 52, 49],
                                "color": "#FF9800"
                            },
                            {
                                "label": "活跃率",
                                "data": [45, 52, 49],
                                "color": "#E91E63",
                                "yAxisID": "percentage"
                            }
                        ],
                        "summary": {
                            "average_active_users": 48,
                            "highest_active_day": "2023-01-02",
                            "highest_active_count": 52,
                            "average_active_rate": 48
                        }
                    }
                }
            )
        ]
    ),
    403: OpenApiResponse(description="权限不足"),
    500: OpenApiResponse(description="服务器错误")
}

# 用户登录情况响应模式
login_heatmap_responses = {
    200: OpenApiResponse(
        description="用户登录情况数据获取成功",
        examples=[
            OpenApiExample(
                name="用户登录热力图示例",
                value={
                    "code": 200,
                    "message": "success",
                    "data": {
                        "chart_type": "heatmap",
                        "title": "用户登录热力图",
                        "description": "不同时间段的登录活跃度",
                        "x_labels": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
                        "y_labels": ["0时", "1时", "2时", "...", "23时"],
                        "dataset": [
                            [0, 0, 5],  # [x, y, value] 表示周一0时有5次登录
                            [0, 1, 3],
                            [0, 2, 1]
                        ],
                        "summary": {
                            "total_logins": 1250,
                            "peak_hour": "周一 10时",
                            "peak_hour_count": 45,
                            "lowest_hour": "周日 3时",
                            "lowest_hour_count": 0
                        }
                    }
                }
            )
        ]
    ),
    403: OpenApiResponse(description="权限不足"),
    500: OpenApiResponse(description="服务器错误")
}

# 定义共享的查询参数
period_param = OpenApiParameter(
    name='period',
    description='统计周期',
    required=False,
    type=OpenApiTypes.STR,
    enum=['daily', 'weekly', 'monthly', 'quarterly', 'yearly'],
    default='monthly',
    examples=[
        OpenApiExample(
            'Monthly',
            value='monthly',
            description='按月统计'
        ),
    ]
)

date_params = [
    OpenApiParameter(
        name='start_date',
        description='开始日期 (YYYY-MM-DD)',
        required=False,
        type=OpenApiTypes.DATE,
    ),
    OpenApiParameter(
        name='end_date',
        description='结束日期 (YYYY-MM-DD)',
        required=False,
        type=OpenApiTypes.DATE,
    )
] 