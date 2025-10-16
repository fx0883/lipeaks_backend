"""
用户相关的 OpenAPI 文档配置
"""
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, OpenApiParameter
from common.schema import common_error_responses
from rest_framework import status

# 登录请求示例
login_request_examples = [
    OpenApiExample(
        name="用户名登录",
        summary="使用用户名和密码登录",
        description="提供用户名和密码进行登录",
        value={
            "username": "admin_cms",
            "password": "admin_main"
        },
        request_only=True
    ),
    OpenApiExample(
        name="邮箱登录",
        summary="使用邮箱和密码登录",
        description="提供邮箱和密码进行登录",
        value={
            "username": "admin@example.com",
            "password": "admin_password"
        },
        request_only=True
    ),
    OpenApiExample(
        name="成员登录（body携带tenant_id）",
        summary="成员使用用户名/邮箱 + 租户ID 登录",
        description=(
            "当相同用户名/邮箱在多个租户中存在时，必须提供租户标识进行消歧。"
            "成员可在请求体提供 tenant_id 进行租户定位。"
        ),
        value={
            "username": "member@example.com",
            "password": "member_password",
            "tenant_id": 1
        },
        request_only=True
    ),
    OpenApiExample(
        name="成员登录（使用请求头X-Tenant-ID）",
        summary="成员使用用户名/邮箱 + X-Tenant-ID 登录",
        description=(
            "成员也可以通过请求头 X-Tenant-ID 指定租户ID（与请求体的 tenant_id 等价，优先级：请求体 > 请求头）。"
            "示例：在请求头中添加 X-Tenant-ID: 1"
        ),
        value={
            "username": "tenant_member",
            "password": "member_password"
        },
        request_only=True
    )
]

# 登录响应示例
login_response_examples = [
    OpenApiExample(
        name="管理员登录成功",
        summary="管理员登录成功响应",
        description="管理员用户登录成功的响应示例",
        value={
            "success": True,
            "code": 2000,
            "message": "登录成功",
            "data": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "nick_name": "管理员",
                    "is_admin": True,
                    "is_super_admin": True,
                    "is_member": False,
                    "avatar": ""
                }
            }
        }
    ),
    OpenApiExample(
        name="普通成员登录成功",
        summary="普通成员登录成功响应",
        description="普通成员用户登录成功的响应示例",
        value={
            "success": True,
            "code": 2000,
            "message": "登录成功",
            "data": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": 2,
                    "username": "member",
                    "email": "member@example.com",
                    "nick_name": "普通成员",
                    "is_admin": False,
                    "is_super_admin": False,
                    "is_member": True,
                    "is_sub_account": False,
                    "avatar": "",
                    "tenant_id": 1,
                    "tenant_name": "测试租户"
                }
            }
        }
    ),
    OpenApiExample(
        name="登录失败",
        summary="登录失败响应",
        description="用户名/邮箱或密码错误的响应示例",
        value={
            "success": False,
            "code": 4002,
            "message": "Invalid username/email or password",
            "data": None
        },
        status_codes=["401"]
    )
]

# 刷新令牌请求示例
token_refresh_request_examples = [
    OpenApiExample(
        name="刷新令牌",
        summary="使用刷新令牌获取新的访问令牌",
        description="提供刷新令牌获取新的访问令牌",
        value={
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        },
        request_only=True
    )
]

# 刷新令牌响应示例
token_refresh_response_examples = [
    OpenApiExample(
        name="刷新成功",
        summary="令牌刷新成功响应",
        description="刷新令牌有效，成功获取新的访问令牌",
        value={
            "success": True,
            "code": 2000,
            "message": "Token refreshed successfully",
            "data": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    ),
    OpenApiExample(
        name="刷新失败",
        summary="令牌刷新失败响应",
        description="刷新令牌无效或已过期",
        value={
            "success": False,
            "code": 4001,
            "message": "Invalid refresh token",
            "data": None
        },
        status_codes=["401"]
    )
]

# 验证令牌响应示例
token_verify_response_examples = [
    OpenApiExample(
        name="管理员令牌验证成功",
        summary="管理员令牌验证成功响应",
        description="管理员用户令牌有效的响应示例",
        value={
            "success": True,
            "code": 2000,
            "message": "令牌有效",
            "data": {
                "user": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "nick_name": "管理员",
                    "is_admin": True,
                    "is_super_admin": True,
                    "is_member": False,
                    "avatar": ""
                }
            }
        }
    ),
    OpenApiExample(
        name="普通成员令牌验证成功",
        summary="普通成员令牌验证成功响应",
        description="普通成员用户令牌有效的响应示例",
        value={
            "success": True,
            "code": 2000,
            "message": "令牌有效",
            "data": {
                "user": {
                    "id": 2,
                    "username": "member",
                    "email": "member@example.com",
                    "nick_name": "普通成员",
                    "is_admin": False,
                    "is_super_admin": False,
                    "is_member": True,
                    "is_sub_account": False,
                    "avatar": "",
                    "tenant_id": 1,
                    "tenant_name": "测试租户"
                }
            }
        }
    )
]

