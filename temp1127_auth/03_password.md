# 密码管理 API

## 修改自己的密码

### 接口信息

- **URL**: `/api/v1/auth/me/change-password/`
- **方法**: `POST` / `PUT` / `PATCH`（三种方法效果相同）
- **认证**: 需要（Bearer Token）
- **描述**: 修改当前登录用户的密码

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `old_password` | string | 是 | 当前密码 |
| `new_password` | string | 是 | 新密码 |
| `new_password_confirm` | string | 是 | 确认新密码 |

### 请求头

| 请求头 | 必需 | 说明 |
|--------|------|------|
| `Authorization` | 是 | `Bearer {token}` |
| `Content-Type` | 是 | `application/json` |
| `X-Tenant-ID` | 是 | 租户 ID |

### curl 示例

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 使用 POST 方法
curl -X POST "http://192.168.1.14:8000/api/v1/auth/me/change-password/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "old_password": "CurrentPassword123",
    "new_password": "NewPassword456",
    "new_password_confirm": "NewPassword456"
  }'

# 使用 PUT 方法（效果相同）
curl -X PUT "http://192.168.1.14:8000/api/v1/auth/me/change-password/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "old_password": "CurrentPassword123",
    "new_password": "NewPassword456",
    "new_password_confirm": "NewPassword456"
  }'

# 使用 PATCH 方法（效果相同）
curl -X PATCH "http://192.168.1.14:8000/api/v1/auth/me/change-password/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "old_password": "CurrentPassword123",
    "new_password": "NewPassword456",
    "new_password_confirm": "NewPassword456"
  }'
```

### 成功响应示例 (200)

```json
{
    "success": true,
    "code": 2000,
    "message": "密码修改成功",
    "data": {}
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
        "new_password_confirm": ["该字段是必填项。"]
    }
}
```

#### 原密码错误 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "old_password": ["原密码不正确"]
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
        "new_password_confirm": ["两次输入的密码不一致"]
    }
}
```

---

## 管理员修改指定用户密码

### 接口信息

- **URL**: `/api/v1/auth/{user_id}/change-password/`
- **方法**: `POST` / `PUT` / `PATCH`
- **认证**: 需要（Bearer Token，需要管理员权限）
- **描述**: 管理员修改指定用户的密码

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | integer | 目标用户 ID |

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `old_password` | string | 是 | 用户当前密码 |
| `new_password` | string | 是 | 新密码 |
| `new_password_confirm` | string | 是 | 确认新密码 |

### curl 示例

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
USER_ID=10

curl -X POST "http://192.168.1.14:8000/api/v1/auth/${USER_ID}/change-password/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "old_password": "UserCurrentPassword",
    "new_password": "NewPassword456",
    "new_password_confirm": "NewPassword456"
  }'
```

### 错误响应示例

#### 权限不足（非管理员）(403)

```json
{
    "success": false,
    "code": 4003,
    "message": "Only administrators can change other users' passwords",
    "data": null,
    "error_code": "AUTH_PERMISSION_DENIED"
}
```

> **注意**: 此接口仅限管理员使用。普通 Member 用户调用此接口会返回权限不足错误。

---

## 请求密码重置

### 接口信息

- **URL**: `/api/v1/auth/password-reset/request/`
- **方法**: `POST`
- **认证**: 不需要
- **描述**: 发送密码重置邮件到指定邮箱

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `email` | string | 是 | 注册邮箱 |

### 请求头

| 请求头 | 必需 | 说明 |
|--------|------|------|
| `Content-Type` | 是 | `application/json` |
| `X-Tenant-ID` | 是 | 租户 ID |

### curl 示例

```bash
curl -X POST "http://192.168.1.14:8000/api/v1/auth/password-reset/request/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "email": "test02@qq.com"
  }'
```

### 成功响应示例 (200)

```json
{
    "success": true,
    "code": 2000,
    "message": "如果该邮箱存在，密码重置链接已发送",
    "data": {
        "detail": "如果该邮箱存在，密码重置链接已发送"
    }
}
```

> **注意**: 出于安全考虑，无论邮箱是否存在，都返回相同的成功消息。

---

## 验证密码重置令牌

### 接口信息

- **URL**: `/api/v1/auth/password-reset/verify/`
- **方法**: `POST`
- **认证**: 不需要
- **描述**: 验证密码重置令牌是否有效

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `token` | string | 是 | 密码重置令牌（从邮件中获取） |
| `confirm_password` | string | 是 | 确认密码（验证时需要） |

### curl 示例

```bash
curl -X POST "http://192.168.1.14:8000/api/v1/auth/password-reset/verify/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "token": "reset-token-from-email",
    "confirm_password": "any"
  }'
```

### 成功响应示例 (200)

```json
{
    "success": true,
    "code": 2000,
    "message": "令牌有效",
    "data": {
        "valid": true
    }
}
```

### 错误响应示例

#### 令牌无效 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "请求数据无效",
    "data": {
        "token": ["Invalid reset token"]
    }
}
```

---

## 确认密码重置

### 接口信息

- **URL**: `/api/v1/auth/password-reset/confirm/`
- **方法**: `POST`
- **认证**: 不需要
- **描述**: 使用重置令牌设置新密码

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `token` | string | 是 | 密码重置令牌 |
| `new_password` | string | 是 | 新密码 |
| `confirm_password` | string | 是 | 确认新密码 |

### curl 示例

```bash
curl -X POST "http://192.168.1.14:8000/api/v1/auth/password-reset/confirm/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "token": "reset-token-from-email",
    "new_password": "NewPassword456",
    "confirm_password": "NewPassword456"
  }'
```

### 成功响应示例 (200)

```json
{
    "success": true,
    "code": 2000,
    "message": "密码重置成功",
    "data": {}
}
```

### 错误响应示例

#### 令牌无效 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "请求数据无效",
    "data": {
        "token": ["Invalid reset token"]
    }
}
```

#### 两次密码不一致 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "请求数据无效",
    "data": {
        "confirm_password": ["两次输入的密码不一致"]
    }
}
```

---

## 密码重置流程

```
┌─────────────┐                              ┌─────────────┐
│   客户端    │                              │   服务器    │
└──────┬──────┘                              └──────┬──────┘
       │                                            │
       │  1. 请求重置 (email)                       │
       │ ────────────────────────────────────────► │
       │                                            │
       │  2. 返回"邮件已发送"                        │
       │ ◄──────────────────────────────────────── │
       │                                            │
       │                    用户收到重置邮件          │
       │                    点击链接获取 token        │
       │                                            │
       │  3. 验证令牌 (token)（可选）                │
       │ ────────────────────────────────────────► │
       │                                            │
       │  4. 返回令牌是否有效                        │
       │ ◄──────────────────────────────────────── │
       │                                            │
       │  5. 确认重置 (token, new_password)         │
       │ ────────────────────────────────────────► │
       │                                            │
       │  6. 返回"重置成功"                          │
       │ ◄──────────────────────────────────────── │
       │                                            │
```
