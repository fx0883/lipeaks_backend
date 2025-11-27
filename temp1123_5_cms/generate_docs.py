#!/usr/bin/env python3
"""
生成CMS API详细文档
"""
import json

# 文章管理API文档
article_apis = """# 文章管理API详细文档

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
curl "http://localhost:8000/api/v1/cms/articles/?status=published" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Member用户  
curl "http://localhost:8000/api/v1/cms/articles/" \\
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \\
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
curl -X POST "http://localhost:8000/api/v1/cms/articles/" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "X-Tenant-ID: 3" \\
  -H "Content-Type: application/json" \\
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
curl "http://localhost:8000/api/v1/cms/articles/10317/" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 4. PATCH /api/v1/cms/articles/{id}/ - 部分更新文章

**权限**: 租户管理员/Member（仅限自己的文章）

### Curl示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/articles/10317/" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"excerpt":"更新的摘要"}'
```

## 5. DELETE /api/v1/cms/articles/{id}/ - 删除文章

**权限**: 租户管理员/Member（仅限自己的文章）

### 查询参数
- `force`: 是否强制删除 (true/false，默认false)

### Curl示例
```bash
# 软删除
curl -X DELETE "http://localhost:8000/api/v1/cms/articles/10317/" \\
  -H "Authorization: Bearer YOUR_TOKEN"

# 强制删除
curl -X DELETE "http://localhost:8000/api/v1/cms/articles/10317/?force=true" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 6. POST /api/v1/cms/articles/{id}/publish/ - 发布文章

**权限**: 租户管理员/Member（仅限自己的文章）

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10317/publish/" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{}'
```

## 7. POST /api/v1/cms/articles/{id}/unpublish/ - 取消发布

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10317/unpublish/" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{}'
```

## 8. POST /api/v1/cms/articles/{id}/archive/ - 归档文章

**权限**: 租户管理员

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10317/archive/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
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
curl "http://localhost:8000/api/v1/cms/articles/10317/statistics/?period=week" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 10. POST /api/v1/cms/articles/{id}/view/ - 记录阅读

**权限**: 无需认证

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/10317/view/" \\
  -H "Content-Type: application/json" \\
  -d '{}'
```

## 11. GET /api/v1/cms/articles/{id}/versions/ - 获取版本历史

**权限**: 租户管理员

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/articles/10317/versions/" \\
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
curl -X POST "http://localhost:8000/api/v1/cms/articles/batch-delete/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"article_ids":[10315,10316],"force":false}'
```
"""

# 分类管理API文档
category_apis = """# 分类管理API详细文档

## 1. GET /api/v1/cms/categories/ - 获取分类列表

**权限**: 租户管理员/Member

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/categories/" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 2. POST /api/v1/cms/categories/ - 创建分类

**权限**: 租户管理员

### 请求体（支持多语言）
```json
{
  "translations": {
    "zh-hans": {
      "name": "技术分类",
      "description": "技术相关文章"
    },
    "en": {
      "name": "Technology",
      "description": "Tech articles"
    }
  },
  "slug": "tech",
  "is_active": true,
  "sort_order": 0
}
```

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/categories/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "translations": {
      "zh-hans": {"name":"新分类","description":"描述"}
    },
    "slug":"new-cat-'$(date +%s)'",
    "is_active":true
  }'
```

## 3. GET /api/v1/cms/categories/{id}/ - 获取分类详情

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/categories/41/" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 4. PATCH /api/v1/cms/categories/{id}/ - 部分更新分类

**推荐**: 使用PATCH而不是PUT

### Curl示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/categories/41/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "translations": {
      "zh-hans": {"name":"更新的分类名"}
    },
    "is_active":true
  }'
```

## 5. DELETE /api/v1/cms/categories/{id}/ - 删除分类

### Curl示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/categories/41/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 6. GET /api/v1/cms/categories/tree/ - 获取分类树

**权限**: 租户管理员/Member

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/categories/tree/" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 响应示例
```json
{
  "success": true,
  "code": 2000,
  "data": [
    {
      "id": 41,
      "name": "技术分类",
      "slug": "tech",
      "description": "技术相关",
      "is_active": true,
      "sort_order": 0,
      "children": [
        {
          "id": 42,
          "name": "Python",
          "slug": "python",
          "children": []
        }
      ]
    }
  ]
}
```
"""

