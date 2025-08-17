# 用户管理 API 文档

## 简介

用户管理 API 提供了对系统中用户的创建、管理、认证和权限控制功能。支持多租户系统下的用户管理，包括超级管理员、租户管理员和普通用户角色。

## Base URL

```
/api/v1/users/
```

## 认证相关 Base URL

```
/api/v1/auth/
```

## 认证方式

除了登录和注册接口外，所有 API 请求需要在 HTTP 头部包含有效的 JWT 令牌：

```
Authorization: Bearer <token>
```

## 权限控制

- **超级管理员**：可以访问所有用户 API，包括创建其他超级管理员
- **租户管理员**：可以管理自己租户内的用户
- **普通用户**：只能访问和修改自己的信息

---

## API 端点

### 认证相关 API

#### 1. 用户注册

创建新用户账号。

- **URL**: `/auth/register/`
- **Method**: `POST`
- **权限要求**: 无需认证
- **请求体**:
  ```json
  {
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepassword",
    "password_confirm": "securepassword",
    "phone": "13900139000",
    "nick_name": "新用户",
    "tenant_id": 1  // 可选，关联到指定租户
  }
  ```

- **成功响应**:
  - 状态码: `201 Created`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "注册成功",
      "data": {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
          "id": 10,
          "username": "newuser",
          "email": "user@example.com",
          "nick_name": "新用户",
          "is_admin": false,
          "is_member": true,
          "avatar": "",
          "tenant_id": 1,
          "tenant_name": "测试租户"
        }
      }
    }
    ```

#### 2. 用户登录

用户登录并获取访问令牌。

- **URL**: `/auth/login/`
- **Method**: `POST`
- **权限要求**: 无需认证
- **请求体**:
  ```json
  {
    "username": "existinguser",
    "password": "userpassword"
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "登录成功",
      "data": {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
          "id": 5,
          "username": "existinguser",
          "email": "existing@example.com",
          "nick_name": "老用户",
          "is_admin": true,
          "is_super_admin": false,
          "avatar": "/media/avatars/user5.png",
          "tenant_id": 1,
          "tenant_name": "测试租户"
        }
      }
    }
    ```

- **错误响应**:
  - 状态码: `401 Unauthorized`
  - 响应体:
    ```json
    {
      "success": false,
      "code": 4002,
      "message": "用户名或密码错误",
      "data": null
    }
    ```

#### 3. 刷新访问令牌

使用刷新令牌获取新的访问令牌。

- **URL**: `/auth/refresh/`
- **Method**: `POST`
- **权限要求**: 无需认证
- **请求体**:
  ```json
  {
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "令牌刷新成功",
      "data": {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
      }
    }
    ```

#### 4. 验证访问令牌

验证当前令牌是否有效。

- **URL**: `/auth/verify/`
- **Method**: `GET`
- **权限要求**: 需要认证
  
- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "success": true,
      "code": 2000,
      "message": "令牌有效",
      "data": {
        "is_valid": true,
        "user": {
          "id": 5,
          "username": "existinguser",
          "email": "existing@example.com",
          "nick_name": "老用户",
          "is_admin": true,
          "is_super_admin": false
        }
      }
    }
    ```

#### 5. 修改用户密码

修改当前登录用户的密码。

- **URL**: `/auth/me/change-password/`
- **Method**: `POST`
- **权限要求**: 需要认证
- **请求体**:
  ```json
  {
    "old_password": "oldpassword",
    "new_password": "newpassword",
    "new_password_confirm": "newpassword"
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "detail": "密码修改成功"
    }
    ```

### 用户管理 API

#### 1. 获取当前用户信息

获取当前登录用户的详细信息。

- **URL**: `/me/`
- **Method**: `GET`
- **权限要求**: 需要认证
  
- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "id": 5,
      "username": "existinguser",
      "email": "existing@example.com",
      "phone": "13800138001",
      "nick_name": "老用户",
      "first_name": "张",
      "last_name": "三",
      "is_active": true,
      "avatar": "https://example.com/media/avatars/user5.png",
      "tenant": 1,
      "tenant_name": "测试租户",
      "is_admin": true,
      "is_member": false,
      "is_super_admin": false,
      "role": "租户管理员",
      "date_joined": "2023-02-01T10:00:00Z"
    }
    ```

#### 2. 更新当前用户信息

更新当前登录用户的基本信息。

- **URL**: `/me/`
- **Method**: `PUT`
- **权限要求**: 需要认证
- **请求体**:
  ```json
  {
    "phone": "13911112222",
    "nick_name": "新昵称",
    "first_name": "李",
    "last_name": "四",
    "email": "new-email@example.com"
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体: 返回更新后的用户信息，格式同"获取当前用户信息"的响应

#### 3. 上传用户头像

上传并更新当前用户的头像。

- **URL**: `/me/upload-avatar/`
- **Method**: `POST`
- **权限要求**: 需要认证
- **Content-Type**: `multipart/form-data`
- **请求参数**:
  - `avatar`: 文件，最大2MB，支持JPG、PNG、GIF、WEBP或BMP格式

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "detail": "头像上传成功",
      "avatar": "https://example.com/media/avatars/user-avatar.jpg"
    }
    ```

#### 4. 获取用户列表

获取系统中的用户列表，支持搜索、分页和过滤。

- **URL**: `/`
- **Method**: `GET`
- **权限要求**: 需要管理员权限
- **URL 参数**:
  - `search` (可选): 搜索关键词，支持用户名、邮箱、昵称和手机号码搜索
  - `status` (可选): 用户状态筛选
  - `is_admin` (可选): 是否为管理员 (true/false)
  - `is_sub_account` (可选): 是否为子账号 (true/false)
  - `parent` (可选): 父账号ID，用于筛选特定父账号下的子账号
  - `tenant_id` (可选): 租户ID，用于筛选特定租户下的用户
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
        "count": 10,
        "next": "http://example.com/api/v1/users/?page=2",
        "previous": null,
        "results": [
          {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "phone": "13800138000",
            "nick_name": "系统管理员",
            "tenant": null,
            "tenant_name": null,
            "is_admin": true,
            "is_member": false,
            "is_super_admin": true,
            "role": "超级管理员"
          },
          // ... 更多用户
        ]
      }
    }
    ```

#### 5. 创建用户

创建新用户。

- **URL**: `/`
- **Method**: `POST`
- **权限要求**: 需要管理员权限
- **请求体**:
  ```json
  {
    "username": "newuser",
    "email": "newuser@example.com",
    "phone": "13900139000",
    "nick_name": "新用户",
    "first_name": "王",
    "last_name": "五",
    "password": "securepassword",
    "password_confirm": "securepassword",
    "tenant_id": 1,
    "is_admin": false,
    "is_member": true,
    "avatar": null
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
        "id": 10,
        "username": "newuser",
        "email": "newuser@example.com",
        "phone": "13900139000",
        "nick_name": "新用户",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_admin": false,
        "is_member": true,
        "is_super_admin": false,
        "role": "普通成员"
      }
    }
    ```

#### 6. 获取用户详情

获取指定用户的详细信息。

- **URL**: `/<user_id>/`
- **Method**: `GET`
- **权限要求**: 需要管理员权限或是本人
- **URL 参数**:
  - `user_id`: 用户 ID
  
- **成功响应**:
  - 状态码: `200 OK`
  - 响应体: 返回用户详细信息，格式同"获取当前用户信息"的响应

#### 7. 更新用户信息

更新指定用户的信息。

- **URL**: `/<user_id>/`
- **Method**: `PUT` 或 `PATCH`
- **权限要求**: 需要管理员权限或是本人
- **URL 参数**:
  - `user_id`: 用户 ID
- **请求体**:
  格式同"更新当前用户信息"的请求体

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体: 返回更新后的用户信息，格式同"获取当前用户信息"的响应

#### 8. 删除用户

软删除指定用户。

