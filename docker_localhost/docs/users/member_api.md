# 普通用户(Member) API 文档

## 简介

普通用户(Member) API 提供了对系统中普通用户和子账号的创建、管理和查询功能。这些API专门设计用于操作`Member`模型的实例，区别于管理员用户API。

## Base URL

```
/api/v1/members/
```

## 认证方式

所有 API 请求需要在 HTTP 头部包含有效的 JWT 令牌：

```
Authorization: Bearer <token>
```

## 权限控制

- **超级管理员**：可以访问所有普通用户 API
- **租户管理员**：可以管理自己租户内的普通用户
- **普通用户**：只能访问和修改自己的信息和子账号

---

## API 端点

### 1. 获取普通用户列表

获取系统中的普通用户列表，支持分页和搜索。

- **URL**: `/`
- **Method**: `GET`
- **权限要求**: 需要管理员权限
- **查询参数**:
  - `search`: 搜索关键词，支持用户名、邮箱、昵称和电话
  - `status`: 用户状态筛选 (active/inactive/suspended)
  - `is_sub_account`: 是否为子账号 (true/false)
  - `parent`: 父账号ID，用于筛选特定父账号下的子账号
  - `tenant_id`: 租户ID，用于筛选特定租户下的用户
  - `page`: 页码
  - `page_size`: 每页结果数

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "获取成功",
      "data": {
        "count": 10,
        "next": "http://example.com/api/v1/members/?page=2",
        "previous": null,
        "results": [
          {
            "id": 10,
            "username": "member1",
            "email": "member1@example.com",
            "phone": "13900139000",
            "nick_name": "普通用户1",
            "is_active": true,
            "avatar": "/media/avatars/member1.png",
            "tenant": 1,
            "tenant_name": "测试租户",
            "is_sub_account": false,
            "parent": null,
            "parent_username": null,
            "date_joined": "2023-01-01T12:00:00Z"
          }
        ]
      }
    }
    ```

### 2. 创建普通用户

创建新的普通用户账号。

- **URL**: `/`
- **Method**: `POST`
- **权限要求**: 需要管理员权限
- **请求体**:
  ```json
  {
    "username": "newmember",
    "email": "newmember@example.com",
    "password": "securepassword",
    "password_confirm": "securepassword",
    "phone": "13900139001",
    "nick_name": "新普通用户",
    "tenant_id": 1
  }
  ```

- **成功响应**:
  - 状态码: `201 Created`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2001,
      "message": "创建成功",
      "data": {
        "id": 11,
        "username": "newmember",
        "email": "newmember@example.com",
        "phone": "13900139001",
        "nick_name": "新普通用户",
        "is_active": true,
        "avatar": "",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": false,
        "parent": null,
        "parent_username": null,
        "date_joined": "2023-01-05T15:30:00Z"
      }
    }
    ```

### 3. 获取普通用户详情

获取单个普通用户的详细信息。

- **URL**: `/<int:pk>/`
- **Method**: `GET`
- **权限要求**: 管理员可以查看任何普通用户；普通用户只能查看自己
- **URL 参数**:
  - `pk`: 普通用户ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "获取成功",
      "data": {
        "id": 11,
        "username": "newmember",
        "email": "newmember@example.com",
        "phone": "13900139001",
        "nick_name": "新普通用户",
        "first_name": "",
        "last_name": "",
        "is_active": true,
        "avatar": "/media/avatars/newmember.png",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": false,
        "parent": null,
        "parent_username": null,
        "date_joined": "2023-01-05T15:30:00Z"
      }
    }
    ```

### 4. 更新普通用户信息

更新指定普通用户的信息。

- **URL**: `/<int:pk>/`
- **Method**: `PUT`
- **权限要求**: 管理员可以更新任何普通用户；普通用户只能更新自己
- **URL 参数**:
  - `pk`: 普通用户ID
- **请求体**:
  ```json
  {
    "nick_name": "更新后的昵称",
    "phone": "13900139002",
    "is_active": true,
    "status": "active"
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "更新成功",
      "data": {
        "id": 11,
        "username": "newmember",
        "email": "newmember@example.com",
        "phone": "13900139002",
        "nick_name": "更新后的昵称",
        "is_active": true,
        "avatar": "/media/avatars/newmember.png",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": false,
        "parent": null,
        "parent_username": null,
        "date_joined": "2023-01-05T15:30:00Z"
      }
    }
    ```

### 5. 删除普通用户

删除指定普通用户（软删除）。

- **URL**: `/<int:pk>/`
- **Method**: `DELETE`
- **权限要求**: 只有管理员可以删除普通用户
- **URL 参数**:
  - `pk`: 普通用户ID

- **成功响应**:
  - 状态码: `204 No Content`

### 6. 获取当前普通用户信息

获取当前登录的普通用户的详细信息。

- **URL**: `/me/`
- **Method**: `GET`
- **权限要求**: 需要普通用户认证

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "获取成功",
      "data": {
        "id": 11,
        "username": "newmember",
        "email": "newmember@example.com",
        "phone": "13900139002",
        "nick_name": "更新后的昵称",
        "first_name": "",
        "last_name": "",
        "is_active": true,
        "avatar": "/media/avatars/newmember.png",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": false,
        "parent": null,
        "parent_username": null,
        "date_joined": "2023-01-05T15:30:00Z"
      }
    }
    ```

