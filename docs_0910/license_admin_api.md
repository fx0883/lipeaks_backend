# 许可证管理 API 文档

## 📋 系统概述

LiPeaks许可证管理系统提供完整的许可证生命周期管理功能，包括许可证的创建、激活、监控、撤销和统计分析。本文档详细介绍了管理端许可证管理API的使用方法。

### 🎯 核心功能
- **许可证CRUD管理** - 创建、查询、更新、删除许可证
- **许可证状态控制** - 激活、撤销、挂起、过期管理
- **机器绑定管控** - 限制和监控设备使用
- **使用统计分析** - 详细的使用数据和趋势分析
- **批量操作支持** - 高效的批量管理功能
- **安全审计跟踪** - 完整的操作日志记录
- **租户隔离** - 多租户环境下的数据隔离

## 🔐 认证与权限

### 认证方式
使用JWT Bearer Token认证：

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

### 权限要求
- **超级管理员 (is_super_admin=true)**: 可访问所有租户数据
- **租户管理员 (is_admin=true)**: 只能访问所属租户的数据

### JWT Token解析示例
```json
{
  "user_id": 2,
  "username": "admin_jin", 
  "exp": 1757593277,
  "model_type": "user",
  "is_admin": true,
  "is_super_admin": false
}
```

## 🚀 许可证管理API

### 基础信息

**基础URL**: `http://localhost:8000/api/v1/licenses/admin/licenses/`

**支持的HTTP方法**: `GET` `POST` `PUT` `PATCH` `DELETE`

---

## 1. GET /api/v1/licenses/admin/licenses/

**获取许可证列表**

获取许可证的分页列表，支持搜索、过滤和排序功能。

### 请求参数

#### Query Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `page` | integer | 否 | 页码，从1开始 | `1` |
| `page_size` | integer | 否 | 每页数量(1-100) | `20` |
| `product` | integer | 否 | 按产品ID过滤 | `3` |
| `plan` | integer | 否 | 按方案ID过滤 | `2` |
| `status` | string | 否 | 按状态过滤 | `activated` |
| `tenant` | integer | 否 | 按租户ID过滤（仅超级管理员可用） | `5` |
| `search` | string | 否 | 搜索许可证密钥、客户名称或邮箱 | `张三` |
| `ordering` | string | 否 | 排序字段 | `-issued_at` |

#### 状态值 (status)
- `generated`: 已生成
- `activated`: 已激活
- `suspended`: 已挂起
- `revoked`: 已撤销
- `expired`: 已过期

#### 可用的排序字段 (ordering)
- `issued_at`: 按签发时间排序
- `expires_at`: 按过期时间排序
- `customer_name`: 按客户名称排序
- 添加`-`前缀表示降序，如：`-issued_at`

### 请求示例

```bash
# 基础查询
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"

# 带过滤和搜索的查询
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/?product=3&status=activated&search=张三&ordering=-issued_at&page=1&page_size=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"
```

### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "count": 156,
    "next": "http://localhost:8000/api/v1/licenses/admin/licenses/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "product": 1,
        "product_name": "SuperApp Pro",
        "plan": 2,
        "plan_name": "专业版",
        "tenant": 3,
        "tenant_name": "科技有限公司",
        "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
        "customer_name": "张三",
        "customer_email": "zhangsan@example.com",
        "max_activations": 5,
        "current_activations": 2,
        "issued_at": "2024-09-01T10:00:00Z",
        "expires_at": "2025-09-01T10:00:00Z",
        "last_verified_at": "2024-09-10T08:30:00Z",
        "status": "activated",
        "machine_bindings_count": 2,
        "days_until_expiry": 356,
        "notes": "年度企业许可证"
      },
      {
        "id": 2,
        "product": 1,
        "product_name": "SuperApp Pro",
        "plan": 1,
        "plan_name": "基础版",
        "tenant": 3,
        "tenant_name": "科技有限公司",
        "license_key": "SAPP-BAS-2024-WXYZ-9876-5432",
        "customer_name": "李四",
        "customer_email": "lisi@example.com",
        "max_activations": 1,
        "current_activations": 1,
        "issued_at": "2024-09-05T14:30:00Z",
        "expires_at": "2025-09-05T14:30:00Z",
        "last_verified_at": "2024-09-10T10:15:00Z",
        "status": "activated",
        "machine_bindings_count": 1,
        "days_until_expiry": 360,
        "notes": ""
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

## 2. POST /api/v1/licenses/admin/licenses/

**创建许可证**

为指定的软件产品和方案创建新的许可证。

### 请求参数

#### Request Body (JSON)

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `product` | integer | 是 | 软件产品ID | `3` |
| `plan` | integer | 是 | 许可方案ID | `2` |
| `tenant` | integer | 是 | 租户ID | `5` |
| `customer_info` | object | 是 | 客户信息对象 | 见下表 |
| `max_activations` | integer | 否 | 最大激活数，默认从方案继承 | `10` |
| `validity_days` | integer | 否 | 有效天数，默认从方案继承 | `365` |
| `notes` | string | 否 | 备注信息(最大1000字符) | `"企业定制版许可证"` |

#### customer_info 对象结构

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `name` | string | 是 | 客户姓名(最大100字符) | `"李四"` |
| `email` | string | 是 | 客户邮箱 | `"lisi@example.com"` |
| `company` | string | 否 | 客户公司(最大200字符) | `"创新科技"` |
| `phone` | string | 否 | 客户电话 | `"13800138000"` |

#### 重要说明

⚠️ **产品-方案一致性验证**: 系统会自动验证所选择的 `plan` 是否属于所选择的 `product`。如果不一致，将返回验证错误。

📋 **推荐做法**:
- **方案1**: 只提供 `plan` 参数，系统会自动设置对应的 `product`
- **方案2**: 先选择 `product`，然后只选择该产品下的 `plan`
- **方案3**: 如果同时提供 `product` 和 `plan`，请确保它们匹配

### 请求示例

#### 推荐方式1：只提供plan，自动设置product
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "plan": 2,
    "tenant": 3,
    "customer_info": {
      "name": "李四",
      "email": "lisi@example.com",
      "company": "创新科技",
      "phone": "13800138000"
    },
    "max_activations": 10,
    "validity_days": 365,
    "notes": "企业定制版许可证"
  }'
```

#### 方式2：同时提供product和plan（需确保匹配）
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "product": 1,
    "plan": 2,
    "tenant": 3,
    "customer_info": {
      "name": "李四", 
      "email": "lisi@example.com",
      "company": "创新科技",
      "phone": "13800138000"
    },
    "max_activations": 10,
    "validity_days": 365,
    "notes": "企业定制版许可证"
  }'
```

### 响应格式

**成功响应 (201 Created)**

```json
{
  "success": true,
  "message": "许可证创建成功",
  "data": {
    "id": 157,
    "product": 1,
    "product_name": "SuperApp Pro",
    "plan": 2,
    "plan_name": "专业版",
    "tenant": 3,
    "tenant_name": "科技有限公司",
    "license_key": "SAPP-PRO-2024-WXYZ-9876-5432",
    "customer_name": "李四",
    "customer_email": "lisi@example.com",
    "max_activations": 10,
    "current_activations": 0,
    "issued_at": "2024-09-10T14:30:00Z",
    "expires_at": "2025-09-10T14:30:00Z",
    "last_verified_at": null,
    "status": "generated",
    "machine_bindings_count": 0,
    "days_until_expiry": 365,
    "notes": "企业定制版许可证"
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
    "customer_info": ["客户信息缺少必要字段: email"],
    "max_activations": ["确保这个值大于或者等于 1。"]
  }
}

// 产品-方案不一致错误 (400 Bad Request)
{
  "success": false,
  "code": "4000",
  "message": "请求参数错误",
  "data": {
    "plan": ["所选方案(基础版)属于产品(SuperApp Basic)，与所选产品(SuperApp Pro)不一致，请重新选择正确的方案。"]
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

## 3. GET /api/v1/licenses/admin/licenses/{id}/

**获取许可证详情**

根据ID获取指定许可证的详细信息，包括机器绑定、激活记录和使用统计。

### 请求参数

#### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证ID | `1` |

### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"
```

### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "product": 1,
    "product_name": "SuperApp Pro",
    "plan": 2,
    "plan_name": "专业版",
    "tenant": 3,
    "tenant_name": "科技有限公司",
    "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
    "customer_name": "张三",
    "customer_email": "zhangsan@example.com",
    "max_activations": 5,
    "current_activations": 2,
    "issued_at": "2024-09-01T10:00:00Z",
    "expires_at": "2025-09-01T10:00:00Z",
    "last_verified_at": "2024-09-10T08:30:00Z",
    "status": "activated",
    "machine_bindings_count": 2,
    "days_until_expiry": 356,
    "notes": "年度企业许可证",
    "metadata": {
      "creation_source": "api",
      "created_by": "admin"
    },
    "machine_bindings": [
      {
        "id": 10,
        "license": 1,
        "license_key_preview": "SAPP-...1234",
        "machine_id": "DESKTOP-ABC123",
        "hardware_summary": {
          "cpu": "Intel i7-10700K",
          "memory": "32GB",
          "gpu": "RTX 3080"
        },
        "os_info": {
          "name": "Windows 11",
          "version": "10.0.22000"
        },
        "last_ip_address": "192.168.1.100",
        "status": "active",
        "first_seen_at": "2024-09-01T12:00:00Z",
        "last_seen_at": "2024-09-10T08:30:00Z",
        "days_since_last_seen": 0
      },
      {
        "id": 11,
        "license": 1,
        "license_key_preview": "SAPP-...1234",
        "machine_id": "LAPTOP-XYZ789",
        "hardware_summary": {
          "cpu": "Intel i5-1135G7",
          "memory": "16GB",
          "gpu": "Intel Iris Xe"
        },
        "os_info": {
          "name": "Windows 10",
          "version": "10.0.19042"
        },
        "last_ip_address": "192.168.1.101",
        "status": "active",
        "first_seen_at": "2024-09-02T09:15:00Z",
        "last_seen_at": "2024-09-09T18:45:00Z",
        "days_since_last_seen": 1
      }
    ],
    "recent_activations": [
      {
        "id": 25,
        "license": 1,
        "license_key_preview": "SAPP-...1234",
        "machine_id": "DESKTOP-ABC123",
        "activation_type": "online",
        "activation_code": "ACT-2024-XYZ789",
        "client_version": "2.1.0",
        "ip_address": "192.168.1.100",
        "result": "success",
        "error_message": "",
        "activated_at": "2024-09-01T12:00:00Z",
        "expires_at": "2025-09-01T12:00:00Z"
      },
      {
        "id": 26,
        "license": 1,
        "license_key_preview": "SAPP-...1234",
        "machine_id": "LAPTOP-XYZ789",
        "activation_type": "online",
        "activation_code": "ACT-2024-ABC456",
        "client_version": "2.1.0",
        "ip_address": "192.168.1.101",
        "result": "success",
        "error_message": "",
        "activated_at": "2024-09-02T09:15:00Z",
        "expires_at": "2025-09-02T09:15:00Z"
      }
    ],
    "usage_stats": {
      "total_usage_logs": 1245,
      "recent_usage_logs": 89
    }
  }
}
```

**错误响应示例**

```json
// 许可证不存在 (404 Not Found)
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

## 4. PUT /api/v1/licenses/admin/licenses/{id}/

**更新许可证**

完整更新指定许可证的所有信息。

