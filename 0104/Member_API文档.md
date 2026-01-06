# Member 用户 API 文档

本文档详细说明了Member（普通用户）可使用的所有API接口，包括认证、个人中心、子账号管理、CMS文章管理和用户互动功能。

---

## 通用说明

### 基础URL
```
http://localhost:8000/api/v1/
```

### 认证方式
大多数API需要JWT认证，请在Header中添加：
```
Authorization: Bearer {JWT_TOKEN}
```

### 租户ID
多租户环境下，需要在Header中指定租户ID：
```
X-Tenant-ID: {TENANT_ID}
```

**注意**: Member用户登录时可以不指定X-Tenant-ID，系统会自动从用户关联的租户获取。

### 响应格式
所有响应遵循标准格式：
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": { ... }
}
```

### 错误码说明
- 2xxx: 成功
- 4000: 请求参数错误
- 4001: 未认证
- 4002: 认证失败
- 4003: 权限不足
- 4004: 资源不存在
- 5000: 服务器内部错误

---

## 一、认证相关 API

### 1.1 Member自助注册

**接口**: `POST /api/v1/auth/member/register/`

**权限**: 无需认证

**请求体**:
```json
{
  "username": "newmember",
  "email": "newmember@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "nick_name": "新用户",
  "tenant_id": 3
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| username | string | 是 | 用户名，唯一 |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码，需满足强度要求 |
| password_confirm | string | 是 | 确认密码 |
| nick_name | string | 否 | 昵称 |
| tenant_id | int | 否 | 租户ID，也可通过X-Tenant-ID请求头指定 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "注册成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 25,
      "username": "newmember",
      "email": "newmember@example.com",
      "nick_name": "新用户",
      "avatar": "",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
      "tenant_id": 3,
      "tenant_name": "填色"
    }
  }
}
```

---

### 1.2 登录

**接口**: `POST /api/v1/auth/login/`

**权限**: 无需认证

**请求体**:
```json
{
  "username": "member_user",
  "password": "YourPassword123!"
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| username | string | 是 | 用户名或邮箱 |
| password | string | 是 | 密码 |
| tenant_id | int | 否 | 租户ID（当同一用户名存在于多租户时需要） |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 20,
      "username": "Feng12345",
      "email": "feng@example.com",
      "nick_name": "风之子",
      "avatar": "http://localhost:8000/media/avatars/xxx.jpg",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
      "tenant_id": 3,
      "tenant_name": "填色"
    }
  }
}
```

---

### 1.3 刷新Token

**接口**: `POST /api/v1/auth/refresh/`

**权限**: 无需认证

**请求体**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "Token refreshed successfully",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

### 1.4 验证Token

**接口**: `GET /api/v1/auth/verify/`

**权限**: 需要认证

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "令牌有效",
  "data": {
    "user": {
      "id": 20,
      "username": "Feng12345",
      "email": "feng@example.com",
      "nick_name": "风之子",
      "avatar": "http://localhost:8000/media/avatars/xxx.jpg",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
      "tenant_id": 3,
      "tenant_name": "填色"
    }
  }
}
```

---

### 1.5 修改密码

**接口**: `POST /api/v1/auth/me/change-password/`

**权限**: 需要认证

**请求体**:
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword456!",
  "new_password_confirm": "NewPassword456!"
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| old_password | string | 是 | 当前密码 |
| new_password | string | 是 | 新密码 |
| new_password_confirm | string | 是 | 确认新密码 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "密码修改成功",
  "data": {
    "detail": "密码修改成功"
  }
}
```

---

### 1.6 请求密码重置

**接口**: `POST /api/v1/auth/password-reset/request/`

**权限**: 无需认证

**请求体**:
```json
{
  "email": "member@example.com",
  "account_type": "member",
  "tenant_id": 3
}
```

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| email | string | 是 | 注册邮箱 |
| account_type | string | 否 | 账号类型：user/member |
| tenant_id | int | 否 | 租户ID（多租户环境可能需要） |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "如果该邮箱存在，密码重置链接已发送",
  "data": {
    "detail": "如果该邮箱存在，密码重置链接已发送"
  }
}
```

---

### 1.7 验证密码重置令牌

