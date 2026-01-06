# CMS API 文档

本文档详细说明了CMS系统的所有API接口，包括文章管理、分类管理、标签管理和评论管理。

---

## 通用说明

### 基础URL
```
http://localhost:8000/api/v1/cms/
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
- 4003: 权限不足
- 4004: 资源不存在
- 5000: 服务器内部错误

---

## 一、分类管理 API

### 1.1 获取分类列表

**接口**: `GET /api/v1/cms/categories/`

**权限**: 需要认证

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| parent | int | 否 | 父分类ID |
| is_active | bool | 否 | 是否激活 |
| is_pinned | bool | 否 | 是否置顶 |
| application | int | 否 | 关联应用ID |
| search | string | 否 | 搜索关键词 |
| ordering | string | 否 | 排序字段：sort_order, created_at, is_pinned |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": [
    {
      "id": 1,
      "slug": "tech-blog",
      "parent": null,
      "cover_image": "http://example.com/media/image.jpg",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "sort_order": 0,
      "tenant": 17,
      "application": 6,
      "application_name": "博客应用",
      "is_active": true,
      "is_pinned": false,
      "translations": {
        "zh-hans": {
          "name": "技术博客",
          "description": "技术相关文章",
          "seo_title": "技术博客",
          "seo_description": "技术博客描述"
        },
        "en": {
          "name": "Tech Blog",
          "description": "Tech articles"
        }
      },
      "name": "技术博客",
      "description": "技术相关文章"
    }
  ]
}
```

---

### 1.2 创建分类

**接口**: `POST /api/v1/cms/categories/`

**权限**: 需要管理员权限

**请求体**:
```json
{
  "slug": "my-category",
  "parent": null,
  "cover_image": "media/uploads/17/image.png",
  "application": 6,
  "is_active": true,
  "is_pinned": false,
  "sort_order": 0,
  "translations": {
    "zh-hans": {
      "name": "分类名称",
      "description": "分类描述",
      "seo_title": "SEO标题",
      "seo_description": "SEO描述"
    }
  }
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| slug | string | 否 | URL别名，不填则自动生成 |
| parent | int | 否 | 父分类ID |
| cover_image | string | 否 | 封面图片路径 |
| application | int | 否 | 关联应用ID |
| is_active | bool | 否 | 是否激活，默认true |
| is_pinned | bool | 否 | 是否置顶，默认false |
| sort_order | int | 否 | 排序，默认0 |
| translations | object | 是 | 多语言翻译内容 |

---

### 1.3 获取分类详情

**接口**: `GET /api/v1/cms/categories/{id}/`

**权限**: 需要认证

**路径参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | int | 分类ID |

---

### 1.4 更新分类

**接口**: `PUT /api/v1/cms/categories/{id}/`

**权限**: 需要管理员权限

**请求体**: 同创建分类

---

### 1.5 删除分类

**接口**: `DELETE /api/v1/cms/categories/{id}/`

**权限**: 需要管理员权限

**注意**: 如有关联文章或子分类，将无法删除

---

### 1.6 获取分类树

**接口**: `GET /api/v1/cms/categories/tree/`

**权限**: 需要认证

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": [
    {
      "id": 1,
      "name": "技术博客",
      "slug": "tech-blog",
      "description": "技术相关文章",
      "is_active": true,
      "sort_order": 0,
      "children": [
        {
          "id": 2,
          "name": "Python教程",
          "slug": "python-tutorial",
          "children": []
        }
      ]
    }
  ]
}
```

---

## 二、标签组管理 API

### 2.1 获取标签组列表

**接口**: `GET /api/v1/cms/tag-groups/`

**权限**: 需要认证

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| is_active | bool | 否 | 是否激活 |
| search | string | 否 | 搜索关键词 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "count": 2,
    "results": [
      {
        "id": 1,
        "name": "技术栈",
        "slug": "tech-stack",
        "description": "编程技术标签",
        "created_at": "2024-01-01T00:00:00Z",
        "is_active": true,
        "tenant": 17
      }
    ]
  }
}
```

---

### 2.2 创建标签组

**接口**: `POST /api/v1/cms/tag-groups/`

**请求体**:
```json
{
  "name": "技术栈",
  "slug": "tech-stack",
  "description": "编程技术标签",
  "is_active": true
}
```

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 标签组名称 |
| slug | string | 否 | URL别名，不填自动生成 |
| description | string | 否 | 描述 |
| is_active | bool | 否 | 是否激活，默认true |

---

## 三、标签管理 API

### 3.1 获取标签列表

**接口**: `GET /api/v1/cms/tags/`

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| group | int | 否 | 标签组ID |
| is_active | bool | 否 | 是否激活 |
| search | string | 否 | 搜索关键词 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "count": 5,
    "results": [
      {
        "id": 1,
        "name": "Python",
        "slug": "python",
        "description": "Python编程语言",
        "group": 1,
        "group_name": "技术栈",
        "color": "#3776AB",
        "is_active": true,
        "tenant": 17
      }
    ]
  }
}
```

