# API参考文档

## 概述

本文档详细说明了许可证激活系统的所有客户端API，包括请求参数、响应格式、错误代码等。

## 通用规则

### 基础URL

```
生产环境: https://your-license-server.com/api/v1/licenses/
测试环境: https://test-license-server.com/api/v1/licenses/
```

### 通用请求头

所有API请求都必须包含以下请求头：

```
Content-Type: application/json
X-Tenant-ID: <租户ID>
```

**X-Tenant-ID 说明：**
- 必需参数，用于租户隔离
- 格式：数字字符串（如："123"）
- 获取方式：由系统管理员提供或通过管理API获取

### 通用响应格式

**成功响应格式：**
```json
{
    "success": true,
    "message": "操作成功信息",
    "data": {
        // 具体的响应数据
    }
}
```

**错误响应格式：**
```json
{
    "success": false,
    "error": "错误描述信息",
    "code": "ERROR_CODE",
    "details": {
        // 详细错误信息（可选）
    }
}
```

### HTTP状态码

- `200` - 成功
- `400` - 请求参数错误
- `401` - 认证失败
- `403` - 权限不足或可疑活动
- `404` - 资源未找到
- `429` - 请求频率限制
- `500` - 服务器内部错误
- `503` - 服务不可用

## API详细说明

### 1. 获取许可证信息

**用途：** 获取许可证的基本信息，用于激活前的验证

**端点：** `GET /info/<license_key>/`

**参数：**
- `license_key` (路径参数): 许可证密钥

**请求示例：**
```
GET /api/v1/licenses/info/7C162-2DC76-F944D-D9AA4-F408E/
X-Tenant-ID: 123
```

**⚠️ 重要说明：** 此API不需要Bearer Token认证，但**必须**提供正确的租户ID头部。

**成功响应 (200)：**
```json
{
    "success": true,
    "license_info": {
        "product": {
            "name": "MyProduct",
            "version": "1.0.2"
        },
        "plan": {
            "name": "Professional",
            "type": "professional",
            "default_max_activations": 10
        },
        "status": "issued",
        "issued_at": "2024-01-01T00:00:00Z",
        "expires_at": "2024-12-31T23:59:59Z",
        "max_activations": 10
    }
}
```

**错误响应：**

**404 - 许可证未找到：**
```json
{
    "success": false,
    "error": "License not found"
}
```

**400 - 密钥格式错误：**
```json
{
    "success": false,
    "error": "Invalid license key format"
}
```

---

### 2. 激活许可证

**用途：** 激活许可证并绑定到当前机器

**端点：** `POST /activate/`

**请求头：**
```
Content-Type: application/json
X-Tenant-ID: <租户ID>
```

**请求参数：**

| 参数 | 类型 | 必需 | 说明 |
|-----|-----|------|-----|
| license_key | string | 是 | 许可证密钥 |
| hardware_info | object | 是 | 硬件信息对象 |
| client_info | object | 否 | 客户端信息 |

**hardware_info 对象结构：**

```json
{
    "hardware_uuid": "12345678-1234-1234-1234-123456789012",
    "cpu_info": {
        "processor": "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz",
        "cores": 6,
        "threads": 12,
        "architecture": "x86_64",
        "serial": "CPU001234567890"  // 可选
    },
    "memory_info": {
        "total": 17179869184,  // 总内存字节数
        "serial": "MEM001234567890"  // 内存条序列号
    },
    "disk_info": {
        "total": 512000000000,  // 总磁盘空间字节数
        "serial": "DISK001234567890"  // 磁盘序列号
    },
    "network_info": {
        "interfaces": ["eth0", "wlan0"],  // 网络接口列表
        "mac_addresses": ["00:11:22:33:44:55", "66:77:88:99:AA:BB"]
    },
    "system_info": {
        "os_version": "Windows 10 Pro",
        "kernel_version": "10.0.19041",
        "hostname": "USER-DESKTOP"
    }
}
```

**client_info 对象结构（可选）：**

