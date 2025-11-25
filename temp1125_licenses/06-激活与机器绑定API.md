# 激活记录与机器绑定管理 API

## 一、激活记录 API

管理许可证的激活记录。

### API 列表

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/licenses/admin/activations/ | 获取激活记录列表 |
| GET | /api/v1/licenses/admin/activations/{id}/ | 获取激活记录详情 |

---

### 1. 获取激活记录列表

#### 请求

```http
GET /api/v1/licenses/admin/activations/
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
| license | integer | 否 | 按许可证 ID 过滤 |
| status | string | 否 | 按状态过滤：success, failed, pending |
| ordering | string | 否 | 排序字段 |

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/activations/" \
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

### 2. 获取激活记录详情

#### 请求

```http
GET /api/v1/licenses/admin/activations/{id}/
```

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/activations/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

---

## 二、机器绑定 API

管理许可证与机器的绑定关系。

### API 列表

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/licenses/admin/machine-bindings/ | 获取机器绑定列表 |
| GET | /api/v1/licenses/admin/machine-bindings/{id}/ | 获取机器绑定详情 |
| POST | /api/v1/licenses/admin/machine-bindings/{id}/block/ | 阻止机器绑定 |

---

### 1. 获取机器绑定列表

#### 请求

```http
GET /api/v1/licenses/admin/machine-bindings/
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
| license | integer | 否 | 按许可证 ID 过滤 |
| status | string | 否 | 按状态过滤：active, inactive, blocked |
| ordering | string | 否 | 排序字段 |

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/machine-bindings/" \
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

### 2. 获取机器绑定详情

#### 请求

```http
GET /api/v1/licenses/admin/machine-bindings/{id}/
```

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/admin/machine-bindings/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY"
```

---

### 3. 阻止机器绑定

阻止特定机器使用许可证。

#### 请求

```http
POST /api/v1/licenses/admin/machine-bindings/{id}/block/
```

#### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| reason | string | 否 | 阻止原因 |

#### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/admin/machine-bindings/1/block/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY2MTU1NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.ZjP5hrGG9H4MJV-1oOhO3m_HaMO0NvwHN7cUKlLi5nY" \
  -H "Content-Type: application/json" \
  -d '{"reason": "检测到异常使用"}'
```

#### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "机器已被阻止",
    "data": {
        "id": 1,
        "status": "blocked",
        "blocked_at": "2025-11-25T10:00:00.000000+00:00"
    }
}
```

---

## 数据模型

### LicenseActivation 字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | integer | 激活记录 ID |
| license | integer | 许可证 ID |
| activation_code | string | 激活码 |
| machine_fingerprint | string | 机器指纹 |
| status | string | 状态：success, failed, pending |
| ip_address | string | IP 地址 |
| activated_at | datetime | 激活时间 |
| expires_at | datetime | 过期时间 |
| error_message | string | 错误信息（失败时） |

### MachineBinding 字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | integer | 机器绑定 ID |
| license | integer | 许可证 ID |
| machine_id | string | 机器 ID |
| machine_fingerprint | string | 机器指纹 |
| hardware_info | object | 硬件信息 |
| status | string | 状态：active, inactive, blocked |
| first_seen_at | datetime | 首次绑定时间 |
| last_seen_at | datetime | 最后活动时间 |
| blocked_at | datetime | 阻止时间 |
| block_reason | string | 阻止原因 |

### MachineBinding 状态枚举

| 状态 | 说明 |
|-----|------|
| active | 活跃 |
| inactive | 不活跃 |
| blocked | 已阻止 |

### hardware_info JSON 示例

```json
{
    "system_info": {
        "hostname": "user-pc",
        "os_version": "Windows 11",
        "platform": "Windows"
    },
    "cpu_info": {
        "processor": "Intel i7-12700",
        "cores": 12
    },
    "disk_info": {
        "serial": "disk-serial-12345"
    },
    "hardware_uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```