---

### 3.2 创建标签

**接口**: `POST /api/v1/cms/tags/`

**请求体**:
```json
{
  "name": "Python",
  "slug": "python",
  "description": "Python编程语言",
  "group": 1,
  "color": "#3776AB",
  "is_active": true
}
```

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 标签名称 |
| slug | string | 否 | URL别名 |
| description | string | 否 | 描述 |
| group | int | 否 | 标签组ID |
| color | string | 否 | 颜色值 |
| is_active | bool | 否 | 是否激活 |

---

### 3.3 获取标签使用统计

**接口**: `GET /api/v1/cms/tags/usage-stats/`

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": [
    {
      "id": 1,
      "name": "Python",
      "slug": "python",
      "color": "#3776AB",
      "articles_count": 15
    }
  ]
}
```

---

## 四、文章管理 API (管理员)

### 4.1 获取文章列表

**接口**: `GET /api/v1/cms/articles/`

**权限**: 需要认证

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | int | 否 | 页码，默认1 |
| status | string | 否 | 状态：draft/pending/published/archived |
| category_id | int | 否 | 分类ID |
| tag_id | int | 否 | 标签ID |
| author_id | int | 否 | 作者ID |
| author_type | string | 否 | 作者类型：member/admin |
| user_id | int | 否 | 管理员用户ID |
| member_id | int | 否 | 会员用户ID |
| search | string | 否 | 搜索标题和内容 |
| sort | string | 否 | 排序字段 |
| sort_direction | string | 否 | 排序方向：asc/desc |
| is_featured | bool | 否 | 是否特色文章 |
| is_pinned | bool | 否 | 是否置顶 |
| visibility | string | 否 | 可见性：public/private/password |
| date_from | string | 否 | 发布日期起始 |
| date_to | string | 否 | 发布日期截止 |
| application | int | 否 | 应用ID |
| has_parent | bool | 否 | 是否有父文章 |
| parent_id | int | 否 | 父文章ID |
| category_application_id | int | 否 | 按分类应用ID过滤 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "count": 50,
    "next": "http://localhost:8000/api/v1/cms/articles/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "title": "示例文章",
        "slug": "example-article",
        "excerpt": "文章摘要...",
        "author_info": {
          "id": 1,
          "username": "admin",
          "display_name": "管理员"
        },
        "author_type": "admin",
        "status": "published",
        "is_featured": false,
        "is_pinned": false,
        "is_locked": false,
        "cover_image": "http://example.com/media/image.jpg",
        "cover_image_small": "http://example.com/media/image_thumb.jpg",
        "published_at": "2024-01-01T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "categories": [
          {"id": 1, "name": "技术", "slug": "tech"}
        ],
        "tags": [
          {"id": 1, "name": "Python", "slug": "python", "color": "#3776AB"}
        ],
        "comments_count": 5,
        "likes_count": 20,
        "views_count": 100,
        "parent": null,
        "parent_info": null,
        "children_count": 0
      }
    ]
  }
}
```

---

### 4.2 创建文章

**接口**: `POST /api/v1/cms/articles/`

**权限**: 需要认证

