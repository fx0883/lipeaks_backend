# CMS评论管理API概述

## 简介

评论管理API提供了对CMS系统中评论的完整管理功能，包括评论的创建、查询、更新、删除以及批量处理等操作。评论系统支持多级评论（回复），支持游客评论，并具有完善的审核机制。

## API基础信息

- **基础路径**: `/api/v1/cms/comments/`
- **认证要求**: 需要JWT认证
- **租户要求**: 需要在请求头中提供`X-Tenant-ID`
- **权限控制**: 
  - 所有认证用户可以查看已批准的评论
  - 普通用户可以创建评论，但只能编辑/删除自己的评论
  - 文章作者可以管理其文章下的所有评论
  - 租户管理员可以管理该租户下的所有评论
  - 超级管理员可以管理所有评论

## 评论状态

评论系统支持以下状态：

- `pending`: 待审核（新评论的默认状态）
- `approved`: 已批准（通过审核的评论）
- `spam`: 垃圾评论
- `trash`: 已删除

## API端点列表

| 方法   | 路径                                 | 描述                     |
|--------|--------------------------------------|--------------------------|
| GET    | `/api/v1/cms/comments/`              | 获取评论列表             |
| POST   | `/api/v1/cms/comments/`              | 创建新评论               |
| GET    | `/api/v1/cms/comments/{id}/`         | 获取单个评论详情         |
| PUT    | `/api/v1/cms/comments/{id}/`         | 更新评论                 |
| PATCH  | `/api/v1/cms/comments/{id}/`         | 部分更新评论             |
| DELETE | `/api/v1/cms/comments/{id}/`         | 删除评论                 |
| GET    | `/api/v1/cms/comments/{id}/replies/` | 获取评论的所有回复       |
| POST   | `/api/v1/cms/comments/{id}/approve/` | 批准评论                 |
| POST   | `/api/v1/cms/comments/{id}/reject/`  | 拒绝评论                 |
| POST   | `/api/v1/cms/comments/{id}/mark-spam/` | 标记为垃圾评论         |
| POST   | `/api/v1/cms/comments/batch/`        | 批量处理评论             |

## 请求头要求

```
Authorization: Bearer {your_jwt_token}
Content-Type: application/json
X-Tenant-ID: {tenant_id}
```

## 数据模型

评论对象包含以下字段：

```json
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
}
```

## 错误处理

所有API端点在发生错误时将返回适当的HTTP状态码和详细的错误信息：

```json
{
  "detail": "错误详细信息",
  "code": "错误代码"
}
```

常见错误状态码：
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误

## 相关文档

- [评论列表API](./comment_list_api.md)
- [评论创建API](./comment_create_api.md)
- [评论详情API](./comment_detail_api.md)
- [评论更新API](./comment_update_api.md)
- [评论回复API](./comment_replies_api.md)
- [评论审核API](./comment_moderation_api.md)
- [批量评论处理API](./comment_batch_api.md) 