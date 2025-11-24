# API 响应格式标准

## 概述

本文档详细定义了 Lipeaks Backend 项目所有 API 的响应格式标准。系统通过中间件和渲染器自动确保所有响应遵循统一的格式。

## 标准响应结构

### 基本格式

所有 API 响应都遵循以下JSON结构：

```json
{
  "success": true/false,
  "code": 2000,
  "message": "操作成功/失败信息",
  "data": <any>,
  "error_code": "ERROR_CODE"  // 仅错误响应
}
```

### 字段详细说明

#### 1. success (Boolean, 必需)

**说明**: 表示请求是否成功处理

**取值**:
- `true` - 请求成功，操作完成
- `false` - 请求失败，发生错误

**规则**:
- HTTP 2xx 状态码时为 `true`
- HTTP 4xx/5xx 状态码时为 `false`

**示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {...}
}
```

#### 2. code (Integer, 必需)

**说明**: 业务状态码，用于标识具体的业务结果

**取值范围**:
- `2000-2999`: 成功响应
- `4000-4999`: 客户端错误
- `5000-5999`: 服务器错误

**规则**:
- 与 HTTP 状态码配合使用
- 提供比 HTTP 状态码更细粒度的业务状态信息
- 便于前端根据具体业务码做不同处理

**常用业务码**:

| 业务码 | 含义 | HTTP状态码 |
|-------|------|-----------|
| 2000 | 操作成功 | 200 |
| 4000 | 请求参数错误 | 400 |
| 4001 | 认证失败，未登录 | 401 |
| 4003 | 权限不足 | 403 |
| 4004 | 资源不存在 | 404 |
| 4005 | 请求方法不允许 | 405 |
| 4029 | 请求过于频繁 | 429 |
| 5000 | 服务器内部错误 | 500 |

**模块化错误码**:

系统采用模块化错误码管理，每个业务模块有独立的错误码范围：

| 模块 | 错误码范围 | 示例 |
|------|-----------|------|
| 认证授权 | 4000-4099 | 4001: 未认证, 4003: 无权限 |
| 租户管理 | 4100-4199 | 4101: 租户不存在, 4102: 租户未激活 |
| 许可证 | 4200-4299 | 4201: 许可证过期, 4203: 配额超限 |
| 用户管理 | 4300-4399 | 4301: 用户不存在, 4302: 用户未激活 |
| 积分系统 | 4400-4499 | 4401: 积分不足, 4402: 积分过期 |
| CMS系统 | 4500-4599 | 4501: 文章不存在, 4502: 分类不存在 |
| 订单系统 | 4600-4699 | 4601: 订单不存在, 4602: 订单已取消 |

详细的错误码规范请参考 [错误码规范文档](../exception/03_error_code_specification.md)。

**示例**:
```json
{
  "success": false,
  "code": 4101,
  "message": "租户不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

#### 3. message (String, 必需)

**说明**: 人类可读的操作结果描述

**规则**:
- 清晰简洁，描述操作结果
- 用户友好，避免技术术语
- 不暴露敏感信息（如数据库结构、堆栈信息）
- 支持国际化（未来）

**成功消息示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {...}
}
```

**错误消息示例**:
```json
{
  "success": false,
  "code": 4101,
  "message": "租户ID 123 不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

**消息编写原则**:

✅ **好的消息**:
- "操作成功"
- "用户创建成功"
- "租户ID 123 不存在"
- "许可证已于 2025-01-15 过期"
- "积分余额不足，当前: 100，需要: 500"

❌ **不好的消息**:
- "Error" - 太模糊
- "Something went wrong" - 不具体
- "Database query failed" - 暴露技术细节
- "Tenant not found in table tenant_table" - 暴露数据库结构

#### 4. data (Any, 必需)

**说明**: 响应的实际数据内容

**取值类型**:
- **对象 (Object)**: 单个资源数据
- **数组 (Array)**: 资源列表
- **null**: 无数据（通常在错误或删除操作中）

**成功响应的 data**:

**单个资源**:
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 1,
    "name": "租户A",
    "status": "active",
    "created_at": "2025-01-08T10:30:00Z"
  }
}
```

**资源列表（无分页）**:
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": [
    {"id": 1, "name": "项目A"},
    {"id": 2, "name": "项目B"}
  ]
}
```

