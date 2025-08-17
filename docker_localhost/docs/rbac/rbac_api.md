# RBAC API 设计

以下是RBAC系统需要实现的API接口设计。这些接口基于文档中的要求，并符合RESTful设计原则。

## 1. 权限管理API

### 1.1 获取权限列表
**端点:** `GET /api/v1/rbac/permissions/`  
**说明:** 获取系统中所有权限，支持分页、搜索和按类别过滤  
**权限要求:** `permission:view`  
**查询参数:**
- `search`: 搜索关键词(针对name, code, description)
- `category`: 按类别过滤
- `is_system`: 是否系统权限(true/false)
- `page`, `page_size`: 分页参数

### 1.2 获取权限详情
**端点:** `GET /api/v1/rbac/permissions/{id}/`  
**说明:** 获取单个权限的详细信息  
**权限要求:** `permission:view`  

### 1.3 创建权限
**端点:** `POST /api/v1/rbac/permissions/`  
**说明:** 创建新权限  
**权限要求:** `permission:create`  
**请求体:**
```json
{
  "code": "resource:action",
  "name": "权限名称",
  "description": "权限描述",
  "category": "权限类别",
  "is_system": false
}
```

### 1.4 更新权限
**端点:** `PUT /api/v1/rbac/permissions/{id}/`  
**说明:** 更新现有权限  
**权限要求:** `permission:edit`  

### 1.5 删除权限
**端点:** `DELETE /api/v1/rbac/permissions/{id}/`  
**说明:** 删除权限(系统权限不可删除)  
**权限要求:** `permission:delete`  

### 1.6 获取权限类别
**端点:** `GET /api/v1/rbac/permissions/categories/`  
**说明:** 获取系统中所有权限类别  
**权限要求:** `permission:view`  

## 2. 角色管理API

### 2.1 获取角色列表
**端点:** `GET /api/v1/rbac/roles/`  
**说明:** 获取角色列表，根据当前用户租户上下文过滤  
**权限要求:** `role:view`  
**查询参数:**
- `search`: 搜索关键词(针对name, code, description)
- `tenant_id`: 按租户过滤(超管可用)
- `is_system`: 是否系统角色(true/false)
- `page`, `page_size`: 分页参数

### 2.2 获取角色详情
**端点:** `GET /api/v1/rbac/roles/{id}/`  
**说明:** 获取角色详情，包括关联的权限  
**权限要求:** `role:view`  

### 2.3 创建角色
**端点:** `POST /api/v1/rbac/roles/`  
**说明:** 创建新角色  
**权限要求:** `role:create`  
**请求体:**
```json
{
  "name": "角色名称",
  "code": "role_code",
  "description": "角色描述",
  "tenant_id": null,  // null表示系统角色
  "is_system": false
}
```

### 2.4 更新角色
**端点:** `PUT /api/v1/rbac/roles/{id}/`  
**说明:** 更新角色信息  
**权限要求:** `role:edit`  

### 2.5 删除角色
**端点:** `DELETE /api/v1/rbac/roles/{id}/`  
**说明:** 删除角色(系统角色不可删除)  
**权限要求:** `role:delete`  

### 2.6 获取角色权限
**端点:** `GET /api/v1/rbac/roles/{id}/permissions/`  
**说明:** 获取角色关联的所有权限  
**权限要求:** `role:view`  

### 2.7 分配权限到角色
**端点:** `POST /api/v1/rbac/roles/{id}/permissions/`  
**说明:** 分配一个或多个权限给角色  
**权限要求:** `permission:assign`  
**请求体:**
```json
{
  "permission_ids": [1, 2, 3]
}
```

### 2.8 从角色移除权限
**端点:** `DELETE /api/v1/rbac/roles/{id}/permissions/{permission_id}/`  
**说明:** 从角色中移除指定权限  
**权限要求:** `permission:assign`  

### 2.9 批量更新角色权限
**端点:** `PUT /api/v1/rbac/roles/{id}/permissions/`  
**说明:** 批量更新角色的全部权限(替换现有权限)  
**权限要求:** `permission:assign`  
**请求体:**
```json
{
  "permission_ids": [1, 2, 3, 4]
}
```

## 3. 用户角色管理API

### 3.1 获取用户角色列表
**端点:** `GET /api/v1/rbac/user-roles/`  
**说明:** 获取用户角色关联列表，支持按用户类型、角色等过滤  
**权限要求:** `role:view`  
**查询参数:**
- `user_type`: 用户类型(user/member)
- `user_id`: 用户ID
- `role_id`: 角色ID
- `is_active`: 是否激活
- `page`, `page_size`: 分页参数

### 3.2 获取指定用户的角色
**端点:** `GET /api/v1/rbac/users/{user_type}/{user_id}/roles/`  
**说明:** 获取指定用户关联的所有角色  
**权限要求:** `role:view`  

