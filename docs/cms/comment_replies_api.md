# 评论回复API

## 接口说明

获取指定评论的所有回复。

- **接口路径**: `/api/v1/cms/comments/{id}/replies/`
- **请求方法**: GET
- **认证要求**: 需要JWT认证
- **权限要求**: 
  - 所有认证用户可以查看已批准的评论回复
  - 普通用户可以查看已批准的评论回复和自己的评论回复
  - 管理员可以查看所有评论回复

## 请求参数

### 路径参数

| 参数名 | 类型    | 必填 | 描述    |
|--------|---------|------|---------|
| id     | integer | 是   | 评论ID  |

### 请求头

```
Authorization: Bearer {your_jwt_token}
X-Tenant-ID: {tenant_id}
```

### 查询参数

| 参数名         | 类型    | 必填 | 描述                                               |
|----------------|---------|------|---------------------------------------------------|
| page           | integer | 否   | 页码，默认为1                                      |
| per_page       | integer | 否   | 每页数量，默认为10                                 |
| status         | string  | 否   | 按状态过滤，可选值: pending, approved, spam, trash |
| sort           | string  | 否   | 排序字段，可选值: created_at, likes_count          |
| sort_direction | string  | 否   | 排序方向，可选值: asc, desc，默认为asc             |

## 响应

### 成功响应

**状态码**: 200 OK

```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 16,
      "article": 5,
      "parent": 15,
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
      "content": "这是一条回复",
      "status": "approved",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2023-06-15T10:35:00Z",
      "updated_at": "2023-06-15T10:35:00Z",
      "is_pinned": false,
      "likes_count": 0,
      "tenant": 1,
      "replies_count": 0
    },
    {
      "id": 17,
      "article": 5,
      "parent": 15,
      "user": null,
      "user_info": null,
      "guest_name": "游客小明",
      "guest_email": "guest@example.com",
      "guest_website": "https://example.com",
      "content": "这是一条游客回复",
      "status": "approved",
      "ip_address": "192.168.1.2",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2023-06-15T10:40:00Z",
      "updated_at": "2023-06-15T10:40:00Z",
      "is_pinned": false,
      "likes_count": 0,
      "tenant": 1,
      "replies_count": 0
    },
    {
      "id": 18,
      "article": 5,
      "parent": 15,
      "user": 4,
      "user_info": {
        "id": 4,
        "username": "admin",
        "first_name": "管理",
        "last_name": "员",
        "email": "admin@example.com",
        "avatar": "https://example.com/avatars/admin.jpg"
      },
      "guest_name": null,
      "guest_email": null,
      "guest_website": null,
      "content": "这是管理员的回复",
      "status": "approved",
      "ip_address": "192.168.1.3",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2023-06-15T10:45:00Z",
      "updated_at": "2023-06-15T10:45:00Z",
      "is_pinned": false,
      "likes_count": 0,
      "tenant": 1,
      "replies_count": 0
    }
  ]
}
```

### 错误响应

**状态码**: 401 Unauthorized

```json
{
  "detail": "身份认证信息未提供。"
}
```

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

## 使用示例

### 获取评论的所有回复

```
GET /api/v1/cms/comments/15/replies/
```

### 获取评论的待审核回复

```
GET /api/v1/cms/comments/15/replies/?status=pending
```

### 按创建时间排序

```
GET /api/v1/cms/comments/15/replies/?sort=created_at&sort_direction=desc
```

## 注意事项

1. 此API仅返回直接回复指定评论的评论，不包括嵌套回复
2. 不同用户角色能看到的回复范围不同：
   - 匿名用户只能看到已批准的回复
   - 普通用户可以看到已批准的回复和自己的回复
   - 管理员可以看到所有回复
3. 回复默认按创建时间升序排列（从早到晚）
4. 回复列表支持分页，默认每页10条回复 