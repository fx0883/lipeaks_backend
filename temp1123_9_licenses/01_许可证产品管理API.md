# 许可证产品管理API文档

## 概述

产品管理API用于管理软件产品（Application），每个产品可以有多个许可证方案和许可证。

## API列表

### 1. 获取产品列表

**接口**: `GET /api/v1/licenses/admin/products/`

**权限**: 租户管理员

**描述**: 获取current租户下所有产品的分页列表

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认10 |
| search | string | 否 | 搜索关键词（名称、代码、描述） |
| status | string | 否 | 状态筛选：development/testing/active/maintenance/deprecated/archived |
| ordering | string | 否 | 排序字段：name/-name/created_at/-created_at/updated_at/-updated_at |

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/products/?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 7,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 1,
        "name": "测试应用",
        "code": "test-app",
        "description": "这是一个测试应用",
        "current_version": "1.0.0",
        "max_activations": 5,
        "offline_days": 30,
        "status": "active",
        "license_plans_count": 0,
        "total_licenses": 0,
        "created_at": "2025-11-21T14:31:49.522138Z",
        "updated_at": "2025-11-23T13:26:20.830823Z"
      }
    ]
  }
}
```

---

### 2. 获取产品详情

**接口**: `GET /api/v1/licenses/admin/products/{id}/`

**权限**: 租户管理员

**描述**: 获取指定产品的详细信息

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | int | 是 | 产品ID |

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/products/1/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "测试应用",
    "code": "test-app",
    "description": "这是一个测试应用",
    "current_version": "1.0.0",
    "max_activations": 5,
    "offline_days": 30,
    "status": "active",
    "license_plans_count": 0,
    "total_licenses": 0,
    "created_at": "2025-11-21T14:31:49.522138Z",
    "updated_at": "2025-11-23T13:26:20.830823Z"
  }
}
```

---

### 3. 创建产品

**接口**: `POST /api/v1/licenses/admin/products/`

**权限**: 租户管理员

**描述**: 创建新的软件产品

**请求体**:
```json
{
  "name": "新产品",
  "code": "new-product",
  "description": "产品描述",
  "current_version": "1.0.0",
  "max_activations": 5,
  "offline_days": 30,
  "generate_keypair": true,
  "status": "development"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 产品名称 |
| code | string | 是 | 产品代码（租户内唯一） |
| description | string | 否 | 产品描述 |
| current_version | string | 否 | current版本号，默认"1.0.0" |
| max_activations | int | 否 | 默认最大激活数，默认5 |
| offline_days | int | 否 | 离线天数，默认30 |
| generate_keypair | bool | 否 | 是否生成RSA密钥对，默认true |
| status | string | 否 | 状态，默认"development" |

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/products/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新产品",
    "code": "new-product",
    "description": "这是一个新产品",
    "current_version": "1.0.0",
    "max_activations": 10,
    "offline_days": 60,
    "generate_keypair": true,
    "status": "development"
  }'
```

**成功响应** (201 Created):
```json
{
  "success": true,
  "code": 2001,
  "message": "创建成功",
  "data": {
    "id": 8,
    "name": "新产品",
    "code": "new-product",
    "description": "这是一个新产品",
    "current_version": "1.0.0",
    "max_activations": 10,
    "offline_days": 60,
    "status": "development",
    "license_plans_count": 0,
    "total_licenses": 0,
    "created_at": "2025-11-23T14:20:00.000000Z",
    "updated_at": "2025-11-23T14:20:00.000000Z"
  }
}
```

---

### 4. 更新产品

**接口**: `PUT /api/v1/licenses/admin/products/{id}/`

**权限**: 租户管理员

**描述**: 完整更新产品信息（需要提供所有字段）

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | int | 是 | 产品ID |

**请求体**: 与创建产品相同

**curl示例**:
```bash
curl -X PUT "http://localhost:8000/api/v1/licenses/admin/products/1/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新后的产品",
    "code": "test-app",
    "description": "更新后的描述",
    "current_version": "2.0.0",
    "status": "active"
  }'
```

---

### 5. 部分更新产品

**接口**: `PATCH /api/v1/licenses/admin/products/{id}/`

**权限**: 租户管理员

**描述**: 部分更新产品信息（只需提供要更新的字段）

**curl示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/licenses/admin/products/1/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_version": "2.1.0",
    "description": "只更新版本号和描述"
  }'
```

---

### 6. 删除产品

**接口**: `DELETE /api/v1/licenses/admin/products/{id}/`

**权限**: 租户管理员

**描述**: 软删除产品（设置is_deleted=true）

**curl示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/licenses/admin/products/1/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

**成功响应** (204 No Content):
```json
{
  "success": true,
  "code": 2004,
  "message": "删除成功",
  "data": null
}
```

---

### 7. 重新生成产品密钥对

**接口**: `POST /api/v1/licenses/admin/products/{id}/regenerate_keypair/`

**权限**: 租户管理员

**描述**: 为产品重新生成RSA密钥对（用于许可证签名）

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/products/1/regenerate_keypair/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "密钥对重新生成成功",
  "public_key_preview": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA..."
}
```

---

### 8. 获取产品统计信息

**接口**: `GET /api/v1/licenses/admin/products/{id}/statistics/`

**权限**: 租户管理员

**描述**: 获取指定产品的统计信息，包括许可证数量、激活情况、机器绑定等

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/products/1/statistics/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

**成功响应** (200 OK):
```json
{
  "product_id": 1,
  "product_name": "测试应用",
  "licenses": {
    "total": 100,
    "active": 80,
    "expired": 10,
    "revoked": 10
  },
  "activations": {
    "total_attempts": 500,
    "successful": 480,
    "failed": 20
  },
  "machine_bindings": {
    "total_machines": 300,
    "active_machines": 250
  },
  "generated_at": "2025-11-23T14:30:00.000000Z"
}
```

## 错误响应

### 400 Bad Request - 请求参数错误
```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "code": ["Application code already exists"]
  }
}
```

### 401 Unauthorized - 未认证
```json
{
  "success": false,
  "code": 4001,
  "message": "未认证或认证失败",
  "data": null
}
```

### 403 Forbidden - 权限不足
```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": null
}
```

### 404 Not Found - 资源不存在
```json
{
  "success": false,
  "code": 4004,
  "message": "资源不存在",
  "data": null
}
```

### 500 Internal Server Error - 服务器内部错误
```json
{
  "success": false,
  "code": 5000,
  "message": "服务器内部错误",
  "data": null,
  "error_code": "INTERNAL_SERVER_ERROR"
}
```

## 注意事项

1. **权限要求**: 所有API都需要租户管理员权限
2. **租户隔离**: 自动根据token中的租户ID过滤数据，无需手动传递tenant_id
3. **代码唯一性**: 产品代码（code）在同一租户内必须唯一
4. **密钥对管理**: 创建产品时可自动生成RSA密钥对，用于许可证签名和验证
5. **软删除**: 删除操作是软删除，数据不会真正删除，只是标记为已删除
