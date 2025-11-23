# 客户端激活API文档

## 概述

客户端激活API是公开API，用于软件客户端激活许可证、验证状态、发送心跳等操作。这些API不需要JWT认证，使用许可证密钥和硬件信息进行验证。

**⚠️ 安全提示**: 这些API有频率限制以防止滥用

## API列表

### 1. 激活许可证

**接口**: `POST /api/v1/licenses/activate/`

**权限**: 公开（无需认证）

**描述**: 客户端首次激活许可证，绑定硬件信息

**请求体**:
```json
{
  "license_key": "6260D-4913D-64411-2A7A4-3321B",
  "hardware_info": {
    "system_info": {
      "os_type": "Windows",
      "os_version": "Windows 11 Pro",
      "hostname": "DESKTOP-ABC123",
      "username": "zhangsan"
    },
    "cpu_info": {
      "processor_id": "BFEBFBFF000906EA",
      "cores": 8,
      "model": "Intel Core i7-9700K"
    },
    "disk_info": {
      "serial_number": "1234567890ABCDEF",
      "total_gb": 512
    },
    "network_info": {
      "mac_addresses": ["00:1A:2B:3C:4D:5E"]
    }
  },
  "client_info": {
    "version": "2.1.0",
    "build": "2024.11.23"
  }
}
```

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/activate/" \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "6260D-4913D-64411-2A7A4-3321B",
    "hardware_info": {
      "system_info": {
        "os_type": "Windows",
        "os_version": "Windows 11 Pro",
        "hostname": "DESKTOP-TEST"
      },
      "cpu_info": {
        "processor_id": "BFEBFBFF000906EA"
      },
      "disk_info": {
        "serial_number": "SSD123456"
      },
      "network_info": {
        "mac_addresses": ["00:1A:2B:3C:4D:5E"]
      }
    },
    "client_info": {
      "version": "2.0.0"
    }
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "License activated successfully",
  "data": {
    "activation_code": "ACT-A1B2C3D4-E5F6-G7H8",
    "machine_id": "MACHINE-XYZ789",
    "expires_at": "2026-11-23T14:30:00Z",
    "features": {
      "max_users": 5,
      "storage_gb": 10,
      "api_calls_per_day": 1000
    }
  }
}
```

**错误响应**:

**400 - 许可证无效**:
```json
{
  "success": false,
  "error": "License key is invalid or expired",
  "code": "INVALID_LICENSE"
}
```

**400 - 激活配额已满**:
```json
{
  "success": false,
  "error": "License activation limit reached",
  "code": "ACTIVATION_LIMIT_EXCEEDED"
}
```

**403 - 可疑活动**:
```json
{
  "success": false,
  "error": "Activation request flagged for review",
  "code": "SUSPICIOUS_ACTIVITY"
}
```

**429 - 频率限制**:
```json
{
  "success": false,
  "error": "Too many activation attempts. Please try again later.",
  "code": "RATE_LIMITED"
}
```

---

### 2. 验证激活状态

**接口**: `POST /api/v1/licenses/verify/`

**权限**: 公开

**描述**: 验证激活码的有效性，不更新最后验证时间

**请求体**:
```json
{
  "activation_code": "ACT-A1B2C3D4-E5F6-G7H8",
  "license_key": "6260D-4913D-64411-2A7A4-3321B"
}
```

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/verify/" \
  -H "Content-Type: application/json" \
  -d '{
    "activation_code": "ACT-A1B2C3D4-E5F6-G7H8",
    "license_key": "6260D-4913D-64411-2A7A4-3321B"
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Activation is valid",
  "data": {
    "valid": true,
    "expires_at": "2026-11-23T14:30:00Z",
    "days_remaining": 365,
    "status": "active"
  }
}
```

**失败响应** (200 OK - 验证失败但请求成功):
```json
{
  "success": true,
  "message": "Activation verification failed",
  "data": {
    "valid": false,
    "reason": "Activation code expired"
  }
}
```

---

### 3. 心跳检测

**接口**: `POST /api/v1/licenses/heartbeat/`

**权限**: 公开

**描述**: 定期发送心跳，更新最后验证时间，上报使用数据

