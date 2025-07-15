# 菜单系统 - API使用指南

## 概述

本文档详细介绍菜单系统的API接口及其使用方法，帮助前端开发人员集成菜单功能。

## 核心API

### 1. 获取菜单列表

此API返回所有菜单列表，是构建动态路由的关键接口。

- **URL**: `/api/v1/menus/`
- **方法**: GET
- **认证**: 需要JWT认证
- **权限**: 已登录用户

#### 响应格式

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

### 2. 获取树形菜单结构

此API返回树形结构的菜单数据，包含父子关系

- **URL**: `/api/v1/menus/tree/`
- **方法**: GET
- **认证**: 需要JWT认证
- **权限**: 已登录用户

#### 响应格式

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

### 3. 菜单管理API

#### 3.1 创建菜单

- **URL**: `/api/v1/menus/`
- **方法**: POST
- **认证**: 需要JWT认证
- **权限**: 管理员

**请求体示例**:

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

**响应示例**:

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

#### 3.2 获取单个菜单

- **URL**: `/api/v1/menus/{id}/`
- **方法**: GET
- **认证**: 需要JWT认证
- **权限**: 管理员

**响应示例**:

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

#### 3.3 更新菜单 (完整更新)

- **URL**: `/api/v1/menus/{id}/`
- **方法**: PUT
- **认证**: 需要JWT认证
- **权限**: 管理员

**请求体示例**:

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

**响应示例**:

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

#### 3.4 更新菜单 (部分更新)

- **URL**: `/api/v1/menus/{id}/`
- **方法**: PATCH
- **认证**: 需要JWT认证
- **权限**: 管理员

**请求体示例**:

```json
{
  "title": "更新后的标题",
  "is_active": false
}
```

**响应示例**:

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

#### 3.5 删除菜单

- **URL**: `/api/v1/menus/{id}/`
- **方法**: DELETE
- **认证**: 需要JWT认证
- **权限**: 管理员

**响应**:
- 状态码: 204 No Content (无响应体)

## 菜单数据字段说明

| 字段名 | 类型 | 是否必填 | 说明 |
|-------|-----|---------|------|
| name | string | 是 | 菜单名称 |
| code | string | 是 | 菜单唯一标识码 |
| path | string | 是 | 菜单路径 |
| component | string | 是 | 组件路径 |
| redirect | string | 否 | 重定向地址 |
| title | string | 否 | 菜单标题 |
| icon | string | 否 | 菜单图标 |
| extra_icon | string | 否 | 额外图标 |
| rank | integer | 是 | 排序值，数值越小越靠前 |
| show_link | boolean | 否 | 是否显示 |
| show_parent | boolean | 否 | 是否显示父级菜单 |
| roles | array | 否 | 菜单角色 |
| auths | array | 否 | 菜单权限 |
| keep_alive | boolean | 否 | 是否缓存路由 |
| frame_src | string | 否 | iframe链接 |
| frame_loading | boolean | 否 | 是否显示iframe加载动画 |
| hidden_tag | boolean | 否 | 是否隐藏标签 |
| dynamic_level | integer | 否 | 动态路由层级 |
| active_path | string | 否 | 激活菜单的路径 |
| parent_id | integer | 否 | 父级菜单ID，顶级菜单为null |
| is_active | boolean | 否 | 是否启用 |
| remarks | string | 否 | 备注信息 |

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

## 最佳实践

1. 创建菜单时，请确保必填字段都已提供
2. 父级菜单的parent_id应为null，而不是0
3. 更新菜单时，可以只提供需要修改的字段 (PATCH方法)
4. 菜单的rank字段决定了显示顺序，确保设置合理的值
5. 删除父级菜单前，建议先处理其所有子菜单

## 常见问题

1. **问题**: 创建菜单时报错
   **解决**: 检查必填字段是否完整，parent_id是否存在

2. **问题**: 菜单顺序不正确
   **解决**: 确认rank字段设置正确

3. **问题**: 树形结构不正确
   **解决**: 检查parent_id关系是否合理，注意顶级菜单parent_id应为null

4. **问题**: 菜单不显示
   **解决**: 确认is_active为true，show_link为true 