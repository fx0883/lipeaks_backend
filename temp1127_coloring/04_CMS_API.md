# Lipeaks Coloring - CMS API 文档

> 内容管理系统API，包括分类、文章、标签、评论管理
> 基础URL: `http://localhost:8000`
> 通用Headers:
> - `Authorization: Bearer {token}` (部分接口需要)
> - `X-Tenant-ID: {租户ID}` (必须)

---

## 一、分类管理 (7个接口)

### 1. 获取分类列表

**接口**: `GET /api/v1/cms/categories/`

**描述**: 获取分类列表，支持多种过滤条件

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| application | integer | 否 | 应用ID (如: 6) |
| parent | integer | 否 | 父分类ID |
| is_active | boolean | 否 | 是否激活 |
| is_pinned | boolean | 否 | 是否置顶 |
| search | string | 否 | 搜索关键词 |
| ordering | string | 否 | 排序字段 |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/categories/?application=6&is_active=true" \
  -H "X-Tenant-ID: 3"
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 41,
      "slug": "category-100",
      "parent": null,
      "cover_image": "http://localhost:8000/media/uploads/xxx.jpg",
      "created_at": "2025-10-26T06:05:30.616703Z",
      "updated_at": "2025-11-27T03:18:16.261694Z",
      "sort_order": 0,
      "tenant": 3,
      "application": 6,
      "application_name": "填色花园",
      "is_active": true,
      "is_pinned": true,
      "translations": {
        "zh-hans": {"name": "分类名", "description": "描述"},
        "en": {"name": "Category Name", "description": "..."}
      },
      "name": "分类名",
      "description": "分类描述"
    }
  ]
}
```

---

### 2. 获取分类详情

**接口**: `GET /api/v1/cms/categories/{id}/`

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/categories/41/" \
  -H "X-Tenant-ID: 3"
```

---

### 3. 创建分类

**接口**: `POST /api/v1/cms/categories/`

**权限**: 需要管理员权限

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 分类名称 |
| slug | string | 否 | URL别名（自动生成） |
| description | string | 否 | 描述 |
| parent | integer | 否 | 父分类ID |
| application | integer | 是 | 应用ID |
| is_active | boolean | 否 | 是否激活，默认true |
| is_pinned | boolean | 否 | 是否置顶 |
| cover_image | string | 否 | 封面图URL |

---

### 4. 更新分类 (PUT)

**接口**: `PUT /api/v1/cms/categories/{id}/`

**权限**: 需要管理员权限

---

### 5. 部分更新分类 (PATCH)

**接口**: `PATCH /api/v1/cms/categories/{id}/`

**权限**: 需要管理员权限

---

### 6. 删除分类

**接口**: `DELETE /api/v1/cms/categories/{id}/`

**权限**: 需要管理员权限

---

### 7. 获取分类树

**接口**: `GET /api/v1/cms/categories/tree/`

**描述**: 获取分类的树形结构

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| application | integer | 否 | 应用ID |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/categories/tree/?application=6" \
  -H "X-Tenant-ID: 3"
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 41,
      "name": "分类1",
      "slug": "category-1",
      "description": "...",
      "is_active": true,
      "sort_order": 0,
      "children": [
        {
          "id": 42,
          "name": "子分类1",
          "children": []
        }
      ]
    }
  ]
}
```

---

## 二、文章管理 (8个接口)

### 1. 获取文章列表

**接口**: `GET /api/v1/cms/articles/`

**描述**: 获取文章列表，支持丰富的过滤条件

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |
| application | integer | 否 | 应用ID |
| id | integer | 否 | 文章ID |
| status | string | 否 | 状态 (draft/published/archived) |
| category_id | integer | 否 | 分类ID |
| tag_id | integer | 否 | 标签ID |
| author_id | integer | 否 | 作者ID |
| search | string | 否 | 搜索关键词 |
| sort | string | 否 | 排序 (created_at/-created_at等) |
| is_featured | boolean | 否 | 是否精选 |
| is_pinned | boolean | 否 | 是否置顶 |
| parent_id | integer | 否 | 父文章ID |
| has_parent | boolean | 否 | 是否有父文章 |
| content_type | string | 否 | 内容类型 |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/?page=1&page_size=10&application=6" \
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
    "pagination": {
      "count": 100,
      "next": "http://localhost:8000/api/v1/cms/articles/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 10
    },
    "results": [
      {
        "id": 10326,
        "title": "文章标题",
        "slug": "article-slug",
        "excerpt": "文章摘要",
        "author_info": {
          "id": 12,
          "username": "7548155",
          "nick_name": "Whahaha",
          "avatar": "..."
        },
        "author_type": "member",
        "status": "published",
        "is_featured": false,
        "is_pinned": false,
        "cover_image": "http://localhost:8000/media/uploads/xxx.jpg",
        "cover_image_small": "http://localhost:8000/media/uploads/xxx_small.jpg",
        "published_at": null,
        "created_at": "2025-11-26T14:30:47.060826Z",
        "updated_at": "2025-11-26T14:30:47.060860Z",
        "categories": [
          {"id": 10, "name": "Category 60", "slug": "category-60"}
        ],
        "tags": [],
        "comments_count": 3,
        "likes_count": 2,
        "views_count": 0,
        "parent": 754,
        "parent_info": {"id": 754, "title": "父文章", "slug": "parent"},
        "children_count": 0
      }
    ]
  }
}
```

