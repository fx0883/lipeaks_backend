# 文章管理 API 文档

## 概述

文章管理API提供了完整的CRUD功能，支持Admin和Member两种用户类型访问。

### 权限说明
- **Admin用户**：可以管理本租户所有文章，使用查询参数`?tenant_id=3`传递租户ID
- **Member用户**：只能管理自己创建的文章，使用HTTP Header`X-Tenant-ID: 3`传递租户ID

### Base URL
```
http://localhost:8000/api/v1/cms/articles
```

## API列表

### 1. 获取文章列表

获取文章列表，支持分页、过滤和搜索。

**接口地址**
```
GET /api/v1/cms/articles/
```

**请求参数（Query Parameters）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tenant_id | integer | Admin必填 | 租户ID（仅Admin用户使用） |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认10 |
| status | string | 否 | 文章状态：draft, pending, published, archived |
| category_id | integer | 否 | 按分类ID过滤 |
| tag_id | integer | 否 | 按标签ID过滤 |
| author_id | integer | 否 | 按作者ID过滤 |
| author_type | string | 否 | 按作者类型过滤：member, admin |
| search | string | 否 | 搜索关键词（标题和内容） |
| sort | string | 否 | 排序字段：created_at, updated_at, published_at, title, views_count |
| sort_direction | string | 否 | 排序方向：asc, desc（默认desc） |
| is_featured | boolean | 否 | 是否只返回特色文章 |
| is_pinned | boolean | 否 | 是否只返回置顶文章 |
| visibility | string | 否 | 可见性：public, private, password |
| date_from | string | 否 | 发布日期起始，格式YYYY-MM-DD |
| date_to | string | 否 | 发布日期截止，格式YYYY-MM-DD |

**请求头（Headers）**

Admin用户：
```
Authorization: Bearer {ADMIN_TOKEN}
```

Member用户：
```
Authorization: Bearer {MEMBER_TOKEN}
X-Tenant-ID: 3
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "count": 100,
    "next": "http://localhost:8000/api/v1/cms/articles/?page=2",
    "previous": null,
    "results": [
      {
        "id": 10298,
        "title": "示例文章标题",
        "slug": "example-article",
        "excerpt": "文章摘要...",
        "author_info": {
          "id": 10,
          "username": "test02@qq.com",
          "email": "test02@qq.com",
          "nick_name": "Nihao",
          "avatar": "http://localhost:8000/media/avatars/xxx.jpg",
          "tenant": 3,
          "tenant_name": "填色"
        },
        "author_type": "member",
        "status": "published",
        "is_featured": false,
        "is_pinned": false,
        "cover_image": "",
        "published_at": "2025-11-23T12:38:19.577494Z",
        "created_at": "2025-11-23T12:20:52.048415Z",
        "updated_at": "2025-11-23T12:38:19.501555Z",
        "categories": [],
        "tags": [],
        "comments_count": 1,
        "likes_count": 0,
        "views_count": 0
      }
    ]
  }
}
```

**curl示例**

Admin用户：
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/?tenant_id=3&page=1&status=published" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

