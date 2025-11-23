# CMS API 文档

## 基础信息

**Base URL**: `http://localhost:8000/api/v1/cms`  
**认证方式**: JWT Bearer Token  
**必需请求头**:
- `Authorization: Bearer {token}`
- `Tenant-ID: {tenant_id}`

---

## Categories API

### 1. 获取分类列表

**GET** `/categories/`

```bash
curl "http://localhost:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

**查询参数**:
- `application` - 按应用ID过滤
- `parent` - 按父分类ID过滤
- `is_active` - 按状态过滤
- `search` - 搜索关键词

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "name": "技术文档",
      "slug": "tech-docs",
      "description": "技术相关文档分类",
      "parent": null,
      "application": 1,
      "application_name": "LiPeaks CMS",
      "icon": "📚",
      "sort_order": 1,
      "is_active": true,
      "article_count": 10,
      "created_at": "2024-11-21T10:00:00Z"
    }
  ]
}
```

---

### 2. 创建分类

**POST** `/categories/`

```bash
curl -X POST "http://localhost:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新分类",
    "slug": "new-category",
    "description": "分类描述",
    "application": 1,
    "icon": "📁",
    "sort_order": 10
  }'
```

**请求体字段**:
- `name` - 分类名称（必填）
- `slug` - URL标识（必填，唯一）
- `description` - 描述（可选）
- `application` - 应用ID（可选）
- `parent` - 父分类ID（可选）
- `icon` - 图标（可选）
- `sort_order` - 排序（可选）
- `is_active` - 是否激活（可选）

---

### 3. 更新分类

**PATCH** `/categories/{id}/`

```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/categories/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"name": "更新后的分类名", "sort_order": 5}'
```

---

### 4. 删除分类

**DELETE** `/categories/{id}/`

```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/categories/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

---

## Articles API

### 1. 获取文章列表

**GET** `/articles/`

```bash
curl "http://localhost:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

**查询参数**:
- `category` - 分类ID
- `category_application_id` - 按分类所属应用过滤
- `status` - 状态: `draft`, `published`, `archived`
- `search` - 搜索标题、内容
- `page` - 页码

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "count": 20,
    "results": [
      {
        "id": 1,
        "title": "如何使用API",
        "slug": "how-to-use-api",
        "excerpt": "本文介绍...",
        "status": "published",
        "author": {
          "id": 1,
          "username": "admin"
        },
        "category": {
          "id": 1,
          "name": "技术文档"
        },
        "view_count": 150,
        "created_at": "2024-11-21T10:00:00Z",
        "published_at": "2024-11-21T12:00:00Z"
      }
    ]
  }
}
```

---

### 2. 创建文章

**POST** `/articles/`

```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "新文章",
    "slug": "new-article",
    "content": "文章内容...",
    "excerpt": "摘要",
    "category": 1,
    "status": "draft",
    "tags": ["api", "文档"]
  }'
```

**请求体字段**:
- `title` - 标题（必填）
- `slug` - URL标识（必填）
- `content` - 内容（必填）
- `excerpt` - 摘要（可选）
- `category` - 分类ID（可选）
- `status` - 状态（可选）
- `tags` - 标签数组（可选）
- `featured_image` - 特色图片URL（可选）

---

### 3. 获取文章详情

**GET** `/articles/{id}/`

```bash
curl "http://localhost:8000/api/v1/cms/articles/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

---

### 4. 更新文章

**PATCH** `/articles/{id}/`

```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/articles/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"status": "published"}'
```

---

### 5. 发布文章

**POST** `/articles/{id}/publish/`

```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/1/publish/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

---

### 6. 归档文章

**POST** `/articles/{id}/archive/`

```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/1/archive/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

---

## 完整测试示例

```bash
# 获取Token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' \
  | jq -r '.data.token')

# 1. 创建分类
CATEGORY_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "使用指南",
    "slug": "user-guide",
    "application": 1,
    "description": "产品使用指南"
  }')

CATEGORY_ID=$(echo "$CATEGORY_RESPONSE" | jq -r '.data.id')
echo "分类ID: $CATEGORY_ID"

# 2. 创建文章
ARTICLE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"快速开始\",
    \"slug\": \"quick-start\",
    \"content\": \"# 快速开始\\n\\n本文介绍如何快速开始使用...\",
    \"excerpt\": \"快速上手指南\",
    \"category\": $CATEGORY_ID,
    \"status\": \"draft\",
    \"tags\": [\"入门\", \"教程\"]
  }")

ARTICLE_ID=$(echo "$ARTICLE_RESPONSE" | jq -r '.data.id')
echo "文章ID: $ARTICLE_ID"

# 3. 发布文章
curl -s -X POST "http://localhost:8000/api/v1/cms/articles/$ARTICLE_ID/publish/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" | jq

# 4. 查询分类下的文章
curl "http://localhost:8000/api/v1/cms/articles/?category=$CATEGORY_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" | jq
```

---

## 注意事项

1. **application字段** - 分类可关联到特定应用，用于多应用场景
2. **层级结构** - 支持父子分类
3. **Markdown** - 文章内容支持Markdown格式
4. **状态管理** - 文章有草稿、已发布、已归档三种状态
