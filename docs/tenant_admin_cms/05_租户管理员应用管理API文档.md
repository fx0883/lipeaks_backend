# 租户管理员 应用管理 API 文档

## 适用范围
- 面向租户管理员（Tenant Admin）用户
- 用于管理本租户下的应用
- 租户管理员只能管理自己租户下的应用

## 基础信息
- 前缀：`/api/v1/applications/`
- 认证：Bearer Token（必须）
- 权限：租户管理员（is_admin=True）

---

## 1. 获取应用列表

### 接口信息
- 路径：GET `/api/v1/applications/`
- 说明：获取本租户下的所有应用列表，支持分页、过滤和搜索

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| status | string | 否 | 应用状态 |
| is_active | boolean | 否 | 是否激活 |
| search | string | 否 | 搜索关键词（名称、代码、描述） |
| ordering | string | 否 | 排序字段（created_at/updated_at/name/code） |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "name": "主站",
        "code": "main-site",
        "description": "公司主站应用",
        "icon": "/media/apps/main.png",
        "status": "active",
        "is_active": true,
        "created_at": "2024-01-10T08:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### curl 调用示例
```bash
# 获取应用列表
curl -X GET "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 搜索应用
curl -X GET "http://localhost:8000/api/v1/applications/?search=主站" \
  -H "Authorization: Bearer eyJhbGciOi..."

# 按状态筛选
curl -X GET "http://localhost:8000/api/v1/applications/?is_active=true" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 2. 创建应用

### 接口信息
- 路径：POST `/api/v1/applications/`
- 说明：创建新应用

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 应用名称 |
| code | string | 是 | 应用代码（唯一标识） |
| description | string | 否 | 应用描述 |
| icon | string | 否 | 应用图标URL |
| status | string | 否 | 应用状态，默认active |
| is_active | boolean | 否 | 是否激活，默认true |

### 请求体示例
```json
{
  "name": "主站",
  "code": "main-site",
  "description": "公司主站应用",
  "is_active": true
}
```

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "主站",
    "code": "main-site",
    "description": "公司主站应用",
    "is_active": true
  }'
```

---

## 3. 获取应用详情

### 接口信息
- 路径：GET `/api/v1/applications/{id}/`

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 4. 更新应用

### 接口信息
- 路径：PUT/PATCH `/api/v1/applications/{id}/`

### curl 调用示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "description": "更新后的描述"
  }'
```

---

## 5. 删除应用

### 接口信息
- 路径：DELETE `/api/v1/applications/{id}/`

### curl 调用示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/applications/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 6. 获取应用统计

### 接口信息
- 路径：GET `/api/v1/applications/{id}/statistics/`
- 说明：获取应用的统计信息

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "licenses": {
      "total": 100,
      "active": 85
    },
    "feedbacks": {
      "total": 50,
      "open": 10
    },
    "articles": {
      "total": 30
    }
  }
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/applications/1/statistics/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 7. 获取应用关联文章

### 接口信息
- 路径：GET `/api/v1/applications/{id}/articles/`
- 说明：获取应用关联的所有文章

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/applications/1/articles/" \
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
