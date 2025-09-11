# 许可证方案管理 API 文档

## 概述

许可证方案管理API提供了对软件产品许可证方案的完整CRUD操作，包括创建、查询、更新、删除和复制等功能。所有API都需要管理员权限（超级管理员或租户管理员）。

## 基础信息

- **Base URL**: `/api/v1/licenses/admin/plans/`
- **认证方式**: JWT Bearer Token
- **权限要求**: 超级管理员或租户管理员
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证说明

所有API请求都需要在请求头中包含JWT Token：

```http
Authorization: Bearer <JWT_TOKEN>
```

## 数据模型

### LicensePlan 许可证方案

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 否(只读) | 方案唯一标识ID | `1` |
| `product` | integer | 是 | 关联的软件产品ID | `3` |
| `product_name` | string | 否(只读) | 产品名称 | `"我的软件 v1.0"` |
| `name` | string | 是 | 方案名称 | `"专业版方案"` |
| `code` | string | 是 | 方案代码(产品内唯一) | `"PRO_001"` |
| `plan_type` | string | 是 | 方案类型 | `"professional"` |
| `max_machines` | integer | 是 | 最大机器数 | `5` |
| `validity_days` | integer | 是 | 有效天数 | `365` |
| `features` | object | 否 | 功能配置(JSON对象) | `{"advanced_features": true}` |
| `price` | decimal | 是 | 价格 | `"999.00"` |
| `currency` | string | 是 | 货币代码 | `"CNY"` |
| `status` | string | 是 | 状态 | `"active"` |
| `licenses_count` | integer | 否(只读) | 该方案的许可证数量 | `12` |
| `created_at` | datetime | 否(只读) | 创建时间 | `"2025-09-10T10:00:00Z"` |
| `updated_at` | datetime | 否(只读) | 更新时间 | `"2025-09-10T11:00:00Z"` |

### 枚举值说明

#### plan_type - 方案类型
- `trial`: 试用版
- `basic`: 基础版  
- `professional`: 专业版
- `enterprise`: 企业版
- `custom`: 定制版

#### status - 状态
- `active`: 启用
- `inactive`: 禁用

---

## API 端点详情

### 1. GET /api/v1/licenses/admin/plans/

**获取许可证方案列表**

获取许可证方案的分页列表，支持搜索、过滤和排序功能。

#### 请求参数

##### Query Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `page` | integer | 否 | 页码，从1开始 | `1` |
| `page_size` | integer | 否 | 每页数量(1-100) | `20` |
| `product` | integer | 否 | 按产品ID过滤 | `3` |
| `plan_type` | string | 否 | 按方案类型过滤 | `professional` |
| `status` | string | 否 | 按状态过滤 | `active` |
| `search` | string | 否 | 搜索方案名称或代码 | `专业版` |
| `ordering` | string | 否 | 排序字段 | `-created_at` |

##### 可用的排序字段 (ordering)
- `name`: 按名称排序
- `price`: 按价格排序
- `created_at`: 按创建时间排序
- 添加`-`前缀表示降序，如：`-created_at`

#### 请求示例

```bash
# 基础查询
curl -X GET "http://localhost:8000/api/v1/licenses/admin/plans/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"

# 带过滤和搜索的查询
curl -X GET "http://localhost:8000/api/v1/licenses/admin/plans/?product=3&status=active&search=专业&ordering=-price&page=1&page_size=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"
```

#### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": "2000",
  "message": "操作成功",
  "data": {
    "count": 25,
    "next": "http://localhost:8000/api/v1/licenses/admin/plans/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "product": 3,
        "product_name": "我的软件 v1.0",
        "name": "专业版方案",
        "code": "PRO_001",
        "plan_type": "professional",
        "max_machines": 5,
        "validity_days": 365,
        "features": {
          "advanced_features": true,
          "premium_support": true,
          "api_access": true
        },
        "price": "999.00",
        "currency": "CNY",
        "status": "active",
        "licenses_count": 12,
        "created_at": "2025-09-10T10:00:00.000000Z",
        "updated_at": "2025-09-10T11:00:00.000000Z"
      },
      {
        "id": 2,
        "product": 3,
        "product_name": "我的软件 v1.0",
        "name": "基础版方案",
        "code": "BASIC_001",
        "plan_type": "basic",
        "max_machines": 1,
        "validity_days": 365,
        "features": {
          "basic_features": true
        },
        "price": "299.00",
        "currency": "CNY",
        "status": "active",
        "licenses_count": 25,
        "created_at": "2025-09-09T15:30:00.000000Z",
        "updated_at": "2025-09-09T15:30:00.000000Z"
      }
    ]
  }
}
```

**错误响应**

```json
{
  "success": false,
  "code": "4001",
  "message": "认证失败",
  "data": null
}
```

---

### 2. POST /api/v1/licenses/admin/plans/

**创建许可证方案**

为指定的软件产品创建新的许可证方案。

#### 请求参数

##### Request Body (JSON)

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `product` | integer | 是 | 关联的软件产品ID | `3` |
| `name` | string | 是 | 方案名称(最大100字符) | `"企业版方案"` |
| `code` | string | 是 | 方案代码(最大50字符,产品内唯一) | `"ENT_001"` |
| `plan_type` | string | 是 | 方案类型 | `"enterprise"` |
| `max_machines` | integer | 是 | 最大机器数(≥1) | `10` |
| `validity_days` | integer | 是 | 有效天数(≥1) | `365` |
| `features` | object | 否 | 功能配置JSON对象 | `{"all_features": true}` |
| `price` | decimal | 是 | 价格(≥0,最多10位数字,2位小数) | `"1999.00"` |
| `currency` | string | 否 | 货币代码(默认CNY) | `"CNY"` |
| `status` | string | 否 | 状态(默认active) | `"active"` |

#### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/plans/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "product": 3,
    "name": "企业版方案",
    "code": "ENT_001",
    "plan_type": "enterprise",
    "max_machines": 10,
    "validity_days": 365,
    "features": {
      "all_features": true,
      "priority_support": true,
      "custom_integration": true
    },
    "price": "1999.00",
    "currency": "CNY",
    "status": "active"
  }'
```

#### 响应格式

**成功响应 (201 Created)**

```json
{
  "success": true,
  "code": "2000",
  "message": "操作成功",
  "data": {
    "id": 3,
    "product": 3,
    "product_name": "我的软件 v1.0",
    "name": "企业版方案",
    "code": "ENT_001",
    "plan_type": "enterprise",
    "max_machines": 10,
    "validity_days": 365,
    "features": {
      "all_features": true,
      "priority_support": true,
      "custom_integration": true
    },
    "price": "1999.00",
    "currency": "CNY",
    "status": "active",
    "licenses_count": 0,
    "created_at": "2025-09-10T12:00:00.000000Z",
    "updated_at": "2025-09-10T12:00:00.000000Z"
  }
}
```

**错误响应示例**

```json
// 验证错误 (400 Bad Request)
{
  "success": false,
  "code": "4000",
  "message": "请求参数错误",
  "data": {
    "code": ["方案代码在该产品下已存在"],
    "price": ["确保这个值大于或者等于 0。"]
  }
}

// 产品不存在 (400 Bad Request)
{
  "success": false,
  "code": "4000", 
  "message": "请求参数错误",
  "data": {
    "product": ["无效的主键值 \"999\" - 对象不存在。"]
  }
}
```

---

### 3. GET /api/v1/licenses/admin/plans/{id}/

**获取许可证方案详情**

根据ID获取指定许可证方案的详细信息。

#### 请求参数

##### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证方案ID | `3` |

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/plans/3/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"
```

#### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": "2000",
  "message": "操作成功",
  "data": {
    "id": 3,
    "product": 3,
    "product_name": "我的软件 v1.0",
    "name": "企业版方案",
    "code": "ENT_001",
    "plan_type": "enterprise",
    "max_machines": 10,
    "validity_days": 365,
    "features": {
      "all_features": true,
      "priority_support": true,
      "custom_integration": true
    },
    "price": "1999.00",
    "currency": "CNY",
    "status": "active",
    "licenses_count": 0,
    "created_at": "2025-09-10T12:00:00.000000Z",
    "updated_at": "2025-09-10T12:00:00.000000Z"
  }
}
```

**错误响应示例**

```json
// 方案不存在 (404 Not Found)
{
  "success": false,
  "code": "4004",
  "message": "资源不存在",
  "data": null
}

// 权限不足 (403 Forbidden)
{
  "success": false,
  "code": "4003",
  "message": "权限不足",
  "data": null
}
```

---

### 4. PUT /api/v1/licenses/admin/plans/{id}/

**更新许可证方案**

