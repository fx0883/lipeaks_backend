# 用户注册 API

## Member 自助注册

### 接口信息

- **URL**: `/api/v1/auth/member/register/`
- **方法**: `POST`
- **认证**: 不需要
- **描述**: Member 用户自助注册账号

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `username` | string | 是 | 用户名（唯一） |
| `email` | string | 是 | 邮箱地址（唯一） |
| `password` | string | 是 | 密码 |
| `password_confirm` | string | 是 | 确认密码 |

### 请求头

| 请求头 | 必需 | 说明 |
|--------|------|------|
| `Content-Type` | 是 | `application/json` |
| `X-Tenant-ID` | 是 | 租户 ID（新用户将注册到该租户） |

### 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `token` | string | 访问令牌 (JWT) |
| `refresh_token` | string | 刷新令牌 |
| `user` | object | 用户信息对象 |
| `user.id` | integer | 用户 ID |
| `user.username` | string | 用户名 |
| `user.email` | string | 邮箱 |
| `user.nick_name` | string | 昵称 |
| `user.avatar` | string | 头像完整 URL（包含 domain，新注册用户为空） |
| `user.is_admin` | boolean | 是否为管理员 |
| `user.is_super_admin` | boolean | 是否为超级管理员 |
| `user.is_member` | boolean | 是否为 Member 用户 |
| `user.is_sub_account` | boolean | 是否为子账号 |
| `user.tenant_id` | integer | 租户 ID |
| `user.tenant_name` | string | 租户名称 |

### curl 示例

```bash
curl -X POST "http://192.168.1.14:8000/api/v1/auth/member/register/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "username": "newmember",
    "email": "newmember@example.com",
    "password": "SecurePassword123",
    "password_confirm": "SecurePassword123"
  }'
```

### 成功响应示例 (200)

```json
{
    "success": true,
    "code": 2000,
    "message": "注册成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user": {
            "id": 13,
            "username": "newmember",
            "email": "newmember@example.com",
            "nick_name": "",
            "avatar": "",
            "is_admin": false,
            "is_super_admin": false,
            "is_member": true,
            "is_sub_account": false,
            "tenant_id": 3,
            "tenant_name": "填色"
        }
    }
}
```

### 错误响应示例

#### 参数缺失 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "username": ["该字段是必填项。"],
        "password": ["该字段是必填项。"]
    }
}
```

#### 用户名已存在 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "username": ["该用户名已被使用"]
    }
}
```

#### 邮箱已存在 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "email": ["该邮箱已被注册"]
    }
}
```

#### 两次密码不一致 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "password_confirm": ["两次输入的密码不一致"]
    }
}
```

---

## 用户注册（管理员接口）

### 接口信息

- **URL**: `/api/v1/auth/register/`
- **方法**: `POST`
- **认证**: 不需要（但需要租户配置）
- **描述**: 用户注册接口（主要用于管理员创建账号）

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `username` | string | 是 | 用户名 |
| `email` | string | 是 | 邮箱地址 |
| `password` | string | 是 | 密码 |
| `password_confirm` | string | 是 | 确认密码 |

### curl 示例

```bash
curl -X POST "http://192.168.1.14:8000/api/v1/auth/register/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePassword123",
    "password_confirm": "SecurePassword123"
  }'
```

### 错误响应示例

#### 租户操作失败 (400)

```json
{
    "success": false,
    "code": 4100,
    "message": "Tenant operation failed",
    "data": null,
    "error_code": "TENANT_ERROR"
}
```

> **注意**: 此接口通常需要特定的租户配置才能使用。对于普通 Member 注册，请使用 `/api/v1/auth/member/register/` 接口。

---

## API 对比

| 接口 | 用途 | 创建用户类型 |
|------|------|-------------|
| `/api/v1/auth/member/register/` | Member 自助注册 | Member 用户 |
| `/api/v1/auth/register/` | 管理员创建用户 | 普通用户（需要配置） |

## 密码要求

密码应满足以下要求（具体规则由系统配置决定）：

- 最小长度：8 个字符
- 建议包含大小写字母、数字和特殊字符
- 不能与用户名相同

## 注册流程

```
┌─────────────┐                              ┌─────────────┐
│   客户端    │                              │   服务器    │
└──────┬──────┘                              └──────┬──────┘
       │                                            │
       │  1. 注册请求                               │
       │     (username, email, password, ...)       │
       │ ────────────────────────────────────────► │
       │                                            │
       │                   服务器验证:               │
       │                   - 用户名唯一             │
       │                   - 邮箱唯一               │
       │                   - 密码符合要求           │
       │                                            │
       │  2. 返回 token + user 信息                 │
       │ ◄──────────────────────────────────────── │
       │                                            │
       │  3. 使用 token 访问其他 API                │
       │ ────────────────────────────────────────► │
       │                                            │
```

## 注册后续操作

注册成功后，用户可以：

1. 使用返回的 `token` 直接访问需要认证的 API
2. 调用 `/api/v1/members/me/` 获取或更新个人资料
3. 上传头像等
