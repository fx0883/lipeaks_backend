# Member文章管理API详细文档

**重要**: 所有Member文章管理API都必须传递 `X-Tenant-ID` header

## 1. GET /api/v1/cms/member/articles/ - 获取我的文章列表

**权限**: Member（只能看到自己的文章）

### 查询参数
- `page`: 页码
- `status`: 状态过滤
- `search`: 搜索关键词
- `sort`: 排序字段 (created_at/updated_at/published_at/title)
- `sort_direction`: 排序方向 (asc/desc)

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/member/articles/?status=published" \
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3"
```

## 2. POST /api/v1/cms/member/articles/ - 创建文章

**权限**: Member

### 请求体
```json
{
  "title": "我的文章",
  "content": "文章内容",
  "content_type": "markdown",
  "excerpt": "摘要",
  "status": "draft",
  "category_ids": [41],
  "tag_ids": [2, 3]
}
```

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"我的新文章",
    "content":"# 标题\n\n内容...",
    "content_type":"markdown",
    "excerpt":"文章摘要",
    "status":"draft"
  }'
```

## 3. GET /api/v1/cms/member/articles/{id}/ - 获取我的单篇文章

**权限**: Member（只能获取自己的文章）

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/member/articles/10317/" \
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3"
```

## 4. PATCH /api/v1/cms/member/articles/{id}/ - 更新文章

**权限**: Member（只能更新自己的文章）

**重要**: 推荐使用PATCH而不是PUT

### Curl示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/member/articles/10317/" \
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"更新的标题",
    "excerpt":"更新的摘要",
    "category_ids":[41,42]
  }'
```

## 5. DELETE /api/v1/cms/member/articles/{id}/ - 删除文章

**权限**: Member（只能删除自己的文章）

**说明**: Member删除文章为软删除，状态改为archived

### Curl示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/member/articles/10317/" \
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3"
```

## 6. POST /api/v1/cms/member/articles/{id}/publish/ - 发布文章

**权限**: Member（只能发布自己的文章）

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/member/articles/10317/publish/" \
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 7. GET /api/v1/cms/member/articles/{id}/statistics/ - 获取文章统计

**权限**: Member（只能查看自己文章的统计）

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/member/articles/10317/statistics/" \
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \
  -H "X-Tenant-ID: 3"
```

### 响应示例
```json
{
  "success": true,
  "data": {
    "views_count": 150,
    "unique_views_count": 100,
    "likes_count": 15,
    "comments_count": 8,
    "shares_count": 3,
    "bookmarks_count": 12
  }
}
```

## Member使用完整流程示例

```bash
# 设置环境变量
MEMBER_TOKEN="YOUR_MEMBER_TOKEN"
TENANT_ID="3"

# 1. 创建草稿
ARTICLE_ID=$(curl -s -X POST "http://localhost:8000/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"title":"测试文章","content":"内容","content_type":"markdown"}' | \
  jq -r '.data.id')

echo "创建的文章ID: $ARTICLE_ID"

# 2. 更新文章
curl -X PATCH "http://localhost:8000/api/v1/cms/member/articles/$ARTICLE_ID/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"excerpt":"添加摘要","category_ids":[41]}'

# 3. 发布文章
curl -X POST "http://localhost:8000/api/v1/cms/member/articles/$ARTICLE_ID/publish/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{}'

# 4. 查看统计
curl "http://localhost:8000/api/v1/cms/member/articles/$ARTICLE_ID/statistics/" \
  -H "Authorization: Bearer $MEMBER_TOKEN" \
  -H "X-Tenant-ID: $TENANT_ID"
```
