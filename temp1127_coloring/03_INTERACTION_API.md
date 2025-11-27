# Lipeaks Coloring - 用户互动 API 文档

> 适用于用户点赞、关注、收藏、文章点赞功能
> 基础URL: `http://localhost:8000`
> 通用Headers:
> - `Authorization: Bearer {token}` (必须)
> - `X-Tenant-ID: {租户ID}` (必须)

---

## 一、用户点赞功能 (6个接口)

### 1. 获取我点赞的用户列表

**接口**: `GET /api/v1/interactions/likes/?page={page}`

**描述**: 获取当前用户点赞的其他用户列表

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认10 |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/likes/?page=1" \
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
      "count": 1,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 1,
        "from_member": 12,
        "to_member": 5,
        "from_member_info": {
          "id": 12,
          "username": "7548155",
          "nick_name": "Whahaha",
          "avatar": "http://localhost:8000/media/avatars/xxx.jpg"
        },
        "to_member_info": {
          "id": 5,
          "username": "Aaahghjkj",
          "nick_name": null,
          "avatar": "http://localhost:8000/media/avatars/xxx.png"
        },
        "tenant": 3,
        "created_at": "2025-11-27T11:30:21.352534Z"
      }
    ]
  }
}
```

---

### 2. 点赞用户

**接口**: `POST /api/v1/interactions/likes/`

**描述**: 给指定用户点赞

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| to_member | integer | 是 | 被点赞用户ID |

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/interactions/likes/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{"to_member": 5}'
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "to_member": 5
  }
}
```

### 业务规则
- 不能点赞自己
- 不能重复点赞同一用户
- 只能点赞本租户内的用户

---

### 3. 取消点赞（通过点赞ID）

**接口**: `DELETE /api/v1/interactions/likes/{likeId}/`

**描述**: 通过点赞记录ID取消点赞

### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| likeId | integer | 点赞记录ID |

### curl 示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/interactions/likes/1/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

### 成功响应
HTTP状态码: 204 No Content

---

### 4. 取消点赞（通过用户ID）

**接口**: `DELETE /api/v1/interactions/likes/by-member/{memberId}/`

**描述**: 通过被点赞用户ID取消点赞（便捷方法）

### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| memberId | integer | 被点赞用户ID |

### curl 示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/interactions/likes/by-member/5/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

### 成功响应
HTTP状态码: 204 No Content

---

### 5. 获取收到的点赞列表

**接口**: `GET /api/v1/interactions/likes/received/?page={page}`

**描述**: 获取其他用户给当前用户的点赞列表

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/likes/received/?page=1" \
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
    "pagination": {...},
    "results": [
      {
        "id": 2,
        "from_member": 5,
        "to_member": 12,
        "from_member_info": {...},
        "to_member_info": {...},
        "tenant": 3,
        "created_at": "2025-11-27T11:30:21.352534Z"
      }
    ]
  }
}
```

---

### 6. 检查是否已点赞用户

**接口**: `GET /api/v1/interactions/likes/check/{memberId}/`

**描述**: 检查当前用户是否已点赞指定用户

### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| memberId | integer | 目标用户ID |

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/likes/check/5/" \
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
    "is_liked": true,
    "like_id": 1,
    "created_at": "2025-11-27T11:30:21.352534Z"
  }
}
```

---

## 二、关注功能 (8个接口)

### 1. 获取我的关注列表

**接口**: `GET /api/v1/interactions/follows/?page={page}`

**描述**: 获取当前用户关注的用户列表

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/follows/?page=1" \
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
    "pagination": {...},
    "results": [
      {
        "id": 1,
        "follower": 12,
        "following": 5,
        "follower_info": {
          "id": 12,
          "username": "7548155",
          "nick_name": "Whahaha",
          "avatar": "http://localhost:8000/media/avatars/xxx.jpg"
        },
        "following_info": {
          "id": 5,
          "username": "Aaahghjkj",
          "nick_name": null,
          "avatar": "http://localhost:8000/media/avatars/xxx.png"
        },
        "is_mutual": false,
        "tenant": 3,
        "created_at": "2025-11-27T11:31:21.132497Z"
      }
    ]
  }
}
```

---

### 2. 关注用户

**接口**: `POST /api/v1/interactions/follows/`

**描述**: 关注指定用户

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| following | integer | 是 | 被关注用户ID |

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/interactions/follows/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{"following": 5}'
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "following": 5
  }
}
```

---

### 3. 取消关注（通过关注ID）

**接口**: `DELETE /api/v1/interactions/follows/{followId}/`

### curl 示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/interactions/follows/1/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 4. 取消关注（通过用户ID）

