# API 响应格式标准文档

## 概述

本目录包含 Lipeaks Backend 项目的 API 响应格式标准文档。系统通过统一的响应格式确保前后端交互的一致性和可预测性。

## 为什么需要统一的响应格式？

在 API 开发中，统一的响应格式带来以下优势：
- ✅ **一致性** - 所有 API 返回相同结构，降低前端开发复杂度
- ✅ **可预测性** - 开发者可以编写通用的响应处理逻辑
- ✅ **易于调试** - 统一的错误码和消息格式便于定位问题
- ✅ **自动化处理** - 中间件自动转换，无需在每个视图中重复编写
- ✅ **向后兼容** - 结构稳定，便于版本升级

## 响应格式概览

### 标准响应结构

所有 API 响应（包括成功和失败）都遵循以下统一格式：

```json
{
  "success": true/false,      // 请求是否成功
  "code": 2000,               // 业务状态码
  "message": "操作成功",       // 提示消息
  "data": {...},              // 响应数据
  "error_code": "..."         // 错误标识符（仅错误响应）
}
```

### 字段说明

| 字段 | 类型 | 说明 | 必需 |
|------|------|------|------|
| `success` | Boolean | 请求是否成功，`true` 表示成功，`false` 表示失败 | 是 |
| `code` | Integer | 业务状态码，2000 表示成功，4xxx 表示客户端错误，5xxx 表示服务器错误 | 是 |
| `message` | String | 操作结果的文字描述 | 是 |
| `data` | Any | 响应的具体数据，可以是对象、数组或 null | 是 |
| `error_code` | String | 错误标识符（字符串常量），仅在 `success=false` 时存在 | 否 |

## 文档导航

### 1. [响应格式标准](./01_response_format_standard.md)
- 完整的响应格式规范
- 字段详细说明
- 业务状态码体系
- HTTP 状态码映射

### 2. [成功响应示例](./02_success_response_examples.md)
- 单个资源查询响应
- 资源列表响应
- 分页数据响应
- 资源创建/更新响应
- 无数据响应

### 3. [错误响应示例](./03_error_response_examples.md)
- 业务异常响应
- 验证错误响应
- 认证授权错误响应
- 资源不存在响应
- 服务器错误响应
- 结合错误码规范的完整示例

### 4. [实现机制说明](./04_implementation_mechanism.md)
- 响应标准化中间件
- 自定义 JSON 渲染器
- 全局异常处理器
- 工作流程图
- 最佳实践

## 快速开始

