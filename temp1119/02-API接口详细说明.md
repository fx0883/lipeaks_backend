# API 接口详细说明

## 📚 目录
- [1. 点赞文章](#1-点赞文章)
- [2. 取消点赞（通过记录ID）](#2-取消点赞通过记录id)
- [3. 取消点赞（通过文章ID）](#3-取消点赞通过文章id)
- [4. 检查点赞状态](#4-检查点赞状态)
- [5. 获取我点赞的文章列表](#5-获取我点赞的文章列表)
- [6. 获取文章的点赞用户列表](#6-获取文章的点赞用户列表)

---

## 1. 点赞文章

### 基本信息
- **接口路径**: `/api/v1/interactions/article-likes/`
- **请求方法**: `POST`
- **权限要求**: 需要 Member 用户登录
- **功能说明**: 对指定文章进行点赞操作

### 请求参数

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer Token，格式：`Bearer {access_token}` |
| X-Tenant-ID | string | 是 | 租户 ID |
| Content-Type | string | 是 | 固定值：`application/json` |

#### Body (JSON)
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| article | integer | 是 | 文章 ID |

### 请求示例

```bash
curl -X POST 'http://localhost:8000/api/v1/interactions/article-likes/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Tenant-ID: 1' \
  -H 'Content-Type: application/json' \
  -d '{
    "article": 100
  }'
```

```javascript
// JavaScript (Fetch API)
const response = await fetch('http://localhost:8000/api/v1/interactions/article-likes/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'X-Tenant-ID': '1',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    article: 100
  })
});
const data = await response.json();
```

```python
# Python (requests)
import requests

response = requests.post(
    'http://localhost:8000/api/v1/interactions/article-likes/',
    headers={
        'Authorization': f'Bearer {access_token}',
        'X-Tenant-ID': '1',
        'Content-Type': 'application/json'
    },
    json={
        'article': 100
    }
)
data = response.json()
```

### 响应示例

#### 成功响应 (201 Created)
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 45,
    "from_member": 5,
    "article": 100,
    "article_detail": {
      "id": 100,
      "title": "深入理解Python装饰器",
      "slug": "python-decorators",
      "excerpt": "本文详细介绍Python装饰器的原理和应用...",
      "cover_image": "https://example.com/python.jpg",
      "author_info": {
        "id": 8,
        "username": "author"
      },
      "status": "published",
      "views_count": 1250,
      "likes_count": 43
    },
    "from_member_info": {
      "id": 5,
      "username": "member_user",
      "nick_name": "普通用户",
      "avatar": "https://example.com/avatar1.jpg"
    },
    "tenant": 1,
    "created_at": "2024-01-20T10:30:00.123456Z",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
  }
}
```

#### 错误响应

**重复点赞 (400 Bad Request)**
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "article": ["您已经点赞过这篇文章"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

**文章不存在或不属于当前租户 (400 Bad Request)**
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "article": ["您无法点赞其他租户的文章"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

**未认证 (401 Unauthorized)**
```json
{
  "success": false,
  "code": 4010,
  "message": "未认证",
  "error_code": "AUTHENTICATION_FAILED"
}
```

**权限不足 (403 Forbidden)**
```json
{
  "success": false,
  "code": 4030,
  "message": "只有Member用户可以点赞文章",
  "error_code": "PERMISSION_DENIED"
}
```

---

## 2. 取消点赞（通过记录ID）

### 基本信息
- **接口路径**: `/api/v1/interactions/article-likes/{id}/`
- **请求方法**: `DELETE`
- **权限要求**: 需要 Member 用户登录
- **功能说明**: 通过点赞记录 ID 取消点赞

### 请求参数

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer Token |
| X-Tenant-ID | string | 是 | 租户 ID |

#### Path Parameters
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 点赞记录 ID |

### 请求示例

```bash
curl -X DELETE 'http://localhost:8000/api/v1/interactions/article-likes/45/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Tenant-ID: 1'
```

```javascript
// JavaScript
const response = await fetch('http://localhost:8000/api/v1/interactions/article-likes/45/', {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'X-Tenant-ID': '1'
  }
});
```

### 响应示例

#### 成功响应 (204 No Content)
```
HTTP/1.1 204 No Content
```

#### 错误响应

**记录不存在 (404 Not Found)**
```json
{
  "success": false,
  "code": 4040,
  "message": "未找到",
  "error_code": "NOT_FOUND"
}
```

**权限不足（尝试删除别人的点赞）(403 Forbidden)**
```json
{
  "success": false,
  "code": 4030,
  "message": "您没有权限执行此操作",
  "error_code": "PERMISSION_DENIED"
}
```

---

## 3. 取消点赞（通过文章ID）

### 基本信息
- **接口路径**: `/api/v1/interactions/article-likes/by-article/{article_id}/`
- **请求方法**: `DELETE`
- **权限要求**: 需要 Member 用户登录
- **功能说明**: 通过文章 ID 取消点赞（便捷方法，无需知道点赞记录 ID）

### 请求参数

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer Token |
| X-Tenant-ID | string | 是 | 租户 ID |

#### Path Parameters
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| article_id | integer | 是 | 文章 ID |

### 请求示例

```bash
curl -X DELETE 'http://localhost:8000/api/v1/interactions/article-likes/by-article/100/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Tenant-ID: 1'
```

```javascript
// JavaScript
const response = await fetch(
  `http://localhost:8000/api/v1/interactions/article-likes/by-article/${articleId}/`,
  {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-ID': '1'
    }
  }
);
```

### 响应示例

#### 成功响应 (204 No Content)
```json
{
  "success": true,
  "code": 2000,
  "message": "已取消点赞"
}
```

#### 错误响应

**未点赞该文章 (404 Not Found)**
```json
{
  "success": false,
  "code": 4040,
  "message": "未找到点赞记录",
  "error_code": "NOT_FOUND"
}
```

---

## 4. 检查点赞状态

### 基本信息
- **接口路径**: `/api/v1/interactions/article-likes/check/{article_id}/`
- **请求方法**: `GET`
- **权限要求**: 需要 Member 用户登录
- **功能说明**: 检查当前用户是否已点赞指定文章

### 请求参数

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer Token |
| X-Tenant-ID | string | 是 | 租户 ID |

#### Path Parameters
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| article_id | integer | 是 | 文章 ID |

### 请求示例

```bash
curl -X GET 'http://localhost:8000/api/v1/interactions/article-likes/check/100/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Tenant-ID: 1'
```

```javascript
// JavaScript
const response = await fetch(
  `http://localhost:8000/api/v1/interactions/article-likes/check/${articleId}/`,
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-ID': '1'
    }
  }
);
const data = await response.json();
```

### 响应示例

#### 已点赞 (200 OK)
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "is_liked": true,
    "like_id": 45,
    "created_at": "2024-01-20T10:30:00.123456Z"
  }
}
```

