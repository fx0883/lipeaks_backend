"""
租户相关的 OpenAPI 文档配置
"""
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, OpenApiParameter
from common.schema import common_error_responses
from rest_framework import status

# 租户列表响应示例
tenant_list_response_examples = [
    OpenApiExample(
        name="租户列表",
        value={
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                    "name": "测试租户1",
                    "status": "active",
                    "contact_name": "张三",
                    "contact_email": "zhangsan@example.com",
                    "contact_phone": "13800138000",
                    "created_at": "2025-04-20T10:00:00Z",
                    "updated_at": "2025-04-20T10:00:00Z"
                },
                {
                    "id": 2,
                    "name": "测试租户2",
                    "status": "suspended",
                    "contact_name": "李四",
                    "contact_email": "lisi@example.com",
                    "contact_phone": "13900139000",
                    "created_at": "2025-04-21T10:00:00Z",
                    "updated_at": "2025-04-21T10:00:00Z"
                }
            ]
        },
        response_only=True
    )
]

# 创建租户请求示例
tenant_create_request_examples = [
    OpenApiExample(
        name="创建租户",
        value={
            "name": "新租户",
            "status": "active",
            "contact_name": "王五",
            "contact_email": "wangwu@example.com",
            "contact_phone": "13700137000"
        },
        request_only=True
    )
]

# 创建租户响应示例
tenant_create_response_examples = [
    OpenApiExample(
        name="创建成功",
        value={
            "success": True,
            "code": 2000,
            "message": "创建租户成功",
            "data": {
                "id": 3,
                "name": "新租户",
                "status": "active",
                "contact_name": "王五",
                "contact_email": "wangwu@example.com",
                "contact_phone": "13700137000",
                "created_at": "2025-04-22T10:00:00Z",
                "updated_at": "2025-04-22T10:00:00Z"
            }
        },
        response_only=True
    )
]

# 租户详情响应示例
tenant_detail_response_examples = [
    OpenApiExample(
        name="租户详情",
        value={
            "id": 1,
            "name": "测试租户1",
            "status": "active",
            "contact_name": "张三",
            "contact_email": "zhangsan@example.com",
            "contact_phone": "13800138000",
            "created_at": "2025-04-20T10:00:00Z",
            "updated_at": "2025-04-20T10:00:00Z",
            "quota": {
                "max_users": 20,
                "max_admins": 5,
                "max_storage_mb": 2048,
                "max_products": 100,
                "current_storage_used_mb": 120
            },
            "users_count": 5,
            "admins_count": 2
        },
        response_only=True
    )
]

# 租户配额响应示例
tenant_quota_response_examples = [
    OpenApiExample(
        name="租户配额",
        value={
            "success": True,
            "code": 2000,
            "message": "获取成功",
            "data": {
                "id": 1,
                "tenant": {
                    "id": 1,
                    "name": "测试租户1"
                },
                "max_users": 20,
                "max_admins": 5,
                "max_storage_mb": 2048,
                "max_products": 100,
                "current_storage_used_mb": 120,
                "created_at": "2025-04-20T10:00:00Z",
                "updated_at": "2025-04-20T10:00:00Z"
            }
        },
        response_only=True
    )
]

# 更新租户配额请求示例
tenant_quota_update_request_examples = [
    OpenApiExample(
        name="更新配额",
        value={
            "max_users": 30,
            "max_admins": 8,
            "max_storage_mb": 5120,
            "max_products": 200
        },
        request_only=True
    )
]

# 更新租户配额响应示例
tenant_quota_update_response_examples = [
    OpenApiExample(
        name="更新成功",
        value={
            "success": True,
            "code": 2000,
            "message": "更新配额成功",
            "data": {
                "id": 1,
                "tenant": {
                    "id": 1,
                    "name": "测试租户1"
                },
                "max_users": 30,
                "max_admins": 8,
                "max_storage_mb": 5120,
                "max_products": 200,
                "current_storage_used_mb": 120,
                "created_at": "2025-04-20T10:00:00Z",
                "updated_at": "2025-04-22T10:00:00Z"
            }
        },
        response_only=True
    )
]

