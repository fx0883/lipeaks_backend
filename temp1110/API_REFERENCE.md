# Member CMS API 完整参考手册

## 📖 文档导航

本文档提供所有API接口的完整索引，按模块分类，便于快速查找和导航。

**📢 验证说明**: 所有API返回示例均通过实际curl调用验证，确保与服务器响应完全一致。

## 🎯 API 模块总览

| 模块 | 文件名 | 接口数量 | 主要功能 |
|------|--------|----------|----------|
| [认证系统](#认证系统) | `01_authentication.md` | 5个 | 用户注册、登录、Token管理 |
| [用户管理](#用户管理) | `02_user_management.md` | 5个 | 个人信息、密码、头像管理 |
| [文章管理](#文章管理) | `03_article_management.md` | 7个 | 文章CRUD、发布、统计 |
| [互动功能](#互动功能) | `04_interactions.md` | 6个 | 收藏、点赞、关注 |
| [分类标签](#分类标签) | `05_categories_tags.md` | 6个 | 分类、标签、标签分组管理 |
| [评论系统](#评论系统) | `06_comments.md` | 13个 | 评论CRUD、回复、审核 |

---

## 🔐 认证系统

**文件**: `01_authentication.md`  
**基础路径**: `/api/v1/auth/`

### 核心接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [用户注册](#用户注册) | POST | `/member/register/` | Member用户注册账号 |
| [用户登录](#用户登录) | POST | `/login/` | 支持Member和Admin登录 |
| [Token刷新](#token刷新) | POST | `/refresh/` | 刷新Access Token |
| [Token验证](#token验证) | GET | `/verify/` | 验证Token有效性 |
| [密码重置请求](#密码重置请求) | POST | `/password-reset/request/` | 请求密码重置邮件 |

### 请求头规范
```bash
# Member用户注册/登录
X-Tenant-ID: {tenant_id}          # 必需
Content-Type: application/json    # POST请求

# Token相关接口
Authorization: Bearer {token}     # 需要认证时
```

### 快速开始示例
```bash
# 1. 用户注册
curl -X POST "https://your-domain.com/api/v1/auth/member/register/" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123", "password_confirm": "password123"}'

# 2. 用户登录
curl -X POST "https://your-domain.com/api/v1/auth/login/" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# 3. 使用Token访问其他接口
curl -X GET "https://your-domain.com/api/v1/members/me/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-ID: 1"
```

---

## 👤 用户管理

**文件**: `02_user_management.md`  
**基础路径**: `/api/v1/members/`

### 核心接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [获取用户信息](#获取用户信息) | GET | `/me/` | 获取当前登录用户的详细信息 |
| [更新用户信息](#更新用户信息) | PUT/PATCH | `/me/` | 更新当前用户的个人信息 |
| [修改密码](#修改密码) | POST | `/me/password/` | 修改当前用户的登录密码 |
| [上传头像](#上传头像) | POST | `/avatar/upload/` | 上传当前用户的头像 |
| [为指定用户上传头像](#为指定用户上传头像) | POST | `/{id}/avatar/upload/` | 管理员为指定用户上传头像 |

### 请求头规范
```bash
Authorization: Bearer {token}     # 必需
X-Tenant-ID: {tenant_id}          # Member用户必需
Content-Type: application/json    # JSON请求
Content-Type: multipart/form-data # 文件上传
```

### 权限说明
- **普通用户**: 只能操作自己的信息
- **管理员**: 可为其他用户上传头像
- **子账号**: 受父账号权限限制

---

## 📝 文章管理

**文件**: `03_article_management.md`  
**基础路径**: `/api/v1/cms/member/articles/`

### 核心接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [获取文章列表](#获取文章列表) | GET | `/` | 获取用户的文章列表（分页、筛选、搜索） |
| [获取单篇文章](#获取单篇文章) | GET | `/{id}/` | 获取文章详情 |
| [创建文章](#创建文章) | POST | `/` | 创建新文章 |
| [更新文章](#更新文章) | PUT/PATCH | `/{id}/` | 更新文章内容 |
| [删除文章](#删除文章) | DELETE | `/{id}/` | 删除文章（软删除） |
| [发布文章](#发布文章) | POST | `/{id}/publish/` | 发布草稿文章 |
| [获取文章统计](#获取文章统计) | GET | `/{id}/statistics/` | 获取文章统计信息 |

### 请求头规范
```bash
Authorization: Bearer {token}     # 必需
X-Tenant-ID: {tenant_id}          # 必需
Content-Type: application/json    # 必需
```

### 查询参数说明
```bash
# 分页参数
page=1&page_size=20

# 状态筛选
status=published  # draft/pending/published/archived

# 搜索
search=Vue教程

# 排序
sort=created_at&sort_direction=desc  # created_at/updated_at/published_at/title
```

### 文章状态流转
```
草稿(draft) → 待审核(pending) → 已发布(published) → 已归档(archived)
     ↓             ↓                        ↓
   保存草稿 → 提交审核 → 管理员审核 → 手动归档
```

---

## 💝 互动功能

**文件**: `04_interactions.md`  
**基础路径**: `/api/v1/interactions/`

### 收藏相关接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [获取收藏列表](#获取收藏列表) | GET | `/favorites/` | 获取用户的文章收藏列表 |
| [收藏文章](#收藏文章) | POST | `/favorites/` | 收藏指定的文章 |
| [取消收藏（按收藏ID）](#取消收藏按收藏id) | DELETE | `/favorites/{id}/` | 通过收藏记录ID取消收藏 |
| [取消收藏（按文章ID）](#取消收藏按文章id) | DELETE | `/favorites/by-article/{article_id}/` | 通过文章ID取消收藏 |
| [检查收藏状态](#检查收藏状态) | GET | `/favorites/check/{article_id}/` | 检查文章是否已被收藏 |

### 点赞相关接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [获取点赞列表](#获取点赞列表) | GET | `/likes/` | 获取用户发出的点赞列表 |
| [点赞用户](#点赞用户) | POST | `/likes/` | 点赞指定的用户 |
| [获取收到的点赞](#获取收到的点赞) | GET | `/likes/received/` | 获取收到的点赞列表 |
| [检查点赞状态](#检查点赞状态) | GET | `/likes/check/{member_id}/` | 检查是否已点赞用户 |

### 请求头规范
```bash
Authorization: Bearer {token}     # 必需
X-Tenant-ID: {tenant_id}          # 必需
Content-Type: application/json    # POST请求
```

### 业务规则
- **收藏**: 每个用户对每篇文章只能收藏一次
- **点赞**: 每个用户对每个用户只能点赞一次
- **权限**: 只能查看本租户内的互动数据
- **数据隔离**: 不同租户的用户互动数据完全隔离

---

## 🏷️ 分类标签

**文件**: `05_categories_tags.md`  
**基础路径**: `/api/v1/cms/`

### 分类相关接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [获取分类列表](#获取分类列表) | GET | `/categories/` | 获取所有分类，支持分页和搜索 |
| [获取分类树](#获取分类树) | GET | `/categories/tree/` | 获取完整的分类树结构 |
| [创建分类](#创建分类) | POST | `/categories/` | 创建新分类（管理员权限） |

### 标签相关接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [获取标签列表](#获取标签列表) | GET | `/tags/` | 获取所有标签，支持分页和搜索 |
| [创建标签](#创建标签) | POST | `/tags/` | 创建新标签（管理员权限） |

### 标签分组相关接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [获取标签分组列表](#获取标签分组列表) | GET | `/tag-groups/` | 获取所有标签分组 |

### 权限说明
- **读取操作**: 公开访问，无需认证
- **管理操作**: 需要管理员权限
- **数据隔离**: 支持按租户过滤

---

## 💬 评论系统

**文件**: `06_comments.md`  
**基础路径**: `/api/v1/cms/comments/`

### 评论基础接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [获取文章评论列表](#获取文章评论列表) | GET | `/` | 获取文章的评论列表 |
| [获取单条评论详情](#获取单条评论详情) | GET | `/{id}/` | 获取单条评论详情 |
| [发表评论](#发表评论) | POST | `/` | 为文章发表新评论 |
| [回复评论](#回复评论) | POST | `/{id}/replies/` | 回复指定的评论 |
| [更新评论](#更新评论) | PUT/PATCH | `/{id}/` | 更新自己的评论 |
| [删除评论](#删除评论) | DELETE | `/{id}/` | 删除评论（软删除） |

### 互动接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [点赞评论](#点赞评论) | POST | `/{id}/like/` | 点赞评论 |
| [取消点赞评论](#取消点赞评论) | DELETE | `/{id}/like/` | 取消点赞评论 |
| [举报评论](#举报评论) | POST | `/{id}/report/` | 举报不当评论 |

### 管理接口

| 接口 | 方法 | 路径 | 功能描述 |
|------|------|------|----------|
| [审核评论](#审核评论) | POST | `/{id}/moderate/` | 管理员审核评论 |
| [获取评论回复](#获取评论回复) | GET | `/{id}/replies/` | 获取评论的所有回复 |
| [获取评论统计](#获取评论统计) | GET | `/{id}/stats/` | 获取评论统计信息 |

### 评论状态流转
```
待审核(pending) → 已通过(approved)
       ↓              ↓
   拒绝(rejected)    举报(spam)
       ↓              ↓
   隐藏(hidden)    删除(deleted)
```

### 权限说明
- **发表评论**: 需要登录认证
- **查看评论**: 公开访问（根据文章权限）
- **管理评论**: 需要管理员权限
- **回复评论**: 支持多层嵌套回复

---

## 🔧 通用规范

### 请求头要求
```bash
Authorization: Bearer {access_token}    # 需要认证的接口必需
X-Tenant-ID: {tenant_id}                # Member用户相关接口必需
Content-Type: application/json          # JSON请求
Content-Type: multipart/form-data       # 文件上传
```

### 响应格式
```json
{
  "success": true,           // 请求是否成功
  "code": 2000,             // 响应码
  "message": "操作成功",      // 响应消息
  "data": { ... },          // 主要数据
  "error_code": null        // 错误时返回错误码
}
```

### 分页响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 150,           // 总条数
    "next": "...",          // 下一页URL
    "previous": "...",      // 上一页URL
    "results": [...]        // 数据列表
  }
}
```

### 错误响应
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "field_name": ["错误信息"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

---

## 📊 状态码说明

| 状态码 | 说明 | 含义 |
|--------|------|------|
| 2000 | 成功 | 请求成功处理 |
| 4000 | 验证错误 | 请求参数不符合要求 |
| 4001 | 未认证 | 需要登录认证 |
| 4003 | 权限不足 | 用户没有操作权限 |
| 4004 | 资源不存在 | 请求的资源不存在 |
| 5000 | 服务器错误 | 服务器内部错误 |

---

## 🏃‍♂️ 快速集成指南

### 1. 环境准备
```javascript
const API_BASE = 'https://your-domain.com/api/v1';

// 全局配置
const config = {
  tenantId: '1',  // 从配置文件获取
  getToken: () => localStorage.getItem('access_token'),
  setToken: (token) => localStorage.setItem('access_token', token)
};
```

### 2. 通用请求方法
```javascript
class ApiClient {
  constructor(baseURL, config) {
    this.baseURL = baseURL;
    this.config = config;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.config.getToken();

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    // 添加认证头
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    // 添加租户头
    if (this.config.tenantId) {
      headers['X-Tenant-ID'] = this.config.tenantId;
    }

    try {
      const response = await fetch(url, {
        headers,
        ...options
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message);
      }

      return result;
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  }
}

// 初始化API客户端
const api = new ApiClient(API_BASE, config);
```

### 3. 常用集成模式
```javascript
// 认证流程
const auth = {
  async login(username, password) {
    const result = await api.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });

    config.setToken(result.data.token);
    return result.data.user;
  },

  async refreshToken() {
    const result = await api.request('/auth/refresh/', {
      method: 'POST',
      body: JSON.stringify({
        refresh_token: localStorage.getItem('refresh_token')
      })
    });

    config.setToken(result.data.token);
    return result.data.token;
  }
};

// 文章管理
const articles = {
  async getList(params = {}) {
    const query = new URLSearchParams(params);
    return await api.request(`/cms/member/articles/?${query}`);
  },

  async create(articleData) {
    return await api.request('/cms/member/articles/', {
      method: 'POST',
      body: JSON.stringify(articleData)
    });
  },

  async update(id, updates) {
    return await api.request(`/cms/member/articles/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    });
  }
};

// 使用示例
async function loadUserArticles() {
  try {
    const result = await articles.getList({
      status: 'published',
      page: 1,
      page_size: 10
    });

    renderArticles(result.data.results);
  } catch (error) {
    if (error.message.includes('登录')) {
      // 重定向到登录页面
      window.location.href = '/login';
    } else {
      showError(error.message);
    }
  }
}
```

---

## 📋 检查清单

### 前端集成前请确认：

- ✅ 已阅读相关模块的详细文档
- ✅ 理解了API的认证和权限要求
- ✅ 配置了正确的Base URL和租户ID
- ✅ 实现了Token存储和管理机制
- ✅ 处理了API响应和错误情况
- ✅ 实现了分页数据的加载逻辑
- ✅ 添加了合适的加载状态和用户反馈
- ✅ 测试了所有核心功能接口

### 常见问题排查：

1. **认证失败**: 检查Token是否有效，是否包含正确的请求头
2. **权限不足**: 确认用户角色和操作权限
3. **数据为空**: 检查租户ID是否正确，数据是否存在
4. **网络错误**: 检查网络连接，API地址是否正确
5. **参数错误**: 参考文档检查请求参数格式

---

## 📞 技术支持

如果在集成过程中遇到问题，请：

1. 仔细阅读相关API文档
2. 检查浏览器开发者工具的网络请求
3. 查看服务器返回的错误信息
4. 参考文档中的示例代码
5. 检查Token和权限配置

**文档版本**: v2.0  
**更新时间**: 2025-11-10  
**适用对象**: 前端开发人员
