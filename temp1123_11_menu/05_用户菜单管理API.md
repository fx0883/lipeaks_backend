# 用户菜单管理API

这组API用于超级管理员为其他用户分配和管理菜单权限。

## 1. 获取用户的菜单列表

### 接口信息
- **URL**: `/api/v1/menus/admins/{user_id}/menus/`
- **方法**: `GET`
- **权限**: 仅超级管理员
- **说明**: 获取指定用户的菜单列表

### 请求参数

#### Path参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | integer | 是 | 管理员用户ID |

### 返回格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "user_id": 3,
    "username": "admin_cms",
    "menus": [
      {
        "id": 1,
        "user_id": 3,
        "username": "admin_cms",
        "menu_id": 23,
        "menu_title": "cms.menu.articleManagement",
        "menu_name": "ArticleManagement",
        "menu_code": "articleManagement",
        "is_active": true,
        "created_at": "2025-11-23T14:34:40.140762Z",
        "updated_at": "2025-11-23T14:34:40.140762Z"
      },
      {
        "id": 2,
        "user_id": 3,
        "username": "admin_cms",
        "menu_id": 28,
        "menu_title": "cms.menu.commentDetail",
        "menu_name": "CommentDetail",
        "menu_code": "commentdetail",
        "is_active": true,
        "created_at": "2025-11-23T14:34:40.140762Z",
        "updated_at": "2025-11-23T14:34:40.140762Z"
      }
    ]
  }
}
```

### curl示例

```bash
# 获取用户ID为3的菜单列表
curl -X GET "http://localhost:8000/api/v1/menus/admins/3/menus/" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 2. 分配菜单给用户

### 接口信息
- **URL**: `/api/v1/menus/admins/{user_id}/menus/`
- **方法**: `POST`
- **权限**: 仅超级管理员
- **说明**: 为指定用户分配菜单，支持批量分配

### 请求参数

#### Path参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | integer | 是 | 管理员用户ID |

#### Body参数（JSON）
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| menu_ids | array | 是 | 菜单ID数组，至少包含一个菜单ID |

### 功能说明
- 会替换用户当前的所有菜单分配
- 不在menu_ids中的菜单会被设置为is_active=False
- 在menu_ids中的菜单会被激活或新建

### 返回格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "assigned_menus": [
      {
        "id": 23,
        "name": "ArticleManagement"
      },
      {
        "id": 28,
        "name": "CommentDetail"
      },
      {
        "id": 29,
        "name": "CategoryManagement"
      }
    ]
  }
}
```

### 错误响应

```json
// 用户不存在
{
  "success": false,
  "code": 4004,
  "message": "用户不存在",
  "data": {}
}

// 目标用户不是管理员
{
  "success": false,
  "code": 4000,
  "message": "只能为管理员用户分配菜单",
  "data": {}
}

// 包含无效的菜单ID
{
  "success": false,
  "code": 4000,
  "message": "包含无效的菜单ID",
  "data": {}
}

// 权限不足
{
  "success": false,
  "code": 4003,
  "message": "只有超级管理员才能分配菜单给用户",
  "data": {}
}
```

### curl示例

```bash
# 为用户分配菜单
curl -X POST "http://localhost:8000/api/v1/menus/admins/3/menus/" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "menu_ids": [23, 28, 29, 30]
  }'

# 替换用户的菜单（新的菜单列表）
curl -X POST "http://localhost:8000/api/v1/menus/admins/3/menus/" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "menu_ids": [23, 29]
  }'
```

---

## 3. 移除用户的特定菜单

### 接口信息
- **URL**: `/api/v1/menus/admins/{user_id}/menus/{id}/`
- **方法**: `DELETE`
- **权限**: 仅超级管理员
- **说明**: 移除用户的特定菜单

### 请求参数

#### Path参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | integer | 是 | 管理员用户ID |
| id | integer | 是 | 菜单ID（注意：这里的id是menu_id，不是UserMenu的id） |

### 返回格式

```
HTTP Status: 204 No Content
```

### 错误响应

```json
// 用户菜单关联不存在
{
  "success": false,
  "code": 4004,
  "message": "用户菜单关联不存在",
  "data": {}
}

// 权限不足
{
  "success": false,
  "code": 4003,
  "message": "只有超级管理员才能移除用户的菜单",
  "data": {}
}
```

### curl示例

```bash
# 移除用户ID为3的菜单ID为23的关联
curl -X DELETE "http://localhost:8000/api/v1/menus/admins/3/menus/23/" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 4. 批量移除用户菜单

