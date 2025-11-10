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

### 接口信息
- **接口地址**: `GET /api/v1/admin/members/`
- **权限要求**: 需要管理员认证（租户管理员或超级管理员）
- **功能说明**: 获取Member用户列表，支持多种筛选条件

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| search | string | 否 | 按用户名/邮箱/昵称/手机号模糊匹配 | "member001" | 最长100字符 |
| status | string | 否 | 按状态筛选 | "active" | active/suspended/inactive |
| is_sub_account | boolean | 否 | 是否为子账号 | true | true/false |
| parent | integer | 否 | 父账号ID | 5 | 有效的Member ID |
| tenant_id | integer | 否 | 租户ID（仅超级管理员） | 1 | 有效的租户ID |
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |

### 权限说明
- **租户管理员**: 只能查看本租户的Member
- **超级管理员**: 可查看所有租户的Member，并可指定tenant_id筛选

### 业务规则
- ✅ 支持多字段模糊搜索
- ✅ 支持精确状态筛选
- ✅ 支持子账号和父子关系筛选
- ✅ 租户管理员自动限定在本租户范围内

## 2. 创建 Member

### 接口信息
- **接口地址**: `POST /api/v1/admin/members/`
- **权限要求**: 需要管理员认证（租户管理员或超级管理员）
- **功能说明**: 创建新的Member用户账号

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| Content-Type | string | 是 | 请求体类型 | "application/json" | 必须为application/json |

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| username | string | 是 | 用户名，租户内唯一 | "member001" | 3-30字符，只能包含字母、数字、下划线 |
| email | string | 是 | 邮箱地址，租户内唯一 | "member001@example.com" | 有效的邮箱格式 |
| password | string | 是 | 登录密码 | "password123" | 最少8字符，包含大小写字母和数字 |
| password_confirm | string | 是 | 密码确认 | "password123" | 必须与password相同 |
| phone | string | 否 | 手机号码，租户内唯一 | "13800138000" | 有效的手机号码格式 |
| nick_name | string | 否 | 昵称 | "测试成员" | 最长50字符 |
| wechat_id | string | 否 | 微信ID | "wechat123" | 最长100字符 |
| tenant_id | integer | 否 | 租户ID（仅超级管理员可指定） | 1 | 有效的租户ID |

### 权限说明
- **租户管理员**: 创建的Member自动绑定到自己的租户，不能指定其他租户
- **超级管理员**: 可指定任意租户ID创建Member

### 业务规则
- ✅ 用户名和邮箱在指定租户内唯一
- ✅ 手机号码在租户内唯一（如果提供）
- ✅ 密码强度自动校验
- ✅ 租户管理员自动绑定到所属租户
- ❌ 租户管理员不能跨租户创建用户

## 3. 获取 Member 详情

### 接口信息
- **接口地址**: `GET /api/v1/admin/members/{id}/`
- **权限要求**: 需要管理员认证（租户管理员或超级管理员）
- **功能说明**: 获取指定Member的详细信息

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | Member ID | 10 | 有效的Member ID |

### 权限说明
- **租户管理员**: 只能查看本租户的Member
- **超级管理员**: 可查看任意租户的Member

## 4. 更新 Member 信息

### 接口信息
- **接口地址**: `PUT/PATCH /api/v1/admin/members/{id}/`
- **权限要求**: 需要管理员认证（租户管理员或超级管理员）
- **功能说明**: 更新指定Member的信息

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| Content-Type | string | 是 | 请求体类型 | "application/json" | 必须为application/json |

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| id | integer | 是 | Member ID | 10 | 有效的Member ID |

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| phone | string | 否 | 手机号码 | "13800138001" | 有效的手机号码格式 |
| nick_name | string | 否 | 昵称 | "新昵称" | 最长50字符 |
| first_name | string | 否 | 名 | "新" | 最长30字符 |
| last_name | string | 否 | 姓 | "名" | 最长30字符 |
| avatar | string | 否 | 头像路径 | "/media/avatars/new.jpg" | 有效的文件路径 |
| status | string | 否 | 账号状态 | "active" | active/suspended/inactive |
| is_active | boolean | 否 | 是否激活 | true | true/false |
| wechat_id | string | 否 | 微信ID | "new_wechat" | 最长100字符 |

### 不可修改字段
- `username` - 用户名
- `email` - 邮箱地址
- `tenant` - 租户ID

### 权限说明
- **租户管理员**: 只能更新本租户的Member
- **超级管理员**: 可更新任意租户的Member

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