### 请求参数

#### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证ID | `1` |

#### Request Body (JSON)

所有字段都是必填的，与创建许可证时相同的字段结构。

⚠️ **产品-方案一致性验证**: 更新时同样会验证产品和方案的一致性，请确保所选择的 `plan` 属于所选择的 `product`。

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `product` | integer | 是 | 关联的软件产品ID | `1` |
| `plan` | integer | 是 | 许可方案ID | `2` |
| `tenant` | integer | 是 | 租户ID | `3` |
| `customer_name` | string | 是 | 客户名称 | `"张三"` |
| `customer_email` | string | 是 | 客户邮箱 | `"zhangsan@example.com"` |
| `max_activations` | integer | 是 | 最大激活数 | `8` |
| `status` | string | 是 | 许可证状态 | `"activated"` |
| `notes` | string | 否 | 备注信息 | `"更新激活数限制"` |

### 请求示例

```bash
curl -X PUT "http://localhost:8000/api/v1/licenses/admin/licenses/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "product": 1,
    "plan": 2,
    "tenant": 3,
    "customer_name": "张三",
    "customer_email": "zhangsan@example.com",
    "max_activations": 8,
    "status": "activated",
    "notes": "更新激活数限制"
  }'
```

### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "message": "许可证更新成功",
  "data": {
    "id": 1,
    "product": 1,
    "product_name": "SuperApp Pro",
    "plan": 2,
    "plan_name": "专业版",
    "tenant": 3,
    "tenant_name": "科技有限公司",
    "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
    "customer_name": "张三",
    "customer_email": "zhangsan@example.com",
    "max_activations": 8,
    "current_activations": 2,
    "issued_at": "2024-09-01T10:00:00Z",
    "expires_at": "2025-09-01T10:00:00Z",
    "last_verified_at": "2024-09-10T08:30:00Z",
    "status": "activated",
    "machine_bindings_count": 2,
    "days_until_expiry": 356,
    "notes": "更新激活数限制"
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
    "max_activations": ["确保这个值大于或者等于 1。"]
  }
}
```

---

## 5. PATCH /api/v1/licenses/admin/licenses/{id}/

**部分更新许可证**

部分更新指定许可证的信息，只需要提供要更新的字段。

### 请求参数

#### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证ID | `1` |

#### Request Body (JSON)

可以只包含需要更新的字段，字段规则与创建许可证时相同。

⚠️ **产品-方案一致性验证**: 部分更新时，如果同时更新 `product` 和 `plan` 字段，系统会验证它们的一致性。

### 请求示例

```bash
# 只更新最大激活数和备注
curl -X PATCH "http://localhost:8000/api/v1/licenses/admin/licenses/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "max_activations": 8,
    "notes": "更新激活数限制"
  }'

# 只更新状态
curl -X PATCH "http://localhost:8000/api/v1/licenses/admin/licenses/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "status": "suspended"
  }'
```

### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "message": "许可证更新成功",
  "data": {
    "id": 1,
    "product": 1,
    "product_name": "SuperApp Pro",
    "plan": 2,
    "plan_name": "专业版",
    "tenant": 3,
    "tenant_name": "科技有限公司",
    "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
    "customer_name": "张三",
    "customer_email": "zhangsan@example.com",
    "max_activations": 8,
    "current_activations": 2,
    "issued_at": "2024-09-01T10:00:00Z",
    "expires_at": "2025-09-01T10:00:00Z",
    "last_verified_at": "2024-09-10T08:30:00Z",
    "status": "activated",
    "machine_bindings_count": 2,
    "days_until_expiry": 356,
    "notes": "更新激活数限制"
  }
}
```

---

## 6. DELETE /api/v1/licenses/admin/licenses/{id}/

**删除许可证**

软删除指定的许可证。注意：这是软删除操作，数据不会真正从数据库中删除，只是标记为已删除状态。

