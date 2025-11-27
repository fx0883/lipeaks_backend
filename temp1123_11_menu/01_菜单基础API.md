# 菜单基础API

## 1. 获取菜单列表

### 接口信息
- **URL**: `/api/v1/menus/`
- **方法**: `GET`
- **权限**: 租户管理员及以上
- **说明**: 获取系统中的所有菜单项，租户管理员只能获取分配给自己的菜单

### 请求参数

#### Query参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| is_active | boolean | 否 | 筛选激活/未激活的菜单 |
| parent_id | integer | 否 | 筛选特定父菜单的子菜单，传"null"获取顶级菜单 |
| search | string | 否 | 搜索菜单名称或标识符 |
| page | integer | 否 | 页码，默认为1 |
| page_size | integer | 否 | 每页数量，默认为10 |

### 返回格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 42,
      "next": "http://localhost:8000/api/v1/menus/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 5
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
        "transition_name": null,
        "enter_transition": null,
        "leave_transition": null,
        "parent_id": 22,
        "is_active": true,
        "remarks": null,
        "created_at": "2025-06-24T14:19:04.706365Z",
        "updated_at": "2025-06-26T10:57:20.980793Z"
      }
    ]
  }
}
```

### curl示例

```bash
# 获取所有菜单
curl -X GET "http://localhost:8000/api/v1/menus/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# 获取激活的菜单
curl -X GET "http://localhost:8000/api/v1/menus/?is_active=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# 获取顶级菜单
curl -X GET "http://localhost:8000/api/v1/menus/?parent_id=null" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# 搜索菜单
curl -X GET "http://localhost:8000/api/v1/menus/?search=article" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 2. 获取单个菜单

### 接口信息
- **URL**: `/api/v1/menus/{id}/`
- **方法**: `GET`
- **权限**: 租户管理员及以上
- **说明**: 获取指定ID的菜单详情

### 请求参数

#### Path参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 菜单ID |

### 返回格式

```json
{
  "success": true,
  "code": "articleManagement",
  "message": "操作成功",
  "data": {
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
    "transition_name": null,
    "enter_transition": null,
    "leave_transition": null,
    "parent_id": 22,
    "is_active": true,
    "remarks": null,
    "created_at": "2025-06-24T14:19:04.706365Z",
    "updated_at": "2025-06-26T10:57:20.980793Z"
  }
}
```

### curl示例

```bash
curl -X GET "http://localhost:8000/api/v1/menus/23/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 3. 创建菜单

### 接口信息
- **URL**: `/api/v1/menus/`
- **方法**: `POST`
- **权限**: 租户管理员及以上
- **说明**: 创建新的菜单项

### 请求参数

#### Body参数（JSON）
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 路由名称，唯一标识 |
| code | string | 是 | 菜单编码，唯一标识 |
| path | string | 是 | 路由路径 |
| title | string | 是 | 菜单标题 |
| component | string | 否 | 前端组件路径 |
| redirect | string | 否 | 重定向路径 |
| icon | string | 否 | 图标名称 |
| extra_icon | string | 否 | 额外图标 |
| rank | integer | 否 | 菜单排序，默认0 |
| show_link | boolean | 否 | 是否在菜单中显示，默认true |
| show_parent | boolean | 否 | 是否显示父级菜单，默认true |
| roles | array | 否 | 页面级别权限设置 |
| auths | array | 否 | 按钮级别权限设置 |
| keep_alive | boolean | 否 | 是否缓存路由页面，默认false |
| frame_src | string | 否 | iframe链接地址 |
| frame_loading | boolean | 否 | iframe是否开启首次加载动画 |
| hidden_tag | boolean | 否 | 禁止添加到标签页 |
| dynamic_level | integer | 否 | 标签页最大数量 |
| active_path | string | 否 | 激活菜单的路径 |
| transition_name | string | 否 | 页面动画名称 |
| enter_transition | string | 否 | 进场动画 |
| leave_transition | string | 否 | 离场动画 |
| parent_id | integer | 否 | 父菜单ID，不传或传null表示顶级菜单 |
| is_active | boolean | 否 | 是否启用，默认true |
| remarks | string | 否 | 备注说明 |

### 返回格式

```json
{
  "success": true,
  "code": "test_menu_tenant",
  "message": "操作成功",
  "data": {
    "name": "test_menu_tenant",
    "code": "test_menu_tenant",
    "path": "/test_tenant",
    "component": null,
    "redirect": null,
    "title": "租户测试菜单",
    "icon": null,
    "extra_icon": null,
    "rank": 100,
    "roles": [],
    "auths": [],
    "frame_src": null,
    "dynamic_level": null,
    "active_path": null,
    "transition_name": null,
    "enter_transition": null,
    "leave_transition": null,
    "parent_id": null,
    "is_active": true,
    "remarks": null
  }
}
```

### curl示例

```bash
# 创建顶级菜单
curl -X POST "http://localhost:8000/api/v1/menus/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "reports",
    "code": "reports_management",
    "path": "/reports",
    "component": "layout/Reports",
    "title": "报表管理",
    "icon": "chart",
    "rank": 5,
    "show_link": true,
    "show_parent": true,
    "is_active": true,
    "remarks": "报表管理模块"
  }'

