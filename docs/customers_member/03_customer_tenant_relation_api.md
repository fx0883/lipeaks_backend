# 客户-租户关系API

本文档描述客户与租户之间关系管理的API，包括获取客户的租户关系列表、创建租户关系、更新租户关系和设置主要租户关系等功能。

## API端点

所有客户-租户关系API的基础URL为：`/api/v1/customers/tenants/relations/`

## 1. 获取客户的租户关系列表

获取指定客户的所有租户关系。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/tenants/relations/`
- **权限**: 管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | int | 否 | 客户ID，用于筛选特定客户的租户关系 |
| tenant_id | int | 否 | 租户ID，用于筛选特定租户的客户关系 |
| relation_type | string | 否 | 关系类型，如'supplier', 'customer', 'partner' |
| page | int | 否 | 页码，默认为1 |
| limit | int | 否 | 每页记录数，默认为10 |

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
        "id": 4,
        "customer_id": 8,
        "customer_name": "示例科技有限公司",
        "tenant_id": 6,
        "tenant_name": "租户B",
        "relation_type": "partner",
        "relation_type_display": "合作伙伴",
        "is_primary": false,
        "contract_number": "PT-20250705-001",
        "start_date": "2025-07-01",
        "end_date": "2026-06-30",
        "description": "战略合作伙伴协议",
        "is_active": true,
        "created_at": "2025-07-05T06:15:42.362927Z",
        "updated_at": "2025-07-05T06:15:42.362927Z",
        "created_by": "admin",
        "updated_by": null
      }
    ]
  }
}
```

## 2. 获取客户-租户关系详情

获取指定ID的客户-租户关系详情。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/tenants/relations/{id}/`
- **权限**: 管理员

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户-租户关系ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
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
  }
}
```

## 3. 创建客户-租户关系

为客户添加新的租户关系。

### 请求

- **方法**: `POST`
- **URL**: `/api/v1/customers/tenants/relations/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 请求体

```json
{
  "customer_id": 8,
  "tenant_id": 7,
  "relation_type": "supplier",
  "is_primary": false,
  "contract_number": "SP-20250710-001",
  "start_date": "2025-07-10",
  "end_date": "2026-07-09",
  "description": "供应商协议"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 5,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "tenant_id": 7,
    "tenant_name": "租户C",
    "relation_type": "supplier",
    "relation_type_display": "供应商",
    "is_primary": false,
    "contract_number": "SP-20250710-001",
    "start_date": "2025-07-10",
    "end_date": "2026-07-09",
    "description": "供应商协议",
    "is_active": true,
    "created_at": "2025-07-10T08:15:30.123456Z",
    "updated_at": "2025-07-10T08:15:30.123456Z",
    "created_by": "admin",
    "updated_by": null
  }
}
```

## 4. 更新客户-租户关系

更新指定ID的客户-租户关系。

### 请求

- **方法**: `PUT`
- **URL**: `/api/v1/customers/tenants/relations/{id}/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户-租户关系ID |

### 请求体

```json
{
  "customer_id": 8,
  "tenant_id": 7,
  "relation_type": "supplier",
  "is_primary": true,
  "contract_number": "SP-20250710-002",
  "start_date": "2025-07-10",
  "end_date": "2027-07-09",
  "description": "更新后的供应商协议"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 5,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "tenant_id": 7,
    "tenant_name": "租户C",
    "relation_type": "supplier",
    "relation_type_display": "供应商",
    "is_primary": true,
    "contract_number": "SP-20250710-002",
    "start_date": "2025-07-10",
    "end_date": "2027-07-09",
    "description": "更新后的供应商协议",
    "is_active": true,
    "created_at": "2025-07-10T08:15:30.123456Z",
    "updated_at": "2025-07-10T09:20:15.123456Z",
    "created_by": "admin",
    "updated_by": "admin"
  }
}
```

## 5. 部分更新客户-租户关系

部分更新指定ID的客户-租户关系。

### 请求