⚠️ **重要提醒**: 删除许可证会影响所有使用该许可证的激活设备，请谨慎操作。

### 请求参数

#### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证ID | `1` |

### 请求示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/licenses/admin/licenses/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 响应格式

**成功响应 (204 No Content)**

```http
HTTP/1.1 204 No Content
Content-Length: 0
```

**错误响应示例**

```json
// 许可证不存在 (404 Not Found)
{
  "success": false,
  "code": "4004",
  "message": "资源不存在",
  "data": null
}

// 许可证仍有活跃激活时的错误 (400 Bad Request)
{
  "success": false,
  "code": "4000",
  "message": "无法删除该许可证，还有2个活跃的设备正在使用",
  "data": null
}
```

---

## 7. POST /api/v1/licenses/admin/licenses/{id}/extend/

**延长许可证有效期**

延长指定许可证的有效期，可以指定延长的天数。

### 请求参数

#### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证ID | `1` |

#### Request Body (JSON)

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `days` | integer | 是 | 延长天数(>0) | `90` |

### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/1/extend/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "days": 90
  }'
```

### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "message": "许可证有效期已延长90天",
  "new_expiry": "2025-12-10T14:30:00Z"
}
```

**错误响应示例**

```json
// 参数验证错误 (400 Bad Request)
{
  "success": false,
  "error": "延长天数必须大于0"
}

// 许可证不存在 (404 Not Found)
{
  "success": false,
  "code": "4004",
  "message": "资源不存在",
  "data": null
}
```

---

## 8. POST /api/v1/licenses/admin/licenses/{id}/revoke/

**撤销许可证**

撤销指定的许可证并记录撤销原因。撤销后的许可证将无法再被激活或使用。

### 请求参数

#### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证ID | `1` |

#### Request Body (JSON)

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `reason` | string | 否 | 撤销原因(最大500字符) | `"客户申请退款"` |

### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/1/revoke/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "客户申请退款"
  }'
```

### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "message": "许可证撤销成功"
}
```

**错误响应示例**

```json
// 许可证已经是撤销状态 (400 Bad Request)
{
  "success": false,
  "error": "许可证已经是撤销状态，无法重复撤销"
}

// 许可证不存在 (404 Not Found)
{
  "success": false,
  "code": "4004",
  "message": "资源不存在",
  "data": null
}
```

---

## 9. GET /api/v1/licenses/admin/licenses/{id}/usage_stats/

**获取许可证使用统计**

获取指定许可证的详细使用统计信息，包括激活情况、机器使用情况和使用趋势。

### 请求参数

#### Path Parameters

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `id` | integer | 是 | 许可证ID | `1` |

### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/1/usage_stats/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"
```

### 响应格式

**成功响应 (200 OK)**

```json
{
  "license_id": 1,
  "status": "activated",
  "created_at": "2024-09-01T10:00:00Z",
  "expires_at": "2025-09-01T10:00:00Z",
  "machine_bindings": {
    "total": 2,
    "active": 2,
    "max_allowed": 5
  },
  "activations": {
    "total_attempts": 3,
    "successful": 2,
    "last_activation": "2024-09-02T09:15:00Z"
  },
  "usage": {
    "recent_events": 89,
    "last_verified": "2024-09-10T08:30:00Z"
  }
}
```

**错误响应示例**

```json
// 许可证不存在 (404 Not Found)
{
  "error": "License not found"
}

