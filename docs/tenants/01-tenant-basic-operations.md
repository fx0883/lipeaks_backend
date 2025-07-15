# 租户基础操作

本文档介绍租户管理模块的基础操作，包括获取租户列表、创建租户、获取租户详情、更新租户信息和删除租户。

## 1. 获取租户列表

### 接口信息

- **URL**: `/api/v1/tenants/`
- **方法**: GET
- **权限要求**: 超级管理员

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| search | string | 否 | 搜索关键词，支持租户名称、联系人姓名和联系人邮箱搜索 |
| status | string | 否 | 租户状态过滤，可选值：active（活跃）、suspended（暂停）、deleted（已删除）、all（所有） |
| page | integer | 否 | 页码，默认为1 |
| page_size | integer | 否 | 每页条数，默认为10 |

### 响应示例

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

## 2. 创建租户

### 接口信息

- **URL**: `/api/v1/tenants/`
- **方法**: POST
- **权限要求**: 超级管理员

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| name | string | 是 | 租户名称，最大长度100 |
| status | string | 否 | 租户状态，默认为"active"，可选值：active、suspended |
| contact_name | string | 否 | 联系人姓名，最大长度50 |
| contact_email | string | 否 | 联系人邮箱 |
| contact_phone | string | 否 | 联系人电话，最大长度20 |

### 请求示例

```json
{
  "name": "新租户",
  "status": "active",
  "contact_name": "王五",
  "contact_email": "wangwu@example.com",
  "contact_phone": "13700137000"
}
```

### 响应示例

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

## 3. 获取租户详情

### 接口信息

- **URL**: `/api/v1/tenants/{id}/`
- **方法**: GET
- **权限要求**: 超级管理员

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应示例

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

## 4. 更新租户信息

### 接口信息

- **URL**: `/api/v1/tenants/{id}/`
- **方法**: PUT
- **权限要求**: 超级管理员

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| name | string | 是 | 租户名称，最大长度100 |
| status | string | 否 | 租户状态，可选值：active、suspended |
| contact_name | string | 否 | 联系人姓名，最大长度50 |
| contact_email | string | 否 | 联系人邮箱 |
| contact_phone | string | 否 | 联系人电话，最大长度20 |

### 请求示例

```json
{
  "name": "更新后的租户名称",
  "status": "active",
  "contact_name": "张三",
  "contact_email": "zhangsan@example.com",
  "contact_phone": "13800138000"
}
```

### 响应示例

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

## 5. 删除租户

### 接口信息

- **URL**: `/api/v1/tenants/{id}/`
- **方法**: DELETE
- **权限要求**: 超级管理员

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应

- **状态码**: 204 No Content

## 6. 获取租户综合信息

### 接口信息

- **URL**: `/api/v1/tenants/{id}/comprehensive/`
- **方法**: GET
- **权限要求**: 超级管理员或该租户的管理员

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应示例

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

## 下一步

请查看[租户配额管理](./02-tenant-quota-management.md)，了解如何管理租户的资源配额。 