# 租户配额使用情况响应示例
tenant_quota_usage_response_examples = [
    OpenApiExample(
        name="配额使用情况",
        value={
            "success": True,
            "code": 2000,
            "message": "获取成功",
            "data": {
                "users": {
                    "current": 10,
                    "maximum": 20,
                    "percentage": 50.0
                },
                "admins": {
                    "current": 2,
                    "maximum": 5,
                    "percentage": 40.0
                },
                "storage": {
                    "current": 120,
                    "maximum": 2048,
                    "percentage": 5.9
                },
                "products": {
                    "current": 25,
                    "maximum": 100,
                    "percentage": 25.0
                }
            }
        },
        response_only=True
    )
]

# 暂停租户响应示例
tenant_suspend_response_examples = [
    OpenApiExample(
        name="暂停成功",
        value={
            "success": True,
            "code": 2000,
            "message": "租户已暂停",
            "data": {
                "id": 1,
                "name": "测试租户1",
                "status": "suspended",
                "updated_at": "2025-04-22T10:00:00Z"
            }
        },
        response_only=True
    )
]

# 激活租户响应示例
tenant_activate_response_examples = [
    OpenApiExample(
        name="激活成功",
        value={
            "success": True,
            "code": 2000,
            "message": "租户已激活",
            "data": {
                "id": 1,
                "name": "测试租户1",
                "status": "active",
                "updated_at": "2025-04-22T10:00:00Z"
            }
        },
        response_only=True
    )
]

# 租户用户列表响应示例
tenant_users_response_examples = [
    OpenApiExample(
        name="租户用户列表",
        value={
            "success": True,
            "code": 2000,
            "message": "获取成功",
            "data": {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 2,
                        "username": "tenant_admin",
                        "email": "tenant_admin@example.com",
                        "nick_name": "租户管理员",
                        "is_active": True,
                        "is_admin": True,
                        "status": "active",
                        "date_joined": "2025-04-21T10:00:00Z"
                    },
                    {
                        "id": 3,
                        "username": "tenant_user",
                        "email": "tenant_user@example.com",
                        "nick_name": "租户用户",
                        "is_active": True,
                        "is_admin": False,
                        "status": "active",
                        "date_joined": "2025-04-21T11:00:00Z"
                    }
                ]
            }
        },
        response_only=True
    )
]

# 租户完整信息响应示例
tenant_comprehensive_response_examples = [
    OpenApiExample(
        name="租户完整信息",
        value={
            "success": True,
            "code": 2000,
            "message": "获取租户信息成功",
            "data": {
                "id": 1,
                "name": "测试租户1",
                "code": "test_tenant_1",
                "status": "active",
                "status_display": "活跃",
                "contact_name": "张三",
                "contact_email": "zhangsan@example.com",
                "contact_phone": "13800138000",
                "created_at": "2025-04-20T10:00:00Z",
                "updated_at": "2025-04-20T10:00:00Z",
                "is_active": True,
                "user_count": 10,
                "admin_count": 2,
                "quota": {
                    "max_users": 20,
                    "max_admins": 5,
                    "max_storage_mb": 2048,
                    "max_products": 100,
                    "current_storage_used_mb": 120,
                    "usage_percentage": {
                        "users": 50.0,
                        "admins": 40.0,
                        "storage": 5.9,
                        "products": 25.0
                    }
                },
                "business_info": None
            }
        },
        response_only=True
    )
]

# 租户完整信息响应
tenant_comprehensive_responses = {
    status.HTTP_200_OK: OpenApiResponse(
        description="获取成功",
        examples=tenant_comprehensive_response_examples
    ),
    **common_error_responses
}

# 租户列表API响应定义
tenant_list_responses = {
    status.HTTP_200_OK: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "code": {"type": "integer", "example": 2000},
            "message": {"type": "string", "example": "获取成功"},
            "data": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "example": 10},
                    "next": {"type": ["string", "null"], "example": "http://api.example.com/tenants/?page=2"},
                    "previous": {"type": ["string", "null"], "example": None},
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer", "example": 1},
                                "name": {"type": "string", "example": "示例企业"},
                                "status": {"type": "string", "example": "active"},
                                "contact_name": {"type": "string", "example": "张三"},
                                "contact_email": {"type": "string", "example": "zhangsan@example.com"},
                                "contact_phone": {"type": "string", "example": "13800138000"},
                                "user_count": {"type": "integer", "example": 15},
                                "admin_count": {"type": "integer", "example": 2},
                                "created_time": {"type": "string", "format": "date-time"},
                                "updated_time": {"type": "string", "format": "date-time"}
                            }
                        }
                    }
                }
            }
        }
    },
    status.HTTP_403_FORBIDDEN: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4003},
            "message": {"type": "string", "example": "权限不足"},
            "data": {"type": "null"}
        }
    }
}

