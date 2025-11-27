# Lipeaks Coloring - Member 管理 API 文档

> 适用于 Member 用户个人信息管理和子账号管理
> 基础URL: `http://localhost:8000`
> 通用Headers:
> - `Authorization: Bearer {token}` (必须)
> - `X-Tenant-ID: {租户ID}` (必须)

---

## 一、个人信息管理 (4个接口)

### 1. 获取当前用户信息

**接口**: `GET /api/v1/members/me/`

**描述**: 获取当前登录Member用户的详细信息

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/members/me/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

### 响应参数
| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 用户ID |
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
| is_sub_account | boolean | 是否子账号 |
| parent | integer/null | 父账号ID |
| parent_username | string/null | 父账号用户名 |
| date_joined | string | 注册时间 |
| status | string | 状态 (active/inactive) |
| wechat_id | string/null | 微信ID |

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 12,
    "username": "7548155",
    "email": "7548155@qq.com",
    "phone": "13645237982",
    "nick_name": "Whahaha",
    "first_name": "",
    "last_name": "",
    "is_active": true,
    "avatar": "http://localhost:8000/media/avatars/xxx.jpg",
    "tenant": 3,
    "tenant_name": "填色",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2025-11-26T13:57:21.936833Z",
    "status": "active",
    "wechat_id": null
  }
}
```

---

### 2. 更新当前用户信息

**接口**: `PUT /api/v1/members/me/`

**描述**: 更新当前登录Member用户的信息

**注意**: 使用PUT方法，不支持PATCH

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nick_name | string | 否 | 昵称 |
| phone | string | 否 | 手机号 |
| first_name | string | 否 | 名 |
| last_name | string | 否 | 姓 |

### curl 示例
```bash
curl -X PUT "http://localhost:8000/api/v1/members/me/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "nick_name": "新昵称"
  }'
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 12,
    "username": "7548155",
    "email": "7548155@qq.com",
    "phone": "13645237982",
    "nick_name": "新昵称",
    ...
  }
}
```

---

### 3. 修改密码

**接口**: `POST /api/v1/members/me/password/`

**描述**: 修改当前登录用户的密码

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 原密码 |
| new_password | string | 是 | 新密码 |
| new_password_confirm | string | 是 | 确认新密码 |

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/members/me/password/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "old_password": "OldPassword123!",
    "new_password": "NewPassword123!",
    "new_password_confirm": "NewPassword123!"
  }'
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "密码更新成功",
  "data": {
    "message": "密码更新成功"
  }
}
```

---

### 4. 上传头像

**接口**: `POST /api/v1/members/avatar/upload/`

**描述**: 上传用户头像图片

### 请求参数
使用 `multipart/form-data` 格式:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| avatar | file | 是 | 头像图片文件 |

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/members/avatar/upload/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3" \
  -F "avatar=@/path/to/avatar.jpg"
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {
    "avatar": "http://localhost:8000/media/avatars/xxx.jpg"
  }
}
```

---

## 二、子账号管理 (5个接口)

### 1. 获取子账号列表

**接口**: `GET /api/v1/members/sub-accounts/?page={page}`

**描述**: 获取当前用户的所有子账号列表

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认10 |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/members/sub-accounts/?page=1" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

### 响应参数
| 参数 | 类型 | 说明 |
|------|------|------|
| pagination.count | integer | 总数量 |
| pagination.next | string/null | 下一页URL |
| pagination.previous | string/null | 上一页URL |
| pagination.page_size | integer | 每页数量 |
| pagination.current_page | integer | 当前页码 |
| pagination.total_pages | integer | 总页数 |
| results | array | 子账号列表 |

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 2,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 17,
        "username": "sub_account_1",
        "email": "sub1@test.com",
        "phone": null,
        "nick_name": "子账号1",
        "first_name": "",
        "last_name": "",
        "avatar": ""
      }
    ]
  }
}
```

---

### 2. 创建子账号

**接口**: `POST /api/v1/members/sub-accounts/`

**描述**: 创建一个新的子账号

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| email | string | 是 | 邮箱 |
| password | string | 是 | 密码 |
| nick_name | string | 否 | 昵称 |

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/members/sub-accounts/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "username": "sub_account_1",
    "email": "sub1@test.com",
    "password": "SubPass123!",
    "nick_name": "子账号1"
  }'
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 17,
    "username": "sub_account_1",
    "email": "sub1@test.com",
    "phone": null,
    "nick_name": "子账号1",
    "first_name": "",
    "last_name": "",
    "avatar": ""
  }
}
```

---

### 3. 获取子账号详情

**接口**: `GET /api/v1/members/sub-accounts/{id}/`

**描述**: 获取指定子账号的详细信息

### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 子账号ID |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/members/sub-accounts/17/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 17,
    "username": "sub_account_1",
    "email": "sub1@test.com",
    "phone": null,
    "nick_name": "子账号1",
    "first_name": "",
    "last_name": "",
    "avatar": "",
    "parent": 12,
    "parent_username": "7548155",
    "tenant": 3,
    "tenant_name": "填色",
    "is_sub_account": true,
    "date_joined": "2025-11-27T11:25:29.885224Z",
    "wechat_id": null
  }
}
```

---

### 4. 更新子账号

**接口**: `PUT /api/v1/members/sub-accounts/{id}/`

**描述**: 更新指定子账号的信息

### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 子账号ID |

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| email | string | 是 | 邮箱 |
| nick_name | string | 否 | 昵称 |

**注意**: PUT方法需要提供完整的必填字段

### curl 示例
```bash
curl -X PUT "http://localhost:8000/api/v1/members/sub-accounts/17/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "username": "sub_account_1",
    "email": "sub1@test.com",
    "nick_name": "子账号1更新"
  }'
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 17,
    "username": "sub_account_1",
    "email": "sub1@test.com",
    "phone": null,
    "nick_name": "子账号1更新",
    ...
  }
}
```

---

### 5. 删除子账号

**接口**: `DELETE /api/v1/members/sub-accounts/{id}/`

**描述**: 删除指定的子账号

### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 子账号ID |

### curl 示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/members/sub-accounts/17/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

### 成功响应
HTTP状态码: 204 No Content

---

## 错误响应说明

| code | message | 说明 |
|------|---------|------|
| 4000 | 数据验证失败 | 请求参数不符合要求 |
| 4004 | No Member matches the given query | 记录不存在 |
| 4005 | 方法不被允许 | HTTP方法不支持 |
| 5000 | 服务器内部错误 | 服务端异常 |
