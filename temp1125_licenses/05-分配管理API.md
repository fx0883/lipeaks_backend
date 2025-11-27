# 许可证分配管理 API

许可证分配（License Assignment）用于管理许可证与用户/组织之间的分配关系。

## API 列表

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/licenses/admin/assignments/ | 获取分配列表 |
| POST | /api/v1/licenses/admin/assignments/ | 创建分配 |
| GET | /api/v1/licenses/admin/assignments/{id}/ | 获取分配详情 |
| PUT | /api/v1/licenses/admin/assignments/{id}/ | 更新分配 |
| PATCH | /api/v1/licenses/admin/assignments/{id}/ | 部分更新分配 |
| DELETE | /api/v1/licenses/admin/assignments/{id}/ | 删除分配 |
| POST | /api/v1/licenses/admin/assignments/{id}/activate/ | 激活分配 |
| POST | /api/v1/licenses/admin/assignments/{id}/revoke/ | 撤销分配 |
| POST | /api/v1/licenses/admin/assignments/{id}/record_usage/ | 记录使用 |
| GET | /api/v1/licenses/admin/assignments/{id}/permissions/ | 获取权限 |
| GET | /api/v1/licenses/admin/assignments/statistics/ | 获取统计 |
| GET | /api/v1/licenses/admin/assignments/expiring_soon/ | 即将过期 |
| GET | /api/v1/licenses/admin/assignments/my_assignments/ | 我的分配 |
| POST | /api/v1/licenses/admin/assignments/batch_assign/ | 批量分配 |
| POST | /api/v1/licenses/admin/assignments/batch_revoke/ | 批量撤销 |

---

## 1. 获取分配列表

### 请求

```http
GET /api/v1/licenses/admin/assignments/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token |

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |
| license | integer | 否 | 按许可证 ID 过滤 |
| member | integer | 否 | 按会员 ID 过滤 |
| status | string | 否 | 按状态过滤：active, expired, revoked |
| assignment_type | string | 否 | 按类型过滤 |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/assignments/" \
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

## 2. 创建分配

### 请求

```http
POST /api/v1/licenses/admin/assignments/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| license | integer | 是 | 许可证 ID |
| member | integer | 是 | 会员 ID |
| assignment_type | string | 否 | 分配类型：direct, inherited, shared, temporary |
| priority | string | 否 | 优先级：low, normal, high, urgent |
| assigned_features | object | 否 | 分配的功能特性 |
| expires_at | datetime | 否 | 过期时间 |
| notes | string | 否 | 备注 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/assignments/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{
    "license": 36,
    "member": 10,
    "assignment_type": "direct",
    "priority": "normal",
    "notes": "测试分配"
  }'
```

---

## 3. 获取分配统计

### 请求

```http
GET /api/v1/licenses/admin/assignments/statistics/
```

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/assignments/statistics/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "total_assignments": 0,
        "status_distribution": {
            "active": 0,
            "expired": 0,
            "revoked": 0
        },
        "assignment_type_distribution": {
            "direct": 0,
            "inherited": 0,
            "shared": 0,
            "temporary": 0
        },
        "priority_distribution": {
            "low": 0,
            "normal": 0,
            "high": 0,
            "urgent": 0
        },
        "usage_statistics": {
            "total_usage_count": 0,
            "active_in_last_30_days": 0,
            "never_used": 0
        }
    }
}
```

---

## 4. 获取即将过期的分配

### 请求

```http
GET /api/v1/licenses/admin/assignments/expiring_soon/
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| days | integer | 否 | 天数范围，默认 30 |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/assignments/expiring_soon/?days=30" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "count": 0,
        "days": 30,
        "expiring_assignments": []
    }
}
```

---

## 5. 激活分配

### 请求

```http
POST /api/v1/licenses/admin/assignments/{id}/activate/
```

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/assignments/1/activate/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json"
```

---

## 6. 撤销分配

### 请求

```http
POST /api/v1/licenses/admin/assignments/{id}/revoke/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| reason | string | 否 | 撤销原因 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/assignments/1/revoke/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{"reason": "用户请求"}'
```

---

## 7. 记录使用

### 请求

```http
POST /api/v1/licenses/admin/assignments/{id}/record_usage/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| feature | string | 否 | 使用的功能 |
| metadata | object | 否 | 额外元数据 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/assignments/1/record_usage/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{"feature": "export", "metadata": {"count": 10}}'
```

---

## 8. 批量分配

### 请求

```http
POST /api/v1/licenses/admin/assignments/batch_assign/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| license_id | integer | 是 | 许可证 ID |
| member_ids | array | 是 | 会员 ID 列表 |
| assignment_type | string | 否 | 分配类型 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/assignments/batch_assign/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{
    "license_id": 36,
    "member_ids": [10, 11, 12],
    "assignment_type": "direct"
  }'
```

---

## 9. 批量撤销

### 请求

```http
POST /api/v1/licenses/admin/assignments/batch_revoke/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| assignment_ids | array | 是 | 分配 ID 列表 |
| reason | string | 否 | 撤销原因 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/assignments/batch_revoke/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{
    "assignment_ids": [1, 2, 3],
    "reason": "批量撤销"
  }'
```

---

## 数据模型

### Assignment 状态枚举

| 状态 | 说明 |
|-----|------|
| active | 激活 |
| expired | 已过期 |
| revoked | 已撤销 |

### Assignment 类型枚举

| 类型 | 说明 |
|-----|------|
| direct | 直接分配 |
| inherited | 继承分配 |
| shared | 共享分配 |
| temporary | 临时分配 |

### Priority 优先级枚举

| 优先级 | 说明 |
|-------|------|
| low | 低 |
| normal | 普通 |
| high | 高 |
| urgent | 紧急 |