# 创建租户API响应定义
tenant_create_responses = {
    status.HTTP_201_CREATED: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "code": {"type": "integer", "example": 2000},
            "message": {"type": "string", "example": "创建租户成功"},
            "data": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "新创建企业"},
                    "status": {"type": "string", "example": "active"},
                    "contact_name": {"type": "string", "example": "李四"},
                    "contact_email": {"type": "string", "example": "lisi@example.com"},
                    "contact_phone": {"type": "string", "example": "13900139000"},
                    "created_time": {"type": "string", "format": "date-time"},
                    "updated_time": {"type": "string", "format": "date-time"}
                }
            }
        }
    },
    status.HTTP_400_BAD_REQUEST: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4000},
            "message": {"type": "string", "example": "参数错误"},
            "data": {
                "type": "object",
                "example": {
                    "name": ["该租户名称已存在"],
                    "contact_email": ["请输入有效的邮箱地址"]
                }
            }
        }
    },
    status.HTTP_403_FORBIDDEN: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4003},
            "message": {"type": "string", "example": "权限不足"},
            "data": {"type": "null"}
        }
    }
}

# 租户详情API响应定义
tenant_detail_responses = {
    status.HTTP_200_OK: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "code": {"type": "integer", "example": 2000},
            "message": {"type": "string", "example": "获取成功"},
            "data": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "示例企业"},
                    "status": {"type": "string", "example": "active"},
                    "contact_name": {"type": "string", "example": "张三"},
                    "contact_email": {"type": "string", "example": "zhangsan@example.com"},
                    "contact_phone": {"type": "string", "example": "13800138000"},
                    "quota": {
                        "type": "object",
                        "properties": {
                            "max_user_count": {"type": "integer", "example": 100},
                            "max_admin_count": {"type": "integer", "example": 5},
                            "max_storage_size": {"type": "integer", "example": 10737418240},  # 10GB in bytes
                            "max_model_count": {"type": "integer", "example": 50},
                            "max_dataset_count": {"type": "integer", "example": 20}
                        }
                    },
                    "usage": {
                        "type": "object",
                        "properties": {
                            "user_count": {"type": "integer", "example": 15},
                            "admin_count": {"type": "integer", "example": 2},
                            "storage_size": {"type": "integer", "example": 1073741824},  # 1GB in bytes
                            "model_count": {"type": "integer", "example": 5},
                            "dataset_count": {"type": "integer", "example": 3}
                        }
                    },
                    "created_time": {"type": "string", "format": "date-time"},
                    "updated_time": {"type": "string", "format": "date-time"}
                }
            }
        }
    },
    status.HTTP_404_NOT_FOUND: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4004},
            "message": {"type": "string", "example": "租户不存在"},
            "data": {"type": "null"}
        }
    },
    status.HTTP_403_FORBIDDEN: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4003},
            "message": {"type": "string", "example": "权限不足"},
            "data": {"type": "null"}
        }
    }
}

# 租户配额API响应定义
tenant_quota_responses = {
    status.HTTP_200_OK: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "code": {"type": "integer", "example": 2000},
            "message": {"type": "string", "example": "获取成功"},
            "data": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "tenant": {"type": "integer", "example": 1},
                    "max_user_count": {"type": "integer", "example": 100},
                    "max_admin_count": {"type": "integer", "example": 5},
                    "max_storage_size": {"type": "integer", "example": 10737418240},  # 10GB in bytes
                    "max_model_count": {"type": "integer", "example": 50},
                    "max_dataset_count": {"type": "integer", "example": 20}
                }
            }
        }
    },
    status.HTTP_404_NOT_FOUND: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4004},
            "message": {"type": "string", "example": "租户不存在"},
            "data": {"type": "null"}
        }
    }
}

