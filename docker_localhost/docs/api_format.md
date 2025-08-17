# API响应统一格式规范

## 概述

本文档详细描述了系统中API响应的统一格式标准。系统使用中间件自动将所有API响应转换为一致的格式，确保前端开发人员获得结构一致的数据。

## 响应格式标准

所有API响应（包括成功和错误响应）都遵循以下统一格式：

```json
{
  "success": true/false,     // 布尔值，表示请求是否成功
  "code": 2000,              // 业务状态码，表示具体状态
  "message": "操作成功/失败信息", // 提示消息
  "data": {                  // 响应数据主体
    // 具体业务数据
  }
}
```

### 字段说明

| 字段名 | 类型 | 说明 |
|-------|------|-----|
| success | Boolean | 请求是否成功，true表示成功，false表示失败 |
| code | Integer | 业务状态码，2000表示成功，4xxx表示客户端错误，5xxx表示服务器错误 |
| message | String | 操作结果的文字描述，成功或错误提示 |
| data | Object/Array/null | 响应的具体数据，错误时可能为null或包含错误详情 |

## 业务状态码说明

系统使用三层业务状态码：

| 业务状态码范围 | 描述 |
| ------------- | --- |
| 2000-2999 | 成功响应 |
| 4000-4999 | 客户端错误 |
| 5000-5999 | 服务器错误 |

### 常见业务状态码

| 业务状态码 | 描述 | HTTP状态码 |
| --------- | ---- | --------- |
| 2000      | 操作成功 | 200 OK |
| 4000      | 请求参数错误 | 400 Bad Request |
| 4001      | 认证失败 | 401 Unauthorized |
| 4003      | 权限不足 | 403 Forbidden |
| 4004      | 资源不存在 | 404 Not Found |
| 4005      | 方法不允许 | 405 Method Not Allowed |
| 4029      | 请求过于频繁 | 429 Too Many Requests |
| 5000      | 服务器内部错误 | 500 Internal Server Error |

## 实现机制

系统通过两种机制确保所有API响应遵循统一格式：

1. **响应标准化中间件**：`ResponseStandardizationMiddleware` 拦截所有API响应并转换为标准格式
2. **自定义JSON渲染器**：`StandardJSONRenderer` 确保所有REST Framework响应符合标准格式

## 常见响应示例

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_active": true
  }
}
```

### 分页数据响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {
      "count": 100,
      "next": "http://example.com/api/users?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 10
    },
    "results": [
      {
        "id": 1,
        "username": "user1"
      },
      {
        "id": 2,
        "username": "user2"
      }
    ]
  }
}
```

### 错误响应示例

#### 参数验证错误

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "username": ["该用户名已被使用"],
    "email": ["请输入有效的电子邮件地址"]
  }
}
```

#### 认证错误

```json
{
  "success": false,
  "code": 4001,
  "message": "认证失败，请登录",
  "data": null
}
```
```