# 客户-租户关系API

本文档详细说明了客户-租户关系API的使用方法、请求参数和响应格式。客户-租户关系API用于管理客户与租户（Tenant）之间的关系。

## 基础路径

所有客户-租户关系API的基础路径为：`/api/v1/customers/tenants/relations/`

## 认证与权限

- **认证方式**：JWT令牌认证，在请求头中添加 `Authorization: Bearer <your_jwt_token>`
- **权限要求**：需要管理员权限 (`IsAdmin`)

## API列表

### 1. 获取客户的租户关系列表

获取客户与租户之间的关系列表，支持分页、排序和筛选。

- **URL**: `/api/v1/customers/tenants/relations/`
- **方法**: `GET`
- **URL参数**:
  - `page`: 页码，默认为1
  - `page_size`: 每页记录数，默认为10
  - `ordering`: 排序字段，例如 `created_at` 或 `-created_at`（降序）
  - `customer_id`: 按客户ID筛选
  - `tenant_id`: 按租户ID筛选
  - `is_primary`: 按是否为主要租户关系筛选（true/false）
  - `relation_type`: 按关系类型筛选

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "pagination": {
        "count": 3,
        "next": null,
        "previous": null,
        "page_size": 10,
        "current_page": 1,
        "total_pages": 1
      },
      "results": [
        {
          "id": 1,
          "customer": {
            "id": 1,
            "name": "上海普全公司"
          },
          "tenant": {
            "id": 1,
            "name": "租户A",
            "code": "tenant_a"
          },
          "relation_type": "service_provider",
          "is_primary": true,
          "start_date": "2025-01-01",
          "end_date": "2025-12-31",
          "status": "active",
          "notes": "主要服务提供商",
          "created_at": "2025-07-03T10:00:00.000000Z"
        },
        {
          "id": 2,
          "customer": {
            "id": 1,
            "name": "上海普全公司"
          },
          "tenant": {
            "id": 2,
            "name": "租户B",
            "code": "tenant_b"
          },
          "relation_type": "partner",
          "is_primary": false,
          "start_date": "2025-01-01",
          "end_date": "2025-12-31",
          "status": "active",
          "notes": "合作伙伴",
          "created_at": "2025-07-03T10:05:00.000000Z"
        }
        // 更多关系记录...
      ]
    }
  }
  ```

### 2. 添加客户与租户的关系

创建客户与租户之间的新关系。

- **URL**: `/api/v1/customers/tenants/relations/`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "customer_id": 1,
    "tenant_id": 3,
    "relation_type": "client",
    "is_primary": false,
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "status": "active",
    "notes": "客户关系"
  }
  ```

- **成功响应**:
  - 状态码: `201 Created`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 3,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "tenant": {
        "id": 3,
        "name": "租户C",
        "code": "tenant_c"
      },
      "relation_type": "client",
      "is_primary": false,
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "status": "active",
      "notes": "客户关系",
      "created_at": "2025-07-05T05:40:00.000000Z",
      "updated_at": "2025-07-05T05:40:00.000000Z",
      "created_by": "admin",
      "updated_by": null
    }
  }
  ```

- **错误响应**:
  - 状态码: `400 Bad Request`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "errors": {
      "customer_id": ["客户不存在"],
      "tenant_id": ["租户不存在"],
      "relation_type": ["此字段为必填项"]
    }
  }
  ```

  - 状态码: `409 Conflict`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4090,
    "message": "关系已存在",
    "errors": {
      "non_field_errors": ["该客户与租户的关系已存在"]
    }
  }
  ```

### 3. 获取特定客户-租户关系详情

获取指定ID的客户-租户关系详情。

- **URL**: `/api/v1/customers/tenants/relations/{id}/`
- **方法**: `GET`
- **URL参数**:
  - `id`: 关系ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 1,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "tenant": {
        "id": 1,
        "name": "租户A",
        "code": "tenant_a"
      },
      "relation_type": "service_provider",
      "is_primary": true,
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "status": "active",
      "notes": "主要服务提供商",
      "created_at": "2025-07-03T10:00:00.000000Z",
      "updated_at": "2025-07-03T10:00:00.000000Z",
      "created_by": "admin",
      "updated_by": null
    }
  }
  ```

