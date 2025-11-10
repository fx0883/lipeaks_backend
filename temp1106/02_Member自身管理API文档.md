# Member 自身管理 API（统一响应版）

## 适用范围
- 面向 iOS / Android / 鸿蒙 / Web / 小程序等所有客户端。
- 仅提供平台无关的字段与示例，不包含语言/框架代码。

## 统一返回结构
- 参见 `docs/api_response/01_response_format_standard.md`。
- 响应：success, code, message, data[, error_code]；分页：data.pagination + data.results。

## 基础信息
- 前缀：`/api/v1/members/`
- Header：
  - Authorization: Bearer <access_token>（必须）
  - X-Tenant-ID: <租户ID>（Member 必须）

## 1. 获取当前 Member 信息

### 接口信息
- **接口地址**: `GET /api/v1/members/me/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 获取当前登录Member的详细信息

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |

### 业务规则
- ✅ 仅Member用户可访问
- ✅ 返回完整的用户信息包括租户、父账号等关联信息
- ✅ 子账号会显示父账号信息
- ❌ 管理员用户访问返回403权限不足

## 2. 更新当前 Member 信息

### 接口信息
- **接口地址**: `PUT/PATCH /api/v1/members/me/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 更新当前登录Member的个人信息

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |
| Content-Type | string | 是 | 请求体类型 | "application/json" | 必须为application/json |

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| phone | string | 否 | 手机号码 | "13800138000" | 有效的手机号码格式，租户内唯一 |
| nick_name | string | 否 | 昵称 | "新昵称" | 最长50字符 |
| first_name | string | 否 | 名 | "张" | 最长30字符 |
| last_name | string | 否 | 姓 | "三" | 最长30字符 |
| avatar | string | 否 | 头像相对路径 | "/media/avatars/uuid.jpg" | 有效的文件路径 |
| wechat_id | string | 否 | 微信ID | "new_wechat_id" | 最长100字符 |

### 业务规则
- ✅ 仅可更新允许的字段
- ✅ username和email字段不可修改
- ✅ PATCH支持部分更新，PUT需要提供所有字段
- ✅ 手机号码在租户内唯一性校验
- ✅ 仅Member用户可访问
- ❌ 子账号不可修改某些敏感信息

## 3. 更新当前 Member 密码

### 接口信息
- **接口地址**: `POST /api/v1/members/me/password/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 更新当前登录Member的登录密码

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |
| Content-Type | string | 是 | 请求体类型 | "application/json" | 必须为application/json |

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| old_password | string | 是 | 当前密码 | "oldpassword123" | 最少1字符，用于验证身份 |
| new_password | string | 是 | 新密码 | "newpassword123" | 最少8字符，包含大小写字母和数字 |
| new_password_confirm | string | 是 | 新密码确认 | "newpassword123" | 必须与new_password完全相同 |

### 业务规则
- ✅ 必须提供正确的当前密码进行身份验证
- ✅ 新密码必须符合密码强度要求
- ✅ 确认密码必须与新密码一致
- ✅ 密码更新后会使所有现有token失效（需要重新登录）
- ✅ 仅Member用户可访问
- ❌ 子账号不支持独立密码修改

## 4. 上传当前 Member 头像

### 接口信息
- **接口地址**: `POST /api/v1/members/avatar/upload/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 上传并更新当前登录Member的头像

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |
| Content-Type | string | 是 | 请求体类型 | "multipart/form-data" | 必须为multipart/form-data |

### 请求参数（表单数据）

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| avatar | file | 是 | 头像图片文件 | user-avatar.jpg | JPG/PNG/GIF/WEBP/BMP格式，最大2MB |

### 文件格式要求
- **支持格式**: JPG, PNG, GIF, WEBP, BMP
- **最大文件大小**: 2MB
- **推荐尺寸**: 200x200像素以上，正方形最佳

### 业务规则
- ✅ 自动处理图片格式转换和压缩
- ✅ 生成唯一的文件名避免冲突
- ✅ 返回相对路径，前端需要拼接域名
- ✅ 旧头像文件会被自动清理
- ✅ 仅Member用户可访问
- ❌ 子账号不允许变更头像

## 5. 为特定 Member 上传头像

### 接口信息
- **接口地址**: `POST /api/v1/members/{id}/avatar/upload/`
- **权限要求**: 需要管理员或父账号认证
- **功能说明**: 为指定的Member上传头像（管理员或父账号权限）

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 条件必填 | 租户ID，Member用户必填 | "1" | Member用户需要，管理员可选 |
| Content-Type | string | 是 | 请求体类型 | "multipart/form-data" | 必须为multipart/form-data |

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| id | integer | 是 | Member ID | 123 | 有效的Member ID |

### 请求参数（表单数据）

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| avatar | file | 是 | 头像图片文件 | member-avatar.jpg | JPG/PNG/GIF/WEBP/BMP格式，最大2MB |

### 权限说明
- **Member用户**: 仅可为自己的子账号上传头像
- **租户管理员**: 可为本租户任意Member上传头像
- **超级管理员**: 可为任意Member上传头像

### 业务规则
- ✅ 文件格式和大小限制同个人上传接口
- ✅ 权限严格校验，只能为有权限的Member上传
- ✅ 自动清理旧头像文件
- ✅ 支持跨租户操作（超级管理员）
- ❌ 普通Member不能为其他非子账号Member上传

## 响应字段摘录（示例）
- Member 详情对象常见字段：
  - id, username, email, phone, nick_name, first_name, last_name
  - is_active, avatar, tenant(id), tenant_name
  - is_sub_account(bool), parent(id), parent_username
  - date_joined(ISO 8601), status(active/suspended/inactive), wechat_id

## 客户端集成要点（平台无关）
- 认证：所有接口均需携带 Bearer Token 与 `X-Tenant-ID`。
- 图片：服务端返回相对路径 `data.avatar`，客户端需拼接域名形成完整 URL。
- 错误处理：字段级错误在 `data` 中按字段名聚合数组；统一先判断 `success`。
- 子账号限制：子账号无登录；也不可进行头像变更等受限操作。

## 示例返回（统一响应）

### 获取当前 Member 信息 200
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 10,
    "username": "member001",
    "email": "member001@example.com",
    "phone": "13800138000",
    "nick_name": "测试成员",
    "first_name": "",
    "last_name": "",
    "is_active": true,
    "avatar": "/media/avatars/uuid.jpg",
    "tenant": 1,
    "tenant_name": "测试租户",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2024-01-20T10:30:00Z",
    "status": "active",
    "wechat_id": "wx_member001"
  }
}

### 更新当前 Member 信息 200
{
  "success": true,
  "code": 2000,
  "message": "更新成功",
  "data": {
    "id": 10,
    "username": "member001",
    "email": "member001@example.com",
    "phone": "13900139000",
    "nick_name": "新昵称",
    "first_name": "张",
    "last_name": "三",
    "is_active": true,
    "avatar": "/media/avatars/uuid.jpg",
    "tenant": 1,
    "tenant_name": "测试租户",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2024-01-20T10:30:00Z",
    "status": "active",
    "wechat_id": "wx_newid"
  }
}

### 更新密码 200
{
  "success": true,
  "code": 2000,
  "message": "密码更新成功",
  "data": null
}

### 上传头像 200
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {"avatar": "/media/avatars/uuid.jpg"}
}

### 典型错误示例（字段校验） 400
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {"old_password": ["Incorrect old password"]},
  "error_code": "VALIDATION_ERROR"
}
