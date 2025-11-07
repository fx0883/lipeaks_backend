# Member 互动 API（统一响应版）

## 适用范围
- 面向 iOS / Android / 鸿蒙 / Web / 小程序等所有客户端。
- 仅提供平台无关的字段与示例，不包含语言/框架代码。

## 统一返回结构
- 参见 `docs/api_response/01_response_format_standard.md`。
- 响应：success, code, message, data[, error_code]；分页：data.pagination + data.results。

## 基础信息
- 前缀：`/api/v1/interactions/`
- Header：
  - Authorization: Bearer <access_token>
  - X-Tenant-ID: <租户ID>（Member 必须）
- 仅 Member 用户可进行点赞/关注等人与人互动；管理员用户不适用。

---

## 一、文章收藏（favorites）

### 1. 获取我的收藏列表
- 路径：GET `/api/v1/interactions/favorites/`
- 查询：page, page_size
- 成功（200，分页）：
{
  "success": true, "code": 2000, "message": "查询成功",
  "data": {"pagination": {...}, "results": [
    {
      "id": 23,
      "user": 5,
      "article": 42,
      "article_detail": {"id": 42, "title": "...", "cover_image": "...", ...},
      "user_info": {"id": 5, "username": "member_user"},
      "tenant": 1,
      "created_at": "2024-01-20T10:30:00Z"
    }
  ]}
}

### 2. 收藏文章
- 路径：POST `/api/v1/interactions/favorites/`
- 请求体：`article`(int, 必填)
- 成功（201）：返回收藏记录详情。
- 失败（400）：
  - 文章不属于当前租户
  - 已收藏

### 3. 取消收藏（按收藏ID）
- 路径：DELETE `/api/v1/interactions/favorites/<id>/`
- 成功（204）：`data=null`；仅能删除自己的收藏记录。

### 4. 取消收藏（按文章ID）
- 路径：DELETE `/api/v1/interactions/favorites/by-article/<article_id>/`
- 成功（204）：`data=null`；记录不存在则返回 404。

### 5. 检查是否已收藏
- 路径：GET `/api/v1/interactions/favorites/check/<article_id>/`
- 成功（200）：
{
  "success": true, "code": 2000, "message": "查询成功",
  "data": {"is_favorited": true, "favorite_id": 23, "created_at": "2024-01-20T10:30:00Z"}
}

---

## 二、用户点赞（likes）

### 1. 获取我点赞的用户列表
- 路径：GET `/api/v1/interactions/likes/`
- 查询：page, page_size
- 成功（200，分页）：`results[].from_member_info`（我）、`results[].to_member_info`（对方）。

### 2. 点赞用户
- 路径：POST `/api/v1/interactions/likes/`
- 请求体：`to_member`(int, 必填)
- 规则：只能点赞本租户用户；不能点赞自己；不可重复点赞。
- 成功（201）：返回点赞记录详情。

### 3. 取消点赞（按记录ID）
- 路径：DELETE `/api/v1/interactions/likes/<id>/`
- 成功（204）：`data=null`；仅能删除自己发起的记录。

### 4. 取消点赞（按用户ID）
- 路径：DELETE `/api/v1/interactions/likes/by-member/<member_id>/`
- 成功（204）：`data=null`；未点赞则 404。

### 5. 获取收到的点赞列表
- 路径：GET `/api/v1/interactions/likes/received/`
- 成功（200，分页）：返回点赞我（to_member=我）的记录列表。

### 6. 检查是否已点赞用户
- 路径：GET `/api/v1/interactions/likes/check/<member_id>/`
- 成功（200）：
{
  "success": true, "code": 2000, "message": "查询成功",
  "data": {"is_liked": true, "like_id": 15, "created_at": "2024-01-20T10:30:00Z"}
}

---

## 三、用户关注（follows）

### 1. 获取我的关注列表
- 路径：GET `/api/v1/interactions/follows/`
- 查询：page, page_size
- 成功（200，分页）：`results[].follower_info`（我）、`results[].following_info`（对方）、`is_mutual`。

### 2. 关注用户
- 路径：POST `/api/v1/interactions/follows/`
- 请求体：`following`(int, 必填)
- 规则：只能关注本租户用户；不能关注自己；不可重复关注。
- 成功（201）：返回关注记录详情（可能立即 `is_mutual=true`）。

### 3. 取消关注（按记录ID）
- 路径：DELETE `/api/v1/interactions/follows/<id>/`
- 成功（204）：`data=null`；仅能删除自己发起的记录。

### 4. 取消关注（按用户ID）
- 路径：DELETE `/api/v1/interactions/follows/by-member/<member_id>/`
- 成功（204）：`data=null`；未关注则 404。

