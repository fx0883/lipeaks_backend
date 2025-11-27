# 管理员菜单路由API

## 获取管理员菜单路由

### 接口信息
- **URL**: `/api/v1/menus/admin/routes/`
- **方法**: `GET`
- **权限**: 已认证用户
- **说明**: 获取管理员菜单路由配置，用于前端路由系统

### 请求参数

无请求参数

### 权限说明

#### 超级管理员
- 返回系统中所有激活的菜单路由
- 首先尝试从Config表中获取`super_admin_menu`配置
- 如果配置不存在，则从Menu表动态构建路由

#### 租户管理员
- 返回分配给该用户的菜单路由
- 从UserMenu关联表中获取用户的菜单权限
- 只返回激活的菜单

#### 普通用户
- 返回空数组

### 返回格式

```json
{
  "success": true,
  "code": 2000,
  "message": "获取路由成功",
  "data": [
    {
      "path": "/member",
      "name": "Member",
      "meta": {
        "title": "member.memberManagement",
        "rank": 0,
        "showLink": true,
        "icon": "ep:avatar",
        "showParent": true,
        "keepAlive": false,
        "frameLoading": false,
        "hiddenTag": false
      },
      "redirect": "/member/index",
      "children": [
        {
          "path": "/member/index",
          "name": "MemberList",
          "meta": {
            "title": "member.memberList",
            "rank": 0,
            "showLink": true,
            "icon": "ri:menu-line",
            "showParent": true,
            "keepAlive": false,
            "frameLoading": false,
            "hiddenTag": false
          },
          "component": "/src/views/member/index.vue"
        },
        {
          "path": "/member/create",
          "name": "MemberCreate",
          "meta": {
            "title": "member.createMember",
            "rank": 0,
            "showLink": false,
            "showParent": false,
            "keepAlive": false,
            "frameLoading": false,
            "hiddenTag": false
          },
          "component": "/src/views/member/create.vue"
        }
      ]
    },
    {
      "path": "/cms",
      "name": "CMS",
      "meta": {
        "title": "cms.menu.contentManagement",
        "rank": 0,
        "showLink": true,
        "icon": "ri:article-line",
        "showParent": true,
        "keepAlive": false,
        "frameLoading": false,
        "hiddenTag": false
      },
      "redirect": "/cms/article",
      "children": [
        {
          "path": "/cms/article",
          "name": "ArticleManagement",
          "meta": {
            "title": "cms.menu.articleManagement",
            "rank": 0,
            "showLink": true,
            "icon": "ri:file-list-line",
            "showParent": true,
            "keepAlive": true,
            "frameLoading": false,
            "hiddenTag": false
          }
        }
      ]
    }
  ]
}
```

### curl示例

```bash
# 租户管理员获取菜单路由
curl -X GET "http://localhost:8000/api/v1/menus/admin/routes/" \
  -H "Authorization: Bearer YOUR_TENANT_ADMIN_TOKEN" \
  -H "Content-Type: application/json"

# 超级管理员获取菜单路由
curl -X GET "http://localhost:8000/api/v1/menus/admin/routes/" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

## 路由配置说明

### 路由对象结构

```typescript
interface Route {
  path: string;              // 路由路径
  name: string;              // 路由名称
  component?: string;        // 组件路径
  redirect?: string;         // 重定向路径
  meta: RouteMeta;          // 路由元数据
  children?: Route[];       // 子路由
}

interface RouteMeta {
  title: string;            // 菜单标题
  rank: number;             // 排序
  showLink: boolean;        // 是否显示在菜单中
  icon?: string;            // 图标
  extraIcon?: string;       // 额外图标
  showParent?: boolean;     // 是否显示父级菜单
  roles?: string[];         // 页面级别权限
  auths?: string[];         // 按钮级别权限
  keepAlive?: boolean;      // 是否缓存
  frameSrc?: string;        // iframe地址
  frameLoading?: boolean;   // iframe加载动画
  hiddenTag?: boolean;      // 是否隐藏标签
  dynamicLevel?: number;    // 动态层级
  activePath?: string;      // 激活路径
  transition?: {            // 转场动画
    name?: string;
    enterTransition?: string;
    leaveTransition?: string;
  };
}
```

## 前端集成示例

### Vue Router 配置

```javascript
import { createRouter, createWebHistory } from 'vue-router';
import axios from 'axios';

// 从API获取路由配置
async function getRoutes() {
  const response = await axios.get('/api/v1/menus/admin/routes/', {
    headers: {
      'Authorization': `Bearer ${getToken()}`
    }
  });
  
  if (response.data.success) {
    return response.data.data;
  }
  return [];
}

// 动态路由转换
function transformRoutes(routes) {
  return routes.map(route => ({
    path: route.path,
    name: route.name,
    component: () => import(`@${route.component}`),
    redirect: route.redirect,
    meta: route.meta,
    children: route.children ? transformRoutes(route.children) : []
  }));
}

// 初始化路由
async function setupRouter() {
  const routes = await getRoutes();
  const transformedRoutes = transformRoutes(routes);
  
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/',
        component: Layout,
        children: transformedRoutes
      }
    ]
  });
  
  return router;
}