**分页数据**:
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

**无数据响应**:
```json
{
  "success": true,
  "code": 2000,
  "message": "删除成功",
  "data": null
}
```

**错误响应的 data**:

**通用错误（data 为 null）**:
```json
{
  "success": false,
  "code": 4101,
  "message": "租户不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

**验证错误（data 包含字段错误详情）**:
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "name": ["该字段不能为空"],
    "email": ["请输入有效的邮箱地址"],
    "age": ["必须是正整数"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

#### 5. error_code (String, 可选)

**说明**: 错误标识符，仅在 `success=false` 时存在

**作用**:
- 提供机器可读的错误标识
- 便于前端根据错误类型做不同处理
- 支持国际化时作为翻译key
- 便于日志记录和问题追踪

**命名规范**:
- 全大写字母
- 使用下划线分隔单词
- 格式: `MODULE_DESCRIPTION`

**示例**:
```json
{
  "success": false,
  "code": 4101,
  "message": "租户ID 123 不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

**常用错误标识符**:

| 错误码 | error_code | 说明 |
|-------|-----------|------|
| 4001 | AUTH_NOT_AUTHENTICATED | 未认证 |
| 4003 | AUTH_PERMISSION_DENIED | 权限不足 |
| 4004 | NOT_FOUND | 资源不存在 |
| 4000 | VALIDATION_ERROR | 验证错误 |
| 4101 | TENANT_NOT_FOUND | 租户不存在 |
| 4201 | LICENSE_EXPIRED | 许可证过期 |
| 5000 | INTERNAL_SERVER_ERROR | 服务器错误 |

完整的错误标识符列表请参考 [错误码规范](../exception/03_error_code_specification.md)。

## HTTP 状态码映射

### HTTP 状态码与业务码的关系

系统同时使用 HTTP 状态码和业务状态码：

- **HTTP 状态码**: 表示 HTTP 协议层面的结果
- **业务状态码**: 表示业务逻辑层面的结果

### 映射表

| HTTP状态码 | 业务码 | 说明 | success |
|-----------|-------|------|---------|
| 200 OK | 2000 | 操作成功 | true |
| 201 Created | 2000 | 资源创建成功 | true |
| 204 No Content | 2000 | 操作成功（无内容） | true |
| 400 Bad Request | 4000 | 请求参数错误 | false |
| 401 Unauthorized | 4001 | 未认证 | false |
| 403 Forbidden | 4003 | 权限不足 | false |
| 404 Not Found | 4004 | 资源不存在 | false |
| 405 Method Not Allowed | 4005 | 方法不允许 | false |
| 429 Too Many Requests | 4029 | 请求过于频繁 | false |
| 500 Internal Server Error | 5000 | 服务器错误 | false |

### 示例

**HTTP 200 + 业务码 2000 (成功)**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {...}
}
```

**HTTP 404 + 业务码 4101 (租户不存在)**:
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "success": false,
  "code": 4101,
  "message": "租户ID 123 不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

**HTTP 400 + 业务码 4201 (许可证过期)**:
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "success": false,
  "code": 4201,
  "message": "许可证已于 2025-01-15 过期",
  "data": null,
  "error_code": "LICENSE_EXPIRED"
}
```

## 特殊响应格式

### 分页响应

分页响应使用特殊的 data 结构：

```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "pagination": {
      "count": 100,           // 总记录数
      "next": "...",          // 下一页链接
      "previous": null,       // 上一页链接
      "page_size": 10,        // 每页数量
      "current_page": 1,      // 当前页码
      "total_pages": 10       // 总页数
    },
    "results": [...]          // 当前页数据
  }
}
```

