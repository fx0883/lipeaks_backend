# 配额与审计日志 API

## 一、租户许可证配额 API

管理租户的许可证使用配额。

### API 列表

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/licenses/admin/quotas/ | 获取配额列表 |
| POST | /api/v1/licenses/admin/quotas/ | 创建配额 |
| GET | /api/v1/licenses/admin/quotas/{id}/ | 获取配额详情 |
| PUT | /api/v1/licenses/admin/quotas/{id}/ | 更新配额 |
| PATCH | /api/v1/licenses/admin/quotas/{id}/ | 部分更新配额 |
| DELETE | /api/v1/licenses/admin/quotas/{id}/ | 删除配额 |

---

### 1. 获取配额列表

#### 请求

```http
GET /api/v1/licenses/admin/quotas/
```

#### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |
| application | integer | 否 | 按产品 ID 过滤 |
| is_active | boolean | 否 | 按激活状态过滤 |

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/quotas/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

#### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "pagination": {
            "count": 0,
            "next": null,
            "previous": null,
            "page_size": 10,
            "current_page": 1,
            "total_pages": 1
        },
        "results": []
    }
}
```

---

### 2. 创建配额

#### 请求

```http
POST /api/v1/licenses/admin/quotas/
```

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| application | integer | 是 | 产品 ID |
| max_licenses | integer | 是 | 最大许可证数量 |
| quota_start_date | date | 是 | 配额开始日期 |
| quota_end_date | date | 是 | 配额结束日期 |
| is_active | boolean | 否 | 是否激活，默认 true |

#### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/quotas/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{
    "application": 6,
    "max_licenses": 100,
    "quota_start_date": "2025-01-01",
    "quota_end_date": "2025-12-31",
    "is_active": true
  }'
```

> **注意**: 当前配额 API 对租户管理员存在已知问题，需要超级管理员权限或修复 tenant 字段自动填充逻辑。

---

## 二、安全审计日志 API

查看系统的安全审计日志。

### API 列表

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/licenses/admin/audit-logs/ | 获取审计日志列表 |
| GET | /api/v1/licenses/admin/audit-logs/{id}/ | 获取审计日志详情 |

---

### 1. 获取审计日志列表

#### 请求

```http
GET /api/v1/licenses/admin/audit-logs/
```

#### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |
| event_type | string | 否 | 事件类型过滤 |
| severity | string | 否 | 严重程度过滤：LOW, MEDIUM, HIGH, CRITICAL |
| user | integer | 否 | 按用户 ID 过滤 |
| ordering | string | 否 | 排序字段，默认 -timestamp |

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/audit-logs/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

#### 响应示例

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
                "id": 157,
                "event_type": "data_access",
                "severity": "LOW",
                "user": 3,
                "user_name": "admin_cms",
                "tenant": 3,
                "tenant_name": "填色",
                "ip_address": "127.0.0.1",
                "user_agent": "",
                "details": {
                    "format": "json",
                    "operation": "download_license",
                    "license_id": 36
                },
                "timestamp": "2025-11-25T09:06:16.877067Z"
            },
            {
                "id": 156,
                "event_type": "system_change",
                "severity": "LOW",
                "user": 3,
                "user_name": "admin_cms",
                "tenant": 3,
                "tenant_name": "填色",
                "ip_address": null,
                "user_agent": "",
                "details": {
                    "operation": "extend_license",
                    "license_id": 36,
                    "new_expiry": "2026-03-25T08:03:32.913887+00:00",
                    "days_extended": 30
                },
                "timestamp": "2025-11-25T09:06:16.683784Z"
            },
            {
                "id": 155,
                "event_type": "license_generated",
                "severity": "LOW",
                "user": null,
                "tenant": 3,
                "tenant_name": "填色",
                "ip_address": null,
                "user_agent": "",
                "details": {
                    "plan": "trial",
                    "license_id": 37,
                    "application": "test-create-app",
                    "customer_name": "API测试客户"
                },
                "timestamp": "2025-11-25T09:06:03.306197Z"
            }
        ]
    }
}
```

---

### 2. 获取审计日志详情

#### 请求

```http
GET /api/v1/licenses/admin/audit-logs/{id}/
```

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/audit-logs/157/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

---

## 数据模型

### TenantLicenseQuota 字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | integer | 配额 ID |
| tenant | integer | 租户 ID |
| application | integer | 产品 ID |
| max_licenses | integer | 最大许可证数量 |
| used_licenses | integer | 已使用数量 |
| quota_start_date | date | 配额开始日期 |
| quota_end_date | date | 配额结束日期 |
| is_active | boolean | 是否激活 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### SecurityAuditLog 字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | integer | 日志 ID |
| event_type | string | 事件类型 |
| severity | string | 严重程度 |
| user | integer | 用户 ID |
| user_name | string | 用户名（只读） |
| tenant | integer | 租户 ID |
| tenant_name | string | 租户名称（只读） |
| ip_address | string | IP 地址 |
| user_agent | string | User Agent |
| details | object | 详细信息 JSON |
| timestamp | datetime | 时间戳 |

### 事件类型枚举

| 事件类型 | 说明 |
|---------|------|
| license_generated | 许可证生成 |
| license_activated | 许可证激活 |
| license_revoked | 许可证撤销 |
| license_expired | 许可证过期 |
| data_access | 数据访问 |
| system_change | 系统变更 |
| security_alert | 安全警报 |
| login_attempt | 登录尝试 |

### 严重程度枚举

| 严重程度 | 说明 |
|---------|------|
| LOW | 低 |
| MEDIUM | 中 |
| HIGH | 高 |
| CRITICAL | 严重 |
