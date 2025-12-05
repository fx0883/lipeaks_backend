# 重置租户管理员密码 API 文档

## API 概述

允许超级管理员或租户管理员重置其他用户（包括租户管理员）的密码。

## 接口信息

- **接口名称**: 管理员修改用户密码
- **接口路径**: `/api/v1/auth/{user_id}/change-password/`
- **请求方法**: `POST` / `PUT` / `PATCH`
- **认证方式**: Bearer Token（JWT）
- **权限要求**:
  - 必须已认证
  - 必须是管理员（租户管理员或超级管理员）

## 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | integer | 是 | 要重置密码的用户ID |

## 请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer {access_token} |
| Content-Type | string | 是 | application/json |

## 请求体参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| new_password | string | 是 | 新密码（需符合密码强度要求）|
| confirm_password | string | 是 | 确认新密码（必须与new_password一致）|

### 密码强度要求

- 长度至少8个字符
- 建议包含大小写字母、数字和特殊字符
- 不能是常见弱密码

## 响应格式

### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "密码修改成功",
  "data": {
    "detail": "密码修改成功"
  }
}
```

### 失败响应

#### 1. 数据验证失败 (400 Bad Request)

```json
{
  "success": false,
  "code": 4000,
  "message": "请求数据无效",
  "data": {
    "confirm_password": ["Passwords do not match"]
  }
}
```

#### 2. 权限不足 (403 Forbidden)

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": {
    "detail": "Only administrators can change other users' passwords"
  }
}
```

#### 3. 用户不存在 (404 Not Found)

```json
{
  "success": false,
  "code": 4004,
  "message": "用户不存在",
  "data": {
    "detail": "未找到指定用户"
  }
}
```

#### 4. 未认证 (401 Unauthorized)

```json
{
  "success": false,
  "code": 4001,
  "message": "未认证",
  "data": null
}
```

## 使用示例

### 步骤1: 超级管理员登录获取Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**响应示例:**

```json
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "is_admin": true,
      "is_super_admin": true
    }
  }
}
```

### 步骤2: 使用Token重置指定用户密码

```bash
curl -X POST http://localhost:8000/api/v1/auth/3/change-password/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "new_password": "NewSecurePass@2024",
    "confirm_password": "NewSecurePass@2024"
  }'
```

### 使用PUT方法

```bash
curl -X PUT http://localhost:8000/api/v1/auth/3/change-password/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "new_password": "NewSecurePass@2024",
    "confirm_password": "NewSecurePass@2024"
  }'
```

### 使用PATCH方法

```bash
curl -X PATCH http://localhost:8000/api/v1/auth/3/change-password/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "new_password": "NewSecurePass@2024",
    "confirm_password": "NewSecurePass@2024"
  }'
```

## PowerShell 示例

### 登录获取Token

```powershell
$loginBody = @{
    username = 'admin'
    password = 'admin123'
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/auth/login/' `
    -Method POST `
    -Headers @{'Content-Type'='application/json'} `
    -Body $loginBody

$token = $loginResponse.data.token
```

### 重置用户密码

```powershell
$resetBody = @{
    new_password = 'NewSecurePass@2024'
    confirm_password = 'NewSecurePass@2024'
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/auth/3/change-password/' `
    -Method POST `
    -Headers @{
        'Content-Type' = 'application/json'
        'Authorization' = "Bearer $token"
    } `
    -Body $resetBody

$response | ConvertTo-Json -Depth 3
```

## 注意事项

1. **Token有效期**: JWT Token有较长的有效期，建议定期刷新
2. **权限控制**:
   - 超级管理员可以重置任何用户的密码
   - 租户管理员只能重置自己租户内用户的密码
3. **密码安全**:
   - 新密码必须符合Django的密码验证规则
   - 两次输入的密码必须完全一致
4. **用户状态**: 只能重置未删除（is_deleted=False）的用户密码
5. **日志记录**: 所有密码重置操作都会被记录在系统日志中

## 常见错误排查

### 1. 401 未认证错误

- 检查Token是否正确
- 检查Token是否过期
- 确认Authorization header格式为 `Bearer {token}`

### 2. 403 权限不足

- 确认当前用户是管理员身份
- 租户管理员确认目标用户在同一租户内
- 检查用户账号是否被禁用

### 3. 404 用户不存在

- 确认user_id是否正确
- 检查目标用户是否已被删除（软删除）

### 4. 400 密码验证失败

- 确认两次输入的密码一致
- 检查密码是否符合强度要求
- 避免使用过于简单的密码

## API位置

- **视图文件**: `users/views/auth_views.py`
- **视图类**: `AdminChangePasswordView`
- **序列化器类**: `AdminChangePasswordSerializer`
- **URL配置**: `users/urls/auth_urls.py`

## 相关API

- 登录: `POST /api/v1/auth/login/`
- 修改自己的密码: `POST /api/v1/auth/me/change-password/`
- Token刷新: `POST /api/v1/auth/refresh/`