**接口**: `POST /api/v1/auth/password-reset/verify/`

**权限**: 无需认证

**请求体**:
```json
{
  "token": "your_reset_token_here"
}
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "重置令牌有效",
  "data": {
    "detail": "重置令牌有效",
    "user_email": "member@example.com"
  }
}
```

---

### 1.8 确认密码重置

**接口**: `POST /api/v1/auth/password-reset/confirm/`

**权限**: 无需认证

**请求体**:
```json
{
  "token": "your_reset_token_here",
  "new_password": "NewSecurePass123!",
  "new_password_confirm": "NewSecurePass123!"
}
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "密码重置成功",
  "data": {
    "detail": "密码重置成功，请使用新密码登录"
  }
}
```

---

## 二、Member个人中心 API

### 2.1 获取当前Member信息

**接口**: `GET /api/v1/members/me/`

**权限**: 需要认证（仅Member用户）

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 20,
    "username": "Feng12345",
    "email": "feng@example.com",
    "phone": "13800138000",
    "nick_name": "风之子",
    "avatar": "http://localhost:8000/media/avatars/xxx.jpg",
    "tenant": 3,
    "tenant_name": "填色",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "status": "active",
    "date_joined": "2024-01-01T00:00:00Z"
  }
}
```

---

### 2.2 更新当前Member信息

**接口**: `PUT /api/v1/members/me/`

**权限**: 需要认证（仅Member用户）

**注意**: 不允许修改`username`和`email`字段

**请求体**:
```json
{
  "nick_name": "新昵称",
  "phone": "13900139000"
}
```

**可更新字段**:

| 字段名 | 类型 | 说明 |
|-------|------|------|
| nick_name | string | 昵称 |
| phone | string | 手机号 |
| first_name | string | 名 |
| last_name | string | 姓 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 20,
    "username": "Feng12345",
    "email": "feng@example.com",
    "phone": "13900139000",
    "nick_name": "新昵称",
    ...
  }
}
```

---

### 2.3 更新密码（Member专用）

**接口**: `POST /api/v1/members/me/password/`

**权限**: 需要认证（仅Member用户）

**请求体**:
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword456!",
  "new_password_confirm": "NewPassword456!"
}
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "密码更新成功",
  "data": null
}
```

---

### 2.4 上传头像

**接口**: `POST /api/v1/members/avatar/upload/`

**权限**: 需要认证（仅Member用户，子账号不可用）

**请求格式**: `multipart/form-data`

**请求参数**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| avatar | file | 是 | 头像文件，支持JPG、PNG、GIF、WEBP、BMP格式 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "detail": "头像上传成功",
    "avatar": "media/avatars/uuid-filename.jpg"
  }
}
```

---

### 2.5 注销账号

**接口**: `POST /api/v1/members/me/deactivate/`

**权限**: 需要认证（仅Member用户）

**警告**: 此操作不可逆，将永久删除账号及所有关联数据

**请求体**:
```json
{
  "password": "YourPassword123!",
  "confirm": true
}
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "账号已注销",
  "data": {
    "detail": "账号已成功注销，感谢您的使用"
  }
}
```

---

## 三、子账号管理 API

### 3.1 获取子账号列表

**接口**: `GET /api/v1/members/sub-accounts/`

**权限**: 需要认证（仅主账号可用）