Member用户：
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/?page=1&status=published" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"
```

---

### 2. 创建文章

创建新文章。

**接口地址**
```
POST /api/v1/cms/articles/
```

**请求头**

Admin用户：
```
Authorization: Bearer {ADMIN_TOKEN}
Content-Type: application/json
```

Member用户：
```
Authorization: Bearer {MEMBER_TOKEN}
X-Tenant-ID: 3
Content-Type: application/json
```

**请求参数（Query Parameters）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tenant_id | integer | Admin必填 | 租户ID（仅Admin用户使用） |

**请求体（Body）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 文章标题，最大255字符 |
| content | string | 是 | 文章内容 |
| content_type | string | 是 | 内容类型：markdown, html, image, video等 |
| excerpt | string | 否 | 文章摘要 |
| status | string | 否 | 状态：draft（默认）, pending, published, archived |
| category_ids | array | 否 | 分类ID数组 |
| tag_ids | array | 否 | 标签ID数组 |
| visibility | string | 否 | 可见性：public（默认）, private, password |
| password | string | 否 | 访问密码（visibility为password时必填） |
| allow_comment | boolean | 否 | 是否允许评论，默认true |
| is_featured | boolean | 否 | 是否特色文章，默认false |
| is_pinned | boolean | 否 | 是否置顶，默认false |
| cover_image | string | 否 | 封面图片URL |
| parent | integer | 否 | 父文章ID（用于创建文章层级） |
| meta | object | 否 | 元数据对象，包含seo_title, seo_description等 |

**请求示例**
```json
{
  "title": "我的第一篇文章",
  "content": "这是文章的详细内容...",
  "content_type": "markdown",
  "excerpt": "文章摘要",
  "status": "draft",
  "category_ids": [2, 5],
  "tag_ids": [3, 8, 12],
  "visibility": "public",
  "allow_comment": true,
  "meta": {
    "seo_title": "SEO标题",
    "seo_description": "SEO描述"
  }
}
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 10304,
    "title": "我的第一篇文章",
    "content": "这是文章的详细内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要",
    "status": "draft",
    "is_featured": false,
    "is_pinned": false,
    "allow_comment": true,
    "visibility": "public",
    "password": null,
    "cover_image": null,
    "published_at": null,
    "created_at": "2025-11-23T12:45:00Z",
    "updated_at": "2025-11-23T12:45:00Z"
  }
}
```

**curl示例**

Admin用户：
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "管理员创建的文章",
    "content": "文章内容",
    "content_type": "markdown",
    "status": "draft"
  }'
```

Member用户：
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Member创建的文章",
    "content": "文章内容",
    "content_type": "markdown",
    "status": "draft"
  }'
```

---

### 3. 获取单篇文章

获取指定ID的文章详情。

**接口地址**
```
GET /api/v1/cms/articles/{id}/
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 文章ID |

**请求参数（Query Parameters）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tenant_id | integer | Admin必填 | 租户ID（仅Admin用户使用） |
| password | string | 否 | 访问密码（visibility为password时需提供） |
| version | integer | 否 | 文章版本号，默认返回最新版本 |

**请求头**

Admin用户：
```
Authorization: Bearer {ADMIN_TOKEN}
```

Member用户：
```
Authorization: Bearer {MEMBER_TOKEN}
X-Tenant-ID: 3
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 10298,
    "title": "示例文章标题",
    "slug": "example-article",
    "content": "文章完整内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要...",
    "author_info": {
      "id": 10,
      "username": "test02@qq.com",
      "email": "test02@qq.com",
      "nick_name": "Nihao",
      "avatar": "http://localhost:8000/media/avatars/xxx.jpg"
    },
    "author_type": "member",
    "status": "published",
    "is_featured": false,
    "is_pinned": false,
    "allow_comment": true,
    "visibility": "public",
    "cover_image": "",
    "published_at": "2025-11-23T12:38:19Z",
    "created_at": "2025-11-23T12:20:52Z",
    "updated_at": "2025-11-23T12:38:19Z",
    "categories": [
      {"id": 2, "name": "技术分类"}
    ],
    "tags": [
      {"id": 3, "name": "Python"},
      {"id": 8, "name": "Django"}
    ],
    "meta": {
      "seo_title": "SEO标题",
      "seo_description": "SEO描述"
    },
    "statistics": {
      "views_count": 100,
      "likes_count": 20,
      "comments_count": 5
    }
  }
}
```

**curl示例**

Admin用户：
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/10298/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

Member用户：
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/10298/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"
```

---

### 4. 更新文章

更新现有文章的所有字段（PUT方法）。

**接口地址**
```
PUT /api/v1/cms/articles/{id}/
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 文章ID |

**请求参数（Query Parameters）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tenant_id | integer | Admin必填 | 租户ID（仅Admin用户使用） |

**请求头**

Admin用户：
```
Authorization: Bearer {ADMIN_TOKEN}
Content-Type: application/json
```

Member用户：
```
Authorization: Bearer {MEMBER_TOKEN}
X-Tenant-ID: 3
Content-Type: application/json
```

**请求体**

与创建文章相同，但title、content、content_type为必填。

**curl示例**

Admin用户：
```bash
curl -X PUT "http://localhost:8000/api/v1/cms/articles/10298/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的标题",
    "content": "更新后的内容",
    "content_type": "markdown",
    "status": "published"
  }'
```

---

### 5. 部分更新文章

更新文章的部分字段（PATCH方法）。