### 接口信息
- **URL**: `/api/v1/menus/admins/{user_id}/menus/batch/`
- **方法**: `DELETE`
- **权限**: 仅超级管理员
- **说明**: 批量移除用户的菜单

### 请求参数

#### Path参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | integer | 是 | 管理员用户ID |

#### Body参数（JSON）
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| menu_ids | array | 是 | 要移除的菜单ID数组 |

### 返回格式

```
HTTP Status: 204 No Content
```

### 错误响应

```json
// 用户不存在
{
  "success": false,
  "code": 4004,
  "message": "用户不存在",
  "data": {}
}

// 权限不足
{
  "success": false,
  "code": 4003,
  "message": "只有超级管理员才能批量移除用户的菜单",
  "data": {}
}
```

### curl示例

```bash
# 批量移除用户的菜单
curl -X DELETE "http://localhost:8000/api/v1/menus/admins/3/menus/batch/" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "menu_ids": [28, 29, 30]
  }'
```

---

## 使用场景

### 1. 用户菜单权限管理界面

```javascript
// Vue组件示例
<template>
  <div>
    <h2>为用户分配菜单</h2>
    
    <!-- 用户选择 -->
    <el-select v-model="selectedUserId" placeholder="选择用户">
      <el-option 
        v-for="user in users" 
        :key="user.id"
        :label="user.username"
        :value="user.id"
      />
    </el-select>
    
    <!-- 菜单树 -->
    <el-tree
      ref="menuTree"
      :data="allMenus"
      show-checkbox
      node-key="id"
      :default-checked-keys="userMenuIds"
      :props="{ label: 'title', children: 'children' }"
    />
    
    <!-- 保存按钮 -->
    <el-button type="primary" @click="saveUserMenus">
      保存
    </el-button>
  </div>
</template>

<script>
import { ref, watch } from 'vue';
import axios from 'axios';

export default {
  setup() {
    const selectedUserId = ref(null);
    const allMenus = ref([]);
    const userMenuIds = ref([]);
    const menuTree = ref(null);
    
    // 获取所有菜单
    const fetchAllMenus = async () => {
      const response = await axios.get('/api/v1/menus/tree/', {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (response.data.success) {
        allMenus.value = response.data.data;
      }
    };
    
    // 获取用户的菜单
    const fetchUserMenus = async (userId) => {
      const response = await axios.get(
        `/api/v1/menus/admins/${userId}/menus/`,
        {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        }
      );
      if (response.data.success) {
        userMenuIds.value = response.data.data.menus.map(m => m.menu_id);
      }
    };
    
    // 保存用户菜单
    const saveUserMenus = async () => {
      const checkedKeys = menuTree.value.getCheckedKeys();
      
      await axios.post(
        `/api/v1/menus/admins/${selectedUserId.value}/menus/`,
        { menu_ids: checkedKeys },
        {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        }
      );
      
      ElMessage.success('保存成功');
    };
    
    // 监听用户选择变化
    watch(selectedUserId, (newUserId) => {
      if (newUserId) {
        fetchUserMenus(newUserId);
      }
    });
    
    onMounted(() => {
      fetchAllMenus();
    });
    
    return {
      selectedUserId,
      allMenus,
      userMenuIds,
      menuTree,
      saveUserMenus
    };
  }
};
</script>
```

### 2. 批量管理用户菜单

```javascript
// 批量为多个用户分配相同的菜单
async function assignMenusToMultipleUsers(userIds, menuIds) {
  const results = [];
  
  for (const userId of userIds) {
    try {
      const response = await axios.post(
        `/api/v1/menus/admins/${userId}/menus/`,
        { menu_ids: menuIds },
        {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        }
      );
      
      results.push({
        userId,
        success: true,
        data: response.data
      });
    } catch (error) {
      results.push({
        userId,
        success: false,
        error: error.message
      });
    }
  }
  
  return results;
}

// 使用示例
const userIds = [3, 4, 5];
const menuIds = [23, 28, 29];
const results = await assignMenusToMultipleUsers(userIds, menuIds);
console.log('分配结果:', results);
```

### 3. 菜单权限模板

```javascript
// 定义菜单权限模板
const menuTemplates = {
  cms_admin: [23, 28, 29, 30], // CMS管理员
  member_admin: [47, 48, 49],   // 会员管理员
  full_admin: [22, 23, 28, 29, 30, 47, 48, 49] // 全部权限
};

// 应用模板
async function applyMenuTemplate(userId, templateName) {
  const menuIds = menuTemplates[templateName];
  
  if (!menuIds) {
    throw new Error('模板不存在');
  }
  
  await axios.post(
    `/api/v1/menus/admins/${userId}/menus/`,
    { menu_ids: menuIds },
    {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    }
  );
}

// 使用示例
await applyMenuTemplate(3, 'cms_admin');
```