- **错误响应**:
  - 状态码: `404 Not Found`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "关系不存在"
  }
  ```

### 4. 更新客户-租户关系

更新指定ID的客户-租户关系。

- **URL**: `/api/v1/customers/tenants/relations/{id}/`
- **方法**: `PUT`
- **URL参数**:
  - `id`: 关系ID
- **请求体**:
  ```json
  {
    "relation_type": "strategic_partner",
    "is_primary": true,
    "start_date": "2025-01-01",
    "end_date": "2026-12-31",
    "status": "active",
    "notes": "战略合作伙伴"
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 1,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "tenant": {
        "id": 1,
        "name": "租户A",
        "code": "tenant_a"
      },
      "relation_type": "strategic_partner",
      "is_primary": true,
      "start_date": "2025-01-01",
      "end_date": "2026-12-31",
      "status": "active",
      "notes": "战略合作伙伴",
      "created_at": "2025-07-03T10:00:00.000000Z",
      "updated_at": "2025-07-05T05:45:00.000000Z",
      "created_by": "admin",
      "updated_by": "admin"
    }
  }
  ```

- **错误响应**:
  - 状态码: `400 Bad Request` 或 `404 Not Found`
  - 响应体: 与创建关系或获取关系详情的错误响应相同

### 5. 删除客户-租户关系

删除指定ID的客户-租户关系。

- **URL**: `/api/v1/customers/tenants/relations/{id}/`
- **方法**: `DELETE`
- **URL参数**:
  - `id`: 关系ID

- **成功响应**:
  - 状态码: `204 No Content`
  - 响应体: 无

- **错误响应**:
  - 状态码: `404 Not Found`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "关系不存在"
  }
  ```

  - 状态码: `400 Bad Request`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4000,
    "message": "无法删除主要租户关系",
    "errors": {
      "non_field_errors": ["无法删除主要租户关系，请先设置其他租户为主要租户"]
    }
  }
  ```

### 6. 设置主要租户关系

将指定ID的客户-租户关系设置为主要租户关系。

- **URL**: `/api/v1/customers/tenants/relations/{id}/set-primary/`
- **方法**: `POST`
- **URL参数**:
  - `id`: 关系ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 2,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "tenant": {
        "id": 2,
        "name": "租户B",
        "code": "tenant_b"
      },
      "relation_type": "partner",
      "is_primary": true,
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "status": "active",
      "notes": "合作伙伴",
      "created_at": "2025-07-03T10:05:00.000000Z",
      "updated_at": "2025-07-05T05:50:00.000000Z",
      "created_by": "admin",
      "updated_by": "admin"
    }
  }
  ```

- **错误响应**:
  - 状态码: `404 Not Found`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "关系不存在"
  }
  ```

### 7. 获取客户的主要租户关系

获取指定客户的主要租户关系。

- **URL**: `/api/v1/customers/tenants/relations/primary/`
- **方法**: `GET`
- **URL参数**:
  - `customer_id`: 客户ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 2,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "tenant": {
        "id": 2,
        "name": "租户B",
        "code": "tenant_b"
      },
      "relation_type": "partner",
      "is_primary": true,
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "status": "active",
      "notes": "合作伙伴",
      "created_at": "2025-07-03T10:05:00.000000Z",
      "updated_at": "2025-07-05T05:50:00.000000Z",
      "created_by": "admin",
      "updated_by": "admin"
    }
  }
  ```

- **错误响应**:
  - 状态码: `404 Not Found`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "未找到主要租户关系"
  }
  ```

  - 状态码: `400 Bad Request`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "errors": {
      "customer_id": ["此字段为必填项"]
    }
  }
  ```

### 8. 获取客户与租户之间的关系

获取指定客户与租户之间的关系。

- **URL**: `/api/v1/customers/tenants/relations/between/`
- **方法**: `GET`
- **URL参数**:
  - `customer_id`: 客户ID
  - `tenant_id`: 租户ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 1,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "tenant": {
        "id": 1,
        "name": "租户A",
        "code": "tenant_a"
      },
      "relation_type": "strategic_partner",
      "is_primary": true,
      "start_date": "2025-01-01",
      "end_date": "2026-12-31",
      "status": "active",
      "notes": "战略合作伙伴",
      "created_at": "2025-07-03T10:00:00.000000Z",
      "updated_at": "2025-07-05T05:45:00.000000Z",
      "created_by": "admin",
      "updated_by": "admin"
    }
  }
  ```

- **错误响应**:
  - 状态码: `404 Not Found`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "未找到客户与租户的关系"
  }
  ```

  - 状态码: `400 Bad Request`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "errors": {
      "customer_id": ["此字段为必填项"],
      "tenant_id": ["此字段为必填项"]
    }
  }
  ```

## 字段说明

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| customer_id | 整数 | 是 | 客户ID |
| tenant_id | 整数 | 是 | 租户ID |
| relation_type | 字符串 | 是 | 关系类型，如 service_provider（服务提供商）、partner（合作伙伴）、client（客户）等 |
| is_primary | 布尔值 | 否 | 是否为主要租户关系，默认为 false |
| start_date | 日期 | 否 | 关系开始日期 |
| end_date | 日期 | 否 | 关系结束日期 |
| status | 字符串 | 是 | 关系状态，如 active（活跃）、inactive（非活跃）、terminated（终止） |
| notes | 字符串 | 否 | 备注 |
| created_at | 日期时间 | 否 | 创建时间，自动生成 |
| updated_at | 日期时间 | 否 | 更新时间，自动生成 |
| created_by | 字符串 | 否 | 创建者，自动填充当前用户 |
| updated_by | 字符串 | 否 | 更新者，自动填充当前用户 |

## 注意事项

1. **主要租户关系**：每个客户只能有一个主要租户关系。当设置一个租户为主要租户时，系统会自动将该客户的其他租户关系设置为非主要租户关系。

2. **删除限制**：无法直接删除主要租户关系。如果需要删除主要租户关系，请先将其他租户设置为主要租户，或者将该关系的 `is_primary` 设置为 `false`。

3. **关系类型枚举值**：关系类型（`relation_type`）字段支持以下枚举值：
   - `service_provider`：服务提供商
   - `partner`：合作伙伴
   - `client`：客户
   - `supplier`：供应商
   - `strategic_partner`：战略合作伙伴
   - `other`：其他

4. **关系状态枚举值**：关系状态（`status`）字段支持以下枚举值：
   - `active`：活跃
   - `inactive`：非活跃
   - `terminated`：终止
   - `suspended`：暂停
   - `expired`：已过期 