**查询参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 3,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 25,
        "username": "sub_account_1",
        "email": "sub1@example.com",
        "phone": "13800138001",
        "nick_name": "子账号1",
        "tenant": 3,
        "tenant_name": "填色",
        "is_sub_account": true,
        "parent": 20,
        "parent_username": "Feng12345"
      }
    ]
  }
}
```

---

### 3.2 创建子账号

**接口**: `POST /api/v1/members/sub-accounts/`

**权限**: 需要认证（仅主账号可用）

**请求体**:
```json
{
  "username": "sub_account_new",
  "email": "subnew@example.com",
  "password": "SubPass123!",
  "password_confirm": "SubPass123!",
  "nick_name": "新子账号"
}
```

**响应示例**:
```json
{
  "success": true,
  "code": 2001,
  "message": "创建成功",
  "data": {
    "id": 26,
    "username": "sub_account_new",
    "email": "subnew@example.com",
    "nick_name": "新子账号",
    "tenant": 3,
    "tenant_name": "填色",
    "is_sub_account": true,
    "parent": 20,
    "parent_username": "Feng12345"
  }
}
```

---

### 3.3 获取子账号详情

**接口**: `GET /api/v1/members/sub-accounts/{id}/`

**权限**: 需要认证（只能查看自己的子账号）

---

### 3.4 更新子账号

**接口**: `PUT /api/v1/members/sub-accounts/{id}/`

**权限**: 需要认证（只能更新自己的子账号）

---

### 3.5 删除子账号

**接口**: `DELETE /api/v1/members/sub-accounts/{id}/`

**权限**: 需要认证（只能删除自己的子账号）

**响应**: 204 No Content

---

## 四、CMS文章管理 API (Member)

### 4.1 获取我的文章列表

**接口**: `GET /api/v1/cms/member/articles/`

**权限**: 需要认证

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | int | 否 | 页码，默认1 |
| status | string | 否 | 状态：draft/pending/published/archived |
| search | string | 否 | 搜索标题和内容 |
| sort | string | 否 | 排序字段：created_at/updated_at/published_at/title |
| sort_direction | string | 否 | 排序方向：asc/desc，默认desc |
| application | int | 否 | 应用ID过滤 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 50,
      "next": "http://localhost:8000/api/v1/cms/member/articles/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 5
    },
    "results": [
      {
        "id": 10331,
        "title": "我的填色作品 - 66",
        "slug": "66",
        "excerpt": "填色作品：66",
        "author_info": {
          "id": 20,
          "username": "Feng12345",
          "avatar": "http://localhost:8000/media/avatars/xxx.jpg"
        },
        "author_type": "member",
        "status": "published",
        "is_featured": false,
        "is_pinned": false,
        "cover_image": "http://localhost:8000/media/colored_artworks/66.png",
        "cover_image_small": "http://localhost:8000/media/colored_artworks/66_small.png",
        "categories": [{"id": 14, "name": "蝶舞翩翩", "slug": "category-64"}],
        "tags": [],
        "comments_count": 5,
        "likes_count": 10,
        "views_count": 100,
        "published_at": "2024-12-01T10:00:00Z",
        "created_at": "2024-12-01T09:00:00Z"
      }
    ]
  }
}
```

---

### 4.2 创建文章

**接口**: `POST /api/v1/cms/member/articles/`

**权限**: 需要认证

**请求体**:
```json
{
  "title": "我的第一篇文章",
  "content": "这是文章内容...",
  "content_type": "markdown",
  "excerpt": "文章摘要",
  "status": "draft",
  "application": 6,
  "category_ids": [12, 14],
  "tag_ids": [1, 3],
  "visibility": "public",
  "allow_comment": true,
  "cover_image": "media/uploads/cover.jpg"
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| title | string | 是 | 文章标题 |
| content | string | 是 | 文章内容 |
| content_type | string | 否 | 内容类型：markdown/html/image_upload |
| excerpt | string | 否 | 摘要，不填自动生成 |
| status | string | 否 | 状态：draft/pending，默认draft |
| application | int | 是 | 关联应用ID |
| category_ids | array | 否 | 分类ID列表 |
| tag_ids | array | 否 | 标签ID列表 |
| visibility | string | 否 | 可见性：public/private，默认public |
| allow_comment | bool | 否 | 允许评论，默认true |
| cover_image | string | 否 | 封面图片路径 |

**响应示例**:
```json
{
  "success": true,
  "code": 2001,
  "message": "创建成功",
  "data": {
    "id": 10500,
    "title": "我的第一篇文章",
    "slug": "wo-de-di-yi-pian-wen-zhang",
    "content": "这是文章内容...",
    "status": "draft",
    ...
  }
}
```

---

### 4.3 获取文章详情

**接口**: `GET /api/v1/cms/member/articles/{id}/`

**权限**: 需要认证（只能查看自己的文章）

---

### 4.4 更新文章

**接口**: `PUT /api/v1/cms/member/articles/{id}/`

**权限**: 需要认证（只能更新自己的文章）

**请求体**: 同创建文章

---

### 4.5 删除文章

**接口**: `DELETE /api/v1/cms/member/articles/{id}/`

**权限**: 需要认证（只能删除自己的文章）

**说明**: 软删除，将状态改为archived

---

### 4.6 发布文章

**接口**: `POST /api/v1/cms/member/articles/{id}/publish/`

**权限**: 需要认证（只能发布自己的文章）

**说明**: 只有draft或pending状态的文章可以发布

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "文章已成功发布",
  "data": {
    "id": 10500,
    "title": "我的第一篇文章",
    "status": "published",
    "published_at": "2024-01-04T12:00:00Z",
    ...
  }
}
```

