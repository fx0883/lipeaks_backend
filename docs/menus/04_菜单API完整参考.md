# 菜单API完整参考

本文档提供菜单管理模块所有API端点的详细参考信息。

## API端点概览

| 端点 | 方法 | 描述 | 权限要求 |
|------|------|------|---------|
| `/api/v1/menus/` | GET | 获取菜单列表 | 已登录用户 |
| `/api/v1/menus/` | POST | 创建新菜单 | 管理员 |
| `/api/v1/menus/{id}/` | GET | 获取菜单详情 | 已登录用户 |
| `/api/v1/menus/{id}/` | PUT | 完整更新菜单 | 管理员 |
| `/api/v1/menus/{id}/` | PATCH | 部分更新菜单 | 管理员 |
| `/api/v1/menus/{id}/` | DELETE | 删除菜单 | 管理员 |
| `/api/v1/menus/tree/` | GET | 获取树形结构菜单 | 已登录用户 |

## 1. 获取菜单列表

### 请求

```
GET /api/v1/menus/
```

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| search | string | 否 | 搜索关键词，支持菜单名称、路径和组件搜索 |
| is_active | boolean | 否 | 过滤活动状态的菜单 (true/false) |
| parent_id | integer | 否 | 过滤特定父菜单下的子菜单 |
| page | integer | 否 | 页码，默认为1 |
| page_size | integer | 否 | 每页条数，默认为10 |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 6,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 1,
        "name": "仪表盘",
        "code": "dashboard",
        "path": "/dashboard",
        "component": "layout/Dashboard",
        "redirect": null,
        "title": "",
        "icon": "dashboard",
        "extra_icon": null,
        "rank": 1,
        "show_link": true,
        "show_parent": true,
        "roles": [],
        "auths": [],
        "keep_alive": false,
        "frame_src": null,
        "frame_loading": true,
        "hidden_tag": false,
        "dynamic_level": null,
        "active_path": null,
        "transition_name": null,
        "enter_transition": null,
        "leave_transition": null,
        "parent_id": null,
        "is_active": true,
        "remarks": "系统仪表盘",
        "created_at": "2023-01-01T08:00:00+08:00",
        "updated_at": "2023-01-01T08:00:00+08:00"
      },
      // 更多菜单项...
    ]
  }
}
```

**错误响应 (403 Forbidden)**

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": null
}
```

## 2. 创建新菜单

### 请求

```
POST /api/v1/menus/
```

### 请求体

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| name | string | 是 | 菜单名称 |
| code | string | 是 | 菜单唯一标识码 |
| path | string | 是 | 菜单路径 |
| component | string | 是 | 组件路径 |
| redirect | string | 否 | 重定向地址 |
| title | string | 否 | 菜单标题 |
| icon | string | 否 | 菜单图标 |
| extra_icon | string | 否 | 额外图标 |
| rank | integer | 是 | 排序值，数值越小越靠前 |
| show_link | boolean | 否 | 是否显示，默认为true |
| show_parent | boolean | 否 | 是否显示父级菜单，默认为true |
| roles | array | 否 | 菜单角色列表 |
| auths | array | 否 | 菜单权限列表 |
| keep_alive | boolean | 否 | 是否缓存路由，默认为false |
| frame_src | string | 否 | iframe链接 |
| frame_loading | boolean | 否 | 是否显示iframe加载动画，默认为true |
| hidden_tag | boolean | 否 | 是否隐藏标签，默认为false |
| dynamic_level | integer | 否 | 动态路由层级 |
| active_path | string | 否 | 激活菜单的路径 |
| parent_id | integer | 否 | 父级菜单ID，顶级菜单为null |
| is_active | boolean | 否 | 是否启用，默认为true |
| remarks | string | 否 | 备注信息 |

### 请求体示例

