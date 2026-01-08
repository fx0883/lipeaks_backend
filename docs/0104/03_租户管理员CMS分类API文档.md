# 租户管理员 CMS 分类管理 API 文档

## 适用范围
- 面向租户管理员（Tenant Admin）用户
- 用于管理本租户下的文章分类
- 租户管理员只能管理自己租户下的分类

## 基础信息
- 前缀：`/api/v1/cms/categories/`
- 认证：Bearer Token（必须）
- 权限：租户管理员（is_admin=True）

---

## 1. 获取分类列表

### 接口信息
- 路径：GET `/api/v1/cms/categories/`
- 说明：获取本租户下的所有分类列表（无分页）

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| parent | integer | 否 | 父分类ID，筛选指定父分类下的子分类 |
| is_active | boolean | 否 | 是否激活 |
| is_pinned | boolean | 否 | 是否置顶 |
| application | integer | 否 | 应用ID过滤 |
| search | string | 否 | 搜索关键词 |
| ordering | string | 否 | 排序字段（sort_order/created_at/is_pinned） |

### 请求头

| 请求头 | 必填 | 说明 |
|-------|------|------|
| Authorization | 是 | Bearer <access_token> |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 5,
      "slug": "how-to-841",
      "parent": null,
      "cover_image": "",
      "created_at": "2025-10-09T10:14:15.921164Z",
      "updated_at": "2025-12-05T04:48:21.156017Z",
      "sort_order": 0,
      "tenant": 1,
      "application": null,
      "application_name": null,
      "is_active": true,
      "is_pinned": false,
      "translations": {
        "zh-hans": {"name": "How To", "description": "How To"},
        "en": {"name": "How To", "description": ""}
      },
      "name": "How To",
      "description": "How To",
      "seo_title": "",
      "seo_description": ""
    },
    {
      "id": 8,
      "slug": "update-150",
      "parent": null,
      "cover_image": "",
      "created_at": "2025-10-10T14:15:13.995358Z",
      "updated_at": "2025-12-05T04:49:47.905056Z",
      "sort_order": 0,
      "tenant": 1,
      "application": null,
      "application_name": null,
      "is_active": true,
      "is_pinned": false,
      "translations": {
        "zh-hans": {"name": "Update", "description": "Update 150分类"}
      },
      "name": "Update",
      "description": "Update 150分类",
      "seo_title": "",
      "seo_description": ""
    }
  ]
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | integer | 分类ID |
| name | string | 分类名称 |
| slug | string | 分类别名（URL友好） |
| description | string | 分类描述 |
| parent | integer | 父分类ID（顶级分类为null） |
| cover_image | string | 封面图片URL |
| icon | string | 图标名称 |
| is_active | boolean | 是否激活 |
| is_pinned | boolean | 是否置顶 |
| sort_order | integer | 排序顺序 |
| seo_title | string | SEO标题 |
| seo_description | string | SEO描述 |
| article_count | integer | 文章数量 |
| application | integer | 所属应用ID |
| application_name | string | 所属应用名称 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### curl 调用示例
```bash
# 获取所有分类
curl -X GET "http://localhost:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 获取顶级分类
curl -X GET "http://localhost:8000/api/v1/cms/categories/?parent=" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 获取激活的分类
curl -X GET "http://localhost:8000/api/v1/cms/categories/?is_active=true" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按应用筛选
curl -X GET "http://localhost:8000/api/v1/cms/categories/?application=1" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 2. 创建分类

### 接口信息
- 路径：POST `/api/v1/cms/categories/`
- 说明：创建新的文章分类

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 分类名称 |
| slug | string | 否 | 分类别名，不填则自动生成 |
| description | string | 否 | 分类描述 |
| parent | integer | 否 | 父分类ID |
| cover_image | string | 否 | 封面图片URL |
| icon | string | 否 | 图标名称 |
| is_active | boolean | 否 | 是否激活，默认true |
| is_pinned | boolean | 否 | 是否置顶，默认false |
| sort_order | integer | 否 | 排序顺序，默认0 |
| seo_title | string | 否 | SEO标题 |
| seo_description | string | 否 | SEO描述 |
| application | integer | 否 | 所属应用ID |

### 请求体示例
```json
{
  "name": "技术博客",
  "slug": "tech-blog",
  "description": "技术相关的文章分类",
  "parent": null,
  "cover_image": "https://example.com/images/tech.jpg",
  "is_active": true,
  "is_pinned": false,
  "seo_title": "技术博客 - 分享技术知识",
  "seo_description": "分享最新的技术知识和教程"
}
```

### 成功响应（201）
```json
{
  "success": true,
  "code": 2001,
  "message": "创建成功",
  "data": {
    "id": 5,
    "name": "技术博客",
    "slug": "tech-blog",
    "description": "技术相关的文章分类",
    "parent": null,
    "cover_image": "https://example.com/images/tech.jpg",
    "icon": null,
    "is_active": true,
    "is_pinned": false,
    "sort_order": 0,
    "seo_title": "技术博客 - 分享技术知识",
    "seo_description": "分享最新的技术知识和教程",
    "article_count": 0,
    "application": null,
    "application_name": null,
    "created_at": "2024-01-20T15:30:00Z",
    "updated_at": "2024-01-20T15:30:00Z"
  }
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术博客",
    "slug": "tech-blog",
    "description": "技术相关的文章分类",
    "is_active": true
  }'
