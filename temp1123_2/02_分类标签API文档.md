# CMS API 文档 - 分类和标签管理

## 租户控制规则
- **Admin用户**: 不需要`X-Tenant-ID`头
- **Member/匿名用户**: 必须提供`X-Tenant-ID: 3`头

---

## 分类管理 API

### 1. 获取分类列表

```bash
# 匿名用户
curl -X GET "http://0.0.0.0:8000/api/v1/cms/categories/" \
  -H "X-Tenant-ID: 3"

# 带过滤
curl -X GET "http://0.0.0.0:8000/api/v1/cms/categories/?is_active=true&parent=1" \
  -H "X-Tenant-ID: 3"
```

**查询参数**:
- `parent`: 父分类ID
- `is_active`: 是否激活（true/false）
- `is_pinned`: 是否置顶
- `search`: 搜索关键词

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "results": [
      {
        "id": 1,
        "slug": "tech-blog",
        "name": "技术博客",
        "description": "技术相关文章",
        "parent": null,
        "is_active": true,
        "is_pinned": false,
        "sort_order": 0,
        "created_at": "2025-10-26T06:05:30.472659Z"
      }
    ]
  }
}
```

### 2. 获取分类树

```bash
curl -X GET "http://0.0.0.0:8000/api/v1/cms/categories/tree/" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": [
    {
      "id": 1,
      "name": "技术博客",
      "slug": "tech-blog",
      "children": [
        {
          "id": 2,
          "name": "Python教程",
          "slug": "python-tutorial",
          "children": []
        }
      ]
    }
  ]
}
```

### 3. 创建分类 (Admin)

**⚠️ 重要**: 分类需要提供`translations`字段，用于多语言支持。

```bash
curl -X POST "http://0.0.0.0:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新分类",
    "slug": "new-category",
    "description": "分类描述",
    "translations": {
      "zh-hans": {
        "name": "新分类",
        "description": "分类描述"
      }
    },
    "parent": null,
    "is_active": true,
    "sort_order": 0
  }'
```

**请求字段**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 分类名称 |
| slug | string | 是 | URL别名 |
| description | string | 否 | 描述 |
| translations | object | 是 | 翻译内容（zh-hans, en等） |
| parent | integer | 否 | 父分类ID |
| is_active | boolean | 否 | 是否激活（默认true） |
| is_pinned | boolean | 否 | 是否置顶（默认false） |
| sort_order | integer | 否 | 排序（默认0） |
| cover_image | string | 否 | 封面图 |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "id": 60,
    "slug": "new-category",
    "name": "新分类",
    "description": "分类描述",
    "parent": null,
    "is_active": true
  }
}
```

### 4. 获取分类详情

```bash
curl -X GET "http://0.0.0.0:8000/api/v1/cms/categories/60/" \
  -H "X-Tenant-ID: 3"
```

### 5. 更新分类 (Admin)

```bash
# 完整更新 (PUT)
curl -X PUT "http://0.0.0.0:8000/api/v1/cms/categories/60/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的分类",
    "slug": "new-category",
    "description": "更新描述",
    "translations": {
      "zh-hans": {
        "name": "更新后的分类",
        "description": "更新描述"
      }
    }
  }'

# 部分更新 (PATCH)
curl -X PATCH "http://0.0.0.0:8000/api/v1/cms/categories/60/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "translations": {
      "zh-hans": {
        "name": "PATCH更新名称"
      }
    }
  }'
```

### 6. 删除分类 (Admin)

```bash
curl -X DELETE "http://0.0.0.0:8000/api/v1/cms/categories/60/" \
  -H "Authorization: Bearer {admin_token}"
```

**注意**: 
- 如果分类下有文章，无法删除
- 如果有子分类，需先删除所有子分类

---

## 标签管理 API

### 1. 获取标签列表

```bash
curl -X GET "http://0.0.0.0:8000/api/v1/cms/tags/" \
  -H "X-Tenant-ID: 3"

# 按标签组过滤
curl -X GET "http://0.0.0.0:8000/api/v1/cms/tags/?group=1" \
  -H "X-Tenant-ID: 3"
```