```json
{
    "version": "1.0.0",          // 软件版本
    "build": "20240115",         // 构建版本
    "language": "zh-CN",         // 界面语言
    "user_id": "user123"         // 用户标识（可选）
}
```

**完整请求示例：**
```json
{
    "license_key": "7C162-2DC76-F944D-D9AA4-F408E",
    "hardware_info": {
        "hardware_uuid": "12345678-1234-1234-1234-123456789012",
        "cpu_info": {
            "processor": "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz",
            "cores": 6,
            "threads": 12,
            "architecture": "x86_64"
        },
        "memory_info": {
            "total": 17179869184,
            "serial": "MEM001234567890"
        },
        "disk_info": {
            "total": 512000000000,
            "serial": "DISK001234567890"
        },
        "network_info": {
            "interfaces": ["eth0", "wlan0"],
            "mac_addresses": ["00:11:22:33:44:55"]
        },
        "system_info": {
            "os_version": "Windows 10 Pro",
            "kernel_version": "10.0.19041",
            "hostname": "USER-DESKTOP"
        }
    },
    "client_info": {
        "version": "1.0.0",
        "build": "20240115"
    }
}
```

**成功响应 (200)：**
```json
{
    "success": true,
    "message": "License activated successfully",
    "data": {
        "activation_code": "ACT-12345678-ABCD-EFGH",
        "machine_id": "MACHINE-ID-12345",
        "expires_at": "2024-12-31T23:59:59Z",
        "features": {
            "advanced_features": true,
            "export_function": true,
            "cloud_sync": false,
            "max_projects": 100
        }
    }
}
```

**错误响应：**

**400 - 许可证已过期：**
```json
{
    "success": false,
    "error": "License has expired",
    "code": "LICENSE_EXPIRED"
}
```

**400 - 达到最大激活数：**
```json
{
    "success": false,
    "error": "Maximum activations (5) reached",
    "code": "MAX_ACTIVATIONS_REACHED"
}
```

**400 - 许可证已撤销：**
```json
{
    "success": false,
    "error": "License has been revoked",
    "code": "LICENSE_REVOKED"
}
```

**403 - 可疑活动：**
```json
{
    "success": false,
    "error": "Activation request flagged for review",
    "code": "SUSPICIOUS_ACTIVITY"
}
```

**429 - 频率限制：**
```json
{
    "success": false,
    "error": "Too many activation attempts. Please try again later.",
    "code": "RATE_LIMITED"
}
```

---

### 3. 验证激活状态

**用途：** 验证已激活许可证的状态

**端点：** `POST /verify/`

**请求头：**
```
Content-Type: application/json
X-Tenant-ID: <租户ID>
```

**请求参数：**

| 参数 | 类型 | 必需 | 说明 |
|-----|-----|------|-----|
| activation_code | string | 是 | 激活码 |
| machine_fingerprint | string | 是 | 机器指纹 |

**请求示例：**
```json
{
    "activation_code": "ACT-12345678-ABCD-EFGH",
    "machine_fingerprint": "abc123def456ghi789jkl012mno345pqr"
}
```

**成功响应 (200)：**
```json
{
    "valid": true,
    "license_info": {
        "product": "MyProduct 1.0",
        "plan": "Professional",
        "expires_at": "2024-12-31T23:59:59Z",
        "features": {
            "advanced_features": true,
            "export_function": true,
            "cloud_sync": false
        }
    },
    "last_verified": "2024-01-15T10:30:00Z"
}
```

**错误响应：**

**400 - 激活码无效：**
```json
{
    "valid": false,
    "error": "Invalid activation code",
    "code": "INVALID_ACTIVATION"
}
```

**400 - 机器指纹不匹配：**
```json
{
    "valid": false,
    "error": "Machine fingerprint mismatch",
    "code": "FINGERPRINT_MISMATCH"
}
```

---

### 4. 心跳检测

**用途：** 发送软件使用状态的心跳信号

**端点：** `POST /heartbeat/`

**请求头：**
```
Content-Type: application/json
X-Tenant-ID: <租户ID>
```

**请求参数：**

