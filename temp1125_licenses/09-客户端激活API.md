# 客户端激活 API

这些 API 供客户端软件调用，用于许可证激活、验证和心跳等操作。**无需认证**，但有速率限制和防滥用检测。

## API 列表

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | /api/v1/licenses/activate/ | 激活许可证 |
| POST | /api/v1/licenses/verify/ | 验证激活状态 |
| POST | /api/v1/licenses/heartbeat/ | 发送心跳 |
| POST | /api/v1/licenses/unbind/ | 解绑许可证 |
| GET | /api/v1/licenses/info/{license_key}/ | 获取许可证信息 |

---

## 1. 激活许可证

客户端软件使用许可证密钥和硬件信息进行激活。

### 请求

```http
POST /api/v1/licenses/activate/
```

### 请求头

| 名称 | 必填 | 说明 |
|-----|------|------|
| Content-Type | 是 | application/json |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| license_key | string | 是 | 许可证密钥 |
| hardware_info | object | 是 | 硬件信息 |
| hardware_info.hardware_uuid | string | 是 | 硬件唯一标识 |
| hardware_info.system_info | object | 否 | 系统信息 |
| hardware_info.cpu_info | object | 否 | CPU 信息 |
| hardware_info.disk_info | object | 否 | 磁盘信息 |

### hardware_info 结构示例

```json
{
    "hardware_uuid": "550e8400-e29b-41d4-a716-446655440000",
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
    }
}
```

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/activate/" \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "8CDAF-05248-584DE-BA4CA-0A57D",
    "hardware_info": {
      "hardware_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "system_info": {
        "hostname": "test-pc",
        "os_version": "Windows 11"
      },
      "cpu_info": {
        "processor": "Intel i7-12700"
      },
      "disk_info": {
        "serial": "disk-12345"
      }
    }
  }'
```

### 成功响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "License activated successfully",
    "data": {
        "activation_code": "ACT-xxxx-xxxx-xxxx",
        "machine_id": "MACH-xxxx",
        "expires_at": "2026-03-25T08:03:32.913887+00:00",
        "features": {
            "basic": true
        }
    }
}
```

### 错误响应示例

```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "success": false,
        "errors": {
            "hardware_info": [
                "Hardware information missing required field: hardware_uuid"
            ]
        }
    }
}
```

### 可能的错误

| 错误码 | 说明 |
|-------|------|
| LICENSE_NOT_FOUND | 许可证不存在 |
| LICENSE_EXPIRED | 许可证已过期 |
| LICENSE_REVOKED | 许可证已被撤销 |
| MAX_ACTIVATIONS_REACHED | 已达到最大激活数 |
| HARDWARE_INFO_INVALID | 硬件信息无效 |

---

## 2. 验证激活状态

客户端定期验证激活状态是否有效。

### 请求

```http
POST /api/v1/licenses/verify/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| activation_code | string | 是 | 激活码 |
| machine_fingerprint | string | 否 | 机器指纹（用于额外验证） |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/verify/" \
  -H "Content-Type: application/json" \
  -d '{
    "activation_code": "ACT-xxxx-xxxx-xxxx",
    "machine_fingerprint": "fingerprint-hash"
  }'
```

### 成功响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "验证成功",
    "data": {
        "valid": true,
        "license_info": {
            "license_key": "8CDAF-05248-584DE-BA4CA-0A57D",
            "status": "active",
            "expires_at": "2026-03-25T08:03:32.913887+00:00",
            "features": {
                "basic": true
            }
        },
        "last_verified_at": "2025-11-25T10:00:00.000000+00:00"
    }
}
```

### 失败响应示例

```json
{
    "success": false,
    "code": "ACTIVATION_NOT_FOUND",
    "message": "请求参数错误",
    "data": {
        "valid": false,
        "error": "Activation not found",
        "code": "ACTIVATION_NOT_FOUND"
    }
}
```

---

## 3. 发送心跳

客户端定期发送心跳以报告活动状态。

### 请求

```http
POST /api/v1/licenses/heartbeat/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| activation_code | string | 是 | 激活码 |
| event_type | string | 否 | 事件类型：heartbeat, startup, shutdown |
| metadata | object | 否 | 额外元数据 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/heartbeat/" \
  -H "Content-Type: application/json" \
  -d '{
    "activation_code": "ACT-xxxx-xxxx-xxxx",
    "event_type": "heartbeat"
  }'
