# 用户菜单API

## 获取current用户的菜单

### 接口信息
- **URL**: `/api/v1/menus/user/`
- **方法**: `GET`
- **权限**: 已认证用户
- **说明**: 获取current登录用户能够访问的菜单列表，返回树形结构的菜单数据

### 请求参数

无请求参数

### 权限说明

#### 超级管理员
- 可以访问所有激活的菜单

#### 租户管理员/普通管理员
- 只能访问分配给自己的激活菜单
- 通过UserMenu关联表确定用户可访问的菜单

#### 普通用户
- 可以获取分配给自己的菜单（如果有分配）

### 返回格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "menus": [
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
}
```

### curl示例

```bash
# 租户管理员获取自己的菜单
curl -X GET "http://localhost:8000/api/v1/menus/user/" \
  -H "Authorization: Bearer YOUR_TENANT_ADMIN_TOKEN" \
  -H "Content-Type: application/json"

# 超级管理员获取自己的菜单
curl -X GET "http://localhost:8000/api/v1/menus/user/" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json"

# 普通用户获取自己的菜单
curl -X GET "http://localhost:8000/api/v1/menus/user/" \
  -H "Authorization: Bearer YOUR_MEMBER_TOKEN" \
  -H "Content-Type: application/json"
```

## 特点说明

### 1. 树形结构
- 只返回顶级菜单（parent_id为null的菜单）
- 子菜单递归嵌套在父菜单的`children`字段中
- 自动过滤未激活的菜单（is_active=True）

### 2. 权限过滤
- 自动根据用户角色过滤菜单
- 只返回用户有权访问的菜单
- 超级管理员可以看到所有激活菜单

### 3. 数据完整性
- 返回完整的菜单信息，包括所有字段
- 包含created_at、updated_at等时间戳
- 包含parent_id等关系字段

## 使用场景

### 1. 渲染用户侧边栏菜单

```javascript
// Vue示例
<template>
  <el-menu>
    <MenuItem 
      v-for="menu in menus" 
      :key="menu.id"
      :menu="menu"
    />
  </el-menu>
</template>

<script>
import { ref, onMounted } from 'vue';
import axios from 'axios';

export default {
  setup() {
    const menus = ref([]);
    
    const fetchMenus = async () => {
      const response = await axios.get('/api/v1/menus/user/', {
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      });
      
      if (response.data.success) {
        menus.value = response.data.data.menus;
      }
    };
    
    onMounted(() => {
      fetchMenus();
    });
    
    return { menus };
  }
};
</script>
```

### 2. 递归渲染菜单组件

```javascript
// MenuItem组件
<template>
  <el-sub-menu 
    v-if="menu.children && menu.children.length > 0"
    :index="menu.path"
  >
    <template #title>
      <el-icon v-if="menu.icon">
        <component :is="menu.icon" />
      </el-icon>
      <span>{{ menu.title }}</span>
    </template>
    
    <MenuItem 
      v-for="child in menu.children"
      :key="child.id"
      :menu="child"
    />
  </el-sub-menu>
  
  <el-menu-item 
    v-else
    :index="menu.path"
  >
    <el-icon v-if="menu.icon">
      <component :is="menu.icon" />
    </el-icon>
    <span>{{ menu.title }}</span>
  </el-menu-item>
</template>

<script>
export default {
  name: 'MenuItem',
  props: {
    menu: {
      type: Object,
      required: true
    }
  }
};
</script>
```

### 3. 基于菜单权限控制路由

```javascript
// 路由守卫
import { useUserMenuStore } from '@/stores/userMenu';

router.beforeEach(async (to, from, next) => {
  const menuStore = useUserMenuStore();
  
  // 如果还没有加载菜单，先加载
  if (!menuStore.menus.length) {
    await menuStore.fetchMenus();
  }
  
  // 检查用户是否有权访问该路由
  const hasPermission = menuStore.hasMenuPermission(to.path);
  
  if (hasPermission) {
    next();
  } else {
    next('/403');
  }
});
```

### 4. 菜单状态管理（Pinia示例）

```javascript
// stores/userMenu.js
import { defineStore } from 'pinia';
import axios from 'axios';

