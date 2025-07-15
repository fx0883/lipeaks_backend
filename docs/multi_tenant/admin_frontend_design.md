# 管理后台前端架构设计文档

## 一、项目概述

**项目名称**：integrated_admin

**项目描述**：基于Vue 3和Element Plus的多租户管理系统前端，用于管理租户和用户信息，包含基于角色的权限控制系统。

**技术栈**：
- Vue 3.x（组合式API）
- JavaScript
- Element Plus
- Vue Router
- Pinia（状态管理）
- Axios（网络请求）
- ECharts（数据可视化）
- xlsx（Excel导出）

## 二、系统架构

### 1. 整体架构

系统采用前后端分离架构，前端基于Vue 3构建单页应用(SPA)，后端API基于RESTful风格。

```
┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │
│   Vue 3 前端    │◄─────►│   RESTful API   │
│                 │       │                 │
└─────────────────┘       └─────────────────┘
```

### 2. 功能模块划分

系统功能模块划分如下：

```
┌─────────────────────────────────────────────────┐
│                   系统整体架构                   │
└─────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
┌─────────▼─────────┐ ┌───▼───┐  ┌────────▼────────┐
│     认证模块      │ │ 核心  │  │   管理模块      │
│ (登录、注册、权限)│ │ 模块  │  │(租户管理、用户管理)│
└───────────────────┘ └───────┘  └─────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
┌─────────▼─────────┐ ┌───▼───┐  ┌────────▼────────┐
│     仪表盘模块    │ │ 个人  │  │    公共模块     │
│   (数据统计图表)  │ │ 设置  │  │  (工具函数等)   │
└───────────────────┘ └───────┘  └─────────────────┘
```

### 3. 项目目录结构设计

```
integrated_admin/
├── public/                  # 静态资源目录
│   ├── favicon.ico         # 网站图标
│   └── index.html          # HTML模板
├── src/                     # 源代码目录
│   ├── api/                 # API请求封装
│   │   ├── index.js        # API统一出口
│   │   ├── request.js      # Axios实例和拦截器
│   │   ├── auth.js         # 认证相关API
│   │   ├── user.js         # 用户相关API
│   │   └── tenant.js       # 租户相关API
│   ├── assets/             # 资源文件（图片、字体等）
│   │   ├── images/         # 图片资源
│   │   ├── styles/         # 样式资源
│   │   └── icons/          # 图标资源
│   ├── components/         # 全局公共组件
│   │   ├── layout/         # 布局组件
│   │   │   ├── AppHeader.vue     # 头部组件
│   │   │   ├── AppSidebar.vue    # 侧边栏组件
│   │   │   └── AppFooter.vue     # 底部组件
│   │   ├── common/         # 通用组件
│   │   │   ├── DataTable.vue     # 数据表格组件
│   │   │   ├── SearchForm.vue    # 搜索表单组件
│   │   │   └── ExportButton.vue  # 导出按钮组件
│   │   └── charts/         # 图表组件
│   ├── directives/         # 自定义指令
│   ├── hooks/              # 自定义组合式函数
│   │   ├── useAuth.js      # 认证相关hooks
│   │   ├── usePermission.js # 权限相关hooks
│   │   └── useTable.js     # 表格操作相关hooks
│   ├── router/             # 路由配置
│   │   ├── index.js        # 路由主文件
│   │   ├── routes.js       # 路由定义
│   │   └── permission.js   # 路由权限控制
│   ├── stores/             # Pinia状态管理
│   │   ├── index.js        # Store入口
│   │   ├── modules/        # 模块化的Store
│   │   │   ├── auth.js     # 认证状态
│   │   │   ├── user.js     # 用户状态
│   │   │   └── tenant.js   # 租户状态
│   │   └── persist.js      # 持久化配置
│   ├── utils/              # 工具函数
│   │   ├── request.js      # 请求工具
│   │   ├── auth.js         # 认证工具
│   │   ├── validator.js    # 验证工具
│   │   ├── format.js       # 格式化工具
│   │   └── export.js       # 导出工具
│   ├── views/              # 页面组件
│   │   ├── auth/           # 认证相关页面
│   │   │   ├── Login.vue   # 登录页
│   │   │   └── Register.vue # 注册页
│   │   ├── dashboard/      # 仪表盘页面
│   │   │   └── Index.vue   # 仪表盘首页
│   │   ├── user/           # 用户管理页面
│   │   │   ├── List.vue    # 用户列表
│   │   │   ├── Create.vue  # 创建用户
│   │   │   └── Edit.vue    # 编辑用户
│   │   ├── tenant/         # 租户管理页面
│   │   │   ├── List.vue    # 租户列表
│   │   │   ├── Create.vue  # 创建租户
│   │   │   └── Edit.vue    # 编辑租户
│   │   └── profile/        # 个人设置页面
│   │       └── Index.vue   # 个人设置首页
│   ├── App.vue             # 根组件
│   └── main.js             # 入口文件
├── .eslintrc.js            # ESLint配置
├── .prettierrc             # Prettier配置
├── vite.config.js          # Vite配置
├── package.json            # 依赖配置
└── README.md               # 项目说明
```