**请求体**:
```json
{
  "activation_code": "ACT-A1B2C3D4-E5F6-G7H8",
  "license_key": "6260D-4913D-64411-2A7A4-3321B",
  "usage_data": {
    "session_id": "SESSION-123456",
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "uptime_seconds": 86400
  }
}
```

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/heartbeat/" \
  -H "Content-Type: application/json" \
  -d '{
    "activation_code": "ACT-A1B2C3D4-E5F6-G7H8",
    "license_key": "6260D-4913D-64411-2A7A4-3321B",
    "usage_data": {
      "session_id": "SESSION-789",
      "cpu_usage": 35.0,
      "memory_usage": 50.0
    }
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "Heartbeat received",
  "data": {
    "server_time": "2025-11-23T14:45:00Z",
    "next_heartbeat_seconds": 300,
    "license_status": "active"
  }
}
```

---

### 4. 解绑许可证

**接口**: `POST /api/v1/licenses/unbind/`

**权限**: 公开

**描述**: 解绑设备，释放激活配额

**请求体**:
```json
{
  "activation_code": "ACT-A1B2C3D4-E5F6-G7H8",
  "license_key": "6260D-4913D-64411-2A7A4-3321B",
  "reason": "Upgrading to new computer"
}
```

**curl示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/unbind/" \
  -H "Content-Type: application/json" \
  -d '{
    "activation_code": "ACT-A1B2C3D4-E5F6-G7H8",
    "license_key": "6260D-4913D-64411-2A7A4-3321B",
    "reason": "Computer reinstalled"
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "License unbound successfully",
  "data": {
    "unbound_at": "2025-11-23T14:50:00Z",
    "remaining_activations": 4
  }
}
```

---

### 5. 获取许可证信息

**接口**: `GET /api/v1/licenses/info/{license_key}/`

**权限**: 公开

**描述**: 获取许可证的公开信息（不包含敏感数据）

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/info/6260D-4913D-64411-2A7A4-3321B/" \
  -H "Content-Type: application/json"
```

**成功响应** (200 OK):
```json
{
  "product_name": "测试应用",
  "product_version": "2.0.0",
  "plan_name": "试用版",
  "plan_type": "trial",
  "features": {
    "max_users": 5,
    "storage_gb": 10
  },
  "expires_at": "2026-11-23T14:30:00Z",
  "status": "active",
  "max_activations": 10,
  "available_activations": 7
}
```

---

### 6. 服务器状态检查

**接口**: `GET /api/v1/licenses/status/`

**权限**: 公开

**描述**: 健康检查端点，用于监控服务可用性

**curl示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/licenses/status/"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "status": "healthy",
    "timestamp": "2025-11-23T14:55:00+00:00",
    "services": {
      "database": "ok",
      "cache": "ok"
    },
    "version": "1.0.0"
  }
}
```

---

## 安全机制

### 1. 频率限制

**激活API限制**: 
- 默认: 100次/小时
- 环境变量: `ACTIVATION_API_RATE_LIMIT`

**可疑活动检测**:
- 同一IP短时间内多次激活
- 同一许可证频繁激活尝试
- 异常的硬件信息模式

### 2. 硬件指纹

系统会根据以下信息生成唯一的硬件指纹:
- CPU处理器ID
- 硬盘序列号
- 网卡MAC地址
- 操作系统信息

### 3. 激活码管理

- 激活码在首次激活时生成
- 格式: `ACT-XXXXXXXX-XXXX-XXXX`
- 与设备硬件绑定
- 撤销许可证会使所有激活码失效

---

## 集成示例

### Python客户端示例

```python
import requests
import platform
import uuid

class LicenseClient:
    def __init__(self, base_url, license_key):
        self.base_url = base_url
        self.license_key = license_key
        self.activation_code = None
    
    def get_hardware_info(self):
        """收集硬件信息"""
        return {
            "system_info": {
                "os_type": platform.system(),
                "os_version": platform.version(),
                "hostname": platform.node()
            },
            "cpu_info": {
                "processor_id": str(uuid.getnode())
            }
        }
    
    def activate(self):
        """激活许可证"""
        url = f"{self.base_url}/api/v1/licenses/activate/"
        data = {
            "license_key": self.license_key,
            "hardware_info": self.get_hardware_info(),
            "client_info": {"version": "1.0.0"}
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            self.activation_code = result['data']['activation_code']
            return True
        return False
    
    def verify(self):
        """验证激活状态"""
        url = f"{self.base_url}/api/v1/licenses/verify/"
        data = {
            "activation_code": self.activation_code,
            "license_key": self.license_key
        }
        
        response = requests.post(url, json=data)
        return response.status_code == 200 and response.json()['data']['valid']
    
    def heartbeat(self):
        """发送心跳"""
        url = f"{self.base_url}/api/v1/licenses/heartbeat/"
        data = {
            "activation_code": self.activation_code,
            "license_key": self.license_key,
            "usage_data": {}
        }
        
        response = requests.post(url, json=data)
        return response.status_code == 200

# 使用示例
client = LicenseClient(
    "http://localhost:8000",
    "6260D-4913D-64411-2A7A4-3321B"
)

if client.activate():
    print("激活成功")
    if client.verify():
        print("验证通过")
```

---

## 注意事项

1. **离线使用**: 客户端应缓存激活状态，支持短期离线使用
2. **心跳频率**: 建议每5-10分钟发送一次心跳
3. **错误处理**: 客户端应妥善处理网络错误和验证失败
4. **安全存储**: 激活码应安全存储，避免泄露
5. **用户体验**: 激活失败时提供清晰的错误提示