---

### 2. 获取文章详情

**接口**: `GET /api/v1/cms/articles/{id}/`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| password | string | 否 | 文章密码（如有） |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/10326/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 3. 创建文章

**接口**: `POST /api/v1/cms/articles/`

**权限**: 需要管理员权限

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 文章标题 |
| slug | string | 否 | URL别名 |
| content | string | 否 | 文章内容 |
| excerpt | string | 否 | 摘要 |
| categories | array | 否 | 分类ID数组 |
| tags | array | 否 | 标签ID数组 |
| application | integer | 是 | 应用ID |
| status | string | 否 | 状态 (draft/published) |
| cover_image | string | 否 | 封面图URL |
| parent | integer | 否 | 父文章ID |

---

### 4-5. 更新文章 (PUT/PATCH)

**接口**: `PUT/PATCH /api/v1/cms/articles/{id}/`

---

### 6. 删除文章

**接口**: `DELETE /api/v1/cms/articles/{id}/`

---

### 7. 发布文章

**接口**: `POST /api/v1/cms/articles/{id}/publish/`

**描述**: 将草稿状态的文章发布

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10326/publish/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 8. 记录文章阅读

**接口**: `POST /api/v1/cms/articles/{id}/record-view/`

**描述**: 记录一次文章浏览，增加views_count

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10326/record-view/" \
  -H "X-Tenant-ID: 3"
```

---

## 三、标签组管理 (6个接口)

### 1. 获取标签组列表

**接口**: `GET /api/v1/cms/tag-groups/`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_active | boolean | 否 | 是否激活 |
| search | string | 否 | 搜索关键词 |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "pagination": {...},
    "results": [
      {
        "id": 5,
        "name": "Test Group",
        "slug": "test-group",
        "description": null,
        "created_at": "2025-11-23T12:46:51.010862Z",
        "updated_at": "2025-11-23T13:01:32.073382Z",
        "is_active": true,
        "tenant": 3
      }
    ]
  }
}
```

---

### 2-6. 标签组 CRUD

- `GET /api/v1/cms/tag-groups/{id}/` - 获取详情
- `POST /api/v1/cms/tag-groups/` - 创建
- `PUT /api/v1/cms/tag-groups/{id}/` - 更新
- `PATCH /api/v1/cms/tag-groups/{id}/` - 部分更新
- `DELETE /api/v1/cms/tag-groups/{id}/` - 删除

---

## 四、标签管理 (7个接口)

### 1. 获取标签列表

**接口**: `GET /api/v1/cms/tags/`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| group | integer | 否 | 标签组ID |
| is_active | boolean | 否 | 是否激活 |
| search | string | 否 | 搜索关键词 |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tags/?is_active=true" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 2-6. 标签 CRUD

同标签组接口格式

---

### 7. 获取标签使用统计

**接口**: `GET /api/v1/cms/tags/usage-stats/`