```json
{
  "name": "reports",
  "code": "reports_management",
  "path": "/reports",
  "component": "layout/Reports",
  "redirect": null,
  "title": "报表管理",
  "icon": "chart",
  "extra_icon": null,
  "rank": 5,
  "show_link": true,
  "show_parent": true,
  "roles": [],
  "auths": [],
  "keep_alive": false,
  "frame_src": null,
  "frame_loading": true,
  "hidden_tag": false,
  "dynamic_level": null,
  "active_path": null,
  "transition_name": null,
  "enter_transition": null,
  "leave_transition": null,
  "parent_id": null,
  "is_active": true,
  "remarks": "报表管理模块"
}
```

### 响应

**成功响应 (201 Created)**

```json
{
  "success": true,
  "code": "reports_management",
  "message": "操作成功",
  "data": {
    "id": 8,
    "name": "reports",
    "path": "/reports",
    "component": "layout/Reports",
    "redirect": null,
    "title": "报表管理",
    "icon": "chart",
    "extra_icon": null,
    "rank": 5,
    "show_link": true,
    "show_parent": true,
    "roles": [],
    "auths": [],
    "keep_alive": false,
    "frame_src": null,
    "frame_loading": true,
    "hidden_tag": false,
    "dynamic_level": null,
    "active_path": null,
    "transition_name": null,
    "enter_transition": null,
    "leave_transition": null,
    "parent_id": null,
    "is_active": true,
    "remarks": "报表管理模块",
    "created_at": "2025-06-17T13:17:34.318045+08:00",
    "updated_at": "2025-06-17T13:17:34.318056+08:00"
  }
}
```

**错误响应 (400 Bad Request)**

```json
{
  "success": false,
  "code": 4000,
  "message": "参数错误",
  "data": {
    "name": ["菜单名称已存在"],
    "code": ["菜单标识码已存在"]
  }
}
```

## 3. 获取菜单详情

### 请求

```
GET /api/v1/menus/{id}/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 菜单ID |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": "reports_management",
  "message": "操作成功",
  "data": {
    "id": 8,
    "name": "reports",
    "path": "/reports",
    "component": "layout/Reports",
    "redirect": null,
    "title": "报表管理",
    "icon": "chart",
    "extra_icon": null,
    "rank": 5,
    "show_link": true,
    "show_parent": true,
    "roles": [],
    "auths": [],
    "keep_alive": false,
    "frame_src": null,
    "frame_loading": true,
    "hidden_tag": false,
    "dynamic_level": null,
    "active_path": null,
    "transition_name": null,
    "enter_transition": null,
    "leave_transition": null,
    "parent_id": null,
    "is_active": true,
    "remarks": "报表管理模块",
    "created_at": "2025-06-17T13:17:34.318045+08:00",
    "updated_at": "2025-06-17T13:17:34.318056+08:00"
  }
}
```

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "菜单不存在",
  "data": null
}
```

## 4. 完整更新菜单

### 请求

```
PUT /api/v1/menus/{id}/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 菜单ID |

### 请求体

请求体字段与创建菜单相同，但不需要提供所有字段，只需要提供要更新的字段。

### 请求体示例

```json
{
  "name": "reports_updated",
  "code": "reports_management",
  "path": "/reports",
  "title": "报表管理更新版",
  "icon": "chart-updated",
  "rank": 6,
  "parent_id": null,
  "is_active": true
}
```

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": "reports_management",
  "message": "操作成功",
  "data": {
    "id": 8,
    "name": "reports_updated",
    "path": "/reports",
    "component": "layout/Reports",
    "redirect": null,
    "title": "报表管理更新版",
    "icon": "chart-updated",
    "extra_icon": null,
    "rank": 6,
    "show_link": true,
    "show_parent": true,
    "roles": [],
    "auths": [],
    "keep_alive": false,
    "frame_src": null,
    "frame_loading": true,
    "hidden_tag": false,
    "dynamic_level": null,
    "active_path": null,
    "transition_name": null,
    "enter_transition": null,
    "leave_transition": null,
    "parent_id": null,
    "is_active": true,
    "remarks": "报表管理模块",
    "created_at": "2025-06-17T13:17:34.318045+08:00",
    "updated_at": "2025-06-17T13:18:11.794225+08:00"
  }
}
```

**错误响应 (400 Bad Request)**

```json
{
  "success": false,
  "code": 4000,
  "message": "参数错误",
  "data": {
    "parent_id": ["指定的父菜单不存在"]
  }
}
```

## 5. 部分更新菜单

### 请求

```
PATCH /api/v1/menus/{id}/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 菜单ID |

