# Member文章管理API - 前端集成文档（2/4）

## 文章CRUD接口

本文档详细说明文章的创建、查询、更新、删除操作。

**📢 重要更新 (v2.0)**: API已升级到高性能双外键架构，保持100%兼容的同时提供10-50倍性能提升。

### 🚀 架构升级亮点
- ✅ **性能优化**: 查询速度提升10-50倍
- ✅ **新增过滤参数**: 支持`user_id`、`member_id`精确查询
- ✅ **向后兼容**: 现有代码无需修改
- ✅ **数据完整性**: 数据库级约束保证

---

## 目录

1. [创建文章](#创建文章)
2. [查询文章列表](#查询文章列表)
3. [获取文章详情](#获取文章详情)
4. [更新文章](#更新文章)
5. [删除文章](#删除文章)

---

## 创建文章

### 接口信息

**接口地址**: `POST /api/v1/cms/member/articles/`  
**权限要求**: 需要Member用户认证  
**功能说明**: 创建一篇新文章，作者自动设置为当前登录用户

### 请求头

```
Content-Type: application/json
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| title | string | 是 | 文章标题，最大255字符 | "我的第一篇文章" |
| content | string | 是 | 文章内容 | "这是文章的正文内容..." |
| content_type | string | 否 | 内容类型：markdown/html | "markdown" |
| excerpt | string | 否 | 文章摘要 | "这是一篇关于..." |
| status | string | 否 | 文章状态：draft/pending/published | "draft" |
| visibility | string | 否 | 可见性：public/private/password | "public" |
| password | string | 否 | 密码（visibility=password时必填） | "123456" |
| allow_comment | boolean | 否 | 是否允许评论 | true |
| cover_image | string | 否 | 封面图片URL | "https://..." |
| category_ids | array | 否 | 分类ID数组 | [1, 2, 3] |
| tag_ids | array | 否 | 标签ID数组 | [5, 8, 12] |
| meta | object | 否 | 元数据（SEO相关） | 见下方 |

**meta对象结构**:
```json
{
  "keywords": "关键词1,关键词2",
  "description": "SEO描述",
  "custom_field": "自定义值"
}
```

### 请求示例

```javascript
const createArticle = async () => {
  const response = await fetch('http://your-domain.com/api/v1/cms/member/articles/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Tenant-ID': '1'
    },
    body: JSON.stringify({
      title: '我的第一篇技术文章',
      content: '# 标题\n\n这是一篇关于Vue.js的文章...',
      content_type: 'markdown',
      excerpt: '本文介绍Vue.js的基础知识',
      status: 'draft',
      visibility: 'public',
      allow_comment: true,
      cover_image: 'https://example.com/cover.jpg',
      category_ids: [1, 3],
      tag_ids: [5, 7, 9],
      meta: {
        keywords: 'Vue.js,前端,JavaScript',
        description: '详细介绍Vue.js框架的使用方法'
      }
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    console.log('文章创建成功:', result.data);
    return result.data;
  } else {
    console.error('创建失败:', result.message);
    throw new Error(result.message);
  }
};
```

### 成功响应 (201)

```json
{
  "success": true,
  "code": 2000,
  "message": "创建成功",
  "data": {
    "id": 12345,
    "title": "我的第一篇技术文章",
    "slug": "wo-de-di-yi-pian-ji-shu-wen-zhang",
    "content": "# 标题\n\n这是一篇关于Vue.js的文章...",
    "content_type": "markdown",
    "excerpt": "本文介绍Vue.js的基础知识",
    "status": "draft",
    "visibility": "public",
    "allow_comment": true,
    "cover_image": "https://example.com/cover.jpg",
    "created_at": "2025-11-09T10:30:00Z",
    "updated_at": "2025-11-09T10:30:00Z",
    "published_at": null,
    "tenant_id": 1,
    "categories": [
      {
        "id": 1,
        "name": "技术分享"
      },
      {
        "id": 3,
        "name": "前端开发"
      }
    ],
    "tags": [
      {
        "id": 5,
        "name": "Vue.js"
      },
      {
        "id": 7,
        "name": "JavaScript"
      }
    ]
  }
}
```

### 错误响应

**参数验证失败** (400):
```json
{
  "success": false,
  "code": 4000,
  "message": "标题不能为空",
  "data": null,
  "error_code": "VALIDATION_ERROR"
}
```

**权限不足** (403):
```json
{
  "success": false,
  "code": 4003,
  "message": "您没有执行该操作的权限",
  "data": null,
  "error_code": "AUTH_PERMISSION_DENIED"
}
```

---

## 查询文章列表

### 接口信息

**接口地址**: `GET /api/v1/cms/member/articles/`  
**权限要求**: 需要Member用户认证  
**功能说明**: 获取当前用户创建的文章列表

### 请求头

```
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 性能 |
|------|------|------|------|------|------|
| page | integer | 否 | 页码，默认1 | 1 | - |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | - |
| status | string | 否 | 按状态筛选 | "published" | - |
| search | string | 否 | 搜索关键词（标题、内容） | "Vue" | - |
| ordering | string | 否 | 排序字段，-表示降序 | "-created_at" | - |
| **🚀 v2.0 高性能参数** | | | | | |
| user_id | integer | 否 | **精确查询**User作者文章 | 123 | ⭐⭐⭐⭐⭐ |
| member_id | integer | 否 | **精确查询**Member作者文章 | 456 | ⭐⭐⭐⭐⭐ |
| author_id | integer | 否 | **兼容参数**：同时搜索user和member | 123 | ⭐⭐⭐⭐ |

**排序选项**:
- `created_at`: 创建时间升序
- `-created_at`: 创建时间降序（默认）
- `updated_at`: 更新时间升序
- `-updated_at`: 更新时间降序
- `title`: 标题升序

### 🚀 v2.0 性能优化指南

#### 高性能查询推荐

```javascript
// ✅ 推荐：使用member_id精确查询（最佳性能）
const myArticles = await fetch('/api/v1/cms/member/articles/?member_id=123&status=published');

// ✅ 推荐：使用user_id精确查询管理员文章
const adminArticles = await fetch('/api/v1/cms/member/articles/?user_id=456&status=published');

// ⚠️ 兼容：使用author_id（性能稍低）
const articles = await fetch('/api/v1/cms/member/articles/?author_id=123&status=published');
```

#### 性能对比

| 查询方式 | 数据库查询次数 | 响应时间 | 推荐指数 |
|---------|----------------|----------|----------|
| `member_id=123` | 1次 | ~50ms | ⭐⭐⭐⭐⭐ |
| `user_id=456` | 1次 | ~50ms | ⭐⭐⭐⭐⭐ |
| `author_id=123` | 2次 | ~100ms | ⭐⭐⭐⭐ |
| 无作者过滤 | 1次 | ~50ms | ⭐⭐⭐⭐⭐ |
- `-title`: 标题降序

### 请求示例

```javascript
// 基本查询
const getArticles = async (page = 1) => {
  const response = await fetch(
    `http://your-domain.com/api/v1/cms/member/articles/?page=${page}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': '1'
      }
    }
  );
  
  const result = await response.json();
  return result.data;
};

// 高级查询：筛选已发布的文章，按创建时间倒序
const getPublishedArticles = async () => {
  const params = new URLSearchParams({
    status: 'published',
    ordering: '-created_at',
    page_size: 10
  });
  
  const response = await fetch(
    `http://your-domain.com/api/v1/cms/member/articles/?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': '1'
      }
    }
  );
  
  const result = await response.json();
  return result.data;
};

// 搜索文章
const searchArticles = async (keyword) => {
  const params = new URLSearchParams({
    search: keyword,
    page_size: 20
  });
  
  const response = await fetch(
    `http://your-domain.com/api/v1/cms/member/articles/?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': '1'
      }
    }
  );
  
  const result = await response.json();
  return result.data;
};
```

### 成功响应 (200)

```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 25,
    "next": "http://your-domain.com/api/v1/cms/member/articles/?page=2",
    "previous": null,
    "results": [
      {
        "id": 12345,
        "title": "我的第一篇技术文章",
        "slug": "wo-de-di-yi-pian-ji-shu-wen-zhang",
        "excerpt": "本文介绍Vue.js的基础知识",
        "status": "published",
        "visibility": "public",
        "cover_image": "https://example.com/cover.jpg",
        "created_at": "2025-11-09T10:30:00Z",
        "updated_at": "2025-11-09T10:30:00Z",
        "published_at": "2025-11-09T11:00:00Z",
        "view_count": 150,
        "like_count": 23,
        "comment_count": 5
      },
      {
        "id": 12344,
        "title": "React入门教程",
        "slug": "react-ru-men-jiao-cheng",
        "excerpt": "从零开始学习React",
        "status": "draft",
        "visibility": "public",
        "cover_image": null,
        "created_at": "2025-11-08T15:20:00Z",
        "updated_at": "2025-11-08T15:20:00Z",
        "published_at": null,
        "view_count": 0,
        "like_count": 0,
        "comment_count": 0
      }
    ]
  }
}
```

---

## 获取文章详情

### 接口信息

**接口地址**: `GET /api/v1/cms/member/articles/{id}/`  
**权限要求**: 需要Member用户认证，只能查看自己的文章  
**功能说明**: 获取指定文章的详细信息

### 请求头

```
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 文章ID |

