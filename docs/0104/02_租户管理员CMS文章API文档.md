# 租户管理员 CMS 文章管理 API 文档

## 适用范围
- 面向租户管理员（Tenant Admin）用户
- 用于管理本租户下的所有文章内容
- 租户管理员只能管理自己租户下的文章

## 基础信息
- 前缀：`/api/v1/cms/articles/`
- 认证：Bearer Token（必须）
- 权限：租户管理员（is_admin=True）

## 统一返回结构
参见 `00_租户管理员API索引.md` 中的说明。

---

## 1. 获取文章列表

### 接口信息
- 路径：GET `/api/v1/cms/articles/`
- 说明：获取本租户下的文章列表，支持分页、过滤和搜索

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| status | string | 否 | 文章状态（draft/pending/published/archived） |
| category_id | integer | 否 | 按分类ID过滤 |
| tag_id | integer | 否 | 按标签ID过滤 |
| author_id | integer | 否 | 按作者ID过滤 |
| author_type | string | 否 | 作者类型（member/admin） |
| user_id | integer | 否 | 管理员用户ID |
| member_id | integer | 否 | 会员用户ID |
| search | string | 否 | 搜索关键词，在标题和内容中匹配 |
| sort | string | 否 | 排序字段（created_at/updated_at/published_at/title/views_count） |
| sort_direction | string | 否 | 排序方向（asc/desc），默认desc |
| is_featured | boolean | 否 | 是否只返回特色文章 |
| is_pinned | boolean | 否 | 是否只返回置顶文章 |
| visibility | string | 否 | 可见性（public/private/password） |
| date_from | string | 否 | 发布日期起始（YYYY-MM-DD） |
| date_to | string | 否 | 发布日期截止（YYYY-MM-DD） |
| application | integer | 否 | 应用ID过滤 |
| has_parent | boolean | 否 | 是否有父文章（true/false） |
| parent_id | integer | 否 | 父文章ID |
| category_application_id | integer | 否 | 按分类所属应用ID过滤 |

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
      "count": 38,
      "next": "http://localhost:8000/api/v1/cms/articles/?page=2&tenant_id=1",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 4
    },
    "results": [
      {
        "id": 631,
        "title": "LipeaksCompress v1 11 svg tiff support: New Features Released",
        "slug": "lipeakscompress-v1-11-svg-tiff-support-new-features-released",
        "excerpt": "LipeaksCompress v1 11 svg tiff support: New Features Released...",
        "author_info": {
          "id": 2,
          "username": "admin_jin",
          "email": "admin_jin@qq.com",
          "nick_name": "",
          "is_admin": true,
          "tenant": 1,
          "tenant_name": "ésir"
        },
        "author_type": "admin",
        "status": "published",
        "is_featured": false,
        "is_pinned": false,
        "is_locked": false,
        "cover_image": "http://localhost:8000/media/article_image/631.png",
        "cover_image_small": "",
        "published_at": null,
        "created_at": "2025-10-10T14:18:07.616788Z",
        "updated_at": "2025-12-04T22:45:25Z",
        "categories": [
          {"id": 5, "name": "How To", "slug": "how-to-841"}
        ],
        "tags": [],
        "comments_count": 0,
        "likes_count": 0,
        "views_count": 1,
        "parent": null,
        "parent_info": null,
        "children_count": 0
      }
    ]
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | integer | 文章ID |
| title | string | 文章标题 |
| slug | string | 文章别名（URL友好） |
| excerpt | string | 文章摘要 |
| status | string | 状态（draft/pending/published/archived） |
| visibility | string | 可见性（public/private/password） |
| is_featured | boolean | 是否特色文章 |
| is_pinned | boolean | 是否置顶 |
| cover_image | string | 封面图片URL |
| author_name | string | 作者名称 |
| author_type | string | 作者类型（admin/member） |
| categories | array | 所属分类列表 |
| tags | array | 标签列表 |
| views_count | integer | 浏览次数 |
| comments_count | integer | 评论数 |
| likes_count | integer | 点赞数 |
| created_at | string | 创建时间（ISO 8601） |
| updated_at | string | 更新时间 |
| published_at | string | 发布时间 |

