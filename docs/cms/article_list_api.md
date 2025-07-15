# 获取文章列表API

## API 端点

```
GET /api/v1/cms/articles/
```

## 描述

获取文章列表，支持分页、过滤和搜索。

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | Bearer token认证 |
| Content-Type | string | 是 | application/json |
| X-Tenant-ID | string | 否 | 租户ID |

## 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| per_page | integer | 否 | 每页数量，默认10，最大50 |
| status | string | 否 | 文章状态过滤(draft/pending/published/archived) |
| category_id | integer | 否 | 按分类ID过滤 |
| tag_id | integer | 否 | 按标签ID过滤 |
| author_id | integer | 否 | 按作者ID过滤 |
| search | string | 否 | 搜索关键词，在标题和内容中匹配 |
| sort | string | 否 | 排序字段，可选值：created_at, updated_at, published_at, title, views_count |
| sort_direction | string | 否 | 排序方向，可选值：asc, desc，默认desc |
| is_featured | boolean | 否 | 是否只返回特色文章 |
| is_pinned | boolean | 否 | 是否只返回置顶文章 |
| visibility | string | 否 | 可见性过滤，可选值：public, private, password |
| date_from | string | 否 | 发布日期起始，格式YYYY-MM-DD |
| date_to | string | 否 | 发布日期截止，格式YYYY-MM-DD |

## 响应

### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 14,
      "next": "http://localhost:8000/api/v1/cms/articles/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 2
    },
    "results": [
      {
        "id": 14,
        "title": "更新后的文章标题",
        "slug": "-4",
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
        "status": "archived",
        "is_featured": true,
        "is_pinned": false,
        "cover_image": null,
        "published_at": "2025-06-22T19:11:21.587812+08:00",
        "categories": [],
        "tags": [],
        "comments_count": 0,
        "likes_count": 0,
        "views_count": 4
      },
      {
        "id": 13,
        "title": "更新后的文章标题",
        "slug": "-3",
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
        "status": "archived",
        "is_featured": false,
        "is_pinned": false,
        "cover_image": null,
        "published_at": null,
        "categories": [
          {
            "id": 3,
            "name": "技术博客",
            "slug": "tech-blog"
          }
        ],
        "tags": [
          {
            "id": 3,
            "name": "Python",
            "slug": "python",
            "color": "#3776AB"
          }
        ],
        "comments_count": 0,
        "likes_count": 0,
        "views_count": 0
      }
      // ... 更多文章
    ]
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
| data.pagination | object | 分页信息 |
| data.pagination.count | integer | 总记录数 |
| data.pagination.next | string | 下一页URL |
| data.pagination.previous | string | 上一页URL |
| data.pagination.page_size | integer | 每页记录数 |
| data.pagination.current_page | integer | 当前页码 |
| data.pagination.total_pages | integer | 总页数 |
| data.results | array | 文章列表 |
| data.results[].id | integer | 文章ID |
| data.results[].title | string | 文章标题 |
| data.results[].slug | string | URL别名 |
| data.results[].excerpt | string | 文章摘要 |
| data.results[].author | integer | 作者ID |
| data.results[].author_info | object | 作者详细信息 |
| data.results[].status | string | 文章状态 |
| data.results[].is_featured | boolean | 是否特色文章 |
| data.results[].is_pinned | boolean | 是否置顶 |
| data.results[].cover_image | string | 封面图片URL |
| data.results[].published_at | string | 发布时间 |
| data.results[].categories | array | 文章分类列表 |
| data.results[].tags | array | 文章标签列表 |
| data.results[].comments_count | integer | 评论数 |
| data.results[].likes_count | integer | 点赞数 |
| data.results[].views_count | integer | 浏览数 |

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

## 示例

### cURL示例

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/cms/articles/?page=1&per_page=10&status=published&category_id=3&search=示例文章' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

### Python示例

```python
import requests

url = 'http://localhost:8000/api/v1/cms/articles/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
}
params = {
    'page': 1,
    'per_page': 10,
    'status': 'published',
    'category_id': 3,
    'search': '示例文章'
}

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.json())
```

## 注意事项

1. 该API支持多种过滤条件组合使用
2. 默认按发布时间倒序排列
3. 如果未指定状态过滤，将返回所有状态的文章
4. 对于非管理员用户，只能查看公开或自己创建的文章 