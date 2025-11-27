# 文章管理API详细文档

## 1. GET /api/v1/cms/articles/ - 获取文章列表

**权限**: 租户管理员/Member  
**分页**: 是

### 查询参数
- `page`: 页码
- `status`: 状态过滤 (draft/pending/published/archived)
- `search`: 搜索关键词
- `category_id`: 分类ID过滤
- `tag_id`: 标签ID过滤
- `author_type`: 作者类型 (member/admin)

### Curl示例
```bash
# 租户管理员
curl "http://localhost:8000/api/v1/cms/articles/?status=published" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Member用户  
curl "http://localhost:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3"
```

## 2. POST /api/v1/cms/articles/ - 创建文章

**权限**: 租户管理员/Member

### 请求体
```json
{
  "title": "文章标题",
  "content": "文章内容",
  "content_type": "markdown",
  "excerpt": "摘要",
  "status": "draft",
  "category_ids": [41, 42],
  "tag_ids": [2, 3],
  "publish_now": false
}
```

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"新文章",
    "content":"内容",
    "content_type":"markdown"
  }'
```

## 3. GET /api/v1/cms/articles/{id}/ - 获取单篇文章

**权限**: 租户管理员/Member

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/articles/10317/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 4. PATCH /api/v1/cms/articles/{id}/ - 部分更新文章

**权限**: 租户管理员/Member（仅限自己的文章）

### Curl示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/articles/10317/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"excerpt":"更新的摘要"}'
```

## 5. DELETE /api/v1/cms/articles/{id}/ - 删除文章

**权限**: 租户管理员/Member（仅限自己的文章）

### 查询参数
- `force`: 是否强制删除 (true/false，默认false)

### Curl示例
```bash
# 软删除
curl -X DELETE "http://localhost:8000/api/v1/cms/articles/10317/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 强制删除
curl -X DELETE "http://localhost:8000/api/v1/cms/articles/10317/?force=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 6. POST /api/v1/cms/articles/{id}/publish/ - 发布文章

**权限**: 租户管理员/Member（仅限自己的文章）

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10317/publish/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 7. POST /api/v1/cms/articles/{id}/unpublish/ - 取消发布

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10317/unpublish/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 8. POST /api/v1/cms/articles/{id}/archive/ - 归档文章

**权限**: 租户管理员

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10317/archive/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 9. GET /api/v1/cms/articles/{id}/statistics/ - 获取统计

**权限**: 租户管理员/Member

### 查询参数
- `period`: 统计周期 (day/week/month/year/all)
- `start_date`: 起始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/articles/10317/statistics/?period=week" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 10. POST /api/v1/cms/articles/{id}/view/ - 记录阅读

**权限**: 无需认证

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10317/view/" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 11. GET /api/v1/cms/articles/{id}/versions/ - 获取版本历史

**权限**: 租户管理员

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/articles/10317/versions/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 12. POST /api/v1/cms/articles/batch-delete/ - 批量删除

**权限**: 租户管理员

### 请求体
```json
{
  "article_ids": [10315, 10316, 10317],
  "force": false
}
```

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/batch-delete/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"article_ids":[10315,10316],"force":false}'
```