**接口**: `DELETE /api/v1/interactions/follows/by-member/{memberId}/`

### curl 示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/interactions/follows/by-member/5/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 5. 获取粉丝列表

**接口**: `GET /api/v1/interactions/follows/followers/?page={page}`

**描述**: 获取关注当前用户的粉丝列表

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/follows/followers/?page=1" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 6. 获取互相关注列表

**接口**: `GET /api/v1/interactions/follows/mutual/?page={page}`

**描述**: 获取互相关注的用户列表

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/follows/mutual/?page=1" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 7. 获取关注统计信息

**接口**: `GET /api/v1/interactions/follows/stats/`

**描述**: 获取当前用户的关注/粉丝/互关数量统计

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/follows/stats/" \
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
    "following_count": 1,
    "followers_count": 0,
    "mutual_count": 0
  }
}
```

---

### 8. 检查是否已关注用户

**接口**: `GET /api/v1/interactions/follows/check/{memberId}/`

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/follows/check/5/" \
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
    "is_following": true,
    "follow_id": 1,
    "is_mutual": false,
    "created_at": "2025-11-27T11:31:21.132497Z"
  }
}
```

---

## 三、收藏功能 (5个接口)

> **注意**: 收藏功能API目前仅支持管理员(User)使用，Member用户会返回500错误。如需Member用户收藏功能，请使用文章点赞API替代。

### 1. 获取收藏列表

**接口**: `GET /api/v1/interactions/favorites/?page={page}`

### 2. 收藏文章

**接口**: `POST /api/v1/interactions/favorites/`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| article | integer | 是 | 文章ID |

### 3. 取消收藏（通过收藏ID）

**接口**: `DELETE /api/v1/interactions/favorites/{favoriteId}/`

### 4. 取消收藏（通过文章ID）

**接口**: `DELETE /api/v1/interactions/favorites/by-article/{articleId}/`

### 5. 检查是否已收藏文章

**接口**: `GET /api/v1/interactions/favorites/check/{articleId}/`

---

## 四、文章点赞功能 (6个接口)

### 1. 获取我点赞的文章列表

**接口**: `GET /api/v1/interactions/article-likes/?page={page}`

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/article-likes/?page=1" \
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
    "pagination": {...},
    "results": [
      {
        "id": 14,
        "from_member": 12,
        "article": 10326,
        "article_detail": {
          "id": 10326,
          "title": "我的填色作品 - 31.png",
          "slug": "31png",
          "excerpt": "填色作品：31.png",
          "cover_image": "http://localhost:8000/media/uploads/xxx.jpg",
          "cover_image_small": "http://localhost:8000/media/uploads/xxx_small.jpg",
          ...
        },
        "from_member_info": {
          "id": 12,
          "username": "7548155",
          "nick_name": "Whahaha",
          "avatar": "..."
        },
        "tenant": 3,
        "created_at": "2025-11-27T05:52:15.800353Z",
        "ip_address": "192.168.1.16",
        "user_agent": "..."
      }
    ]
  }
}
```

---

### 2. 点赞文章

**接口**: `POST /api/v1/interactions/article-likes/`

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| article | integer | 是 | 文章ID |

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/interactions/article-likes/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{"article": 10326}'
```

---

### 3. 取消点赞（通过点赞ID）

**接口**: `DELETE /api/v1/interactions/article-likes/{likeId}/`

### curl 示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/interactions/article-likes/14/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 4. 取消点赞（通过文章ID）

**接口**: `DELETE /api/v1/interactions/article-likes/by-article/{articleId}/`

### curl 示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/interactions/article-likes/by-article/10326/" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

### 5. 检查是否已点赞文章

**接口**: `GET /api/v1/interactions/article-likes/check/{articleId}/`

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/article-likes/check/10326/" \
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
    "is_liked": true,
    "like_id": 14,
    "created_at": "2025-11-27T05:52:15.800353Z"
  }
}
```

---

### 6. 获取文章的点赞用户列表

**接口**: `GET /api/v1/interactions/article-likes/by-article/{articleId}/likers/?page={page}`

**描述**: 获取点赞指定文章的用户列表

### curl 示例
```bash
curl -X GET "http://localhost:8000/api/v1/interactions/article-likes/by-article/10326/likers/?page=1" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3"
```

---

## 错误响应说明

| code | message | 说明 |
|------|---------|------|
| 4000 | 数据验证失败 | 验证失败，如已点赞、点赞自己等 |
| 4004 | Not Found | 记录不存在 |
| 5000 | 服务器内部错误 | 服务端异常 |
