# 租户管理 API 文档

## 简介

租户管理 API 提供了对多租户系统中租户的创建、管理和配额控制功能。租户是系统中的一个隔离单元，拥有自己的用户、资源和权限。

## Base URL

```
/api/v1/tenants/
```

## 认证方式

所有 API 请求需要在 HTTP 头部包含有效的 JWT 令牌：

```
Authorization: Bearer <token>
```

## 权限控制

- **超级管理员**：可以访问所有租户相关 API
- **租户管理员**：仅能访问自己租户的配额使用情况和用户列表
- **普通用户**：无权访问租户管理 API

---

## API 端点

### 1. 获取租户列表

获取系统中所有租户的列表，支持搜索和状态过滤。

- **URL**: `/`
- **Method**: `GET`
- **权限要求**: 超级管理员
- **URL 参数**:
  - `search` (可选): 搜索关键词，支持租户名称、联系人姓名和联系人邮箱搜索
  - `status` (可选): 租户状态筛选 (`active`, `suspended`, `deleted`)
  - `page` (可选): 页码，默认为 1
  - `page_size` (可选): 每页条数，默认为 10
  
- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "获取成功",
      "data": {
        "count": 15,
        "next": "http://example.com/api/v1/tenants/?page=2",
        "previous": null,
        "results": [
          {
            "id": 1,
            "name": "测试租户1",
            "status": "active",
            "contact_name": "张三",
            "contact_email": "zhangsan@example.com",
            "contact_phone": "13800138000",
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-01-10T15:30:00Z"
          },
          // ... 更多租户
        ]
      }
    }
    ```

### 2. 创建租户

创建新的租户，包括租户名称、状态和联系人信息。

- **URL**: `/`
- **Method**: `POST`
- **权限要求**: 超级管理员
- **请求体**:
  ```json
  {
    "name": "新租户名称",
    "status": "active",
    "contact_name": "联系人姓名",
    "contact_email": "contact@example.com",
    "contact_phone": "13900139000"
  }
  ```

- **成功响应**:
  - 状态码: `201 Created`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "创建租户成功",
      "data": {
        "id": 16,
        "name": "新租户名称",
        "status": "active",
        "contact_name": "联系人姓名",
        "contact_email": "contact@example.com",
        "contact_phone": "13900139000",
        "created_at": "2023-08-15T09:12:34Z",
        "updated_at": "2023-08-15T09:12:34Z"
      }
    }
    ```

- **错误响应**:
  - 状态码: `400 Bad Request` (请求参数错误)
  - 状态码: `401 Unauthorized` (未认证)
  - 状态码: `403 Forbidden` (无权限)
  - 状态码: `500 Internal Server Error` (服务器错误)

### 3. 获取租户详情

获取指定租户的详细信息，包括配额和用户统计。

- **URL**: `/<tenant_id>/`
- **Method**: `GET`
- **权限要求**: 超级管理员
- **URL 参数**:
  - `tenant_id`: 租户 ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
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
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-10T15:30:00Z",
        "user_count": 5,
        "admin_count": 2
      }
    }
    ```

### 4. 更新租户信息

更新指定租户的信息，包括名称、状态和联系人信息。

- **URL**: `/<tenant_id>/`
- **Method**: `PUT` 或 `PATCH`
- **权限要求**: 超级管理员
- **URL 参数**:
  - `tenant_id`: 租户 ID
- **请求体** (PUT 方法需要提供完整数据，PATCH 方法可以只提供需要更新的字段):
  ```json
  {
    "name": "更新后的租户名称",
    "status": "active",
    "contact_name": "新联系人",
    "contact_email": "new-contact@example.com",
    "contact_phone": "13911112222"
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "更新租户成功",
      "data": {
        "id": 1,
        "name": "更新后的租户名称",
        "status": "active",
        "contact_name": "新联系人",
        "contact_email": "new-contact@example.com",
        "contact_phone": "13911112222",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-08-15T10:20:30Z",
        "user_count": 5,
        "admin_count": 2
      }
    }
    ```

### 5. 删除租户

软删除指定租户（标记为已删除状态）。

- **URL**: `/<tenant_id>/`
- **Method**: `DELETE`
- **权限要求**: 超级管理员
- **URL 参数**:
  - `tenant_id`: 租户 ID

- **成功响应**:
  - 状态码: `204 No Content`

### 6. 获取租户配额

获取指定租户的配额信息，包括最大用户数、管理员数量和存储空间等。

- **URL**: `/<tenant_id>/quota/`
- **Method**: `GET`
- **权限要求**: 超级管理员或租户管理员（租户管理员只能查看自己租户）
- **URL 参数**:
  - `tenant_id`: 租户 ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "获取成功",
      "data": {
        "id": 1,
        "tenant": 1,
        "tenant_name": "测试租户1",
        "max_users": 10,
        "max_admins": 2,
        "max_storage_mb": 1024,
        "max_products": 100,
        "current_storage_used_mb": 256,
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-08-01T10:00:00Z"
      }
    }
    ```