---

### 4.7 获取文章统计

**接口**: `GET /api/v1/cms/member/articles/{id}/statistics/`

**权限**: 需要认证（只能查看自己文章的统计）

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "views_count": 100,
    "unique_views_count": 80,
    "likes_count": 20,
    "comments_count": 5,
    "shares_count": 10,
    "bookmarks_count": 15
  }
}
```

---

## 五、用户互动 API

### 5.1 获取我的收藏列表

**接口**: `GET /api/v1/interactions/favorites/`

**权限**: 需要认证

**查询参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 15,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 2
    },
    "results": [
      {
        "id": 23,
        "user": 20,
        "article": 42,
        "article_detail": {
          "id": 42,
          "title": "精美作品欣赏",
          "slug": "jing-mei-zuo-pin",
          "excerpt": "这是一篇精美的作品...",
          "cover_image": "http://localhost:8000/media/xxx.jpg",
          "author_info": {"id": 15, "username": "other_user"},
          "status": "published",
          "views_count": 1250,
          "likes_count": 42
        },
        "user_info": {
          "id": 20,
          "username": "Feng12345"
        },
        "tenant": 3,
        "created_at": "2024-01-20T10:30:00Z"
      }
    ]
  }
}
```

---

### 5.2 收藏文章

**接口**: `POST /api/v1/interactions/favorites/`

**权限**: 需要认证

**请求体**:
```json
{
  "article": 42
}
```

**响应示例**:
```json
{
  "success": true,
  "code": 2001,
  "message": "收藏成功",
  "data": {
    "id": 24,
    "user": 20,
    "article": 42,
    "article_detail": {...},
    "user_info": {...},
    "tenant": 3,
    "created_at": "2024-01-20T11:00:00Z"
  }
}
```

---

### 5.3 取消收藏

**接口**: `DELETE /api/v1/interactions/favorites/{id}/`

**权限**: 需要认证（只能删除自己的收藏）

**响应**: 204 No Content

---

### 5.4 获取文章点赞列表

**接口**: `GET /api/v1/interactions/article-likes/`

**权限**: 需要认证

---

### 5.5 点赞文章

**接口**: `POST /api/v1/interactions/article-likes/`

**权限**: 需要认证

**请求体**:
```json
{
  "article": 42
}
```

---

### 5.6 取消点赞

**接口**: `DELETE /api/v1/interactions/article-likes/{id}/`

**权限**: 需要认证（只能删除自己的点赞）

---

### 5.7 关注用户

**接口**: `POST /api/v1/interactions/follows/`

**权限**: 需要认证

**请求体**:
```json
{
  "followed": 15
}
```

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| followed | int | 是 | 被关注用户ID |

---

### 5.8 取消关注

**接口**: `DELETE /api/v1/interactions/follows/{id}/`

**权限**: 需要认证（只能取消自己的关注）

---

### 5.9 获取我的关注列表

**接口**: `GET /api/v1/interactions/follows/`

**权限**: 需要认证

---

## 六、文件上传 API

### 6.1 通用文件上传

**接口**: `POST /api/v1/common/upload-file/`

**权限**: 需要认证

**请求格式**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| file | file | 是 | 图片文件，支持JPG/JPEG/PNG/GIF/WEBP/BMP |
| folder | string | 否 | 存储子文件夹名称 |

**文件限制**:
- 支持格式：JPG、JPEG、PNG、GIF、WEBP、BMP
- 最大大小：20MB