**请求体**:
```json
{
  "title": "文章标题",
  "content": "文章内容...",
  "content_type": "markdown",
  "excerpt": "文章摘要",
  "status": "draft",
  "is_featured": false,
  "is_pinned": false,
  "is_locked": false,
  "allow_comment": true,
  "visibility": "public",
  "password": null,
  "cover_image": "media/uploads/17/image.png",
  "cover_image_small": "media/uploads/17/image_thumb.jpg",
  "template": null,
  "sort_order": 0,
  "parent": null,
  "category_ids": [1, 2],
  "tag_ids": [1, 3],
  "applications": [6],
  "meta": {
    "seo_title": "SEO标题",
    "seo_description": "SEO描述",
    "seo_keywords": "关键词1,关键词2"
  },
  "publish_now": false,
  "scheduled_publish_time": null
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| title | string | 是 | 文章标题 |
| content | string | 是 | 文章内容 |
| content_type | string | 否 | 内容类型：markdown/html/image等 |
| excerpt | string | 否 | 摘要，不填自动从内容提取 |
| status | string | 否 | 状态：draft/pending/published/archived |
| is_featured | bool | 否 | 是否特色，默认false |
| is_pinned | bool | 否 | 是否置顶，默认false |
| is_locked | bool | 否 | 是否锁定，默认false |
| allow_comment | bool | 否 | 允许评论，默认true |
| visibility | string | 否 | 可见性：public/private/password |
| password | string | 否 | 访问密码（visibility为password时） |
| cover_image | string | 否 | 封面图片路径 |
| cover_image_small | string | 否 | 封面缩略图路径 |
| template | string | 否 | 模板名称 |
| sort_order | int | 否 | 排序 |
| parent | int | 否 | 父文章ID |
| category_ids | array | 否 | 分类ID列表 |
| tag_ids | array | 否 | 标签ID列表 |
| applications | array | 是 | 关联应用ID列表(创建时必填) |
| meta | object | 否 | SEO元数据 |
| publish_now | bool | 否 | 是否立即发布 |
| scheduled_publish_time | datetime | 否 | 定时发布时间 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "创建成功",
  "data": {
    "id": 1,
    "title": "文章标题",
    "slug": "wen-zhang-biao-ti",
    ...
  }
}
```

---

### 4.3 获取文章详情

**接口**: `GET /api/v1/cms/articles/{id}/`

**权限**: 需要认证

**路径参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | int | 文章ID |

**查询参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| password | string | 访问密码(文章为password可见性时需要) |
| version | int | 指定版本号 |

---

### 4.4 更新文章

**接口**: `PUT /api/v1/cms/articles/{id}/`

**请求体**: 同创建文章，额外字段：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| change_description | string | 变更说明 |
| create_new_version | bool | 是否创建新版本，默认true |

---

### 4.5 删除文章

**接口**: `DELETE /api/v1/cms/articles/{id}/`

**查询参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| force | bool | 是否强制删除(true=物理删除，false=软删除) |

---

### 4.6 批量删除文章

**接口**: `POST /api/v1/cms/articles/batch-delete/`

**请求体**:
```json
{
  "article_ids": [1, 2, 3],
  "force": false
}
```

---

### 4.7 发布文章

**接口**: `POST /api/v1/cms/articles/{id}/publish/`

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "文章已成功发布",
  "data": {
    "id": 1,
    "status": "published",
    "published_at": "2024-01-04T12:00:00Z"
  }
}
```

---

### 4.8 取消发布文章

**接口**: `POST /api/v1/cms/articles/{id}/unpublish/`

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "文章已取消发布",
  "data": {
    "id": 1,
    "status": "draft"
  }
}
```

---

### 4.9 归档文章

**接口**: `POST /api/v1/cms/articles/{id}/archive/`

---

### 4.10 获取文章版本历史

**接口**: `GET /api/v1/cms/articles/{id}/versions/`

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": [
    {
      "id": 1,
      "article": 1,
      "title": "文章标题",
      "content": "文章内容...",
      "content_type": "markdown",
      "excerpt": "摘要",
      "editor": 1,
      "editor_info": {...},
      "version_number": 2,
      "change_description": "更新了内容",
      "created_at": "2024-01-02T00:00:00Z"
    }
  ]
}
```

---

### 4.11 获取特定版本

**接口**: `GET /api/v1/cms/articles/{id}/versions/{version_number}/`

---

### 4.12 获取文章统计

**接口**: `GET /api/v1/cms/articles/{id}/statistics/`

**查询参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| period | string | 周期：day/week/month/year/all |
| start_date | string | 起始日期 |
| end_date | string | 结束日期 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "basic_stats": {
      "views_count": 100,
      "unique_views_count": 80,
      "likes_count": 20,
      "dislikes_count": 2,
      "comments_count": 5,
      "shares_count": 10,
      "bookmarks_count": 15,
      "avg_reading_time": 180,
      "bounce_rate": 25.5
    },
    "time_series": {
      "views": [
        {"date": "2024-01-01", "count": 10},
        {"date": "2024-01-02", "count": 15}
      ]
    },
    "demographics": {
      "countries": [{"name": "中国", "count": 80}],
      "devices": [{"name": "Mobile", "count": 60}],
      "browsers": [{"name": "Chrome", "count": 50}]
    },
    "referrers": [
      {"source": "直接访问", "count": 40}
    ]
  }
}
```

---

### 4.13 记录文章阅读

**接口**: `POST /api/v1/cms/articles/{id}/view/`

**权限**: 无需认证

**说明**: 每次调用增加阅读数1次

---

## 五、Member文章管理 API

供普通会员用户使用，只能操作自己的文章。