- **方法**: `PATCH`
- **URL**: `/api/v1/customers/tenants/relations/{id}/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户-租户关系ID |

### 请求体

```json
{
  "contract_number": "SP-20250710-003",
  "description": "修订后的供应商协议"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 5,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "tenant_id": 7,
    "tenant_name": "租户C",
    "relation_type": "supplier",
    "relation_type_display": "供应商",
    "is_primary": true,
    "contract_number": "SP-20250710-003",
    "start_date": "2025-07-10",
    "end_date": "2027-07-09",
    "description": "修订后的供应商协议",
    "is_active": true,
    "created_at": "2025-07-10T08:15:30.123456Z",
    "updated_at": "2025-07-10T10:30:45.123456Z",
    "created_by": "admin",
    "updated_by": "admin"
  }
}
```

## 6. 删除客户-租户关系

删除指定ID的客户-租户关系。

### 请求

- **方法**: `DELETE`
- **URL**: `/api/v1/customers/tenants/relations/{id}/`
- **权限**: 管理员

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户-租户关系ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "删除成功",
  "data": null
}
```

## 7. 设置主要租户关系

将指定的租户关系设置为客户的主要租户关系。

### 请求

- **方法**: `POST`
- **URL**: `/api/v1/customers/tenants/relations/{id}/set-primary/`
- **权限**: 管理员

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户-租户关系ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 4,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "tenant_id": 6,
    "tenant_name": "租户B",
    "relation_type": "partner",
    "relation_type_display": "合作伙伴",
    "is_primary": true,
    "contract_number": "PT-20250705-001",
    "start_date": "2025-07-01",
    "end_date": "2026-06-30",
    "description": "战略合作伙伴协议",
    "is_active": true,
    "created_at": "2025-07-05T06:15:42.362927Z",
    "updated_at": "2025-07-10T11:45:30.123456Z",
    "created_by": "admin",
    "updated_by": "admin"
  }
}
```

## 8. 获取客户的主要租户关系

获取指定客户的主要租户关系。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/tenants/relations/primary/`
- **权限**: 管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | int | 是 | 客户ID |
| relation_type | string | 否 | 关系类型，如果指定，则获取该类型的主要关系 |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 4,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "tenant_id": 6,
    "tenant_name": "租户B",
    "relation_type": "partner",
    "relation_type_display": "合作伙伴",
    "is_primary": true,
    "contract_number": "PT-20250705-001",
    "start_date": "2025-07-01",
    "end_date": "2026-06-30",
    "description": "战略合作伙伴协议",
    "is_active": true,
    "created_at": "2025-07-05T06:15:42.362927Z",
    "updated_at": "2025-07-10T11:45:30.123456Z",
    "created_by": "admin",
    "updated_by": "admin"
  }
}
```

## 9. 获取客户与租户的关系

获取特定客户与租户之间的关系。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/tenants/relations/between/`
- **权限**: 管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | int | 是 | 客户ID |
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
    }
  ]
}
```

## 错误响应示例

### 1. 客户ID不存在

```json
{
  "success": false,
  "code": 4004,
  "message": "客户不存在",
  "data": null
}
```

### 2. 缺少必要参数

```json
{
  "success": false,
  "code": 4000,
  "message": "请提供客户ID和租户ID",
  "data": null
}
```

### 3. 日期验证错误

```json
{
  "success": false,
  "code": 4000,
  "message": "结束日期不能早于开始日期",
  "data": null
}
```

## 数据模型

### 客户-租户关系字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int | 关系ID |
| customer_id | int | 客户ID |
| customer_name | string | 客户名称 |
| tenant_id | int | 租户ID |
| tenant_name | string | 租户名称 |
| relation_type | string | 关系类型 |
| relation_type_display | string | 关系类型显示名称 |
| is_primary | boolean | 是否为主要关系 |
| contract_number | string | 合同编号 |
| start_date | date | 关系开始日期 |
| end_date | date | 关系结束日期 |
| description | string | 关系描述 |
| is_active | boolean | 关系是否处于活跃状态 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
| created_by | string | 创建人 |
| updated_by | string | 更新人 |

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