# 4. 互动功能 API 集成指南

## 🎯 概述

互动功能API提供文章收藏、用户点赞、用户关注等社交互动功能，帮助增加用户粘性和平台活跃度。所有操作都基于Member用户身份验证。

## 📋 API 列表

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| [获取收藏列表](#获取收藏列表) | GET | `/interactions/favorites/` | 获取用户的文章收藏列表 |
| [收藏文章](#收藏文章) | POST | `/interactions/favorites/` | 收藏指定的文章 |
| [取消收藏（按收藏ID）](#取消收藏按收藏id) | DELETE | `/interactions/favorites/{id}/` | 通过收藏记录ID取消收藏 |
| [取消收藏（按文章ID）](#取消收藏按文章id) | DELETE | `/interactions/favorites/by-article/{article_id}/` | 通过文章ID取消收藏 |
| [检查收藏状态](#检查收藏状态) | GET | `/interactions/favorites/check/{article_id}/` | 检查文章是否已被收藏 |
| [获取点赞列表](#获取点赞列表) | GET | `/interactions/likes/` | 获取用户发出的点赞列表 |
| [点赞用户](#点赞用户) | POST | `/interactions/likes/` | 点赞指定的用户 |
| [取消点赞（按记录ID）](#取消点赞按记录id) | DELETE | `/interactions/likes/{id}/` | 通过点赞记录ID取消点赞 |
| [取消点赞（按用户ID）](#取消点赞按用户id) | DELETE | `/interactions/likes/by-member/{member_id}/` | 通过用户ID取消点赞 |
| [获取收到的点赞](#获取收到的点赞) | GET | `/interactions/likes/received/` | 获取收到的点赞列表 |
| [检查点赞状态](#检查点赞状态) | GET | `/interactions/likes/check/{member_id}/` | 检查是否已点赞用户 |
| [获取关注列表](#获取关注列表) | GET | `/interactions/follows/` | 获取用户的关注列表 |
| [关注用户](#关注用户) | POST | `/interactions/follows/` | 关注指定的用户 |
| [取消关注](#取消关注) | DELETE | `/interactions/follows/{id}/` | 取消关注 |
| [检查关注状态](#检查关注状态) | GET | `/interactions/follows/check/{member_id}/` | 检查是否已关注用户 |

---

## 获取收藏列表

### 接口信息
- **接口地址**: `GET /api/v1/interactions/favorites/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 获取当前用户收藏的所有文章列表

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

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/interactions/favorites/?page=1&page_size=10" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取收藏列表
```javascript
const getFavorites = async (params = {}) => {
  const queryParams = new URLSearchParams({
    page: params.page || 1,
    page_size: params.pageSize || 20
  });

  try {
    const response = await fetch(`https://your-domain.com/api/v1/interactions/favorites/?${queryParams}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('收藏列表:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取收藏列表失败:', error);
    throw error;
  }
};

// 使用示例
const favorites = await getFavorites({ page: 1, pageSize: 10 });
displayFavorites(favorites.results);
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 25,
    "next": "https://your-domain.com/api/v1/interactions/favorites/?page=2&page_size=10",
    "previous": null,
    "results": [
      {
        "id": 23,
        "user": 5,
        "article": 42,
        "article_detail": {
          "id": 42,
          "title": "深入理解Vue.js响应式原理",
          "slug": "vue-reactivity-deep-dive",
          "excerpt": "本文详细介绍Vue.js的响应式系统实现原理...",
          "cover_image": "https://example.com/vue.jpg",
          "author_info": {
            "id": 3,
            "username": "author",
            "nick_name": "技术专家"
          },
          "status": "published",
          "views_count": 1250,
          "likes_count": 42,
          "created_at": "2024-01-20T10:30:00Z"
        },
        "user_info": {
          "id": 5,
          "username": "member_user",
          "nick_name": "学习者"
        },
        "tenant": 1,
        "created_at": "2024-01-20T15:45:00Z"
      }
    ]
  }
}
```

---

## 收藏文章

### 接口信息
- **接口地址**: `POST /api/v1/interactions/favorites/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 将指定的文章添加到收藏列表

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| article | integer | 是 | 要收藏的文章ID | 42 | 有效的文章ID，必须是已发布的文章 |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/interactions/favorites/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 42
  }'
```

#### JavaScript 收藏文章
```javascript
const favoriteArticle = async (articleId) => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/interactions/favorites/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        article: articleId
      })
    });

    const result = await response.json();

    if (result.success) {
      console.log('收藏成功:', result.data);
      // 更新UI状态
      updateFavoriteButton(articleId, true);
      showToast('收藏成功');
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('收藏失败:', error);
    throw error;
  }
};

// 使用示例
document.getElementById('favorite-btn').addEventListener('click', async (event) => {
  const articleId = event.target.dataset.articleId;
  try {
    await favoriteArticle(parseInt(articleId));
  } catch (error) {
    showToast('收藏失败: ' + error.message, 'error');
  }
});
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "收藏成功",
  "data": {
    "id": 23,
    "user": 5,
    "article": 42,
    "article_detail": {
      "id": 42,
      "title": "深入理解Vue.js响应式原理",
      "slug": "vue-reactivity-deep-dive",
      "excerpt": "本文详细介绍Vue.js的响应式系统实现原理...",
      "cover_image": "https://example.com/vue.jpg"
    },
    "user_info": {
      "id": 5,
      "username": "member_user",
      "nick_name": "学习者"
    },
    "tenant": 1,
    "created_at": "2024-01-20T15:45:00Z"
  }
}
```

### 错误响应示例
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "article": ["文章不存在"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

---

## 取消收藏（按收藏ID）

### 接口信息
- **接口地址**: `DELETE /api/v1/interactions/favorites/{id}/`
- **权限要求**: 需要Member用户认证，只能删除自己的收藏
- **功能说明**: 通过收藏记录ID取消收藏

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| id | integer | 是 | 收藏记录ID | 23 | 有效的收藏记录ID |

### 使用示例

#### cURL 命令
```bash
curl -X DELETE "https://your-domain.com/api/v1/interactions/favorites/23/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 取消收藏
```javascript
const unfavoriteArticle = async (favoriteId, articleId) => {
  try {
    const response = await fetch(`https://your-domain.com/api/v1/interactions/favorites/${favoriteId}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    if (response.status === 204) {
      console.log('取消收藏成功');
      // 更新UI状态
      updateFavoriteButton(articleId, false);
      showToast('已取消收藏');
      return true;
    } else {
      const result = await response.json();
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('取消收藏失败:', error);
    throw error;
  }
};
```

### 成功响应
```http
HTTP/1.1 204 No Content
```

---

## 取消收藏（按文章ID）

### 接口信息
- **接口地址**: `DELETE /api/v1/interactions/favorites/by-article/{article_id}/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 通过文章ID取消收藏（如果已收藏）

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|------|----------|
| article_id | integer | 是 | 文章ID | 42 | 有效的文章ID |

### 使用示例

#### cURL 命令
```bash
curl -X DELETE "https://your-domain.com/api/v1/interactions/favorites/by-article/42/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 通过文章ID取消收藏
```javascript
const unfavoriteByArticle = async (articleId) => {
  try {
    const response = await fetch(`https://your-domain.com/api/v1/interactions/favorites/by-article/${articleId}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    if (response.status === 204) {
      console.log('取消收藏成功');
      updateFavoriteButton(articleId, false);
      showToast('已取消收藏');
      return true;
    } else {
      const result = await response.json();
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('取消收藏失败:', error);
    throw error;
  }
};
```

### 成功响应
```http
HTTP/1.1 204 No Content
```

---

## 检查收藏状态

### 接口信息
- **接口地址**: `GET /api/v1/interactions/favorites/check/{article_id}/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 检查当前用户是否已收藏指定文章

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| article_id | integer | 是 | 文章ID | 42 | 有效的文章ID |

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/interactions/favorites/check/42/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 检查收藏状态
```javascript
const checkFavoriteStatus = async (articleId) => {
  try {
    const response = await fetch(`https://your-domain.com/api/v1/interactions/favorites/check/${articleId}/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('收藏状态:', result.data);
      return result.data; // {is_favorited: true/false, favorite_id: 23, created_at: "..."}
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('检查收藏状态失败:', error);
    throw error;
  }
};

// 使用示例 - 初始化页面时检查收藏状态
const initFavoriteButton = async (articleId) => {
  try {
    const status = await checkFavoriteStatus(articleId);
    updateFavoriteButton(articleId, status.is_favorited, status.favorite_id);
  } catch (error) {
    console.warn('检查收藏状态失败:', error);
  }
};
```

### 成功响应 - 已收藏
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "is_favorited": true,
    "favorite_id": 23,
    "created_at": "2024-01-20T15:45:00Z"
  }
}
```

### 成功响应 - 未收藏
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "is_favorited": false,
    "favorite_id": null,
    "created_at": null
  }
}
```

---

## 获取点赞列表

### 接口信息
- **接口地址**: `GET /api/v1/interactions/likes/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 获取当前用户发出的点赞记录列表

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/interactions/likes/?page=1&page_size=10" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取点赞列表
```javascript
const getLikes = async (params = {}) => {
  const queryParams = new URLSearchParams({
    page: params.page || 1,
    page_size: params.pageSize || 20
  });

  try {
    const response = await fetch(`https://your-domain.com/api/v1/interactions/likes/?${queryParams}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('点赞列表:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取点赞列表失败:', error);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 15,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 15,
        "from_member": 5,
        "to_member": 8,
        "from_member_info": {
          "id": 5,
          "username": "member_user",
          "nick_name": "学习者",
          "avatar": "/media/avatars/avatar_5.jpg"
        },
        "to_member_info": {
          "id": 8,
          "username": "expert_user",
          "nick_name": "技术专家",
          "avatar": "/media/avatars/avatar_8.jpg"
        },
        "tenant": 1,
        "created_at": "2024-01-20T14:30:00Z"
      }
    ]
  }
}
```

---

## 点赞用户

### 接口信息
- **接口地址**: `POST /api/v1/interactions/likes/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 点赞指定的用户

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| to_member | integer | 是 | 被点赞的用户ID | 8 | 有效的Member ID，必须在本租户 |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/interactions/likes/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "to_member": 8
  }'
```

#### JavaScript 点赞用户
```javascript
const likeUser = async (targetUserId) => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/interactions/likes/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        to_member: targetUserId
      })
    });

    const result = await response.json();

    if (result.success) {
      console.log('点赞成功:', result.data);
      updateLikeButton(targetUserId, true);
      showToast('点赞成功');
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('点赞失败:', error);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "点赞成功",
  "data": {
    "id": 15,
    "from_member": 5,
    "to_member": 8,
    "from_member_info": {
      "id": 5,
      "username": "member_user",
      "nick_name": "学习者"
    },
    "to_member_info": {
      "id": 8,
      "username": "expert_user",
      "nick_name": "技术专家"
    },
    "tenant": 1,
    "created_at": "2024-01-20T14:30:00Z"
  }
}
```

---

## 获取收到的点赞

### 接口信息
- **接口地址**: `GET /api/v1/interactions/likes/received/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 获取当前用户收到的点赞记录列表

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/interactions/likes/received/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取收到的点赞
```javascript
const getReceivedLikes = async (params = {}) => {
  const queryParams = new URLSearchParams({
    page: params.page || 1,
    page_size: params.pageSize || 20
  });

  try {
    const response = await fetch(`https://your-domain.com/api/v1/interactions/likes/received/?${queryParams}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('收到的点赞:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取收到的点赞失败:', error);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 8,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 16,
        "from_member": 12,
        "to_member": 5,
        "from_member_info": {
          "id": 12,
          "username": "fan_user",
          "nick_name": "忠实粉丝",
          "avatar": "/media/avatars/avatar_12.jpg"
        },
        "to_member_info": {
          "id": 5,
          "username": "member_user",
          "nick_name": "学习者"
        },
        "tenant": 1,
        "created_at": "2024-01-20T16:20:00Z"
      }
    ]
  }
}
```

---

## 检查点赞状态

### 接口信息
- **接口地址**: `GET /api/v1/interactions/likes/check/{member_id}/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 检查当前用户是否已点赞指定用户

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|------|----------|
| member_id | integer | 是 | 用户ID | 8 | 有效的Member ID |

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/interactions/likes/check/8/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 检查点赞状态
```javascript
const checkLikeStatus = async (targetUserId) => {
  try {
    const response = await fetch(`https://your-domain.com/api/v1/interactions/likes/check/${targetUserId}/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('点赞状态:', result.data);
      return result.data; // {is_liked: true/false, like_id: 15, created_at: "..."}
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('检查点赞状态失败:', error);
    throw error;
  }
};
```

### 成功响应 - 已点赞
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "is_liked": true,
    "like_id": 15,
    "created_at": "2024-01-20T14:30:00Z"
  }
}
```

### 成功响应 - 未点赞
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "is_liked": false,
    "like_id": null,
    "created_at": null
  }
}
```

---

## 🔧 前端集成最佳实践

### 1. 互动管理器类
```javascript
class InteractionManager {
  constructor() {
    this.baseURL = 'https://your-domain.com/api/v1';
    this.tenantId = '1';
  }