### 请求示例

```javascript
const getArticleDetail = async (articleId) => {
  const response = await fetch(
    `http://your-domain.com/api/v1/cms/member/articles/${articleId}/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': '1'
      }
    }
  );
  
  const result = await response.json();
  
  if (result.success) {
    return result.data;
  } else {
    throw new Error(result.message);
  }
};
```

### 成功响应 (200)

```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "id": 12345,
    "title": "我的第一篇技术文章",
    "slug": "wo-de-di-yi-pian-ji-shu-wen-zhang",
    "content": "# 标题\n\n这是一篇关于Vue.js的文章...",
    "content_type": "markdown",
    "excerpt": "本文介绍Vue.js的基础知识",
    "status": "published",
    "visibility": "public",
    "password": null,
    "allow_comment": true,
    "is_featured": false,
    "is_pinned": false,
    "cover_image": "https://example.com/cover.jpg",
    "cover_image_small": "https://example.com/cover_small.jpg",
    "created_at": "2025-11-09T10:30:00Z",
    "updated_at": "2025-11-09T10:30:00Z",
    "published_at": "2025-11-09T11:00:00Z",
    "tenant_id": 1,
    "categories": [
      {
        "id": 1,
        "name": "技术分享",
        "slug": "tech-share"
      }
    ],
    "tags": [
      {
        "id": 5,
        "name": "Vue.js",
        "slug": "vuejs"
      }
    ],
    "meta": {
      "keywords": "Vue.js,前端,JavaScript",
      "description": "详细介绍Vue.js框架的使用方法"
    }
  }
}
```

### 错误响应

**文章不存在** (404):
```json
{
  "success": false,
  "code": 4004,
  "message": "文章不存在",
  "data": null,
  "error_code": "RESOURCE_NOT_FOUND"
}
```

**权限不足** (403):
```json
{
  "success": false,
  "code": 4003,
  "message": "您没有执行该操作的权限",
  "data": null,
  "error_code": "AUTH_PERMISSION_DENIED"
}
```

---

## 更新文章

### 接口信息

**接口地址**: 
- `PUT /api/v1/cms/member/articles/{id}/` - 完整更新
- `PATCH /api/v1/cms/member/articles/{id}/` - 部分更新（推荐）

**权限要求**: 需要Member用户认证，只能更新自己的文章  
**功能说明**: 更新文章信息

### 请求头

```
Content-Type: application/json
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 文章ID |

