# 客户批量操作API

本文档详细说明了客户批量操作API的使用方法、请求参数和响应格式。

## 基础路径

所有客户批量操作API的基础路径为：`/api/v1/customers/`

## 认证与权限

- **认证方式**：JWT令牌认证，在请求头中添加 `Authorization: Bearer <your_jwt_token>`
- **权限要求**：需要管理员权限 (`IsAdmin`)

## API列表

### 1. 批量创建客户

一次性创建多个客户记录。

- **URL**: `/api/v1/customers/bulk-create/`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "customers": [
      {
        "name": "客户A",
        "type": "company",
        "value_level": "vip",
        "status": "active",
        "business_license_number": "91110000123456789X",
        "industry_type": "信息技术",
        "company_size": "medium",
        "primary_contact_name": "张三",
        "primary_contact_phone": "13800138000"
      },
      {
        "name": "客户B",
        "type": "company",
        "value_level": "normal",
        "status": "active",
        "business_license_number": "91110000123456788X",
        "industry_type": "制造业",
        "company_size": "large",
        "primary_contact_name": "李四",
        "primary_contact_phone": "13900139000"
      }
    ]
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
      "created_count": 2,
      "failed_count": 0,
      "created_customers": [
        {
          "id": 9,
          "name": "客户A",
          "type": "company",
          "value_level": "vip",
          "status": "active",
          "business_license_number": "91110000123456789X",
          "industry_type": "信息技术",
          "company_size": "medium",
          "primary_contact_name": "张三",
          "primary_contact_phone": "13800138000",
          "created_at": "2025-07-05T05:10:42.362927Z"
        },
        {
          "id": 10,
          "name": "客户B",
          "type": "company",
          "value_level": "normal",
          "status": "active",
          "business_license_number": "91110000123456788X",
          "industry_type": "制造业",
          "company_size": "large",
          "primary_contact_name": "李四",
          "primary_contact_phone": "13900139000",
          "created_at": "2025-07-05T05:10:42.362927Z"
        }
      ],
      "failed_customers": []
    }
  }
  ```

- **部分成功响应**:
  - 状态码: `207 Multi-Status`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2070,
    "message": "部分操作成功",
    "data": {
      "created_count": 1,
      "failed_count": 1,
      "created_customers": [
        {
          "id": 9,
          "name": "客户A",
          "type": "company",
          "value_level": "vip",
          "status": "active",
          "business_license_number": "91110000123456789X",
          "industry_type": "信息技术",
          "company_size": "medium",
          "primary_contact_name": "张三",
          "primary_contact_phone": "13800138000",
          "created_at": "2025-07-05T05:10:42.362927Z"
        }
      ],
      "failed_customers": [
        {
          "data": {
            "name": "客户B",
            "type": "company",
            "value_level": "normal",
            "status": "active",
            "business_license_number": "91110000123456788X",
            "industry_type": "制造业",
            "company_size": "large",
            "primary_contact_name": "李四",
            "primary_contact_phone": "13900139000"
          },
          "errors": {
            "name": ["客户名称已存在"]
          }
        }
      ]
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
      "customers": ["必须提供至少一个客户"]
    }
  }
  ```

### 2. 批量更新客户

一次性更新多个客户记录。

- **URL**: `/api/v1/customers/bulk-update/`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "customers": [
      {
        "id": 1,
        "status": "inactive",
        "notes": "已暂停合作"
      },
      {
        "id": 2,
        "value_level": "vip",
        "notes": "已升级为VIP客户"
      }
    ]
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
      "updated_count": 2,
      "failed_count": 0,
      "updated_customers": [
        {
          "id": 1,
          "name": "上海普全公司",
          "status": "inactive",
          "notes": "已暂停合作",
          "updated_at": "2025-07-05T05:15:42.362927Z"
        },
        {
          "id": 2,
          "name": "hello1",
          "value_level": "vip",
          "notes": "已升级为VIP客户",
          "updated_at": "2025-07-05T05:15:42.362927Z"
        }
      ],
      "failed_customers": []
    }
  }
  ```

- **部分成功响应**:
  - 状态码: `207 Multi-Status`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2070,
    "message": "部分操作成功",
    "data": {
      "updated_count": 1,
      "failed_count": 1,
      "updated_customers": [
        {
          "id": 1,
          "name": "上海普全公司",
          "status": "inactive",
          "notes": "已暂停合作",
          "updated_at": "2025-07-05T05:15:42.362927Z"
        }
      ],
      "failed_customers": [
        {
          "data": {
            "id": 2,
            "value_level": "vip",
            "notes": "已升级为VIP客户"
          },
          "errors": {
            "id": ["客户不存在或已被删除"]
          }
        }
      ]
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
      "customers": ["必须提供至少一个客户"],
      "id": ["每个客户记录必须包含ID"]
    }
  }
  ```

### 3. 批量删除客户

一次性删除多个客户记录（软删除）。

- **URL**: `/api/v1/customers/bulk-delete/`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "ids": [1, 2, 3]
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
      "deleted_count": 3,
      "failed_count": 0,
      "deleted_ids": [1, 2, 3],
      "failed_ids": []
    }
  }
  ```

- **部分成功响应**:
  - 状态码: `207 Multi-Status`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2070,
    "message": "部分操作成功",
    "data": {
      "deleted_count": 2,
      "failed_count": 1,
      "deleted_ids": [1, 2],
      "failed_ids": [
        {
          "id": 3,
          "error": "客户不存在或已被删除"
        }
      ]
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
      "ids": ["必须提供至少一个客户ID"]
    }
  }
  ```

## 批量操作注意事项

1. **事务处理**：批量操作API使用数据库事务来确保操作的一致性。如果在处理过程中发生错误，系统会尝试回滚已完成的操作。

2. **部分成功处理**：批量操作API支持部分成功处理，即使某些记录处理失败，其他记录仍然可以成功处理。在这种情况下，API会返回`207 Multi-Status`状态码，并在响应中详细说明哪些记录处理成功，哪些处理失败以及失败原因。

3. **性能考虑**：为了避免服务器过载，批量操作API对每次请求的记录数量有限制。建议每次请求不超过100条记录。

4. **并发控制**：在高并发环境下，批量操作API可能会受到数据库锁的影响。如果遇到锁超时或死锁问题，请尝试减少每次批量操作的记录数量或者调整操作的时间间隔。

5. **唯一性约束**：在批量创建和更新操作中，系统会检查客户名称的唯一性。如果发现重复的客户名称，相应的记录将会处理失败，但不会影响其他记录的处理。 