  // 收藏相关方法
  async getFavorites(params = {}) {
    const queryParams = new URLSearchParams(params);
    return await this.apiRequest(`/interactions/favorites/?${queryParams}`);
  }

  async favoriteArticle(articleId) {
    return await this.apiRequest('/interactions/favorites/', {
      method: 'POST',
      body: JSON.stringify({ article: articleId })
    });
  }

  async unfavoriteArticle(favoriteId) {
    const response = await fetch(`${this.baseURL}/interactions/favorites/${favoriteId}/`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    return response.status === 204;
  }

  async unfavoriteByArticle(articleId) {
    const response = await fetch(`${this.baseURL}/interactions/favorites/by-article/${articleId}/`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    return response.status === 204;
  }

  async checkFavoriteStatus(articleId) {
    return await this.apiRequest(`/interactions/favorites/check/${articleId}/`);
  }

  // 点赞相关方法
  async getLikes(params = {}) {
    const queryParams = new URLSearchParams(params);
    return await this.apiRequest(`/interactions/likes/?${queryParams}`);
  }

  async likeUser(targetUserId) {
    return await this.apiRequest('/interactions/likes/', {
      method: 'POST',
      body: JSON.stringify({ to_member: targetUserId })
    });
  }

  async unlikeUser(likeId) {
    const response = await fetch(`${this.baseURL}/interactions/likes/${likeId}/`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    return response.status === 204;
  }

  async unlikeByUser(targetUserId) {
    const response = await fetch(`${this.baseURL}/interactions/likes/by-member/${targetUserId}/`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    return response.status === 204;
  }

  async getReceivedLikes(params = {}) {
    const queryParams = new URLSearchParams(params);
    return await this.apiRequest(`/interactions/likes/received/?${queryParams}`);
  }

  async checkLikeStatus(targetUserId) {
    return await this.apiRequest(`/interactions/likes/check/${targetUserId}/`);
  }

  // 关注相关方法（如果有实现）
  async getFollows(params = {}) {
    const queryParams = new URLSearchParams(params);
    return await this.apiRequest(`/interactions/follows/?${queryParams}`);
  }

  async followUser(targetUserId) {
    return await this.apiRequest('/interactions/follows/', {
      method: 'POST',
      body: JSON.stringify({ to_member: targetUserId })
    });
  }

  async unfollowUser(followId) {
    const response = await fetch(`${this.baseURL}/interactions/follows/${followId}/`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    return response.status === 204;
  }

  async checkFollowStatus(targetUserId) {
    return await this.apiRequest(`/interactions/follows/check/${targetUserId}/`);
  }

  // 通用API请求方法
  async apiRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
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
const interactionManager = new InteractionManager();
```

### 2. 收藏按钮组件
```javascript
class FavoriteButton {
  constructor(buttonElement, articleId) {
    this.button = buttonElement;
    this.articleId = articleId;
    this.interactionManager = new InteractionManager();
    this.isFavorited = false;
    this.favoriteId = null;

    this.init();
  }

  async init() {
    // 检查初始收藏状态
    try {
      const status = await this.interactionManager.checkFavoriteStatus(this.articleId);
      this.updateStatus(status.is_favorited, status.favorite_id);
    } catch (error) {
      console.warn('检查收藏状态失败:', error);
    }

    // 绑定点击事件
    this.button.addEventListener('click', () => this.toggleFavorite());
  }

  updateStatus(isFavorited, favoriteId = null) {
    this.isFavorited = isFavorited;
    this.favoriteId = favoriteId;

    // 更新按钮样式和文本
    if (isFavorited) {
      this.button.classList.add('favorited');
      this.button.innerHTML = '❤️ 已收藏';
    } else {
      this.button.classList.remove('favorited');
      this.button.innerHTML = '🤍 收藏';
    }
  }

  async toggleFavorite() {
    try {
      this.button.disabled = true;

      if (this.isFavorited) {
        // 取消收藏
        const success = await this.interactionManager.unfavoriteByArticle(this.articleId);
        if (success) {
          this.updateStatus(false, null);
          showToast('已取消收藏');
        }
      } else {
        // 添加收藏
        const result = await this.interactionManager.favoriteArticle(this.articleId);
        this.updateStatus(true, result.data.id);
        showToast('收藏成功');
      }
    } catch (error) {
      showToast('操作失败: ' + error.message, 'error');
    } finally {
      this.button.disabled = false;
    }
  }
}

// 初始化收藏按钮
document.addEventListener('DOMContentLoaded', () => {
  const favoriteBtn = document.getElementById('favorite-btn');
  const articleId = favoriteBtn.dataset.articleId;

  if (favoriteBtn && articleId) {
    new FavoriteButton(favoriteBtn, parseInt(articleId));
  }
});
```

### 3. 点赞按钮组件
```javascript
class LikeButton {
  constructor(buttonElement, targetUserId) {
    this.button = buttonElement;
    this.targetUserId = targetUserId;
    this.interactionManager = new InteractionManager();
    this.isLiked = false;
    this.likeId = null;

    this.init();
  }

  async init() {
    // 检查初始点赞状态
    try {
      const status = await this.interactionManager.checkLikeStatus(this.targetUserId);
      this.updateStatus(status.is_liked, status.like_id);
    } catch (error) {
      console.warn('检查点赞状态失败:', error);
    }

    // 绑定点击事件
    this.button.addEventListener('click', () => this.toggleLike());
  }

  updateStatus(isLiked, likeId = null) {
    this.isLiked = isLiked;
    this.likeId = likeId;

    // 更新按钮样式和文本
    const likeCountElement = this.button.querySelector('.like-count');

    if (isLiked) {
      this.button.classList.add('liked');
      this.button.innerHTML = `👍 已点赞 ${likeCountElement ? likeCountElement.textContent : ''}`;
    } else {
      this.button.classList.remove('liked');
      this.button.innerHTML = `👍 点赞 ${likeCountElement ? likeCountElement.textContent : ''}`;
    }
  }

  async toggleLike() {
    try {
      this.button.disabled = true;

      if (this.isLiked) {
        // 取消点赞
        const success = await this.interactionManager.unlikeByUser(this.targetUserId);
        if (success) {
          this.updateStatus(false, null);
          showToast('已取消点赞');
          // 更新点赞计数
          this.updateLikeCount(-1);
        }
      } else {
        // 点赞
        const result = await this.interactionManager.likeUser(this.targetUserId);
        this.updateStatus(true, result.data.id);
        showToast('点赞成功');
        // 更新点赞计数
        this.updateLikeCount(1);
      }
    } catch (error) {
      showToast('操作失败: ' + error.message, 'error');
    } finally {
      this.button.disabled = false;
    }
  }

  updateLikeCount(delta) {
    const countElement = this.button.querySelector('.like-count');
    if (countElement) {
      const currentCount = parseInt(countElement.textContent) || 0;
      countElement.textContent = Math.max(0, currentCount + delta);
    }
  }
}

// 初始化点赞按钮
document.addEventListener('DOMContentLoaded', () => {
  // 为所有点赞按钮初始化
  document.querySelectorAll('.like-btn').forEach(btn => {
    const targetUserId = btn.dataset.userId;
    if (targetUserId) {
      new LikeButton(btn, parseInt(targetUserId));
    }
  });
});
```

### 4. 互动统计面板
```javascript
class InteractionStats {
  constructor(container) {
    this.container = container;
    this.interactionManager = new InteractionManager();
    this.stats = {
      favorites: 0,
      likesGiven: 0,
      likesReceived: 0,
      follows: 0
    };
  }

  async loadStats() {
    try {
      this.showLoading();

      // 并行加载各种统计数据
      const [favorites, likes, receivedLikes, follows] = await Promise.all([
        this.interactionManager.getFavorites({ page_size: 1 }), // 只获取总数
        this.interactionManager.getLikes({ page_size: 1 }),
        this.interactionManager.getReceivedLikes({ page_size: 1 }),
        this.interactionManager.getFollows ? this.interactionManager.getFollows({ page_size: 1 }) : Promise.resolve({ data: { count: 0 } })
      ]);

      this.stats = {
        favorites: favorites.data.count,
        likesGiven: likes.data.count,
        likesReceived: receivedLikes.data.count,
        follows: follows.data.count
      };

      this.renderStats();

    } catch (error) {
      console.error('加载统计数据失败:', error);
      this.showError(error.message);
    } finally {
      this.hideLoading();
    }
  }

  renderStats() {
    const html = `
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-icon">⭐</div>
          <div class="stat-content">
            <div class="stat-number">${this.stats.favorites}</div>
            <div class="stat-label">收藏文章</div>
          </div>
        </div>

        <div class="stat-item">
          <div class="stat-icon">👍</div>
          <div class="stat-content">
            <div class="stat-number">${this.stats.likesGiven}</div>
            <div class="stat-label">发出点赞</div>
          </div>
        </div>

        <div class="stat-item">
          <div class="stat-icon">❤️</div>
          <div class="stat-content">
            <div class="stat-number">${this.stats.likesReceived}</div>
            <div class="stat-label">收到点赞</div>
          </div>
        </div>

        ${this.stats.follows !== undefined ? `
        <div class="stat-item">
          <div class="stat-icon">👥</div>
          <div class="stat-content">
            <div class="stat-number">${this.stats.follows}</div>
            <div class="stat-label">关注用户</div>
          </div>
        </div>
        ` : ''}
      </div>
    `;

    this.container.innerHTML = html;
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

// 初始化统计面板
document.addEventListener('DOMContentLoaded', () => {
  const statsContainer = document.getElementById('interaction-stats');
  if (statsContainer) {
    const stats = new InteractionStats(statsContainer);
    stats.loadStats();
  }
});
```