```

### 成功响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "Heartbeat recorded",
    "data": {
        "status": "active",
        "expires_at": "2026-03-25T08:03:32.913887+00:00",
        "expiry_warning": null
    }
}
```

### 过期警告响应

```json
{
    "success": true,
    "code": 2000,
    "message": "Heartbeat recorded",
    "data": {
        "status": "active",
        "expires_at": "2025-12-01T00:00:00.000000+00:00",
        "expiry_warning": "License expires in 5 days"
    }
}
```

### 错误响应示例

```json
{
    "success": false,
    "code": "INVALID_ACTIVATION",
    "message": "请求参数错误",
    "data": {
        "success": false,
        "error": "Invalid activation code",
        "code": "INVALID_ACTIVATION"
    }
}
```

---

## 4. 解绑许可证

从当前机器解绑许可证，释放激活配额。

### 请求

```http
POST /api/v1/licenses/unbind/
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| license_key | string | 是 | 许可证密钥 |
| activation_code | string | 是 | 激活码 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/unbind/" \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "8CDAF-05248-584DE-BA4CA-0A57D",
    "activation_code": "ACT-xxxx-xxxx-xxxx"
  }'
```

### 成功响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "License unbound successfully",
    "data": {
        "unbound_at": "2025-11-25T10:00:00.000000+00:00",
        "remaining_activations": 2
    }
}
```

---

## 5. 获取许可证信息

通过许可证密钥获取基本信息（不需要激活）。

### 请求

```http
GET /api/v1/licenses/info/{license_key}/
```

### 路径参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| license_key | string | 许可证密钥 |

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/info/8CDAF-05248-584DE-BA4CA-0A57D/"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "license_info": {
            "product_name": "填色花园",
            "product_code": "test-create-app",
            "plan_name": "试用版",
            "plan_type": "trial",
            "status": "generated",
            "issued_at": "2025-11-25T08:03:32.963383+00:00",
            "expires_at": "2026-03-25T08:03:32.913887+00:00",
            "max_activations": 3,
            "current_activations": 0,
            "features": {
                "basic": true
            }
        }
    }
}
```

---

## 速率限制

| API | 限制 |
|-----|------|
| /activate/ | 10 次/分钟/IP |
| /verify/ | 60 次/分钟/IP |
| /heartbeat/ | 120 次/分钟/IP |
| /unbind/ | 5 次/分钟/IP |
| /info/ | 30 次/分钟/IP |

超出速率限制将返回 429 Too Many Requests 错误。

---

## 安全说明

1. **防滥用检测**：系统会检测异常激活行为，如短时间内大量激活尝试
2. **IP 记录**：所有激活请求会记录 IP 地址
3. **硬件指纹**：使用硬件信息生成唯一指纹，防止许可证滥用
4. **激活码安全**：激活码应由客户端安全存储，不应明文传输或存储

---

## 客户端集成建议

### 1. 激活流程

```
1. 用户输入许可证密钥
2. 收集硬件信息（包含 hardware_uuid）
3. 调用 /activate/ API
4. 保存返回的 activation_code
5. 定期调用 /heartbeat/ 保持活跃
```

### 2. 启动验证流程

```
1. 读取保存的 activation_code
2. 调用 /verify/ API
3. 如果有效，允许软件运行
4. 如果无效，提示用户重新激活
```

### 3. 心跳间隔建议

- **正常使用**：每 30 分钟发送一次心跳
- **活跃使用**：每 15 分钟发送一次心跳
- **后台运行**：每 60 分钟发送一次心跳