### 5.1 获取我的文章列表

**接口**: `GET /api/v1/cms/member/articles/`

**查询参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| page | int | 页码 |
| status | string | 状态 |
| search | string | 搜索 |
| sort | string | 排序字段 |
| sort_direction | string | 排序方向 |
| application | int | 应用ID |

---

### 5.2 创建文章 (Member)

**接口**: `POST /api/v1/cms/member/articles/`

**请求体**:
```json
{
  "title": "我的第一篇文章",
  "content": "文章内容...",
  "content_type": "markdown",
  "excerpt": "摘要",
  "status": "draft",
  "application": 6,
  "category_ids": [1, 2],
  "tag_ids": [1, 3],
  "visibility": "public",
  "allow_comment": true
}
```

**注意**: Member用户使用单值`application`，而非数组`applications`

---

### 5.3 发布文章 (Member)

**接口**: `POST /api/v1/cms/member/articles/{id}/publish/`

---

## 六、评论管理 API

### 6.1 获取评论列表

**接口**: `GET /api/v1/cms/comments/`

**查询参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| article | int | 文章ID |
| parent | int | 父评论ID(为空获取顶级评论) |
| user | int | 用户ID |
| status | string | 状态：pending/approved/rejected/spam |
| is_pinned | bool | 是否置顶 |
| search | string | 搜索内容 |
| sort | string | 排序字段 |
| sort_direction | string | 排序方向 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "count": 10,
    "results": [
      {
        "id": 1,
        "article": 1,
        "parent": null,
        "user": null,
        "member": 5,
        "author_info": {
          "id": 5,
          "username": "member1",
          "display_name": "会员1"
        },
        "author_type": "member",
        "guest_name": null,
        "guest_email": null,
        "content": "这是一条评论",
        "status": "approved",
        "created_at": "2024-01-01T00:00:00Z",
        "is_pinned": false,
        "likes_count": 5,
        "replies_count": 2
      }
    ]
  }
}
```

---

### 6.2 创建评论

**接口**: `POST /api/v1/cms/comments/`

**请求体 (已认证用户)**:
```json
{
  "article": 1,
  "parent": null,
  "content": "这是一条评论内容"
}
```

**请求体 (游客)**:
```json
{
  "article": 1,
  "parent": null,
  "content": "这是一条评论内容",
  "guest_name": "游客小明",
  "guest_email": "guest@example.com",
  "guest_website": "https://example.com"
}
```

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| article | int | 是 | 文章ID |
| parent | int | 否 | 父评论ID(回复时) |
| content | string | 是 | 评论内容 |
| guest_name | string | 否 | 游客名称(游客评论必填) |
| guest_email | string | 否 | 游客邮箱 |
| guest_website | string | 否 | 游客网站 |

---

### 6.3 更新评论

**接口**: `PUT /api/v1/cms/comments/{id}/`

**权限**: 只能更新自己的评论，或管理员

---

### 6.4 删除评论

**接口**: `DELETE /api/v1/cms/comments/{id}/`

**权限**: 只能删除自己的评论，或管理员

---

## cURL 验证命令和结果

以下是API的cURL验证命令和实际返回结果。

### 前置条件

- 服务器运行在 `http://localhost:8000`
- 需要有有效的租户管理员账号
- 租户管理员登录时**不需要**X-Tenant-ID（系统自动从用户关联获取）

---

### 1. 登录获取Token

**命令**:
```bash
curl -X POST 'http://localhost:8000/api/v1/auth/login/' \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin_cms", "password": "Admin123!"}'
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
      "id": 3,
      "username": "admin_cms",
      "email": "jackfeng8123@gmail.com",
      "is_admin": true,
      "is_super_admin": false,
      "tenant_id": 3,
      "tenant_name": "填色"
    }
  }
}
```

---

### 2. 获取分类列表

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'Authorization: Bearer {TOKEN}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 12,
      "slug": "category-62",
      "parent": null,
      "cover_image": "http://localhost:8000/media/category_image/12.png",
      "created_at": "2025-10-26T06:05:13.899884Z",
      "sort_order": 0,
      "tenant": 3,
      "application": 6,
      "application_name": "填色花园",
      "is_active": true,
      "is_pinned": true,
      "translations": {
        "zh-hans": {"name": "二次元少女", "description": ""},
        "en": {"name": "Anime Girls", "description": ""}
      },
      "name": "二次元少女",
      "description": ""
    }
  ]
}
```

---

### 3. 获取分类树

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/categories/tree/' \
  -H 'Authorization: Bearer {TOKEN}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 12,
      "name": "二次元少女",
      "slug": "category-62",
      "description": "",
      "is_active": true,
      "sort_order": 0,
      "children": []
    },
    {
      "id": 30,
      "name": "美味时刻",
      "slug": "category-84",
      "description": "",
      "is_active": true,
      "sort_order": 1,
      "children": []
    }
  ]
}
```

