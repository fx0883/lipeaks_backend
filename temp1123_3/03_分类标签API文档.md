# 分类和标签管理 API 文档

## 概述

分类和标签管理API主要供Admin用户使用，用于组织和管理文章的分类和标签体系。

### 权限说明
- **Admin用户**：可以完全管理分类和标签，使用查询参数`?tenant_id=3`
- **Member用户**：只能查看，使用Header `X-Tenant-ID: 3`

---

# 分类管理 API

## Base URL
```
http://localhost:8000/api/v1/cms/categories
```

### 1. 获取分类列表

**接口地址**
```
GET /api/v1/cms/categories/
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tenant_id | integer | Admin必填 | 租户ID |
| parent | integer | 否 | 父分类ID |
| is_active | boolean | 否 | 是否激活 |
| is_pinned | boolean | 否 | 是否置顶 |
| search | string | 否 | 搜索关键词 |
| ordering | string | 否 | 排序字段 |

**curl示例**
```bash
curl -X GET "http://localhost:8000/api/v1/cms/categories/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "slug": "tech",
      "name": "技术分类",
      "description": "技术相关文章",
      "parent": null,
      "is_active": true,
      "is_pinned": false,
      "sort_order": 0,
      "created_at": "2025-11-23T10:00:00Z"
    }
  ]
}
```

---

### 2. 创建分类

**接口地址**
```
POST /api/v1/cms/categories/
```

**请求体**

由于分类支持多语言，需要提供translations字段：

```json
{
  "slug": "new-category",
  "translations": {
    "zh-hans": {
      "name": "新分类",
      "description": "分类描述",
      "seo_title": "SEO标题",
      "seo_description": "SEO描述"
    },
    "en": {
      "name": "New Category",
      "description": "Category description"
    }
  },
  "parent": null,
  "is_active": true,
  "sort_order": 0
}
```

**curl示例**
```bash
curl -X POST "http://localhost:8000/api/v1/cms/categories/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "tech-blog",
    "translations": {
      "zh-hans": {
        "name": "技术博客",
        "description": "技术相关内容"
      }
    }
  }'
```

---

### 3. 获取分类树

获取树形结构的分类列表。

**接口地址**
```
GET /api/v1/cms/categories/tree/
```

**curl示例**
```bash
curl -X GET "http://localhost:8000/api/v1/cms/categories/tree/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "name": "技术博客",
      "slug": "tech-blog",
      "description": "技术相关文章",
      "is_active": true,
      "sort_order": 0,
      "children": [
        {
          "id": 2,
          "name": "Python教程",
          "slug": "python-tutorial",
          "description": "Python编程教程",
          "is_active": true,
          "sort_order": 0,
          "children": []
        }
      ]
    }
  ]
}
```

---

### 4. 更新分类

**接口地址**
```
PUT /api/v1/cms/categories/{id}/
```

**curl示例**
```bash
curl -X PUT "http://localhost:8000/api/v1/cms/categories/1/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "updated-slug",
    "translations": {
      "zh-hans": {
        "name": "更新后的分类名",
        "description": "更新后的描述"
      }
    }
  }'
```

---

### 5. 部分更新分类

**接口地址**
```
PATCH /api/v1/cms/categories/{id}/
```

**curl示例**
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/categories/1/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}'
```

---

### 6. 删除分类

**接口地址**
```
DELETE /api/v1/cms/categories/{id}/
```

**注意**：
- 如果分类下有文章，无法删除
- 如果有子分类，需要先删除所有子分类

**curl示例**
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/categories/1/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

# 标签管理 API

## Base URL
```
http://localhost:8000/api/v1/cms/tags
```

### 1. 获取标签列表

**接口地址**
```
GET /api/v1/cms/tags/
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tenant_id | integer | Admin必填 | 租户ID |
| is_active | boolean | 否 | 是否激活 |
| group | integer | 否 | 标签组ID |
| search | string | 否 | 搜索关键词 |

**curl示例**
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tags/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 2. 创建标签

**接口地址**
```
POST /api/v1/cms/tags/
```

**请求体**
```json
{
  "name": "Python",
  "slug": "python",
  "description": "Python相关内容",
  "group": null,
  "color": "#3776ab",
  "is_active": true
}
```

**curl示例**
```bash
curl -X POST "http://localhost:8000/api/v1/cms/tags/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Django",
    "slug": "django",
    "color": "#092e20"
  }'
```

---

### 3. 获取标签使用统计

获取所有标签的使用次数统计。

**接口地址**
```
GET /api/v1/cms/tags/usage-stats/
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "name": "Python",
      "slug": "python",
      "usage_count": 25,
      "color": "#3776ab"
    },
    {
      "id": 2,
      "name": "Django",
      "slug": "django",
      "usage_count": 18,
      "color": "#092e20"
    }
  ]
}
```

**curl示例**
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tags/usage-stats/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 4. 更新标签

**接口地址**
```
PUT /api/v1/cms/tags/{id}/
```

**curl示例**
```bash
curl -X PUT "http://localhost:8000/api/v1/cms/tags/1/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python 3.x",
    "slug": "python-3x",
    "color": "#3776ab"
  }'
```

---

### 5. 删除标签

**接口地址**
```
DELETE /api/v1/cms/tags/{id}/
```

**curl示例**
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/tags/1/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

# 标签组管理 API

## Base URL
```
http://localhost:8000/api/v1/cms/tag-groups
```

### 1. 获取标签组列表

**接口地址**
```
GET /api/v1/cms/tag-groups/
```

**curl示例**
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tag-groups/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 2. 创建标签组

**接口地址**
```
POST /api/v1/cms/tag-groups/
```

**请求体**
```json
{
  "name": "技术栈",
  "slug": "tech-stack",
  "description": "文章使用的技术栈标签",
  "is_active": true
}
```

**curl示例**
```bash
curl -X POST "http://localhost:8000/api/v1/cms/tag-groups/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "编程语言",
    "slug": "programming-languages"
  }'
```

---

### 3. 更新标签组

**接口地址**
```
PUT /api/v1/cms/tag-groups/{id}/
PATCH /api/v1/cms/tag-groups/{id}/
```

**curl示例**
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/tag-groups/1/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

---

### 4. 删除标签组

**接口地址**
```
DELETE /api/v1/cms/tag-groups/{id}/
```

**curl示例**
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/tag-groups/1/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

## 注意事项

### 分类相关
1. **多语言支持**：分类使用django-parler支持多语言，创建时必须提供translations字段
2. **树形结构**：支持父子分类关系，可以创建多级分类
3. **删除限制**：有关联文章或子分类的分类无法删除

### 标签相关
1. **标签组**：标签可以归属到标签组，便于管理
2. **颜色标识**：可以为标签指定颜色，用于前端显示
3. **使用统计**：可以查询标签的使用次数，了解热门标签

### 通用规则
- **Admin用户**必须使用查询参数`?tenant_id=3`
- **Member用户**只能查看，使用Header `X-Tenant-ID: 3`
- 所有创建和更新操作都需要Admin权限