# 更新租户配额API响应定义
tenant_quota_update_responses = {
    status.HTTP_200_OK: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "code": {"type": "integer", "example": 2000},
            "message": {"type": "string", "example": "更新配额成功"},
            "data": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "tenant": {"type": "integer", "example": 1},
                    "max_user_count": {"type": "integer", "example": 150},
                    "max_admin_count": {"type": "integer", "example": 8},
                    "max_storage_size": {"type": "integer", "example": 21474836480},  # 20GB in bytes
                    "max_model_count": {"type": "integer", "example": 80},
                    "max_dataset_count": {"type": "integer", "example": 30}
                }
            }
        }
    },
    status.HTTP_400_BAD_REQUEST: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4000},
            "message": {"type": "string", "example": "参数错误"},
            "data": {
                "type": "object",
                "example": {
                    "max_user_count": ["该值不能小于current已有用户数"],
                    "max_storage_size": ["存储空间必须是整数"]
                }
            }
        }
    },
    status.HTTP_404_NOT_FOUND: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4004},
            "message": {"type": "string", "example": "租户不存在"},
            "data": {"type": "null"}
        }
    }
}

# 租户配额使用情况API响应定义
tenant_quota_usage_responses = {
    status.HTTP_200_OK: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "code": {"type": "integer", "example": 2000},
            "message": {"type": "string", "example": "获取成功"},
            "data": {
                "type": "object",
                "properties": {
                    "user_count": {"type": "integer", "example": 15},
                    "admin_count": {"type": "integer", "example": 2},
                    "storage_size": {"type": "integer", "example": 1073741824},  # 1GB in bytes
                    "storage_size_formatted": {"type": "string", "example": "1.00 GB"},
                    "model_count": {"type": "integer", "example": 5},
                    "dataset_count": {"type": "integer", "example": 3},
                    "user_usage_percent": {"type": "number", "example": 15.0},
                    "admin_usage_percent": {"type": "number", "example": 40.0},
                    "storage_usage_percent": {"type": "number", "example": 10.0},
                    "model_usage_percent": {"type": "number", "example": 10.0},
                    "dataset_usage_percent": {"type": "number", "example": 15.0}
                }
            }
        }
    },
    status.HTTP_404_NOT_FOUND: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4004},
            "message": {"type": "string", "example": "租户不存在"},
            "data": {"type": "null"}
        }
    }
}

# 暂停租户API响应定义
tenant_suspend_responses = {
    status.HTTP_200_OK: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "code": {"type": "integer", "example": 2000},
            "message": {"type": "string", "example": "租户已暂停"},
            "data": {"type": "null"}
        }
    },
    status.HTTP_404_NOT_FOUND: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4004},
            "message": {"type": "string", "example": "租户不存在"},
            "data": {"type": "null"}
        }
    }
}

# 激活租户API响应定义
tenant_activate_responses = {
    status.HTTP_200_OK: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "code": {"type": "integer", "example": 2000},
            "message": {"type": "string", "example": "租户已激活"},
            "data": {"type": "null"}
        }
    },
    status.HTTP_404_NOT_FOUND: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4004},
            "message": {"type": "string", "example": "租户不存在"},
            "data": {"type": "null"}
        }
    }
}

# 租户用户列表API响应定义
tenant_users_responses = {
    status.HTTP_200_OK: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "code": {"type": "integer", "example": 2000},
            "message": {"type": "string", "example": "获取成功"},
            "data": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "example": 15},
                    "next": {"type": ["string", "null"], "example": "http://api.example.com/tenants/1/users/?page=2"},
                    "previous": {"type": ["string", "null"], "example": None},
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer", "example": 1},
                                "username": {"type": "string", "example": "user1"},
                                "email": {"type": "string", "example": "user1@example.com"},
                                "name": {"type": "string", "example": "用户1"},
                                "role": {"type": "string", "example": "admin"},
                                "is_active": {"type": "boolean", "example": True},
                                "last_login": {"type": ["string", "null"], "format": "date-time"},
                                "created_time": {"type": "string", "format": "date-time"}
                            }
                        }
                    }
                }
            }
        }
    },
    status.HTTP_404_NOT_FOUND: {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "code": {"type": "integer", "example": 4004},
            "message": {"type": "string", "example": "租户不存在"},
            "data": {"type": "null"}
        }
    }
} 