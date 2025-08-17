# 子账号管理 API

本文档详细描述了与子账号管理相关的API端点。子账号是指由普通成员创建的附属账号，用于代表成员执行特定操作，但不能直接登录系统。

## 1. 获取子账号列表

获取子账号列表，支持分页和搜索。

- **URL**: `/api/v1/members/sub-accounts/`
- **Method**: `GET`
- **权限要求**: 
  - 超级管理员可以查看所有子账号
  - 租户管理员只能查看自己租户内的子账号
  - 普通成员只能查看自己创建的子账号
  - 子账号不能查看子账号

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| search | string | 否 | 搜索关键词，支持用户名、邮箱、昵称和电话 |
| parent | integer | 否 | 父账号ID，用于筛选特定父账号下的子账号 |
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
        "id": 38,
        "username": "sub_account1",
        "email": "sub1@example.com",
        "phone": "13800138001",
        "nick_name": "子账号1",
        "first_name": "",
        "last_name": "",
        "is_active": false,
        "avatar": "http://localhost:8000/media/avatars/sub1.webp",
        "tenant": 17,
        "tenant_name": "cms_espressox",
        "is_sub_account": true,
        "parent": 34,
        "parent_username": "946fUn82cqfJzKIUq-zA1g-.IE@TOK_@MnWcIZRsnoZTGKnK",
        "date_joined": "2025-07-06T02:15:13.214361Z",
        "status": "active"
      },
      {
        "id": 39,
        "username": "sub_account2",
        "email": "sub2@example.com",
        "phone": "13800138002",
        "nick_name": "子账号2",
        "first_name": "",
        "last_name": "",
        "is_active": false,
        "avatar": "http://localhost:8000/media/avatars/sub2.webp",
        "tenant": 17,
        "tenant_name": "cms_espressox",
        "is_sub_account": true,
        "parent": 34,
        "parent_username": "946fUn82cqfJzKIUq-zA1g-.IE@TOK_@MnWcIZRsnoZTGKnK",
        "date_joined": "2025-07-06T02:16:13.214361Z",
        "status": "active"
      }
    ]
  }
}
```

## 2. 创建子账号

创建新的子账号。子账号将自动关联到当前登录的成员，并继承其租户。

- **URL**: `/api/v1/members/sub-accounts/`
- **Method**: `POST`
- **权限要求**: 需要普通成员权限，且不能是子账号

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| username | string | 是 | 用户名，必须唯一 |
| email | string | 是 | 电子邮箱 |
| phone | string | 否 | 手机号码 |
| nick_name | string | 否 | 昵称 |
| first_name | string | 否 | 名字 |
| last_name | string | 否 | 姓氏 |
| avatar | string | 否 | 头像URL |

### 请求示例

```json
{
  "username": "sub_account1",
  "email": "sub1@example.com",
  "phone": "13800138001",
  "nick_name": "子账号1",
  "first_name": "",
  "last_name": "",
  "avatar": ""
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 38,
    "username": "sub_account1",
    "email": "sub1@example.com",
    "phone": "13800138001",
    "nick_name": "子账号1",
    "first_name": "",
    "last_name": "",
    "avatar": ""
  }
}
```

## 3. 获取子账号详情

获取单个子账号的详细信息。

- **URL**: `/api/v1/members/sub-accounts/{id}/`
- **Method**: `GET`
- **权限要求**: 
  - 超级管理员可以查看任何子账号
  - 租户管理员只能查看自己租户内的子账号
  - 普通成员只能查看自己创建的子账号

### 路径参数

| 参数名 | 类型 | 描述 |
|-------|------|------|
| id | integer | 子账号ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 38,
    "username": "sub_account1",
    "email": "sub1@example.com",
    "phone": "13800138001",
    "nick_name": "子账号1",
    "first_name": "",
    "last_name": "",
    "is_active": false,
    "avatar": "http://localhost:8000/media/avatars/sub1.webp",
    "tenant": 17,
    "tenant_name": "cms_espressox",
    "is_sub_account": true,
    "parent": 34,
    "parent_username": "946fUn82cqfJzKIUq-zA1g-.IE@TOK_@MnWcIZRsnoZTGKnK",
    "date_joined": "2025-07-06T02:15:13.214361Z",
    "status": "active"
  }
}
```