## 三、核心模块设计

### 1. 认证与权限模块

#### 1.1 登录流程

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  输入用户 │    │  表单验证 │    │ API请求   │    │ 存储Token │
│  名和密码 │───►│  (前端)   │───►│ 登录接口  │───►│ 和用户信息│
└───────────┘    └───────────┘    └───────────┘    └───────────┘
                                                         │
                       ┌───────────┐                     │
                       │ 重定向到  │◄────────────────────┘
                       │ 主页     │
                       └───────────┘
```

#### 1.2 权限控制设计

基于RBAC（基于角色的访问控制）模型，根据用户角色动态生成路由和菜单。

权限控制分为以下几个层面：
- 路由级别：不同角色能访问的路由不同
- 组件级别：同一页面内，不同角色可见的组件不同
- 按钮级别：同一组件内，不同角色可用的按钮不同

### 2. 请求处理模块

#### 2.1 请求拦截器

```javascript
// 请求拦截器功能
axios.interceptors.request.use(
  config => {
    // 1. 添加Token到请求头
    const token = getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    // 2. 其他请求处理（如添加时间戳防止缓存等）
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);
```

#### 2.2 响应拦截器

```javascript
// 响应拦截器功能
axios.interceptors.response.use(
  response => {
    // 统一处理响应数据
    return response.data;
  },
  error => {
    const { response } = error;
    if (response) {
      // 处理HTTP错误状态码
      switch (response.status) {
        case 401: // 未授权
          // 处理token过期
          handleTokenExpired();
          break;
        case 403: // 禁止访问
          // 处理权限问题
          handleForbidden();
          break;
        case 404: // 资源不存在
          // 处理资源不存在
          handleNotFound();
          break;
        case 500: // 服务器错误
          // 处理服务器错误
          handleServerError();
          break;
        default:
          // 处理其他错误
          handleOtherError(response);
      }
    } else {
      // 处理网络错误
      handleNetworkError();
    }
    // 统一错误提示
    showErrorMessage(error);
    return Promise.reject(error);
  }
);
```

#### 2.3 Token刷新机制

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  检测到   │    │ 使用Refresh│    │ 获取新的  │    │ 更新存储的│
│  Token过期│───►│  Token    │───►│ Access    │───►│ Token     │
└───────────┘    └───────────┘    │ Token     │    └───────────┘
                                   └───────────┘          │
                      ┌───────────┐                       │
                      │ 重试原始  │◄──────────────────────┘
                      │ 请求      │
                      └───────────┘
```

### 3. 数据表格与导出模块

#### 3.1 表格组件设计

提供统一的表格组件，支持以下功能：
- 分页
- 排序
- 筛选
- 搜索
- 批量操作
- 行内编辑
- 导出数据

#### 3.2 数据导出流程

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  选择要   │    │  调用导出 │    │ 转换数据  │    │ 生成并下载│
│  导出的数据│───►│  函数     │───►│ 为Excel格式│───►│ Excel文件 │
└───────────┘    └───────────┘    └───────────┘    └───────────┘
```

## 四、UI设计

### 1. 主题配置

使用Element Plus的主题配置，定制绿色主题：

```scss
// 主题变量
:root {
  --el-color-primary: #2c9678; // 主题色：绿色
  --el-color-success: #67C23A;
  --el-color-warning: #E6A23C;
  --el-color-danger: #F56C6C;
  --el-color-info: #909399;
  
  // ...其他变量
}
```

### 2. 布局设计

整体采用Classic布局，包含：
- 顶部导航栏（显示logo、用户信息、通知等）
- 左侧菜单（根据权限动态生成）
- 内容区域
- 面包屑导航

### 3. 响应式设计

使用Element Plus的响应式栅格系统，适配不同屏幕尺寸：
- 大屏（>=1200px）：显示所有功能
- 中屏（>=992px）：略微紧凑的布局
- 小屏（>=768px）：隐藏部分非核心功能
- 移动端（<768px）：侧边栏可收起，优化移动体验

## 五、路由设计

### 1. 路由配置

```javascript
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '仪表盘', icon: 'dashboard' }
      },
      {
        path: 'users',
        name: 'Users',
        component: { render: (h) => h('router-view') },
        meta: { title: '用户管理', icon: 'user', roles: ['admin', 'super_admin'] },
        children: [
          {
            path: '',
            name: 'UsersList',
            component: () => import('@/views/user/List.vue'),
            meta: { title: '用户列表' }
          },
          {
            path: 'create',
            name: 'CreateUser',
            component: () => import('@/views/user/Create.vue'),
            meta: { title: '创建用户' }
          },
          {
            path: 'edit/:id',
            name: 'EditUser',
            component: () => import('@/views/user/Edit.vue'),
            meta: { title: '编辑用户', hidden: true }
          }
        ]
      },
      {
        path: 'tenants',
        name: 'Tenants',
        component: { render: (h) => h('router-view') },
        meta: { title: '租户管理', icon: 'building', roles: ['super_admin'] },
        children: [
          {
            path: '',
            name: 'TenantsList',
            component: () => import('@/views/tenant/List.vue'),
            meta: { title: '租户列表' }
          },
          {
            path: 'create',
            name: 'CreateTenant',
            component: () => import('@/views/tenant/Create.vue'),
            meta: { title: '创建租户' }
          },
          {
            path: 'edit/:id',
            name: 'EditTenant',
            component: () => import('@/views/tenant/Edit.vue'),
            meta: { title: '编辑租户', hidden: true }
          }
        ]
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Index.vue'),
        meta: { title: '个人设置', icon: 'setting' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  },
  {
    path: '/404',
    component: () => import('@/views/error/404.vue'),
    meta: { requiresAuth: false, hidden: true }
  }
];
```

### 2. 路由守卫

```javascript
router.beforeEach(async (to, from, next) => {
  // 显示加载进度条
  NProgress.start();
  
  // 判断是否需要登录
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false);
  const isLoggedIn = store.getters['auth/isLoggedIn'];
  
  if (requiresAuth && !isLoggedIn) {
    // 需要登录但未登录，重定向到登录页
    next({ name: 'Login', query: { redirect: to.fullPath } });
  } else if (to.meta.roles && to.meta.roles.length) {
    // 需要特定角色
    const userRole = store.getters['auth/userRole'];
    if (to.meta.roles.includes(userRole)) {
      // 有权限，放行
      next();
    } else {
      // 无权限，重定向到403页面
      next({ name: '403' });
    }
  } else {
    // 不需要验证，直接放行
    next();
  }
  
  // 结束加载进度条
  NProgress.done();
});
```

## 六、状态管理设计

### 1. Store模块划分

使用Pinia进行状态管理，将Store分为以下几个模块：

#### 1.1 认证模块 (auth)

```javascript
// 认证状态模块
export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null,
    refreshToken: null,
    user: null,
    permissions: []
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    userRole: (state) => state.user?.role || '',
    isSuperAdmin: (state) => state.user?.is_super_admin || false,
    isAdmin: (state) => state.user?.is_admin || false
  },
  actions: {
    async login(credentials) {
      // 实现登录逻辑
    },
    async register(userData) {
      // 实现注册逻辑
    },
    async logout() {
      // 实现登出逻辑
    },
    async refreshAccessToken() {
      // 实现刷新Token逻辑
    }
  }
});
```

#### 1.2 用户模块 (user)

```javascript
// 用户状态模块
export const useUserStore = defineStore('user', {
  state: () => ({
    users: [],
    loading: false,
    pagination: {
      page: 1,
      pageSize: 10,
      total: 0
    },
    filters: {},
    currentUser: null
  }),
  actions: {
    async fetchUsers(params) {
      // 获取用户列表
    },
    async createUser(userData) {
      // 创建用户
    },
    async updateUser(id, userData) {
      // 更新用户
    },
    async deleteUser(id) {
      // 删除用户
    },
    async getUserById(id) {
      // 获取用户详情
    }
  }
});
```

#### 1.3 租户模块 (tenant)

```javascript
// 租户状态模块
export const useTenantStore = defineStore('tenant', {
  state: () => ({
    tenants: [],
    loading: false,
    pagination: {
      page: 1,
      pageSize: 10,
      total: 0
    },
    filters: {},
    currentTenant: null
  }),
  actions: {
    async fetchTenants(params) {
      // 获取租户列表
    },
    async createTenant(tenantData) {
      // 创建租户
    },
    async updateTenant(id, tenantData) {
      // 更新租户
    },
    async deleteTenant(id) {
      // 删除租户
    },
    async getTenantById(id) {
      // 获取租户详情
    }
  }
});
```

### 2. 持久化配置

使用pinia-plugin-persist实现状态持久化：

```javascript
// 持久化配置
const piniaPersistConfig = {
  auth: {
    key: 'auth',
    storage: localStorage,
    paths: ['token', 'refreshToken', 'user']
  }
};
```

## 七、API接口封装

### 1. 基础请求封装

```javascript
// 基础配置
const service = axios.create({
  baseURL: 'http://localhost:8000/api/v1/',
  timeout: 15000
});

