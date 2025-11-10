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

#### 接口信息
- **接口地址**: `GET /api/v1/interactions/favorites/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 获取当前用户的文章收藏列表

#### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |

#### 业务规则
- ✅ 仅返回当前用户的收藏记录
- ✅ 支持标准分页格式
- ✅ 包含文章详细信息和用户信息
- ✅ 自动过滤已删除的文章
- ❌ 管理员用户无法使用此接口

### 2. 收藏文章

#### 接口信息
- **接口地址**: `POST /api/v1/interactions/favorites/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 收藏指定的文章

#### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |
| Content-Type | string | 是 | 请求体类型 | "application/json" | 必须为application/json |

#### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| article | integer | 是 | 文章ID | 42 | 有效的文章ID，必须属于当前租户 |

#### 业务规则
- ✅ 同一用户不能重复收藏同一文章
- ✅ 只能收藏本租户的文章
- ✅ 自动记录收藏时间
- ✅ 文章不存在或已删除时返回错误
- ❌ 不能收藏自己的文章（可选业务规则）

### 3. 取消收藏（按收藏ID）

#### 接口信息
- **接口地址**: `DELETE /api/v1/interactions/favorites/{id}/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 通过收藏记录ID取消收藏

#### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |

#### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | 收藏记录ID | 23 | 有效的收藏记录ID |

#### 业务规则
- ✅ 只能删除自己的收藏记录
- ✅ 删除不存在的记录返回404
- ✅ 删除成功返回204无内容

### 4. 取消收藏（按文章ID）

#### 接口信息
- **接口地址**: `DELETE /api/v1/interactions/favorites/by-article/{article_id}/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 通过文章ID取消收藏

#### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |

#### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| article_id | integer | 是 | 文章ID | 42 | 有效的文章ID |

#### 业务规则
- ✅ 只能取消自己的收藏
- ✅ 如果未收藏该文章，返回404
- ✅ 成功取消返回204无内容

### 5. 检查是否已收藏

#### 接口信息
- **接口地址**: `GET /api/v1/interactions/favorites/check/{article_id}/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 检查当前用户是否已收藏指定文章

#### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |

#### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| article_id | integer | 是 | 文章ID | 42 | 有效的文章ID |

#### 业务规则
- ✅ 返回收藏状态和收藏ID（如果已收藏）
- ✅ 包含收藏时间信息
- ✅ 文章不存在时返回适当错误

---

## 二、用户点赞（likes）

### 1. 获取我点赞的用户列表

#### 接口信息
- **接口地址**: `GET /api/v1/interactions/likes/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 获取当前用户发出的点赞记录列表

#### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|----------|
| page | integer | 否 | 页码，默认1 | 1 | 大于0的整数 |
| page_size | integer | 否 | 每页数量，默认20，最大100 | 20 | 1-100之间的整数 |

#### 业务规则
- ✅ 仅返回当前用户发出的点赞记录
- ✅ 包含被点赞用户和点赞用户信息
- ✅ 支持标准分页格式

### 2. 点赞用户

#### 接口信息
- **接口地址**: `POST /api/v1/interactions/likes/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 点赞指定的用户

#### 请求头

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|----------|
| Authorization | string | 是 | Bearer token认证 | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的Bearer token格式 |
| X-Tenant-ID | string | 是 | 租户ID | "1" | 有效的租户ID |
| Content-Type | string | 是 | 请求体类型 | "application/json" | 必须为application/json |

#### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| to_member | integer | 是 | 被点赞的用户ID | 10 | 有效的Member ID，必须在本租户 |

#### 业务规则
- ✅ 只能点赞本租户的用户
- ✅ 不能给自己点赞
- ✅ 不能重复点赞同一用户
- ✅ 被点赞用户不存在时返回错误

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