```

---

## 3. 获取分类详情

### 接口信息
- 路径：GET `/api/v1/cms/categories/{id}/`
- 说明：获取指定分类的详细信息

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| id | integer | 是 | 分类ID |

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/categories/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 4. 更新分类

### 接口信息
- 路径：PUT/PATCH `/api/v1/cms/categories/{id}/`
- 说明：更新分类信息

### 请求体示例
```json
{
  "name": "更新后的分类名称",
  "description": "更新后的分类描述",
  "is_pinned": true
}
```

### curl 调用示例
```bash
# 全量更新
curl -X PUT "http://localhost:8000/api/v1/cms/categories/1/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的分类名称",
    "description": "更新后的分类描述"
  }'

# 部分更新
curl -X PATCH "http://localhost:8000/api/v1/cms/categories/1/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "is_pinned": true
  }'
```

---

## 5. 删除分类

### 接口信息
- 路径：DELETE `/api/v1/cms/categories/{id}/`
- 说明：删除指定分类

### 业务规则
- 不能删除有文章关联的分类
- 不能删除有子分类的分类

### 失败响应（400）
```json
{
  "success": false,
  "code": 4000,
  "message": "Cannot delete category with associated articles, please remove associated articles first",
  "data": null
}
```

### curl 调用示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/categories/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 6. 获取分类树

### 接口信息
- 路径：GET `/api/v1/cms/categories/tree/`
- 说明：以树形结构获取所有分类

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
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
        },
        {
          "id": 3,
          "name": "JavaScript教程",
          "slug": "javascript-tutorial",
          "description": "JavaScript编程教程",
          "is_active": true,
          "sort_order": 1,
          "children": []
        }
      ]
    },
    {
      "id": 4,
      "name": "生活随笔",
      "slug": "life-notes",
      "description": "生活记录",
      "is_active": true,
      "sort_order": 1,
      "children": []
    }
  ]
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/categories/tree/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 错误码说明

| 错误码 | HTTP状态码 | 说明 |
|-------|-----------|------|
| 2000 | 200 | 操作成功 |
| 2001 | 201 | 创建成功 |
| 4000 | 400 | 参数验证失败 |
| 4001 | 401 | 认证失败 |
| 4003 | 403 | 权限不足 |
| 4004 | 404 | 资源不存在 |
| 5000 | 500 | 服务器内部错误 |

## 业务规则

1. **租户隔离**：租户管理员只能管理自己租户下的分类
2. **层级关系**：分类支持多级嵌套，通过parent字段建立父子关系
3. **删除限制**：
   - 有文章关联的分类不能删除
   - 有子分类的分类不能删除
4. **排序规则**：默认按置顶、排序顺序、ID排序
