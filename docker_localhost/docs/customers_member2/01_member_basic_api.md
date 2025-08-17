# 成员基本操作 API

本文档详细描述了与成员(Member)基本操作相关的API端点。

## 1. 获取成员列表

获取系统中的成员列表，支持分页和搜索。

- **URL**: `/api/v1/members/`
- **Method**: `GET`
- **权限要求**: 需要管理员权限或成员权限（成员只能查看自己和自己的子账号）

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| search | string | 否 | 搜索关键词，支持用户名、邮箱、昵称和电话 |
| status | string | 否 | 用户状态筛选 (active/inactive/suspended) |
| is_sub_account | boolean | 否 | 是否为子账号 (true/false) |
| parent | integer | 否 | 父账号ID，用于筛选特定父账号下的子账号 |
| tenant_id | integer | 否 | 租户ID，用于筛选特定租户下的用户 |
| page | integer | 否 | 页码，默认为1 |
| page_size | integer | 否 | 每页结果数，默认为10 |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 2,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 34,
        "username": "946fUn82cqfJzKIUq-zA1g-.IE@TOK_@MnWcIZRsnoZTGKnK",
        "email": "user@example.com",
        "phone": "string",
        "nick_name": "string",
        "first_name": "string",
        "last_name": "string",
        "is_active": true,
        "avatar": "http://localhost:8000/media/avatars/1a4ee062-c297-4ae4-9657-8b93695edf7e.webp",
        "tenant": 17,
        "tenant_name": "cms_espressox",
        "is_sub_account": false,
        "parent": null,
        "parent_username": null,
        "date_joined": "2025-07-06T01:24:59.048885Z",
        "status": "active"
      },
      {
        "id": 35,
        "username": "95nEg5OcyUrCtiTrvMwwf9h_9nQmW2fSKUiSZp+w4DPA3ZQWMq-l67W-3Tb_yvqi0tU034HvmcVL_57pdZsiO5jX",
        "email": "user@example.com",
        "phone": "string",
        "nick_name": "string",
        "first_name": "string",
        "last_name": "string",
        "is_active": true,
        "avatar": "http://localhost:8000/string",
        "tenant": 17,
        "tenant_name": "cms_espressox",
        "is_sub_account": false,
        "parent": null,
        "parent_username": null,
        "date_joined": "2025-07-06T01:29:14.932961Z",
        "status": "active"
      }
    ]
  }
}
```

## 2. 创建成员

创建新的成员账号。

- **URL**: `/api/v1/members/`
- **Method**: `POST`
- **权限要求**: 需要管理员权限

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| username | string | 是 | 用户名，必须唯一 |
| email | string | 是 | 电子邮箱 |
| password | string | 是 | 密码 |
| password_confirm | string | 是 | 确认密码，必须与password一致 |
| phone | string | 否 | 手机号码 |
| nick_name | string | 否 | 昵称 |
| first_name | string | 否 | 名字 |
| last_name | string | 否 | 姓氏 |
| avatar | string | 否 | 头像URL |
| tenant_id | integer | 否 | 租户ID，超级管理员必填，租户管理员会自动使用当前租户 |

### 请求示例

```json
{
  "username": "@ET+ZuXvG7e",
  "email": "user@example.com",
  "phone": "string",
  "nick_name": "string",
  "first_name": "string",
  "last_name": "string",
  "password": "string123",
  "password_confirm": "string123",
  "avatar": "string"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 37,
    "username": "@ET+ZuXvG7e",
    "email": "user@example.com",
    "phone": "string",
    "nick_name": "string",
    "first_name": "string",
    "last_name": "string",
    "avatar": "string"
  }
}
```

## 3. 获取成员详情

获取单个成员的详细信息。

- **URL**: `/api/v1/members/{id}/`
- **Method**: `GET`
- **权限要求**: 超级管理员可查看任何成员；租户管理员只能查看自己租户的成员；成员只能查看自己和自己的子账号

### 路径参数

| 参数名 | 类型 | 描述 |
|-------|------|------|
| id | integer | 成员ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 37,
    "username": "@ET+ZuXvG7e",
    "email": "user@example.com",
    "phone": "string",
    "nick_name": "string",
    "first_name": "string",
    "last_name": "string",
    "is_active": true,
    "avatar": "http://localhost:8000/string",
    "tenant": 17,
    "tenant_name": "cms_espressox",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2025-07-06T01:35:13.214361Z",
    "status": "active"
  }
}
```

## 4. 更新成员信息

更新指定成员的信息。

- **URL**: `/api/v1/members/{id}/`
- **Method**: `PUT`
- **权限要求**: 超级管理员可更新任何成员；租户管理员只能更新自己租户的成员；成员只能更新自己