### 4. 复制用户菜单权限

```javascript
// 将一个用户的菜单权限复制到另一个用户
async function copyUserMenus(sourceUserId, targetUserId) {
  // 获取源用户的菜单
  const response = await axios.get(
    `/api/v1/menus/admins/${sourceUserId}/menus/`,
    {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    }
  );
  
  if (response.data.success) {
    const menuIds = response.data.data.menus.map(m => m.menu_id);
    
    // 分配给目标用户
    await axios.post(
      `/api/v1/menus/admins/${targetUserId}/menus/`,
      { menu_ids: menuIds },
      {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      }
    );
  }
}

// 使用示例
await copyUserMenus(3, 4); // 将用户3的菜单权限复制给用户4
```

## 工作流程

### 完整的菜单分配流程

```mermaid
sequenceDiagram
    超级管理员->>后端: 获取所有菜单 (GET /api/v1/menus/tree/)
    后端-->>超级管理员: 返回菜单树
    超级管理员->>后端: 获取用户current菜单 (GET /admins/{user_id}/menus/)
    后端-->>超级管理员: 返回用户菜单列表
    超级管理员->>前端: 在树形组件中勾选菜单
    超级管理员->>后端: 保存菜单分配 (POST /admins/{user_id}/menus/)
    后端-->>超级管理员: 返回分配结果
    用户->>后端: 获取自己的菜单 (GET /api/v1/menus/user/)
    后端-->>用户: 返回新的菜单列表
```

## 注意事项

### 1. 目标用户必须是管理员
只能为管理员用户分配菜单，普通用户不能分配菜单。

```javascript
// 检查用户是否是管理员
const checkIsAdmin = async (userId) => {
  const response = await axios.get(`/api/v1/users/${userId}/`);
  return response.data.data.is_admin || response.data.data.is_super_admin;
};
```

### 2. 菜单ID必须有效
分配的菜单ID必须在系统中存在，否则会返回错误。

### 3. 分配操作是替换性的
调用分配接口时，会替换用户现有的所有菜单分配。如果要保留现有菜单，需要包含在menu_ids中。

### 4. 激活状态管理
- 分配新菜单时，会设置为激活状态
- 不在分配列表中的菜单会被设置为非激活状态
- 删除操作会完全删除关联记录

### 5. 父子菜单关系
在分配菜单时，建议同时分配父菜单和子菜单，避免出现只有子菜单没有父菜单的情况。

```javascript
// 确保包含父菜单
function ensureParentMenus(menuIds, allMenus) {
  const result = new Set(menuIds);
  
  for (const menuId of menuIds) {
    const menu = findMenuById(allMenus, menuId);
    if (menu && menu.parent_id) {
      result.add(menu.parent_id);
      // 递归添加祖先菜单
      ensureParentMenus([menu.parent_id], allMenus).forEach(id => result.add(id));
    }
  }
  
  return Array.from(result);
}
```

### 6. 实时生效
菜单分配后，用户需要刷新页面或重新获取菜单才能看到变更。建议提示用户刷新。

```javascript
// 提示用户刷新
ElMessageBox.confirm(
  '菜单分配已更新，用户需要刷新页面才能看到新菜单。是否通知用户？',
  '提示',
  {
    confirmButtonText: '通知',
    cancelButtonText: '取消'
  }
).then(() => {
  // 发送通知给用户
  notifyUser(userId, '您的菜单权限已更新，请刷新页面');
});
```

## 权限设计建议

### 1. 菜单分组
建议将菜单按功能模块分组，方便批量分配：

```javascript
const menuGroups = {
  'CMS模块': [22, 23, 28, 29, 30],
  '会员模块': [47, 48, 49, 50],
  '订单模块': [51, 52, 53],
  '系统设置': [60, 61, 62]
};
```

### 2. 角色预设
为常见角色预设菜单配置：

```javascript
const roleMenus = {
  'content_manager': menuGroups['CMS模块'],
  'member_manager': menuGroups['会员模块'],
  'order_manager': menuGroups['订单模块'],
  'system_admin': Object.values(menuGroups).flat()
};
```

### 3. 最小权限原则
只分配用户实际需要的菜单，避免过度授权。

### 4. 定期审计
定期检查用户的菜单权限，移除不再需要的权限。