### 请求体

只需要提供要更新的字段。

### 请求体示例

```json
{
  "title": "更新后的标题",
  "is_active": false
}
```

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": "reports_management",
  "message": "操作成功",
  "data": {
    "id": 8,
    "name": "reports_updated",
    "path": "/reports",
    "component": "layout/Reports",
    "redirect": null,
    "title": "更新后的标题",
    "icon": "chart-updated",
    "extra_icon": null,
    "rank": 6,
    "show_link": true,
    "show_parent": true,
    "roles": [],
    "auths": [],
    "keep_alive": false,
    "frame_src": null,
    "frame_loading": true,
    "hidden_tag": false,
    "dynamic_level": null,
    "active_path": null,
    "transition_name": null,
    "enter_transition": null,
    "leave_transition": null,
    "parent_id": null,
    "is_active": false,
    "remarks": "报表管理模块",
    "created_at": "2025-06-17T13:17:34.318045+08:00",
    "updated_at": "2025-06-17T13:18:24.231802+08:00"
  }
}
```

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "菜单不存在",
  "data": null
}
```

## 6. 删除菜单

### 请求

```
DELETE /api/v1/menus/{id}/
```

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 菜单ID |

### 响应

**成功响应 (204 No Content)**

无响应体

**错误响应 (404 Not Found)**

```json
{
  "success": false,
  "code": 4004,
  "message": "菜单不存在",
  "data": null
}
```

**错误响应 (400 Bad Request)**

```json
{
  "success": false,
  "code": 4000,
  "message": "无法删除菜单",
  "data": {
    "detail": ["该菜单下有子菜单，请先删除子菜单"]
  }
}
```

## 7. 获取树形结构菜单

### 请求

```
GET /api/v1/menus/tree/
```

### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| is_active | boolean | 否 | 过滤活动状态的菜单 (true/false) |

### 响应

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "name": "仪表盘",
      "code": "dashboard",
      "path": "/dashboard",
      "component": "layout/Dashboard",
      "redirect": null,
      "title": "",
      "icon": "dashboard",
      "extra_icon": null,
      "rank": 1,
      "show_link": true,
      "show_parent": true,
      "roles": [],
      "auths": [],
      "keep_alive": false,
      "frame_src": null,
      "frame_loading": true,
      "hidden_tag": false,
      "dynamic_level": null,
      "active_path": null,
      "transition_name": null,
      "enter_transition": null,
      "leave_transition": null,
      "parent_id": null,
      "is_active": true,
      "remarks": "系统仪表盘",
      "created_at": "2023-01-01T08:00:00+08:00",
      "updated_at": "2023-01-01T08:00:00+08:00",
      "children": []
    },
    {
      "id": 2,
      "name": "用户管理",
      "code": "user_management",
      "path": "/users",
      "component": "layout/UserManagement",
      "redirect": null,
      "title": "",
      "icon": "user-group",
      "extra_icon": null,
      "rank": 2,
      "show_link": true,
      "show_parent": true,
      "roles": [],
      "auths": [],
      "keep_alive": false,
      "frame_src": null,
      "frame_loading": true,
      "hidden_tag": false,
      "dynamic_level": null,
      "active_path": null,
      "transition_name": null,
      "enter_transition": null,
      "leave_transition": null,
      "parent_id": null,
      "is_active": true,
      "remarks": "用户管理模块",
      "created_at": "2023-01-01T08:00:00+08:00",
      "updated_at": "2023-01-01T08:00:00+08:00",
      "children": [
        {
          "id": 3,
          "name": "用户列表",
          "code": "user_list",
          "path": "/users/list",
          "component": "views/users/UserList",
          "redirect": null,
          "title": "",
          "icon": "list",
          "extra_icon": null,
          "rank": 1,
          "show_link": true,
          "show_parent": true,
          "roles": [],
          "auths": [],
          "keep_alive": false,
          "frame_src": null,
          "frame_loading": true,
          "hidden_tag": false,
          "dynamic_level": null,
          "active_path": null,
          "transition_name": null,
          "enter_transition": null,
          "leave_transition": null,
          "parent_id": 2,
          "is_active": true,
          "remarks": "用户列表",
          "created_at": "2023-01-01T08:00:00+08:00",
          "updated_at": "2023-01-01T08:00:00+08:00",
          "children": []
        }
      ]
    },
    // 更多菜单项...
  ]
}
```

**错误响应 (403 Forbidden)**

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": null
}
```