# 创建子菜单
curl -X POST "http://localhost:8000/api/v1/menus/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "monthly_report",
    "code": "monthly_report",
    "path": "/reports/monthly",
    "component": "views/reports/MonthlyReport",
    "title": "月度报表",
    "icon": "bar-chart",
    "rank": 1,
    "parent_id": 4,
    "is_active": true,
    "remarks": "月度统计报表"
  }'
```

---

## 4. 更新菜单

### 接口信息
- **URL**: `/api/v1/menus/{id}/`
- **方法**: `PUT`
- **权限**: 仅超级管理员
- **说明**: 更新指定ID的菜单，需要提供所有必填字段

### 请求参数

#### Path参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 菜单ID |

#### Body参数（JSON）
与创建菜单相同，但需要提供所有必填字段

### 返回格式

```json
{
  "success": true,
  "code": "articleManagement",
  "message": "操作成功",
  "data": {
    "id": 23,
    "name": "ArticleManagement",
    "code": "articleManagement",
    "path": "/cms/article",
    "title": "cms.menu.articleManagement",
    "icon": "ri:file-list-line",
    "rank": 0,
    "parent_id": 22,
    "is_active": true,
    // ... 其他字段
  }
}
```

### curl示例

```bash
curl -X PUT "http://localhost:8000/api/v1/menus/23/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ArticleManagement",
    "code": "articleManagement",
    "path": "/cms/article",
    "title": "cms.menu.articleManagement",
    "icon": "ri:file-list-line",
    "rank": 0,
    "parent_id": 22,
    "is_active": true
  }'
```

---

## 5. 部分更新菜单

### 接口信息
- **URL**: `/api/v1/menus/{id}/`
- **方法**: `PATCH`
- **权限**: 仅超级管理员
- **说明**: 部分更新指定ID的菜单，只需要提供需要更新的字段

### 请求参数

#### Path参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 菜单ID |

#### Body参数（JSON）
只需提供需要更新的字段

### 返回格式

```json
{
  "success": true,
  "code": "articleManagement",
  "message": "操作成功",
  "data": {
    "id": 23,
    "name": "ArticleManagement",
    "code": "articleManagement",
    // ... 完整的菜单数据
  }
}
```

### curl示例

```bash
# 只更新标题
curl -X PATCH "http://localhost:8000/api/v1/menus/23/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的标题"
  }'

# 更新是否激活状态
curl -X PATCH "http://localhost:8000/api/v1/menus/23/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

---

## 6. 删除菜单

### 接口信息
- **URL**: `/api/v1/menus/{id}/`
- **方法**: `DELETE`
- **权限**: 仅超级管理员
- **说明**: 删除指定ID的菜单（同时会删除其所有子菜单）

### 请求参数

#### Path参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 菜单ID |

### 返回格式

```
HTTP Status: 204 No Content
```

### curl示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/menus/23/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 字段说明

### 菜单字段详解

#### 基本路由配置
- **name**: 路由名称，前端路由的唯一标识，必须唯一
- **code**: 菜单编码，后端使用的唯一标识，必须唯一
- **path**: 路由路径，如 `/cms/article`
- **component**: 前端组件路径，如 `/src/views/cms/article/index.vue`
- **redirect**: 重定向路径

#### Meta相关字段（前端显示和行为）
- **title**: 菜单标题，显示在菜单栏
- **icon**: 图标名称，如 `ri:file-list-line`
- **extra_icon**: 额外图标
- **rank**: 菜单排序，数字越小越靠前
- **show_link**: 是否在菜单中显示
- **show_parent**: 是否显示父级菜单
- **roles**: 页面级别权限设置，数组格式
- **auths**: 按钮级别权限设置，数组格式
- **keep_alive**: 是否缓存路由页面
- **frame_src**: iframe链接地址
- **frame_loading**: iframe是否开启首次加载动画
- **hidden_tag**: 禁止添加到标签页
- **dynamic_level**: 标签页最大数量
- **active_path**: 激活菜单的路径

#### Transition相关字段（页面动画）
- **transition_name**: 页面动画名称
- **enter_transition**: 进场动画
- **leave_transition**: 离场动画

#### 层级关系
- **parent_id**: 父菜单ID，不传或传null表示顶级菜单

#### 状态字段
- **is_active**: 是否启用
- **remarks**: 备注说明
- **created_at**: 创建时间（只读）
- **updated_at**: 更新时间（只读）