## 4. 更新子账号信息

更新指定子账号的信息。

- **URL**: `/api/v1/members/sub-accounts/{id}/`
- **Method**: `PUT`
- **权限要求**: 
  - 超级管理员可以更新任何子账号
  - 租户管理员只能更新自己租户内的子账号
  - 普通成员只能更新自己创建的子账号

### 路径参数

| 参数名 | 类型 | 描述 |
|-------|------|------|
| id | integer | 子账号ID |

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| username | string | 是 | 用户名 |
| email | string | 是 | 电子邮箱 |
| phone | string | 否 | 手机号码 |
| nick_name | string | 否 | 昵称 |
| first_name | string | 否 | 名字 |
| last_name | string | 否 | 姓氏 |
| avatar | string | 否 | 头像URL |
| status | string | 否 | 状态(active/inactive/suspended) |

### 请求示例

```json
{
  "username": "sub_account1_updated",
  "email": "sub1_updated@example.com",
  "phone": "13800138001",
  "nick_name": "子账号1更新",
  "first_name": "",
  "last_name": "",
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
    "id": 38,
    "username": "sub_account1_updated",
    "email": "sub1_updated@example.com",
    "phone": "13800138001",
    "nick_name": "子账号1更新",
    "first_name": "",
    "last_name": "",
    "is_active": false,
    "avatar": "http://localhost:8000/media/avatars/sub1.webp",
    "tenant": 17,
    "tenant_name": "cms_espressox",
    "is_sub_account": true,
    "parent": 34,
    "parent_username": "946fUn82cqfJzKIUq-zA1g-.IE@TOK_@MnWcIZRsnoZTGKnK",
    "date_joined": "2025-07-06T02:15:13.214361Z",
    "status": "active"
  }
}
```

## 5. 部分更新子账号信息

部分更新指定子账号的信息。

- **URL**: `/api/v1/members/sub-accounts/{id}/`
- **Method**: `PATCH`
- **权限要求**: 
  - 超级管理员可以更新任何子账号
  - 租户管理员只能更新自己租户内的子账号
  - 普通成员只能更新自己创建的子账号

### 路径参数

| 参数名 | 类型 | 描述 |
|-------|------|------|
| id | integer | 子账号ID |

### 请求参数

与PUT方法相同，但所有字段都是可选的。

### 请求示例

```json
{
  "nick_name": "子账号1部分更新"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 38,
    "username": "sub_account1_updated",
    "email": "sub1_updated@example.com",
    "phone": "13800138001",
    "nick_name": "子账号1部分更新",
    "first_name": "",
    "last_name": "",
    "is_active": false,
    "avatar": "http://localhost:8000/media/avatars/sub1.webp",
    "tenant": 17,
    "tenant_name": "cms_espressox",
    "is_sub_account": true,
    "parent": 34,
    "parent_username": "946fUn82cqfJzKIUq-zA1g-.IE@TOK_@MnWcIZRsnoZTGKnK",
    "date_joined": "2025-07-06T02:15:13.214361Z",
    "status": "active"
  }
}
```

## 6. 删除子账号

删除（软删除）指定的子账号。

- **URL**: `/api/v1/members/sub-accounts/{id}/`
- **Method**: `DELETE`
- **权限要求**: 
  - 超级管理员可以删除任何子账号
  - 租户管理员只能删除自己租户内的子账号
  - 普通成员只能删除自己创建的子账号

### 路径参数

| 参数名 | 类型 | 描述 |
|-------|------|------|
| id | integer | 子账号ID |

### 响应

- **状态码**: 204 No Content

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

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": {
    "detail": "子账号不能创建子账号。"
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
      "该用户名已被使用"
    ],
    "email": [
      "该邮箱已被使用"
    ]
  }
}
```

## 技术实现说明

1. 子账号是Member模型的实例，通过parent字段关联到其父账号
2. 子账号的is_active字段默认为false，表示不能登录系统
3. 子账号自动继承父账号的租户
4. 创建子账号时不需要设置密码，因为子账号不能直接登录 