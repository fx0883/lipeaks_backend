# 评论管理API详细文档

## 1. GET /api/v1/cms/comments/ - 获取评论列表

**权限**: 租户管理员/Member

### 查询参数
- `article_id`: 按文章ID过滤
- `status`: 状态过滤 (pending/approved/rejected/spam)
- `parent`: 父评论ID（获取回复）

### Curl示例
```bash
# 获取所有评论
curl "http://localhost:8000/api/v1/cms/comments/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取特定文章的评论
curl "http://localhost:8000/api/v1/cms/comments/?article_id=10317" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取待审核的评论
curl "http://localhost:8000/api/v1/cms/comments/?status=pending" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 2. POST /api/v1/cms/comments/ - 创建评论

**权限**: 租户管理员/Member/游客

### 请求体（Member/管理员）
```json
{
  "article": 10317,
  "content": "这是一条评论",
  "parent": null
}
```

### 请求体（游客）
```json
{
  "article": 10317,
  "content": "游客评论",
  "guest_name": "游客名字",
  "guest_email": "guest@example.com",
  "guest_website": "https://example.com"
}
```

### Curl示例
```bash
# Member评论
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"article":10317,"content":"很好的文章！"}'

# 游客评论
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "article":10317,
    "content":"游客评论",
    "guest_name":"张三",
    "guest_email":"guest@qq.com"
  }'
```

## 3. POST /api/v1/cms/comments/{id}/approve/ - 批准评论

**权限**: 租户管理员

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/123/approve/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 4. POST /api/v1/cms/comments/{id}/reject/ - 拒绝评论

**权限**: 租户管理员

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/123/reject/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 5. POST /api/v1/cms/comments/{id}/mark-spam/ - 标记为垃圾

**权限**: 租户管理员

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/123/mark-spam/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 6. GET /api/v1/cms/comments/{id}/replies/ - 获取评论回复

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/comments/123/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 7. POST /api/v1/cms/comments/batch/ - 批量处理评论

**权限**: 租户管理员

### 请求体
```json
{
  "comment_ids": [123, 124, 125],
  "action": "approve"
}
```

### 支持的操作
- `approve`: 批准
- `reject`: 拒绝
- `spam`: 标记为垃圾
- `delete`: 删除

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/batch/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comment_ids":[123,124,125],
    "action":"approve"
  }'
```