## 状态码说明

| 状态码 | 描述 |
|-------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功，无内容返回 |
| 400 | 请求参数错误 |
| 401 | 未认证或认证失败 |
| 403 | 权限不足 |
| 404 | 请求的资源不存在 |
| 500 | 服务器内部错误 |

## 业务状态码说明

| 业务状态码 | 描述 |
|----------|------|
| 2000 | 操作成功 |
| 4000 | 参数错误 |
| 4001 | 未认证或认证失败 |
| 4003 | 权限不足 |
| 4004 | 资源不存在 |
| 5000 | 服务器内部错误 |

## 菜单字段说明

| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | integer | 菜单唯一标识符 |
| name | string | 菜单名称 |
| code | string | 菜单唯一标识码 |
| path | string | 菜单路径 |
| component | string | 组件路径 |
| redirect | string | 重定向地址 |
| title | string | 菜单标题 |
| icon | string | 菜单图标 |
| extra_icon | string | 额外图标 |
| rank | integer | 排序值，数值越小越靠前 |
| show_link | boolean | 是否在菜单中显示 |
| show_parent | boolean | 是否显示父级菜单 |
| roles | array | 菜单角色列表 |
| auths | array | 菜单权限列表 |
| keep_alive | boolean | 是否缓存路由 |
| frame_src | string | iframe链接地址 |
| frame_loading | boolean | iframe是否开启首次加载动画 |
| hidden_tag | boolean | 禁止添加到标签页 |
| dynamic_level | integer | 标签页最大数量 |
| active_path | string | 激活菜单的路径 |
| parent_id | integer | 父级菜单ID，顶级菜单为null |
| is_active | boolean | 是否启用 |
| remarks | string | 备注信息 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

## 重要提示

### 关于parent_id字段

在创建或更新菜单时，请注意以下关于parent_id的重要规则：

1. **顶级菜单**：对于顶级菜单，`parent_id`必须设置为`null`，而不是0或其他值
2. **子菜单**：子菜单的`parent_id`必须是一个已存在的菜单ID
3. **常见错误**：将顶级菜单的`parent_id`设置为0会导致创建失败，因为系统中不存在ID为0的菜单

示例（正确）：
```json
// 顶级菜单
{
  "name": "系统设置",
  "parent_id": null
}

// 子菜单
{
  "name": "用户管理",
  "parent_id": 6  // 假设6是"系统设置"菜单的ID
}
```

示例（错误）：
```json
// 错误：使用0作为顶级菜单的parent_id
{
  "name": "系统设置",
  "parent_id": 0  // 错误！应该使用null
}
```

## 常见问题处理

### 认证失败

```json
{
  "success": false,
  "code": 4001,
  "message": "认证失败，请重新登录",
  "data": null
}
```

### 权限不足

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足，无法访问该资源",
  "data": null
}
```

### 菜单不存在

```json
{
  "success": false,
  "code": 4004,
  "message": "菜单不存在",
  "data": null
}
```

### 服务器错误

```json
{
  "success": false,
  "code": 5000,
  "message": "服务器内部错误",
  "data": null
}
``` 