**接口地址**
```
PATCH /api/v1/cms/articles/{id}/
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 文章ID |

**请求体示例**
```json
{
  "status": "published",
  "is_featured": true
}
```

**curl示例**

```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/articles/10298/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"status": "published"}'
```

---

### 6. 删除文章

删除指定的文章（软删除，将状态改为archived）。

**接口地址**
```
DELETE /api/v1/cms/articles/{id}/
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 文章ID |

**请求参数（Query Parameters）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tenant_id | integer | Admin必填 | 租户ID（仅Admin用户使用） |
| force | boolean | 否 | 是否强制删除（真删除），默认false |

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": null
}
```

**curl示例**

软删除：
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/articles/10298/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

强制删除：
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/articles/10298/?tenant_id=3&force=true" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 7. 发布文章

将草稿文章状态改为已发布（Admin和Member都可使用，但Member只能发布自己的文章）。

**接口地址**
```
POST /api/v1/cms/articles/{id}/publish/
```

**curl示例**

Member用户发布自己的文章：
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10295/publish/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"
```

---

### 8. 取消发布文章

将已发布的文章改为草稿状态。

**接口地址**
```
POST /api/v1/cms/articles/{id}/unpublish/
```

**curl示例**

```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10298/unpublish/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"
```

---

### 9. 归档文章

将文章状态改为归档（不在前台展示）。

**接口地址**
```
POST /api/v1/cms/articles/{id}/archive/
```

**curl示例**

```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10299/archive/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"
```

---

### 10. 获取文章统计数据

获取文章的详细统计信息，包括浏览量、点赞数、地域分布等。

**接口地址**
```
GET /api/v1/cms/articles/{id}/statistics/
```

**请求参数（Query Parameters）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tenant_id | integer | Admin必填 | 租户ID |
| period | string | 否 | 统计周期：day, week, month, year, all（默认） |
| start_date | string | 否 | 统计起始日期，格式YYYY-MM-DD |
| end_date | string | 否 | 统计结束日期，格式YYYY-MM-DD |

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "basic_stats": {
      "views_count": 2,
      "unique_views_count": 0,
      "likes_count": 0,
      "dislikes_count": 0,
      "comments_count": 3,
      "shares_count": 0,
      "bookmarks_count": 0,
      "avg_reading_time": 0,
      "bounce_rate": 0.0
    },
    "time_series": {
      "views": [
        {"date": "2025-11-23", "count": 2}
      ]
    },
    "demographics": {
      "countries": [
        {"name": "未知", "count": 2}
      ],
      "devices": [
        {"name": "未知", "count": 2}
      ],
      "browsers": [
        {"name": "未知", "count": 2}
      ]
    },
    "referrers": [
      {"source": "直接访问", "count": 2}
    ]
  }
}
```

**curl示例**

```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/10298/statistics/?tenant_id=3&period=week" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 11. 记录文章阅读

记录文章的阅读行为，不需要认证。

**接口地址**
```
POST /api/v1/cms/articles/{id}/view/
```

**权限**：无需认证（公开访问）

**curl示例**

```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10298/view/" \
  -H "X-Tenant-ID: 3"
```

---

### 12. 获取文章版本历史

获取文章的所有历史版本。

**接口地址**
```
GET /api/v1/cms/articles/{id}/versions/
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "version_number": 2,
      "title": "文章标题 v2",
      "content": "更新后的内容",
      "editor": {
        "id": 3,
        "username": "admin_cms"
      },
      "change_description": "更新了文章内容",
      "created_at": "2025-11-23T12:00:00Z"
    }
  ]
}
```

**curl示例**

```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/10298/versions/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 13. 批量删除文章

批量删除多篇文章。

**接口地址**
```
POST /api/v1/cms/articles/batch-delete/
```

**请求体**
```json
{
  "article_ids": [1, 2, 3],
  "force": false
}
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "message": "文章批量删除成功",
    "requested_count": 3,
    "deleted_count": 3,
    "deleted_ids": [1, 2, 3]
  }
}
```

**curl示例**

```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/batch-delete/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [10290, 10291],
    "force": false
  }'
```

---

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无内容返回） |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 错误响应格式

```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "title": ["该字段是必填项。"]
  },
  "error_code": "VALIDATION_ERROR"
}
```
