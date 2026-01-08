# 租户管理员 菜单管理 API 文档

## 适用范围
- 面向租户管理员（Tenant Admin）用户
- 用于管理本租户下的菜单配置
- 租户管理员只能管理自己租户下的菜单

## 基础信息
- 前缀：`/api/v1/menus/`
- 认证：Bearer Token（必须）
- 权限：租户管理员（is_admin=True）

---

## 1. 获取菜单列表

### 接口信息
- 路径：GET `/api/v1/menus/`
- 说明：获取本租户下的所有菜单列表

### 请求参数（Query）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |
| parent | integer | 否 | 父菜单ID |
| is_active | boolean | 否 | 是否激活 |
| search | string | 否 | 搜索关键词 |

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 74,
      "next": "http://localhost:8000/api/v1/menus/?page=2&tenant_id=1",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 8
    },
    "results": [
      {
        "id": 23,
        "name": "ArticleManagement",
        "code": "articleManagement",
        "path": "/cms/article",
        "component": "",
        "redirect": "",
        "title": "cms.menu.articleManagement",
        "icon": "ri:file-list-line",
        "extra_icon": null,
        "rank": 0,
        "show_link": true,
        "show_parent": true,
        "roles": [],
        "auths": [],
        "keep_alive": true,
        "frame_src": null,
        "frame_loading": false,
        "hidden_tag": false,
        "dynamic_level": null,
        "active_path": null,
        "parent_id": 22,
        "is_active": true,
        "remarks": null,
        "created_at": "2025-06-24T14:19:04.706365Z",
        "updated_at": "2025-11-23T14:34:40.172328Z"
      }
    ]
  }
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/menus/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 2. 创建菜单

### 接口信息
- 路径：POST `/api/v1/menus/`
- 说明：创建新菜单

### 请求参数（Body）

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 菜单名称 |
| path | string | 是 | 菜单路径 |
| icon | string | 否 | 菜单图标 |
| parent | integer | 否 | 父菜单ID |
| sort_order | integer | 否 | 排序顺序 |
| is_active | boolean | 否 | 是否激活，默认true |
| permission_code | string | 否 | 权限代码 |

### curl 调用示例
```bash
curl -X POST "http://localhost:8000/api/v1/menus/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "仪表盘",
    "path": "/dashboard",
    "icon": "dashboard",
    "sort_order": 0,
    "is_active": true
  }'
```

---

## 3. 获取菜单详情

### 接口信息
- 路径：GET `/api/v1/menus/{id}/`

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/menus/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 4. 更新菜单

### 接口信息
- 路径：PUT/PATCH `/api/v1/menus/{id}/`

### curl 调用示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/menus/1/" \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的菜单名称"
  }'
```

---

## 5. 删除菜单

### 接口信息
- 路径：DELETE `/api/v1/menus/{id}/`

### curl 调用示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/menus/1/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 6. 获取当前用户菜单

### 接口信息
- 路径：GET `/api/v1/menus/user/`
- 说明：获取当前登录用户有权限访问的菜单列表

### 成功响应（200）
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": [
    {
      "id": 1,
      "name": "仪表盘",
      "path": "/dashboard",
      "icon": "dashboard",
      "children": []
    }
  ]
}
```

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/menus/user/" \
  -H "Authorization: Bearer eyJhbGciOi..."
```

---

## 7. 获取管理员路由

### 接口信息
- 路径：GET `/api/v1/menus/admin/routes/`
- 说明：获取管理员前端路由配置

### curl 调用示例
```bash
curl -X GET "http://localhost:8000/api/v1/menus/admin/routes/" \
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
