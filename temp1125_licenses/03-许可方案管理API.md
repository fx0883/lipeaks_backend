# 许可方案管理 API

许可方案（License Plan）定义了许可证的类型、功能特性、有效期和价格等属性。

## API 列表

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/licenses/admin/plans/ | 获取许可方案列表 |
| POST | /api/v1/licenses/admin/plans/ | 创建许可方案 |
| GET | /api/v1/licenses/admin/plans/{id}/ | 获取许可方案详情 |
| PUT | /api/v1/licenses/admin/plans/{id}/ | 更新许可方案（全量） |
| PATCH | /api/v1/licenses/admin/plans/{id}/ | 更新许可方案（部分） |
| DELETE | /api/v1/licenses/admin/plans/{id}/ | 删除许可方案 |
| POST | /api/v1/licenses/admin/plans/{id}/duplicate/ | 复制许可方案 |

---

## 1. 获取许可方案列表

### 请求

```http
GET /api/v1/licenses/admin/plans/
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
| search | string | 否 | 搜索关键词 |
| application | integer | 否 | 按产品 ID 过滤 |
| plan_type | string | 否 | 按类型过滤：trial, subscription, perpetual, floating, professional, enterprise |
| status | string | 否 | 按状态过滤：active, inactive |
| ordering | string | 否 | 排序字段 |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/plans/" \
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
            "count": 1,
            "next": null,
            "previous": null,
            "page_size": 10,
            "current_page": 1,
            "total_pages": 1
        },
        "results": [
            {
                "id": 19,
                "application": 6,
                "application_name": "填色花园",
                "name": "试用版",
                "code": "trial",
                "plan_type": "trial",
                "default_max_activations": 1,
                "default_validity_days": 30,
                "features": {
                    "basic": true
                },
                "price": "0.00",
                "currency": "CNY",
                "status": "active",
                "licenses_count": 2,
                "created_at": "2025-11-25T08:00:26.553126Z",
                "updated_at": "2025-11-25T08:00:26.553175Z"
            }
        ]
    }
}
```

---

## 2. 创建许可方案

### 请求

```http
POST /api/v1/licenses/admin/plans/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token |
| Content-Type | 是 | application/json |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| application | integer | 是 | 关联的产品 ID |
| name | string | 是 | 方案名称 |
| code | string | 是 | 方案代码（在同一产品下唯一） |
| plan_type | string | 是 | 方案类型 |
| default_max_activations | integer | 否 | 默认最大激活数，默认 1 |
| default_validity_days | integer | 否 | 默认有效天数，默认 30 |
| features | object | 否 | 功能特性 JSON |
| price | string | 否 | 价格，默认 "0.00" |
| currency | string | 否 | 货币代码，默认 "CNY" |
| status | string | 否 | 状态，默认 "active" |

### 方案类型枚举

| 类型 | 说明 |
|-----|------|
| trial | 试用版 |
| subscription | 订阅版 |
| perpetual | 永久版 |
| floating | 浮动授权 |
| professional | 专业版 |
| enterprise | 企业版 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/plans/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{
    "application": 6,
    "name": "专业版",
    "code": "professional",
    "plan_type": "professional",
    "default_max_activations": 5,
    "default_validity_days": 365,
    "features": {
      "advanced": true,
      "support": true
    },
    "price": "199.00",
    "currency": "CNY",
    "status": "active"
  }'
```

### 响应示例

```json
{
    "success": true,
    "code": "professional",
    "message": "操作成功",
    "data": {
        "id": 20,
        "application": 6,
        "application_name": "填色花园",
        "name": "专业版",
        "code": "professional",
        "plan_type": "professional",
        "default_max_activations": 5,
        "default_validity_days": 365,
        "features": {
            "advanced": true,
            "support": true
        },
        "price": "199.00",
        "currency": "CNY",
        "status": "active",
        "licenses_count": 0,
        "created_at": "2025-11-25T09:28:59.182928Z",
        "updated_at": "2025-11-25T09:28:59.182977Z"
    }
}
```

---

## 3. 获取许可方案详情

### 请求

```http
GET /api/v1/licenses/admin/plans/{id}/
```

### 路径参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| id | integer | 许可方案 ID |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/plans/19/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

### 响应示例

```json
{
    "success": true,
    "code": "trial",
    "message": "操作成功",
    "data": {
        "id": 19,
        "application": 6,
        "application_name": "填色花园",
        "name": "试用版",
        "code": "trial",
        "plan_type": "trial",
        "default_max_activations": 1,
        "default_validity_days": 30,
        "features": {
            "basic": true
        },
        "price": "0.00",
        "currency": "CNY",
        "status": "active",
        "licenses_count": 2,
        "created_at": "2025-11-25T08:00:26.553126Z",
        "updated_at": "2025-11-25T08:00:26.553175Z"
    }
}
```

---

## 4. 更新许可方案

### PATCH 请求（部分更新）

```http
PATCH /api/v1/licenses/admin/plans/{id}/
```

### PUT 请求（全量更新）

```http
PUT /api/v1/licenses/admin/plans/{id}/
```

### curl 示例（部分更新）

```bash
curl -X PATCH "http://localhost:8000/api/v1/licenses/admin/plans/19/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{
    "default_validity_days": 60,
    "features": {
      "basic": true,
      "export": true
    }
  }'
```

---

## 5. 删除许可方案

### 请求

```http
DELETE /api/v1/licenses/admin/plans/{id}/
```

### curl 示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/licenses/admin/plans/21/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": null
}
```

---

## 6. 复制许可方案

创建一个现有方案的副本。

### 请求

```http
POST /api/v1/licenses/admin/plans/{id}/duplicate/
```

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/plans/20/duplicate/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "方案复制成功",
    "data": {
        "id": 22,
        "application": 6,
        "application_name": "填色花园",
        "name": "专业版 (副本)",
        "code": "professional-copy",
        "plan_type": "professional",
        "default_max_activations": 5,
        "default_validity_days": 365,
        "features": {
            "advanced": true,
            "support": true
        },
        "price": "199.00",
        "currency": "CNY",
        "status": "inactive",
        "licenses_count": 0,
        "created_at": "2025-11-25T10:00:00.000000Z",
        "updated_at": "2025-11-25T10:00:00.000000Z"
    }
}
```

> **注意**: 当前该 API 存在一个已知 Bug，需要修复 `get_tenant_id` 方法。

---

## 数据模型

### LicensePlan 字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | integer | 方案 ID |
| application | integer | 关联的产品 ID |
| application_name | string | 产品名称（只读） |
| name | string | 方案名称 |
| code | string | 方案代码 |
| plan_type | string | 方案类型 |
| default_max_activations | integer | 默认最大激活数 |
| default_validity_days | integer | 默认有效天数 |
| features | object | 功能特性 JSON |
| price | string | 价格 |
| currency | string | 货币代码 |
| status | string | 状态 |
| licenses_count | integer | 关联的许可证数量（只读） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### Features JSON 示例

```json
{
    "basic": true,
    "advanced": true,
    "export": true,
    "import": true,
    "api_access": true,
    "priority_support": true,
    "max_users": 100,
    "max_storage_gb": 50
}
```
