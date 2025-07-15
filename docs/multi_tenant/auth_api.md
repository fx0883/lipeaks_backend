# 认证API

本文档描述了系统的认证相关API，包括用户注册、登录、令牌刷新等功能。

## 用户注册

新用户注册。

**请求URL**：`/api/v1/auth/register/`

**请求方式**：`POST`

**请求头**：
- Content-Type: application/json

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| username | string | 是 | 用户名，长度为3-30个字符，只能包含字母、数字、下划线 |
| password | string | 是 | 密码，长度至少8位，必须包含大小写字母、数字和特殊字符 |
| email | string | 是 | 邮箱地址 |
| phone | string | 是 | 手机号码 |
| real_name | string | 否 | 真实姓名 |
| tenant_id | integer | 否 | 所属租户ID（如果是超级管理员创建租户管理员，此处可为null） |

**请求示例**：

```json
{
  "username": "testuser",
  "password": "Test@123",
  "email": "testuser@example.com",
  "phone": "13900138000",
  "real_name": "测试用户",
  "tenant_id": 1
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "注册成功",
  "data": {
    "user": {
      "id": 100,
      "username": "testuser",
      "email": "testuser@example.com",
      "phone": "13900138000",
      "real_name": "测试用户",
      "avatar": null,
      "tenant_id": 1,
      "is_admin": false,
      "is_active": true,
      "date_joined": "2023-10-28T10:30:00Z"
    },
    "token": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

**错误响应**：

```json
{
  "code": 4000,
  "message": "注册失败",
  "data": {
    "username": ["该租户下此用户名已被使用"],
    "email": ["该租户下此邮箱已被注册"],
    "phone": ["该租户下此手机号已被注册"],
    "password": ["密码强度不足，必须包含大小写字母、数字和特殊字符"]
  }
}
```

```json
{
  "code": 4004,
  "message": "未找到",
  "data": {
    "detail": "指定的租户不存在或已被删除"
  }
}
```

```json
{
  "code": 4009,
  "message": "租户状态异常",
  "data": {
    "detail": "该租户已被暂停，无法注册新用户"
  }
}
```

## 用户登录

用户登录并获取令牌。

**请求URL**：`/api/v1/auth/login/`

**请求方式**：`POST`

**请求头**：
- Content-Type: application/json

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**请求示例**：

```json
{
  "username": "testuser",
  "password": "Test@123"
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "user": {
      "id": 100,
      "username": "testuser",
      "email": "testuser@example.com",
      "phone": "13900138000",
      "real_name": "测试用户",
      "avatar": "https://example.com/avatar/100.jpg",
      "tenant_id": 1,
      "tenant_name": "测试租户1",
      "is_admin": false,
      "is_active": true,
      "last_login": "2023-10-28T15:30:00Z",
      "date_joined": "2023-10-15T10:30:00Z"
    },
    "token": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    },
    "permissions": [
      "view_user",
      "add_user",
      "change_user",
      "delete_user",
      "view_project",
      "add_project"
    ]
  }
}
```

**错误响应**：

```json
{
  "code": 4001,
  "message": "验证失败",
  "data": {
    "detail": "用户名或密码错误"
  }
}
```

```json
{
  "code": 4003,
  "message": "帐号已停用",
  "data": {
    "detail": "您的帐号已被管理员停用，请联系管理员"
  }
}
```

```json
{
  "code": 4009,
  "message": "租户状态异常",
  "data": {
    "detail": "您所属的租户已被暂停，无法登录系统"
  }
}
```

## 刷新令牌

使用刷新令牌获取新的访问令牌。

**请求URL**：`/api/v1/auth/token/refresh/`

**请求方式**：`POST`

**请求头**：
- Content-Type: application/json

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| refresh | string | 是 | 刷新令牌 |

**请求示例**：

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "刷新成功",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

**错误响应**：

```json
{
  "code": 4001,
  "message": "验证失败",
  "data": {
    "detail": "刷新令牌无效或已过期"
  }
}
```

## 验证令牌

验证访问令牌是否有效。

**请求URL**：`/api/v1/auth/token/verify/`

**请求方式**：`POST`

**请求头**：
- Content-Type: application/json

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| token | string | 是 | 访问令牌 |

**请求示例**：

```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "验证成功",
  "data": {}
}
```

**错误响应**：

```json
{
  "code": 4001,
  "message": "验证失败",
  "data": {
    "detail": "令牌无效或已过期"
  }
}
```

## 修改密码

已登录用户修改自己的密码。

**请求URL**：`/api/v1/auth/change-password/`

**请求方式**：`POST`

**请求头**：
- Content-Type: application/json
- Authorization: Bearer {access_token}

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码，长度至少8位，必须包含大小写字母、数字和特殊字符 |
| confirm_password | string | 是 | 确认新密码，必须与new_password相同 |

**请求示例**：

```json
{
  "old_password": "Test@123",
  "new_password": "NewTest@456",
  "confirm_password": "NewTest@456"
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "密码修改成功",
  "data": {}
}
```

**错误响应**：

```json
{
  "code": 4000,
  "message": "修改失败",
  "data": {
    "old_password": ["旧密码不正确"],
    "new_password": ["密码强度不足，必须包含大小写字母、数字和特殊字符"],
    "confirm_password": ["两次输入的密码不一致"]
  }
}
```

```json
{
  "code": 4001,
  "message": "验证失败",
  "data": {
    "detail": "令牌无效或已过期"
  }
}
```

## 找回密码 - 发送验证码

通过邮箱或手机号发送验证码，用于找回密码。

**请求URL**：`/api/v1/auth/reset-password/send-code/`

**请求方式**：`POST`

**请求头**：
- Content-Type: application/json

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| type | string | 是 | 验证类型，可选值：email（邮箱）、phone（手机） |
| value | string | 是 | 邮箱地址或手机号码 |

**请求示例**：

```json
{
  "type": "email",
  "value": "testuser@example.com"
}
```

或

```json
{
  "type": "phone",
  "value": "13900138000"
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "验证码已发送",
  "data": {
    "expires_in": 300
  }
}
```

**错误响应**：

```json
{
  "code": 4000,
  "message": "发送失败",
  "data": {
    "detail": "该邮箱不存在或未绑定任何用户"
  }
}
```

```json
{
  "code": 4029,
  "message": "请求过于频繁",
  "data": {
    "detail": "请求过于频繁，请在60秒后重试"
  }
}
```

## 找回密码 - 验证并重置

验证验证码并重置密码。

**请求URL**：`/api/v1/auth/reset-password/verify/`

**请求方式**：`POST`

**请求头**：
- Content-Type: application/json

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| type | string | 是 | 验证类型，可选值：email（邮箱）、phone（手机） |
| value | string | 是 | 邮箱地址或手机号码 |
| code | string | 是 | 收到的验证码 |
| new_password | string | 是 | 新密码，长度至少8位，必须包含大小写字母、数字和特殊字符 |
| confirm_password | string | 是 | 确认新密码，必须与new_password相同 |

**请求示例**：

```json
{
  "type": "email",
  "value": "testuser@example.com",
  "code": "123456",
  "new_password": "NewTest@456",
  "confirm_password": "NewTest@456"
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "密码重置成功",
  "data": {}
}
```

**错误响应**：

```json
{
  "code": 4000,
  "message": "验证失败",
  "data": {
    "code": ["验证码错误或已过期"],
    "new_password": ["密码强度不足，必须包含大小写字母、数字和特殊字符"],
    "confirm_password": ["两次输入的密码不一致"]
  }
}
```

```json
{
  "code": 4004,
  "message": "未找到",
  "data": {
    "detail": "该邮箱不存在或未绑定任何用户"
  }
}
``` 