export const useUserMenuStore = defineStore('userMenu', {
  state: () => ({
    menus: [],
    loading: false
  }),
  
  actions: {
    async fetchMenus() {
      this.loading = true;
      try {
        const response = await axios.get('/api/v1/menus/user/', {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        });
        
        if (response.data.success) {
          this.menus = response.data.data.menus;
        }
      } catch (error) {
        console.error('Failed to fetch menus:', error);
      } finally {
        this.loading = false;
      }
    },
    
    hasMenuPermission(path) {
      const checkMenu = (menus, path) => {
        for (const menu of menus) {
          if (menu.path === path) return true;
          if (menu.children && menu.children.length > 0) {
            if (checkMenu(menu.children, path)) return true;
          }
        }
        return false;
      };
      
      return checkMenu(this.menus, path);
    },
    
    findMenuByPath(path) {
      const findMenu = (menus, path) => {
        for (const menu of menus) {
          if (menu.path === path) return menu;
          if (menu.children && menu.children.length > 0) {
            const found = findMenu(menu.children, path);
            if (found) return found;
          }
        }
        return null;
      };
      
      return findMenu(this.menus, path);
    }
  },
  
  getters: {
    flatMenus: (state) => {
      const flatten = (menus) => {
        return menus.reduce((acc, menu) => {
          acc.push(menu);
          if (menu.children && menu.children.length > 0) {
            acc.push(...flatten(menu.children));
          }
          return acc;
        }, []);
      };
      
      return flatten(state.menus);
    }
  }
});
```

## 与管理员路由API的区别

| 特性 | 用户菜单API | 管理员路由API |
|------|-------------|---------------|
| URL | /api/v1/menus/user/ | /api/v1/menus/admin/routes/ |
| 数据格式 | 完整菜单数据 | 前端路由格式 |
| 字段命名 | 下划线命名 | 驼峰命名 |
| 用途 | 菜单渲染、权限判断 | 前端路由配置 |
| 返回结构 | data.menus数组 | data数组 |

## 性能优化建议

### 1. 缓存策略

```javascript
// localStorage缓存
const MENU_CACHE_KEY = 'user_menus';
const CACHE_DURATION = 30 * 60 * 1000; // 30分钟

class MenuCache {
  static set(menus) {
    const data = {
      menus,
      timestamp: Date.now()
    };
    localStorage.setItem(MENU_CACHE_KEY, JSON.stringify(data));
  }
  
  static get() {
    const cached = localStorage.getItem(MENU_CACHE_KEY);
    if (!cached) return null;
    
    const data = JSON.parse(cached);
    const isExpired = Date.now() - data.timestamp > CACHE_DURATION;
    
    if (isExpired) {
      this.clear();
      return null;
    }
    
    return data.menus;
  }
  
  static clear() {
    localStorage.removeItem(MENU_CACHE_KEY);
  }
}

// 使用缓存
async function fetchUserMenus() {
  // 先尝试从缓存获取
  const cached = MenuCache.get();
  if (cached) {
    return cached;
  }
  
  // 缓存不存在或已过期，从API获取
  const response = await axios.get('/api/v1/menus/user/');
  if (response.data.success) {
    const menus = response.data.data.menus;
    MenuCache.set(menus);
    return menus;
  }
  
  return [];
}
```

### 2. 按需刷新

```javascript
// 提供刷新菜单的方法
export const useUserMenuStore = defineStore('userMenu', {
  actions: {
    async refreshMenus() {
      MenuCache.clear();
      await this.fetchMenus();
    }
  }
});

// 在用户权限变更后调用
async function onUserPermissionChanged() {
  const menuStore = useUserMenuStore();
  await menuStore.refreshMenus();
  // 可能需要重新加载路由
  router.go(0);
}
```

### 3. 懒加载子菜单

对于非常大的菜单树，可以考虑按需加载子菜单（需要后端支持）：

```javascript
// 懒加载示例（需要后端提供单独的子菜单API）
async function loadSubMenus(parentId) {
  const response = await axios.get(`/api/v1/menus/?parent_id=${parentId}`);
  return response.data.data.results;
}
```

## 注意事项

### 1. 用户登录后立即获取
建议在用户登录成功后立即获取用户菜单，存储在状态管理中。

### 2. 权限变更处理
当用户权限发生变更时，需要清除缓存并重新获取菜单。

### 3. 错误处理
API调用失败时，应该有合理的降级方案，避免用户完全无法使用系统。

### 4. 多语言支持
title字段使用的是i18n的key（如"member.memberManagement"），需要在前端进行翻译。

```javascript
// 使用i18n翻译菜单标题
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const translatedTitle = t(menu.title);
```
