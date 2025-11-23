# CMS API 文档 - 文章管理

## 基础信息

- **基础URL**: `http://0.0.0.0:8000/api/v1/cms`
- **认证方式**: Bearer Token (JWT)
- **租户控制**:
  - **Admin用户**: 不需要`X-Tenant-ID`头，自动使用其关联的租户
  - **Member用户**: 必须提供`X-Tenant-ID`头
  - **匿名用户**: 必须提供`X-Tenant-ID`头

---

## 1. 获取文章列表

### 基本信息
- **端点**: `GET /articles/`
- **权限**: 公开（需租户ID）
- **分页**: 支持

### 请求头
```http
# 匿名/Member用户
X-Tenant-ID: 3

# Admin用户
Authorization: Bearer {admin_token}
```

### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认10 |
| status | string | 否 | 文章状态：draft, pending, published, archived |
| category_id | integer | 否 | 分类ID过滤 |
| tag_id | integer | 否 | 标签ID过滤 |
| author_id | integer | 否 | 作者ID过滤 |
| author_type | string | 否 | 作者类型：member, admin |
| search | string | 否 | 搜索关键词（标题、内容） |
| is_featured | boolean | 否 | 是否特色文章 |
| is_pinned | boolean | 否 | 是否置顶 |
| visibility | string | 否 | 可见性：public, private, password |
| date_from | string | 否 | 发布日期起始，格式YYYY-MM-DD |
| date_to | string | 否 | 发布日期截止，格式YYYY-MM-DD |
| sort | string | 否 | 排序字段：created_at, updated_at, published_at, title, views_count |
| sort_direction | string | 否 | 排序方向：asc, desc（默认desc） |

### curl示例

```bash
# 匿名用户获取文章列表
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/" \
  -H "X-Tenant-ID: 3"

# Admin用户获取文章列表
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer {admin_token}"

# Member用户获取文章列表（带过滤）
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/?status=published&page=1" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 100,
      "next": "http://0.0.0.0:8000/api/v1/cms/articles/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 10
    },
    "results": [
      {
        "id": 10285,
        "title": "示例文章标题",
        "slug": "example-article",
        "excerpt": "文章摘要",
        "author_info": {
          "id": 10,
          "username": "test02@qq.com",
          "email": "test02@qq.com",
          "nick_name": "测试用户",
          "avatar": "http://localhost:8000/media/avatars/xxx.jpg",
          "tenant": 3,
          "tenant_name": "填色"
        },
        "author_type": "member",
        "status": "draft",
        "is_featured": false,
        "is_pinned": false,
        "cover_image": "",
        "published_at": null,
        "created_at": "2025-11-23T11:55:55.319532Z",
        "updated_at": "2025-11-23T11:55:55.319540Z",
        "categories": [],
        "tags": [],
        "comments_count": 0,
        "likes_count": 0,
        "views_count": 0
      }
    ]
  }
}
```

---

## 2. 创建文章

### 基本信息
- **端点**: `POST /articles/`
- **权限**: 需要认证（Admin或Member）
- **Content-Type**: `application/json`

### 请求头
```http
# Admin用户
Authorization: Bearer {admin_token}

# Member用户
Authorization: Bearer {member_token}
X-Tenant-ID: 3
```

### 请求体
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 文章标题 |
| content | string | 是 | 文章内容 |
| excerpt | string | 否 | 文章摘要 |
| content_type | string | 否 | 内容类型：markdown, html, rich_text（默认markdown） |
| status | string | 否 | 文章状态：draft（默认）, pending, published, archived |
| visibility | string | 否 | 可见性：public（默认）, private, password |
| password | string | 否 | 访问密码（visibility=password时） |
| slug | string | 否 | URL别名（自动生成） |
| cover_image | string | 否 | 封面图片URL |
| is_featured | boolean | 否 | 是否特色文章（默认false） |
| is_pinned | boolean | 否 | 是否置顶（默认false） |
| allow_comment | boolean | 否 | 是否允许评论（默认true） |
| category_ids | array | 否 | 分类ID数组 |
| tag_ids | array | 否 | 标签ID数组 |
| parent | integer | 否 | 父文章ID |
| meta | object | 否 | 元数据（SEO等） |
| template | string | 否 | 模板名称 |

### curl示例

