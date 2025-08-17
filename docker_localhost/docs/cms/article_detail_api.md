# 获取文章详情API

## API 端点

```
GET /api/v1/cms/articles/{id}/
```

## 描述

通过ID获取单篇文章的详细信息。

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

## 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| password | string | 否 | 访问密码，当文章可见性为password时需提供 |
| version | integer | 否 | 文章版本号，默认返回最新版本 |

## 响应

### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 16,
    "title": "示例文章133标题",
    "slug": "133",
    "content": "文章详细3内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要...",
    "author": 34,
    "author_info": {
      "id": 34,
      "username": "admin_cms",
      "email": "fx0883@qq.com",
      "phone": "",
      "nick_name": "",
      "first_name": "",
      "last_name": "",
      "is_active": true,
      "avatar": "",
      "tenant": 17,
      "tenant_name": "cms_espressox",
      "is_admin": true,
      "is_member": false,
      "is_super_admin": false,
      "role": "租户管理员",
      "date_joined": "2025-06-21T10:57:45.571973+08:00"
    },
    "status": "draft",
    "is_featured": false,
    "is_pinned": false,
    "allow_comment": true,
    "visibility": "public",
    "password": null,
    "created_at": "2025-06-22T21:38:17.003389+08:00",
    "updated_at": "2025-06-22T21:38:17.003402+08:00",
    "published_at": null,
    "cover_image": null,
    "template": null,
    "sort_order": 0,
    "tenant": 17,
    "tenant_info": {
      "id": 17,
      "quota": {
        "id": 29,
        "usage_percentage": {
          "users": 10,
          "admins": 50,
          "storage": 0,
          "products": 0
        },
        "max_users": 10,
        "max_admins": 2,
        "max_storage_mb": 1024,
        "max_products": 100,
        "current_storage_used_mb": 0,
        "created_at": "2025-06-21T10:56:47.501163+08:00",
        "updated_at": "2025-06-21T10:56:47.501171+08:00"
      },
      "status_display": "活跃",
      "has_business_info": false,
      "name": "cms_espressox",
      "code": "cms_espressox",
      "status": "active",
      "contact_name": "Feng",
      "contact_email": "fx0883@qq.com",
      "contact_phone": "13397159629",
      "created_at": "2025-06-21T10:56:47.500085+08:00",
      "updated_at": "2025-06-21T10:56:47.500100+08:00",
      "is_deleted": false
    },
    "categories": [
      {
        "id": 4,
        "name": "技术博客22111",
        "slug": "tech-blo111g22"
      }
    ],
    "tags": [
      {
        "id": 3,
        "name": "P231yth1on",
        "slug": "pyt123h1on",
        "color": "#3776AB"
      }
    ],
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
    },
    "stats": {
      "id": 25,
      "article": 16,
      "views_count": 0,
      "unique_views_count": 0,
      "likes_count": 0,
      "dislikes_count": 0,
      "comments_count": 0,
      "shares_count": 0,
      "bookmarks_count": 0,
      "avg_reading_time": 0,
      "bounce_rate": "0.00",
      "last_updated_at": "2025-06-22T21:38:17.018402+08:00",
      "tenant": 17
    },
    "version_info": {
      "current_version": 1,
      "last_updated_by": {
        "id": 34,
        "username": "admin_cms",
        "email": "fx0883@qq.com",
        "phone": "",
        "nick_name": "",
        "first_name": "",
        "last_name": "",
        "is_active": true,
        "avatar": "",
        "tenant": 17,
        "tenant_name": "cms_espressox",
        "is_admin": true,
        "is_member": false,
        "is_super_admin": false,
        "role": "租户管理员",
        "date_joined": "2025-06-21T10:57:45.571973+08:00"
      },
      "last_updated_at": "2025-06-22T13:38:17.023867Z"
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
| data.slug | string | URL别名 |
| data.content | string | 文章内容 |
| data.content_type | string | 内容类型 |
| data.excerpt | string | 文章摘要 |
| data.author | integer | 作者ID |
| data.author_info | object | 作者详细信息 |
| data.status | string | 文章状态 |
| data.is_featured | boolean | 是否特色文章 |
| data.is_pinned | boolean | 是否置顶 |
| data.allow_comment | boolean | 是否允许评论 |
| data.visibility | string | 可见性 |
| data.password | string | 访问密码 |
| data.created_at | string | 创建时间 |
| data.updated_at | string | 更新时间 |
| data.published_at | string | 发布时间 |
| data.cover_image | string | 封面图片URL |
| data.template | string | 使用的模板 |
| data.sort_order | integer | 排序顺序 |
| data.tenant | integer | 所属租户ID |
| data.tenant_info | object | 租户详细信息 |
| data.categories | array | 文章分类列表 |
| data.tags | array | 文章标签列表 |
| data.meta | object | 文章元数据 |
| data.stats | object | 文章统计数据 |
| data.version_info | object | 文章版本信息 |

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

#### 400 Bad Request (密码保护的文章未提供密码)

```json
{
  "detail": "此文章需要密码访问。"
}
```

#### 400 Bad Request (密码错误)

```json
{
  "detail": "密码错误。"
}
```

## 示例

### cURL示例

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/cms/articles/16/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
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
params = {
    'version': 1  # 可选，获取特定版本的文章
}

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.json())
```

## 注意事项

1. 如果文章设置了密码保护，需要在查询参数中提供正确的密码才能访问
2. 可以通过version参数获取特定版本的文章内容
3. 对于非管理员用户，只能查看公开或自己创建的文章
4. 文章详情API会返回完整的文章信息，包括内容、分类、标签、统计数据和版本信息 