### 成功响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "示例数据",
    "created_at": "2025-01-08T10:30:00Z"
  }
}
```

### 错误响应示例

```json
{
  "success": false,
  "code": 4101,
  "message": "租户ID 123 不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

### 分页响应示例

```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {
      "count": 100,
      "next": "http://api.example.com/users?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 10
    },
    "results": [
      {"id": 1, "name": "用户1"},
      {"id": 2, "name": "用户2"}
    ]
  }
}
```

## 业务状态码体系

### 状态码范围

| 范围 | 类别 | 说明 |
|------|------|------|
| 2000-2999 | 成功响应 | 操作成功完成 |
| 4000-4999 | 客户端错误 | 请求参数错误、权限不足等 |
| 5000-5999 | 服务器错误 | 服务器内部错误 |

### 常用业务状态码

| 业务状态码 | 描述 | HTTP状态码 |
|-----------|------|-----------|
| 2000 | 操作成功 | 200 OK |
| 4000 | 请求参数错误 | 400 Bad Request |
| 4001 | 认证失败 | 401 Unauthorized |
| 4003 | 权限不足 | 403 Forbidden |
| 4004 | 资源不存在 | 404 Not Found |
| 4029 | 请求过于频繁 | 429 Too Many Requests |
| 5000 | 服务器内部错误 | 500 Internal Server Error |

### 模块化错误码

系统采用模块化错误码管理，详细错误码请参考 [错误码规范文档](../exception/03_error_code_specification.md)：

| 模块 | 错误码范围 | 示例 |
|------|-----------|------|
| 认证授权 | 4000-4099 | 4001: 未认证, 4003: 无权限 |
| 租户管理 | 4100-4199 | 4101: 不存在, 4102: 未激活 |
| 许可证管理 | 4200-4299 | 4201: 已过期, 4203: 配额超限 |
| 用户管理 | 4300-4399 | 4301: 不存在, 4302: 未激活 |
| 积分系统 | 4400-4499 | 4401: 余额不足, 4402: 已过期 |
| CMS系统 | 4500-4599 | 4501: 文章不存在 |
| 订单系统 | 4600-4699 | 4601: 订单不存在 |

## 实现机制

系统通过三个核心组件实现响应格式的自动标准化：

### 1. ResponseStandardizationMiddleware

**位置**: `common/middleware/response_standardization_middleware.py`

**职责**: 拦截所有 API 响应，将非标准格式转换为统一格式

### 2. StandardJSONRenderer

**位置**: `common/renderers.py`

**职责**: 确保所有 REST Framework 响应符合标准格式

### 3. custom_exception_handler

**位置**: `common/exceptions/handler.py`

**职责**: 捕获所有异常并转换为标准错误响应

### 工作流程

```
[View 层返回数据]
        ↓
[StandardJSONRenderer 渲染]
        ↓
[ResponseStandardizationMiddleware 处理]
        ↓
[标准格式响应]
```

如果发生异常：

```
[异常抛出]
        ↓
[custom_exception_handler 捕获]
        ↓
[转换为标准错误响应]
        ↓
[返回客户端]
```

## 最佳实践

### 视图层开发

1. **直接返回数据** - 不要在视图中构建响应格式
2. **使用 DRF Response** - 让中间件和渲染器处理格式化
3. **抛出异常** - 错误情况直接抛出异常，由全局处理器处理

```python
# ✅ 好的做法
from rest_framework.response import Response

def get(self, request, pk):
    user = User.objects.get(pk=pk)
    serializer = UserSerializer(user)
    return Response(serializer.data)  # 自动转换为标准格式

# ❌ 不好的做法
def get(self, request, pk):
    user = User.objects.get(pk=pk)
    serializer = UserSerializer(user)
    return Response({
        'success': True,
        'code': 2000,
        'message': '成功',
        'data': serializer.data  # 手动构建，冗余且易错
    })
```

### 错误处理

```python
# ✅ 好的做法 - 抛出业务异常
from common.exceptions import TenantNotFoundException

def get_tenant(tenant_id):
    try:
        return Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        raise TenantNotFoundException(
            detail=f'租户ID {tenant_id} 不存在',
            tenant_id=tenant_id
        )

# ❌ 不好的做法 - 手动构建错误响应
def get_tenant(tenant_id):
    try:
        return Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return Response({
            'success': False,
            'code': 4101,
            'message': '租户不存在'
        }, status=404)
```

## 与异常处理系统的集成

本响应格式标准与 [异常处理系统](../exception/README.md) 深度集成：

- **统一格式** - 错误响应与成功响应使用相同的结构
- **错误码体系** - 业务状态码与异常类一一对应
- **自动转换** - 异常自动转换为标准错误响应
- **上下文信息** - 异常中的额外信息可以包含在响应中

详细的异常处理文档请参考：
- [异常处理架构设计](../exception/01_exception_architecture.md)
- [错误码规范](../exception/03_error_code_specification.md)
- [异常使用指南](../exception/04_exception_usage_guide.md)

## 前端集成指南

### TypeScript 类型定义

```typescript
// API 响应基础接口
interface ApiResponse<T = any> {
  success: boolean;
  code: number;
  message: string;
  data: T;
  error_code?: string;
}

// 分页响应接口
interface PaginationInfo {
  count: number;
  next: string | null;
  previous: string | null;
  page_size: number;
  current_page: number;
  total_pages: number;
}

interface PaginatedResponse<T> {
  pagination: PaginationInfo;
  results: T[];
}

// 使用示例
type UserListResponse = ApiResponse<PaginatedResponse<User>>;
type UserDetailResponse = ApiResponse<User>;
```

### Axios 拦截器示例

```javascript
import axios from 'axios';

// 响应拦截器
axios.interceptors.response.use(
  (response) => {
    // 提取标准响应的 data 字段
    const { success, code, message, data, error_code } = response.data;
    
    if (success) {
      return data; // 返回实际数据
    } else {
      // 处理业务错误
      return Promise.reject({
        code,
        message,
        error_code
      });
    }
  },
  (error) => {
    // 处理 HTTP 错误
    if (error.response) {
      const { code, message, error_code } = error.response.data;
      return Promise.reject({
        code,
        message,
        error_code
      });
    }
    return Promise.reject(error);
  }
);
```

### Fetch API 示例

```javascript
async function fetchUser(userId) {
  const response = await fetch(`/api/users/${userId}`);
  const result = await response.json();
  
  if (result.success) {
    return result.data;
  } else {
    throw new Error(result.message);
  }
}
```

## 版本变更记录

### v1.0.0 (2025-01-08)
- 建立统一的 API 响应格式标准
- 实现响应标准化中间件
- 集成异常处理系统
- 完善文档体系

## 相关资源

- [异常处理系统文档](../exception/README.md)
- [错误码规范](../exception/03_error_code_specification.md)
- [Django REST Framework 文档](https://www.django-rest-framework.org/)
- 项目代码：
  - `common/middleware/response_standardization_middleware.py`
  - `common/renderers.py`
  - `common/exceptions/handler.py`

---

**维护者**: Lipeaks Backend Team  
**最后更新**: 2025-11-02



















