export default setupRouter;
```

### React Router 配置

```javascript
import { createBrowserRouter } from 'react-router-dom';
import axios from 'axios';

// 从API获取路由配置
async function getRoutes() {
  const response = await axios.get('/api/v1/menus/admin/routes/', {
    headers: {
      'Authorization': `Bearer ${getToken()}`
    }
  });
  
  if (response.data.success) {
    return response.data.data;
  }
  return [];
}

// 动态加载组件
const componentMap = {
  '/src/views/member/index.vue': () => import('@/views/member/index'),
  '/src/views/member/create.vue': () => import('@/views/member/create'),
  // ... 其他组件映射
};

// 转换路由配置
function transformRoutes(routes) {
  return routes.map(route => {
    const Component = componentMap[route.component];
    
    return {
      path: route.path,
      element: Component ? <Component /> : null,
      children: route.children ? transformRoutes(route.children) : undefined,
      // 可以在loader中使用meta数据
      loader: () => ({ meta: route.meta })
    };
  });
}

// 初始化路由
export async function setupRouter() {
  const routes = await getRoutes();
  const transformedRoutes = transformRoutes(routes);
  
  return createBrowserRouter([
    {
      path: '/',
      element: <Layout />,
      children: transformedRoutes
    }
  ]);
}
```

## 使用场景

### 1. 动态菜单渲染

```javascript
// 使用路由配置渲染侧边栏菜单
const SidebarMenu = ({ routes }) => {
  return (
    <Menu>
      {routes.map(route => {
        if (!route.meta.showLink) return null;
        
        return (
          <MenuItem 
            key={route.name}
            icon={route.meta.icon}
            title={route.meta.title}
          >
            {route.children && (
              <SubMenu routes={route.children} />
            )}
          </MenuItem>
        );
      })}
    </Menu>
  );
};
```

### 2. 权限控制

```javascript
// 基于路由配置进行权限验证
const checkPermission = (route, userRoles) => {
  if (!route.meta.roles || route.meta.roles.length === 0) {
    return true; // 无权限限制
  }
  
  return route.meta.roles.some(role => userRoles.includes(role));
};

// 在路由守卫中使用
router.beforeEach((to, from, next) => {
  const userRoles = getUserRoles();
  const route = findRoute(to.path);
  
  if (route && checkPermission(route, userRoles)) {
    next();
  } else {
    next('/403'); // 无权限访问
  }
});
```

### 3. 面包屑导航

```javascript
// 根据路由配置生成面包屑
const Breadcrumb = ({ currentPath }) => {
  const breadcrumbs = generateBreadcrumbs(routes, currentPath);
  
  return (
    <nav>
      {breadcrumbs.map((item, index) => (
        <span key={index}>
          {index > 0 && ' / '}
          <Link to={item.path}>{item.meta.title}</Link>
        </span>
      ))}
    </nav>
  );
};
```

## 注意事项

### 1. 缓存策略
- 菜单路由配置相对稳定，建议缓存在localStorage
- 用户登录后获取一次，存储在本地
- 当用户权限变更时，需要重新获取

```javascript
// 缓存策略示例
const CACHE_KEY = 'admin_routes';
const CACHE_TIME = 24 * 60 * 60 * 1000; // 24小时

async function getCachedRoutes() {
  const cached = localStorage.getItem(CACHE_KEY);
  
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < CACHE_TIME) {
      return data;
    }
  }
  
  // 缓存过期或不存在，重新获取
  const routes = await getRoutes();
  localStorage.setItem(CACHE_KEY, JSON.stringify({
    data: routes,
    timestamp: Date.now()
  }));
  
  return routes;
}
```

### 2. 组件懒加载
- component路径是字符串，需要动态导入组件
- 建议使用懒加载避免首次加载过慢

```javascript
// 组件懒加载
const loadComponent = (componentPath) => {
  return () => import(`@${componentPath}`);
};
```

### 3. 路由更新
- 当菜单配置更新后，用户需要重新登录或刷新页面
- 可以提供"刷新菜单"功能让用户手动更新

```javascript
// 刷新菜单
async function refreshRoutes() {
  localStorage.removeItem(CACHE_KEY);
  const routes = await getRoutes();
  // 重新配置路由器
  router.addRoute(transformRoutes(routes));
}
```

### 4. 错误处理
- API调用失败时，应该有降级方案
- 可以使用默认的静态路由配置

```javascript
// 错误处理
async function getRoutesWithFallback() {
  try {
    return await getRoutes();
  } catch (error) {
    console.error('Failed to load routes:', error);
    // 返回默认路由
    return defaultRoutes;
  }
}
```

## 与菜单树形接口的区别

| 特性 | 路由API | 树形API |
|------|---------|---------|
| 数据格式 | 前端路由格式 | 完整菜单数据 |
| 字段命名 | 驼峰命名(showLink) | 下划线命名(show_link) |
| 用途 | 前端路由配置 | 菜单管理、展示 |
| 权限控制 | 基于用户角色自动筛选 | 需要手动筛选 |
| meta字段 | 扁平化 | 分散在多个字段 |
