# 3. 文章管理 API 集成指南

## 🎯 概述

文章管理API提供完整的Member文章CRUD功能，包括创建、查询、更新、删除文章，以及文章发布和统计等高级功能。所有操作都严格限制在用户自己的文章范围内。

## 📋 API 列表

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| [获取文章列表](#获取文章列表) | GET | `/cms/member/articles/` | 获取用户的文章列表（支持分页、筛选、搜索） |
| [获取单篇文章](#获取单篇文章) | GET | `/cms/member/articles/{id}/` | 获取文章详情 |
| [创建文章](#创建文章) | POST | `/cms/member/articles/` | 创建新文章 |
| [更新文章](#更新文章) | PUT/PATCH | `/cms/member/articles/{id}/` | 更新文章内容 |
| [删除文章](#删除文章) | DELETE | `/cms/member/articles/{id}/` | 删除文章（软删除） |
| [发布文章](#发布文章) | POST | `/cms/member/articles/{id}/publish/` | 发布草稿文章 |
| [获取文章统计](#获取文章统计) | GET | `/cms/member/articles/{id}/statistics/` | 获取文章统计信息 |

---

## 获取文章列表

### 接口信息
- **接口地址**: `GET /api/v1/cms/member/articles/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 获取当前用户的所有文章列表，支持分页、筛选和搜索

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |
| status | string | 否 | 按状态筛选 | "published" | draft/pending/published/archived |
| search | string | 否 | 搜索关键词（标题和内容） | "Vue教程" | 最长100字符 |
| sort | string | 否 | 排序字段 | "created_at" | created_at/updated_at/published_at/title |
| sort_direction | string | 否 | 排序方向 | "desc" | asc/desc |

### 使用示例

#### cURL 命令 - 获取已发布文章
```bash
curl -X GET "https://your-domain.com/api/v1/cms/member/articles/?status=published&page=1&page_size=10" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### cURL 命令 - 搜索文章
```bash
curl -X GET "https://your-domain.com/api/v1/cms/member/articles/?search=Vue教程&sort=created_at&sort_direction=desc" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取文章列表
```javascript
const getArticles = async (params = {}) => {
  const queryParams = new URLSearchParams({
    page: params.page || 1,
    page_size: params.pageSize || 20,
    status: params.status || '',
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
    const response = await fetch(`https://your-domain.com/api/v1/cms/member/articles/?${queryParams}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('文章列表:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取文章列表失败:', error);
    throw error;
  }
};

// 使用示例
// 获取已发布文章
const publishedArticles = await getArticles({ status: 'published' });

// 搜索文章
const searchResults = await getArticles({ search: 'Vue教程' });

// 获取草稿
const drafts = await getArticles({ status: 'draft' });
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {
      "count": 1,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 10247,
        "title": "测试文章",
        "slug": "-4",
        "excerpt": "这是一个测试文章的内容",
        "author_info": {
          "id": 8,
          "username": "testuser456",
          "email": "test456@example.com",
          "phone": null,
          "nick_name": null,
          "first_name": "",
          "last_name": "",
          "is_active": true,
          "avatar": "",
          "tenant": 1,
          "tenant_name": "金sir",
          "is_sub_account": false,
          "parent": null,
          "parent_username": null,
          "date_joined": "2025-11-10T06:43:51.896344Z",
          "status": "active",
          "wechat_id": null
        },
        "author_type": "member",
        "status": "draft",
        "is_featured": false,
        "is_pinned": false,
        "cover_image": "",
        "cover_image_small": "",
        "published_at": null,
        "created_at": "2025-11-10T06:44:02.216630Z",
        "updated_at": "2025-11-10T06:44:02.216669Z",
        "categories": [],
        "tags": [],
        "comments_count": 0,
        "likes_count": 0,
        "views_count": 0,
        "parent": null,
        "parent_info": null,
        "children_count": 0
      }
    ]
  }
}
```

---

## 获取单篇文章

### 接口信息
- **接口地址**: `GET /api/v1/cms/member/articles/{id}/`
- **权限要求**: 需要Member用户认证，只能查看自己的文章
- **功能说明**: 获取指定文章的完整详细信息

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | 文章ID | 42 | 有效的文章ID |

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/cms/member/articles/42/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取单篇文章
```javascript
const getArticle = async (articleId) => {
  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/member/articles/${articleId}/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('文章详情:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取文章失败:', error);
    throw error;
  }
};

// 使用示例
const article = await getArticle(42);
displayArticle(article);
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 42,
    "title": "深入理解Vue.js响应式原理",
    "slug": "vue-reactivity-deep-dive",
    "excerpt": "本文详细介绍Vue.js的响应式系统实现原理...",
    "content": "# Vue.js响应式原理\n\n## 前言\n\nVue.js的响应式系统是其核心特性之一...\n\n## 实现原理\n\n### 1. 数据劫持\n\n```javascript\nconst data = { message: 'Hello' };\n\nObject.defineProperty(data, 'message', {\n  get() {\n    // 收集依赖\n    return value;\n  },\n  set(newValue) {\n    // 触发更新\n    value = newValue;\n  }\n});\n```\n\n### 2. 发布订阅模式\n\n响应式系统的核心是发布订阅模式...",
    "content_type": "markdown",
    "status": "published",
    "visibility": "public",
    "password": null,
    "allow_comment": true,
    "cover_image": "https://example.com/vue-cover.jpg",
    "author_info": {
      "id": 10,
      "username": "member001",
      "nick_name": "技术作者"
    },
    "category_info": {
      "id": 3,
      "name": "前端开发",
      "slug": "frontend"
    },
    "tags": [
      {
        "id": 5,
        "name": "Vue.js",
        "slug": "vue-js"
      },
      {
        "id": 8,
        "name": "JavaScript",
        "slug": "javascript"
      }
    ],
    "meta": {
      "keywords": "Vue.js,响应式,前端开发",
      "description": "深入理解Vue.js响应式系统的实现原理和应用场景"
    },
    "statistics": {
      "views_count": 1250,
      "likes_count": 42,
      "comments_count": 8,
      "shares_count": 15,
      "bookmarks_count": 23
    },
    "created_at": "2024-01-20T10:30:00Z",
    "updated_at": "2024-01-20T14:20:00Z",
    "published_at": "2024-01-20T15:00:00Z"
  }
}
```

---

## 创建文章

### 接口信息
- **接口地址**: `POST /api/v1/cms/member/articles/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 创建一篇新文章，默认状态为草稿

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| title | string | 是 | 文章标题 | "Vue.js入门教程" | 1-255字符 |
| content | string | 是 | 文章内容 | "# 标题\n\n内容..." | 最少1字符 |
| content_type | string | 否 | 内容类型 | "markdown" | markdown/html，默认markdown |
| excerpt | string | 否 | 文章摘要 | "本文介绍Vue.js基础知识" | 最长500字符 |
| status | string | 否 | 文章状态 | "draft" | draft/pending，默认draft |
| visibility | string | 否 | 可见性 | "public" | public/private/password，默认public |
| password | string | 否 | 访问密码（visibility=password时必填） | "123456" | 4-20字符 |
| allow_comment | boolean | 否 | 是否允许评论 | true | true/false，默认true |
| cover_image | string | 否 | 封面图片URL | "https://example.com/cover.jpg" | 有效的URL |
| category_ids | array | 否 | 分类ID数组 | [2, 5] | 有效的分类ID数组 |
| tag_ids | array | 否 | 标签ID数组 | [3, 8, 12] | 有效的标签ID数组 |
| meta | object | 否 | SEO元数据 | {"keywords": "Vue.js,教程"} | 包含keywords和description |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Vue.js入门教程",
    "content": "# Vue.js入门教程\n\n## 前言\n\nVue.js是一个渐进式的JavaScript框架...",
    "content_type": "markdown",
    "excerpt": "本文适合Vue.js初学者阅读",
    "status": "draft",
    "visibility": "public",
    "allow_comment": true,
    "cover_image": "https://example.com/vue-tutorial-cover.jpg",
    "category_ids": [2, 5],
    "tag_ids": [3, 8],
    "meta": {
      "keywords": "Vue.js,前端开发,JavaScript",
      "description": "Vue.js入门教程，适合初学者学习"
    }
  }'
```

#### JavaScript 创建文章
```javascript
const createArticle = async (articleData) => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/cms/member/articles/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(articleData)
    });

    const result = await response.json();

    if (result.success) {
      console.log('文章创建成功:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('创建文章失败:', error);
    throw error;
  }
};

// 使用示例
const newArticle = {
  title: 'React Hooks 完全指南',
  content: `# React Hooks 完全指南

## 介绍

React Hooks 是 React 16.8 引入的新特性，让你在不写 class 的情况下使用 state 以及其他的 React 特性。

## useState

\`\`\`javascript
import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>当前计数: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        增加
      </button>
    </div>
  );
}
\`\`\`

## useEffect

\`\`\`javascript
import React, { useState, useEffect } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);

  return user ? <div>{user.name}</div> : <div>加载中...</div>;
}
\`\`\`
`,
  content_type: 'markdown',
  excerpt: '全面介绍React Hooks的使用方法和最佳实践',
  status: 'draft',
  visibility: 'public',
  allow_comment: true,
  category_ids: [1, 3],
  tag_ids: [1, 2, 4],
  meta: {
    keywords: 'React,Hooks,useState,useEffect',
    description: 'React Hooks 完全指南，包含所有常用Hooks的使用方法'
  }
};

const createdArticle = await createArticle(newArticle);
console.log('新文章ID:', createdArticle.id);
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "文章创建成功",
  "data": {
    "id": 43,
    "title": "React Hooks 完全指南",
    "slug": "react-hooks-complete-guide",
    "excerpt": "全面介绍React Hooks的使用方法和最佳实践",
    "content": "# React Hooks 完全指南\n\n## 介绍\n\nReact Hooks 是 React 16.8 引入的新特性...",
    "content_type": "markdown",
    "status": "draft",
    "visibility": "public",
    "password": null,
    "allow_comment": true,
    "cover_image": null,
    "author_info": {
      "id": 10,
      "username": "member001",
      "nick_name": "技术作者"
    },
    "category_info": {
      "id": 1,
      "name": "React",
      "slug": "react"
    },
    "tags": [
      {
        "id": 1,
        "name": "React",
        "slug": "react"
      },
      {
        "id": 2,
        "name": "Hooks",
        "slug": "hooks"
      }
    ],
    "meta": {
      "keywords": "React,Hooks,useState,useEffect",
      "description": "React Hooks 完全指南，包含所有常用Hooks的使用方法"
    },
    "statistics": {
      "views_count": 0,
      "likes_count": 0,
      "comments_count": 0,
      "shares_count": 0,
      "bookmarks_count": 0
    },
    "created_at": "2024-01-21T09:15:00Z",
    "updated_at": "2024-01-21T09:15:00Z",
    "published_at": null
  }
}
```

---

## 更新文章

### 接口信息
- **接口地址**: `PUT /api/v1/cms/member/articles/{id}/` (完整更新) 或 `PATCH /api/v1/cms/member/articles/{id}/` (部分更新)
- **权限要求**: 需要Member用户认证，只能更新自己的文章
- **功能说明**: 更新文章内容，支持完整更新和部分更新

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | 文章ID | 43 | 有效的文章ID |

### 请求参数
同[创建文章](#创建文章)的请求参数，PATCH请求只需要传递要更新的字段。

### 使用示例

#### cURL 命令 - 部分更新
```bash
curl -X PATCH "https://your-domain.com/api/v1/cms/member/articles/43/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "React Hooks 完全指南 (更新版)",
    "excerpt": "全面介绍React Hooks的使用方法和最佳实践 (更新版)",
    "status": "pending"
  }'
```

#### JavaScript 更新文章
```javascript
const updateArticle = async (articleId, updates, partial = true) => {
  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/member/articles/${articleId}/`, {
      method: partial ? 'PATCH' : 'PUT',  // PATCH为部分更新，PUT为完整更新
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });

    const result = await response.json();

    if (result.success) {
      console.log('文章更新成功:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('更新文章失败:', error);
    throw error;
  }
};

// 使用示例

// 部分更新 - 只更新标题和摘要
await updateArticle(43, {
  title: 'React Hooks 完全指南 (2024版)',
  excerpt: '最新版React Hooks使用指南'
});

// 发布文章 - 更新状态为published
await updateArticle(43, {
  status: 'published'
});

// 完整更新 - 替换整篇文章内容
await updateArticle(43, {
  title: '完整的React Hooks教程',
  content: '新的完整内容...',
  content_type: 'markdown',
  excerpt: '完整版教程',
  status: 'published',
  visibility: 'public',
  allow_comment: true,
  category_ids: [1, 3],
  tag_ids: [1, 2, 4]
}, false);  // false表示完整更新
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "文章更新成功",
  "data": {
    "id": 43,
    "title": "React Hooks 完全指南 (2024版)",
    "slug": "react-hooks-complete-guide-2024",
    "excerpt": "最新版React Hooks使用指南",
    "content": "# React Hooks 完全指南\n\n## 介绍...",
    "content_type": "markdown",
    "status": "published",
    "visibility": "public",
    "password": null,
    "allow_comment": true,
    "cover_image": "https://example.com/react-hooks-cover.jpg",
    "author_info": {
      "id": 10,
      "username": "member001",
      "nick_name": "技术作者"
    },
    "category_info": {
      "id": 1,
      "name": "React",
      "slug": "react"
    },
    "tags": [
      {
        "id": 1,
        "name": "React",
        "slug": "react"
      },
      {
        "id": 2,
        "name": "Hooks",
        "slug": "hooks"
      }
    ],
    "meta": {
      "keywords": "React,Hooks,useState,useEffect",
      "description": "React Hooks 完全指南，包含所有常用Hooks的使用方法"
    },
    "statistics": {
      "views_count": 0,
      "likes_count": 0,
      "comments_count": 0,
      "shares_count": 0,
      "bookmarks_count": 0
    },
    "created_at": "2024-01-21T09:15:00Z",
    "updated_at": "2024-01-21T09:30:00Z",
    "published_at": "2024-01-21T09:30:00Z"
  }
}
```

---

## 删除文章

### 接口信息
- **接口地址**: `DELETE /api/v1/cms/member/articles/{id}/`
- **权限要求**: 需要Member用户认证，只能删除自己的文章
- **功能说明**: 删除文章（软删除，状态改为archived）

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | 文章ID | 43 | 有效的文章ID |

### 使用示例

#### cURL 命令
```bash
curl -X DELETE "https://your-domain.com/api/v1/cms/member/articles/43/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 删除文章
```javascript
const deleteArticle = async (articleId) => {
  // 显示确认对话框
  const confirmed = confirm('确定要删除这篇文章吗？删除后可以恢复文章状态。');
  if (!confirmed) return false;

  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/member/articles/${articleId}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    if (response.status === 204) {
      console.log('文章删除成功');
      return true;
    } else {
      const result = await response.json();
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('删除文章失败:', error);
    throw error;
  }
};

// 使用示例
const success = await deleteArticle(43);
if (success) {
  // 刷新文章列表或跳转页面
  refreshArticleList();
}
```

### 成功响应
```http
HTTP/1.1 204 No Content
```

---

## 发布文章

### 接口信息
- **接口地址**: `POST /api/v1/cms/member/articles/{id}/publish/`
- **权限要求**: 需要Member用户认证，只能发布自己的文章
- **功能说明**: 将草稿或待审核状态的文章发布

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | 文章ID | 43 | 有效的文章ID |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/cms/member/articles/43/publish/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 发布文章
```javascript
const publishArticle = async (articleId) => {
  const confirmed = confirm('确定要发布这篇文章吗？');
  if (!confirmed) return false;

  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/member/articles/${articleId}/publish/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('文章发布成功:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('发布文章失败:', error);
    throw error;
  }
};

// 使用示例
const publishedArticle = await publishArticle(43);
if (publishedArticle) {
  showToast('文章发布成功');
  // 更新UI状态
  updateArticleStatus(publishedArticle.id, 'published');
}
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "文章发布成功",
  "data": {
    "id": 43,
    "title": "React Hooks 完全指南 (2024版)",
    "status": "published",
    "published_at": "2024-01-21T10:00:00Z",
    "updated_at": "2024-01-21T10:00:00Z"
  }
}
```

---

## 获取文章统计

### 接口信息
- **接口地址**: `GET /api/v1/cms/member/articles/{id}/statistics/`
- **权限要求**: 需要Member用户认证，只能查看自己文章的统计
- **功能说明**: 获取文章的统计信息（浏览量、点赞数等）

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | 文章ID | 43 | 有效的文章ID |

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/cms/member/articles/43/statistics/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取文章统计
```javascript
const getArticleStatistics = async (articleId) => {
  try {
    const response = await fetch(`https://your-domain.com/api/v1/cms/member/articles/${articleId}/statistics/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('文章统计:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取文章统计失败:', error);
    throw error;
  }
};

// 使用示例
const stats = await getArticleStatistics(43);
displayArticleStats(stats);

// 显示统计信息
function displayArticleStats(stats) {
  document.getElementById('views-count').textContent = stats.views_count;
  document.getElementById('likes-count').textContent = stats.likes_count;
  document.getElementById('comments-count').textContent = stats.comments_count;
  document.getElementById('shares-count').textContent = stats.shares_count;
  document.getElementById('bookmarks-count').textContent = stats.bookmarks_count;
}
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "views_count": 1250,
    "unique_views_count": 980,
    "likes_count": 42,
    "comments_count": 8,
    "shares_count": 15,
    "bookmarks_count": 23
  }
}
```

---

## 🔧 前端集成最佳实践

### 1. 文章管理器类
```javascript
class ArticleManager {
  constructor() {
    this.baseURL = 'https://your-domain.com/api/v1';
    this.tenantId = '1';
  }

  // 获取文章列表
  async getArticles(params = {}) {
    const queryParams = new URLSearchParams(params);
    const url = `${this.baseURL}/cms/member/articles/?${queryParams}`;

    return await this.apiRequest(url);
  }

  // 获取单篇文章
  async getArticle(articleId) {
    const url = `${this.baseURL}/cms/member/articles/${articleId}/`;
    return await this.apiRequest(url);
  }

  // 创建文章
  async createArticle(articleData) {
    const url = `${this.baseURL}/cms/member/articles/`;
    return await this.apiRequest(url, {
      method: 'POST',
      body: JSON.stringify(articleData)
    });
  }

  // 更新文章
  async updateArticle(articleId, updates, partial = true) {
    const url = `${this.baseURL}/cms/member/articles/${articleId}/`;
    return await this.apiRequest(url, {
      method: partial ? 'PATCH' : 'PUT',
      body: JSON.stringify(updates)
    });
  }

  // 删除文章
  async deleteArticle(articleId) {
    const url = `${this.baseURL}/cms/member/articles/${articleId}/`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });

    if (response.status === 204) {
      return { success: true };
    } else {
      const result = await response.json();
      throw new Error(result.message);
    }
  }

  // 发布文章
  async publishArticle(articleId) {
    const url = `${this.baseURL}/cms/member/articles/${articleId}/publish/`;
    return await this.apiRequest(url, { method: 'POST' });
  }

  // 获取文章统计
  async getArticleStatistics(articleId) {
    const url = `${this.baseURL}/cms/member/articles/${articleId}/statistics/`;
    return await this.apiRequest(url);
  }

  // 通用API请求方法
  async apiRequest(url, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...this.getAuthHeaders(),
      ...options.headers
    };

    try {
      const response = await fetch(url, {
        headers,
        ...options
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message || '请求失败');
      }

      return result;
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  }

  // 获取认证头
  getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    const headers = {};

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    // Member用户需要租户ID
    const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
    if (userInfo.is_member) {
      headers['X-Tenant-ID'] = this.tenantId;
    }

    return headers;
  }
}

// 使用示例
const articleManager = new ArticleManager();

// 获取文章列表
const articles = await articleManager.getArticles({
  status: 'published',
  page: 1,
  page_size: 10
});

// 创建文章
const newArticle = await articleManager.createArticle({
  title: '新文章标题',
  content: '文章内容...',
  status: 'draft'
});

// 发布文章
await articleManager.publishArticle(newArticle.data.id);
```

### 2. 富文本编辑器集成
```javascript
class ArticleEditor {
  constructor(options = {}) {
    this.articleManager = options.articleManager;
    this.editorElement = options.editorElement;
    this.previewElement = options.previewElement;
    this.autoSave = options.autoSave !== false;
    this.autoSaveInterval = options.autoSaveInterval || 30000; // 30秒

    this.currentArticle = null;
    this.hasUnsavedChanges = false;

    this.init();
  }

  init() {
    this.setupEditor();
    if (this.autoSave) {
      this.startAutoSave();
    }
  }

  setupEditor() {
    // 这里可以集成各种富文本编辑器，如TinyMCE, CKEditor等
    // 示例使用简单的textarea + markdown预览

    const editor = this.editorElement;
    const preview = this.previewElement;

    editor.addEventListener('input', () => {
      this.hasUnsavedChanges = true;
      this.updatePreview();
    });
  }

  updatePreview() {
    // 简单的markdown预览实现
    const content = this.editorElement.value;
    const html = this.markdownToHtml(content);
    this.previewElement.innerHTML = html;
  }

  markdownToHtml(markdown) {
    // 简化的markdown转换（实际项目中建议使用marked.js等库）
    return markdown
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*)\*/gim, '<em>$1</em>')
      .replace(/```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/gim, '<code>$1</code>')
      .replace(/\n/gim, '<br>');
  }

  startAutoSave() {
    setInterval(async () => {
      if (this.hasUnsavedChanges && this.currentArticle) {
        try {
          await this.saveArticle(false); // 自动保存，不显示提示
          this.hasUnsavedChanges = false;
        } catch (error) {
          console.warn('自动保存失败:', error);
        }
      }
    }, this.autoSaveInterval);
  }

  async loadArticle(articleId) {
    try {
      const result = await this.articleManager.getArticle(articleId);
      this.currentArticle = result.data;

      // 填充编辑器
      this.editorElement.value = this.currentArticle.content;
      this.updatePreview();

      this.hasUnsavedChanges = false;
    } catch (error) {
      console.error('加载文章失败:', error);
    }
  }

  async saveArticle(showToast = true) {
    if (!this.currentArticle) return;

    const content = this.editorElement.value;
    const updates = { content };

    try {
      const result = await this.articleManager.updateArticle(
        this.currentArticle.id,
        updates,
        true // 部分更新
      );

      this.currentArticle = result.data;
      this.hasUnsavedChanges = false;

      if (showToast) {
        showToast('文章保存成功');
      }

      return result.data;
    } catch (error) {
      console.error('保存文章失败:', error);
      throw error;
    }
  }

  async publishArticle() {
    if (!this.currentArticle) return;

    try {
      const result = await this.articleManager.publishArticle(this.currentArticle.id);
      this.currentArticle = result.data;

      showToast('文章发布成功');
      return result.data;
    } catch (error) {
      console.error('发布文章失败:', error);
      throw error;
    }
  }
}

// 使用示例
const editor = new ArticleEditor({
  articleManager: new ArticleManager(),
  editorElement: document.getElementById('article-editor'),
  previewElement: document.getElementById('article-preview'),
  autoSave: true
});

// 加载文章进行编辑
await editor.loadArticle(42);

// 手动保存
document.getElementById('save-btn').addEventListener('click', () => {
  editor.saveArticle();
});

// 发布文章
document.getElementById('publish-btn').addEventListener('click', () => {
  editor.publishArticle();
});
```

### 3. 文章列表组件
```javascript
class ArticleList {
  constructor(options = {}) {
    this.articleManager = options.articleManager;
    this.container = options.container;
    this.pageSize = options.pageSize || 20;
    this.currentPage = 1;
    this.currentStatus = 'all'; // all, published, draft, pending, archived

    this.init();
  }

  init() {
    this.loadArticles();
    this.setupFilters();
  }

  async loadArticles(page = 1, status = this.currentStatus) {
    try {
      this.showLoading();

      const params = {
        page: page,
        page_size: this.pageSize
      };

      if (status !== 'all') {
        params.status = status;
      }

      const result = await this.articleManager.getArticles(params);

      this.currentPage = page;
      this.currentStatus = status;

      this.renderArticles(result.data);
      this.renderPagination(result.data);

    } catch (error) {
      console.error('加载文章列表失败:', error);
      this.showError(error.message);
    } finally {
      this.hideLoading();
    }
  }

  renderArticles(data) {
    const articles = data.results;
    const html = articles.map(article => `
      <div class="article-item" data-id="${article.id}">
        <div class="article-header">
          <h3 class="article-title">${article.title}</h3>
          <span class="article-status status-${article.status}">${this.getStatusText(article.status)}</span>
        </div>
        <div class="article-meta">
          <span class="article-date">${this.formatDate(article.created_at)}</span>
          <span class="article-views">${article.statistics.views_count} 阅读</span>
          <span class="article-likes">${article.statistics.likes_count} 点赞</span>
        </div>
        <div class="article-excerpt">${article.excerpt || '暂无摘要'}</div>
        <div class="article-actions">
          <button class="btn-edit" onclick="editArticle(${article.id})">编辑</button>
          <button class="btn-preview" onclick="previewArticle(${article.id})">预览</button>
          ${article.status === 'draft' || article.status === 'pending' ?
            `<button class="btn-publish" onclick="publishArticle(${article.id})">发布</button>` : ''}
          <button class="btn-delete" onclick="deleteArticle(${article.id})">删除</button>
        </div>
      </div>
    `).join('');

    this.container.innerHTML = html;
  }

  renderPagination(data) {
    const { count, next, previous, total_pages } = data;
    const paginationHtml = `
      <div class="pagination">
        <button class="btn-prev" ${!previous ? 'disabled' : ''} onclick="changePage(${this.currentPage - 1})">
          上一页
        </button>
        <span class="page-info">第 ${this.currentPage} 页，共 ${total_pages} 页 (${count} 篇文章)</span>
        <button class="btn-next" ${!next ? 'disabled' : ''} onclick="changePage(${this.currentPage + 1})">
          下一页
        </button>
      </div>
    `;

    // 添加分页到容器
    const paginationContainer = document.createElement('div');
    paginationContainer.innerHTML = paginationHtml;
    this.container.appendChild(paginationContainer);
  }

  setupFilters() {
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
      statusFilter.addEventListener('change', (e) => {
        this.loadArticles(1, e.target.value);
      });
    }
  }

  getStatusText(status) {
    const statusMap = {
      'draft': '草稿',
      'pending': '待审核',
      'published': '已发布',
      'archived': '已归档'
    };
    return statusMap[status] || status;
  }

  formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
  }

  showLoading() {
    this.container.innerHTML = '<div class="loading">加载中...</div>';
  }

  hideLoading() {
    // 移除loading状态
  }

  showError(message) {
    this.container.innerHTML = `<div class="error">加载失败: ${message}</div>`;
  }
}

// 全局函数供按钮调用
window.editArticle = (id) => {
  // 跳转到编辑页面
  window.location.href = `/articles/${id}/edit`;
};

window.previewArticle = (id) => {
  // 打开预览窗口
  window.open(`/articles/${id}/preview`, '_blank');
};

window.publishArticle = async (id) => {
  if (confirm('确定要发布这篇文章吗？')) {
    try {
      const articleManager = new ArticleManager();
      await articleManager.publishArticle(id);
      // 重新加载列表
      articleList.loadArticles();
      showToast('文章发布成功');
    } catch (error) {
      showToast('发布失败: ' + error.message, 'error');
    }
  }
};

window.deleteArticle = async (id) => {
  if (confirm('确定要删除这篇文章吗？删除后可以恢复。')) {
    try {
      const articleManager = new ArticleManager();
      await articleManager.deleteArticle(id);
      // 重新加载列表
      articleList.loadArticles();
      showToast('文章删除成功');
    } catch (error) {
      showToast('删除失败: ' + error.message, 'error');
    }
  }
};

window.changePage = (page) => {
  articleList.loadArticles(page);
};

// 初始化
const articleList = new ArticleList({
  articleManager: new ArticleManager(),
  container: document.getElementById('article-list'),
  pageSize: 10
});
```
