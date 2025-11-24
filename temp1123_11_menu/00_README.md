# 菜单管理API文档

## 概述

本文档详细说明了菜单管理系统的所有API端点，包括参数说明、返回格式和使用示例。

## 目录

1. [01_菜单基础API.md](./01_菜单基础API.md) - 菜单的增删改查操作
2. [02_菜单树形结构API.md](./02_菜单树形结构API.md) - 获取菜单树形结构
3. [03_管理员菜单路由API.md](./03_管理员菜单路由API.md) - 获取前端路由配置
4. [04_用户菜单API.md](./04_用户菜单API.md) - 用户菜单相关操作
5. [05_用户菜单管理API.md](./05_用户菜单管理API.md) - 为用户分配和管理菜单

## 测试说明

- 服务器地址：`http://localhost:8000`
- 所有API都需要认证，使用Bearer Token
- 测试脚本：`test_menu_apis.sh`

## 权限说明

### 租户管理员权限
- 可以查看所有菜单列表
- 可以查看菜单详情
- 可以创建新菜单
- 可以查看菜单树形结构
- 可以获取自己的菜单路由
- 可以查看自己的菜单

### 超级管理员权限
- 拥有租户管理员的所有权限
- 可以更新和删除菜单
- 可以为其他用户分配菜单
- 可以移除用户的菜单

## Token说明

### 租户管理员Token
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM
```

### 超级管理员Token
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNzY0NTEwNzExLCJtb2RlbF90eXBlIjoidXNlciIsImlzX2FkbWluIjp0cnVlLCJpc19zdXBlcl9hZG1pbiI6dHJ1ZSwiaXNfc3RhZmYiOnRydWV9.fr23WBsROaD207MCYN-cLzVpR3gqA7EPiFoivmmfNeQ
```

## 测试结果

所有API测试通过 ✅

- ✅ GET /api/v1/menus/ - 获取菜单列表
- ✅ GET /api/v1/menus/{id}/ - 获取单个菜单
- ✅ POST /api/v1/menus/ - 创建菜单
- ✅ PUT /api/v1/menus/{id}/ - 更新菜单
- ✅ PATCH /api/v1/menus/{id}/ - 部分更新菜单
- ✅ DELETE /api/v1/menus/{id}/ - 删除菜单
- ✅ GET /api/v1/menus/tree/ - 获取菜单树形结构
- ✅ GET /api/v1/menus/admin/routes/ - 获取管理员菜单路由
- ✅ GET /api/v1/menus/user/ - 获取current用户的菜单
- ✅ GET /api/v1/menus/admins/{user_id}/menus/ - 获取用户的菜单列表
- ✅ POST /api/v1/menus/admins/{user_id}/menus/ - 分配菜单给用户
- ✅ DELETE /api/v1/menus/admins/{user_id}/menus/{id}/ - 移除用户的菜单
- ✅ DELETE /api/v1/menus/admins/{user_id}/menus/batch/ - 批量移除用户菜单

## 数据模型

### Menu（菜单）
菜单模型定义了系统的导航菜单项，包含路由配置、显示属性、权限设置等。

### UserMenu（用户菜单）
用户菜单关联模型，定义用户与菜单的多对多关系。
