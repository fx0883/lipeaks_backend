# Member 认证相关 API（统一响应版）

## 适用范围
- 面向 iOS / Android / 鸿蒙 / Web / 小程序等所有客户端。
- 文档仅提供平台无关的说明、字段与示例，不包含任意具体语言/框架代码。

## 统一返回结构
- 全部接口遵循 `docs/api_response/01_response_format_standard.md`。
- 响应固定结构：success(boolean), code(int), message(string), data(any), error_code(optional string)。
- 分页返回使用 data.pagination + data.results 结构。

## 认证域名与前置条件
- 基础前缀：`/api/v1/auth/`
- Header 说明：
  - Authorization: Bearer <access_token>（除登录/注册/刷新/重置外）
  - X-Tenant-ID: <租户ID>（Member 必须；User/管理员 禁止）

## 1. 成员自助注册

### 接口信息
- **接口地址**: `POST /api/v1/auth/member/register/`
- **权限要求**: 无需认证，匿名访问
- **功能说明**: Member在指定租户下自助注册账号

### 请求头
```
X-Tenant-ID: {tenant_id}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| username | string | 是 | 用户名，全局唯一 | "member001" | 3-30字符，只能包含字母、数字、下划线 |
| email | string | 是 | 邮箱地址，全局唯一 | "member001@example.com" | 有效的邮箱格式 |
| password | string | 是 | 登录密码 | "password123" | 最少8字符，包含大小写字母和数字 |
| password_confirm | string | 是 | 密码确认 | "password123" | 必须与password相同 |
| phone | string | 否 | 手机号码，租户内唯一 | "13800138000" | 有效的手机号码格式 |
| nick_name | string | 否 | 昵称 | "测试成员" | 最长50字符 |
| wechat_id | string | 否 | 微信ID | "wechat123" | 最长100字符 |

### 业务规则
- ✅ 租户ID通过请求头`X-Tenant-ID`指定，必填
- ✅ 同租户内username/email/phone唯一性校验
- ✅ 密码强度自动校验（长度、复杂度）
- ✅ 仅Member类型用户允许注册
- ❌ 不支持管理员注册
- 成功（201）：
{
  "success": true,
  "code": 2000,
  "message": "注册成功",
  "data": {
    "token": "<access_token>",
    "refresh_token": "<refresh_token>",
    "user": {
      "id": 10, "username": "member001", "email": "member001@example.com",
      "nick_name": "测试成员", "avatar": "", "is_member": true,
      "is_admin": false, "is_super_admin": false, "is_sub_account": false,
      "tenant_id": 1, "tenant_name": "测试租户"
    }
  }
}
- 失败（400 示例）：
{
  "success": false, "code": 4000, "message": "注册失败",
  "data": {"username": ["Username already used in this tenant"]},
  "error_code": "VALIDATION_ERROR"
}
- 规则要点：同租户内 username/email/phone 唯一；密码强度校验；仅 Member 允许携带 `X-Tenant-ID`。

## 2. 用户登录（Member / 管理员）

### 接口信息
- **接口地址**: `POST /api/v1/auth/login/`
- **权限要求**: 无需认证，匿名访问
- **功能说明**: 用户登录，支持Member和管理员两种用户类型

### 请求头（条件必填）
```
X-Tenant-ID: {tenant_id}  // Member用户必填，管理员用户禁止
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| username | string | 是 | 用户名或邮箱地址 | "member001" 或 "admin@example.com" | 有效的用户名或邮箱格式 |
| password | string | 是 | 登录密码 | "password123" | 最少1字符 |
| tenant_id | integer | 否 | 租户ID，仅Member用户使用 | 1 | 有效的租户ID，当X-Tenant-ID缺失时使用 |

### 业务规则
- ✅ Member用户：必须通过请求头`X-Tenant-ID`或请求体`tenant_id`指定租户
- ✅ 管理员用户：禁止携带`X-Tenant-ID`请求头
- ✅ 支持用户名或邮箱登录
- ✅ 用户和租户都必须处于激活状态
- ❌ 子账号不支持登录
- ❌ 账户被暂停的用户无法登录
- 成功（200）：返回 `token`、`refresh_token` 及用户摘要（含 `is_member` / `is_admin` / `is_super_admin` 等）。
- 失败（401 示例，凭据错误）：
{
  "success": false, "code": 4002, "message": "Invalid username/email or password", "data": null
}
- 失败（401 示例，Header 规则不符）：
{
  "success": false, "code": 4001, "message": "Invalid or missing X-Tenant-ID", "data": null,
  "error_code": "AUTH_NOT_AUTHENTICATED"
}
- 规则要点：子账号禁止登录；用户与其租户均需为 `active`。

## 3. 刷新访问令牌

### 接口信息
- **接口地址**: `POST /api/v1/auth/refresh/`
- **权限要求**: 无需认证，匿名访问
- **功能说明**: 使用refresh token刷新access token

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| refresh_token | string | 是 | 刷新令牌 | "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的JWT refresh token |

### 业务规则
- ✅ 支持Member和管理员用户
- ✅ refresh token必须有效且未过期
- ✅ 用户和租户必须处于激活状态
- ❌ 子账号不支持刷新token
- ❌ 无效或过期的refresh token会被拒绝
- 成功（200）：
{
  "success": true, "code": 2000, "message": "Token refreshed successfully",
  "data": {"token": "<new_access_token>", "refresh_token": "<new_refresh_token>"}
}
- 失败（401 示例）：
{
  "success": false, "code": 4001, "message": "Invalid refresh token", "data": null,
  "error_code": "AUTH_NOT_AUTHENTICATED"
}
- 规则要点：子账号不能刷新；令牌 `model_type` 与用户状态校验；租户需 `active`。

## 4. 验证访问令牌

