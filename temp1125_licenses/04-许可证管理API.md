# 许可证管理 API

许可证（License）是系统的核心实体，代表颁发给客户的软件授权。

## API 列表

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/licenses/admin/licenses/ | 获取许可证列表 |
| POST | /api/v1/licenses/admin/licenses/ | 创建许可证 |
| GET | /api/v1/licenses/admin/licenses/{id}/ | 获取许可证详情 |
| PUT | /api/v1/licenses/admin/licenses/{id}/ | 更新许可证（全量） |
| PATCH | /api/v1/licenses/admin/licenses/{id}/ | 更新许可证（部分） |
| DELETE | /api/v1/licenses/admin/licenses/{id}/ | 删除许可证 |
| GET | /api/v1/licenses/admin/licenses/{id}/download/ | 下载许可证 |
| POST | /api/v1/licenses/admin/licenses/{id}/extend/ | 延长许可证有效期 |
| POST | /api/v1/licenses/admin/licenses/{id}/revoke/ | 撤销许可证 |
| GET | /api/v1/licenses/admin/licenses/{id}/usage_stats/ | 获取使用统计 |
| POST | /api/v1/licenses/admin/licenses/batch_operation/ | 批量操作 |

---

## 1. 获取许可证列表

### 请求

```http
GET /api/v1/licenses/admin/licenses/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token |

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 10 |
| search | string | 否 | 搜索（许可证密钥、客户名、邮箱） |
| application | integer | 否 | 按产品 ID 过滤 |
| plan | integer | 否 | 按方案 ID 过滤 |
| status | string | 否 | 按状态过滤 |
| ordering | string | 否 | 排序字段：-created_at, expires_at 等 |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

### 响应示例

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
                "id": 37,
                "application": 6,
                "application_name": "填色花园",
                "plan": 19,
                "plan_name": "试用版",
                "tenant": 3,
                "tenant_name": "填色",
                "license_key": "9CE64-B11D7-004FF-4B6AE-30967",
                "customer_name": "API测试客户",
                "customer_email": "apitest@example.com",
                "max_activations": 5,
                "current_activations": 0,
                "issued_at": "2025-11-25T09:06:03.300302Z",
                "expires_at": "2026-01-24T09:06:03.240637Z",
                "last_verified_at": null,
                "status": "generated",
                "machine_bindings_count": 0,
                "days_until_expiry": 59,
                "notes": ""
            },
            {
                "id": 36,
                "application": 6,
                "application_name": "填色花园",
                "plan": 19,
                "plan_name": "试用版",
                "tenant": 3,
                "tenant_name": "填色",
                "license_key": "8CDAF-05248-584DE-BA4CA-0A57D",
                "customer_name": "测试客户",
                "customer_email": "test@example.com",
                "max_activations": 3,
                "current_activations": 0,
                "issued_at": "2025-11-25T08:03:32.963383Z",
                "expires_at": "2026-03-25T08:03:32.913887Z",
                "last_verified_at": null,
                "status": "generated",
                "machine_bindings_count": 0,
                "days_until_expiry": 119,
                "notes": "更新的备注"
            }
        ]
    }
}
```

---

## 2. 创建许可证

### 请求

```http
POST /api/v1/licenses/admin/licenses/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token |
| Content-Type | 是 | application/json |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| application | integer | 是 | 产品 ID |
| plan | integer | 是 | 许可方案 ID |
| customer_info | object | 是 | 客户信息 |
| customer_info.name | string | 是 | 客户名称 |
| customer_info.email | string | 是 | 客户邮箱 |
| max_activations | integer | 否 | 最大激活数（默认使用方案设置） |
| validity_days | integer | 否 | 有效天数（默认使用方案设置） |
| notes | string | 否 | 备注 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{
    "application": 6,
    "plan": 19,
    "customer_info": {
      "name": "Curl测试客户",
      "email": "curltest@example.com"
    },
    "max_activations": 5,
    "validity_days": 90,
    "notes": "通过Curl创建的许可证"
  }'
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "application": 6,
        "plan": 19,
        "tenant": 3,
        "max_activations": 5,
        "notes": ""
    }
}
```

---

## 3. 获取许可证详情

### 请求

```http
GET /api/v1/licenses/admin/licenses/{id}/
```

### 路径参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| id | integer | 许可证 ID |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/36/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 36,
        "application": 6,
        "application_name": "填色花园",
        "plan": 19,
        "plan_name": "试用版",
        "tenant": 3,
        "tenant_name": "填色",
        "license_key": "8CDAF-05248-584DE-BA4CA-0A57D",
        "customer_name": "测试客户",
        "customer_email": "test@example.com",
        "max_activations": 3,
        "current_activations": 0,
        "issued_at": "2025-11-25T08:03:32.963383Z",
        "expires_at": "2026-03-25T08:03:32.913887Z",
        "last_verified_at": null,
        "status": "generated",
        "machine_bindings_count": 0,
        "days_until_expiry": 119,
        "notes": "更新的备注",
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

## 4. 更新许可证

### PATCH 请求（部分更新）

```http
PATCH /api/v1/licenses/admin/licenses/{id}/
```

### 可更新字段

| 字段 | 类型 | 说明 |
|-----|------|------|
| customer_name | string | 客户名称 |
| customer_email | string | 客户邮箱 |
| max_activations | integer | 最大激活数 |
| notes | string | 备注 |

