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
- 路径：POST `/api/v1/auth/member/register/`
- 说明：Member 在指定租户下自助注册。租户来源优先级：请求头 `X-Tenant-ID`（必需）。
- 请求体：
  - username(string, 必填)
  - email(string, 必填)
  - password(string, 必填)
  - password_confirm(string, 必填)
  - phone(string, 可选)
  - nick_name(string, 可选)
  - wechat_id(string, 可选)
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
- 路径：POST `/api/v1/auth/login/`
- 说明：
  - Member：必须提供租户（请求头 `X-Tenant-ID` 或 body.tenant_id）。
  - 管理员(User)：禁止携带 `X-Tenant-ID`。
- 请求体：
  - username(string, 必填)  // 用户名或邮箱
  - password(string, 必填)
  - tenant_id(integer, 可选，仅 Member 消歧)
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
- 路径：POST `/api/v1/auth/refresh/`
- 请求体：`refresh_token`(string, 必填)
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
- 路径：GET `/api/v1/auth/verify/`
- Header：Authorization 必填
- 成功（200）：返回 `user` 摘要（区分 Member / 管理员），用于前端校验会话有效。

## 5. 请求密码重置
- 路径：POST `/api/v1/auth/password-reset/request/`
- 说明：匿名接口，统一返回匿名成功提示，避免用户枚举。
- Header：
  - Member：必须携带 `X-Tenant-ID`（或 body.tenant_id）；
  - 管理员：禁止携带 `X-Tenant-ID`。
- 请求体：
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