# 用户列表响应示例
user_list_response_examples = [
    OpenApiExample(
        name="用户列表",
        value={
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "nick_name": "管理员",
                    "phone": "13800138000",
                    "is_active": True,
                    "is_admin": True,
                    "is_super_admin": True,
                    "is_member": False,
                    "status": "active",
                    "tenant": None,
                    "date_joined": "2025-04-21T10:00:00Z",
                    "avatar": "https://example.com/avatar.jpg"
                },
                {
                    "id": 2,
                    "username": "tenant_admin",
                    "email": "tenant_admin@example.com",
                    "nick_name": "租户管理员",
                    "phone": "13900139000",
                    "is_active": True,
                    "is_admin": True,
                    "is_super_admin": False,
                    "is_member": False,
                    "status": "active",
                    "tenant": {
                        "id": 1,
                        "name": "测试租户"
                    },
                    "date_joined": "2025-04-21T11:00:00Z",
                    "avatar": "https://example.com/avatar2.jpg"
                }
            ]
        },
        response_only=True
    )
]

# 创建用户请求示例
user_create_request_examples = [
    OpenApiExample(
        name="创建普通用户",
        value={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "User@123",
            "confirm_password": "User@123",
            "nick_name": "新用户",
            "phone": "13800138001",
            "is_admin": False,
            "is_member": True,
            "tenant_id": 1  # 超级管理员可以指定租户
        },
        request_only=True
    )
]

# 创建用户响应示例
user_create_response_examples = [
    OpenApiExample(
        name="创建成功",
        value={
            "success": True,
            "code": 2000,
            "message": "用户创建成功",
            "data": {
                "id": 3,
                "username": "newuser",
                "email": "newuser@example.com",
                "nick_name": "新用户",
                "phone": "13800138001",
                "is_active": True,
                "is_admin": False,
                "is_super_admin": False,
                "is_member": True,
                "status": "active",
                "tenant": {
                    "id": 1,
                    "name": "测试租户"
                },
                "date_joined": "2025-04-22T10:00:00Z"
            }
        },
        response_only=True
    )
]

# 用户详情响应示例
user_detail_response_examples = [
    OpenApiExample(
        name="用户详情",
        value={
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "nick_name": "管理员",
            "phone": "13800138000",
            "is_active": True,
            "is_admin": True,
            "is_super_admin": True,
            "is_member": False,
            "status": "active",
            "tenant": None,
            "date_joined": "2025-04-21T10:00:00Z",
            "avatar": "https://example.com/avatar.jpg"
        },
        response_only=True
    )
]

# 修改密码请求示例
change_password_request_examples = [
    OpenApiExample(
        name="修改密码",
        value={
            "old_password": "OldPassword@123",
            "new_password": "NewPassword@123",
            "confirm_password": "NewPassword@123"
        },
        request_only=True
    )
]

# 修改密码响应示例
change_password_response_examples = [
    OpenApiExample(
        name="修改成功",
        value={
            "detail": "密码修改成功"
        },
        response_only=True
    )
]

# 登录API响应定义
login_responses = {
    200: OpenApiResponse(
        description="登录成功",
        examples=login_response_examples
    ),
    401: OpenApiResponse(
        description="登录失败",
        examples=[
            OpenApiExample(
                name="用户名或邮箱或密码错误",
                value={
                    "success": False,
                    "code": 4002,
                    "message": "Invalid username/email or password",
                    "data": None
                }
            )
        ]
    )
}