**存储路径规则**:
- 租户用户: `uploads/{租户ID}/` 或 `uploads/{租户ID}/{folder}/`
- 超级管理员: `uploads/super_admin/` 或 `uploads/super_admin/{folder}/`

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "文件上传成功",
  "data": {
    "url": "media/uploads/3/avatars/c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "filename": "c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "size": 235065
  }
}
```

---

### 6.2 图片上传并生成缩略图

**接口**: `POST /api/v1/common/upload-image-with-thumbnail/`

**权限**: 需要认证

**请求格式**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| file | file | 是 | 图片文件，支持JPG/JPEG/PNG/GIF/WEBP/BMP |
| folder | string | 否 | 存储子文件夹名称 |

**缩略图规格**:
- 宽度: 200px（固定）
- 高度: 自适应（保持宽高比）
- 格式: JPEG
- 质量: 85
- 命名规则: `{原图UUID}_thumb_small.jpg`

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "图片上传成功",
  "data": {
    "url": "media/uploads/3/product_images/c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "filename": "c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "size": 235065,
    "thumbnail_url": "media/uploads/3/product_images/c96f4957-af76-456b-80cc-5a343f927cd3_thumb_small.jpg",
    "thumbnail_filename": "c96f4957-af76-456b-80cc-5a343f927cd3_thumb_small.jpg",
    "thumbnail_size": 15234
  }
}
```

---

### 文件上传错误响应

**未提供文件**:
```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "detail": "未提供文件"
  }
}
```

**不支持的文件类型**:
```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "detail": "不支持的文件类型，请上传JPG、PNG、GIF、WEBP或BMP格式的图片"
  }
}
```

**文件太大**:
```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "detail": "文件太大，图片大小不能超过20MB"
  }
}
```

---

### 两个API的对比

| 特性 | upload-file | upload-image-with-thumbnail |
|------|-------------|----------------------------|
| 返回内容 | 仅原图信息 | 原图 + 缩略图信息 |
| 缩略图生成 | 否 | 是（200px宽，保持宽高比） |
| 适用场景 | 通用文件上传 | 需要缩略图的图片上传 |
| 性能影响 | 较小 | 略大（需生成缩略图） |

**使用建议**:
- 如果只需要原图，使用 `upload-file`
- 如果需要列表展示/预览场景，使用 `upload-image-with-thumbnail`
- 常用folder值：`avatars`（头像）、`product_images`（产品图）、`blog_posts`（博客图）

---

## cURL 验证命令和结果

以下是API的cURL验证命令和实际返回结果。

### 前置条件

- 服务器运行在 `http://localhost:8000`
- 需要有有效的Member账号
- Member用户登录时**需要**`X-Tenant-ID`请求头

---

### 1. Member登录

**命令**:
```bash
curl -X POST 'http://localhost:8000/api/v1/auth/login/' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 3' \
  -d '{"username": "Feng12345", "password": "Member123!"}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 20,
      "username": "Feng12345",
      "email": "Feng12345@qq.com",
      "nick_name": "",
      "avatar": "http://localhost:8000/media/avatars/xxx.jpg",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
      "tenant_id": 3,
      "tenant_name": "填色"
    }
  }
}
```

---

### 2. 验证Token

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/auth/verify/' \
  -H 'Authorization: Bearer {TOKEN}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "令牌有效",
  "data": {
    "user": {
      "id": 20,
      "username": "Feng12345",
      "email": "Feng12345@qq.com",
      "nick_name": "",
      "avatar": "http://localhost:8000/media/avatars/xxx.jpg",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
      "tenant_id": 3,
      "tenant_name": "填色"
    }
  }
}
```

---

### 3. 刷新Token

**命令**:
```bash
curl -X POST 'http://localhost:8000/api/v1/auth/refresh/' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "Token refreshed successfully",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

### 4. 获取当前Member信息

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/members/me/' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'X-Tenant-ID: 3'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "username": "fx0883",
    "email": "fx0883@qq.com",
    "phone": "13397159622",
    "nick_name": "Felix",
    "first_name": "",
    "last_name": "",
    "is_active": true,
    "avatar": "http://localhost:8000/media/avatars/xxx.webp",
    "tenant": 1,
    "tenant_name": "金sir",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2025-09-04T08:07:22.287750Z",
    "status": "active",
    "wechat_id": null
  }
}
```

---

### 5. 获取子账号列表

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/members/sub-accounts/' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'X-Tenant-ID: 1'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 0,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": []
  }
}
```