```bash
# Admin创建文章
curl -X POST "http://0.0.0.0:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的第一篇文章",
    "content": "这是文章内容...",
    "excerpt": "文章摘要",
    "status": "draft",
    "content_type": "markdown",
    "category_ids": [1, 2],
    "tag_ids": [3, 4, 5],
    "meta": {
      "seo_title": "SEO标题",
      "seo_description": "SEO描述"
    }
  }'

# Member创建文章
curl -X POST "http://0.0.0.0:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Member的文章",
    "content": "文章内容...",
    "excerpt": "摘要",
    "status": "draft"
  }'
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 10299,
    "title": "我的第一篇文章",
    "slug": "my-first-article",
    "content": "这是文章内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要",
    "status": "draft",
    "visibility": "public",
    "is_featured": false,
    "is_pinned": false,
    "allow_comment": true,
    "cover_image": null,
    "published_at": null,
    "created_at": "2025-11-23T12:00:00.000000Z",
    "updated_at": "2025-11-23T12:00:00.000000Z",
    "author_info": {
      "id": 3,
      "username": "admin_cms",
      "email": "jackfeng8123@gmail.com"
    },
    "categories": [],
    "tags": []
  }
}
```

---

## 3. 获取单篇文章

### 基本信息
- **端点**: `GET /articles/{id}/`
- **权限**: 公开（需租户ID）

### 路径参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 文章ID |

### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| password | string | 否 | 访问密码（visibility=password时） |
| version | integer | 否 | 版本号（查看历史版本） |

### curl示例

```bash
# 匿名用户获取文章
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/10299/" \
  -H "X-Tenant-ID: 3"

# 获取需要密码的文章
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/10299/?password=123456" \
  -H "X-Tenant-ID: 3"

# 获取特定版本
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/10299/?version=2" \
  -H "X-Tenant-ID: 3"
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 10299,
    "title": "我的第一篇文章",
    "slug": "my-first-article",
    "content": "这是文章内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要",
    "status": "published",
    "visibility": "public",
    "is_featured": false,
    "is_pinned": false,
    "allow_comment": true,
    "cover_image": null,
    "published_at": "2025-11-23T12:00:00.000000Z",
    "created_at": "2025-11-23T12:00:00.000000Z",
    "updated_at": "2025-11-23T12:05:00.000000Z",
    "author_info": {
      "id": 3,
      "username": "admin_cms",
      "email": "jackfeng8123@gmail.com",
      "nick_name": "",
      "avatar": "",
      "tenant": 3,
      "tenant_name": "填色"
    },
    "author_type": "admin",
    "categories": [
      {
        "id": 1,
        "name": "技术博客",
        "slug": "tech-blog"
      }
    ],
    "tags": [
      {
        "id": 3,
        "name": "Python",
        "slug": "python"
      }
    ],
    "comments_count": 5,
    "likes_count": 10,
    "views_count": 100,
    "parent": null,
    "children_count": 0
  }
}
```

---

## 4. 更新文章

### 基本信息
- **端点**: 
  - `PUT /articles/{id}/` - 完整更新
  - `PATCH /articles/{id}/` - 部分更新
- **权限**: 需要认证且为作者或管理员

### 请求头
```http
# Admin用户
Authorization: Bearer {admin_token}

# Member用户
Authorization: Bearer {member_token}
X-Tenant-ID: 3
```

### 请求体
与创建文章相同，但所有字段都是可选的（PATCH方法）。

PUT方法需要提供所有必填字段。

额外字段：
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| create_new_version | boolean | 否 | 是否创建新版本（默认false） |
| change_description | string | 否 | 更改说明（创建新版本时） |

### curl示例

```bash
# Admin完整更新文章 (PUT)
curl -X PUT "http://0.0.0.0:8000/api/v1/cms/articles/10299/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的文章标题",
    "content": "更新后的内容...",
    "excerpt": "更新摘要",
    "status": "published",
    "create_new_version": true,
    "change_description": "更新了文章内容和标题"
  }'

# Admin部分更新文章 (PATCH)
curl -X PATCH "http://0.0.0.0:8000/api/v1/cms/articles/10299/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "只更新标题",
    "is_featured": true
  }'

# Member更新自己的文章
curl -X PATCH "http://0.0.0.0:8000/api/v1/cms/articles/10299/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "更新内容"
  }'
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 10299,
    "title": "更新后的文章标题",
    "content": "更新后的内容...",
    "updated_at": "2025-11-23T12:10:00.000000Z",
    ...
  }
}
```

---

## 5. 删除文章

### 基本信息
- **端点**: `DELETE /articles/{id}/`
- **权限**: 需要认证且为作者或管理员

### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| force | boolean | 否 | 是否强制删除（默认软删除） |

### curl示例

```bash
# Admin软删除文章
curl -X DELETE "http://0.0.0.0:8000/api/v1/cms/articles/10299/" \
  -H "Authorization: Bearer {admin_token}"

# Admin强制删除文章
curl -X DELETE "http://0.0.0.0:8000/api/v1/cms/articles/10299/?force=true" \
  -H "Authorization: Bearer {admin_token}"

# Member删除自己的文章
curl -X DELETE "http://0.0.0.0:8000/api/v1/cms/articles/10299/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": null
}
```

HTTP Status: 204 No Content

---

## 6. 发布文章

### 基本信息
- **端点**: `POST /articles/{id}/publish/`
- **权限**: 需要认证且为作者或管理员

