# 客户基础操作API

本文档描述客户管理系统的基础操作API，包括客户的增删改查、搜索、统计和批量操作等功能。

## API端点

所有客户基础操作API的基础URL为：`/api/v1/customers/`

## 1. 获取客户列表

获取系统中的所有客户，支持分页、排序和筛选。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/`
- **权限**: 管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认为1 |
| limit | int | 否 | 每页记录数，默认为10 |
| status | string | 否 | 按状态筛选客户 (active, inactive, potential, lost) |
| type | string | 否 | 按类型筛选客户 (company, personal, government, nonprofit, education) |
| value_level | string | 否 | 按价值等级筛选客户 (platinum, gold, silver, bronze) |
| company_size | string | 否 | 按公司规模筛选客户 (micro, small, medium, large) |
| search | string | 否 | 搜索客户名称、联系人等信息 |
| ordering | string | 否 | 排序字段，如 name, -created_at (前缀-表示降序) |
| show_deleted | boolean | 否 | 是否显示已删除客户，默认false |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 10,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 16,
        "name": "阿斯顿法师打发是的法师打发",
        "type": "enterprise",
        "value_level": "silver",
        "status": "active",
        "primary_contact_name": null,
        "primary_contact_phone": null,
        "industry_type": null,
        "company_size": null,
        "created_at": "2025-07-05T12:02:11.968053Z"
      },
      // ... 更多客户记录
    ]
  }
}
```

## 2. 获取单个客户

获取指定ID的客户详情。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/{id}/`
- **权限**: 管理员

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 8,
    "name": "示例科技有限公司",
    "type": "company",
    "value_level": "vip",
    "status": "active",
    "business_license_number": "91110000123456789X",
    "tax_identification_number": "91110000123456789X",
    "registered_capital": "1000万元",
    "legal_representative": "张三",
    "registered_address": "北京市海淀区中关村南大街5号",
    "business_address": "北京市海淀区中关村南大街5号",
    "business_scope": "软件开发、技术咨询、技术服务",
    "industry_type": "信息技术",
    "company_size": "medium",
    "establishment_date": "2010-01-01",
    "website": "http://www.example.com",
    "primary_contact_name": "李四",
    "primary_contact_phone": "13800138000",
    "primary_contact_email": "contact@example.com",
    "bank_name": "中国银行",
    "bank_account": "6222020000123456789",
    "credit_rating": "A",
    "payment_terms": "月结30天",
    "special_requirements": "需要定期技术支持",
    "notes": "重要客户",
    "source": "展会",
    "is_deleted": false,
    "created_at": "2025-07-05T05:04:42.362927Z",
    "updated_at": "2025-07-05T05:04:42.362927Z",
    "created_by": "admin",
    "updated_by": null
  }
}
```

## 3. 创建客户

创建新的客户记录。

### 请求

- **方法**: `POST`
- **URL**: `/api/v1/customers/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 请求体

```json
{
  "name": "示例科技有限公司",
  "type": "company",
  "value_level": "vip",
  "status": "active",
  "business_license_number": "91110000123456789X",
  "tax_identification_number": "91110000123456789X",
  "registered_capital": "1000万元",
  "legal_representative": "张三",
  "registered_address": "北京市海淀区中关村南大街5号",
  "business_address": "北京市海淀区中关村南大街5号",
  "business_scope": "软件开发、技术咨询、技术服务",
  "industry_type": "信息技术",
  "company_size": "medium",
  "establishment_date": "2010-01-01",
  "website": "http://www.example.com",
  "primary_contact_name": "李四",
  "primary_contact_phone": "13800138000",
  "primary_contact_email": "contact@example.com",
  "bank_name": "中国银行",
  "bank_account": "6222020000123456789",
  "credit_rating": "A",
  "payment_terms": "月结30天",
  "special_requirements": "需要定期技术支持",
  "notes": "重要客户",
  "source": "展会"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 17,
    "name": "示例科技有限公司",
    // ... 其他客户字段
    "created_at": "2025-07-10T08:15:30.123456Z",
    "updated_at": "2025-07-10T08:15:30.123456Z",
    "created_by": "admin",
    "updated_by": null
  }
}
```

## 4. 更新客户

更新指定ID的客户信息。

### 请求

- **方法**: `PUT`
- **URL**: `/api/v1/customers/{id}/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户ID |

### 请求体

