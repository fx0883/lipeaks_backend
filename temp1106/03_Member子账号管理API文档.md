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

### 接口信息
- **接口地址**: `GET /api/v1/members/sub-accounts/`
- **权限要求**: 需要用户认证，根据角色返回不同范围的数据
- **功能说明**: 获取子账号列表，支持分页和权限过滤

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 条件必填 | 租户ID，Member用户必填 | "1" | Member用户需要，管理员可选 |

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |

### 权限说明
- **Member用户**: 仅返回自己作为父账号的子账号
- **子账号**: 无权限查看任何子账号（返回空列表）
- **租户管理员**: 可查看本租户全部子账号
- **超级管理员**: 可查看全部子账号（跨租户）

### 业务规则
- ✅ 支持标准分页格式
- ✅ 权限严格控制，只能查看有权限的子账号
- ✅ 自动过滤已删除的子账号
- ✅ 返回子账号基本信息和关联关系

## 2. 创建子账号

### 接口信息
- **接口地址**: `POST /api/v1/members/sub-accounts/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 为当前用户创建子账号

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |
| Content-Type | string | 是 | 请求体类型 | "application/json" | 必须为application/json |

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| username | string | 是 | 用户名，全局唯一 | "sub_account_001" | 3-30字符，只能包含字母、数字、下划线 |
| email | string | 是 | 邮箱地址，全局唯一 | "sub@example.com" | 有效的邮箱格式 |
| phone | string | 否 | 手机号码，租户内唯一 | "13800138001" | 有效的手机号码格式 |
| nick_name | string | 否 | 昵称 | "子账号" | 最长50字符 |
| first_name | string | 否 | 名 | "子" | 最长30字符 |
| last_name | string | 否 | 姓 | "账号" | 最长30字符 |
| avatar | string | 否 | 头像相对路径 | "/media/avatars/default.jpg" | 有效的文件路径 |
| wechat_id | string | 否 | 微信ID | "sub_wechat" | 最长100字符 |

### 业务规则
- ✅ 子账号默认`is_active=false`，不能独立登录
- ✅ 自动继承父账号的租户关系
- ✅ username和email全局唯一性校验
- ✅ phone号码在租户内唯一
- ✅ 无需设置密码，子账号不能独立认证
- ✅ 只有Member用户可以创建子账号
- ❌ 子账号不能创建自己的子账号

## 3. 获取子账号详情

### 接口信息
- **接口地址**: `GET /api/v1/members/sub-accounts/{id}/`
- **权限要求**: 需要用户认证，根据角色限制访问范围
- **功能说明**: 获取指定子账号的详细信息

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 条件必填 | 租户ID，Member用户必填 | "1" | Member用户需要，管理员可选 |

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | 子账号ID | 123 | 有效的子账号ID |

### 权限说明
- **Member用户**: 仅可查看自己的子账号
- **租户管理员**: 可查看本租户的子账号
- **超级管理员**: 可查看任意子账号（跨租户）

### 业务规则
- ✅ 返回完整的子账号信息包括关联关系
- ✅ 权限严格校验，只能查看有权限的子账号
- ✅ 自动过滤已删除的子账号
- ❌ 无权限时返回404或403错误

## 4. 更新子账号信息

### 接口信息
- **接口地址**: `PUT/PATCH /api/v1/members/sub-accounts/{id}/`
- **权限要求**: 需要父账号或管理员权限
- **功能说明**: 更新指定子账号的信息

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 条件必填 | 租户ID，Member用户必填 | "1" | Member用户需要，管理员可选 |
| Content-Type | string | 是 | 请求体类型 | "application/json" | 必须为application/json |

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | 子账号ID | 123 | 有效的子账号ID |

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| phone | string | 否 | 手机号码，租户内唯一 | "13800138002" | 有效的手机号码格式 |
| nick_name | string | 否 | 昵称 | "新昵称" | 最长50字符 |
| first_name | string | 否 | 名 | "新" | 最长30字符 |
| last_name | string | 否 | 姓 | "名" | 最长30字符 |
| avatar | string | 否 | 头像相对路径 | "/media/avatars/new.jpg" | 有效的文件路径 |
| wechat_id | string | 否 | 微信ID | "new_wechat_id" | 最长100字符 |

### 不可修改字段
- `username` - 用户名
- `email` - 邮箱地址
- `parent` - 父账号ID
- `tenant` - 租户ID

### 权限说明
- **Member用户**: 仅可更新自己的子账号
- **租户管理员**: 可更新本租户的子账号
- **超级管理员**: 可更新任意子账号

### 业务规则
- ✅ PATCH支持部分更新，PUT需要完整数据
- ✅ 权限严格校验，只能更新有权限的子账号
- ✅ phone号码在租户内唯一性校验
- ✅ 不可修改核心关联字段
- ❌ 子账号不能更新自己的信息（需要通过父账号或管理员）

## 5. 删除子账号（软删除）

### 接口信息
- **接口地址**: `DELETE /api/v1/members/sub-accounts/{id}/`
- **权限要求**: 需要父账号或管理员权限
- **功能说明**: 软删除指定的子账号

### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 条件必填 | 租户ID，Member用户必填 | "1" | Member用户需要，管理员可选 |

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | 子账号ID | 123 | 有效的子账号ID |

### 权限说明
- **Member用户**: 仅可删除自己的子账号
- **租户管理员**: 可删除本租户的子账号
- **超级管理员**: 可删除任意子账号

### 业务规则
- ✅ 软删除，不会真正从数据库删除
- ✅ 删除后账号变为非活跃状态
- ✅ 保留所有关联数据和历史记录
- ✅ 权限严格校验，只能删除有权限的子账号
- ❌ 删除操作不可逆，需要管理员恢复

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
