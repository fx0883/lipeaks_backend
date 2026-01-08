# 租户管理员 CMS 标签管理 API 文档

## 适用范围
- 面向租户管理员（Tenant Admin）用户
- 用于管理本租户下的文章标签和标签组
- 租户管理员只能管理自己租户下的标签

## 基础信息
- 标签组前缀：`/api/v1/cms/tag-groups/`
- 标签前缀：`/api/v1/cms/tags/`
- 认证：Bearer Token（必须）
- 权限：租户管理员（is_admin=True）

---

# 一、标签组管理

## 1. 获取标签组列表

### 接口信息
- 路径：GET `/api/v1/cms/tag-groups/`
- 说明：获取本租户下的所有标签组列表

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| is_active | boolean | 否 | 是否激活 |
| search | string | 否 | 搜索关键词 |
| ordering | string | 否 | 排序字段（name/created_at） |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": [
    {
      "id": 1,
      "name": "技术栈",
      "slug": "tech-stack",
      "description": "技术栈相关标签",
      "is_active": true,
      "tag_count": 10,
      "created_at": "2024-01-10T08:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 2. 创建标签组

### 接口信息
- 路径：POST `/api/v1/cms/tag-groups/`
- 说明：创建新的标签组

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 标签组名称 |
| slug | string | 否 | 标签组别名 |
| description | string | 否 | 标签组描述 |
| is_active | boolean | 否 | 是否激活，默认true |

### 请求体示例
```json
{
  "name": "技术栈",
  "slug": "tech-stack",
  "description": "文章使用的技术栈标签",
  "is_active": true
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术栈",
    "slug": "tech-stack",
    "description": "文章使用的技术栈标签",
    "is_active": true
  }'
```

---

## 3. 获取标签组详情

### 接口信息
- 路径：GET `/api/v1/cms/tag-groups/{id}/`

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tag-groups/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 4. 更新标签组

### 接口信息
- 路径：PUT/PATCH `/api/v1/cms/tag-groups/{id}/`

### curl 调用示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/tag-groups/1/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的标签组名称"
  }'
```

---

## 5. 删除标签组

### 接口信息
- 路径：DELETE `/api/v1/cms/tag-groups/{id}/`
- 说明：删除标签组（有关联标签时不能删除）

### curl 调用示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/tag-groups/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

# 二、标签管理

## 1. 获取标签列表

### 接口信息
- 路径：GET `/api/v1/cms/tags/`
- 说明：获取本租户下的所有标签列表

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| group | integer | 否 | 标签组ID |
| is_active | boolean | 否 | 是否激活 |
| search | string | 否 | 搜索关键词 |
| ordering | string | 否 | 排序字段（name/created_at） |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 1,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 1,
        "name": "hello",
        "slug": "hello-235",
        "description": "",
        "group": null,
        "group_name": null,
        "created_at": "2025-10-08T12:58:55.756408Z",
        "updated_at": "2025-10-08T12:58:55.756457Z",
        "color": "#409EFF",
        "is_active": true,
        "tenant": 1
      }
    ]
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | integer | 标签ID |
| name | string | 标签名称 |
| slug | string | 标签别名 |
| description | string | 标签描述 |
| group | integer | 所属标签组ID |
| group_name | string | 所属标签组名称 |
| color | string | 标签颜色（十六进制） |
| icon | string | 标签图标 |
| is_active | boolean | 是否激活 |
| article_count | integer | 关联文章数量 |

### curl 调用示例
```bash
# 获取所有标签
curl -X GET "http://localhost:8000/api/v1/cms/tags/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按标签组筛选
curl -X GET "http://localhost:8000/api/v1/cms/tags/?group=1" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 搜索标签
curl -X GET "http://localhost:8000/api/v1/cms/tags/?search=python" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 2. 创建标签

### 接口信息
- 路径：POST `/api/v1/cms/tags/`
- 说明：创建新标签

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 标签名称 |
| slug | string | 否 | 标签别名 |
| description | string | 否 | 标签描述 |
| group | integer | 否 | 所属标签组ID |
| color | string | 否 | 标签颜色（十六进制） |
| icon | string | 否 | 标签图标 |
| is_active | boolean | 否 | 是否激活，默认true |

### 请求体示例
```json
{
  "name": "Python",
  "slug": "python",
  "description": "Python编程语言相关文章",
  "group": 1,
  "color": "#3776AB",
  "is_active": true
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/tags/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python",
    "slug": "python",
    "description": "Python编程语言相关文章",
    "group": 1,
    "color": "#3776AB"
  }'
```

---

## 3. 获取标签详情

### 接口信息
- 路径：GET `/api/v1/cms/tags/{id}/`

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tags/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 4. 更新标签

### 接口信息
- 路径：PUT/PATCH `/api/v1/cms/tags/{id}/`

### curl 调用示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/tags/1/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "color": "#FF5733"
  }'
```

---

## 5. 删除标签

### 接口信息
- 路径：DELETE `/api/v1/cms/tags/{id}/`

### curl 调用示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/tags/1/" \
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

1. **租户隔离**：租户管理员只能管理自己租户下的标签和标签组
2. **标签组关联**：标签可以归属于某个标签组，也可以不属于任何组
3. **删除限制**：有关联标签的标签组不能删除