### 接口信息
- **接口地址**: `GET /api/v1/auth/verify/`
- **权限要求**: 需要有效的access token
- **功能说明**: 验证access token有效性并返回用户信息

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 条件必填 | 租户ID，Member用户必填 | "1" | Member用户需要，管理员用户不需要 |

### 业务规则
- ✅ 支持Member和管理员用户
- ✅ access token必须有效且未过期
- ✅ Member用户必须提供X-Tenant-ID
- ✅ 返回用户详细信息用于前端状态同步
- ❌ 子账号不支持独立token验证（通过父账号token）
- 成功（200）：返回 `user` 摘要（区分 Member / 管理员），用于前端校验会话有效。

## 5. 请求密码重置

### 接口信息
- **接口地址**: `POST /api/v1/auth/password-reset/request/`
- **权限要求**: 无需认证，匿名访问
- **功能说明**: 请求密码重置邮件/短信，统一返回成功避免用户枚举

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| X-Tenant-ID | string | 条件必填 | 租户ID，Member用户必填 | "1" | Member用户需要，管理员用户禁止 |

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| username | string | 否 | 用户名或邮箱 | "member001" 或 "admin@example.com" | 有效的用户名或邮箱格式 |
| email | string | 否 | 邮箱地址 | "user@example.com" | 有效的邮箱格式 |
| phone | string | 否 | 手机号码 | "13800138000" | 有效的手机号码格式 |
| tenant_id | integer | 否 | 租户ID，当X-Tenant-ID缺失时使用 | 1 | 有效的租户ID |

### 业务规则
- ✅ 无论用户是否存在都返回成功，避免用户名枚举攻击
- ✅ Member用户必须指定租户（头或参数）
- ✅ 管理员用户禁止携带X-Tenant-ID
- ✅ 支持多种标识符查找用户（用户名/邮箱/手机号）
- ❌ 不验证用户存在性或激活状态
  - email(string, 必填)
  - account_type(enum[user, member], 可选)
  - tenant_id(integer, 可选，仅 member 消歧)
- 成功（200）：
{
  "success": true, "code": 2000, "message": "如果该邮箱存在，密码重置链接已发送",
  "data": {"detail": "如果该邮箱存在，密码重置链接已发送"}
}
- 频率限制（429）：同一 IP 10 分钟最多 3 次。

## 6. 验证密码重置令牌
- 路径：POST `/api/v1/auth/password-reset/verify/`
- 请求体：`token`(string, 必填)
- 成功（200）：返回 `{ detail, user_email }`。
- 失败（400）：token 无效/过期，返回标准验证错误格式。

## 7. 确认密码重置
- 路径：POST `/api/v1/auth/password-reset/confirm/`
- 请求体：
  - token(string, 必填)
  - new_password(string, 必填)
  - confirm_password(string, 必填)
- 成功（200）：`message`: "密码重置成功"；失败（400）：`VALIDATION_ERROR`。

## 客户端集成要点（平台无关）
- 统一处理响应：先判断 `success`，再按 `code`/`message` 分流；从 `data` 提取业务数据。
- 认证与会话：`token` 通过 `Authorization` 头传递；注意刷新与失效处理。
- 多租户：Member 调用必须附带 `X-Tenant-ID`；管理员禁止携带。
- 分页：读取 `data.pagination` 与 `data.results`；不要直接依赖 HTTP Link。
- 幂等与错误：删除/取消类接口幂等；校验错误用 `4000` + `data` 字段级错误；遵循错误码规范。

## 示例返回（统一响应）

### 成员自助注册 201
{
  "success": true,
  "code": 2000,
  "message": "注册成功",
  "data": {
    "token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "user": {
      "id": 10,
      "username": "member001",
      "email": "member001@example.com",
      "nick_name": "测试成员",
      "avatar": "",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
      "tenant_id": 1,
      "tenant_name": "测试租户"
    }
  }
}

### 成员登录 200
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "user": {
      "id": 10,
      "username": "member001",
      "email": "member001@example.com",
      "nick_name": "测试成员",
      "avatar": "",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
      "tenant_id": 1,
      "tenant_name": "测试租户"
    }
  }
}

### 管理员登录 200
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "nick_name": "管理员",
      "avatar": "",
      "is_admin": true,
      "is_super_admin": true,
      "is_member": false
    }
  }
}

### 刷新访问令牌 200
{
  "success": true,
  "code": 2000,
  "message": "Token refreshed successfully",
  "data": {
    "token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi..."
  }
}

### 验证令牌 200
{
  "success": true,
  "code": 2000,
  "message": "令牌有效",
  "data": {
    "user": {
      "id": 10,
      "username": "member001",
      "email": "member001@example.com",
      "nick_name": "测试成员",
      "avatar": "",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
      "tenant_id": 1,
      "tenant_name": "测试租户"
    }
  }
}

### 请求密码重置 200（匿名化成功返回）
{
  "success": true,
  "code": 2000,
  "message": "如果该邮箱存在，密码重置链接已发送",
  "data": {"detail": "如果该邮箱存在，密码重置链接已发送"}
}

### 验证密码重置令牌 200
{
  "success": true,
  "code": 2000,
  "message": "重置令牌有效",
  "data": {"detail": "重置令牌有效", "user_email": "member001@example.com"}
}

### 确认密码重置 200
{
  "success": true,
  "code": 2000,
  "message": "密码重置成功",
  "data": {"detail": "密码重置成功，请使用新密码登录"}
}

### 典型错误示例
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {"username": ["Username already used in this tenant"]},
  "error_code": "VALIDATION_ERROR"
}
{
  "success": false,
  "code": 4001,
  "message": "Invalid or missing X-Tenant-ID",
  "data": null,
  "error_code": "AUTH_NOT_AUTHENTICATED"
}
