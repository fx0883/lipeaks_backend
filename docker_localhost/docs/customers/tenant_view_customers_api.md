# 租户视角的客户API

本文档详细说明了租户视角的客户API的使用方法、请求参数和响应格式。租户视角的客户API用于从租户的角度查看和管理与其相关的客户。

## 基础路径

所有租户视角的客户API的基础路径为：`/api/v1/customers/tenants/view/`

## 认证与权限

- **认证方式**：JWT令牌认证，在请求头中添加 `Authorization: Bearer <your_jwt_token>`
- **权限要求**：需要租户管理员权限 (`IsTenantAdmin`)

## API列表

### 1. 获取租户关联的客户列表

获取当前租户关联的所有客户列表，支持分页、排序和筛选。

- **URL**: `/api/v1/customers/tenants/view/`
- **方法**: `GET`
- **URL参数**:
  - `page`: 页码，默认为1
  - `page_size`: 每页记录数，默认为10
  - `ordering`: 排序字段，例如 `name` 或 `-created_at`（降序）
  - `type`: 按客户类型筛选
  - `value_level`: 按客户价值等级筛选
  - `status`: 按客户状态筛选
  - `relation_type`: 按关系类型筛选
  - `relation_status`: 按关系状态筛选

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
          "name": "上海普全公司",
          "type": "company",
          "value_level": "vip",
          "status": "active",
          "primary_contact_name": "张三",
          "primary_contact_phone": "13800138000",
          "industry_type": "信息技术",
          "company_size": "medium",
          "relation": {
            "id": 1,
            "relation_type": "service_provider",
            "is_primary": true,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "status": "active",
            "notes": "主要服务提供商",
            "created_at": "2025-07-03T10:00:00.000000Z"
          },
          "created_at": "2025-07-03T09:51:20.456142Z"
        },
        {
          "id": 2,
          "name": "北京科技有限公司",
          "type": "company",
          "value_level": "normal",
          "status": "active",
          "primary_contact_name": "李四",
          "primary_contact_phone": "13900139000",
          "industry_type": "制造业",
          "company_size": "large",
          "relation": {
            "id": 2,
            "relation_type": "client",
            "is_primary": false,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "status": "active",
            "notes": "客户",
            "created_at": "2025-07-03T10:05:00.000000Z"
          },
          "created_at": "2025-07-03T10:00:00.000000Z"
        }
        // 更多客户记录...
      ]
    }
  }
  ```

### 2. 获取租户视角下的客户详情

获取租户视角下指定客户的详细信息。

- **URL**: `/api/v1/customers/tenants/view/{id}/`
- **方法**: `GET`
- **URL参数**:
  - `id`: 客户ID

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
      "name": "上海普全公司",
      "type": "company",
      "value_level": "vip",
      "status": "active",
      "business_license_number": "91110000123456789X",
      "tax_identification_number": "91110000123456789X",
      "registered_capital": "1000万元",
      "legal_representative": "张三",
      "registered_address": "上海市浦东新区张江高科技园区",
      "business_address": "上海市浦东新区张江高科技园区",
      "business_scope": "软件开发、技术咨询、技术服务",
      "industry_type": "信息技术",
      "company_size": "medium",
      "establishment_date": "2010-01-01",
      "website": "http://www.example.com",
      "primary_contact_name": "张三",
      "primary_contact_phone": "13800138000",
      "primary_contact_email": "zhangsan@example.com",
      "bank_name": "中国银行",
      "bank_account": "6222020000123456789",
      "credit_rating": "A",
      "payment_terms": "月结30天",
      "special_requirements": "需要定期技术支持",
      "notes": "重要客户",
      "source": "展会",
      "relation": {
        "id": 1,
        "relation_type": "service_provider",
        "is_primary": true,
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "status": "active",
        "notes": "主要服务提供商",
        "created_at": "2025-07-03T10:00:00.000000Z",
        "updated_at": "2025-07-03T10:00:00.000000Z"
      },
      "created_at": "2025-07-03T09:51:20.456142Z",
      "updated_at": "2025-07-03T09:51:20.456152Z"
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
    "message": "客户不存在或与当前租户无关联"
  }
  ```

### 3. 获取租户的客户统计数据

获取当前租户关联的客户统计数据。

- **URL**: `/api/v1/customers/tenants/view/statistics/`
- **方法**: `GET`

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "total_count": 3,
      "active_count": 2,
      "inactive_count": 1,
      "by_type": {
        "company": 3
      },
      "by_value_level": {
        "normal": 1,
        "vip": 2
      },
      "by_relation_type": {
        "service_provider": 1,
        "client": 1,
        "partner": 1
      },
      "by_relation_status": {
        "active": 2,
        "inactive": 1
      }
    }
  }
  ```

### 4. 获取客户与租户的关系

获取指定客户与当前租户之间的关系。

- **URL**: `/api/v1/customers/tenants/view/{id}/relation/`
- **方法**: `GET`
- **URL参数**:
  - `id`: 客户ID

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
    "message": "未找到客户与当前租户的关系"
  }
  ```

### 5. 搜索租户关联的客户

根据关键词搜索租户关联的客户。

- **URL**: `/api/v1/customers/tenants/view/search/`
- **方法**: `GET`
- **URL参数**:
  - `q`: 搜索关键词
  - `page`: 页码，默认为1
  - `page_size`: 每页记录数，默认为10

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
        "count": 1,
        "next": null,
        "previous": null,
        "page_size": 10,
        "current_page": 1,
        "total_pages": 1
      },
      "results": [
        {
          "id": 1,
          "name": "上海普全公司",
          "type": "company",
          "value_level": "vip",
          "status": "active",
          "primary_contact_name": "张三",
          "primary_contact_phone": "13800138000",
          "industry_type": "信息技术",
          "company_size": "medium",
          "relation": {
            "id": 1,
            "relation_type": "service_provider",
            "is_primary": true,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "status": "active",
            "notes": "主要服务提供商",
            "created_at": "2025-07-03T10:00:00.000000Z"
          },
          "created_at": "2025-07-03T09:51:20.456142Z"
        }
      ]
    }
  }
  ```

## 租户视角的客户数据访问限制

1. **数据范围限制**：租户视角的客户API只能访问与当前租户有关联关系的客户数据。

2. **字段访问限制**：某些敏感字段可能会根据关系类型和状态进行限制访问。

3. **操作权限限制**：租户管理员只能查看客户数据，不能创建、更新或删除客户记录。如需修改客户信息，请联系系统管理员。

## 注意事项

1. **租户上下文**：租户视角的API会自动使用当前用户所属的租户作为上下文，无需显式指定租户ID。

2. **关系过滤**：可以通过 `relation_type` 和 `relation_status` 参数筛选特定类型或状态的客户关系。

3. **数据同步**：租户视角的客户数据与系统中的客户数据保持同步，但可能会有一定的延迟。

4. **缓存策略**：为了提高性能，租户视角的客户数据可能会被缓存，缓存时间通常为5分钟。 