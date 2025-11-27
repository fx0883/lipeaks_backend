# 会员许可证 API

这些 API 供会员用户使用，用于申请试用许可证、查看自己的许可证和管理设备绑定。

## 认证说明

会员 API 需要：
1. **会员 Token**：在 Authorization 头中提供
2. **租户 ID**：在 X-Tenant-ID 头中提供

## API 列表

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/licenses/member/available-products/ | 获取可申请试用的产品 |
| POST | /api/v1/licenses/member/apply/ | 申请试用许可证 |
| GET | /api/v1/licenses/member/my-licenses/ | 查看我的许可证 |
| DELETE | /api/v1/licenses/member/my-licenses/{license_id}/ | 删除我的许可证 |
| GET | /api/v1/licenses/member/my-licenses/{license_id}/devices/ | 查看许可证的设备 |
| POST | /api/v1/licenses/member/unbind-device/ | 解绑设备 |

---

## 1. 获取可申请试用的产品

获取当前租户下可以申请试用的产品列表。

### 请求

```http
GET /api/v1/licenses/member/available-products/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token（会员） |
| X-Tenant-ID | 是 | 租户 ID |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/member/available-products/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NjYwOTUwLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.VQmBQI5C-zWSgzyBrY5XaG0IXflUlve2xpH7uT4I2hk" \
  -H "X-Tenant-ID: 3"
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
            "count": 2,
            "products": [
                {
                    "id": 6,
                    "name": "填色花园",
                    "code": "test-create-app",
                    "description": "填色花园",
                    "current_version": "1.0.0",
                    "trial_plan": {
                        "id": 19,
                        "name": "试用版",
                        "validity_days": 30,
                        "max_activations": 1,
                        "features": {
                            "basic": true
                        }
                    },
                    "already_has_license": false
                }
            ]
        }
    }
}
```

### 响应字段说明

| 字段 | 说明 |
|-----|------|
| count | 可申请产品数量 |
| products[].id | 产品 ID |
| products[].name | 产品名称 |
| products[].trial_plan | 试用方案信息 |
| products[].already_has_license | 是否已有该产品的许可证 |

---

## 2. 申请试用许可证

会员申请某个产品的试用许可证。

### 请求

```http
POST /api/v1/licenses/member/apply/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token（会员） |
| X-Tenant-ID | 是 | 租户 ID |
| Content-Type | 是 | application/json |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| application_id | integer | 是 | 产品 ID |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/member/apply/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NjYwOTUwLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.VQmBQI5C-zWSgzyBrY5XaG0IXflUlve2xpH7uT4I2hk" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"application_id": 6}'
```