### 7. 更新租户配额

更新指定租户的配额设置，包括最大用户数、管理员数量和存储空间等。

- **URL**: `/<tenant_id>/quota/`
- **Method**: `PUT`
- **权限要求**: 超级管理员
- **URL 参数**:
  - `tenant_id`: 租户 ID
- **请求体**:
  ```json
  {
    "max_users": 20,
    "max_admins": 3,
    "max_storage_mb": 2048,
    "max_products": 200
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "更新配额成功",
      "data": {
        "id": 1,
        "tenant": 1,
        "tenant_name": "测试租户1",
        "max_users": 20,
        "max_admins": 3,
        "max_storage_mb": 2048,
        "max_products": 200,
        "current_storage_used_mb": 256,
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-08-15T11:25:40Z"
      }
    }
    ```

### 8. 获取租户配额使用情况

获取指定租户的配额使用情况，包括资源使用百分比。

- **URL**: `/<tenant_id>/quota/usage/`
- **Method**: `GET`
- **权限要求**: 超级管理员或租户管理员（租户管理员只能查看自己租户）
- **URL 参数**:
  - `tenant_id`: 租户 ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "获取成功",
      "data": {
        "tenant": 1,
        "tenant_name": "测试租户1",
        "max_users": 20,
        "max_admins": 3,
        "max_storage_mb": 2048,
        "max_products": 200,
        "current_storage_used_mb": 256,
        "usage_percentage": {
          "users": 25.0,
          "admins": 66.7,
          "storage": 12.5,
          "products": 10.0
        }
      }
    }
    ```

### 9. 暂停租户

将指定租户的状态更改为暂停状态。

- **URL**: `/<tenant_id>/suspend/`
- **Method**: `POST`
- **权限要求**: 超级管理员
- **URL 参数**:
  - `tenant_id`: 租户 ID
- **请求体** (可选):
  ```json
  {
    "reason": "账单逾期未付"
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "租户已暂停",
      "data": {
        "id": 1,
        "name": "测试租户1",
        "status": "suspended",
        "updated_at": "2023-08-15T13:40:00Z"
      }
    }
    ```

### 10. 激活租户

将指定的暂停租户状态更改为活跃状态。

- **URL**: `/<tenant_id>/activate/`
- **Method**: `POST`
- **权限要求**: 超级管理员
- **URL 参数**:
  - `tenant_id`: 租户 ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "租户已激活",
      "data": {
        "id": 1,
        "name": "测试租户1",
        "status": "active",
        "updated_at": "2023-08-15T14:05:30Z"
      }
    }
    ```

### 11. 获取租户用户列表

获取指定租户下的所有用户列表。

- **URL**: `/<tenant_id>/users/`
- **Method**: `GET`
- **权限要求**: 超级管理员或租户管理员（租户管理员只能查看自己租户）
- **URL 参数**:
  - `tenant_id`: 租户 ID
  - `search` (可选): 搜索关键词，支持用户名、邮箱和昵称搜索
  - `is_admin` (可选): 是否为管理员 (true/false)
  - `status` (可选): 用户状态筛选
  - `page` (可选): 页码，默认为 1
  - `page_size` (可选): 每页条数，默认为 10

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "获取成功",
      "data": {
        "count": 5,
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
            "tenant_name": "测试租户1",
            "is_admin": true,
            "is_member": false,
            "is_super_admin": false,
            "role": "租户管理员",
            "date_joined": "2023-02-01T10:00:00Z"
          },
          // ... 更多用户
        ]
      }
    }
    ```

## 状态码说明

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `204 No Content`: 请求成功处理，无返回内容
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未提供认证信息或认证失败
- `403 Forbidden`: 无权限访问所请求的资源
- `404 Not Found`: 请求的资源不存在
- `500 Internal Server Error`: 服务器内部错误

## 错误响应格式

当发生错误时，API 将返回包含错误详情的 JSON 对象：

```json
{
  "success": false,
  "code": 4000, // 错误代码，4xxx表示客户端错误，5xxx表示服务器错误
  "message": "错误消息",
  "data": {
    "detail": "详细错误说明", // 或字段级别的错误信息
    "field_name": ["字段错误说明"]
  }
}
```

## 错误代码说明

- `4000`: 请求参数错误
- `4001`: 认证失败
- `4003`: 权限不足
- `4004`: 资源不存在
- `5000`: 服务器内部错误 