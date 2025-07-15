# 评论审核API

## 接口说明

提供评论审核相关的API，包括批准评论、拒绝评论和标记为垃圾评论等操作。

## 批准评论

将评论状态改为已批准。

### 请求信息

- **接口路径**: `/api/v1/cms/comments/{id}/approve/`
- **请求方法**: POST
- **认证要求**: 需要JWT认证
- **权限要求**: 
  - 文章作者可以批准其文章下的评论
  - 租户管理员可以批准该租户下的所有评论
  - 超级管理员可以批准所有评论

### 请求参数

#### 路径参数

| 参数名 | 类型    | 必填 | 描述    |
|--------|---------|------|---------|
| id     | integer | 是   | 评论ID  |

#### 请求头

```
Authorization: Bearer {your_jwt_token}
Content-Type: application/json
X-Tenant-ID: {tenant_id}
```

#### 请求体

无需请求体

### 响应

#### 成功响应

**状态码**: 200 OK

```json
{
  "id": 15,
  "article": 5,
  "parent": null,
  "user": 3,
  "user_info": {
    "id": 3,
    "username": "user123",
    "first_name": "张",
    "last_name": "三",
    "email": "user@example.com",
    "avatar": "https://example.com/avatars/user.jpg"
  },
  "guest_name": null,
  "guest_email": null,
  "guest_website": null,
  "content": "这是一条评论内容",
  "status": "approved",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2023-06-15T10:30:00Z",
  "updated_at": "2023-06-15T10:40:00Z",
  "is_pinned": false,
  "likes_count": 0,
  "tenant": 1,
  "replies_count": 0
}
```

#### 错误响应

**状态码**: 403 Forbidden

```json
{
  "detail": "您没有执行该操作的权限。"
}
```

**状态码**: 404 Not Found

```json
{
  "detail": "未找到。"
}
```

## 拒绝评论

将评论状态改为已拒绝。

### 请求信息

- **接口路径**: `/api/v1/cms/comments/{id}/reject/`
- **请求方法**: POST
- **认证要求**: 需要JWT认证
- **权限要求**: 
  - 文章作者可以拒绝其文章下的评论
  - 租户管理员可以拒绝该租户下的所有评论
  - 超级管理员可以拒绝所有评论

### 请求参数

#### 路径参数

| 参数名 | 类型    | 必填 | 描述    |
|--------|---------|------|---------|
| id     | integer | 是   | 评论ID  |

#### 请求头

```
Authorization: Bearer {your_jwt_token}
Content-Type: application/json
X-Tenant-ID: {tenant_id}
```

#### 请求体

无需请求体

### 响应

#### 成功响应

**状态码**: 200 OK

```json
{
  "id": 15,
  "article": 5,
  "parent": null,
  "user": 3,
  "user_info": {
    "id": 3,
    "username": "user123",
    "first_name": "张",
    "last_name": "三",
    "email": "user@example.com",
    "avatar": "https://example.com/avatars/user.jpg"
  },
  "guest_name": null,
  "guest_email": null,
  "guest_website": null,
  "content": "这是一条评论内容",
  "status": "trash",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2023-06-15T10:30:00Z",
  "updated_at": "2023-06-15T10:40:00Z",
  "is_pinned": false,
  "likes_count": 0,
  "tenant": 1,
  "replies_count": 0
}
```

#### 错误响应

与批准评论的错误响应相同。

## 标记为垃圾评论

将评论状态改为垃圾评论。

### 请求信息

- **接口路径**: `/api/v1/cms/comments/{id}/mark-spam/`
- **请求方法**: POST
- **认证要求**: 需要JWT认证
- **权限要求**: 
  - 文章作者可以标记其文章下的评论为垃圾评论
  - 租户管理员可以标记该租户下的所有评论为垃圾评论
  - 超级管理员可以标记所有评论为垃圾评论

### 请求参数

#### 路径参数

| 参数名 | 类型    | 必填 | 描述    |
|--------|---------|------|---------|
| id     | integer | 是   | 评论ID  |

#### 请求头

```
Authorization: Bearer {your_jwt_token}
Content-Type: application/json
X-Tenant-ID: {tenant_id}
```

#### 请求体

无需请求体

### 响应

#### 成功响应

**状态码**: 200 OK

```json
{
  "id": 15,
  "article": 5,
  "parent": null,
  "user": 3,
  "user_info": {
    "id": 3,
    "username": "user123",
    "first_name": "张",
    "last_name": "三",
    "email": "user@example.com",
    "avatar": "https://example.com/avatars/user.jpg"
  },
  "guest_name": null,
  "guest_email": null,
  "guest_website": null,
  "content": "这是一条评论内容",
  "status": "spam",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2023-06-15T10:30:00Z",
  "updated_at": "2023-06-15T10:40:00Z",
  "is_pinned": false,
  "likes_count": 0,
  "tenant": 1,
  "replies_count": 0
}
```

#### 错误响应

与批准评论的错误响应相同。

## 注意事项

1. 评论状态变更会自动更新文章的评论统计数据
2. 评论状态变更会记录操作日志
3. 只有已批准的评论会显示在前台页面
4. 评论状态变更后会更新评论的`updated_at`字段 