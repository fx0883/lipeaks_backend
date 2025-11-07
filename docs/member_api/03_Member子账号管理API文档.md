# Member 子账号管理 API（统一响应版）

## 适用范围
- 面向 iOS / Android / 鸿蒙 / Web / 小程序等所有客户端。
- 仅提供平台无关的字段与示例，不包含语言/框架代码。

## 统一返回结构
- 参见 `docs/api_response/01_response_format_standard.md`。
- 响应：success, code, message, data[, error_code]；分页：data.pagination + data.results。

## 基础信息
- 前缀：`/api/v1/members/sub-accounts/`
- Header：
  - Authorization: Bearer <access_token>（必须）
  - X-Tenant-ID: <租户ID>（Member 必须）

## 1. 获取子账号列表
- 路径：GET `/api/v1/members/sub-accounts/`
- 权限：已认证用户；
  - Member：仅返回自己作为父账号的子账号；
  - 子账号：无权限查看（返回空）；
  - 租户管理员：可查看本租户全部子账号；
  - 超级管理员：可查看全部子账号。
- 成功（200，分页）：
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {"count": 5, "next": null, "previous": null, "page_size": 20, "current_page": 1, "total_pages": 1},
    "results": [
      {"id": 20, "username": "sub1", "email": "sub1@example.com", "parent": 10, "tenant": 1, "is_sub_account": true}
    ]
  }
}

## 2. 创建子账号
- 路径：POST `/api/v1/members/sub-accounts/`
- 说明：子账号默认不能登录（`is_active=false`），自动继承父账号租户；无需密码。
- 请求体：
  - username(string, 必填，全局唯一)
  - email(string, 必填，全局唯一)
  - phone(string, 可选)
  - nick_name(string, 可选)
  - first_name(string, 可选)
  - last_name(string, 可选)
  - avatar(string, 可选，相对路径)
  - wechat_id(string, 可选)
- 成功（201）：返回新子账号详情。
- 失败（400）：`VALIDATION_ERROR`（如用户名/邮箱重复）。

## 3. 获取子账号详情
- 路径：GET `/api/v1/members/sub-accounts/<id>/`
- 权限：
  - Member：仅可查看自己的子账号；
  - 租户管理员：查看本租户子账号；
  - 超级管理员：可查看任意子账号。
- 成功（200）：返回子账号详情。

## 4. 更新子账号信息
- 路径：PUT/PATCH `/api/v1/members/sub-accounts/<id>/`
- 不可修改字段：`username`、`email`、`parent`、`tenant`
- 允许字段：`phone`、`nick_name`、`first_name`、`last_name`、`avatar`、`wechat_id`
- 成功（200）：返回更新后的子账号详情；失败（400）：`VALIDATION_ERROR`。

## 5. 删除子账号（软删除）
- 路径：DELETE `/api/v1/members/sub-accounts/<id>/`
- 成功（204）：`data=null`；失败（404/403）：按统一错误规范返回。

## 规则与限制
- 子账号：
  - 不能登录（`is_active=false`），无需/不可设置登录密码；
  - 自动继承父账号租户；
  - 主要用作数据归属与权限隔离。
- 唯一性要求：子账号 `username/email` 在全局范围内唯一（与所有 User/Member 不得重复）。
- 分页：列表统一以 `data.pagination + data.results` 返回。

## 响应字段摘录（示例）
- 子账号对象常见字段：
  - id, username, email, phone, nick_name, first_name, last_name, avatar, wechat_id
  - parent(id), parent_username
  - tenant(id), tenant_name
  - is_sub_account(true), date_joined

## 客户端集成要点（平台无关）
- 认证：携带 Bearer Token 与 `X-Tenant-ID`。
- 错误处理：按统一格式解析 `success/code/message/data/error_code`。
- 图片：`avatar` 返回相对路径；客户端拼接域名获取完整 URL。
- 幂等：删除等操作视为幂等；多次调用不应导致异常界面状态。

## 示例返回（统一响应）

### 获取子账号列表 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {
      "count": 2,
      "next": null,
      "previous": null,
      "page_size": 20,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 20,
        "username": "subaccount1",
        "email": "sub1@example.com",
        "phone": "13900001111",
        "nick_name": "子账号1",
        "parent": 10,
        "parent_username": "member001",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": true,
        "date_joined": "2024-01-21T10:00:00Z"
      },
      {
        "id": 21,
        "username": "subaccount2",
        "email": "sub2@example.com",
        "phone": "13900002222",
        "nick_name": "子账号2",
        "parent": 10,
        "parent_username": "member001",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": true,
        "date_joined": "2024-01-21T11:00:00Z"
      }
    ]
  }
}

### 创建子账号 201
{
  "success": true,
  "code": 2000,
  "message": "创建成功",
  "data": {
    "id": 22,
    "username": "subaccount3",
    "email": "sub3@example.com",
    "phone": "13900003333",
    "nick_name": "子账号3",
    "parent": 10,
    "parent_username": "member001",
    "tenant": 1,
    "tenant_name": "测试租户",
    "is_sub_account": true,
    "date_joined": "2024-01-21T12:00:00Z"
  }
}

### 获取子账号详情 200
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 22,
    "username": "subaccount3",
    "email": "sub3@example.com",
    "phone": "13900003333",
    "nick_name": "子账号3",
    "parent": 10,
    "parent_username": "member001",
    "tenant": 1,
    "tenant_name": "测试租户",
    "is_sub_account": true,
    "date_joined": "2024-01-21T12:00:00Z",
    "wechat_id": ""
  }
}

### 更新子账号信息 200
{
  "success": true,
  "code": 2000,
  "message": "更新成功",
  "data": {
    "id": 22,
    "username": "subaccount3",
    "email": "sub3@example.com",
    "phone": "13900004444",
    "nick_name": "更新后的子账号3",
    "parent": 10,
    "tenant": 1,
    "is_sub_account": true
  }
}

### 删除子账号（软删除） 204
{
  "success": true,
  "code": 2000,
  "message": "删除成功",
  "data": null
}

### 典型错误示例 400
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {"username": ["Username already in use"]},
  "error_code": "VALIDATION_ERROR"
}