#### 未点赞 (200 OK)
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "is_liked": false,
    "like_id": null,
    "created_at": null
  }
}
```

#### 错误响应

**文章不存在 (404 Not Found)**
```json
{
  "success": false,
  "code": 4040,
  "message": "文章不存在",
  "error_code": "NOT_FOUND"
}
```

---

## 5. 获取我点赞的文章列表

### 基本信息
- **接口路径**: `/api/v1/interactions/article-likes/`
- **请求方法**: `GET`
- **权限要求**: 需要 Member 用户登录
- **功能说明**: 获取当前用户点赞的所有文章列表

### 请求参数

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer Token |
| X-Tenant-ID | string | 是 | 租户 ID |

#### Query Parameters
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 10 | 每页数量（最大100） |

### 请求示例

```bash
curl -X GET 'http://localhost:8000/api/v1/interactions/article-likes/?page=1&page_size=10' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Tenant-ID: 1'
```

```javascript
// JavaScript
const response = await fetch(
  'http://localhost:8000/api/v1/interactions/article-likes/?page=1&page_size=10',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-ID': '1'
    }
  }
);
const data = await response.json();
```

### 响应示例

#### 成功响应 (200 OK)
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 25,
      "next": "http://api.example.com/api/v1/interactions/article-likes/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 3
    },
    "results": [
      {
        "id": 45,
        "from_member": 5,
        "article": 100,
        "article_detail": {
          "id": 100,
          "title": "深入理解Python装饰器",
          "slug": "python-decorators",
          "excerpt": "本文详细介绍Python装饰器的原理和应用...",
          "cover_image": "https://example.com/python.jpg",
          "cover_image_small": "https://example.com/python_small.jpg",
          "author_info": {
            "id": 8,
            "username": "author",
            "nick_name": "作者昵称",
            "avatar": "https://example.com/author_avatar.jpg"
          },
          "author_type": "member",
          "status": "published",
          "is_featured": false,
          "is_pinned": false,
          "published_at": "2024-01-15T08:00:00Z",
          "created_at": "2024-01-15T08:00:00Z",
          "updated_at": "2024-01-18T12:00:00Z",
          "categories": [
            {
              "id": 5,
              "name": "Python",
              "slug": "python"
            }
          ],
          "tags": [
            {
              "id": 10,
              "name": "装饰器",
              "slug": "decorator"
            }
          ],
          "comments_count": 15,
          "likes_count": 43,
          "views_count": 1250
        },
        "from_member_info": {
          "id": 5,
          "username": "member_user",
          "nick_name": "普通用户",
          "avatar": "https://example.com/avatar1.jpg"
        },
        "tenant": 1,
        "created_at": "2024-01-20T10:30:00.123456Z",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0..."
      }
      // ... 更多点赞记录
    ]
  }
}
```

