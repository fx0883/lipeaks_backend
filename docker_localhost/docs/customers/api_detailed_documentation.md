# 客户管理API详细文档

本文档提供了客户管理系统API的详细文档索引，包括各类API的使用方法、请求参数和响应格式。

## 文档目录

1. [客户管理API概述](api_overview.md) - 客户管理API的概述和基本说明
2. [客户基础操作API](customer_basic_api.md) - 客户的基本CRUD操作API
3. [客户批量操作API](customer_bulk_operations_api.md) - 客户的批量创建、更新和删除API
4. [客户-联系人关系API](customer_member_relations_api.md) - 客户与联系人之间关系的管理API
5. [客户-租户关系API](customer_tenant_relations_api.md) - 客户与租户之间关系的管理API
6. [租户视角的客户API](tenant_view_customers_api.md) - 从租户角度查看和管理客户的API

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

## 响应格式

所有API的响应都遵循标准的JSON格式：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    // 响应数据
  }
}
```

分页响应格式：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 100,
      "next": "http://api.example.com/api/v1/customers/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 10
    },
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
  "success": false,
  "code": 4000,
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
- `409 Conflict` - 资源冲突
- `500 Internal Server Error` - 服务器内部错误

## API文档

详细的API文档可以通过以下链接访问：

- Swagger UI：`/api/v1/docs/`
- ReDoc：`/api/v1/redoc/`
- OpenAPI Schema：`/api/v1/schema/` 