# 集成系统多租户RBAC权限设计文档

## 1. 概述

本文档描述了集成系统的多租户环境下的基于角色的访问控制(RBAC)设计。该系统支持多个租户，每个租户拥有独立的用户群体和管理员。系统通过精细化的权限模型确保数据隔离和安全访问。

## 2. 用户角色定义

系统定义了以下三种主要角色：

### 2.1 超级管理员 (Super Admin)

**角色标识**: `super_admin`

**权限范围**:
- 可以管理所有租户
- 可以创建、修改、删除任何租户
- 可以在任何租户内创建、修改、删除用户
- 可以赋予或撤销用户的租户管理员权限
- 可以访问系统的所有功能和页面

### 2.2 租户管理员 (Tenant Admin)

**角色标识**: `admin`

**权限范围**:
- 只能管理自己所属租户内的用户
- 可以在自己的租户内创建、修改、删除用户
- 无法访问租户管理功能
- 无法管理其他租户的用户
- 可以上传、修改用户头像（仅在编辑用户时，不能在创建用户时上传头像）

### 2.3 普通用户 (User)

**角色标识**: `user`

**权限范围**:
- 只能访问基本功能和自己的个人资料
- 可以修改自己的基本信息和密码
- 可以上传、修改自己的头像
- 无法访问管理功能

## 3. 权限实现机制

### 3.1 后端权限控制

#### 3.1.1 自定义权限类

系统使用Django REST Framework的权限类机制，定义了以下核心权限类：

- `IsSuperAdmin`: 验证用户是否是超级管理员
- `IsAdmin`: 验证用户是否是租户管理员或超级管理员
- `IsAdminUser`: 验证用户是否是系统管理员用户
- `IsTeamMember`: 验证用户是否是团队成员
- `IsOwner`: 验证用户是否是资源所有者

这些权限类在`common/permissions.py`中定义，并在视图中应用。

#### 3.1.2 数据过滤

- 租户管理员只能看到和管理自己租户内的数据
- 系统在查询时自动添加租户过滤条件
- 示例：用户列表API会根据当前用户的租户ID自动过滤数据

```python
# 自动添加租户过滤条件示例
if not request.user.is_super_admin:
    queryset = queryset.filter(tenant_id=request.user.tenant_id)
```

### 3.2 前端权限控制

#### 3.2.1 基于角色的菜单显示

- 只对有权限的用户显示相应的菜单项
- 租户管理模块只对超级管理员显示
- 使用Vue.js的条件渲染和Pinia状态管理实现

```vue
<!-- 只对超级管理员显示租户管理菜单 -->
<el-sub-menu index="tenants" v-if="hasPermission(['super_admin'])">
  <template #title>
    <el-icon><OfficeBuilding /></el-icon>
    <span>租户管理</span>
  </template>
  <el-menu-item index="/tenants">租户列表</el-menu-item>
  <el-menu-item index="/tenants/create">创建租户</el-menu-item>
</el-sub-menu>
```

#### 3.2.2 API调用权限控制

- 前端根据用户角色调整API请求
- 租户管理员在获取用户列表时自动传递租户ID参数
- 非超级管理员不调用租户相关API

```javascript
// 用户列表API调用示例
async getUserList() {
  try {
    // 构建查询参数
    const params = { ...this.queryParams }
    
    // 只有超级管理员可以按租户筛选用户
    if (!this.isSuperAdmin && params.tenant_id) {
      delete params.tenant_id
    }
    
    // 调用API
    const response = await getUserList(params)
    this.userList = response.data.results
    this.total = response.data.count
  } catch (error) {
    console.error('获取用户列表失败:', error)
    this.$message.error('获取用户列表失败')
  }
}
```

## 4. 租户隔离实现

### 4.1 数据隔离

- 所有用户数据模型包含tenant_id字段，关联到对应的租户
- 查询数据时自动添加租户过滤条件
- 租户管理员无法越权访问其他租户数据

### 4.2 功能隔离

- 租户管理员无法访问租户管理功能
- 前端通过路由守卫防止越权访问：

```javascript
// 路由守卫示例
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查是否需要超级管理员权限
  if (to.meta.requiresSuperAdmin && !authStore.isSuperAdmin) {
    next('/403') // 重定向到无权限页面
    return
  }
  
  next()
})
```

## 5. 认证机制

### 5.1 JWT认证

- 系统使用JWT(JSON Web Token)进行API认证
- 登录成功后，服务器返回token
- 前端将token存储在localStorage中
- 每次API请求通过Authorization头传递token

### 5.2 Token配置

- token有效期为24小时
- 支持通过刷新token延长会话
- 登出时清除token

## 6. 安全最佳实践

### 6.1 API权限强制校验

- 所有API默认需要认证
- 使用drf_spectacular hooks确保所有API文档包含安全要求
- 避免依赖前端进行权限控制，后端始终进行严格校验

### 6.2 详细日志记录

- 记录所有权限检查过程
- 记录权限验证失败的原因
- 便于问题排查和安全审计

### 6.3 防止越权访问

- 参数验证：检查URL参数与用户所属租户是否匹配
- 数据验证：确保只返回用户有权限访问的数据
- 避免直接在URL中暴露敏感ID

## 7. 示例场景

### 7.1 租户管理员登录流程

1. 租户管理员使用凭据登录系统
2. 系统验证凭据并返回包含用户信息和权限的token
3. 前端根据用户角色渲染菜单，租户管理选项不可见
4. 租户管理员访问用户列表，系统自动只显示其所属租户的用户
5. 尝试通过URL直接访问租户管理页面时，系统拒绝访问

### 7.2 用户管理

1. 租户管理员只能为自己租户创建用户
2. 租户管理员无法为用户选择租户，自动使用管理员所属租户
3. 超级管理员可以选择任何租户来创建用户

## 8. 未来改进

- 实现更细粒度的权限控制，支持自定义角色和权限组
- 添加双因素认证增强安全性
- 实现基于资源的访问控制(ABAC)
- 添加IP地址限制和异常登录监测