# 标签管理API文档
tag_apis = """# 标签管理API详细文档

## 标签组管理

### 1. GET /api/v1/cms/tag-groups/ - 获取标签组列表

```bash
curl "http://localhost:8000/api/v1/cms/tag-groups/" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. POST /api/v1/cms/tag-groups/ - 创建标签组

```bash
curl -X POST "http://localhost:8000/api/v1/cms/tag-groups/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name":"编程语言",
    "slug":"prog-lang-'$(date +%s)'",
    "description":"编程语言相关标签",
    "is_active":true
  }'
```

### 3. PATCH /api/v1/cms/tag-groups/{id}/ - 更新标签组

```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/tag-groups/5/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"name":"更新的标签组名"}'
```

## 标签管理

### 1. GET /api/v1/cms/tags/ - 获取标签列表

```bash
curl "http://localhost:8000/api/v1/cms/tags/" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. POST /api/v1/cms/tags/ - 创建标签

```bash
curl -X POST "http://localhost:8000/api/v1/cms/tags/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name":"Python",
    "slug":"python-'$(date +%s)'",
    "description":"Python编程语言",
    "color":"#3776AB",
    "group":5,
    "is_active":true
  }'
```

### 3. GET /api/v1/cms/tags/{id}/ - 获取标签详情

```bash
curl "http://localhost:8000/api/v1/cms/tags/2/" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. PATCH /api/v1/cms/tags/{id}/ - 更新标签

```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/tags/2/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"color":"#FF0000","is_active":true}'
```

### 5. DELETE /api/v1/cms/tags/{id}/ - 删除标签

```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/tags/2/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### 6. GET /api/v1/cms/tags/usage-stats/ - 获取标签使用统计

```bash
curl "http://localhost:8000/api/v1/cms/tags/usage-stats/" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应示例:
```json
{
  "success": true,
  "data": [
    {
      "id": 2,
      "name": "Python",
      "slug": "python",
      "color": "#3776AB",
      "articles_count": 25
    }
  ]
}
```
"""

# 评论管理API文档
comment_apis = """# 评论管理API详细文档

## 1. GET /api/v1/cms/comments/ - 获取评论列表

**权限**: 租户管理员/Member

### 查询参数
- `article_id`: 按文章ID过滤
- `status`: 状态过滤 (pending/approved/rejected/spam)
- `parent`: 父评论ID（获取回复）

### Curl示例
```bash
# 获取所有评论
curl "http://localhost:8000/api/v1/cms/comments/" \\
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取特定文章的评论
curl "http://localhost:8000/api/v1/cms/comments/?article_id=10317" \\
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取待审核的评论
curl "http://localhost:8000/api/v1/cms/comments/?status=pending" \\
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
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \\
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \\
  -H "X-Tenant-ID: 3" \\
  -H "Content-Type: application/json" \\
  -d '{"article":10317,"content":"很好的文章！"}'

# 游客评论
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \\
  -H "X-Tenant-ID: 3" \\
  -H "Content-Type: application/json" \\
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
curl -X POST "http://localhost:8000/api/v1/cms/comments/123/approve/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{}'
```

## 4. POST /api/v1/cms/comments/{id}/reject/ - 拒绝评论

**权限**: 租户管理员

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/123/reject/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{}'
```

## 5. POST /api/v1/cms/comments/{id}/mark-spam/ - 标记为垃圾

**权限**: 租户管理员

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/123/mark-spam/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{}'
```

## 6. GET /api/v1/cms/comments/{id}/replies/ - 获取评论回复

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/comments/123/replies/" \\
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
curl -X POST "http://localhost:8000/api/v1/cms/comments/batch/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "comment_ids":[123,124,125],
    "action":"approve"
  }'
```
"""