**描述**: 获取标签的使用次数统计

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tags/usage-stats/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

## 五、评论管理 (11个接口)

### 1. 获取评论列表

**接口**: `GET /api/v1/cms/comments/`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码 |
| article | integer | 否 | 文章ID |
| parent | integer | 否 | 父评论ID |
| user | integer | 否 | 用户ID |
| status | string | 否 | 状态 (pending/approved/rejected/spam) |
| has_parent | boolean | 否 | 是否有父评论 |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/?article=10326" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "pagination": {...},
    "results": [
      {
        "id": 116,
        "article": 10326,
        "parent": null,
        "user": null,
        "member": 10,
        "author_info": {
          "id": 10,
          "username": "test02@qq.com",
          "nick_name": "Nihao",
          "avatar": "..."
        },
        "author_type": "member",
        "guest_name": null,
        "guest_email": null,
        "content": "评论内容",
        "status": "approved",
        "ip_address": "192.168.1.14",
        "user_agent": "...",
        "created_at": "2025-11-27T06:52:32.461738Z",
        "is_pinned": false,
        "likes_count": 0,
        "tenant": 3,
        "replies_count": 0
      }
    ]
  }
}
```

---

### 2. 获取评论详情

**接口**: `GET /api/v1/cms/comments/{id}/`

---

### 3. 创建评论

**接口**: `POST /api/v1/cms/comments/`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| article | integer | 是 | 文章ID |
| content | string | 是 | 评论内容 |
| parent | integer | 否 | 父评论ID（回复用） |

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "article": 10326,
    "content": "这是一条评论"
  }'
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 117,
    "article": 10326,
    "parent": null,
    "member": 12,
    "author_info": {...},
    "author_type": "member",
    "content": "这是一条评论",
    "status": "approved",
    "created_at": "2025-11-27T11:34:34.091060Z",
    ...
  }
}
```

---

### 4-6. 评论 更新/删除

- `PUT /api/v1/cms/comments/{id}/`
- `PATCH /api/v1/cms/comments/{id}/`
- `DELETE /api/v1/cms/comments/{id}/`

---

### 7. 获取评论的回复

**接口**: `GET /api/v1/cms/comments/{id}/replies/`

**描述**: 获取指定评论的所有回复

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/116/replies/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 8-10. 评论审核 (管理员)

- `POST /api/v1/cms/comments/{id}/approve/` - 批准评论
- `POST /api/v1/cms/comments/{id}/reject/` - 拒绝评论
- `POST /api/v1/cms/comments/{id}/mark-spam/` - 标记为垃圾评论

---

### 11. 批量处理评论 (管理员)

**接口**: `POST /api/v1/cms/comments/batch/`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | array | 是 | 评论ID数组 |
| action | string | 是 | 操作 (approve/reject/delete/mark_spam) |

---

## 六、Member文章管理 (5个接口)

> 专为Member用户设计的文章管理接口

### 1. 获取我的文章列表

**接口**: `GET /api/v1/cms/member/articles/`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码 |
| status | string | 否 | 状态 |
| content_type | string | 否 | 内容类型 |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/member/articles/?page=1" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 2. 获取我的文章详情

**接口**: `GET /api/v1/cms/member/articles/{id}/`

---

### 3. 创建Member文章

**接口**: `POST /api/v1/cms/member/articles/`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 标题 |
| content | string | 否 | 内容 |
| excerpt | string | 否 | 摘要 |
| categories | array | 否 | 分类ID数组 |
| cover_image | string | 否 | 封面图URL |
| parent | integer | 否 | 父文章ID |

---

### 4. 删除我的文章

**接口**: `DELETE /api/v1/cms/member/articles/{id}/`

---

### 5. 发布我的文章

**接口**: `POST /api/v1/cms/member/articles/{id}/publish/`

---

## 错误响应说明

| code | message | 说明 |
|------|---------|------|
| 4000 | 数据验证失败 | 请求参数错误 |
| 4001 | 缺少租户ID | 需要X-Tenant-ID Header |
| 4003 | 权限不足 | 无权操作 |
| 4004 | Not Found | 记录不存在 |
| 5000 | 服务器内部错误 | 服务端异常 |
