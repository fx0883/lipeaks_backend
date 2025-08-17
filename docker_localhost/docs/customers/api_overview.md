# 客户管理API概述

本文档提供了客户管理系统API的概述和使用指南。客户管理系统API提供了对客户信息、客户与联系人关系、客户与租户关系的管理功能。

## API基础路径

所有客户管理API的基础路径为：`/api/v1/customers/`

## 认证要求

所有API都需要认证，请在请求头中添加JWT令牌：

```
Authorization: Bearer <your_jwt_token>
```

## 权限要求

- 大多数API需要管理员权限（`IsAdmin`）
- 租户视角的客户API需要租户管理员权限（`IsTenantAdmin`）

## API分类

客户管理API分为以下几类：

### 1. 客户基础操作API

提供客户的基本CRUD操作，以及搜索、筛选和统计功能。

- `GET /api/v1/customers/` - 获取客户列表（支持分页、排序）
- `GET /api/v1/customers/{id}/` - 获取单个客户详情
- `POST /api/v1/customers/` - 创建新客户
- `PUT /api/v1/customers/{id}/` - 更新客户全部信息
- `PATCH /api/v1/customers/{id}/` - 部分更新客户信息
- `DELETE /api/v1/customers/{id}/` - 删除客户（软删除）
- `GET /api/v1/customers/search/` - 搜索客户
- `GET /api/v1/customers/statistics/` - 获取客户统计数据

### 2. 客户批量操作API

提供客户的批量创建、更新和删除功能。

- `POST /api/v1/customers/bulk-create/` - 批量创建客户
- `POST /api/v1/customers/bulk-update/` - 批量更新客户
- `POST /api/v1/customers/bulk-delete/` - 批量删除客户

### 3. 客户-联系人关系API

管理客户与联系人（Member）之间的关系。

- `GET /api/v1/customers/members/relations/` - 获取客户的联系人关系列表
- `POST /api/v1/customers/members/relations/` - 添加客户与联系人的关系
- `GET /api/v1/customers/members/relations/{id}/` - 获取特定客户-联系人关系详情
- `PUT /api/v1/customers/members/relations/{id}/` - 更新客户-联系人关系
- `DELETE /api/v1/customers/members/relations/{id}/` - 删除客户-联系人关系
- `POST /api/v1/customers/members/relations/{id}/set-primary/` - 设置主要联系人
- `GET /api/v1/customers/members/relations/primary/` - 获取客户的主要联系人

### 4. 客户-租户关系API

管理客户与租户（Tenant）之间的关系。

- `GET /api/v1/customers/tenants/relations/` - 获取客户的租户关系列表
- `POST /api/v1/customers/tenants/relations/` - 添加客户与租户的关系
- `GET /api/v1/customers/tenants/relations/{id}/` - 获取特定客户-租户关系详情
- `PUT /api/v1/customers/tenants/relations/{id}/` - 更新客户-租户关系
- `DELETE /api/v1/customers/tenants/relations/{id}/` - 删除客户-租户关系
- `POST /api/v1/customers/tenants/relations/{id}/set-primary/` - 设置主要租户关系
- `GET /api/v1/customers/tenants/relations/primary/` - 获取客户的主要租户关系
- `GET /api/v1/customers/tenants/relations/between/` - 获取客户与租户之间的关系

### 5. 租户视角的客户API

从租户的视角查看和管理客户。

- `GET /api/v1/customers/tenants/view/` - 获取租户关联的客户列表
- `GET /api/v1/customers/tenants/view/{id}/` - 获取租户视角下的客户详情
- `GET /api/v1/customers/tenants/view/statistics/` - 获取租户的客户统计数据
- `GET /api/v1/customers/tenants/view/{id}/relations/` - 获取客户与租户的关系

## 请求参数

大多数API支持以下查询参数：

- 分页参数：`page`、`page_size`
- 排序参数：`ordering`（例如：`ordering=name`、`ordering=-created_at`）
- 筛选参数：根据API不同，支持不同的筛选字段

## 响应格式

所有API的响应都遵循标准的JSON格式：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    // 响应数据
  }
}
```

分页响应格式：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "count": 100,
    "next": "http://api.example.com/api/v1/customers/?page=2",
    "previous": null,
    "results": [
      // 数据列表
    ]
  }
}
```

## 错误处理

当API发生错误时，会返回相应的HTTP状态码和错误信息：

```json
{
  "code": 400,
  "message": "请求参数错误",
  "errors": {
    "field_name": [
      "错误描述"
    ]
  }
}
```

常见的错误状态码：

- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未认证或认证失败
- `403 Forbidden` - 权限不足
- `404 Not Found` - 资源不存在
- `500 Internal Server Error` - 服务器内部错误

## API文档

详细的API文档可以通过以下链接访问：

- Swagger UI：`/api/v1/docs/`
- ReDoc：`/api/v1/redoc/`
- OpenAPI Schema：`/api/v1/schema/` 