# 刷新令牌API响应定义
token_refresh_responses = {
    200: OpenApiResponse(
        description="令牌刷新成功",
        examples=token_refresh_response_examples
    ),
    400: OpenApiResponse(
        description="Invalid refresh token",
        examples=[
            OpenApiExample(
                name="无效令牌",
                value={
                    "success": False,
                    "code": 4000,
                    "message": "Invalid refresh token",
                    "data": None
                }
            )
        ]
    ),
    401: OpenApiResponse(
        description="令牌验证失败",
        examples=[
            OpenApiExample(
                name="令牌无效",
                value={
                    "success": False,
                    "code": 4001,
                    "message": "Invalid refresh token",
                    "data": None
                }
            ),
            OpenApiExample(
                name="用户不存在",
                value={
                    "success": False,
                    "code": 4001,
                    "message": "User not found or disabled",
                    "data": None
                }
            )
        ]
    ),
    500: OpenApiResponse(
        description="服务器错误",
        examples=[
            OpenApiExample(
                name="服务器错误",
                value={
                    "success": False,
                    "code": 5000,
                    "message": "Token refresh failed",
                    "data": None
                }
            )
        ]
    )
}

# 验证令牌API响应定义
token_verify_responses = {
    200: OpenApiResponse(
        description="令牌验证成功",
        examples=token_verify_response_examples
    )
}

# 用户列表API响应定义
user_list_responses = {
    200: OpenApiResponse(
        description="获取用户列表成功",
        examples=user_list_response_examples
    )
}

# 创建用户API响应定义
user_create_responses = {
    201: OpenApiResponse(
        description="创建用户成功",
        examples=user_create_response_examples
    )
}

# 用户详情API响应定义
user_detail_responses = {
    200: OpenApiResponse(
        description="获取用户详情成功",
        examples=user_detail_response_examples
    ),
    404: OpenApiResponse(
        description="用户不存在",
        examples=[
            OpenApiExample(
                name="用户不存在",
                value={
                    "success": False,
                    "code": 4004,
                    "message": "用户不存在",
                    "data": None
                }
            )
        ]
    )
}

# 修改密码API响应定义
change_password_responses = {
    200: OpenApiResponse(
        description="密码修改成功",
        examples=change_password_response_examples
    ),
    400: OpenApiResponse(
        description="密码修改失败",
        examples=[
            OpenApiExample(
                name="旧密码错误",
                value={
                    "old_password": ["Incorrect old password"]
                }
            )
        ]
    )
}

# 注册响应定义
register_responses = {
    201: OpenApiResponse(description="注册成功"),
    400: OpenApiResponse(description="注册失败，输入数据无效")
}

# 注册请求示例
register_request_examples = [
    OpenApiExample(
        name="标准注册",
        summary="注册新用户",
        description="提供用户名、邮箱、密码等信息注册新用户",
        value={
            "username": "newuser",
            "email": "user@example.com",
            "phone": "13800138000",
            "nick_name": "新用户",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "tenant_id": 1
        },
        request_only=True
    ),
    OpenApiExample(
        name="简单注册",
        summary="简化注册",
        description="仅提供必要信息注册新用户",
        value={
            "username": "simpleuser",
            "email": "simple@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!"
        },
        request_only=True
    )
]

# 注册响应示例
register_response_examples = [
    OpenApiExample(
        name="注册成功",
        summary="注册成功响应",
        description="用户注册成功的响应示例",
        value={
            "success": True,
            "code": 2000,
            "message": "注册成功",
            "data": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": 10,
                    "username": "newuser",
                    "email": "user@example.com",
                    "nick_name": "新用户",
                    "is_admin": False,
                    "is_member": True,
                    "avatar": "",
                    "tenant_id": 1,
                    "tenant_name": "测试租户"
                }
            }
        },
        status_codes=["201"]
    ),
    OpenApiExample(
        name="注册失败",
        summary="注册失败响应",
        description="注册数据无效的响应示例",
        value={
            "success": False,
            "code": 4000,
            "message": "注册失败",
            "data": {
                "username": ["Username already in use"],
                "email": ["Email already registered"],
                "password": ["密码至少需要包含8个字符，并且不能是常见密码"]
            }
        },
        status_codes=["400"]
    )
]

# 子账号创建请求示例
sub_account_create_request_examples = [
    OpenApiExample(
        name="创建子账号（指定密码）",
        value={
            "username": "subaccount",
            "email": "subaccount@example.com",
            "password": "Secure@Password123",
            "nick_name": "子账号",
            "phone": "13800138001",
            "first_name": "",
            "last_name": "",
            "avatar": ""
        },
        request_only=True
    ),
    OpenApiExample(
        name="创建子账号（使用默认密码）",
        value={
            "username": "subaccount2",
            "email": "subaccount2@example.com",
            "nick_name": "子账号2",
            "phone": "13800138002",
            "first_name": "",
            "last_name": "",
            "avatar": ""
        },
        request_only=True
    )
]

