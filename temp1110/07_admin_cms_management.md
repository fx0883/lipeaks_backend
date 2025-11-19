# 7. 管理员 CMS 管理 API 集成指南

## 🎯 概述

管理员CMS管理API提供完整的后台内容管理系统，支持管理员对所有租户内文章、分类、标签、评论等内容进行全面管理。所有操作都基于严格的权限控制和租户隔离。

## 📋 API 列表

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| [获取文章列表](#获取文章列表) | GET | `/cms/articles/` | 获取所有文章列表（支持分页、筛选、搜索） |
| [获取单篇文章](#获取单篇文章) | GET | `/cms/articles/{id}/` | 获取文章详情 |
| [创建文章](#创建文章) | POST | `/cms/articles/` | 创建新文章 |
| [更新文章](#更新文章) | PUT/PATCH | `/cms/articles/{id}/` | 更新文章内容 |
| [删除文章](#删除文章) | DELETE | `/cms/articles/{id}/` | 删除文章（硬删除） |
| [发布文章](#发布文章) | POST | `/cms/articles/{id}/publish/` | 发布草稿文章 |
| [取消发布](#取消发布) | POST | `/cms/articles/{id}/unpublish/` | 取消发布文章 |
| [归档文章](#归档文章) | POST | `/cms/articles/{id}/archive/` | 归档文章 |
| [获取文章统计](#获取文章统计) | GET | `/cms/articles/{id}/statistics/` | 获取文章统计信息 |
| [获取版本历史](#获取版本历史) | GET | `/cms/articles/{id}/versions/` | 获取文章版本历史 |
| [批量删除文章](#批量删除文章) | POST | `/cms/articles/batch-delete/` | 批量删除文章 |

---

## 获取文章列表

### 接口信息
- **接口地址**: `GET /api/v1/cms/articles/`
- **权限要求**: 需要管理员认证（Admin用户）
- **功能说明**: 获取当前租户内的所有文章列表，支持分页、筛选和搜索

### 请求头
```bash
Authorization: Bearer {access_token}
Content-Type: application/json
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|----------|
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |
| status | string | 否 | 按状态筛选 | "published" | draft/pending/published/archived |
| content_type | string | 否 | 按内容类型筛选 | "image_upload" | markdown/html/image/image_upload/video/audio/file/link/quote/code/table/list |
| visibility | string | 否 | 按可见性筛选 | "public" | public/private/password |
| is_featured | boolean | 否 | 是否特色文章 | true | true/false |
| is_pinned | boolean | 否 | 是否置顶文章 | true | true/false |
| category_id | integer | 否 | 按分类筛选 | 1 | 有效的分类ID |
| tag_id | integer | 否 | 按标签筛选 | 1 | 有效的标签ID |
| user_id | integer | 否 | 按管理员作者筛选 | 1 | 有效的User ID |
| member_id | integer | 否 | 按Member作者筛选 | 1 | 有效的Member ID |
| author_type | string | 否 | 按作者类型筛选 | "member" | member/admin |
| author_id | integer | 否 | 按作者筛选（兼容参数） | 1 | User或Member的ID |
| parent_id | integer | 否 | 按父文章筛选 | 1 | 有效的文章ID |
| has_parent | string | 否 | 是否有父文章 | "true" | true/false |
| date_from | string | 否 | 发布时间起始日期 | "2024-01-01" | YYYY-MM-DD格式 |
| date_to | string | 否 | 发布时间结束日期 | "2024-12-31" | YYYY-MM-DD格式 |
| search | string | 否 | 搜索关键词（标题和内容） | "Vue教程" | 最长100字符 |
| sort | string | 否 | 排序字段 | "created_at" | created_at/updated_at/published_at/title/views_count |
| sort_direction | string | 否 | 排序方向 | "desc" | asc/desc |

### 使用示例

#### cURL 命令 - 获取已发布文章
```bash
curl -X GET "https://your-domain.com/api/v1/cms/articles/?status=published&page=1&page_size=10" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

#### cURL 命令 - 按内容类型筛选图片上传文章
```bash
curl -X GET "https://your-domain.com/api/v1/cms/articles/?content_type=image_upload&status=published" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

#### cURL 命令 - 按作者类型筛选Member文章
```bash
curl -X GET "https://your-domain.com/api/v1/cms/articles/?author_type=member&status=published" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

#### cURL 命令 - 筛选管理员发布的文章
```bash
curl -X GET "https://your-domain.com/api/v1/cms/articles/?author_type=admin&status=published" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

#### cURL 命令 - 搜索和排序
```bash
curl -X GET "https://your-domain.com/api/v1/cms/articles/?search=教程&sort=views_count&sort_direction=desc" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

#### JavaScript 获取文章列表
```javascript
const getAdminArticles = async (params = {}) => {
  const queryParams = new URLSearchParams({
    page: params.page || 1,
    page_size: params.pageSize || 20,
    status: params.status || '',
    content_type: params.contentType || '',
    author_type: params.authorType || '',  // 'member' 或 'admin'
    search: params.search || '',
    sort: params.sort || 'created_at',
    sort_direction: params.sortDirection || 'desc'
  });

  // 过滤空参数
  for (const [key, value] of queryParams.entries()) {
    if (!value) {
      queryParams.delete(key);
    }
  }

  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/articles/?${queryParams}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
        'Content-Type': 'application/json'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('管理员文章列表:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取管理员文章列表失败:', error);
    throw error;
  }
};
```

### 响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 156,
    "next": "https://your-domain.com/api/v1/cms/articles/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "title": "Vue.js 3.0 完全指南",
        "slug": "vue-js-3-guide",
        "content_type": "markdown",
        "status": "published",
        "visibility": "public",
        "is_featured": true,
        "is_pinned": false,
        "excerpt": "Vue.js 3.0 的完整学习指南...",
        "author": {
          "id": 1,
          "username": "admin",
          "display_name": "系统管理员",
          "is_admin": true
        },
        "published_at": "2024-01-15T10:30:00Z",
        "created_at": "2024-01-10T09:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "cover_image": "/media/images/vue-cover.jpg",
        "categories": [
          {
            "id": 1,
            "name": "前端开发"
          }
        ],
        "tags": [
          {
            "id": 1,
            "name": "Vue.js"
          },
          {
            "id": 2,
            "name": "JavaScript"
          }
        ],
        "statistics": {
          "views_count": 1250,
          "likes_count": 45,
          "comments_count": 12
        }
      }
    ]
  }
}
```

---

## 获取单篇文章

### 接口信息
- **接口地址**: `GET /api/v1/cms/articles/{id}/`
- **权限要求**: 需要管理员认证
- **功能说明**: 获取指定文章的详细信息

### 请求头
```bash
Authorization: Bearer {access_token}
Content-Type: application/json
```

### 路径参数
- `id` (integer): 文章ID，必填

### 使用示例
```bash
curl -X GET "https://your-domain.com/api/v1/cms/articles/1/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

---

## 创建文章

### 接口信息
- **接口地址**: `POST /api/v1/cms/articles/`
- **权限要求**: 需要管理员认证
- **功能说明**: 创建新文章（管理员可以为任何用户创建文章）

### 请求头
```bash
Authorization: Bearer {access_token}
Content-Type: application/json
```

### 请求体参数

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|------|
| title | string | 是 | 文章标题 | "Vue.js 教程" |
| content | string | 是 | 文章内容 | "# Vue.js 入门指南..." |
| content_type | string | 否 | 内容类型 | "markdown" |
| excerpt | string | 否 | 文章摘要 | "Vue.js 入门教程" |
| status | string | 否 | 文章状态 | "draft" |
| visibility | string | 否 | 可见性 | "public" |
| is_featured | boolean | 否 | 是否特色 | false |
| is_pinned | boolean | 否 | 是否置顶 | false |
| allow_comment | boolean | 否 | 允许评论 | true |
| password | string | 否 | 访问密码（仅密码访问时） | "" |
| cover_image | string | 否 | 封面图片URL | "/media/images/cover.jpg" |
| template | string | 否 | 模板名称 | "default" |
| parent_id | integer | 否 | 父文章ID | null |
| category_ids | array | 否 | 分类ID列表 | [1, 2] |
| tag_ids | array | 否 | 标签ID列表 | [1, 3] |
| author_type | string | 否 | 作者类型 | "admin" |
| author_id | integer | 否 | 作者ID | 1 |

### 使用示例

#### cURL 命令 - 创建文章
```bash
curl -X POST "https://your-domain.com/api/v1/cms/articles/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Django REST Framework 指南",
    "content": "# Django REST Framework 完全指南\n\nDRF 是 Django 的强大 API 框架...",
    "content_type": "markdown",
    "status": "draft",
    "visibility": "public",
    "is_featured": false,
    "category_ids": [1, 3],
    "tag_ids": [2, 5],
    "author_type": "admin",
    "author_id": 1
  }'
```

---

## 发布文章

### 接口信息
- **接口地址**: `POST /api/v1/cms/articles/{id}/publish/`
- **权限要求**: 需要管理员认证
- **功能说明**: 发布草稿状态的文章

### 请求头
```bash
Authorization: Bearer {access_token}
Content-Type: application/json
```

### 路径参数
- `id` (integer): 文章ID，必填

### 使用示例
```bash
curl -X POST "https://your-domain.com/api/v1/cms/articles/1/publish/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

### 响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "文章发布成功",
  "data": {
    "id": 1,
    "title": "Django REST Framework 指南",
    "status": "published",
    "published_at": "2024-01-20T14:30:00Z"
  }
}
```

---

## 获取文章统计

### 接口信息
- **接口地址**: `GET /api/v1/cms/articles/{id}/statistics/`
- **权限要求**: 需要管理员认证
- **功能说明**: 获取文章的详细统计信息

### 请求头
```bash
Authorization: Bearer {access_token}
Content-Type: application/json
```

### 路径参数
- `id` (integer): 文章ID，必填

### 使用示例
```bash
curl -X GET "https://your-domain.com/api/v1/cms/articles/1/statistics/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json"
```

### 响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "获取统计信息成功",
  "data": {
    "article_id": 1,
    "views_count": 1250,
    "unique_views_count": 980,
    "likes_count": 45,
    "dislikes_count": 2,
    "comments_count": 12,
    "shares_count": 8,
    "bookmarks_count": 23,
    "avg_reading_time": 180,
    "bounce_rate": 35.50,
    "last_updated_at": "2024-01-20T15:00:00Z"
  }
}
```

---

## 批量删除文章

### 接口信息
- **接口地址**: `POST /api/v1/cms/articles/batch-delete/`
- **权限要求**: 需要管理员认证
- **功能说明**: 批量删除多篇文章

### 请求头
```bash
Authorization: Bearer {access_token}
Content-Type: application/json
```

### 请求体参数

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|------|
| article_ids | array | 是 | 要删除的文章ID列表 | [1, 2, 3] |
| force_delete | boolean | 否 | 是否强制删除（true为硬删除） | false |

### 使用示例
```bash
curl -X POST "https://your-domain.com/api/v1/cms/articles/batch-delete/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [1, 2, 3],
    "force_delete": false
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

## 权限说明

### 管理员权限层级
- **超级管理员**: 可以管理所有租户的文章
- **租户管理员**: 可以管理本租户内的所有文章
- **内容管理员**: 可以管理本租户内的文章，但受限定的操作权限

### 操作权限矩阵

| 操作 | 超级管理员 | 租户管理员 | 内容管理员 |
|------|----------|----------|----------|
| 查看所有文章 | ✅ | ✅ (本租户) | ✅ (本租户) |
| 创建文章 | ✅ | ✅ | ✅ |
| 编辑任何文章 | ✅ | ✅ (本租户) | ❌ |
| 删除文章 | ✅ | ✅ (本租户) | ❌ |
| 发布文章 | ✅ | ✅ (本租户) | ❌ |
| 批量操作 | ✅ | ✅ (本租户) | ❌ |

---

## 错误处理

### 常见错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 4003 | 权限不足 | 检查用户角色和权限设置 |
| 4004 | 资源不存在 | 确认文章ID是否正确 |
| 4000 | 参数验证失败 | 检查请求参数格式 |
| 5000 | 服务器错误 | 联系技术支持 |

### 权限错误示例
```json
{
  "success": false,
  "code": 4003,
  "message": "您没有权限执行此操作",
  "error_code": "PERMISSION_DENIED"
}
```

---

## 最佳实践

### 1. 批量操作建议
```javascript
// 批量发布文章
const batchPublish = async (articleIds) => {
  const results = [];
  for (const id of articleIds) {
    try {
      const result = await fetch(`/api/v1/cms/articles/${id}/publish/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        }
      });
      results.push(await result.json());
    } catch (error) {
      console.error(`发布文章 ${id} 失败:`, error);
    }
  }
  return results;
};
```

### 2. 高效查询
```javascript
// 使用多个筛选条件优化查询
const getFilteredArticles = async (filters) => {
  const params = new URLSearchParams({
    status: filters.status || 'published',
    content_type: filters.contentType || '',
    category_id: filters.categoryId || '',
    page_size: '50',  // 较大页面大小减少请求次数
    sort: 'updated_at',
    sort_direction: 'desc'
  });

  const response = await fetch(`/api/v1/cms/articles/?${params}`, {
    headers: {
      'Authorization': `Bearer ${adminToken}`
    }
  });

  return await response.json();
};
```

---

## 集成检查清单

- ✅ 使用管理员账号进行认证
- ✅ 正确设置Authorization请求头
- ✅ 理解租户隔离机制
- ✅ 处理分页和大量数据
- ✅ 实现错误处理和重试机制
- ✅ 定期清理草稿和归档文章
- ✅ 监控文章统计数据变化
- ✅ 测试批量操作功能

---

**文档版本**: v1.0
**更新时间**: 2025-11-10
**适用对象**: 管理员、开发者