---

### 6. 获取我的文章列表

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/member/articles/?page=1' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'X-Tenant-ID: 3'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 5,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 10333,
        "title": "我的填色作品 - 36",
        "slug": "36",
        "excerpt": "填色作品：36",
        "author_info": {
          "id": 20,
          "username": "Feng12345",
          "avatar": "http://localhost:8000/media/avatars/xxx.jpg"
        },
        "author_type": "member",
        "status": "archived",
        "is_featured": false,
        "is_pinned": false,
        "cover_image": "http://localhost:8000/media/uploads/3/colored_artworks/xxx.jpg",
        "categories": [],
        "tags": [],
        "comments_count": 0,
        "likes_count": 0,
        "views_count": 0
      },
      {
        "id": 10331,
        "title": "我的填色作品 - 66",
        "slug": "66",
        "excerpt": "填色作品：66",
        "author_info": {...},
        "author_type": "member",
        "status": "published",
        "cover_image": "http://localhost:8000/media/colored_artworks/66.png",
        "categories": [{"id": 14, "name": "蝶舞翩翩"}],
        "comments_count": 5,
        "likes_count": 0,
        "views_count": 0
      }
    ]
  }
}
```

---

### 7. 获取文章统计

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/member/articles/10331/statistics/' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'X-Tenant-ID: 3'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "views_count": 0,
    "unique_views_count": 0,
    "likes_count": 0,
    "comments_count": 5,
    "shares_count": 0,
    "bookmarks_count": 0
  }
}
```

---

### 8. 获取点赞列表

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/interactions/article-likes/' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'X-Tenant-ID: 3'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 0,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": []
  }
}
```

---

### 9. 通用文件上传

**命令**:
```bash
# 基本上传
curl -X POST 'http://localhost:8000/api/v1/common/upload-file/' \
  -H 'Authorization: Bearer {TOKEN}' \
  -F 'file=@/path/to/image.png'

# 指定folder上传
curl -X POST 'http://localhost:8000/api/v1/common/upload-file/' \
  -H 'Authorization: Bearer {TOKEN}' \
  -F 'file=@/path/to/image.png' \
  -F 'folder=avatars'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "文件上传成功",
  "data": {
    "url": "media/uploads/3/avatars/c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "filename": "c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "size": 235065
  }
}
```

---

### 10. 图片上传并生成缩略图

**命令**:
```bash
curl -X POST 'http://localhost:8000/api/v1/common/upload-image-with-thumbnail/' \
  -H 'Authorization: Bearer {TOKEN}' \
  -F 'file=@/path/to/image.png' \
  -F 'folder=product_images'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "图片上传成功",
  "data": {
    "url": "media/uploads/3/product_images/c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "filename": "c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "size": 235065,
    "thumbnail_url": "media/uploads/3/product_images/c96f4957-af76-456b-80cc-5a343f927cd3_thumb_small.jpg",
    "thumbnail_filename": "c96f4957-af76-456b-80cc-5a343f927cd3_thumb_small.jpg",
    "thumbnail_size": 15234
  }
}
```

---

### 错误响应示例

#### 未提供租户ID

```json
{
  "success": false,
  "code": 4100,
  "message": "Tenant operation failed",
  "data": null,
  "error_code": "TENANT_ERROR"
}
```

#### 认证失败

```json
{
  "success": false,
  "code": 4002,
  "message": "Invalid username/email or password",
  "data": null
}
```

#### 权限不足 (非Member用户访问Member专属API)

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": {
    "detail": "此接口仅适用于普通用户，请使用对应的管理员用户接口"
  }
}
```

#### 资源不存在

```json
{
  "success": false,
  "code": 4004,
  "message": "Not found.",
  "data": null,
  "error_code": "NOT_FOUND"
}
```

---

### 注意事项

1. **X-Tenant-ID必须**: Member用户登录时必须在请求头中提供`X-Tenant-ID`
2. **Token有效期**: access_token默认有1小时有效期，refresh_token有7天有效期
3. **权限限制**: Member只能操作自己的数据（文章、子账号等）
4. **软删除**: 删除文章和子账号是软删除（改为archived状态）