**查询参数**:
- `group`: 标签组ID
- `is_active`: 是否激活
- `search`: 搜索关键词

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "results": [
      {
        "id": 2,
        "name": "Python",
        "slug": "python",
        "description": null,
        "group": null,
        "group_name": null,
        "color": "#3776AB",
        "is_active": true,
        "tenant": 3,
        "created_at": "2025-11-23T10:59:05.123066Z"
      }
    ]
  }
}
```

### 2. 创建标签 (Admin)

```bash
curl -X POST "http://0.0.0.0:8000/api/v1/cms/tags/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Django",
    "slug": "django",
    "description": "Django框架相关",
    "group": 1,
    "color": "#092E20",
    "is_active": true
  }'
```

**请求字段**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 标签名称 |
| slug | string | 是 | URL别名 |
| description | string | 否 | 描述 |
| group | integer | 否 | 标签组ID |
| color | string | 否 | 颜色代码（如#3776AB） |
| is_active | boolean | 否 | 是否激活（默认true） |

### 3. 更新标签 (Admin)

```bash
curl -X PATCH "http://0.0.0.0:8000/api/v1/cms/tags/2/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python 3",
    "description": "Python 3相关内容"
  }'
```

### 4. 删除标签 (Admin)

```bash
curl -X DELETE "http://0.0.0.0:8000/api/v1/cms/tags/2/" \
  -H "Authorization: Bearer {admin_token}"
```

**注意**: 如果标签关联了文章，无法删除

### 5. 获取标签使用统计

```bash
curl -X GET "http://0.0.0.0:8000/api/v1/cms/tags/usage-stats/" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": [
    {
      "id": 3,
      "name": "Python",
      "slug": "python",
      "color": "#3776AB",
      "articles_count": 25
    },
    {
      "id": 5,
      "name": "Django",
      "slug": "django",
      "color": "#092E20",
      "articles_count": 15
    }
  ]
}
```

---

## 标签组管理 API

### 1. 获取标签组列表

```bash
curl -X GET "http://0.0.0.0:8000/api/v1/cms/tag-groups/" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "results": [
      {
        "id": 1,
        "name": "编程语言",
        "slug": "programming-languages",
        "description": "各种编程语言",
        "is_active": true,
        "created_at": "2025-11-23T12:00:00.000000Z"
      }
    ]
  }
}
```

### 2. 创建标签组 (Admin)

```bash
curl -X POST "http://0.0.0.0:8000/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术栈",
    "slug": "tech-stack",
    "description": "技术栈相关标签",
    "is_active": true
  }'
```

**请求字段**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 标签组名称 |
| slug | string | 是 | URL别名 |
| description | string | 否 | 描述 |
| is_active | boolean | 否 | 是否激活（默认true） |

### 3. 更新标签组 (Admin)

```bash
# 部分更新
curl -X PATCH "http://0.0.0.0:8000/api/v1/cms/tag-groups/1/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的标签组"
  }'
```

### 4. 删除标签组 (Admin)

```bash
curl -X DELETE "http://0.0.0.0:8000/api/v1/cms/tag-groups/1/" \
  -H "Authorization: Bearer {admin_token}"
```

**注意**: 如果标签组下有标签，无法删除

---

## 完整的使用流程示例

### 1. 创建内容分类体系

```bash
# Step 1: 创建顶级分类
curl -X POST "http://0.0.0.0:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术博客",
    "slug": "tech-blog",
    "translations": {
      "zh-hans": {
        "name": "技术博客",
        "description": "技术相关文章"
      }
    }
  }'
# 返回: {"id": 1, ...}

# Step 2: 创建子分类
curl -X POST "http://0.0.0.0:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python教程",
    "slug": "python-tutorial",
    "parent": 1,
    "translations": {
      "zh-hans": {
        "name": "Python教程"
      }
    }
  }'

# Step 3: 创建标签组
curl -X POST "http://0.0.0.0:8000/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "编程语言",
    "slug": "languages"
  }'
# 返回: {"id": 1, ...}

# Step 4: 创建标签
curl -X POST "http://0.0.0.0:8000/api/v1/cms/tags/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python",
    "slug": "python",
    "group": 1,
    "color": "#3776AB"
  }'

# Step 5: 查看分类树
curl -X GET "http://0.0.0.0:8000/api/v1/cms/categories/tree/" \
  -H "X-Tenant-ID: 3"
```

---

## 错误处理

### 常见错误

1. **缺少translations字段**
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "translations": ["该字段是必填项。"]
  }
}
```

2. **删除有关联的分类/标签**
```json
{
  "success": false,
  "code": 4000,
  "message": "无法删除有关联文章的分类，请先移除关联的文章"
}
```

3. **租户权限错误**
```json
{
  "success": false,
  "code": 4100,
  "message": "Tenant operation failed"
}
```
