# 分类管理API详细文档

## 1. GET /api/v1/cms/categories/ - 获取分类列表

**权限**: 租户管理员/Member

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/categories/" \
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
curl -X POST "http://localhost:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
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
curl "http://localhost:8000/api/v1/cms/categories/41/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 4. PATCH /api/v1/cms/categories/{id}/ - 部分更新分类

**推荐**: 使用PATCH而不是PUT

### Curl示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/categories/41/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
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
curl -X DELETE "http://localhost:8000/api/v1/cms/categories/41/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 6. GET /api/v1/cms/categories/tree/ - 获取分类树

**权限**: 租户管理员/Member

### Curl示例
```bash
curl "http://localhost:8000/api/v1/cms/categories/tree/" \
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
