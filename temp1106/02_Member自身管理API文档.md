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
- 路径：GET `/api/v1/members/me/`
- 说明：仅 Member 可用；管理员访问返回权限不足。
- 成功（200）：data 为 Member 详情对象（含 `tenant_name`、`is_sub_account`、`parent_username` 等）。
- 失败（403）：非 Member 访问。

## 2. 更新当前 Member 信息
- 路径：PUT/PATCH `/api/v1/members/me/`
- 不可修改字段：`username`、`email`
- 允许字段（示例）：`phone`、`nick_name`、`first_name`、`last_name`、`avatar`、`wechat_id`
- 成功（200）：返回更新后的 Member 详情。
- 失败（400）：校验错误统一按 `4000/VALIDATION_ERROR` 返回字段级错误。
- 失败（403）：非 Member 访问。

## 3. 更新当前 Member 密码
- 路径：POST `/api/v1/members/me/password/`
- 请求体：
  - old_password(string, 必填)
  - new_password(string, 必填)
  - new_password_confirm(string, 必填)
- 成功（200）：`message` = "密码更新成功"。
- 失败（400 示例）：
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "old_password": ["Incorrect old password"]
  },
  "error_code": "VALIDATION_ERROR"
}
- 失败（403）：非 Member 访问。

## 4. 上传当前 Member 头像
- 路径：POST `/api/v1/members/avatar/upload/`
- Header：`Content-Type: multipart/form-data`
- 表单字段：avatar(file, 必填；JPG/PNG/GIF/WEBP/BMP；<= 2MB)
- 成功（200）：
{
  "success": true, "code": 2000, "message": "头像上传成功",
  "data": {"avatar": "/media/avatars/uuid.jpg"}
}
- 失败（400）：未提供文件/类型不支持/超限。
- 失败（403）：子账号不允许变更头像；或非 Member 访问。
- 失败（500）：存储失败。

## 5. 为特定 Member 上传头像
- 路径：POST `/api/v1/members/<id>/avatar/upload/`
- 权限/行为：
  - Member：仅可为自己的子账号上传。
  - 租户管理员：仅可为本租户 Member 上传。
  - 超级管理员：可为任意 Member 上传。
- 其余规则同“上传当前 Member 头像”。

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
