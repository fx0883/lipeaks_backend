# 租户视角的客户API

本文档描述从租户视角查看和管理客户的API，包括获取租户关联的客户列表、获取租户视角下的客户详情和获取租户的客户统计数据等功能。

## API端点

所有租户视角的客户API的基础URL为：`/api/v1/customers/tenants/view/`

## 1. 获取租户关联的客户列表

获取与指定租户有关系的所有客户。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/tenants/view/`
- **权限**: 管理员或租户管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| tenant_id | int | 是 | 租户ID |
| relation_type | string | 否 | 关系类型，用于筛选特定关系类型的客户 |
| status | string | 否 | 客户状态，用于筛选特定状态的客户 |
| page | int | 否 | 页码，默认为1 |
| limit | int | 否 | 每页记录数，默认为10 |
| search | string | 否 | 搜索客户名称、联系人等信息 |
| ordering | string | 否 | 排序字段，如 name, -created_at (前缀-表示降序) |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 2,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
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
      {
        "id": 9,
        "name": "123123123",
        "type": "personal",
        "value_level": "normal",
        "status": "active",
        "primary_contact_name": null,
        "primary_contact_phone": null,
        "industry_type": null,
        "company_size": null,
        "created_at": "2025-07-05T12:02:11.968053Z"
      }
    ]
  }
}
```

## 2. 获取租户视角下的客户详情

获取指定租户视角下的客户详情。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/tenants/view/{id}/`
- **权限**: 管理员或租户管理员

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户ID |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| tenant_id | int | 是 | 租户ID |

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

## 3. 获取租户的客户统计数据

获取指定租户关联的客户统计数据。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/tenants/view/statistics/`
- **权限**: 管理员或租户管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| tenant_id | int | 是 | 租户ID |
| relation_type | string | 否 | 关系类型，用于筛选特定关系类型的客户统计 |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "total_count": 5,
    "active_count": 4,
    "inactive_count": 1,
    "potential_count": 0,
    "lost_count": 0,
    "by_type": {
      "company": 3,
      "personal": 1,
      "government": 1,
      "nonprofit": 0,
      "education": 0
    },
    "by_value_level": {
      "platinum": 1,
      "gold": 2,
      "silver": 1,
      "bronze": 1
    },
    "by_company_size": {
      "micro": 0,
      "small": 1,
      "medium": 2,
      "large": 0
    }
  }
}
```

## 4. 获取客户与租户的关系

获取指定客户与租户之间的所有关系。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/tenants/view/{id}/relations/`
- **权限**: 管理员或租户管理员

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户ID |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| tenant_id | int | 是 | 租户ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 3,
      "customer_id": 8,
      "customer_name": "示例科技有限公司",
      "tenant_id": 5,
      "tenant_name": "租户A",
      "relation_type": "customer",
      "relation_type_display": "客户",
      "is_primary": true,
      "contract_number": "CT-20250705-001",
      "start_date": "2025-07-01",
      "end_date": "2026-06-30",
      "description": "年度服务合同",
      "is_active": true,
      "created_at": "2025-07-05T06:14:42.362927Z",
      "updated_at": "2025-07-05T06:14:42.362927Z",
      "created_by": "admin",
      "updated_by": null
    },
    {
      "id": 6,
      "customer_id": 8,
      "customer_name": "示例科技有限公司",
      "tenant_id": 5,
      "tenant_name": "租户A",
      "relation_type": "partner",
      "relation_type_display": "合作伙伴",
      "is_primary": false,
      "contract_number": "PT-20250705-002",
      "start_date": "2025-07-01",
      "end_date": "2026-06-30",
      "description": "战略合作伙伴协议",
      "is_active": true,
      "created_at": "2025-07-05T06:18:42.362927Z",
      "updated_at": "2025-07-05T06:18:42.362927Z",
      "created_by": "admin",
      "updated_by": null
    }
  ]
}
```

## 错误响应示例

### 1. 缺少租户ID

```json
{
  "success": false,
  "code": 4000,
  "message": "请提供租户ID",
  "data": null
}
```

### 2. 客户与租户没有关系

```json
{
  "success": false,
  "code": 4004,
  "message": "该客户与租户没有关系",
  "data": null
}
```

## 数据模型

### 客户类型 (type)

| 值 | 描述 |
|------|------|
| company | 公司 |
| personal | 个人 |
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

### 关系类型 (relation_type)

| 值 | 显示名称 | 描述 |
|------|------|------|
| customer | 客户 | 该客户是租户的客户 |
| supplier | 供应商 | 该客户是租户的供应商 |
| partner | 合作伙伴 | 该客户是租户的合作伙伴 |
| distributor | 分销商 | 该客户是租户的分销商 |
| agent | 代理商 | 该客户是租户的代理商 |
| competitor | 竞争对手 | 该客户是租户的竞争对手 |
| other | 其他 | 其他关系类型 | 