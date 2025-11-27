# Token 管理 API

## 验证访问令牌

### 接口信息

- **URL**: `/api/v1/auth/verify/`
- **方法**: `GET`
- **认证**: 需要（Bearer Token）
- **描述**: 验证访问令牌是否有效，并返回当前用户信息

### 请求头

| 请求头 | 必需 | 说明 |
|--------|------|------|
| `Authorization` | 是 | `Bearer {token}` |
| `X-Tenant-ID` | 是 | 租户 ID |

### 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `user` | object | 当前登录用户信息 |
| `user.id` | integer | 用户 ID |
| `user.username` | string | 用户名 |
| `user.email` | string | 邮箱 |
| `user.nick_name` | string | 昵称 |
| `user.avatar` | string | 头像路径 |
| `user.is_admin` | boolean | 是否为管理员 |
| `user.is_super_admin` | boolean | 是否为超级管理员 |
| `user.is_member` | boolean | 是否为 Member 用户 |
| `user.is_sub_account` | boolean | 是否为子账号 |
| `user.tenant_id` | integer | 租户 ID |
| `user.tenant_name` | string | 租户名称 |

### curl 示例

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://192.168.1.14:8000/api/v1/auth/verify/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 3"
```

### 成功响应示例 (200)

```json
{
    "success": true,
    "code": 2000,
    "message": "令牌有效",
    "data": {
        "user": {
            "id": 10,
            "username": "test02@qq.com",
            "email": "test02@qq.com",
            "nick_name": "Nihao",
            "avatar": "/media/avatars/c7e4e047-62d5-4002-b9b8-0f5e480ace78.jpg",
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

#### Token 已过期 (401)

```json
{
    "success": false,
    "code": 4001,
    "message": "Token has expired",
    "data": null,
    "error_code": "AUTH_TOKEN_EXPIRED"
}
```

#### Token 无效 (401)

```json
{
    "success": false,
    "code": 4001,
    "message": "Invalid token",
    "data": null,
    "error_code": "AUTH_INVALID_TOKEN"
}
```

---

## 刷新访问令牌

### 接口信息

- **URL**: `/api/v1/auth/refresh/`
- **方法**: `POST`
- **认证**: 不需要（使用 refresh_token）
- **描述**: 使用刷新令牌获取新的访问令牌和刷新令牌

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `refresh_token` | string | 是 | 刷新令牌 |

### 请求头

| 请求头 | 必需 | 说明 |
|--------|------|------|
| `Content-Type` | 是 | `application/json` |
| `X-Tenant-ID` | 是 | 租户 ID |

### 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `token` | string | 新的访问令牌 |
| `refresh_token` | string | 新的刷新令牌 |

### curl 示例

```bash
REFRESH_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST "http://192.168.1.14:8000/api/v1/auth/refresh/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }"
```

### 成功响应示例 (200)

```json
{
    "success": true,
    "code": 2000,
    "message": "Token refreshed successfully",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...(新token)",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...(新refresh_token)"
    }
}
```

### 错误响应示例

#### 刷新令牌无效 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "Invalid refresh token",
    "data": null
}
```

#### 刷新令牌已过期 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "Refresh token has expired",
    "data": null
}
```

---

## Token 使用流程

```
┌─────────────┐                              ┌─────────────┐
│   客户端    │                              │   服务器    │
└──────┬──────┘                              └──────┬──────┘
       │                                            │
       │  1. 登录请求 (username, password)          │
       │ ────────────────────────────────────────► │
       │                                            │
       │  2. 返回 token + refresh_token             │
       │ ◄──────────────────────────────────────── │
       │                                            │
       │  3. API 请求 (Authorization: Bearer token) │
       │ ────────────────────────────────────────► │
       │                                            │
       │  4. Token 过期 (401)                       │
       │ ◄──────────────────────────────────────── │
       │                                            │
       │  5. 刷新请求 (refresh_token)               │
       │ ────────────────────────────────────────► │
       │                                            │
       │  6. 返回新的 token + refresh_token         │
       │ ◄──────────────────────────────────────── │
       │                                            │
```

## 最佳实践

1. **Token 存储**: 将 token 存储在安全的位置（如 HttpOnly Cookie 或安全存储）
2. **Token 刷新**: 在 token 过期前主动刷新，避免用户体验中断
3. **错误处理**: 当收到 401 错误时，尝试刷新 token；如果刷新失败，引导用户重新登录
4. **Token 验证**: 定期调用 `/api/v1/auth/verify/` 验证 token 有效性