# Member文章管理API文档
member_apis = """# Member文章管理API详细文档

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
curl "http://localhost:8000/api/v1/cms/member/articles/?status=published" \\
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \\
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
curl -X POST "http://localhost:8000/api/v1/cms/member/articles/" \\
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \\
  -H "X-Tenant-ID: 3" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title":"我的新文章",
    "content":"# 标题\\n\\n内容...",
    "content_type":"markdown",
    "excerpt":"文章摘要",
    "status":"draft"
  }'
```

## 3. GET /api/v1/cms/member/articles/{id}/ - 获取我的单篇文章

**权限**: Member（只能获取自己的文章）

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/member/articles/10317/" \\
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \\
  -H "X-Tenant-ID: 3"
```

## 4. PATCH /api/v1/cms/member/articles/{id}/ - 更新文章

**权限**: Member（只能更新自己的文章）

**重要**: 推荐使用PATCH而不是PUT

### Curl示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/member/articles/10317/" \\
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \\
  -H "X-Tenant-ID: 3" \\
  -H "Content-Type: application/json" \\
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
curl -X DELETE "http://localhost:8000/api/v1/cms/member/articles/10317/" \\
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \\
  -H "X-Tenant-ID: 3"
```

## 6. POST /api/v1/cms/member/articles/{id}/publish/ - 发布文章

**权限**: Member（只能发布自己的文章）

### Curl示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/member/articles/10317/publish/" \\
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \\
  -H "X-Tenant-ID: 3" \\
  -H "Content-Type: application/json" \\
  -d '{}'
```

## 7. GET /api/v1/cms/member/articles/{id}/statistics/ - 获取文章统计

**权限**: Member（只能查看自己文章的统计）

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/member/articles/10317/statistics/" \\
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \\
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
ARTICLE_ID=$(curl -s -X POST "http://localhost:8000/api/v1/cms/member/articles/" \\
  -H "Authorization: Bearer $MEMBER_TOKEN" \\
  -H "X-Tenant-ID: $TENANT_ID" \\
  -H "Content-Type: application/json" \\
  -d '{"title":"测试文章","content":"内容","content_type":"markdown"}' | \\
  jq -r '.data.id')

echo "创建的文章ID: $ARTICLE_ID"

# 2. 更新文章
curl -X PATCH "http://localhost:8000/api/v1/cms/member/articles/$ARTICLE_ID/" \\
  -H "Authorization: Bearer $MEMBER_TOKEN" \\
  -H "X-Tenant-ID: $TENANT_ID" \\
  -H "Content-Type: application/json" \\
  -d '{"excerpt":"添加摘要","category_ids":[41]}'

# 3. 发布文章
curl -X POST "http://localhost:8000/api/v1/cms/member/articles/$ARTICLE_ID/publish/" \\
  -H "Authorization: Bearer $MEMBER_TOKEN" \\
  -H "X-Tenant-ID: $TENANT_ID" \\
  -H "Content-Type: application/json" \\
  -d '{}'

# 4. 查看统计
curl "http://localhost:8000/api/v1/cms/member/articles/$ARTICLE_ID/statistics/" \\
  -H "Authorization: Bearer $MEMBER_TOKEN" \\
  -H "X-Tenant-ID: $TENANT_ID"
```
"""

# 写入文件
docs = {
    "01_文章管理API.md": article_apis,
    "02_分类管理API.md": category_apis,
    "03_标签管理API.md": tag_apis,
    "04_评论管理API.md": comment_apis,
    "05_Member文章管理API.md": member_apis
}

for filename, content in docs.items():
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ 已生成: {filename}")

print("\n所有API文档已生成完成！")
