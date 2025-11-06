# 管理员端 Member 管理 API（统一响应版）

## 适用范围
- 面向 iOS / Android / 鸿蒙 / Web / 小程序等所有客户端的管理端集成。
- 仅提供平台无关的字段与示例，不包含语言/框架代码。

## 统一返回结构
- 参见 `docs/api_response/01_response_format_standard.md`。
- 响应：success, code, message, data[, error_code]；分页：data.pagination + data.results。

## 基础信息
- 前缀：`/api/v1/admin/members/`
- Header：Authorization: Bearer <access_token>
- 管理员规则：
  - 超级管理员：跨租户读写；可使用 `tenant_id` 过滤或创建指定租户数据。
  - 租户管理员：仅可读写本租户数据；禁止跨租户操作；创建时不可指定其他租户。
  - 管理员接口禁止携带 `X-Tenant-ID`。

## 1. 获取 Member 列表（分页）
- 路径：GET `/api/v1/admin/members/`
- 查询参数（可选）：
  - search(string)：按用户名/邮箱/昵称/手机号模糊匹配
  - status(enum)：`active`/`suspended`/`inactive`
  - is_sub_account(bool)
  - parent(int)
  - tenant_id(int，仅超级管理员可用)
  - page(int), page_size(int)
- 成功（200，分页）：
{
  "success": true, "code": 2000, "message": "查询成功",
  "data": {"pagination": {...}, "results": [{"id": 10, "username": "member001", ...}]}
}

## 2. 创建 Member
- 路径：POST `/api/v1/admin/members/`
- 请求体：
  - username(string, 必填；租户内唯一)
  - email(string, 必填；租户内唯一)
  - password(string, 必填)
  - password_confirm(string, 必填)
  - phone(string, 可选；租户内唯一)
  - nick_name(string, 可选)
  - wechat_id(string, 可选)
  - tenant_id(int, 可选；仅超级管理员可指定)
- 成功（201）：返回 Member 详情。
- 失败（400）：`VALIDATION_ERROR`（唯一性/强度/租户ID合法性等）。
- 权限：租户管理员创建时隐式绑定其所属租户且不得越权。

## 3. 获取 Member 详情
- 路径：GET `/api/v1/admin/members/<id>/`
- 成功（200）：返回 Member 详情；失败（404/403）：按统一错误规范。

## 4. 更新 Member 信息
- 路径：PUT/PATCH `/api/v1/admin/members/<id>/`
- 不建议修改字段：`username`、`email`、`tenant`
- 可更新字段（示例）：`phone`、`nick_name`、`first_name`、`last_name`、`avatar`、`status`、`is_active`、`wechat_id`
- 成功（200）：返回更新后的 Member；失败（400）：`VALIDATION_ERROR`。

## 5. 删除 Member（软删除）
- 路径：DELETE `/api/v1/admin/members/<id>/`
- 成功（204）：`data=null`；失败（404/403）：按统一错误规范。

## 6. 子账号（管理员端）
- 列表：GET `/api/v1/admin/members/sub-accounts/`（分页）
- 详情：GET `/api/v1/admin/members/sub-accounts/<id>/`
- 更新：PUT/PATCH `/api/v1/admin/members/sub-accounts/<id>/`
- 删除（软）：DELETE `/api/v1/admin/members/sub-accounts/<id>/`
- 权限：租户管理员仅可操作本租户；超级管理员可操作任意租户。

## 7. 为 Member 上传头像（管理员端）
- 路径：POST `/api/v1/admin/members/<id>/avatar/upload/`
- Header：`Content-Type: multipart/form-data`
- 表单：avatar(file, 必填；JPG/PNG/GIF/WEBP/BMP；<= 2MB)
- 成功（200）：返回新头像相对路径；失败（400/403/404/500）按统一规范。

## 分页与过滤
- 列表接口均返回 `data.pagination + data.results`；
- 超级管理员可使用 `tenant_id` 实现跨租户过滤；
- 租户管理员忽略跨租户筛选，始终限定在自身租户。

## 错误与权限
- 未认证：`4001/AUTH_NOT_AUTHENTICATED`；
- 权限不足：`4003/AUTH_PERMISSION_DENIED`；
- 资源不存在：`4004/NOT_FOUND`；
- 校验错误：`4000/VALIDATION_ERROR`；
- 服务器错误：`5000/INTERNAL_SERVER_ERROR`。

## 客户端集成要点（平台无关）
- 管理端请求禁止携带 `X-Tenant-ID`，以免触发成员头校验冲突；
- 统一按 `success/code/message/data/error_code` 解析；
- 创建/更新前做基础校验与去重提示；
- 删除为软删除，列表需忽略已删除用户；
- 头像上传返回相对路径，前端需拼接域名展示。

## 示例返回（统一响应）

### 获取 Member 列表 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {"count": 1, "next": null, "previous": null, "page_size": 20, "current_page": 1, "total_pages": 1},
    "results": [
      {
        "id": 11,
        "username": "member001",
        "email": "member001@example.com",
        "phone": "13800138000",
        "nick_name": "普通成员1",
        "is_active": true,
        "avatar": "",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": false,
        "date_joined": "2024-01-20T10:30:00Z",
        "status": "active",
        "wechat_id": "wx_member001"
      }
    ]
  }
}

### 创建 Member 201
{
  "success": true,
  "code": 2000,
  "message": "创建成功",
  "data": {
    "id": 12,
    "username": "newmember",
    "email": "newmember@example.com",
    "phone": "",
    "nick_name": "新成员",
    "is_active": true,
    "avatar": "",
    "tenant": 1,
    "tenant_name": "测试租户",
    "is_sub_account": false,
    "date_joined": "2024-01-22T10:00:00Z",
    "status": "active"
  }
}

### 获取 Member 详情 200
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {"id": 11, "username": "member001", "email": "member001@example.com", "tenant": 1, "tenant_name": "测试租户", "is_sub_account": false}
}

### 更新 Member 200
{
  "success": true,
  "code": 2000,
  "message": "更新成功",
  "data": {"id": 11, "username": "member001", "nick_name": "更新后的昵称", "status": "active"}
}

### 删除 Member 204
{
  "success": true,
  "code": 2000,
  "message": "删除成功",
  "data": null
}

### 子账号列表（管理员端） 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {"count": 1, "next": null, "previous": null, "page_size": 20, "current_page": 1, "total_pages": 1},
    "results": [
      {"id": 20, "username": "subaccount1", "email": "sub1@example.com", "parent": 11, "tenant": 1, "is_sub_account": true}
    ]
  }
}

### 为 Member 上传头像 200
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {"avatar": "/media/avatars/uuid.jpg"}
}

### 典型错误示例 403
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": {"detail": "Only administrators can access"},
  "error_code": "AUTH_PERMISSION_DENIED"
}