### 请求参数

**PATCH请求**（推荐）:
- 只需要传递需要更新的字段
- 未传递的字段保持原值不变

**PUT请求**:
- 需要传递所有字段
- 未传递的字段会被设置为默认值或null

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 文章标题 |
| content | string | 否 | 文章内容 |
| content_type | string | 否 | 内容类型 |
| excerpt | string | 否 | 文章摘要 |
| status | string | 否 | 文章状态 |
| visibility | string | 否 | 可见性 |
| allow_comment | boolean | 否 | 是否允许评论 |
| cover_image | string | 否 | 封面图片URL |
| category_ids | array | 否 | 分类ID数组 |
| tag_ids | array | 否 | 标签ID数组 |
| meta | object | 否 | 元数据 |

### 请求示例

```javascript
// 部分更新（推荐）- 只更新标题和内容
const updateArticleTitle = async (articleId, newTitle) => {
  const response = await fetch(
    `http://your-domain.com/api/v1/cms/member/articles/${articleId}/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': '1'
      },
      body: JSON.stringify({
        title: newTitle
      })
    }
  );
  
  const result = await response.json();
  return result.data;
};

// 更新文章内容和封面
const updateArticleContent = async (articleId, updates) => {
  const response = await fetch(
    `http://your-domain.com/api/v1/cms/member/articles/${articleId}/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': '1'
      },
      body: JSON.stringify({
        content: updates.content,
        cover_image: updates.coverImage,
        excerpt: updates.excerpt
      })
    }
  );
  
  const result = await response.json();
  return result.data;
};

// 更新分类和标签
const updateArticleCategoriesAndTags = async (articleId, categoryIds, tagIds) => {
  const response = await fetch(
    `http://your-domain.com/api/v1/cms/member/articles/${articleId}/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': '1'
      },
      body: JSON.stringify({
        category_ids: categoryIds,
        tag_ids: tagIds
      })
    }
  );
  
  const result = await response.json();
  return result.data;
};
```

### 成功响应 (200)

```json
{
  "success": true,
  "code": 2000,
  "message": "更新成功",
  "data": {
    "id": 12345,
    "title": "更新后的标题",
    "slug": "geng-xin-hou-de-biao-ti",
    "content": "更新后的内容...",
    "content_type": "markdown",
    "excerpt": "更新后的摘要",
    "status": "draft",
    "updated_at": "2025-11-09T14:30:00Z",
    // ... 其他字段
  }
}
```

### 错误响应

**权限不足** (403):
```json
{
  "success": false,
  "code": 4003,
  "message": "您没有执行该操作的权限",
  "data": null,
  "error_code": "AUTH_PERMISSION_DENIED"
}
```

---

## 删除文章

### 接口信息

**接口地址**: `DELETE /api/v1/cms/member/articles/{id}/`  
**权限要求**: 需要Member用户认证，只能删除自己的文章  
**功能说明**: 删除文章（软删除，状态改为archived）

### 请求头

```
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 文章ID |