完整更新指定许可证方案的所有信息。

#### 请求参数

##### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证方案ID | `3` |

##### Request Body (JSON)

所有字段都是必填的，与创建方案时相同。

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `product` | integer | 是 | 关联的软件产品ID | `3` |
| `name` | string | 是 | 方案名称 | `"企业版方案(升级版)"` |
| `code` | string | 是 | 方案代码 | `"ENT_001"` |
| `plan_type` | string | 是 | 方案类型 | `"enterprise"` |
| `max_machines` | integer | 是 | 最大机器数 | `15` |
| `validity_days` | integer | 是 | 有效天数 | `730` |
| `features` | object | 是 | 功能配置 | `{"all_features": true}` |
| `price` | decimal | 是 | 价格 | `"2999.00"` |
| `currency` | string | 是 | 货币代码 | `"CNY"` |
| `status` | string | 是 | 状态 | `"active"` |

#### 请求示例

```bash
curl -X PUT "http://localhost:8000/api/v1/licenses/admin/plans/3/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "product": 3,
    "name": "企业版方案(升级版)",
    "code": "ENT_001", 
    "plan_type": "enterprise",
    "max_machines": 15,
    "validity_days": 730,
    "features": {
      "all_features": true,
      "priority_support": true,
      "custom_integration": true,
      "24x7_support": true
    },
    "price": "2999.00",
    "currency": "CNY",
    "status": "active"
  }'
```

#### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": "2000",
  "message": "操作成功",
  "data": {
    "id": 3,
    "product": 3,
    "product_name": "我的软件 v1.0",
    "name": "企业版方案(升级版)",
    "code": "ENT_001",
    "plan_type": "enterprise",
    "max_machines": 15,
    "validity_days": 730,
    "features": {
      "all_features": true,
      "priority_support": true,
      "custom_integration": true,
      "24x7_support": true
    },
    "price": "2999.00",
    "currency": "CNY",
    "status": "active",
    "licenses_count": 0,
    "created_at": "2025-09-10T12:00:00.000000Z",
    "updated_at": "2025-09-10T13:15:30.000000Z"
  }
}
```

**错误响应示例**

```json
// 验证错误 (400 Bad Request)
{
  "success": false,
  "code": "4000",
  "message": "请求参数错误", 
  "data": {
    "max_machines": ["确保这个值大于或者等于 1。"]
  }
}
```

---

### 5. PATCH /api/v1/licenses/admin/plans/{id}/

**部分更新许可证方案**

部分更新指定许可证方案的信息，只需要提供要更新的字段。

#### 请求参数

##### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证方案ID | `3` |

##### Request Body (JSON)

可以只包含需要更新的字段，字段规则与创建方案时相同。

#### 请求示例

```bash
# 只更新价格和状态
curl -X PATCH "http://localhost:8000/api/v1/licenses/admin/plans/3/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "price": "2499.00",
    "status": "inactive"
  }'

# 只更新功能配置
curl -X PATCH "http://localhost:8000/api/v1/licenses/admin/plans/3/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "all_features": true,
      "priority_support": true,
      "ai_features": true
    }
  }'
```

#### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "code": "2000",
  "message": "操作成功",
  "data": {
    "id": 3,
    "product": 3,
    "product_name": "我的软件 v1.0",
    "name": "企业版方案(升级版)",
    "code": "ENT_001",
    "plan_type": "enterprise",
    "max_machines": 15,
    "validity_days": 730,
    "features": {
      "all_features": true,
      "priority_support": true,
      "ai_features": true
    },
    "price": "2499.00",
    "currency": "CNY",
    "status": "inactive",
    "licenses_count": 0,
    "created_at": "2025-09-10T12:00:00.000000Z",
    "updated_at": "2025-09-10T14:20:15.000000Z"
  }
}
```

---

### 6. DELETE /api/v1/licenses/admin/plans/{id}/

**删除许可证方案**

软删除指定的许可证方案。注意：这是软删除操作，数据不会真正从数据库中删除，只是标记为已删除状态。

⚠️ **重要提醒**: 删除许可证方案会影响使用该方案的所有许可证，请谨慎操作。

#### 请求参数

##### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证方案ID | `3` |

#### 请求示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/licenses/admin/plans/3/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 响应格式

**成功响应 (204 No Content)**

```http
HTTP/1.1 204 No Content
Content-Length: 0
```