```json
{
  "name": "更新后的科技有限公司",
  "type": "company",
  "value_level": "vip",
  "status": "active",
  // ... 其他需要更新的字段
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 8,
    "name": "更新后的科技有限公司",
    // ... 其他客户字段
    "updated_at": "2025-07-10T09:20:15.123456Z",
    "updated_by": "admin"
  }
}
```

## 5. 部分更新客户

部分更新指定ID的客户信息。

### 请求

- **方法**: `PATCH`
- **URL**: `/api/v1/customers/{id}/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户ID |

### 请求体

```json
{
  "status": "inactive",
  "notes": "已暂停合作"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 8,
    "name": "示例科技有限公司",
    "status": "inactive",
    "notes": "已暂停合作",
    // ... 其他客户字段
    "updated_at": "2025-07-10T10:30:45.123456Z",
    "updated_by": "admin"
  }
}
```

## 6. 删除客户

删除指定ID的客户（软删除）。

### 请求

- **方法**: `DELETE`
- **URL**: `/api/v1/customers/{id}/`
- **权限**: 管理员

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "删除成功",
  "data": null
}
```

## 7. 搜索客户

根据关键词搜索客户信息。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/search/`
- **权限**: 管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 8,
      "name": "示例科技有限公司",
      "type": "company",
      "value_level": "vip",
      "status": "active",
      "primary_contact_name": "李四",
      "primary_contact_phone": "13800138000",
      "industry_type": "信息技术",
      "company_size": "medium",
      "created_at": "2025-07-05T05:04:42.362927Z"
    },
    // ... 更多匹配的客户记录
  ]
}
```

## 8. 客户统计

获取客户统计数据。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/statistics/`
- **权限**: 管理员

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "total_count": 10,
    "active_count": 8,
    "inactive_count": 1,
    "potential_count": 1,
    "lost_count": 0,
    "by_type": {
      "company": 7,
      "personal": 1,
      "government": 1,
      "nonprofit": 0,
      "education": 1
    },
    "by_value_level": {
      "platinum": 2,
      "gold": 3,
      "silver": 4,
      "bronze": 1
    },
    "by_company_size": {
      "micro": 1,
      "small": 3,
      "medium": 4,
      "large": 2
    }
  }
}
```

## 9. 批量创建客户

批量创建多个客户记录。

### 请求

- **方法**: `POST`
- **URL**: `/api/v1/customers/bulk-create/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 请求体

```json
{
  "customers": [
    {
      "name": "客户A",
      "type": "company",
      "value_level": "gold",
      "status": "active",
      // ... 其他客户字段
    },
    {
      "name": "客户B",
      "type": "personal",
      "value_level": "silver",
      "status": "active",
      // ... 其他客户字段
    }
  ]
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "批量创建成功",
  "data": [
    {
      "id": 18,
      "name": "客户A",
      // ... 其他客户字段
    },
    {
      "id": 19,
      "name": "客户B",
      // ... 其他客户字段
    }
  ]
}
```

## 10. 批量更新客户

批量更新多个客户记录。

### 请求

- **方法**: `POST`
- **URL**: `/api/v1/customers/bulk-update/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 请求体

```json
{
  "customers": [
    {
      "id": 8,
      "status": "inactive"
    },
    {
      "id": 9,
      "status": "inactive"
    }
  ]
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "批量更新成功",
  "data": [
    {
      "id": 8,
      "name": "示例科技有限公司",
      "status": "inactive",
      // ... 其他客户字段
    },
    {
      "id": 9,
      "name": "123123123",
      "status": "inactive",
      // ... 其他客户字段
    }
  ]
}
```

## 11. 批量删除客户

批量删除多个客户记录（软删除）。

### 请求

- **方法**: `POST`
- **URL**: `/api/v1/customers/bulk-delete/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 请求体

```json
{
  "ids": [8, 9]
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "批量删除成功",
  "data": null
}
```

## 数据模型

### 客户类型 (type)

| 值 | 描述 |
|------|------|
| company | 公司 |
| individual | 个人 |
| government | 政府机构 |
| nonprofit | 非营利组织 |
| education | 教育机构 |

### 价值等级 (value_level)

| 值 | 描述 |
|------|------|
| platinum | 铂金 |
| gold | 黄金 |
| silver | 白银 |
| bronze | 青铜 |

### 客户状态 (status)

| 值 | 描述 |
|------|------|
| active | 活跃 |
| inactive | 非活跃 |
| potential | 潜在 |
| lost | 流失 |

### 公司规模 (company_size)

| 值 | 描述 |
|------|------|
| micro | 微型 |
| small | 小型 |
| medium | 中型 |
| large | 大型 | 