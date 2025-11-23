# 许可证管理API文档

## 概述

许可证（License）是授权用户使用软件的凭证，包含许可证密钥、有效期、激活限制等信息。

## API列表

### 1. 获取许可证列表

**接口**: `GET /api/v1/licenses/admin/licenses/`

**权限**: 租户管理员

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| application | int | 否 | 按产品ID过滤 |
| plan | int | 否 | 按方案ID过滤 |
| status | string | 否 | 状态: generated/activated/suspended/revoked/expired |
| search | string | 否 | 搜索（客户名、邮箱、许可证密钥） |
| ordering | string | 否 | 排序字段 |

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/?status=activated&page=1" \
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
      "count": 4,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 34,
        "application": null,
        "application_name": null,
        "plan": 15,
        "plan_name": "试用版",
        "tenant": 1,
        "tenant_name": "金sir",
        "license_key": "6260D-4913D-64411-2A7A4-3321B",
        "customer_name": "fx0883",
        "customer_email": "fx0883@qq.com",
        "max_activations": 10,
        "current_activations": 1,
        "issued_at": "2025-10-18T06:35:59.402792Z",
        "expires_at": "2025-11-22T06:35:59.389130Z",
        "last_verified_at": "2025-10-18T08:23:09.935771Z",
        "status": "revoke",
        "machine_bindings_count": 0,
        "days_until_expiry": -2,
        "notes": ""
      }
    ]
  }
}
```

---

### 2. 创建许可证

**接口**: `POST /api/v1/licenses/admin/licenses/`

**权限**: 租户管理员

**请求体**:
```json
{
  "plan": 15,
  "customer_name": "张三",
  "customer_email": "zhangsan@example.com",
  "max_activations": 5,
  "validity_days": 365,
  "notes": "企业客户订单#12345"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| plan | int | 是 | 许可证方案ID |
| customer_name | string | 是 | 客户名称 |
| customer_email | string | 是 | 客户邮箱 |
| max_activations | int | 否 | 最大激活数，默认继承方案 |
| validity_days | int | 否 | 有效天数，默认继承方案 |
| notes | string | 否 | 备注信息 |

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": 15,
    "customer_name": "李四",
    "customer_email": "lisi@example.com",
    "max_activations": 10,
    "validity_days": 365,
    "notes": "年度企业客户"
  }'
```

**成功响应** (201 Created):
```json
{
  "success": true,
  "code": 2001,
  "message": "创建成功",
  "data": {
    "id": 35,
    "application": 1,
    "plan": 15,
    "plan_name": "试用版",
    "tenant": 1,
    "tenant_name": "金sir",
    "license_key": "A12B3-C45D6-E78F9-G01H2-I34J5",
    "customer_name": "李四",
    "customer_email": "lisi@example.com",
    "max_activations": 10,
    "current_activations": 0,
    "issued_at": "2025-11-23T14:30:00.000000Z",
    "expires_at": "2026-11-23T14:30:00.000000Z",
    "last_verified_at": null,
    "status": "generated",
    "machine_bindings_count": 0,
    "days_until_expiry": 365,
    "notes": "年度企业客户"
  }
}
```

---

### 3. 获取许可证详情

**接口**: `GET /api/v1/licenses/admin/licenses/{id}/`

**权限**: 租户管理员

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/34/" \
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
    "id": 34,
    "application": 1,
    "plan": 15,
    "plan_name": "试用版",
    "tenant": 1,
    "tenant_name": "金sir",
    "license_key": "6260D-4913D-64411-2A7A4-3321B",
    "customer_name": "fx0883",
    "customer_email": "fx0883@qq.com",
    "max_activations": 10,
    "current_activations": 1,
    "issued_at": "2025-10-18T06:35:59.402792Z",
    "expires_at": "2025-11-22T06:35:59.389130Z",
    "last_verified_at": "2025-10-18T08:23:09.935771Z",
    "status": "revoke",
    "machine_bindings_count": 0,
    "days_until_expiry": -2,
    "notes": "",
    "machine_bindings": [],
    "recent_activations": [],
    "usage_stats": {
      "total_usage_logs": 0,
      "recent_usage_logs": 0
    },
    "metadata": {
      "creation_source": "api"
    }
  }
}
```

---

### 4. 更新许可证

**接口**: `PUT /api/v1/licenses/admin/licenses/{id}/`

**权限**: 租户管理员