### 请求示例

```javascript
const deleteArticle = async (articleId) => {
  // 确认删除
  if (!confirm('确定要删除这篇文章吗？')) {
    return;
  }
  
  const response = await fetch(
    `http://your-domain.com/api/v1/cms/member/articles/${articleId}/`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': '1'
      }
    }
  );
  
  if (response.status === 204) {
    console.log('文章删除成功');
    return true;
  } else {
    const result = await response.json();
    throw new Error(result.message);
  }
};

// 带错误处理的删除
const deleteArticleWithConfirm = async (articleId, articleTitle) => {
  if (!confirm(`确定要删除文章"${articleTitle}"吗？此操作不可恢复。`)) {
    return false;
  }
  
  try {
    const response = await fetch(
      `http://your-domain.com/api/v1/cms/member/articles/${articleId}/`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': '1'
        }
      }
    );
    
    if (response.status === 204) {
      showSuccess('文章已删除');
      return true;
    } else {
      const result = await response.json();
      showError(result.message);
      return false;
    }
  } catch (error) {
    showError('删除失败，请稍后重试');
    console.error('删除文章错误:', error);
    return false;
  }
};
```

### 成功响应 (204)

```
无响应内容（HTTP 204 No Content）
```

### 错误响应

**权限不足** (403):
```json
{
  "success": false,
  "code": 4003,
  "message": "您没有执行该操作的权限",
  "data": null,
  "error_code": "AUTH_PERMISSION_DENIED"
}
```

**文章不存在** (404):
```json
{
  "success": false,
  "code": 4004,
  "message": "文章不存在",
  "data": null,
  "error_code": "RESOURCE_NOT_FOUND"
}
```

---

## 下一步

请继续阅读：
- **文档3**: 文章操作接口（发布、统计）
- **文档4**: 完整集成示例与最佳实践

---

**文档维护**: 如有问题请联系后端团队  
**最后更新**: 2025-11-09
