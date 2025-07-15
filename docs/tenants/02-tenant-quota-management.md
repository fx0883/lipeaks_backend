# 租户配额管理

本文档介绍租户管理模块的配额管理功能，包括获取租户配额、更新租户配额和获取租户配额使用情况。

## 1. 获取租户配额

### 接口信息

- **URL**: `/api/v1/tenants/{id}/quota/`
- **方法**: GET
- **权限要求**: 超级管理员或该租户的管理员

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 1,
    "tenant": {
      "id": 1,
      "name": "测试租户1"
    },
    "max_users": 20,
    "max_admins": 5,
    "max_storage_mb": 2048,
    "max_products": 100,
    "current_storage_used_mb": 120,
    "created_at": "2025-04-20T10:00:00Z",
    "updated_at": "2025-04-20T10:00:00Z"
  }
}
```

## 2. 更新租户配额

### 接口信息

- **URL**: `/api/v1/tenants/{id}/quota/`
- **方法**: PUT
- **权限要求**: 超级管理员

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| max_users | integer | 是 | 最大用户数 |
| max_admins | integer | 是 | 最大管理员数 |
| max_storage_mb | integer | 是 | 最大存储空间(MB) |
| max_products | integer | 是 | 最大产品数 |

### 请求示例

```json
{
  "max_users": 30,
  "max_admins": 8,
  "max_storage_mb": 5120,
  "max_products": 200
}
```

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "更新配额成功",
  "data": {
    "id": 1,
    "tenant": {
      "id": 1,
      "name": "测试租户1"
    },
    "max_users": 30,
    "max_admins": 8,
    "max_storage_mb": 5120,
    "max_products": 200,
    "current_storage_used_mb": 120,
    "created_at": "2025-04-20T10:00:00Z",
    "updated_at": "2025-04-22T10:00:00Z"
  }
}
```

## 3. 获取租户配额使用情况

### 接口信息

- **URL**: `/api/v1/tenants/{id}/quota/usage/`
- **方法**: GET
- **权限要求**: 超级管理员或该租户的管理员

### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| id | integer | 是 | 租户ID |

### 响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "users": {
      "current": 10,
      "maximum": 20,
      "percentage": 50.0
    },
    "admins": {
      "current": 2,
      "maximum": 5,
      "percentage": 40.0
    },
    "storage": {
      "current": 120,
      "maximum": 2048,
      "percentage": 5.9,
      "formatted": "120 MB / 2.0 GB"
    },
    "products": {
      "current": 25,
      "maximum": 100,
      "percentage": 25.0
    }
  }
}
```

## 4. 配额管理界面设计建议

### 配额展示组件

1. **配额卡片**：为每种资源类型（用户、管理员、存储空间、产品）创建卡片，显示当前使用量和最大限制。

2. **配额使用情况仪表盘**：使用图表库创建仪表盘，直观显示配额使用情况。

### 配额编辑表单

创建一个表单，允许超级管理员修改租户配额，包含以下字段：
- 最大用户数
- 最大管理员数
- 最大存储空间(MB)
- 最大产品数

## 下一步

请查看[租户状态管理](./03-tenant-status-management.md)，了解如何管理租户的状态（激活/暂停）。 