### curl示例

```bash
# Admin发布文章
curl -X POST "http://0.0.0.0:8000/api/v1/cms/articles/10299/publish/" \
  -H "Authorization: Bearer {admin_token}"

# Member发布自己的文章
curl -X POST "http://0.0.0.0:8000/api/v1/cms/articles/10299/publish/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "文章已发布",
  "data": {
    "id": 10299,
    "status": "published",
    "published_at": "2025-11-23T12:15:00.000000Z"
  }
}
```

---

## 7. 取消发布文章

### 基本信息
- **端点**: `POST /articles/{id}/unpublish/`
- **权限**: 需要认证且为作者或管理员

### curl示例

```bash
# Admin取消发布文章
curl -X POST "http://0.0.0.0:8000/api/v1/cms/articles/10299/unpublish/" \
  -H "Authorization: Bearer {admin_token}"
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "文章已取消发布",
  "data": {
    "id": 10299,
    "status": "draft",
    "published_at": null
  }
}
```

---

## 8. 归档文章

### 基本信息
- **端点**: `POST /articles/{id}/archive/`
- **权限**: 需要认证且为作者或管理员

### curl示例

```bash
# Admin归档文章
curl -X POST "http://0.0.0.0:8000/api/v1/cms/articles/10299/archive/" \
  -H "Authorization: Bearer {admin_token}"
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "文章已归档",
  "data": {
    "id": 10299,
    "status": "archived"
  }
}
```

---

## 9. 获取文章统计

### 基本信息
- **端点**: `GET /articles/{id}/statistics/`
- **权限**: 需要认证

### curl示例

```bash
# Admin获取文章统计
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/10299/statistics/" \
  -H "Authorization: Bearer {admin_token}"

# Member获取文章统计
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/10299/statistics/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "views_count": 100,
    "likes_count": 10,
    "favorites_count": 5,
    "comments_count": 8,
    "shares_count": 3
  }
}
```

---

## 10. 记录文章阅读

### 基本信息
- **端点**: `POST /articles/{id}/view/`
- **权限**: 公开（需租户ID）

### curl示例

```bash
# 记录文章阅读（匿名）
curl -X POST "http://0.0.0.0:8000/api/v1/cms/articles/10299/view/" \
  -H "X-Tenant-ID: 3"

# 记录文章阅读（已登录）
curl -X POST "http://0.0.0.0:8000/api/v1/cms/articles/10299/view/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "阅读记录已保存",
  "data": {
    "views_count": 101
  }
}
```

---

## 11. 获取文章版本历史

### 基本信息
- **端点**: `GET /articles/{id}/versions/`
- **权限**: 需要认证且为作者或管理员

### curl示例

```bash
# Admin获取版本历史
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/10299/versions/" \
  -H "Authorization: Bearer {admin_token}"
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "version_number": 2,
      "title": "更新后的文章标题",
      "change_description": "更新了文章内容和标题",
      "created_at": "2025-11-23T12:10:00.000000Z",
      "created_by": {
        "id": 3,
        "username": "admin_cms"
      }
    },
    {
      "version_number": 1,
      "title": "我的第一篇文章",
      "change_description": "初始版本",
      "created_at": "2025-11-23T12:00:00.000000Z",
      "created_by": {
        "id": 3,
        "username": "admin_cms"
      }
    }
  ]
}
```

---

## 12. 获取特定版本的文章内容

### 基本信息
- **端点**: `GET /articles/{id}/versions/{version_number}/`
- **权限**: 需要认证且为作者或管理员

### 路径参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 文章ID |
| version_number | integer | 是 | 版本号 |

### curl示例

```bash
# Admin获取特定版本
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/10299/versions/1/" \
  -H "Authorization: Bearer {admin_token}"
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "version_number": 1,
    "title": "我的第一篇文章",
    "content": "这是文章内容...",
    "excerpt": "文章摘要",
    "change_description": "初始版本",
    "created_at": "2025-11-23T12:00:00.000000Z"
  }
}
```

---

## 13. 批量删除文章

### 基本信息
- **端点**: `POST /articles/batch-delete/`
- **权限**: 需要Admin权限

### 请求体
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| article_ids | array | 是 | 要删除的文章ID数组 |
| force | boolean | 否 | 是否强制删除（默认软删除） |

### curl示例

```bash
# Admin批量删除文章
curl -X POST "http://0.0.0.0:8000/api/v1/cms/articles/batch-delete/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [10299, 10300, 10301],
    "force": false
  }'
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "批量删除成功",
  "data": {
    "deleted_count": 3,
    "failed_ids": []
  }
}
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 4000 | 数据验证失败 |
| 4001 | 未认证或Token无效 |
| 4003 | 权限不足 |
| 4004 | 未找到资源 |
| 4100 | 租户操作失败 |
| 5000 | 服务器内部错误 |
