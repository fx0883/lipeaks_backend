# RBAC权限系统使用指南

## 1. 系统概述

RBAC（基于角色的访问控制）是一种广泛使用的权限管理方法，通过角色作为用户和权限之间的桥梁，实现灵活而高效的权限控制。本系统实现了完整的RBAC权限管理功能，支持多租户环境下的权限隔离和管理。

### 1.1 核心概念

- **权限(Permission)**: 代表系统中的一项具体操作权限，如"查看用户"、"创建角色"等
- **角色(Role)**: 权限的集合，可分配给用户
- **用户角色(UserRole)**: 用户与角色的关联关系，支持时间限制
- **租户(Tenant)**: 系统支持多租户，每个租户可以有自己的角色和权限体系

### 1.2 主要特点

- **多租户支持**: 支持租户级别的角色隔离，系统角色可跨租户使用
- **时间限制**: 角色分配支持有效期设置，可临时授权
- **权限缓存**: 使用缓存提高权限检查性能
- **多用户类型**: 支持管理员(User)和普通成员(Member)两种用户类型
- **灵活的权限检查**: 提供多种权限检查方式，适用于不同场景

## 2. 权限管理

### 2.1 权限结构

权限由以下属性组成：

| 属性 | 说明 | 示例 |
|------|------|------|
| code | 权限唯一标识符 | user:create |
| name | 权限名称 | 创建用户 |
| description | 权限描述 | 允许创建新用户 |
| category | 权限分类 | 用户管理 |
| is_system | 是否系统权限 | True |

### 2.2 查看权限列表

通过API获取所有权限：

```
GET /api/v1/rbac/permissions/
```

### 2.3 创建自定义权限

创建新权限：

```
POST /api/v1/rbac/permissions/
{
    "code": "custom:action",
    "name": "自定义操作",
    "description": "自定义权限描述",
    "category": "自定义分类"
}
```

## 3. 角色管理

### 3.1 角色结构

角色由以下属性组成：

| 属性 | 说明 | 示例 |
|------|------|------|
| name | 角色名称 | 内容编辑 |
| code | 角色代码 | content_editor |
| description | 角色描述 | 负责内容编辑和发布 |
| tenant | 所属租户 | null(系统角色)/租户ID |
| is_system | 是否系统角色 | False |
| permissions | 角色包含的权限 | [权限列表] |

### 3.2 角色操作

#### 3.2.1 查看角色列表

```
GET /api/v1/rbac/roles/
```

#### 3.2.2 创建角色

```
POST /api/v1/rbac/roles/
{
    "name": "内容编辑",
    "code": "content_editor",
    "description": "负责内容编辑和发布",
    "tenant": 1,  // 可选，为null表示系统角色
    "permissions": [1, 2, 3]  // 权限ID列表
}
```

#### 3.2.3 查看租户角色

```
GET /api/v1/rbac/tenants/{tenant_id}/roles/
```

#### 3.2.4 从模板创建租户角色

```
POST /api/v1/rbac/tenants/{tenant_id}/roles/from-template/
```

## 4. 用户角色管理

### 4.1 分配角色给用户

```
POST /api/v1/rbac/users/{user_type}/{user_id}/roles/
{
    "role_id": 1,
    "is_active": true,
    "start_date": "2023-01-01",  // 可选
    "end_date": "2023-12-31"     // 可选
}
```

其中，`user_type`可以是`user`(管理员)或`member`(普通成员)。

### 4.2 查看用户角色

```
GET /api/v1/rbac/users/{user_type}/{user_id}/roles/
```

### 4.3 删除用户角色

```
DELETE /api/v1/rbac/users/{user_type}/{user_id}/roles/{role_id}/
```

### 4.4 查看用户权限

```
GET /api/v1/rbac/users/{user_type}/{user_id}/permissions/
```

## 5. 权限缓存管理

为提高性能，系统会缓存用户权限。当角色或权限发生变化时，可能需要刷新缓存。

### 5.1 刷新所有缓存

```
POST /api/v1/rbac/cache/refresh/
```

### 5.2 刷新指定用户缓存

```
POST /api/v1/rbac/cache/refresh/user/{user_type}/{user_id}/
```

## 6. 在代码中使用RBAC

### 6.1 检查用户权限

```python
from rbac.permissions import has_permission

# 检查用户是否有指定权限
if has_permission(request.user, 'user:create'):
    # 允许操作
    pass
else:
    # 拒绝操作
    pass
```

### 6.2 使用装饰器保护视图函数

```python
from rbac.permissions import rbac_permission_required

@rbac_permission_required('user:create')
def create_user_view(request):
    # 只有拥有'user:create'权限的用户才能访问此视图
    pass
```

### 6.3 在DRF视图中使用权限类

```python
from rbac.permissions import HasRBACPermission

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [HasRBACPermission('user:view')]
    # ...
```

### 6.4 在DRF视图集中使用动态权限

```python
from rbac.permissions import RBACPermissionRequired

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [RBACPermissionRequired]
    rbac_permissions = {
        'list': 'user:view',
        'retrieve': 'user:view',
        'create': 'user:create',
        'update': 'user:edit',
        'partial_update': 'user:edit',
        'destroy': 'user:delete'
    }
    # ...
```

## 7. 初始化RBAC数据

系统提供了管理命令来初始化RBAC数据：

```bash
# 初始化基本RBAC结构
python manage.py init_rbac

# 初始化示例RBAC数据
python manage.py init_rbac_data
```

## 8. 最佳实践

### 8.1 权限命名规范

建议使用`资源:操作`的格式命名权限，例如：
- user:create
- role:assign
- content:publish

### 8.2 角色设计原则

- 遵循最小权限原则，只授予必要的权限
- 根据职责划分角色，避免角色权限过大
- 系统角色应谨慎创建，因为它们对所有租户可见

### 8.3 权限缓存管理

- 在批量更新权限或角色后，记得刷新相关用户的权限缓存
- 权限缓存默认有效期为10分钟，可根据需要调整

## 9. 常见问题

### 9.1 权限检查失败

如果权限检查失败，可能的原因：
- 用户未被分配相应角色
- 角色未包含所需权限
- 用户角色已过期或未激活
- 权限缓存未更新

### 9.2 系统角色与租户角色

- 系统角色(tenant=null)对所有租户可见
- 租户角色只在特定租户内可见和使用
- 超级管理员(is_super_admin=True)拥有所有权限，不受RBAC限制

### 9.3 权限缓存问题

如果权限变更未生效，尝试：
1. 刷新特定用户的权限缓存
2. 刷新所有权限缓存
3. 检查用户角色的有效期和激活状态 