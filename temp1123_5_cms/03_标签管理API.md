# 标签管理API详细文档

## 标签组管理

### 1. GET /api/v1/cms/tag-groups/ - 获取标签组列表

```bash
curl "http://localhost:8000/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. POST /api/v1/cms/tag-groups/ - 创建标签组

```bash
curl -X POST "http://localhost:8000/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"编程语言",
    "slug":"prog-lang-'$(date +%s)'",
    "description":"编程语言相关标签",
    "is_active":true
  }'
```

### 3. PATCH /api/v1/cms/tag-groups/{id}/ - 更新标签组

```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/tag-groups/5/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"更新的标签组名"}'
```

## 标签管理

### 1. GET /api/v1/cms/tags/ - 获取标签列表

```bash
curl "http://localhost:8000/api/v1/cms/tags/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. POST /api/v1/cms/tags/ - 创建标签

```bash
curl -X POST "http://localhost:8000/api/v1/cms/tags/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
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
curl "http://localhost:8000/api/v1/cms/tags/2/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. PATCH /api/v1/cms/tags/{id}/ - 更新标签

```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/tags/2/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"color":"#FF0000","is_active":true}'
```

### 5. DELETE /api/v1/cms/tags/{id}/ - 删除标签

```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/tags/2/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### 6. GET /api/v1/cms/tags/usage-stats/ - 获取标签使用统计

```bash
curl "http://localhost:8000/api/v1/cms/tags/usage-stats/" \
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
