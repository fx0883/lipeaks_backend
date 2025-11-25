# 报告与统计 API

## API 列表

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/licenses/status/ | 获取服务状态 |
| GET | /api/v1/licenses/statistics/ | 获取许可证统计 |
| GET | /api/v1/licenses/reports/dashboard/ | 获取仪表板数据 |
| POST | /api/v1/licenses/reports/generate/ | 生成自定义报表 |

---

## 1. 获取服务状态

获取许可证服务的运行状态（无需认证）。

### 请求

```http
GET /api/v1/licenses/status/
```

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/status/"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "status": "healthy",
        "timestamp": "2025-11-25T09:26:09.905025+00:00",
        "services": {
            "database": "ok",
            "cache": "ok"
        },
        "version": "1.0.0"
    }
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| status | string | 服务状态：healthy, degraded, unhealthy |
| timestamp | datetime | 当前时间戳 |
| services.database | string | 数据库状态 |
| services.cache | string | 缓存状态 |
| version | string | 服务版本号 |

---

## 2. 获取许可证统计

获取许可证系统的综合统计数据。

### 请求

```http
GET /api/v1/licenses/statistics/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/statistics/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "success": true,
        "data": {
            "overview": {
                "total_licenses": 2,
                "active_licenses": 0,
                "generated_licenses": 2,
                "suspended_licenses": 0,
                "revoked_licenses": 0,
                "expired_licenses": 0,
                "activation_rate": 0.0
            },
            "products": {
                "total_products": 3,
                "active_products": 2,
                "inactive_products": 0
            },
            "activations": {
                "total_activations": 0,
                "successful_activations": 0,
                "failed_activations": 0,
                "pending_activations": 0,
                "success_rate": 0
            },
            "machines": {
                "total_machines": 0,
                "active_machines": 0,
                "inactive_machines": 0,
                "blocked_machines": 0
            },
            "usage": {
                "total_events": 0,
                "recent_events_24h": 0,
                "heartbeat_events": 0,
                "startup_events": 0
            },
            "time_based": {
                "licenses_this_month": 2,
                "licenses_last_month": 0,
                "activations_today": 0,
                "activations_yesterday": 0
            }
        },
        "generated_at": "2025-11-25T09:26:17.008943+00:00"
    }
}
```

### 响应字段说明

| 字段 | 说明 |
|-----|------|
| overview.total_licenses | 许可证总数 |
| overview.active_licenses | 已激活许可证数 |
| overview.generated_licenses | 已生成许可证数 |
| overview.suspended_licenses | 已暂停许可证数 |
| overview.revoked_licenses | 已撤销许可证数 |
| overview.expired_licenses | 已过期许可证数 |
| overview.activation_rate | 激活率（百分比） |
| products.total_products | 产品总数 |
| products.active_products | 活跃产品数 |
| activations.total_activations | 激活总次数 |
| activations.success_rate | 激活成功率 |
| machines.total_machines | 机器绑定总数 |
| machines.active_machines | 活跃机器数 |
| machines.blocked_machines | 被阻止机器数 |
| usage.recent_events_24h | 24小时内使用事件数 |
| time_based.licenses_this_month | 本月新增许可证数 |
| time_based.activations_today | 今日激活数 |

---

## 3. 获取仪表板数据

获取许可证管理仪表板的摘要数据和趋势图表数据。

### 请求

```http
GET /api/v1/licenses/reports/dashboard/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/reports/dashboard/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "summary": {
            "total_licenses": 2,
            "active_licenses": 0,
            "expiring_soon": 0,
            "today_activations": 0,
            "active_machines": 0
        },
        "trends": {
            "activation_trend": [
                {
                    "date": "2025-11-19",
                    "count": 0
                },
                {
                    "date": "2025-11-20",
                    "count": 0
                },
                {
                    "date": "2025-11-21",
                    "count": 0
                },
                {
                    "date": "2025-11-22",
                    "count": 0
                },
                {
                    "date": "2025-11-23",
                    "count": 0
                },
                {
                    "date": "2025-11-24",
                    "count": 0
                },
                {
                    "date": "2025-11-25",
                    "count": 0
                }
            ]
        },
        "generated_at": "2025-11-25T09:26:21.107094+00:00"
    }
}
```

### 响应字段说明

| 字段 | 说明 |
|-----|------|
| summary.total_licenses | 许可证总数 |
| summary.active_licenses | 已激活许可证数 |
| summary.expiring_soon | 即将过期的许可证数（30天内） |
| summary.today_activations | 今日激活数 |
| summary.active_machines | 活跃机器数 |
| trends.activation_trend | 最近7天激活趋势数据 |

---

## 4. 生成自定义报表

生成指定类型的许可证报表。

### 请求

```http
POST /api/v1/licenses/reports/generate/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token |
| Content-Type | 是 | application/json |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| report_type | string | 是 | 报表类型 |
| start_date | date | 否 | 开始日期 |
| end_date | date | 否 | 结束日期 |
| application_id | integer | 否 | 产品 ID（可选过滤） |

### 报表类型枚举

| 类型 | 说明 |
|-----|------|
| summary | 综合摘要报表 |
| activation | 激活报表 |
| usage | 使用报表 |
| security | 安全报表 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/reports/generate/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "summary"}'
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "success": true,
        "report": {
            "type": "summary",
            "period": {
                "start_date": "2025-10-26",
                "end_date": "2025-11-25"
            },
            "generated_at": "2025-11-25T09:28:25.456471+00:00",
            "data": {
                "licenses": {
                    "total_licenses": 2,
                    "active_licenses": 0,
                    "expired_licenses": 0,
                    "revoked_licenses": 0
                },
                "activations": {
                    "total_activations": 0,
                    "successful_activations": 0,
                    "failed_activations": 0
                },
                "machine_bindings": {
                    "new_machines": 0,
                    "active_machines": 0,
                    "blocked_machines": 0
                },
                "usage": {
                    "total_events": 0,
                    "startup_events": 0,
                    "heartbeat_events": 0
                }
            }
        }
    }
}
```

### 带日期范围的报表请求

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/reports/generate/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "activation",
    "start_date": "2025-11-01",
    "end_date": "2025-11-30",
    "application_id": 6
  }'
```

---

## 使用场景

### 1. 管理仪表板

前端可以调用 `/reports/dashboard/` 获取仪表板所需的核心指标和图表数据。

### 2. 详细统计分析

调用 `/statistics/` 获取更详细的分类统计数据，用于深入分析。

### 3. 定期报表

使用 `/reports/generate/` 生成特定时间段的报表，用于业务分析或导出。

### 4. 健康检查

外部监控系统可以调用 `/status/` 检查服务健康状态。