**curl示例**:
```bash
curl -X PUT "http://localhost:8000/api/v1/licenses/admin/licenses/34/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": 15,
    "customer_name": "fx0883（更新）",
    "customer_email": "fx0883@qq.com",
    "max_activations": 15,
    "notes": "更新激活数限制"
  }'
```

---

### 5. 部分更新许可证

**接口**: `PATCH /api/v1/licenses/admin/licenses/{id}/`

**权限**: 租户管理员

**curl示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/licenses/admin/licenses/34/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "max_activations": 20,
    "notes": "客户升级套餐"
  }'
```

---

### 6. 删除许可证

**接口**: `DELETE /api/v1/licenses/admin/licenses/{id}/`

**权限**: 租户管理员

**描述**: 软删除许可证

**curl示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/licenses/admin/licenses/34/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

---

### 7. 下载许可证

**接口**: `GET /api/v1/licenses/admin/licenses/{id}/download/`

**权限**: 租户管理员

**描述**: 下载许可证文件（通常为.lic或.key格式）

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/34/download/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -o license.lic
```

---

### 8. 延长许可证有效期

**接口**: `POST /api/v1/licenses/admin/licenses/{id}/extend/`

**权限**: 租户管理员

**请求体**:
```json
{
  "days": 90
}
```

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/34/extend/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "days": 90
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "许可证有效期已延长90天",
  "data": {
    "old_expires_at": "2025-11-22T06:35:59.389130Z",
    "new_expires_at": "2026-02-20T06:35:59.389130Z",
    "extended_days": 90
  }
}
```

---

### 9. 撤销许可证

**接口**: `POST /api/v1/licenses/admin/licenses/{id}/revoke/`

**权限**: 租户管理员

**请求体**:
```json
{
  "reason": "客户违反使用条款"
}
```

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/34/revoke/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "客户要求退款"
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "许可证已撤销",
  "data": {
    "license_id": 34,
    "status": "revoked",
    "revoked_at": "2025-11-23T14:35:00.000000Z",
    "reason": "客户要求退款"
  }
}
```

---

### 10. 获取许可证使用统计

**接口**: `GET /api/v1/licenses/admin/licenses/{id}/usage_stats/`

**权限**: 租户管理员

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/34/usage_stats/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

**成功响应** (200 OK):
```json
{
  "license_id": 34,
  "license_key": "6260D-***-3321B",
  "statistics": {
    "total_activations": 5,
    "successful_activations": 5,
    "failed_activations": 0,
    "current_active_machines": 3,
    "total_machines": 5,
    "usage_events": {
      "total": 1250,
      "last_7_days": 350,
      "last_30_days": 1200
    },
    "heartbeats": {
      "total": 500,
      "last_24_hours": 50
    }
  },
  "generated_at": "2025-11-23T14:40:00.000000Z"
}
```

---

### 11. 批量操作许可证

**接口**: `POST /api/v1/licenses/admin/licenses/batch_operation/`

**权限**: 租户管理员

**请求体**:
```json
{
  "operation": "revoke",
  "license_ids": [31, 32, 33],
  "reason": "批量撤销过期许可证"
}
```

**操作类型**:
- `revoke`: 批量撤销
- `extend`: 批量延期
- `suspend`: 批量挂起
- `activate`: 批量激活

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "extend",
    "license_ids": [31, 32, 33],
    "days": 30
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "批量操作完成",
  "data": {
    "operation": "extend",
    "total": 3,
    "succeeded": 3,
    "failed": 0,
    "results": [
      {"license_id": 31, "status": "success"},
      {"license_id": 32, "status": "success"},
      {"license_id": 33, "status": "success"}
    ]
  }
}
```

---

## 许可证状态说明

### generated - 已生成
- 许可证刚创建，尚未激活
- 可以分配给用户

### activated - 已激活
- 至少有一个设备已激活
- 正常使用中

### suspended - 已挂起
- 临时停用
- 可恢复使用

### revoked - 已撤销
- 永久撤销
- 无法恢复

### expired - 已过期
- 超过有效期
- 可以通过延期恢复

---

## 注意事项

1. **许可证密钥**: 创建时自动生成，格式为5组5位字符
2. **有效期计算**: 从issued_at开始，加上validity_days
3. **激活限制**: current_activations不能超过max_activations
4. **撤销影响**: 撤销后所有激活的设备将失效
5. **删除限制**: 已激活的许可证建议撤销而非删除
6. **批量操作**: 注意操作影响范围，建议先测试