### 7. 更新当前普通用户信息

更新当前登录的普通用户的基本信息。

- **URL**: `/me/`
- **Method**: `PUT`
- **权限要求**: 需要普通用户认证
- **请求体**:
  ```json
  {
    "nick_name": "我的新昵称",
    "phone": "13900139003",
    "first_name": "张",
    "last_name": "三"
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "更新成功",
      "data": {
        "id": 11,
        "username": "newmember",
        "email": "newmember@example.com",
        "phone": "13900139003",
        "nick_name": "我的新昵称",
        "first_name": "张",
        "last_name": "三",
        "is_active": true,
        "avatar": "/media/avatars/newmember.png",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": false,
        "parent": null,
        "parent_username": null,
        "date_joined": "2023-01-05T15:30:00Z"
      }
    }
    ```

### 8. 创建子账号

创建一个与当前普通用户关联的子账号。

- **URL**: `/sub-account/create/`
- **Method**: `POST`
- **权限要求**: 需要普通用户认证
- **请求体**:
  ```json
  {
    "username": "subaccount1",
    "email": "sub1@example.com",
    "nick_name": "子账号1",
    "phone": "13900139004"
  }
  ```

- **成功响应**:
  - 状态码: `201 Created`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2001,
      "message": "创建成功",
      "data": {
        "id": 12,
        "username": "subaccount1",
        "email": "sub1@example.com",
        "phone": "13900139004",
        "nick_name": "子账号1",
        "is_active": false,
        "avatar": "",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": true,
        "parent": 11,
        "parent_username": "newmember",
        "date_joined": "2023-01-10T09:15:00Z"
      }
    }
    ```

### 9. 上传普通用户头像

上传并更新当前登录普通用户的头像图片。

- **URL**: `/me/upload-avatar/`
- **Method**: `POST`
- **权限要求**: 需要普通用户认证
- **内容类型**: `multipart/form-data`
- **表单字段**:
  - `avatar`: 图片文件 (JPG, PNG, GIF, WEBP 或 BMP)

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "头像上传成功",
      "data": {
        "detail": "头像上传成功",
        "avatar": "/media/avatars/newmember-123456.jpg"
      }
    }
    ```

### 10. 为指定普通用户上传头像

管理员为指定普通用户上传头像。

- **URL**: `/<int:pk>/upload-avatar/`
- **Method**: `POST`
- **权限要求**: 需要管理员权限
- **URL 参数**:
  - `pk`: 普通用户ID
- **内容类型**: `multipart/form-data`
- **表单字段**:
  - `avatar`: 图片文件 (JPG, PNG, GIF, WEBP 或 BMP)

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "头像上传成功",
      "data": {
        "detail": "头像上传成功",
        "avatar": "/media/avatars/subaccount1-123456.jpg"
      }
    }
    ```

## 错误响应

### 1. 未认证错误

- 状态码: `401 Unauthorized`
- 响应体:
  ```json
  {
    "success": false,
    "code": 4001,
    "message": "未认证或认证已过期",
    "data": {
      "detail": "身份认证信息未提供。"
    }
  }
  ```

### 2. 权限错误

- 状态码: `403 Forbidden`
- 响应体:
  ```json
  {
    "success": false,
    "code": 4003,
    "message": "权限不足",
    "data": {
      "detail": "您没有执行该操作的权限。"
    }
  }
  ```

### 3. 资源不存在

- 状态码: `404 Not Found`
- 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "资源不存在",
    "data": {
      "detail": "未找到。"
    }
  }
  ```

### 4. 请求验证错误

- 状态码: `400 Bad Request`
- 响应体:
  ```json
  {
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
      "username": ["该字段不能为空。"],
      "email": ["请输入一个有效的电子邮件地址。"]
    }
  }
  ```

## 状态码说明

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `204 No Content`: 删除成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或认证已过期
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误 