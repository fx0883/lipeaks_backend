# Member API Integration Guide

- Base URL: `/api/v1/`
- Auth routes prefix: `/api/v1/auth/`
- Member routes prefix: `/api/v1/members/`
- Auth: JWT required for protected member endpoints. Header: `Authorization: Bearer <token>`
- Tenant header rules:
  - 只要带了 `X-Tenant-ID` 的调用，一律视为“member 或匿名”上下文。
  - 成员用户调用任何 API 必须携带该头，且与其租户一致；缺失 4001（"缺少或非法的租户ID"），不一致 4003（"租户不匹配，或者没有权限"）。
  - 管理员/超级管理员不允许携带该头；若携带，返回 4001（"缺少或非法的租户ID"）。

## Conventions
- Success envelope: `{ success: boolean, code: number, message: string, data: any }`
- Errors: standard DRF errors with status codes

---

## 1) Auth: Login

Path: `POST /api/v1/auth/login/`
- Permissions: Public
- Body (LoginSerializer):
  - `username` or `email` (one of them)
  - `password` (required)
  - `tenant_id` (成员登录禁用；仅 header 生效)
- Response: 200
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "登录成功",
    "data": {
      "token": "<jwt>",
      "refresh_token": "<jwt>",
      "user": {
        "id": 1,
        "username": "alice",
        "email": "alice@example.com",
        "nick_name": "",
        "avatar": "",
        "is_admin": false,
        "is_super_admin": false,
        "is_member": true,
        "is_sub_account": false,
        "tenant_id": 10,
        "tenant_name": "Acme"
      }
    }
  }
  ```

错误示例：
- 成员登录缺少头：400 / code=4001
- 管理员登录携带头：400 / code=4001

---

## 2) Auth: Register (User)

Path: `POST /api/v1/auth/register/`
- Permissions: Public
- Body (RegisterSerializer):
  - `username` (required)
  - `email` (required)
  - `password` (required)
  - `password_confirm` (required; match)
  - `tenant_id` (optional)
- Response: 201 同登录返回结构（包含 token、refresh_token、user）

---

## 3) Auth: Member Self Register

Path: `POST /api/v1/auth/member/register/`
- Permissions: Public
- Body (MemberSelfRegisterSerializer):
  - `username` (required)
  - `email` (required)
  - `password` (required)
  - `password_confirm` (required; match)
  - `tenant_id`（禁用；仅从请求头 `X-Tenant-ID` 获取）
错误示例：
- 无头：400 / code=4001
- Body 带 `tenant_id`：400 / code=4001
- Response: 201 同登录返回结构（成员 user 字段 `is_member: true`）

---

## 4) Auth: Password Reset - Request

Path: `POST /api/v1/auth/password-reset/request/`
- Permissions: Public
- Body (PasswordResetRequestSerializer):
  - `email` (required)
  - `account_type` (optional: `user` | `member`)
  - `tenant_id`（禁用；成员仅 header 消歧）
规则：
- 当 account_type=member 或系统识别目标主体为 member：必须携带 `X-Tenant-ID`；
- 当 account_type=user：禁止携带 `X-Tenant-ID`。
- Behavior: 频控（同一IP 10分钟最多3次）；无论邮箱是否存在均返回通用成功，避免用户枚举
- Response: 200 `{ success: true, message: "如果邮箱存在，将发送重置邮件" }`

---

## 5) Auth: Password Reset - Verify Token

Path: `POST /api/v1/auth/password-reset/verify/`
- Permissions: Public
- Body (PasswordResetVerifySerializer):
  - `token` (required)
规则：
- 若 token 属于 member：必须携带 `X-Tenant-ID` 且与 token.member.tenant 一致，否则 4001/4003
- 若 token 属于 user：禁止携带 `X-Tenant-ID`
- Response: 200 `{ success: true, message: "令牌有效" }`，无效则 400 `{ message: "无效的重置令牌" }`

---

## 6) Auth: Password Reset - Confirm

Path: `POST /api/v1/auth/password-reset/confirm/`
- Permissions: Public
- Body (PasswordResetConfirmSerializer):
  - `token` (required)
  - `new_password` (required)
  - `new_password_confirm` (required; match; 强度校验)
规则同 verify。
- Response: 200 `{ success: true, message: "密码重置成功" }`

---

## 6.1) CMS APIs — 访问规则与示例

- 主体规则：
  - 成员/匿名：必须携带 `X-Tenant-ID`；缺失/非法 → 400, code=4001（"缺少或非法的租户ID"）；成员错租户 → 403, code=4003（"租户不匹配，或者没有权限"）。
  - 管理员：禁止携带 `X-Tenant-ID`；无任何租户参数时默认使用绑定租户；若提供 `?tenant_id=` 则按参数指定。
  - 超级管理员：禁止携带 `X-Tenant-ID`；允许 `?tenant_id=` 指定租户；未指定则返回全量数据（沿用现有逻辑）。
  - 成员请求里若出现 query/body 的 `tenant_id`：忽略并记录 Warning 日志，仅以请求头为准。
  - 建议在成员/匿名路径的响应设置：`Vary: X-Tenant-ID`。

- 错误示例：
  - 匿名/成员访问 CMS 无头：400 / code=4001，message="缺少或非法的租户ID"
  - 成员访问 CMS 头与自身租户不一致：403 / code=4003，message="租户不匹配，或者没有权限"
  - 管理员/超管访问 CMS 携带头：400 / code=4001，message="缺少或非法的租户ID"

---

## 7) Current member: Me

Path: `/api/v1/members/me/` 
- GET current profile
  - Permissions: logged-in Member only (not admin)
  - 需携带 `X-Tenant-ID`，与当前成员租户一致；缺失 4001，不一致 4003
  - Response: 200 success envelope with MemberSerializer data
- PUT update current profile
  - Permissions: logged-in Member only
  - Body: partial MemberSerializer; username/email cannot be changed here
  - Response: 200 success envelope with updated MemberSerializer

## 8) Current member: Change password

Path: `POST /api/v1/members/me/password/`
- Permissions: logged-in Member only
- Body (UserPasswordUpdateSerializer):
  - `old_password` (required)
  - `new_password` (required)
  - `new_password_confirm` (required; must match)
- Response: 200 `{ success: true, message: "密码更新成功" }`

## 9) Sub-accounts: List & Create

Path: `/api/v1/members/sub-accounts/`
- GET list sub-accounts (Member: only own children; Admin roles as per permissions)
- POST create sub-account (Member creates under self)
- Response: 200 (GET paginated) / 201 (POST created)

## 10) Avatar upload (current member)

Path: `POST /api/v1/members/avatar/upload/`
- Permissions: logged-in Member; sub-accounts not allowed
 - 需携带 `X-Tenant-ID`
- Form: multipart `avatar` (JPG/PNG/GIF/WEBP/BMP)
- Response: 200 `{ detail: "头像上传成功", avatar: "/media/avatars/<file>" }`

---

## Serializers (field reference)
- UserPasswordUpdateSerializer: `old_password`, `new_password`, `new_password_confirm`
- SubAccountCreateSerializer: `username`, `email`, `phone?`, `nick_name?`, `first_name?`, `last_name?`, `avatar?`
- MemberSerializer: `id`, `username`, `email`, `phone`, `nick_name`, `first_name`, `last_name`, `is_active`, `avatar`, `tenant`, `tenant_name`, `is_sub_account`, `parent`, `parent_username`, `date_joined`, `status`, `wechat_id` (ro: `id`, `date_joined`, `tenant_name`, `is_sub_account`, `parent_username`)

---

## Notes & best practices
- Always send JWT in `Authorization` header for protected endpoints.
- File uploads return relative URLs under `MEDIA_URL`.
- Password strength is enforced by Django validators.
- API docs (OpenAPI): `/api/v1/docs/` and schema at `/api/v1/schema/`.