# 子账号创建响应示例
sub_account_create_response_examples = [
    OpenApiExample(
        name="创建成功",
        value={
            "success": True,
            "code": 2000,
            "message": "子账号创建成功",
            "data": {
                "id": 5,
                "username": "subaccount",
                "email": "subaccount@example.com",
                "nick_name": "子账号",
                "phone": "13800138001",
                "first_name": "",
                "last_name": "",
                "is_active": False,
                "avatar": "",
                "tenant": 1,
                "tenant_name": "测试租户",
                "is_admin": False,
                "is_member": True,
                "is_super_admin": False,
                "role": "子账号",
                "date_joined": "2025-04-22T10:00:00Z",
                "parent": 3
            }
        },
        response_only=True
    )
]

# 子账号创建API响应定义
sub_account_create_responses = {
    status.HTTP_201_CREATED: OpenApiResponse(
        description="子账号创建成功",
        examples=sub_account_create_response_examples
    ),
    status.HTTP_400_BAD_REQUEST: OpenApiResponse(
        description="创建失败，输入数据无效",
        examples=[
            OpenApiExample(
                name="用户名已存在",
                value={
                    "success": False,
                    "code": 4000,
                    "message": "创建失败",
                    "data": {
                        "username": ["Username already in use"]
                    }
                }
            ),
            OpenApiExample(
                name="邮箱已存在",
                value={
                    "success": False,
                    "code": 4000,
                    "message": "创建失败",
                    "data": {
                        "email": ["Email already in use"]
                    }
                }
            )
        ]
    ),
    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
        description="未认证或认证失败",
        examples=[
            OpenApiExample(
                name="未认证",
                value={
                    "success": False,
                    "code": 4001,
                    "message": "认证失败",
                    "data": {
                        "detail": "未提供有效的认证凭据"
                    }
                }
            )
        ]
    )
}

# 密码重置请求示例和响应
password_reset_request_examples = [
    OpenApiExample(
        name="管理员/平台用户重置（默认）",
        summary="平台用户通过邮箱发起重置",
        description="用于后台管理员或平台用户（account_type=user），仅需提供邮箱。",
        value={
            "email": "user@example.com",
            "account_type": "user"
        },
        request_only=True
    ),
    OpenApiExample(
        name="成员重置（携带租户ID）",
        summary="成员通过邮箱 + 租户ID 发起重置",
        description="当邮箱在多个租户中可能重复时，需要提供 tenant_id 进行租户定位。",
        value={
            "email": "member@example.com",
            "account_type": "member",
            "tenant_id": 1
        },
        request_only=True
    ),
    OpenApiExample(
        name="成员重置（省略租户ID，可能歧义）",
        summary="成员仅提供邮箱发起重置（存在歧义时将返回匿名成功，不发送邮件）",
        description="若该邮箱在多个租户中均存在成员账号且未提供 tenant_id，将返回通用成功提示以避免枚举，但不会发送邮件。",
        value={
            "email": "member.same@example.com",
            "account_type": "member"
        },
        request_only=True
    )
]

password_reset_response_examples = [
    OpenApiExample(
        name="密码重置请求成功响应（匿名化）",
        summary="无论是否存在该邮箱，均返回通用成功提示",
        value={
            "success": True,
            "code": 2000,
            "message": "如果该邮箱存在，密码重置链接已发送",
            "data": {
                "detail": "如果该邮箱存在，密码重置链接已发送"
            }
        },
        response_only=True
    ),
    OpenApiExample(
        name="请求数据无效（示例）",
        summary="例如参数缺失或格式错误",
        value={
            "success": False,
            "code": 4000,
            "message": "请求数据无效",
            "data": {
                "account_type": ["无效的选项"]
            }
        },
        response_only=True
    )
]

password_reset_request_responses = {
    200: OpenApiResponse(
        description="密码重置链接发送成功",
        examples=[
            OpenApiExample(
                name="密码重置请求成功响应（匿名化）",
                value={
                    "success": True,
                    "code": 2000,
                    "message": "如果该邮箱存在，密码重置链接已发送",
                    "data": {
                        "detail": "如果该邮箱存在，密码重置链接已发送"
                    }
                }
            )
        ]
    ),
    400: OpenApiResponse(
        description="请求数据无效",
        examples=[
            OpenApiExample(
                name="参数无效",
                value={
                    "success": False,
                    "code": 4000,
                    "message": "请求数据无效",
                    "data": {
                        "account_type": ["无效的选项"]
                    }
                }
            )
        ]
    ),
    429: OpenApiResponse(
        description="请求过于频繁",
        examples=[
            OpenApiExample(
                name="请求频率限制响应",
                value={
                    "success": False,
                    "code": 4029,
                    "message": "Too many requests, please try again later",
                    "data": {
                        "detail": "Too many requests, please try again later"
                    }
                }
            )
        ]
    )
}