---

### 4. 获取标签组列表

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/tag-groups/' \
  -H 'Authorization: Bearer {TOKEN}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 10,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 5,
        "name": "Test Group",
        "slug": "test-group",
        "description": null,
        "created_at": "2025-11-23T12:46:51.010862Z",
        "is_active": true,
        "tenant": 3
      }
    ]
  }
}
```

---

### 5. 获取标签列表

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/tags/' \
  -H 'Authorization: Bearer {TOKEN}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 16,
      "next": "http://localhost:8000/api/v1/cms/tags/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 2
    },
    "results": [
      {
        "id": 16,
        "name": "Python",
        "slug": "python",
        "description": "Python编程语言",
        "group": 11,
        "group_name": "编程语言",
        "color": "#3776AB",
        "is_active": true,
        "tenant": 3
      }
    ]
  }
}
```

---

### 6. 获取标签使用统计

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/tags/usage-stats/' \
  -H 'Authorization: Bearer {TOKEN}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 2,
      "name": "验证更新标签",
      "slug": "test-tag",
      "color": null,
      "articles_count": 0
    }
  ]
}
```

---

### 7. 获取文章列表

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/articles/?page=1&status=published' \
  -H 'Authorization: Bearer {TOKEN}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 9609,
      "next": "http://localhost:8000/api/v1/cms/articles/?page=2&status=published",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 961
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
        "likes_count": 0,
        "views_count": 0
      }
    ]
  }
}
```

---

### 8. 获取文章详情

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/articles/10331/' \
  -H 'Authorization: Bearer {TOKEN}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 10331,
    "title": "我的填色作品 - 66",
    "slug": "66",
    "content": "这是我的填色作品",
    "content_type": "image_upload",
    "excerpt": "填色作品：66",
    "author_info": {...},
    "author_type": "member",
    "status": "published",
    "is_featured": false,
    "is_pinned": false,
    "is_locked": false,
    "allow_comment": true,
    "visibility": "public",
    "cover_image": "http://localhost:8000/media/colored_artworks/66.png",
    "tenant_info": {
      "id": 3,
      "name": "填色",
      "status": "active"
    },
    "categories": [{"id": 14, "name": "蝶舞翩翩"}],
    "tags": [],
    "meta": null,
    "stats": {...}
  }
}
```

---

### 9. 获取文章统计

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/articles/10331/statistics/' \
  -H 'Authorization: Bearer {TOKEN}'
```

**成功响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "basic_stats": {
      "views_count": 0,
      "unique_views_count": 0,
      "likes_count": 0,
      "dislikes_count": 0,
      "comments_count": 5,
      "shares_count": 0,
      "bookmarks_count": 0,
      "avg_reading_time": 0,
      "bounce_rate": 0.0
    },
    "time_series": {"views": []},
    "demographics": {
      "countries": [],
      "devices": [],
      "browsers": []
    },
    "referrers": []
  }
}
```

---

### 10. 获取评论列表

**命令**:
```bash
curl -X GET 'http://localhost:8000/api/v1/cms/comments/?article=10331' \
  -H 'Authorization: Bearer {TOKEN}'
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
        "id": 124,
        "article": 10331,
        "parent": null,
        "user": null,
        "member": 21,
        "author_info": {
          "id": 21,
          "username": "Mike",
          "avatar": ""
        },
        "author_type": "member",
        "guest_name": null,
        "content": "👏 越来越棒了！",
        "status": "approved",
        "created_at": "2025-12-19T04:21:20.712272Z",
        "is_pinned": false,
        "likes_count": 0,
        "replies_count": 0
      }
    ]
  }
}
```

---

### 错误响应示例

#### 未提供租户ID (超级管理员访问时)

```json
{
  "success": false,
  "code": 4500,
  "message": "未提供租户ID，无法访问CMS资源",
  "data": null,
  "error_code": "TENANT_ID_REQUIRED"
}
```

#### 资源不存在

```json
{
  "success": false,
  "code": 4004,
  "message": "No Article matches the given query.",
  "data": null,
  "error_code": "NOT_FOUND"
}
```

#### 认证失败

```json
{
  "success": false,
  "code": 4001,
  "message": "认证失败",
  "data": {
    "detail": "身份验证凭据未提供或已过期"
  }
}
```
