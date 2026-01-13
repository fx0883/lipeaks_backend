# 租户管理员 Member 管理 API 文档

## 适用范围
- 面向租户管理员（Tenant Admin）用户
- 用于管理本租户下的所有Member用户
- 租户管理员只能管理自己租户下的Member

## 基础信息
- 前缀：`/api/v1/admin/members/`
- 认证：Bearer Token（必须）
- 权限：租户管理员（is_admin=True）

## 统一返回结构
参见 `00_租户管理员API索引.md` 中的说明。

---

## 1. 获取Member列表

### 接口信息
- 路径：GET `/api/v1/admin/members/`
- 说明：获取本租户下的所有Member列表，支持分页、搜索和过滤

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20，最大100 |
| search | string | 否 | 搜索关键词，支持用户名、邮箱、昵称、手机号搜索 |
| status | string | 否 | 用户状态筛选（active/suspended/inactive） |
| is_sub_account | boolean | 否 | 是否为子账号（true/false） |
| parent | integer | 否 | 父账号ID，筛选特定父账号下的子账号 |

### 请求头

| 请求头 | 必填 | 说明 |
|-------|------|------|
| Authorization | 是 | Bearer <access_token> |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 29,
      "next": "http://localhost:8000/api/v1/admin/members/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 3
    },
    "results": [
      {
        "id": 1,
        "username": "fx0883",
        "email": "fx0883@qq.com",
        "phone": "13397159622",
        "nick_name": "Felix",
        "first_name": "",
        "last_name": "",
        "is_active": true,
        "avatar": "http://localhost:8000/media/avatars/b74ab020-a885-46a7-bcdd-60c5fea68ef0.webp",
        "tenant": 1,
        "tenant_name": "ésir",
        "is_sub_account": false,
        "parent": null,
        "parent_username": null,
        "date_joined": "2025-09-04T08:07:22.287750Z",
        "status": "active",
        "wechat_id": null
      }
    ]
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | integer | Member ID |
| username | string | 用户名 |
| email | string | 邮箱 |
| phone | string | 手机号 |
| nick_name | string | 昵称 |
| first_name | string | 名 |
| last_name | string | 姓 |
| is_active | boolean | 是否激活 |
| avatar | string | 头像URL |
| tenant | integer | 租户ID |
| tenant_name | string | 租户名称 |
| is_sub_account | boolean | 是否为子账号 |
| parent | integer | 父账号ID（子账号时有值） |
| parent_username | string | 父账号用户名 |
| date_joined | string | 注册时间（ISO 8601） |
| status | string | 状态（active/suspended/inactive） |
| wechat_id | string | 微信ID |

### 失败响应
- 401：未认证
- 403：权限不足（非租户管理员）

### curl 调用示例
```bash
# 获取Member列表
curl -X GET "http://localhost:8000/api/v1/admin/members/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 带搜索和分页
curl -X GET "http://localhost:8000/api/v1/admin/members/?search=test&page=1&page_size=10" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 筛选子账号
curl -X GET "http://localhost:8000/api/v1/admin/members/?is_sub_account=true" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按状态筛选
curl -X GET "http://localhost:8000/api/v1/admin/members/?status=active" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 2. 创建新Member

### 接口信息
- 路径：POST `/api/v1/admin/members/`
- 说明：在本租户下创建新的Member用户

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| username | string | 是 | 用户名（租户内唯一） |
| email | string | 是 | 邮箱（租户内唯一） |
| password | string | 是 | 密码 |
| phone | string | 否 | 手机号 |
| nick_name | string | 否 | 昵称 |
| first_name | string | 否 | 名 |
| last_name | string | 否 | 姓 |
| wechat_id | string | 否 | 微信ID |
| status | string | 否 | 状态，默认active |

### 请求头

| 请求头 | 必填 | 说明 |
|-------|------|------|
| Authorization | 是 | Bearer <access_token> |
| Content-Type | 是 | application/json |

### 请求体示例
```json
{
  "username": "newmember",
  "email": "newmember@example.com",
  "password": "SecurePass123!",
  "phone": "13900139000",
  "nick_name": "新用户",
  "first_name": "张",
  "last_name": "三"
}
```

### 成功响应（201）
```json
{
  "success": true,
  "code": 2001,
  "message": "创建成功",
  "data": {
    "id": 11,
    "username": "newmember",
    "email": "newmember@example.com",
    "phone": "13900139000",
    "nick_name": "新用户",
    "first_name": "张",
    "last_name": "三",
    "is_active": true,
    "avatar": "",
    "tenant": 1,
    "tenant_name": "测试租户",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2024-01-20T15:30:00Z",
    "status": "active",
    "wechat_id": ""
  }
}
```

### 失败响应（400 验证错误）
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "username": ["Username already used in this tenant"],
    "email": ["Email already used in this tenant"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/admin/members/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newmember",
    "email": "newmember@example.com",
    "password": "SecurePass123!",
    "phone": "13900139000",
    "nick_name": "新用户"
  }'
```

---

## 3. 获取Member详情

### 接口信息
- 路径：GET `/api/v1/admin/members/{id}/`
- 说明：获取指定Member的详细信息

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| id | integer | 是 | Member ID |

### 请求头

