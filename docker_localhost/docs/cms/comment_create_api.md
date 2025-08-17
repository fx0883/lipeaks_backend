# 评论创建API

## 接口说明

创建新的评论，支持登录用户评论和游客评论。

- **接口路径**: `/api/v1/cms/comments/`
- **请求方法**: POST
- **认证要求**: 
  - 登录用户评论：需要JWT认证
  - 游客评论：无需认证，但需要提供游客名称和邮箱
- **权限要求**: 
  - 文章必须允许评论
  - 用户必须有权限访问该文章

## 请求参数

### 请求头

```
Authorization: Bearer {your_jwt_token} (登录用户评论时需要)
Content-Type: application/json
X-Tenant-ID: {tenant_id}
```

### 请求体

| 字段名        | 类型    | 必填 | 描述                                   |
|---------------|---------|------|----------------------------------------|
| article       | integer | 是   | 文章ID                                 |
| parent        | integer | 否   | 父评论ID，回复某条评论时使用           |
| content       | string  | 是   | 评论内容                               |
| guest_name    | string  | 条件 | 游客名称，游客评论时必填               |
| guest_email   | string  | 条件 | 游客邮箱，游客评论时必填               |
| guest_website | string  | 否   | 游客网站                               |

**注意**：
- 如果是登录用户评论，系统会自动关联当前用户
- 如果是游客评论，必须提供`guest_name`和`guest_email`
- 用户和游客信息至少要提供一项

## 请求示例

### 登录用户评论

```json
{
  "article": 5,
  "parent": null,
  "content": "这是一条评论内容"
}
```

### 游客评论

```json
{
  "article": 5,
  "parent": null,
  "content": "这是一条游客评论",
  "guest_name": "游客小明",
  "guest_email": "guest@example.com",
  "guest_website": "https://example.com"
}
```

### 回复评论

```json
{
  "article": 5,
  "parent": 10,
  "content": "这是对ID为10的评论的回复"
}
```

## 响应

### 成功响应

**状态码**: 201 Created

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
  "status": "pending",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2023-06-15T10:30:00Z",
  "updated_at": "2023-06-15T10:30:00Z",
  "is_pinned": false,
  "likes_count": 0,
  "tenant": 1,
  "replies_count": 0
}
```

### 错误响应

**状态码**: 400 Bad Request

```json
{
  "detail": "用户或游客名称至少提供一项"
}
```

```json
{
  "detail": "该文章不允许评论"
}
```

```json
{
  "detail": "文章不存在或无权限访问"
}
```

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

## 评论审核规则

创建评论时，系统会根据用户角色自动设置评论状态：

1. 管理员和文章作者的评论会自动批准（status = "approved"）
2. 其他用户和游客的评论需要审核（status = "pending"）

## 注意事项

1. 评论创建后，系统会自动记录IP地址和User-Agent信息
2. 系统会自动更新文章的评论数统计
3. 评论创建后会记录操作日志
4. 游客评论需要提供名称和邮箱，但不会显示邮箱
5. 回复评论时需要提供父评论ID（parent字段） 