**错误响应示例**

```json
// 方案不存在 (404 Not Found)
{
  "success": false,
  "code": "4004",
  "message": "资源不存在",
  "data": null
}

// 方案仍有活跃许可证时的错误 (400 Bad Request)
{
  "success": false,
  "code": "4000",
  "message": "无法删除该方案，还有12个活跃的许可证正在使用",
  "data": null
}
```

---

### 7. POST /api/v1/licenses/admin/plans/{id}/duplicate/

**复制许可证方案**

复制指定的许可证方案，创建一个新的副本。复制的方案将有新的代码和名称，状态默认为`inactive`。

#### 请求参数

##### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 要复制的许可证方案ID | `3` |

#### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/plans/3/duplicate/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

#### 响应格式

**成功响应 (201 Created)**

```json
{
  "success": true,
  "code": "2000",
  "message": "方案复制成功",
  "data": {
    "id": 4,
    "product": 3,
    "product_name": "我的软件 v1.0",
    "name": "企业版方案(升级版) (副本)",
    "code": "ENT_001_copy_20250910_142030",
    "plan_type": "enterprise",
    "max_machines": 15,
    "validity_days": 730,
    "features": {
      "all_features": true,
      "priority_support": true,
      "ai_features": true
    },
    "price": "2499.00",
    "currency": "CNY",
    "status": "inactive",
    "licenses_count": 0,
    "created_at": "2025-09-10T14:20:30.000000Z",
    "updated_at": "2025-09-10T14:20:30.000000Z"
  }
}
```

**错误响应示例**

```json
// 原方案不存在 (404 Not Found)
{
  "success": false,
  "code": "4004",
  "message": "资源不存在",
  "data": null
}

// 服务器内部错误 (500 Internal Server Error)
{
  "success": false,
  "code": "5000",
  "message": "服务器内部错误",
  "data": null
}
```

---

## 权限与访问控制

### 用户类型权限

1. **超级管理员 (is_super_admin=true)**
   - 可以访问所有租户的许可证方案
   - 可以执行所有操作（CRUD + 复制）

2. **租户管理员 (is_admin=true)**
   - 只能访问有权限的产品的许可证方案
   - 权限通过 `TenantLicenseQuota` 模型控制
   - 可以执行所有操作（CRUD + 复制）

### 数据隔离

- 租户管理员只能操作与其租户相关联的产品的许可证方案
- 通过 `product__tenant_quotas__tenant` 关联进行数据过滤
- 只能看到 `product__tenant_quotas__is_active=True` 的产品方案

---

## 错误处理

### HTTP状态码

| 状态码 | 业务代码 | 描述 | 常见原因 |
|-------|----------|------|----------|
| 200 | 2000 | 请求成功 | 操作成功完成 |
| 201 | 2000 | 创建成功 | 资源创建成功 |
| 204 | - | 删除成功 | 资源删除成功 |
| 400 | 4000 | 请求参数错误 | 参数验证失败、数据格式错误 |
| 401 | 4001 | 认证失败 | Token无效或过期 |
| 403 | 4003 | 权限不足 | 用户无权限访问资源 |
| 404 | 4004 | 资源不存在 | 请求的方案不存在 |
| 500 | 5000 | 服务器内部错误 | 系统内部异常 |

### 常见错误场景

#### 1. 认证错误

```json
{
  "success": false,
  "code": "4001",
  "message": "认证失败",
  "data": null
}
```

**解决方案**：检查Authorization头是否正确，Token是否有效。

#### 2. 权限不足

```json
{
  "success": false,
  "code": "4003",
  "message": "权限不足",
  "data": null
}
```

**解决方案**：确认当前用户是管理员角色且有权限访问该资源。

#### 3. 参数验证错误

```json
{
  "success": false,
  "code": "4000",
  "message": "请求参数错误",
  "data": {
    "code": ["方案代码在该产品下已存在"],
    "max_machines": ["确保这个值大于或者等于 1。"],
    "price": ["这个字段是必填项。"]
  }
}
```

**解决方案**：根据data字段中的详细错误信息修正请求参数。

#### 4. 资源不存在

```json
{
  "success": false,
  "code": "4004", 
  "message": "资源不存在",
  "data": null
}
```

**解决方案**：检查请求的方案ID是否正确。

---

## 使用示例

### Python 使用示例

