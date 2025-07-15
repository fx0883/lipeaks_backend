# 租户API完整参考

本文档提供租户管理模块所有API端点的详细参考信息。

## API端点概览

| 端点 | 方法 | 描述 | 权限要求 |
|------|------|------|---------|
| `/api/v1/tenants/` | GET | 获取租户列表 | 超级管理员 |
| `/api/v1/tenants/` | POST | 创建新租户 | 超级管理员 |
| `/api/v1/tenants/{id}/` | GET | 获取租户详情 | 超级管理员 |
| `/api/v1/tenants/{id}/` | PUT | 更新租户信息 | 超级管理员 |
| `/api/v1/tenants/{id}/` | DELETE | 删除租户 | 超级管理员 |
| `/api/v1/tenants/{id}/comprehensive/` | GET | 获取租户综合信息 | 超级管理员或该租户管理员 |
| `/api/v1/tenants/{id}/quota/` | GET | 获取租户配额 | 超级管理员或该租户管理员 |
| `/api/v1/tenants/{id}/quota/` | PUT | 更新租户配额 | 超级管理员 |
| `/api/v1/tenants/{id}/quota/usage/` | GET | 获取租户配额使用情况 | 超级管理员或该租户管理员 |
| `/api/v1/tenants/{id}/suspend/` | POST | 暂停租户 | 超级管理员 |
| `/api/v1/tenants/{id}/activate/` | POST | 激活租户 | 超级管理员 |
| `/api/v1/tenants/{id}/users/` | GET | 获取租户用户列表 | 超级管理员或该租户管理员 |

## 1. 获取租户列表

### 请求

```
GET /api/v1/tenants/
```

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| search | string | 否 | 搜索关键词，支持租户名称、联系人姓名和联系人邮箱搜索 |
| status | string | 否 | 租户状态过滤，可选值：active（活跃）、suspended（暂停）、deleted（已删除）、all（所有） |
| page | integer | 否 | 页码，默认为1 |
| page_size | integer | 否 | 每页条数，默认为10 |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 2,
    "next": null,
    "previous": null,
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
  }
}
```

**错误响应 (403 Forbidden)**

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": null
}
```

## 2. 创建新租户

### 请求

```
POST /api/v1/tenants/
```

### 请求体

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| name | string | 是 | 租户名称，最大长度100 |
| status | string | 否 | 租户状态，默认为"active"，可选值：active、suspended |
| contact_name | string | 否 | 联系人姓名，最大长度50 |
| contact_email | string | 否 | 联系人邮箱 |
| contact_phone | string | 否 | 联系人电话，最大长度20 |

### 响应

**成功响应 (201 Created)**

```json
{
  "success": true,
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
}
```

**错误响应 (400 Bad Request)**

```json
{
  "success": false,
  "code": 4000,
  "message": "参数错误",
  "data": {
    "name": ["租户名称已存在"]
  }
}
```

## 3. 获取租户详情

### 请求

```
GET /api/v1/tenants/{id}/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 1,
    "name": "测试租户1",
    "status": "active",
    "contact_name": "张三",
    "contact_email": "zhangsan@example.com",
    "contact_phone": "13800138000",
    "created_at": "2025-04-20T10:00:00Z",
    "updated_at": "2025-04-20T10:00:00Z",
    "user_count": 5,
    "admin_count": 2
  }
}
```

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "租户不存在",
  "data": null
}
```

## 4. 更新租户信息

### 请求

```
PUT /api/v1/tenants/{id}/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 请求体

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| name | string | 是 | 租户名称，最大长度100 |
| status | string | 否 | 租户状态，可选值：active、suspended |
| contact_name | string | 否 | 联系人姓名，最大长度50 |
| contact_email | string | 否 | 联系人邮箱 |
| contact_phone | string | 否 | 联系人电话，最大长度20 |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": 2000,
  "message": "更新租户成功",
  "data": {
    "id": 1,
    "name": "更新后的租户名称",
    "status": "active",
    "contact_name": "张三",
    "contact_email": "zhangsan@example.com",
    "contact_phone": "13800138000",
    "created_at": "2025-04-20T10:00:00Z",
    "updated_at": "2025-04-22T11:00:00Z",
    "user_count": 5,
    "admin_count": 2
  }
}
```

**错误响应 (400 Bad Request)**

```json
{
  "success": false,
  "code": 4000,
  "message": "参数错误",
  "data": {
    "name": ["租户名称已存在"]
  }
}
```

## 5. 删除租户

### 请求

```
DELETE /api/v1/tenants/{id}/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应