### curl 调用示例
```bash
# 获取文章列表
curl -X GET "http://localhost:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按状态筛选已发布文章
curl -X GET "http://localhost:8000/api/v1/cms/articles/?status=published" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按分类筛选
curl -X GET "http://localhost:8000/api/v1/cms/articles/?category_id=1" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 搜索文章
curl -X GET "http://localhost:8000/api/v1/cms/articles/?search=Python教程" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按日期范围筛选
curl -X GET "http://localhost:8000/api/v1/cms/articles/?date_from=2024-01-01&date_to=2024-01-31" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 2. 创建文章

### 接口信息
- 路径：POST `/api/v1/cms/articles/`
- 说明：创建新文章

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| title | string | 是 | 文章标题 |
| content | string | 是 | 文章内容 |
| content_type | string | 否 | 内容类型（markdown/html/text），默认markdown |
| excerpt | string | 否 | 文章摘要 |
| slug | string | 否 | 文章别名，不填则自动生成 |
| status | string | 否 | 状态（draft/published），默认draft |
| visibility | string | 否 | 可见性（public/private/password），默认public |
| password | string | 否 | 访问密码（visibility为password时需要） |
| category_ids | array | 否 | 分类ID列表 |
| tag_ids | array | 否 | 标签ID列表 |
| cover_image | string | 否 | 封面图片URL |
| is_featured | boolean | 否 | 是否特色文章 |
| is_pinned | boolean | 否 | 是否置顶 |
| allow_comments | boolean | 否 | 是否允许评论，默认true |
| parent_id | integer | 否 | 父文章ID（用于创建子文章） |
| meta | object | 否 | SEO元信息 |

### 请求体示例
```json
{
  "title": "示例文章标题",
  "content": "# 标题\n\n这是文章内容...",
  "content_type": "markdown",
  "excerpt": "文章摘要内容",
  "status": "draft",
  "category_ids": [1, 2],
  "tag_ids": [3, 5],
  "is_featured": false,
  "is_pinned": false,
  "meta": {
    "seo_title": "SEO标题",
    "seo_description": "SEO描述"
  }
}
```

### 成功响应（201）
```json
{
  "success": true,
  "code": 2001,
  "message": "创建成功",
  "data": {
    "id": 10,
    "title": "示例文章标题",
    "slug": "shi-li-wen-zhang-biao-ti",
    "content": "# 标题\n\n这是文章内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要内容",
    "status": "draft",
    "visibility": "public",
    "is_featured": false,
    "is_pinned": false,
    "cover_image": null,
    "author_name": "admin",
    "author_type": "admin",
    "categories": [
      {"id": 1, "name": "技术博客"},
      {"id": 2, "name": "教程"}
    ],
    "tags": [
      {"id": 3, "name": "Python"},
      {"id": 5, "name": "Django"}
    ],
    "created_at": "2024-01-20T15:30:00Z",
    "updated_at": "2024-01-20T15:30:00Z",
    "published_at": null
  }
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "示例文章标题",
    "content": "# 标题\n\n这是文章内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要内容",
    "status": "draft",
    "category_ids": [1, 2],
    "tag_ids": [3, 5]
  }'