**分页字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| count | Integer | 总记录数 |
| next | String/null | 下一页的完整URL，最后一页为 null |
| previous | String/null | 上一页的完整URL，第一页为 null |
| page_size | Integer | 每页显示的记录数 |
| current_page | Integer | 当前页码（从1开始） |
| total_pages | Integer | 总页数 |
| results | Array | 当前页的数据列表 |

**实现**: 使用 `common/pagination/StandardResultsSetPagination`

### 验证错误响应

数据验证失败时，`data` 字段包含字段级错误信息：

```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "username": ["该字段不能为空"],
    "email": ["请输入有效的邮箱地址", "该邮箱已被使用"],
    "age": ["必须是正整数", "年龄必须在18-100之间"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

**特点**:
- `data` 为对象，key 是字段名
- 每个字段的值是错误消息数组（支持多个错误）
- HTTP 状态码为 400
- 业务码为 4000

## 响应格式的自动化

### 自动转换机制

开发者无需手动构建响应格式，系统会自动处理：

```python
# ✅ 推荐做法 - 直接返回数据
from rest_framework.response import Response

def get(self, request, pk):
    user = User.objects.get(pk=pk)
    serializer = UserSerializer(user)
    return Response(serializer.data)
    # 自动转换为标准格式

# ❌ 不推荐 - 手动构建格式
def get(self, request, pk):
    user = User.objects.get(pk=pk)
    serializer = UserSerializer(user)
    return Response({
        'success': True,
        'code': 2000,
        'message': '成功',
        'data': serializer.data
    })
```

### 转换组件

系统通过以下组件实现自动转换：

1. **ResponseStandardizationMiddleware** - 中间件层转换
2. **StandardJSONRenderer** - 渲染器层转换
3. **custom_exception_handler** - 异常处理转换

详细实现机制请参考 [实现机制说明](./04_implementation_mechanism.md)。

## 版本兼容性

### 当前版本: v1.0

所有 API 默认使用 v1.0 响应格式。

### 未来版本规划

- **v1.1** - 添加 `timestamp` 字段（响应时间戳）
- **v1.2** - 添加 `request_id` 字段（请求追踪ID）
- **v2.0** - 支持多语言错误消息

### 向后兼容承诺

- 现有字段不会删除
- 字段类型不会改变
- 只会添加新的可选字段
- 重大变更会通过新的 API 版本号标识

## 最佳实践

### 1. 使用 DRF Response

```python
# ✅ 使用 DRF Response
from rest_framework.response import Response

return Response(data)

# ❌ 不要使用 Django JsonResponse
from django.http import JsonResponse

return JsonResponse({'data': data})  # 可能不会被正确处理
```

### 2. 让系统处理错误

```python
# ✅ 抛出异常，让全局处理器处理
from common.exceptions import TenantNotFoundException

if not tenant:
    raise TenantNotFoundException(detail=f'租户ID {tenant_id} 不存在')

# ❌ 手动构建错误响应
if not tenant:
    return Response({
        'success': False,
        'code': 4101,
        'message': '租户不存在'
    }, status=404)
```

### 3. 使用序列化器

```python
# ✅ 使用序列化器处理数据
serializer = UserSerializer(user)
return Response(serializer.data)

# ❌ 手动构建数据结构
return Response({
    'id': user.id,
    'name': user.name,
    # ... 容易遗漏字段
})
```

### 4. 使用 raise_exception

```python
# ✅ 使用 raise_exception=True
serializer = UserSerializer(data=request.data)
serializer.is_valid(raise_exception=True)
# 自动抛出 ValidationError

# ❌ 手动处理验证错误
if not serializer.is_valid():
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=400)
```

## 总结

遵循本响应格式标准可以：

1. ✅ **统一体验** - 所有 API 返回一致的结构
2. ✅ **简化开发** - 无需手动构建响应格式
3. ✅ **易于调试** - 清晰的错误码和消息
4. ✅ **便于集成** - 前端可以编写通用的响应处理逻辑
5. ✅ **向后兼容** - 结构稳定，便于版本升级

---

**维护者**: Lipeaks Backend Team  
**最后更新**: 2025-11-02  
**版本**: 1.0.0