// 请求拦截器
service.interceptors.request.use(...);

// 响应拦截器
service.interceptors.response.use(...);

// 请求方法封装
export const request = {
  get(url, params) {
    return service({
      method: 'get',
      url,
      params
    });
  },
  post(url, data) {
    return service({
      method: 'post',
      url,
      data
    });
  },
  put(url, data) {
    return service({
      method: 'put',
      url,
      data
    });
  },
  delete(url) {
    return service({
      method: 'delete',
      url
    });
  }
};
```

### 2. 业务API封装

#### 2.1 认证API

```javascript
import { request } from '@/utils/request';

export const authApi = {
  login(data) {
    return request.post('/auth/login/', data);
  },
  register(data) {
    return request.post('/auth/register/', data);
  },
  refreshToken(data) {
    return request.post('/auth/token/refresh/', data);
  },
  verifyToken(data) {
    return request.post('/auth/token/verify/', data);
  }
};
```

#### 2.2 用户API

```javascript
import { request } from '@/utils/request';

export const userApi = {
  getCurrentUser() {
    return request.get('/users/me/');
  },
  getUsers(params) {
    return request.get('/users/', params);
  },
  getUserById(id) {
    return request.get(`/users/${id}/`);
  },
  createUser(data) {
    return request.post('/users/', data);
  },
  updateUser(id, data) {
    return request.put(`/users/${id}/`, data);
  },
  deleteUser(id) {
    return request.delete(`/users/${id}/`);
  },
  changePassword(id, data) {
    return request.post(`/users/${id}/change-password/`, data);
  }
};
```

#### 2.3 租户API

```javascript
import { request } from '@/utils/request';

export const tenantApi = {
  getTenants(params) {
    return request.get('/tenants/', params);
  },
  getTenantById(id) {
    return request.get(`/tenants/${id}/`);
  },
  createTenant(data) {
    return request.post('/tenants/', data);
  },
  updateTenant(id, data) {
    return request.put(`/tenants/${id}/`, data);
  },
  deleteTenant(id) {
    return request.delete(`/tenants/${id}/`);
  },
  updateTenantQuota(id, data) {
    return request.put(`/tenants/${id}/quota/`, data);
  },
  getTenantUsers(id, params) {
    return request.get(`/tenants/${id}/users/`, params);
  }
};
``` 