---

## 6. 获取文章的点赞用户列表

### 基本信息
- **接口路径**: `/api/v1/interactions/article-likes/by-article/{article_id}/likers/`
- **请求方法**: `GET`
- **权限要求**: 需要 Member 用户登录
- **功能说明**: 获取指定文章的所有点赞用户列表

### 请求参数

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer Token |
| X-Tenant-ID | string | 是 | 租户 ID |

#### Path Parameters
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| article_id | integer | 是 | 文章 ID |

#### Query Parameters
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 10 | 每页数量 |

### 请求示例

```bash
curl -X GET 'http://localhost:8000/api/v1/interactions/article-likes/by-article/100/likers/?page=1' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Tenant-ID: 1'
```

```javascript
// JavaScript
const response = await fetch(
  `http://localhost:8000/api/v1/interactions/article-likes/by-article/${articleId}/likers/?page=1`,
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-ID': '1'
    }
  }
);
const data = await response.json();
```

### 响应示例

#### 成功响应 (200 OK)
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 43,
      "next": "http://api.example.com/api/v1/interactions/article-likes/by-article/100/likers/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 5
    },
    "results": [
      {
        "id": 45,
        "from_member": 5,
        "from_member_info": {
          "id": 5,
          "username": "member_user1",
          "nick_name": "用户1",
          "avatar": "https://example.com/avatar1.jpg"
        },
        "tenant": 1,
        "created_at": "2024-01-20T10:30:00.123456Z",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0..."
      },
      {
        "id": 46,
        "from_member": 8,
        "from_member_info": {
          "id": 8,
          "username": "member_user2",
          "nick_name": "用户2",
          "avatar": "https://example.com/avatar2.jpg"
        },
        "tenant": 1,
        "created_at": "2024-01-20T11:15:00.456789Z",
        "ip_address": "192.168.1.101",
        "user_agent": "Mozilla/5.0..."
      }
      // ... 更多点赞用户
    ]
  }
}
```

#### 错误响应

**文章不存在 (404 Not Found)**
```json
{
  "success": false,
  "code": 4040,
  "message": "文章不存在",
  "error_code": "NOT_FOUND"
}
```

---

## 📝 通用说明

### 分页参数
所有列表接口都支持分页：
- `page`: 页码，从 1 开始
- `page_size`: 每页数量，默认 10，最大 100

### 响应中的分页信息
```json
{
  "pagination": {
    "count": 25,           // 总记录数
    "next": "...",         // 下一页 URL（null 表示没有下一页）
    "previous": "...",     // 上一页 URL（null 表示没有上一页）
    "page_size": 10,       // 每页数量
    "current_page": 1,     // 当前页码
    "total_pages": 3       // 总页数
  }
}
```

### 日期时间格式
所有日期时间字段使用 ISO 8601 格式：
- 格式：`YYYY-MM-DDTHH:MM:SS.ffffffZ`
- 时区：UTC
- 示例：`2024-01-20T10:30:00.123456Z`

### HTTP 状态码
| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无内容返回） |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

---

**更新日期**: 2024-11-19  
**版本**: v1.0