- **URL**: `/<user_id>/`
- **Method**: `DELETE`
- **权限要求**: 需要管理员权限，且不能删除当前登录账号
- **URL 参数**:
  - `user_id`: 用户 ID
  
- **成功响应**:
  - 状态码: `204 No Content`

#### 9. 更新用户角色

更新指定用户的角色（管理员/普通成员）。

- **URL**: `/<user_id>/change-role/`
- **Method**: `POST`
- **权限要求**: 需要管理员权限
- **URL 参数**:
  - `user_id`: 用户 ID
- **请求体**:
  ```json
  {
    "is_admin": true,
    "is_member": false
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "id": 10,
      "is_admin": true,
      "is_member": false
    }
    ```

#### 10. 创建超级管理员

创建新的超级管理员账号。

- **URL**: `/super-admin/create/`
- **Method**: `POST`
- **权限要求**: 需要超级管理员权限
- **请求体**:
  ```json
  {
    "username": "superadmin2",
    "email": "super2@example.com",
    "password": "securepassword",
    "password_confirm": "securepassword",
    "phone": "13922223333",
    "nick_name": "超管2号",
    "first_name": "超级",
    "last_name": "管理员",
    "avatar": null
  }
  ```

- **成功响应**:
  - 状态码: `201 Created`
  - 响应体: 返回创建的超级管理员信息

#### 11. 授予超级管理员权限

将普通用户提升为超级管理员。

- **URL**: `/<user_id>/grant-super-admin/`
- **Method**: `POST`
- **权限要求**: 需要超级管理员权限
- **URL 参数**:
  - `user_id`: 用户 ID
  
- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "detail": "已将用户 username 提升为超级管理员"
    }
    ```

#### 12. 撤销超级管理员权限

撤销指定用户的超级管理员权限。

- **URL**: `/<user_id>/revoke-super-admin/`
- **Method**: `POST`
- **权限要求**: 需要超级管理员权限，且不能撤销自己的权限
- **URL 参数**:
  - `user_id`: 用户 ID
  
- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "detail": "已撤销用户 username 的超级管理员权限"
    }
    ```

#### 13. 创建子账号

创建一个与当前用户关联的子账号。

- **URL**: `/sub-account/create/`
- **Method**: `POST`
- **权限要求**: 需要认证
- **请求体**:
  ```json
  {
    "username": "subaccount1",
    "email": "sub1@example.com",
    "phone": "13900139001",
    "nick_name": "子账号1",
    "password": "123456",  // 可选，默认为"123456"
    "avatar": null
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
        "phone": "13900139001",
        "nick_name": "子账号1",
        "parent": 10,
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": true
      }
    }
    ```

#### 14. 为特定用户上传头像

管理员为指定用户上传头像。

- **URL**: `/<user_id>/upload-avatar/`
- **Method**: `POST`
- **权限要求**: 需要管理员权限
- **URL 参数**:
  - `user_id`: 用户 ID
- **Content-Type**: `multipart/form-data`
- **请求参数**:
  - `avatar`: 文件，最大2MB，支持JPG、PNG、GIF、WEBP或BMP格式

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
    ```json
    {
      "detail": "头像上传成功",
      "avatar": "https://example.com/media/avatars/user-avatar.jpg"
    }
    ```

#### 15. 获取租户下的用户列表

获取指定租户下的所有用户。

- **URL**: `/tenant/<tenant_id>/`
- **Method**: `GET`
- **权限要求**: 需要管理员权限
- **URL 参数**:
  - `tenant_id`: 租户 ID
  - `search` (可选): 搜索关键词
  - `is_admin` (可选): 是否为管理员 (true/false)
  - `status` (可选): 用户状态筛选
  - `page` (可选): 页码，默认为 1
  - `page_size` (可选): 每页条数，默认为 10
  
- **成功响应**:
  - 状态码: `200 OK`
  - 响应体: 返回用户列表，格式同"获取用户列表"的响应

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
- `4001`: 认证令牌已过期
- `4002`: 用户名或密码错误
- `4003`: 权限不足
- `4004`: 资源不存在
- `5000`: 服务器内部错误 