### 3.3 为用户分配角色
**端点:** `POST /api/v1/rbac/users/{user_type}/{user_id}/roles/`  
**说明:** 为指定用户分配一个角色  
**权限要求:** `role:assign`  
**请求体:**
```json
{
  "role_id": 1,
  "is_active": true,
  "start_date": "2023-01-01",  // 可选
  "end_date": "2023-12-31"     // 可选
}
```

### 3.4 从用户移除角色
**端点:** `DELETE /api/v1/rbac/users/{user_type}/{user_id}/roles/{role_id}/`  
**说明:** 从用户中移除指定角色  
**权限要求:** `role:assign`  

### 3.5 更新用户角色关联
**端点:** `PUT /api/v1/rbac/users/{user_type}/{user_id}/roles/{role_id}/`  
**说明:** 更新用户角色关联的属性(如有效期、激活状态)  
**权限要求:** `role:assign`  
**请求体:**
```json
{
  "is_active": false,
  "start_date": "2023-01-01",
  "end_date": "2023-12-31"
}
```

## 4. 权限验证API

### 4.1 检查当前用户权限
**端点:** `GET /api/v1/rbac/permissions/check/`  
**说明:** 检查当前用户是否拥有指定权限  
**权限要求:** 任何已认证用户  
**查询参数:**
- `code`: 权限代码

### 4.2 批量检查权限
**端点:** `POST /api/v1/rbac/permissions/batch-check/`  
**说明:** 批量检查当前用户是否拥有多个权限  
**权限要求:** 任何已认证用户  
**请求体:**
```json
{
  "codes": ["permission:code1", "permission:code2", "permission:code3"]
}
```

### 4.3 获取用户所有权限
**端点:** `GET /api/v1/rbac/users/{user_type}/{user_id}/permissions/`  
**说明:** 获取指定用户拥有的所有权限  
**权限要求:** `permission:view`  

## 5. 权限缓存管理API

### 5.1 刷新权限缓存
**端点:** `POST /api/v1/rbac/cache/refresh/`  
**说明:** 刷新所有权限缓存  
**权限要求:** `permission:manage`  

### 5.2 刷新指定用户权限缓存
**端点:** `POST /api/v1/rbac/cache/refresh/user/{user_type}/{user_id}/`  
**说明:** 刷新指定用户的权限缓存  
**权限要求:** `permission:manage`  

## 6. 租户权限管理API

### 6.1 获取租户角色列表
**端点:** `GET /api/v1/rbac/tenants/{tenant_id}/roles/`  
**说明:** 获取指定租户的所有角色  
**权限要求:** `role:view` + 租户访问权限  

### 6.2 从系统角色创建租户角色
**端点:** `POST /api/v1/rbac/tenants/{tenant_id}/roles/from-template/`  
**说明:** 从系统角色模板创建租户特定角色  
**权限要求:** `role:create` + 租户访问权限  
**请求体:**
```json
{
  "template_role_id": 1,  // 系统角色模板ID
  "name": "租户特定角色名称",  // 可选，默认使用模板名称
  "code": "custom_code",   // 可选，默认使用模板代码
  "description": "租户特定角色描述"  // 可选
}
```

## 权限缓存机制说明

系统使用Django的缓存框架存储用户权限，以提高权限检查的性能。缓存的配置和使用方式如下：

### 缓存存储位置

权限缓存存储在Django配置的默认缓存后端中，通常是以下几种之一：

1. **内存缓存**：在开发环境中默认使用，数据存储在应用内存中
2. **Redis缓存**：生产环境推荐使用，数据存储在Redis服务器中
3. **数据库缓存**：可选配置，数据存储在数据库的缓存表中
4. **文件缓存**：可选配置，数据存储在文件系统中

### 缓存键设计

缓存键的格式为：`rbac_user_permissions_{user_type}_{user_id}`

例如：
- `rbac_user_permissions_user_1`：表示ID为1的管理员用户的权限缓存
- `rbac_user_permissions_member_5`：表示ID为5的普通成员用户的权限缓存

### 缓存值内容

缓存的值是一个包含用户所有权限代码的集合(set)，例如：
```
{'user:view', 'user:edit', 'role:view', 'cms:view', ...}
```

### 缓存过期策略

缓存默认设置了10分钟的过期时间（`RBAC_CACHE_TIMEOUT = 60 * 10`），避免长期使用过时的权限数据。

### 缓存刷新触发点

在以下情况下需要刷新权限缓存：

1. 用户的角色发生变化（增加、移除、修改角色关联）
2. 角色的权限发生变化（增加或移除权限）
3. 用户相关属性变更（如租户变更）
4. 系统管理员手动触发缓存刷新 