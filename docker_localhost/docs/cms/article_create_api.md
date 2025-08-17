# 创建文章API

## API 端点

```
POST /api/v1/cms/articles/
```

## 描述

创建新文章，需要提供标题和内容。

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | Bearer token认证 |
| Content-Type | string | 是 | application/json |
| X-Tenant-ID | string | 否 | 租户ID |

## 请求体

```json
{
  "title": "示例文章标题",
  "content": "文章详细内容...",
  "content_type": "markdown",
  "excerpt": "文章摘要...",
  "status": "draft",
  "category_ids": [4],
  "tag_ids": [3],
  "meta": {
    "seo_title": "SEO标题",
    "seo_description": "SEO描述"
  }
}
```

### 参数说明

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| title | string | 是 | 文章标题 |
| content | string | 是 | 文章内容 |
| content_type | string | 否 | 内容类型，可选值：markdown, html，默认markdown |
| excerpt | string | 否 | 文章摘要，如不提供将自动从内容中提取 |
| status | string | 否 | 文章状态，可选值：draft, pending, published, archived，默认draft |
| is_featured | boolean | 否 | 是否特色文章，默认false |
| is_pinned | boolean | 否 | 是否置顶，默认false |
| allow_comment | boolean | 否 | 是否允许评论，默认true |
| visibility | string | 否 | 可见性，可选值：public, private, password，默认public |
| password | string | 否 | 访问密码，当visibility=password时必填 |
| cover_image | string | 否 | 封面图片URL |
| template | string | 否 | 使用的模板 |
| sort_order | integer | 否 | 排序顺序，默认0 |
| category_ids | array | 否 | 分类ID列表 |
| tag_ids | array | 否 | 标签ID列表 |
| meta | object | 否 | 文章元数据 |
| meta.seo_title | string | 否 | SEO标题 |
| meta.seo_description | string | 否 | SEO描述 |
| meta.seo_keywords | string | 否 | SEO关键词 |
| meta.og_title | string | 否 | Open Graph标题 |
| meta.og_description | string | 否 | Open Graph描述 |
| meta.og_image | string | 否 | Open Graph图片URL |
| publish_now | boolean | 否 | 是否立即发布，设置为true时会自动将status改为published并设置发布时间 |
| scheduled_publish_time | string | 否 | 计划发布时间，格式为ISO 8601 |

## 响应

### 成功响应 (201 Created)

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 15,
    "title": "示例文章标题",
    "content": "文章详细内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要...",
    "status": "draft",
    "is_featured": false,
    "is_pinned": false,
    "allow_comment": true,
    "visibility": "public",
    "password": null,
    "cover_image": null,
    "template": null,
    "sort_order": 0,
    "meta": {
      "id": 15,
      "article": 15,
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
      "created_at": "2025-06-22T21:37:50.760355+08:00",
      "updated_at": "2025-06-22T21:37:50.760369+08:00",
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
| data.meta.id | integer | 元数据ID |
| data.meta.article | integer | 关联的文章ID |
| data.meta.seo_title | string | SEO标题 |
| data.meta.seo_description | string | SEO描述 |
| data.meta.seo_keywords | string | SEO关键词 |
| data.meta.og_title | string | Open Graph标题 |
| data.meta.og_description | string | Open Graph描述 |
| data.meta.og_image | string | Open Graph图片URL |
| data.meta.schema_markup | string | Schema标记 |
| data.meta.canonical_url | string | 规范URL |
| data.meta.robots | string | Robots指令 |
| data.meta.custom_meta | object | 自定义元数据 |
| data.meta.created_at | string | 创建时间 |
| data.meta.updated_at | string | 更新时间 |
| data.meta.tenant | integer | 所属租户ID |

### 错误响应

#### 400 Bad Request

```json
{
  "title": [
    "该字段是必填项。"
  ],
  "content": [
    "该字段是必填项。"
  ]
}
```

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

## 示例

### cURL示例

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/cms/articles/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{
  "title": "示例文章标题",
  "content": "文章详细内容...",
  "content_type": "markdown",
  "excerpt": "文章摘要...",
  "status": "draft",
  "category_ids": [4],
  "tag_ids": [3],
  "meta": {
    "seo_title": "SEO标题",
    "seo_description": "SEO描述"
  }
}'
```

### Python示例

```python
import requests

url = 'http://localhost:8000/api/v1/cms/articles/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
}
data = {
    'title': '示例文章标题',
    'content': '文章详细内容...',
    'content_type': 'markdown',
    'excerpt': '文章摘要...',
    'status': 'draft',
    'category_ids': [4],
    'tag_ids': [3],
    'meta': {
        'seo_title': 'SEO标题',
        'seo_description': 'SEO描述'
    }
}

response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.json())
```

## 注意事项

1. 创建文章时会自动创建初始版本（版本号为1）
2. 如果未提供摘要，系统会自动从内容中提取前200个字符作为摘要
3. 如果未提供slug，系统会自动根据标题生成
4. 作者默认为当前登录用户
5. 创建文章时会自动创建统计记录 