### 5. 获取粉丝列表
- 路径：GET `/api/v1/interactions/follows/followers/`
- 成功（200，分页）：`results[].follower_info`（粉丝）、`results[].following_info`（我）、`is_mutual`。

### 6. 检查是否已关注用户
- 路径：GET `/api/v1/interactions/follows/check/<member_id>/`
- 成功（200）：
{
  "success": true, "code": 2000, "message": "查询成功",
  "data": {"is_following": true, "follow_id": 30, "is_mutual": true, "created_at": "2024-01-20T11:00:00Z"}
}

### 7. 获取互相关注列表
- 路径：GET `/api/v1/interactions/follows/mutual/`
- 成功（200，分页）：仅包含互相关注的记录。

### 8. 获取关注统计
- 路径：GET `/api/v1/interactions/follows/stats/`
- 成功（200）：
{
  "success": true, "code": 2000, "message": "查询成功",
  "data": {"following_count": 15, "followers_count": 25, "mutual_count": 10}
}

---

## 错误与权限（通用）
- 未认证：`4001/AUTH_NOT_AUTHENTICATED`
- 权限不足：`4003/AUTH_PERMISSION_DENIED`
- 资源不存在：`4004/NOT_FOUND`
- 校验错误：`4000/VALIDATION_ERROR`
- 服务器错误：`5000/INTERNAL_SERVER_ERROR`

## 多租户要点
- 所有互动均基于当前租户隔离；跨租户对象将返回校验错误。
- `X-Tenant-ID` 必须与登录用户租户一致。

## 客户端集成要点（平台无关）
- 统一解析响应：先 `success` 再 `code/message`；从 `data` 取业务值。
- 列表页统一读取 `data.pagination + data.results`。
- 取消/删除类接口为幂等；UI 状态应根据 `is_*` 检查接口自洽更新。

## 示例返回（统一响应）

### 收藏列表 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {"count": 1, "next": null, "previous": null, "page_size": 20, "current_page": 1, "total_pages": 1},
    "results": [
      {
        "id": 23,
        "user": 5,
        "article": 42,
        "article_detail": {"id": 42, "title": "深入理解Python装饰器", "slug": "python-decorators", "cover_image": "https://example.com/python.jpg"},
        "user_info": {"id": 5, "username": "member_user"},
        "tenant": 1,
        "created_at": "2024-01-20T10:30:00Z"
      }
    ]
  }
}

### 收藏文章 201
{
  "success": true,
  "code": 2000,
  "message": "收藏成功",
  "data": {
    "id": 23,
    "user": 5,
    "article": 42,
    "article_detail": {"id": 42, "title": "深入理解Python装饰器"},
    "tenant": 1,
    "created_at": "2024-01-20T10:30:00Z"
  }
}

### 检查是否收藏 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {"is_favorited": true, "favorite_id": 23, "created_at": "2024-01-20T10:30:00Z"}
}

### 我点赞的列表 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {"count": 1, "next": null, "previous": null, "page_size": 20, "current_page": 1, "total_pages": 1},
    "results": [
      {"id": 15, "from_member": 5, "to_member": 8, "from_member_info": {"id": 5, "username": "member_user"}, "to_member_info": {"id": 8, "username": "another_member"}, "tenant": 1, "created_at": "2024-01-20T10:30:00Z"}
    ]
  }
}

### 点赞用户 201
{
  "success": true,
  "code": 2000,
  "message": "点赞成功",
  "data": {"id": 15, "from_member": 5, "to_member": 8}
}

### 检查是否已点赞 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {"is_liked": true, "like_id": 15, "created_at": "2024-01-20T10:30:00Z"}
}

### 我关注的列表 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {"count": 1, "next": null, "previous": null, "page_size": 20, "current_page": 1, "total_pages": 1},
    "results": [
      {"id": 30, "follower": 5, "following": 12, "is_mutual": true, "follower_info": {"id": 5, "username": "member_user"}, "following_info": {"id": 12, "username": "followed_user"}, "tenant": 1, "created_at": "2024-01-20T11:00:00Z"}
    ]
  }
}

### 关注用户 201
{
  "success": true,
  "code": 2000,
  "message": "关注成功",
  "data": {"id": 30, "follower": 5, "following": 12, "is_mutual": false}
}

### 检查是否关注用户 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {"is_following": true, "follow_id": 30, "is_mutual": true, "created_at": "2024-01-20T11:00:00Z"}
}

### 互相关注列表 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {"pagination": {"count": 1, "next": null, "previous": null, "page_size": 20, "current_page": 1, "total_pages": 1}, "results": [{"id": 30, "follower": 5, "following": 12, "is_mutual": true}]}
}

### 关注统计 200
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {"following_count": 15, "followers_count": 25, "mutual_count": 10}
}

### 典型错误示例 400
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {"to_member": ["不能点赞自己"]},
  "error_code": "VALIDATION_ERROR"
}
