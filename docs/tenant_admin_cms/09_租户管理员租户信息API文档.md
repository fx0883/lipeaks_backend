# 租户管理员 租户信息 API 文档

## 适用范围
- 面向租户管理员（Tenant Admin）用户
- 用于查看本租户的完整信息和配额使用情况
- 租户管理员只能查看自己租户的信息

## 基础信息
- 前缀：`/api/v1/tenants/`
- 认证：Bearer Token（必须）
- 权限：租户管理员（is_admin=True）

---

## 1. 获取租户完整信息

### 接口信息
- 路径：GET `/api/v1/tenants/{id}/comprehensive/`
- 说明：获取租户的所有信息，包括基本信息、配额信息和企业信息

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| id | integer | 是 | 租户ID（必须是当前管理员所属的租户） |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取租户信息成功",
  "data": {
    "id": 1,
    "name": "测试租户",
    "code": "test-tenant",
    "status": "active",
    "contact_name": "张三",
    "contact_email": "zhangsan@example.com",
    "contact_phone": "13800138000",
    "description": "这是一个测试租户",
    "logo": "/media/tenants/logo.png",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-20T10:30:00Z",
    "quota": {
      "max_users": 100,
      "max_admins": 10,
      "max_storage_mb": 10240,
      "max_articles": 1000,
      "max_categories": 50,
      "max_tags": 200
    },
    "usage": {
      "current_users": 25,
      "current_admins": 3,
      "current_storage_mb": 2048,
      "current_articles": 150,
      "current_categories": 10,
      "current_tags": 45
    },
    "enterprise_info": {
      "company_name": "测试有限公司",
      "industry": "互联网",
      "address": "北京市朝阳区xxx",
      "website": "https://example.com"
    }
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | integer | 租户ID |
| name | string | 租户名称 |
| code | string | 租户代码 |
| status | string | 租户状态（active/suspended） |
| contact_name | string | 联系人姓名 |
| contact_email | string | 联系人邮箱 |
| contact_phone | string | 联系人电话 |
| description | string | 租户描述 |
| logo | string | 租户Logo URL |
| quota | object | 配额信息 |
| usage | object | 当前使用情况 |
| enterprise_info | object | 企业信息 |

### 失败响应（403 无权限）
```json
{
  "success": false,
  "code": 4030,
  "message": "您没有权限访问此租户的信息",
  "data": null
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/tenants/1/comprehensive/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 2. 获取租户配额使用情况

### 接口信息
- 路径：GET `/api/v1/tenants/{id}/quota/usage/`
- 说明：获取租户资源配额的使用情况

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| id | integer | 是 | 租户ID（必须是当前管理员所属的租户） |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "tenant": 1,
    "tenant_name": "ésir",
    "max_users": 10,
    "max_admins": 2,
    "max_storage_mb": 1024,
    "max_products": 100,
    "current_storage_used_mb": 0,
    "usage_percentage": {
      "users": 10.0,
      "admins": 50.0,
      "storage": 0.0,
      "products": 0.0
    }
  }
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/tenants/1/quota/usage/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 3. 获取租户用户列表

### 接口信息
- 路径：GET `/api/v1/tenants/{id}/users/`
- 说明：获取本租户下的所有管理员用户列表

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| search | string | 否 | 搜索关键词（用户名、邮箱、昵称） |
| is_admin | boolean | 否 | 是否为管理员 |
| status | string | 否 | 用户状态 |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 2,
        "username": "tenant_admin",
        "email": "admin@tenant.com",
        "phone": "13800138001",
        "nick_name": "租户管理员",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_admin": true,
        "is_member": false,
        "is_super_admin": false,
        "role": "租户管理员",
        "is_active": true,
        "date_joined": "2024-01-05T10:00:00Z"
      }
    ]
  }
}
```

### curl 调用示例
```bash
# 获取租户用户列表
curl -X GET "http://localhost:8000/api/v1/tenants/1/users/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 搜索用户
curl -X GET "http://localhost:8000/api/v1/tenants/1/users/?search=admin" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 只获取管理员
curl -X GET "http://localhost:8000/api/v1/tenants/1/users/?is_admin=true" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 错误码说明

| 错误码 | HTTP状态码 | 说明 |
|-------|-----------|------|
| 2000 | 200 | 操作成功 |
| 4001 | 401 | 认证失败 |
| 4003 | 403 | 权限不足 |
| 4030 | 403 | 无权限访问此租户 |
| 4004 | 404 | 资源不存在 |
| 4040 | 404 | 租户不存在 |
| 5000 | 500 | 服务器内部错误 |

## 权限说明

1. **租户隔离**：租户管理员只能查看自己所属租户的信息
2. **只读权限**：租户管理员只能查看租户信息，不能修改租户配额等设置
3. **用户列表**：只能查看本租户下的管理员用户，不包括Member用户（Member通过`/api/v1/admin/members/`管理）