### 成功响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "试用许可证申请成功",
    "data": {
        "success": true,
        "data": {
            "license_key": "TRIAL-xxxx-xxxx-xxxx",
            "product_name": "填色花园",
            "plan_name": "试用版",
            "expires_at": "2025-12-25T10:00:00.000000+00:00",
            "max_activations": 1,
            "features": {
                "basic": true
            }
        }
    }
}
```

### 可能的错误

| 错误码 | 说明 |
|-------|------|
| PRODUCT_NOT_FOUND | 产品不存在 |
| NO_TRIAL_PLAN | 该产品没有试用方案 |
| ALREADY_HAS_LICENSE | 已有该产品的许可证 |
| TRIAL_LIMIT_REACHED | 已达到试用限制 |

---

## 3. 查看我的许可证

获取当前会员拥有的所有许可证。

### 请求

```http
GET /api/v1/licenses/member/my-licenses/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Authorization | 是 | Bearer Token（会员） |
| X-Tenant-ID | 是 | 租户 ID |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/member/my-licenses/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NjYwOTUwLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.VQmBQI5C-zWSgzyBrY5XaG0IXflUlve2xpH7uT4I2hk" \
  -H "X-Tenant-ID: 3"
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
            "count": 1,
            "active_count": 1,
            "trial_count": 1,
            "expiring_soon_count": 0,
            "licenses": [
                {
                    "id": 40,
                    "license_key": "TRIAL-xxxx-xxxx-xxxx",
                    "product": {
                        "id": 6,
                        "name": "填色花园",
                        "code": "test-create-app"
                    },
                    "plan": {
                        "id": 19,
                        "name": "试用版",
                        "type": "trial"
                    },
                    "status": "active",
                    "issued_at": "2025-11-25T10:00:00.000000+00:00",
                    "expires_at": "2025-12-25T10:00:00.000000+00:00",
                    "days_until_expiry": 30,
                    "max_activations": 1,
                    "current_activations": 1,
                    "features": {
                        "basic": true
                    }
                }
            ]
        }
    }
}
```

### 响应字段说明

| 字段 | 说明 |
|-----|------|
| count | 许可证总数 |
| active_count | 活跃许可证数 |
| trial_count | 试用许可证数 |
| expiring_soon_count | 即将过期数（30天内） |
| licenses[].days_until_expiry | 距离过期天数 |

---

## 4. 删除我的许可证

删除自己的某个许可证（仅限试用许可证）。

### 请求

```http
DELETE /api/v1/licenses/member/my-licenses/{license_id}/
```

### 路径参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| license_id | integer | 许可证 ID |

### curl 示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/licenses/member/my-licenses/40/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NjYwOTUwLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.VQmBQI5C-zWSgzyBrY5XaG0IXflUlve2xpH7uT4I2hk" \
  -H "X-Tenant-ID: 3"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "许可证已删除",
    "data": null
}
```

---

## 5. 查看许可证的设备

查看某个许可证绑定的所有设备。

### 请求

```http
GET /api/v1/licenses/member/my-licenses/{license_id}/devices/
```

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/member/my-licenses/40/devices/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NjYwOTUwLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.VQmBQI5C-zWSgzyBrY5XaG0IXflUlve2xpH7uT4I2hk" \
  -H "X-Tenant-ID: 3"
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
            "license_id": 40,
            "max_devices": 1,
            "current_devices": 1,
            "devices": [
                {
                    "id": 1,
                    "machine_id": "MACH-xxxx",
                    "hostname": "user-pc",
                    "os_version": "Windows 11",
                    "status": "active",
                    "first_seen_at": "2025-11-25T10:00:00.000000+00:00",
                    "last_seen_at": "2025-11-25T12:00:00.000000+00:00"
                }
            ]
        }
    }
}
```

---

## 6. 解绑设备

从自己的许可证中解绑某个设备。

### 请求

```http
POST /api/v1/licenses/member/unbind-device/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| license_id | integer | 是 | 许可证 ID |
| device_id | integer | 是 | 设备（机器绑定）ID |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/member/unbind-device/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NjYwOTUwLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.VQmBQI5C-zWSgzyBrY5XaG0IXflUlve2xpH7uT4I2hk" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "license_id": 40,
    "device_id": 1
  }'
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "设备已解绑",
    "data": {
        "success": true,
        "data": {
            "unbound_at": "2025-11-25T12:30:00.000000+00:00",
            "remaining_devices": 0,
            "max_devices": 1
        }
    }
}
```

---

## 使用场景

### 1. 会员中心 - 许可证管理

```
1. 调用 /my-licenses/ 显示用户的所有许可证
2. 显示每个许可证的状态、有效期、激活数等信息
3. 提供"查看设备"按钮，调用 /my-licenses/{id}/devices/
4. 提供"解绑设备"功能，调用 /unbind-device/
```

### 2. 产品试用申请

```
1. 调用 /available-products/ 获取可试用产品
2. 显示产品列表，标注已有许可证的产品
3. 用户点击"申请试用"，调用 /apply/
4. 显示生成的许可证密钥
```

### 3. 设备管理

```
1. 用户查看某个许可证的设备列表
2. 显示设备信息（主机名、系统、最后活动时间）
3. 允许用户解绑不再使用的设备
4. 解绑后可在新设备上激活
```