**成功响应 (204 No Content)**

无响应体

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "租户不存在",
  "data": null
}
```

## 6. 获取租户综合信息

### 请求

```
GET /api/v1/tenants/{id}/comprehensive/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
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
    "is_active": true,
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
    "business_info": {
      "company_name": "测试科技有限公司",
      "legal_representative": "张三",
      "unified_social_credit_code": "91310000MA1FL1000X",
      "verification_status": "verified",
      "verification_status_display": "已验证"
    }
  }
}
```

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "租户不存在",
  "data": null
}
```

## 7. 获取租户配额

### 请求

```
GET /api/v1/tenants/{id}/quota/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
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
}
```

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "租户不存在",
  "data": null
}
```

## 8. 更新租户配额

### 请求

```
PUT /api/v1/tenants/{id}/quota/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 请求体

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| max_users | integer | 是 | 最大用户数 |
| max_admins | integer | 是 | 最大管理员数 |
| max_storage_mb | integer | 是 | 最大存储空间(MB) |
| max_products | integer | 是 | 最大产品数 |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
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
}
```

**错误响应 (400 Bad Request)**

```json
{
  "success": false,
  "code": 4000,
  "message": "参数错误",
  "data": {
    "max_users": ["该值不能小于当前已有用户数"],
    "max_storage_mb": ["存储空间必须是整数"]
  }
}
```

## 9. 获取租户配额使用情况

### 请求

```
GET /api/v1/tenants/{id}/quota/usage/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "tenant": 1,
    "tenant_name": "测试租户1",
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
  }
}
```

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "租户不存在",
  "data": null
}
```

## 10. 暂停租户

### 请求

```
POST /api/v1/tenants/{id}/suspend/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": 2000,
  "message": "租户已暂停",
  "data": {
    "id": 1,
    "name": "测试租户1",
    "status": "suspended",
    "updated_at": "2025-04-22T10:00:00Z"
  }
}
```

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "租户不存在",
  "data": null
}
```

## 11. 激活租户

### 请求

```
POST /api/v1/tenants/{id}/activate/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": 2000,
  "message": "租户已激活",
  "data": {
    "id": 1,
    "name": "测试租户1",
    "status": "active",
    "updated_at": "2025-04-22T10:00:00Z"
  }
}
```

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "租户不存在",
  "data": null
}
```

## 12. 获取租户用户列表

### 请求

```
GET /api/v1/tenants/{id}/users/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| search | string | 否 | 搜索关键词，支持用户名、邮箱和昵称搜索 |
| is_admin | boolean | 否 | 是否为管理员 (true/false) |
| status | string | 否 | 用户状态筛选 |
| page | integer | 否 | 页码，默认为1 |
| page_size | integer | 否 | 每页条数，默认为10 |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 2,
        "username": "tenant_admin",
        "email": "tenant_admin@example.com",
        "nick_name": "租户管理员",
        "is_active": true,
        "is_admin": true,
        "status": "active",
        "date_joined": "2025-04-21T10:00:00Z"
      },
      {
        "id": 3,
        "username": "tenant_user",
        "email": "tenant_user@example.com",
        "nick_name": "租户用户",
        "is_active": true,
        "is_admin": false,
        "status": "active",
        "date_joined": "2025-04-21T11:00:00Z"
      }
    ]
  }
}
```

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "租户不存在",
  "data": null
}
```

## 状态码说明

| 状态码 | 描述 |
|-------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功，无内容返回 |
| 400 | 请求参数错误 |
| 401 | 未认证或认证失败 |
| 403 | 权限不足 |
| 404 | 请求的资源不存在 |
| 500 | 服务器内部错误 |

## 业务状态码说明

| 业务状态码 | 描述 |
|----------|------|
| 2000 | 操作成功 |
| 4000 | 参数错误 |
| 4001 | 未认证或认证失败 |
| 4003 | 权限不足 |
| 4004 | 资源不存在 |
| 5000 | 服务器内部错误 |

## 常见错误处理

### 认证失败

```json
{
  "success": false,
  "code": 4001,
  "message": "认证失败，请重新登录",
  "data": null
}
```

### 权限不足

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足，无法访问该资源",
  "data": null
}
```

### 资源不存在

```json
{
  "success": false,
  "code": 4004,
  "message": "租户不存在",
  "data": null
}
```

### 服务器错误

```json
{
  "success": false,
  "code": 5000,
  "message": "服务器内部错误",
  "data": null
}
``` 