```python
import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api/v1/licenses/admin/plans/"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. 获取方案列表
response = requests.get(f"{BASE_URL}?product=3&status=active", headers=headers)
print("方案列表:", response.json())

# 2. 创建新方案
plan_data = {
    "product": 3,
    "name": "试用版方案",
    "code": "TRIAL_001",
    "plan_type": "trial",
    "max_machines": 1,
    "validity_days": 30,
    "features": {"basic_features": True},
    "price": "0.00",
    "currency": "CNY",
    "status": "active"
}

response = requests.post(BASE_URL, headers=headers, json=plan_data)
new_plan = response.json()
print("创建的方案:", new_plan)

# 3. 获取方案详情
plan_id = new_plan["data"]["id"]
response = requests.get(f"{BASE_URL}{plan_id}/", headers=headers)
print("方案详情:", response.json())

# 4. 更新方案
update_data = {"price": "99.00"}
response = requests.patch(f"{BASE_URL}{plan_id}/", headers=headers, json=update_data)
print("更新后的方案:", response.json())

# 5. 复制方案
response = requests.post(f"{BASE_URL}{plan_id}/duplicate/", headers=headers)
print("复制的方案:", response.json())

# 6. 删除方案（谨慎操作）
# response = requests.delete(f"{BASE_URL}{plan_id}/", headers=headers)
# print("删除响应状态:", response.status_code)
```

### JavaScript 使用示例

```javascript
const BASE_URL = 'http://localhost:8000/api/v1/licenses/admin/plans/';
const TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';

const headers = {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json'
};

// 1. 获取方案列表
async function getLicensePlans(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${BASE_URL}?${params}`, {
        method: 'GET',
        headers: headers
    });
    return await response.json();
}

// 2. 创建方案
async function createLicensePlan(planData) {
    const response = await fetch(BASE_URL, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(planData)
    });
    return await response.json();
}

// 3. 更新方案
async function updateLicensePlan(planId, updateData) {
    const response = await fetch(`${BASE_URL}${planId}/`, {
        method: 'PATCH',
        headers: headers,
        body: JSON.stringify(updateData)
    });
    return await response.json();
}

// 4. 复制方案
async function duplicateLicensePlan(planId) {
    const response = await fetch(`${BASE_URL}${planId}/duplicate/`, {
        method: 'POST',
        headers: headers
    });
    return await response.json();
}

// 使用示例
async function example() {
    try {
        // 获取产品3的所有活跃方案
        const plans = await getLicensePlans({product: 3, status: 'active'});
        console.log('方案列表:', plans);
        
        // 创建新方案
        const newPlan = await createLicensePlan({
            product: 3,
            name: '测试方案',
            code: 'TEST_001',
            plan_type: 'trial',
            max_machines: 1,
            validity_days: 30,
            price: '0.00'
        });
        console.log('新创建的方案:', newPlan);
        
    } catch (error) {
        console.error('API调用失败:', error);
    }
}
```

---

## 最佳实践

### 1. 方案代码设计
- 使用有意义的前缀，如 `TRIAL_`, `BASIC_`, `PRO_`, `ENT_`
- 包含版本信息，如 `PRO_V1_001`
- 保持简短但描述性强

### 2. 功能配置设计
```json
{
  "features": {
    "core_features": true,
    "advanced_reporting": true,
    "api_access": {
      "enabled": true,
      "rate_limit": 1000
    },
    "support_level": "premium",
    "concurrent_users": 100
  }
}
```

### 3. 价格策略
- 使用decimal类型确保精确计算
- 统一货币单位管理
- 考虑不同地区的定价策略

### 4. 状态管理
- 新方案建议先设为`inactive`状态
- 充分测试后再激活
- 定期清理无用的方案

### 5. 错误处理
- 始终检查响应状态和业务代码
- 实现重试机制处理网络错误
- 记录详细的错误日志

---

## 总结

许可证方案管理API提供了完整的CRUD操作和方案复制功能，支持灵活的查询过滤和排序。通过合理的权限控制确保数据安全，通过详细的错误信息帮助快速定位问题。

在实际使用中，建议：
1. 仔细设计方案的代码和功能配置
2. 充分利用过滤和搜索功能提高查询效率
3. 合理使用方案复制功能快速创建相似方案
4. 在删除方案前确保没有依赖的许可证
5. 建立完善的错误处理和日志记录机制

如有任何问题或需要进一步的技术支持，请联系系统管理员。