### 路径参数

| 参数名 | 类型 | 描述 |
|-------|------|------|
| id | integer | 成员ID |

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| username | string | 是 | 用户名 |
| email | string | 是 | 电子邮箱 |
| phone | string | 否 | 手机号码 |
| nick_name | string | 否 | 昵称 |
| first_name | string | 否 | 名字 |
| last_name | string | 否 | 姓氏 |
| is_active | boolean | 否 | 是否激活 |
| status | string | 否 | 状态(active/inactive/suspended) |

### 请求示例

```json
{
  "username": "acUJ6u@KeTpEn9m2cv4A9du6bgZ4OXzeVXlBrS@sxVQdJFeLjxaB-ennR-kr-zwRZ5NE4W_rmTvZT1Vk",
  "email": "user@example.com",
  "phone": "string",
  "nick_name": "string",
  "first_name": "string",
  "last_name": "string",
  "is_active": true,
  "status": "active"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 37,
    "username": "acUJ6u@KeTpEn9m2cv4A9du6bgZ4OXzeVXlBrS@sxVQdJFeLjxaB-ennR-kr-zwRZ5NE4W_rmTvZT1Vk",
    "email": "user@example.com",
    "phone": "string",
    "nick_name": "string",
    "first_name": "string",
    "last_name": "string",
    "is_active": true,
    "avatar": "http://localhost:8000/string",
    "tenant": 17,
    "tenant_name": "cms_espressox",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2025-07-06T01:35:13.214361Z",
    "status": "active"
  }
}
```

## 5. 部分更新成员信息

部分更新指定成员的信息。

- **URL**: `/api/v1/members/{id}/`
- **Method**: `PATCH`
- **权限要求**: 超级管理员可更新任何成员；租户管理员只能更新自己租户的成员；成员只能更新自己

### 路径参数

| 参数名 | 类型 | 描述 |
|-------|------|------|
| id | integer | 成员ID |

### 请求参数

与PUT方法相同，但所有字段都是可选的。

### 请求示例

```json
{
  "username": "xkvdDku+laBMj-tnrI_Cjzh.bt-z4uWieiT5aqnAUc6+cysZE0xNP7UFyTqthFKDtpAmLVZT04kLdE_q@pTlG",
  "email": "user@example.com",
  "phone": "string",
  "nick_name": "string",
  "first_name": "string",
  "last_name": "string",
  "is_active": true,
  "status": "active"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 37,
    "username": "xkvdDku+laBMj-tnrI_Cjzh.bt-z4uWieiT5aqnAUc6+cysZE0xNP7UFyTqthFKDtpAmLVZT04kLdE_q@pTlG",
    "email": "user@example.com",
    "phone": "string",
    "nick_name": "string",
    "first_name": "string",
    "last_name": "string",
    "is_active": true,
    "avatar": "http://localhost:8000/string",
    "tenant": 17,
    "tenant_name": "cms_espressox",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2025-07-06T01:35:13.214361Z",
    "status": "active"
  }
}
```

## 6. 删除成员

删除（软删除）指定的成员。

- **URL**: `/api/v1/members/{id}/`
- **Method**: `DELETE`
- **权限要求**: 超级管理员可删除任何成员；租户管理员只能删除自己租户的成员；成员不能删除自己

### 路径参数

| 参数名 | 类型 | 描述 |
|-------|------|------|
| id | integer | 成员ID |

### 响应

- **状态码**: 204 No Content

## 7. 获取当前登录成员信息

获取当前登录成员的详细信息。

- **URL**: `/api/v1/members/me/`
- **Method**: `GET`
- **权限要求**: 需要成员身份验证

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 37,
    "username": "xkvdDku+laBMj-tnrI_Cjzh.bt-z4uWieiT5aqnAUc6+cysZE0xNP7UFyTqthFKDtpAmLVZT04kLdE_q@pTlG",
    "email": "user@example.com",
    "phone": "string",
    "nick_name": "string",
    "first_name": "string",
    "last_name": "string",
    "is_active": true,
    "avatar": "http://localhost:8000/string",
    "tenant": 17,
    "tenant_name": "cms_espressox",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2025-07-06T01:35:13.214361Z",
    "status": "active"
  }
}
```

## 错误响应

### 401 未认证

```json
{
  "success": false,
  "code": 4001,
  "message": "认证失败",
  "data": {
    "detail": "身份认证信息未提供。"
  }
}
```

### 403 权限不足

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

### 404 资源不存在

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

### 400 请求参数错误

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "username": [
      "该字段不能为空。"
    ],
    "email": [
      "请输入有效的电子邮件地址。"
    ]
  }
}
``` 