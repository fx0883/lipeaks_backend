# CMS文章管理API概述

## 简介

CMS文章管理API提供了一套完整的RESTful接口，用于管理内容管理系统中的文章。这些API支持文章的创建、查询、更新、删除等基本操作，以及文章版本管理、统计数据、状态变更等高级功能。

## 基础URL

```
/api/v1/cms/articles/
```

## 认证与授权

所有API都需要JWT认证，请在请求头中包含以下字段：

```
Authorization: Bearer <your_token>
```

## 多租户支持

系统支持多租户架构，可以通过以下两种方式指定租户：

1. 在请求头中添加租户ID：
   ```
   X-Tenant-ID: <tenant_id>
   ```

2. 通过JWT令牌中包含的租户信息（推荐）

## API列表

### 基础操作

1. [获取文章列表](./article_list_api.md) - `GET /api/v1/cms/articles/`
2. [获取文章详情](./article_detail_api.md) - `GET /api/v1/cms/articles/{id}/`
3. [创建文章](./article_create_api.md) - `POST /api/v1/cms/articles/`
4. [更新文章](./article_update_api.md) - `PUT /api/v1/cms/articles/{id}/`
5. [部分更新文章](./article_partial_update_api.md) - `PATCH /api/v1/cms/articles/{id}/`
6. [删除文章](./article_delete_api.md) - `DELETE /api/v1/cms/articles/{id}/`
7. [批量删除文章](./batch_delete_articles.md) - `POST /api/v1/cms/articles/batch-delete/`

### 文章状态管理

1. [发布文章](./article_publish_api.md) - `POST /api/v1/cms/articles/{id}/publish/`
2. [取消发布文章](./article_unpublish_api.md) - `POST /api/v1/cms/articles/{id}/unpublish/`
3. [归档文章](./article_archive_api.md) - `POST /api/v1/cms/articles/{id}/archive/`

### 文章版本管理

1. [获取文章版本历史](./article_versions_api.md) - `GET /api/v1/cms/articles/{id}/versions/`
2. [获取特定版本的文章内容](./article_version_detail_api.md) - `GET /api/v1/cms/articles/{id}/versions/{version_number}/`

### 文章统计

1. [获取文章统计数据](./article_statistics_api.md) - `GET /api/v1/cms/articles/{id}/statistics/`
2. [记录文章阅读](./article_view_record_api.md) - `POST /api/v1/cms/articles/{id}/view/`

## 数据模型

### 文章(Article)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer | 文章ID |
| title | string | 文章标题 |
| slug | string | URL别名 |
| content | string | 文章内容 |
| content_type | string | 内容类型(markdown/html) |
| excerpt | string | 文章摘要 |
| author | integer | 作者ID |
| status | string | 状态(draft/pending/published/archived) |
| is_featured | boolean | 是否特色文章 |
| is_pinned | boolean | 是否置顶 |
| allow_comment | boolean | 是否允许评论 |
| visibility | string | 可见性(public/private/password) |
| password | string | 访问密码(当visibility=password时) |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
| published_at | datetime | 发布时间 |
| cover_image | string | 封面图片URL |
| template | string | 使用的模板 |
| sort_order | integer | 排序顺序 |
| tenant | integer | 所属租户ID |

## 错误处理

API使用标准HTTP状态码表示请求结果：

- 200: 成功
- 201: 创建成功
- 204: 删除成功
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器错误

错误响应格式：

```json
{
  "detail": "错误描述信息"
}
```

## 分页

列表API支持分页，使用以下查询参数：

- `page`: 页码，默认1
- `per_page`: 每页数量，默认10，最大50

分页响应格式：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 100,
      "next": "http://example.com/api/v1/cms/articles/?page=3",
      "previous": "http://example.com/api/v1/cms/articles/?page=1",
      "page_size": 10,
      "current_page": 2,
      "total_pages": 10
    },
    "results": [
      // 文章列表数据
    ]
  }
}
``` 