// 服务器内部错误 (500 Internal Server Error)
{
  "error": "统计数据获取失败"
}
```

---

## 10. POST /api/v1/licenses/admin/licenses/batch_operation/

**批量操作许可证**

对多个许可证执行批量操作，支持批量撤销、延期等操作。

### 请求参数

#### Request Body (JSON)

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|-------|------|------|------|-------|
| `license_ids` | array | 是 | 许可证ID列表(1-100个) | `[1, 2, 3, 4, 5]` |
| `operation` | string | 是 | 操作类型 | `"revoke"` |
| `parameters` | object | 否 | 操作参数 | `{"days": 30}` |
| `reason` | string | 否 | 操作原因(最大500字符) | `"批量清理过期许可证"` |

#### 支持的操作类型 (operation)
- `revoke`: 撤销许可证
- `suspend`: 挂起许可证  
- `activate`: 激活许可证
- `extend`: 延长有效期（需要在parameters中指定days）

#### parameters 参数说明
- 对于 `extend` 操作：`{"days": 30}` - 延长天数
- 对于其他操作：通常为空对象 `{}`

### 请求示例

#### 批量撤销示例
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "license_ids": [1, 2, 3, 4, 5],
    "operation": "revoke",
    "reason": "批量清理过期许可证"
  }'
```

#### 批量延期示例
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "license_ids": [10, 11, 12],
    "operation": "extend",
    "parameters": {
      "days": 30
    },
    "reason": "VIP客户服务延期"
  }'
```

### 响应格式

**成功响应 (200 OK)**

```json
{
  "success": true,
  "message": "批量操作完成，成功: 4/5",
  "results": [
    {
      "license_id": 1,
      "success": true,
      "message": "撤销成功"
    },
    {
      "license_id": 2,
      "success": true,
      "message": "撤销成功"
    },
    {
      "license_id": 3,
      "success": false,
      "error": "许可证已经是撤销状态"
    },
    {
      "license_id": 4,
      "success": true,
      "message": "撤销成功"
    },
    {
      "license_id": 5,
      "success": true,
      "message": "撤销成功"
    }
  ]
}
```

**错误响应示例**

```json
// 参数验证错误 (400 Bad Request)
{
  "success": false,
  "errors": {
    "license_ids": ["以下许可证ID不存在: [999, 1000]"],
    "operation": ["请选择一个有效的操作。"]
  }
}