```

---

## 3. 获取文章详情

### 接口信息
- 路径：GET `/api/v1/cms/articles/{id}/`
- 说明：获取指定文章的详细信息

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| id | integer | 是 | 文章ID |

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| password | string | 否 | 访问密码（当文章可见性为password时需提供） |
| version | integer | 否 | 文章版本号，默认返回最新版本 |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 1,
    "title": "示例文章标题",
    "slug": "example-article",
    "content": "# 标题\n\n这是文章完整内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要内容",
    "status": "published",
    "visibility": "public",
    "is_featured": false,
    "is_pinned": false,
    "cover_image": "/media/articles/cover.jpg",
    "author": {
      "id": 1,
      "username": "admin",
      "nick_name": "管理员",
      "avatar": "/media/avatars/admin.jpg"
    },
    "author_type": "admin",
    "categories": [
      {"id": 1, "name": "技术博客", "slug": "tech"}
    ],
    "tags": [
      {"id": 1, "name": "Python", "slug": "python"}
    ],
    "meta": {
      "seo_title": "SEO标题",
      "seo_description": "SEO描述",
      "seo_keywords": "关键词1,关键词2"
    },
    "statistics": {
      "views_count": 100,
      "unique_views_count": 80,
      "likes_count": 20,
      "dislikes_count": 2,
      "comments_count": 5,
      "shares_count": 10,
      "bookmarks_count": 15
    },
    "allow_comments": true,
    "parent": null,
    "children": [],
    "version_number": 3,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-20T15:30:00Z",
    "published_at": "2024-01-16T08:00:00Z"
  }
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 获取特定版本
curl -X GET "http://localhost:8000/api/v1/cms/articles/1/?version=2" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 4. 更新文章

### 接口信息
- 路径：PUT/PATCH `/api/v1/cms/articles/{id}/`
- 说明：更新文章内容（PUT全量更新，PATCH部分更新）

### 请求参数（Body）
同创建文章参数，另外支持：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| create_new_version | boolean | 否 | 是否创建新版本，默认false |
| change_description | string | 否 | 版本变更说明 |

### 请求体示例
```json
{
  "title": "更新后的文章标题",
  "content": "更新后的文章内容...",
  "create_new_version": true,
  "change_description": "更新了文章标题和内容"
}
```

### curl 调用示例
```bash
# 全量更新
curl -X PUT "http://localhost:8000/api/v1/cms/articles/1/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的文章标题",
    "content": "更新后的文章内容...",
    "status": "published"
  }'

# 部分更新
curl -X PATCH "http://localhost:8000/api/v1/cms/articles/1/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "is_featured": true
  }'
```

---

## 5. 删除文章

### 接口信息
- 路径：DELETE `/api/v1/cms/articles/{id}/`
- 说明：删除指定文章（默认软删除）

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| force | boolean | 否 | 是否强制删除（true为真实删除，false为软删除） |

### curl 调用示例
```bash
# 软删除（归档）
curl -X DELETE "http://localhost:8000/api/v1/cms/articles/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 强制删除
curl -X DELETE "http://localhost:8000/api/v1/cms/articles/1/?force=true" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 6. 发布文章

### 接口信息
- 路径：POST `/api/v1/cms/articles/{id}/publish/`
- 说明：将文章状态改为已发布

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "文章已成功发布",
  "data": {
    "id": 1,
    "status": "published",
    "published_at": "2024-01-20T16:00:00Z"
  }
}
```

### 失败响应（400）
```json
{
  "success": false,
  "code": 4000,
  "message": "文章已经是发布状态",
  "data": null
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/1/publish/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 7. 取消发布文章

### 接口信息
- 路径：POST `/api/v1/cms/articles/{id}/unpublish/`
- 说明：将文章状态从已发布改为草稿

### 成功响应（200）
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

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/1/unpublish/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 8. 归档文章

### 接口信息
- 路径：POST `/api/v1/cms/articles/{id}/archive/`
- 说明：将文章状态改为归档（不在前台展示但保留数据）

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "文章已归档",
  "data": {
    "id": 1,
    "status": "archived"
  }
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/1/archive/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 9. 批量删除文章

### 接口信息
- 路径：POST `/api/v1/cms/articles/batch-delete/`
- 说明：批量删除多篇文章

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| article_ids | array | 是 | 要删除的文章ID列表 |
| force | boolean | 否 | 是否强制删除，默认false |

### 请求体示例
```json
{
  "article_ids": [1, 2, 3],
  "force": false
}
```

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "文章批量删除成功",
  "data": {
    "requested_count": 3,
    "deleted_count": 3,
    "deleted_ids": [1, 2, 3]
  }
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/batch-delete/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [1, 2, 3],
    "force": false
  }'