### curl 示例

```bash
curl -X PATCH "http://localhost:8000/api/v1/licenses/admin/licenses/36/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{"notes": "更新后的备注信息"}'
```

---

## 5. 删除许可证

### 请求

```http
DELETE /api/v1/licenses/admin/licenses/{id}/
```

### curl 示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/licenses/admin/licenses/38/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

---

## 6. 下载许可证

获取许可证的完整信息，包括使用说明。

### 请求

```http
GET /api/v1/licenses/admin/licenses/{id}/download/
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| format | string | 否 | 格式：json（默认）、text |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/36/download/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "license_key": "8CDAF-05248-584DE-BA4CA-0A57D",
        "customer_info": {
            "name": "测试客户",
            "email": "test@example.com"
        },
        "application_info": {
            "name": "填色花园",
            "code": "test-create-app",
            "version": "1.0.0",
            "description": "填色花园"
        },
        "plan_info": {
            "name": "试用版",
            "type": "trial",
            "features": {
                "basic": true
            },
            "default_max_activations": 1
        },
        "activation_info": {
            "max_activations": 3,
            "current_activations": 0,
            "status": "generated"
        },
        "validity_info": {
            "issued_at": "2025-11-25T08:03:32.963383+00:00",
            "expires_at": "2026-03-25T08:03:32.913887+00:00",
            "last_verified_at": null
        },
        "instructions": "许可证使用说明\n=============\n\n产品名称: 填色花园\n许可方案: 试用版\n许可证密钥: 8CDAF-05248-584DE-BA4CA-0A57D\n\n安装说明:\n1. 下载并安装 填色花园 软件\n2. 启动软件后，在许可证激活界面输入上述许可证密钥\n3. 按照软件提示完成激活流程\n\n重要信息:\n- 最大激活设备数: 3\n- current已激活设备数: 0\n- 许可证过期时间: 2026年03月25日 08:03:32\n- 许可证状态: 已生成\n\n注意事项:\n- 请妥善保管许可证密钥，避免泄露\n- 如需在新设备激活，请先在原设备解除激活\n- 如遇激活问题，请联系技术支持\n\n技术支持:\n如有任何问题，请联系我们的技术支持团队。\n\n生成时间: 2025年11月25日 09:28:29",
        "generated_at": "2025-11-25T09:28:29.616404+00:00",
        "download_by": "admin_cms"
    }
}
```

---

## 7. 延长许可证有效期

### 请求

```http
POST /api/v1/licenses/admin/licenses/{id}/extend/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| days | integer | 是 | 延长的天数 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/36/extend/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "许可证有效期已延长30天",
    "data": {
        "new_expiry": "2026-04-24T08:03:32.913887+00:00"
    }
}
```

---

## 8. 撤销许可证

### 请求

```http
POST /api/v1/licenses/admin/licenses/{id}/revoke/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| reason | string | 否 | 撤销原因 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/36/revoke/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{"reason": "客户要求退款"}'
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "许可证已撤销",
    "data": {
        "status": "revoked",
        "revoked_at": "2025-11-25T10:00:00.000000+00:00"
    }
}
```

---

## 9. 获取使用统计

### 请求

```http
GET /api/v1/licenses/admin/licenses/{id}/usage_stats/
```

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/licenses/36/usage_stats/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "license_id": 36,
        "status": "generated",
        "created_at": "2025-11-25T08:03:32.963329+00:00",
        "expires_at": "2026-03-25T08:03:32.913887+00:00",
        "machine_bindings": {
            "total": 0,
            "active": 0,
            "max_allowed": 3
        },
        "activations": {
            "total_attempts": 0,
            "successful": 0,
            "last_activation": null
        },
        "usage": {
            "recent_events": 0,
            "last_verified": null
        }
    }
}
```

---

## 10. 批量操作

### 请求

```http
POST /api/v1/licenses/admin/licenses/batch_operation/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| operation | string | 是 | 操作类型：revoke, extend, delete |
| license_ids | array | 是 | 许可证 ID 列表 |
| days | integer | 条件 | 延长天数（extend 操作时必填） |
| reason | string | 否 | 操作原因 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "extend",
    "license_ids": [36, 37],
    "days": 30
  }'
```

---

## 数据模型

### License 状态枚举

| 状态 | 说明 |
|-----|------|
| generated | 已生成（未激活） |
| active | 已激活 |
| suspended | 已暂停 |
| revoked | 已撤销 |
| expired | 已过期 |

### License 字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | integer | 许可证 ID |
| application | integer | 产品 ID |
| application_name | string | 产品名称（只读） |
| plan | integer | 方案 ID |
| plan_name | string | 方案名称（只读） |
| tenant | integer | 租户 ID |
| tenant_name | string | 租户名称（只读） |
| license_key | string | 许可证密钥（只读，自动生成） |
| customer_name | string | 客户名称 |
| customer_email | string | 客户邮箱 |
| max_activations | integer | 最大激活数 |
| current_activations | integer | 当前激活数（只读） |
| issued_at | datetime | 颁发时间（只读） |
| expires_at | datetime | 过期时间 |
| last_verified_at | datetime | 最后验证时间（只读） |
| status | string | 状态 |
| machine_bindings_count | integer | 机器绑定数量（只读） |
| days_until_expiry | integer | 距离过期天数（只读） |
| notes | string | 备注 |
