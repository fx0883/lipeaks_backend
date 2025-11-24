# 菜单树形结构API

## 获取菜单树形结构

### 接口信息
- **URL**: `/api/v1/menus/tree/`
- **方法**: `GET`
- **权限**: 租户管理员及以上
- **说明**: 获取菜单的树形结构，子菜单嵌套在父菜单的children字段内

### 请求参数

#### Query参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| is_active | boolean | 否 | 筛选激活/未激活的菜单 |

### 返回格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 47,
      "name": "Member",
      "code": "member",
      "path": "/member",
      "component": "",
      "redirect": "/member/index",
      "title": "member.memberManagement",
      "icon": "ep:avatar",
      "extra_icon": null,
      "rank": 0,
      "show_link": true,
      "show_parent": true,
      "roles": [],
      "auths": [],
      "keep_alive": false,
      "frame_src": null,
      "frame_loading": false,
      "hidden_tag": false,
      "dynamic_level": null,
      "active_path": null,
      "transition_name": null,
      "enter_transition": null,
      "leave_transition": null,
      "parent_id": null,
      "is_active": true,
      "remarks": null,
      "created_at": "2025-07-06T06:12:52.289264Z",
      "updated_at": "2025-08-14T08:15:05.874042Z",
      "children": [
        {
          "id": 48,
          "name": "MemberList",
          "code": "memberList",
          "path": "/member/index",
          "component": "/src/views/member/index.vue",
          "redirect": "",
          "title": "member.memberList",
          "icon": "ri:menu-line",
          "extra_icon": null,
          "rank": 0,
          "show_link": true,
          "show_parent": true,
          "roles": [],
          "auths": [],
          "keep_alive": false,
          "frame_src": null,
          "frame_loading": false,
          "hidden_tag": false,
          "dynamic_level": null,
          "active_path": null,
          "transition_name": null,
          "enter_transition": null,
          "leave_transition": null,
          "parent_id": 47,
          "is_active": true,
          "remarks": null,
          "created_at": "2025-07-06T06:12:52.292179Z",
          "updated_at": "2025-08-14T08:21:17.824914Z",
          "children": []
        },
        {
          "id": 49,
          "name": "MemberCreate",
          "code": "memberCreate",
          "path": "/member/create",
          "component": "/src/views/member/create.vue",
          "redirect": "",
          "title": "member.createMember",
          "icon": "",
          "extra_icon": null,
          "rank": 0,
          "show_link": false,
          "show_parent": false,
          "roles": [],
          "auths": [],
          "keep_alive": false,
          "frame_src": null,
          "frame_loading": false,
          "hidden_tag": false,
          "dynamic_level": null,
          "active_path": null,
          "transition_name": null,
          "enter_transition": null,
          "leave_transition": null,
          "parent_id": 47,
          "is_active": true,
          "remarks": null,
          "created_at": "2025-07-06T06:21:50.516395Z",
          "updated_at": "2025-08-14T08:21:17.826972Z",
          "children": []
        }
      ]
    },
    {
      "id": 22,
      "name": "CMS",
      "code": "cms",
      "path": "/cms",
      "component": "",
      "redirect": "/cms/article",
      "title": "cms.menu.contentManagement",
      "icon": "ri:article-line",
      "extra_icon": null,
      "rank": 0,
      "show_link": true,
      "show_parent": true,
      "roles": [],
      "auths": [],
      "keep_alive": false,
      "frame_src": null,
      "frame_loading": false,
      "hidden_tag": false,
      "dynamic_level": null,
      "active_path": null,
      "transition_name": null,
      "enter_transition": null,
      "leave_transition": null,
      "parent_id": null,
      "is_active": true,
      "remarks": null,
      "created_at": "2025-06-24T14:19:04.704604Z",
      "updated_at": "2025-07-13T06:06:33.287657Z",
      "children": [
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
          "updated_at": "2025-06-26T10:57:20.980793Z",
          "children": []
        }
      ]
    }
  ]
}
```

### curl示例

```bash
# 获取所有菜单的树形结构
curl -X GET "http://localhost:8000/api/v1/menus/tree/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# 只获取激活的菜单树形结构
curl -X GET "http://localhost:8000/api/v1/menus/tree/?is_active=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## 特点说明

### 1. 树形结构
- 只返回顶级菜单（parent_id为null的菜单）
- 子菜单递归嵌套在父菜单的`children`字段中
- 每个节点都包含完整的菜单信息

### 2. 层级关系
```
菜单A (顶级)
├── 子菜单A1
│   ├── 孙菜单A1-1
│   └── 孙菜单A1-2
└── 子菜单A2
```

### 3. 筛选功能
- 使用`is_active`参数可以只获取激活的菜单
- 如果父菜单不活跃，其子菜单也不会显示（如果设置了is_active=true）

### 4. 排序
- 同级菜单按照`rank`字段排序
- rank值越小，排序越靠前
- rank相同时按ID排序

## 使用场景

### 1. 前端菜单渲染
前端可以直接使用这个树形结构渲染菜单导航：

```javascript
// 示例：使用返回的树形数据渲染菜单
const renderMenu = (menus) => {
  return menus.map(menu => ({
    label: menu.title,
    icon: menu.icon,
    path: menu.path,
    children: menu.children.length > 0 ? renderMenu(menu.children) : undefined
  }));
};
```

### 2. 权限控制
可以基于用户权限筛选显示的菜单：

```javascript
// 示例：根据用户角色筛选菜单
const filterMenuByRole = (menus, userRoles) => {
  return menus.filter(menu => {
    if (menu.roles.length === 0) return true; // 无权限限制
    return menu.roles.some(role => userRoles.includes(role));
  });
};
```

### 3. 菜单管理
管理后台可以使用这个API展示菜单的完整层级结构，方便编辑和管理：

```javascript
// 示例：树形菜单组件
<Tree
  data={menuTreeData}
  expandAll={true}
  showCheckbox={true}
  onCheck={handleMenuSelection}
/>
```

## 性能优化建议

1. **缓存策略**: 菜单数据相对稳定，建议在前端缓存一段时间
2. **按需加载**: 对于层级很深的菜单，可以考虑按需加载子菜单
3. **本地筛选**: 获取完整树后，可以在前端进行搜索和筛选，减少API调用

## 与普通列表接口的区别

| 特性 | 树形结构API | 列表API |
|------|------------|---------|
| 数据组织 | 嵌套树形 | 平铺列表 |
| 父子关系 | 直观展示 | 通过parent_id关联 |
| 适用场景 | 菜单渲染、层级展示 | 表格展示、搜索筛选 |
| 数据量 | 相对较大（包含所有层级） | 支持分页 |
| 加载方式 | 一次性加载 | 分页加载 |