| 参数 | 类型 | 必需 | 说明 |
|-----|-----|------|-----|
| activation_code | string | 是 | 激活码 |
| event_type | string | 是 | 事件类型 |
| event_data | object | 否 | 事件数据 |
| software_version | string | 否 | 软件版本 |
| session_id | string | 否 | 会话ID |
| system_status | object | 否 | 系统状态信息 |

**event_type 可选值：**
- `startup` - 软件启动
- `heartbeat` - 心跳检测
- `feature_use` - 功能使用
- `shutdown` - 软件关闭
- `verification` - 在线验证

**请求示例：**
```json
{
    "activation_code": "ACT-12345678-ABCD-EFGH",
    "event_type": "heartbeat",
    "event_data": {
        "active_features": ["advanced_features", "export_function"],
        "usage_stats": {
            "projects_created": 5,
            "exports_performed": 12
        }
    },
    "software_version": "1.0.0",
    "session_id": "SESSION-12345678",
    "system_status": {
        "cpu_usage": 25.5,
        "memory_usage": 68.2,
        "uptime": 7200
    }
}
```

**成功响应 (200)：**
```json
{
    "success": true,
    "message": "Heartbeat recorded",
    "license_status": {
        "status": "activated",
        "expires_at": "2024-12-31T23:59:59Z",
        "days_until_expiry": 180
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "warnings": [
        "License will expire in 30 days"
    ]
}
```

**错误响应：**

**400 - 激活码无效：**
```json
{
    "success": false,
    "error": "Invalid activation code",
    "code": "INVALID_ACTIVATION"
}
```

**400 - 许可证非活跃状态：**
```json
{
    "success": false,
    "error": "License is suspended",
    "code": "LICENSE_INACTIVE"
}
```

---

### 5. 服务器状态检查

**用途：** 检查许可证服务器的运行状态

**端点：** `GET /status/`

**请求头：**
```
X-Tenant-ID: <租户ID>
```

**请求示例：**
```
GET /api/v1/licenses/status/
X-Tenant-ID: 123
```

**成功响应 (200)：**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "services": {
        "database": "ok",
        "cache": "ok"
    },
    "version": "1.0.0"
}
```

**错误响应 (503)：**
```json
{
    "status": "unhealthy",
    "error": "Database connection failed",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## 实现建议

### 1. 机器指纹生成

机器指纹应该基于收集到的硬件信息生成，建议实现：

```
// 伪代码
function generateMachineFingerprint(hardwareInfo) {
    // 提取关键硬件信息
    key_data = {
        cpu_serial: hardwareInfo.cpu_info.serial,
        memory_serial: hardwareInfo.memory_info.serial,
        disk_serial: hardwareInfo.disk_info.serial,
        mac_address: hardwareInfo.network_info.mac_addresses[0]
    }
    
    // 使用SHA256生成指纹
    fingerprint = SHA256(JSON.stringify(key_data))
    return fingerprint.substring(0, 32)  // 取前32位
}
```

### 2. 错误处理建议

**网络错误：**
```json
{
    "success": false,
    "error": "Network connection failed",
    "code": "NETWORK_ERROR",
    "retry_after": 300  // 建议重试间隔（秒）
}
```

**服务器维护：**
```json
{
    "success": false,
    "error": "Server is under maintenance",
    "code": "MAINTENANCE_MODE",
    "estimated_completion": "2024-01-15T12:00:00Z"
}
```

### 3. 缓存策略

**验证结果缓存：**
- 缓存时间：5分钟
- 缓存键：`activation_verify:{activation_code}:{machine_fingerprint_hash}`

**服务器状态缓存：**
- 缓存时间：30秒
- 用于减少健康检查频率

### 4. 安全建议

1. **HTTPS通信：** 所有API调用必须使用HTTPS
2. **证书验证：** 验证服务器SSL证书
3. **请求签名：** 可选择对请求进行数字签名
4. **敏感信息保护：** 不在日志中记录完整的许可证密钥或激活码

---

**下一步：** 查看 [激活场景文档](./activation_scenarios.md) 了解不同使用场景的处理方式