# 密码重置令牌验证示例和响应
password_reset_verify_examples = [
    OpenApiExample(
        name="验证令牌请求示例",
        value={
            "token": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        },
        request_only=True
    )
]

password_reset_verify_response_examples = [
    OpenApiExample(
        name="令牌验证成功响应",
        value={
            "success": True,
            "code": 2000,
            "message": "重置令牌有效",
            "data": {
                "detail": "重置令牌有效",
                "user_email": "user@example.com"  # 与 user 或 member 绑定的邮箱
            }
        },
        response_only=True
    ),
    OpenApiExample(
        name="令牌无效响应",
        value={
            "success": False,
            "code": 4000,
            "message": "请求数据无效",
            "data": {
                "token": ["Invalid reset token"]
            }
        },
        response_only=True
    ),
    OpenApiExample(
        name="令牌过期响应",
        value={
            "success": False,
            "code": 4000,
            "message": "请求数据无效",
            "data": {
                "token": ["Reset token has expired"]
            }
        },
        response_only=True
    )
]

password_reset_verify_responses = {
    200: OpenApiResponse(
        description="令牌验证成功",
        examples=[
            OpenApiExample(
                name="令牌验证成功响应",
                value={
                    "success": True,
                    "code": 2000,
                    "message": "重置令牌有效",
                    "data": {
                        "detail": "重置令牌有效",
                        "user_email": "user@example.com"
                    }
                }
            )
        ]
    ),
    400: OpenApiResponse(
        description="令牌无效或已过期",
        examples=[
            OpenApiExample(
                name="令牌无效响应",
                value={
                    "success": False,
                    "code": 4000,
                    "message": "请求数据无效",
                    "data": {
                        "token": ["Invalid reset token"]
                    }
                }
            ),
            OpenApiExample(
                name="令牌过期响应",
                value={
                    "success": False,
                    "code": 4000,
                    "message": "请求数据无效",
                    "data": {
                        "token": ["Reset token has expired"]
                    }
                }
            )
        ]
    )
}

# 密码重置确认示例和响应
password_reset_confirm_examples = [
    OpenApiExample(
        name="密码重置确认请求示例",
        value={
            "token": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "new_password": "newPassword123",
            "confirm_password": "newPassword123"
        },
        request_only=True
    )
]

password_reset_confirm_response_examples = [
    OpenApiExample(
        name="密码重置成功响应",
        value={
            "success": True,
            "code": 2000,
            "message": "密码重置成功",
            "data": {
                "detail": "密码重置成功，请使用新密码登录"
            }
        },
        response_only=True
    ),
    OpenApiExample(
        name="密码不匹配响应",
        value={
            "success": False,
            "code": 4000,
            "message": "请求数据无效",
            "data": {
                "confirm_password": ["Passwords do not match"]
            }
        },
        response_only=True
    ),
    OpenApiExample(
        name="令牌无效响应",
        value={
            "success": False,
            "code": 4000,
            "message": "请求数据无效",
            "data": {
                "token": ["Invalid reset token"]
            }
        },
        response_only=True
    )
]

password_reset_confirm_responses = {
    200: OpenApiResponse(
        description="密码重置成功",
        examples=[
            OpenApiExample(
                name="密码重置成功响应",
                value={
                    "success": True,
                    "code": 2000,
                    "message": "密码重置成功",
                    "data": {
                        "detail": "密码重置成功，请使用新密码登录"
                    }
                }
            )
        ]
    ),
    400: OpenApiResponse(
        description="请求数据无效",
        examples=[
            OpenApiExample(
                name="密码不匹配响应",
                value={
                    "success": False,
                    "code": 4000,
                    "message": "请求数据无效",
                    "data": {
                        "confirm_password": ["Passwords do not match"]
                    }
                }
            ),
            OpenApiExample(
                name="令牌无效响应",
                value={
                    "success": False,
                    "code": 4000,
                    "message": "请求数据无效",
                    "data": {
                        "token": ["Invalid reset token"]
                    }
                }
            )
        ]
    )
} 