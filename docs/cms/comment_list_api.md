# 评论列表API

## 接口说明

获取评论列表，支持分页、过滤和搜索。

- **接口路径**: `/api/v1/cms/comments/`
- **请求方法**: GET
- **认证要求**: 需要JWT认证
- **权限要求**: 
  - 匿名用户: 只能查看已批准的评论
  - 已认证用户: 可以查看已批准的评论和自己的评论
  - 管理员: 可以查看所有评论

## 请求参数

### 请求头

```
Authorization: Bearer {your_jwt_token}
X-Tenant-ID: {tenant_id}
```

### 查询参数

| 参数名         | 类型    | 必填 | 描述                                                |
|----------------|---------|------|-----------------------------------------------------|
| page           | integer | 否   | 页码，默认为1                                       |
| per_page       | integer | 否   | 每页数量，默认为10                                  |
| article        | integer | 否   | 按文章ID过滤                                        |
| parent         | integer | 否   | 按父评论ID过滤，为空字符串或"null"时获取顶级评论    |
| user           | integer | 否   | 按用户ID过滤                                        |
| status         | string  | 否   | 按状态过滤，可选值: pending, approved, spam, trash  |
| is_pinned      | boolean | 否   | 按是否置顶过滤                                      |
| search         | string  | 否   | 搜索关键词，在评论内容、访客名称和邮箱中匹配        |
| sort           | string  | 否   | 排序字段，可选值: created_at, likes_count           |
| sort_direction | string  | 否   | 排序方向，可选值: asc, desc，默认为desc             |

## 响应

### 成功响应

**状态码**: 200 OK

```json
{
  "count": 100,
  "next": "http://example.com/api/v1/cms/comments/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
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
      "updated_at": "2023-06-15T10:35:00Z",
      "is_pinned": false,
      "likes_count": 5,
      "tenant": 1,
      "replies_count": 2
    },
    // 更多评论...
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

## 使用示例

### 获取特定文章的所有评论

```
GET /api/v1/cms/comments/?article=5
```

### 获取顶级评论（不包含回复）

```
GET /api/v1/cms/comments/?parent=null
```

### 获取待审核的评论

```
GET /api/v1/cms/comments/?status=pending
```

### 搜索评论

```
GET /api/v1/cms/comments/?search=关键词
```

### 按创建时间排序

```
GET /api/v1/cms/comments/?sort=created_at&sort_direction=desc
```

## 注意事项

1. 不同用户角色能看到的评论范围不同：
   - 匿名用户只能看到已批准的评论
   - 普通用户可以看到已批准的评论和自己的评论
   - 管理员可以看到所有评论

2. 使用`parent`参数可以区分顶级评论和回复：
   - `parent=null`：获取顶级评论
   - `parent={id}`：获取指定评论的回复

3. 评论列表默认按创建时间倒序排列

4. 评论列表支持分页，默认每页10条评论 