// 批量操作部分失败
{
  "success": true,
  "message": "批量操作完成，成功: 2/3",
  "results": [
    {
      "license_id": 10,
      "success": true,
      "message": "延长30天成功"
    },
    {
      "license_id": 11,
      "success": true,
      "message": "延长30天成功"
    },
    {
      "license_id": 12,
      "success": false,
      "error": "许可证已过期，无法延期"
    }
  ]
}
```

---

## 📊 相关API端点

### 软件产品管理
- `GET /api/v1/licenses/admin/products/` - 获取产品列表
- `POST /api/v1/licenses/admin/products/` - 创建产品
- `GET /api/v1/licenses/admin/products/{id}/` - 获取产品详情
- `POST /api/v1/licenses/admin/products/{id}/regenerate_keypair/` - 重新生成密钥对
- `GET /api/v1/licenses/admin/products/{id}/statistics/` - 获取产品统计

### 许可方案管理  
- `GET /api/v1/licenses/admin/plans/` - 获取方案列表
- `POST /api/v1/licenses/admin/plans/` - 创建方案
- `POST /api/v1/licenses/admin/plans/{id}/duplicate/` - 复制方案

### 机器绑定管理
- `GET /api/v1/licenses/admin/machine-bindings/` - 获取机器绑定列表
- `GET /api/v1/licenses/admin/machine-bindings/{id}/` - 获取绑定详情
- `POST /api/v1/licenses/admin/machine-bindings/{id}/block/` - 阻止机器绑定

### 激活记录管理
- `GET /api/v1/licenses/admin/activations/` - 获取激活记录
- `GET /api/v1/licenses/admin/activations/{id}/` - 获取激活详情

### 安全审计日志
- `GET /api/v1/licenses/admin/audit-logs/` - 获取审计日志
- `GET /api/v1/licenses/admin/audit-logs/{id}/` - 获取日志详情

### 租户配额管理
- `GET /api/v1/licenses/admin/quotas/` - 获取配额列表
- `POST /api/v1/licenses/admin/quotas/` - 创建配额

---

## ❌ 错误处理

### 标准错误响应格式
```json
{
  "success": false,
  "code": 4001,
  "message": "未提供租户ID，无法访问CMS资源",
  "errors": {
    "field_name": ["具体错误信息"]
  }
}
```

### 常见错误码
| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 401 | 401 | 未认证或Token过期 |
| 403 | 403 | 权限不足 |
| 404 | 404 | 资源不存在 |
| 4001 | 400 | 租户ID缺失 |
| 4002 | 400 | 租户不存在 |
| 4003 | 403 | 租户访问权限不足 |
| 500 | 500 | 服务器内部错误 |

### 常见错误场景

#### 1. 认证失败
```json
{
  "success": false,
  "detail": "Invalid token header. Token string should not contain spaces."
}
```

#### 2. 权限不足
```json
{
  "success": false,
  "detail": "You do not have permission to perform this action."
}
```

#### 3. 参数验证失败
```json
{
  "success": false,
  "errors": {
    "customer_info": ["客户信息缺少必要字段: email"],
    "max_activations": ["确保该值大于或等于1。"]
  }
}
```

#### 4. 业务逻辑错误
```json
{
  "success": false,
  "error": "许可证已经是撤销状态，无法重复撤销"
}
```

---

## 📚 最佳实践

### 1. 认证Token管理
- Token有效期为30天，建议在过期前刷新
- 使用HTTPS传输保护Token安全
- 客户端应实现Token自动刷新机制

### 2. 分页处理建议
```javascript
// 前端分页处理示例
async function getAllLicenses() {
  let allLicenses = [];
  let page = 1;
  let hasMore = true;
  
  while (hasMore) {
    const response = await fetch(`/api/v1/licenses/admin/licenses/?page=${page}`);
    const data = await response.json();
    
    allLicenses = allLicenses.concat(data.data.results);
    hasMore = data.data.next !== null;
    page++;
  }
  
  return allLicenses;
}
```

### 3. 错误重试策略
```javascript
// 带重试的API调用示例
async function apiCallWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.status === 429) { // 限流
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        continue;
      }
      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

### 4. 批量操作最佳实践
- 单次批量操作建议不超过100条记录
- 大量数据处理时采用分批处理
- 监控批量操作的成功率并做好错误处理

### 5. 许可证状态管理
- 创建后的许可证状态为 `generated`
- 首次激活后状态变为 `activated`
- 定期检查过期许可证并更新状态
- 撤销后的许可证无法恢复，请谨慎操作

### 6. 产品-方案选择策略
- **推荐做法**: 只提供 `plan` 参数，让系统自动设置 `product`
- **前端实现**: 实现级联选择，先选产品再选方案
- **数据验证**: 始终验证产品和方案的匹配关系
- **错误处理**: 为不匹配情况提供清晰的错误提示

### 7. 租户隔离
- 多租户环境下，确保只访问授权租户的数据
- 超级管理员操作时需要明确指定租户ID
- 定期审计跨租户访问行为

---

## 🔄 版本更新

### 当前版本: v1.0

### 更新记录
- **2024-09-11**: 添加产品-方案一致性验证功能
  - 新增自动验证product和plan的匹配关系
  - 支持只提供plan参数，自动设置product
  - 增加详细的验证错误提示和处理建议
- **2024-09-10**: 创建初始版本文档
- **功能特性**: 完整的CRUD操作、批量操作、使用统计等

### 向后兼容性
- API接口保持向后兼容
- 新增字段采用可选参数
- 废弃功能会提前至少一个版本通知

---

## 📞 技术支持

如果您在使用过程中遇到问题，请联系技术支持团队：

- **邮箱**: tech-support@lipeaks.com
- **文档**: https://docs.lipeaks.com/licenses
- **API状态**: https://status.lipeaks.com

---

*本文档最后更新时间：2024年9月11日*