```

---

## 10. 获取文章版本历史

### 接口信息
- 路径：GET `/api/v1/cms/articles/{id}/versions/`
- 说明：获取文章的所有历史版本

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": [
    {
      "id": 3,
      "version_number": 3,
      "title": "最新版本标题",
      "change_description": "更新了标题",
      "created_by": "admin",
      "created_at": "2024-01-20T15:00:00Z"
    },
    {
      "id": 2,
      "version_number": 2,
      "title": "第二版标题",
      "change_description": "添加了更多内容",
      "created_by": "admin",
      "created_at": "2024-01-18T10:00:00Z"
    },
    {
      "id": 1,
      "version_number": 1,
      "title": "初始版本标题",
      "change_description": "初始创建",
      "created_by": "admin",
      "created_at": "2024-01-15T08:00:00Z"
    }
  ]
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/1/versions/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 11. 获取特定版本内容

### 接口信息
- 路径：GET `/api/v1/cms/articles/{id}/versions/{version_number}/`
- 说明：获取文章的指定版本内容

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/1/versions/2/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 12. 获取文章统计数据

### 接口信息
- 路径：GET `/api/v1/cms/articles/{id}/statistics/`
- 说明：获取文章的详细统计数据

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| period | string | 否 | 统计周期（day/week/month/year/all） |
| start_date | string | 否 | 统计起始日期（YYYY-MM-DD） |
| end_date | string | 否 | 统计结束日期（YYYY-MM-DD） |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "basic_stats": {
      "views_count": 1000,
      "unique_views_count": 800,
      "likes_count": 50,
      "dislikes_count": 5,
      "comments_count": 20,
      "shares_count": 30,
      "bookmarks_count": 45,
      "avg_reading_time": 180,
      "bounce_rate": 0.25
    },
    "time_series": {
      "views": [
        {"date": "2024-01-15", "count": 50},
        {"date": "2024-01-16", "count": 80},
        {"date": "2024-01-17", "count": 120}
      ]
    },
    "demographics": {
      "countries": [
        {"name": "中国", "count": 500},
        {"name": "美国", "count": 200}
      ],
      "devices": [
        {"name": "Mobile", "count": 600},
        {"name": "Desktop", "count": 400}
      ],
      "browsers": [
        {"name": "Chrome", "count": 700},
        {"name": "Safari", "count": 200}
      ]
    },
    "referrers": [
      {"source": "直接访问", "count": 300},
      {"source": "Google", "count": 200}
    ]
  }
}
```

### curl 调用示例
```bash
# 获取全部统计
curl -X GET "http://localhost:8000/api/v1/cms/articles/1/statistics/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按周期筛选
curl -X GET "http://localhost:8000/api/v1/cms/articles/1/statistics/?period=month" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按日期范围
curl -X GET "http://localhost:8000/api/v1/cms/articles/1/statistics/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 13. 记录文章阅读

### 接口信息
- 路径：POST `/api/v1/cms/articles/{id}/view/`
- 说明：记录文章的阅读行为（无需认证）

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "阅读记录已保存",
  "data": null
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/1/view/"
```

---

## 文章状态说明

| 状态 | 说明 |
|------|------|
| draft | 草稿，仅作者和管理员可见 |
| pending | 待审核，等待管理员审核 |
| published | 已发布，对外公开可见 |
| archived | 已归档，不在前台展示 |

## 可见性说明

| 可见性 | 说明 |
|-------|------|
| public | 公开，所有人可见 |
| private | 私密，仅作者和管理员可见 |
| password | 密码保护，需输入密码访问 |

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