| 请求头 | 必填 | 说明 |
|-------|------|------|
| Authorization | 是 | Bearer <access_token> |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 10,
    "username": "member1",
    "email": "member1@example.com",
    "phone": "13800138000",
    "nick_name": "普通用户1",
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
```

### 失败响应
- 403：权限不足（Member不属于当前租户）
- 404：Member不存在

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/admin/members/10/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 4. 更新Member信息

### 接口信息
- 路径：PUT/PATCH `/api/v1/admin/members/{id}/`
- 说明：更新指定Member的信息（PUT为全量更新，PATCH为部分更新）

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| id | integer | 是 | Member ID |

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| phone | string | 否 | 手机号 |
| nick_name | string | 否 | 昵称 |
| first_name | string | 否 | 名 |
| last_name | string | 否 | 姓 |
| wechat_id | string | 否 | 微信ID |
| status | string | 否 | 状态（active/suspended/inactive） |
| is_active | boolean | 否 | 是否激活 |

### 请求体示例
```json
{
  "nick_name": "更新后的昵称",
  "phone": "13900139001",
  "status": "active"
}
```

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "更新成功",
  "data": {
    "id": 10,
    "username": "member1",
    "email": "member1@example.com",
    "phone": "13900139001",
    "nick_name": "更新后的昵称",
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
```

### curl 调用示例
```bash
# 全量更新（PUT）
curl -X PUT "http://localhost:8000/api/v1/admin/members/10/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "nick_name": "更新后的昵称",
    "phone": "13900139001",
    "status": "active"
  }'

# 部分更新（PATCH）
curl -X PATCH "http://localhost:8000/api/v1/admin/members/10/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "nick_name": "只更新昵称"
  }'
```

---

## 5. 删除Member

### 接口信息
- 路径：DELETE `/api/v1/admin/members/{id}/`
- 说明：删除指定的Member（软删除）

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| id | integer | 是 | Member ID |

### 成功响应（204）
无响应体

### 失败响应
- 403：权限不足
- 404：Member不存在

### curl 调用示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/members/10/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 6. 获取子账号列表

### 接口信息
- 路径：GET `/api/v1/admin/members/sub-accounts/`
- 说明：获取本租户下的所有子账号列表

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 15,
        "username": "sub_member1",
        "email": "sub1@example.com",
        "phone": "",
        "nick_name": "子账号1",
        "is_active": true,
        "avatar": "",
        "tenant": 1,
        "tenant_name": "测试租户",
        "is_sub_account": true,
        "parent": 10,
        "parent_username": "member1",
        "date_joined": "2024-01-25T10:30:00Z",
        "status": "active"
      }
    ]
  }
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/admin/members/sub-accounts/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 7. 获取子账号详情

### 接口信息
- 路径：GET `/api/v1/admin/members/sub-accounts/{id}/`
- 说明：获取指定子账号的详细信息

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/admin/members/sub-accounts/15/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 8. 更新子账号信息

### 接口信息
- 路径：PUT/PATCH `/api/v1/admin/members/sub-accounts/{id}/`
- 说明：更新指定子账号的信息

### curl 调用示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/admin/members/sub-accounts/15/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "nick_name": "更新子账号昵称"
  }'
```

---

## 9. 删除子账号

### 接口信息
- 路径：DELETE `/api/v1/admin/members/sub-accounts/{id}/`
- 说明：删除指定的子账号（软删除）

### curl 调用示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/members/sub-accounts/15/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 10. 为Member上传头像

### 接口信息
- 路径：POST `/api/v1/admin/members/{id}/avatar/upload/`
- 说明：为指定Member上传头像图片

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| id | integer | 是 | Member ID |

### 请求参数（Form-Data）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| avatar | file | 是 | 头像文件（JPG/PNG/GIF/WEBP/BMP，≤10MB） |

### 请求头

| 请求头 | 必填 | 说明 |
|-------|------|------|
| Authorization | 是 | Bearer <access_token> |
| Content-Type | 是 | multipart/form-data |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {
    "detail": "头像上传成功",
    "avatar": "media/avatars/uuid-filename.jpg"
  }
}
```

### 失败响应（400）
```json
{
  "success": false,
  "code": 4000,
  "message": "不支持的文件类型，请上传JPG、PNG、GIF、WEBP或BMP格式的图片",
  "data": null
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/admin/members/10/avatar/upload/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -F "avatar=@/path/to/avatar.jpg"
```

---

## 错误码说明

| 错误码 | HTTP状态码 | 说明 |
|-------|-----------|------|
| 2000 | 200 | 操作成功 |
| 2001 | 201 | 创建成功 |
| 4000 | 400 | 参数验证失败 |
| 4001 | 401 | 认证失败 |
| 4003 | 403 | 权限不足 |
| 4004 | 404 | 资源不存在 |
| 5000 | 500 | 服务器内部错误 |

## 业务规则

1. **租户隔离**：租户管理员只能管理自己租户下的Member
2. **唯一性约束**：同一租户内username、email、phone必须唯一
3. **软删除**：删除操作为软删除，数据不会真正删除
4. **子账号限制**：子账号不能登录系统，不能修改头像
5. **头像限制**：
   - 支持格式：JPG、PNG、GIF、WEBP、BMP
   - 最大大小：10MB
   - 上传后会自动删除旧头像
