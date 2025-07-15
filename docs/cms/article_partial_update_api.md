# 部分更新文章API

## API 端点

```
PATCH /api/v1/cms/articles/{id}/
```

## 描述

更新现有文章的部分字段。

## 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | Bearer token认证 |
| Content-Type | string | 是 | application/json |
| X-Tenant-ID | string | 否 | 租户ID |

## 请求体

```json
{
  "status": "published",
  "is_featured": true,
  "publish_now": true
}
```

### 参数说明

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| title | string | 否 | 文章标题 |
| content | string | 否 | 文章内容 |
| content_type | string | 否 | 内容类型，可选值：markdown, html |
| excerpt | string | 否 | 文章摘要 |
| status | string | 否 | 文章状态，可选值：draft, pending, published, archived |
| is_featured | boolean | 否 | 是否特色文章 |
| is_pinned | boolean | 否 | 是否置顶 |
| allow_comment | boolean | 否 | 是否允许评论 |
| visibility | string | 否 | 可见性，可选值：public, private, password |
| password | string | 否 | 访问密码，当visibility=password时必填 |
| cover_image | string | 否 | 封面图片URL |
| template | string | 否 | 使用的模板 |
| sort_order | integer | 否 | 排序顺序 |
| category_ids | array | 否 | 分类ID列表 |
| tag_ids | array | 否 | 标签ID列表 |
| meta | object | 否 | 文章元数据 |
| create_new_version | boolean | 否 | 是否创建新版本，默认true |
| change_description | string | 否 | 版本变更说明 |
| publish_now | boolean | 否 | 是否立即发布，设置为true时会自动将status改为published并设置发布时间 |
| scheduled_publish_time | string | 否 | 计划发布时间，格式为ISO 8601 |

## 响应

### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 16,
    "title": "更新后的文章标题",
    "content": "更新后的文章内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要...",
    "status": "published",
    "is_featured": true,
    "is_pinned": false,
    "allow_comment": true,
    "visibility": "public",
    "password": null,
    "cover_image": null,
    "template": null,
    "sort_order": 0,
    "meta": {
      "id": 16,
      "article": 16,
      "seo_title": "SEO标题",
      "seo_description": "SEO描述",
      "seo_keywords": null,
      "og_title": null,
      "og_description": null,
      "og_image": null,
      "schema_markup": null,
      "canonical_url": null,
      "robots": null,
      "custom_meta": null,
      "created_at": "2025-06-22T21:38:17.019856+08:00",
      "updated_at": "2025-06-22T21:38:17.019868+08:00",
      "tenant": 17
    }
  }
}
```

### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 是否成功 |
| code | integer | 状态码 |
| message | string | 操作结果描述 |
| data | object | 返回数据 |
| data.id | integer | 文章ID |
| data.title | string | 文章标题 |
| data.content | string | 文章内容 |
| data.content_type | string | 内容类型 |
| data.excerpt | string | 文章摘要 |
| data.status | string | 文章状态 |
| data.is_featured | boolean | 是否特色文章 |
| data.is_pinned | boolean | 是否置顶 |
| data.allow_comment | boolean | 是否允许评论 |
| data.visibility | string | 可见性 |
| data.password | string | 访问密码 |
| data.cover_image | string | 封面图片URL |
| data.template | string | 使用的模板 |
| data.sort_order | integer | 排序顺序 |
| data.meta | object | 文章元数据 |

### 错误响应

#### 401 Unauthorized

```json
{
  "detail": "身份认证信息未提供。"
}
```

#### 403 Forbidden

```json
{
  "detail": "您没有执行此操作的权限。"
}
```

#### 404 Not Found

```json
{
  "detail": "未找到。"
}
```

## 示例

### cURL示例

```bash
curl -X 'PATCH' \
  'http://localhost:8000/api/v1/cms/articles/16/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{
  "status": "published",
  "is_featured": true,
  "publish_now": true
}'
```

### Python示例

```python
import requests

article_id = 16
url = f'http://localhost:8000/api/v1/cms/articles/{article_id}/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
}
data = {
    'status': 'published',
    'is_featured': True,
    'publish_now': True
}

response = requests.patch(url, headers=headers, json=data)
print(response.status_code)
print(response.json())
```

## 注意事项

1. PATCH方法用于更新文章的部分字段，不需要提供完整的文章数据
2. 如果设置publish_now=true，系统会自动将文章状态改为published并设置当前时间为发布时间
3. 如果只修改文章状态，推荐使用专门的状态变更API，如发布文章API、取消发布API或归档API
4. 默认情况下，更新文章会创建新的版本记录，如果不想创建新版本，可以设置create_new_version=false
5. 只有在文章内容、标题、摘要或内容类型有变化时才会创建新版本
6. 只有文章作者或管理员才能更新文章
7. 如果更改作者，需要管理员权限 