# 客户端激活API

## 概述

客户端激活API提供许可证激活、验证和心跳检测功能，供客户端软件集成使用。

**Base URL**: `/api/v1/licenses/`  
**认证要求**: 无需JWT Token（基于许可证验证）  
**权限要求**: 有效的许可证信息  

## API端点详解

### 1. 许可证激活

#### 请求
```http
POST /api/v1/licenses/activate/
Content-Type: application/json

{
    "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
    "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890abcd",
    "machine_name": "DESKTOP-ABC123",
    "hardware_info": {
        "cpu": "Intel Core i7-9700K",
        "memory": "16GB",
        "disk": "1TB SSD",
        "os": "Windows 10 Pro"
    }
}
```

#### 请求字段详解
| 字段名 | 类型 | 必填 | 说明 | 生成方式 |
|--------|------|------|------|----------|
| `license_key` | string | 是 | 许可证密钥 | 管理员分发给客户 |
| `machine_fingerprint` | string | 是 | 机器硬件指纹 | 客户端根据硬件信息生成 |
| `machine_name` | string | 是 | 机器名称 | 客户端获取系统计算机名 |
| `hardware_info` | object | 否 | 硬件详细信息 | 客户端收集 |

#### 成功响应
```json
{
    "success": true,
    "data": {
        "activation_code": "ACT-12345678901234567890123456789012",
        "license_info": {
            "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
            "customer_name": "张三",
            "expires_at": "2025-01-15T10:30:00Z",
            "max_activations": 5,
            "current_activations": 1
        },
        "product_info": {
            "name": "MyApplication Pro",
            "version": "2.1.0",
            "features": {
                "advanced_analytics": true,
                "api_access": true
            }
        },
        "machine_binding": {
            "fingerprint": "a1b2c3d4e5f6789012345678901234567890abcd",
            "bound_at": "2024-01-25T16:45:00Z"
        }
    },
    "message": "激活成功"
}
```

#### 激活失败响应
```json
{
    "success": false,
    "error": "许可证已过期",
    "code": "LICENSE_EXPIRED",
    "details": {
        "expired_at": "2024-01-15T10:30:00Z",
        "current_time": "2024-01-25T16:45:00Z"
    }
}
```

### 2. 激活状态验证

#### 请求
```http
POST /api/v1/licenses/verify/
Content-Type: application/json

{
    "activation_code": "ACT-12345678901234567890123456789012",
    "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890abcd"
}
```

#### 成功响应
```json
{
    "success": true,
    "data": {
        "is_valid": true,
        "license_status": "active",
        "expires_at": "2025-01-15T10:30:00Z",
        "features": {
            "advanced_analytics": true,
            "api_access": true
        },
        "last_verified": "2024-01-25T16:45:00Z"
    }
}
```

### 3. 心跳检测

#### 请求
```http
POST /api/v1/licenses/heartbeat/
Content-Type: application/json

{
    "activation_code": "ACT-12345678901234567890123456789012",
    "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890abcd",
    "status": "online"
}
```

#### 响应
```json
{
    "success": true,
    "data": {
        "acknowledged": true,
        "server_time": "2024-01-25T16:45:00Z",
        "next_heartbeat": "2024-01-25T17:45:00Z"
    }
}
```

### 4. 许可证信息查询

#### 请求
```http
POST /api/v1/licenses/info/
Content-Type: application/json

{
    "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX"
}
```

#### 响应
```json
{
    "success": true,
    "data": {
        "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
        "status": "active",
        "expires_at": "2025-01-15T10:30:00Z",
        "max_activations": 5,
        "current_activations": 2,
        "product": {
            "name": "MyApplication Pro",
            "version": "2.1.0"
        },
        "plan": {
            "name": "专业版年度订阅",
            "features": {
                "advanced_analytics": true,
                "api_access": true
            }
        }
    }
}
```

### 5. 服务状态查询

#### 请求
```http
GET /api/v1/licenses/status/
```

#### 响应
```json
{
    "success": true,
    "data": {
        "service_status": "healthy",
        "version": "2.1.0",
        "server_time": "2024-01-25T16:45:00Z",
        "uptime_seconds": 86400
    }
}
```

## 错误处理

### 常见错误码
| 错误码 | HTTP状态码 | 说明 | 解决方法 |
|--------|-----------|------|----------|
| `LICENSE_NOT_FOUND` | 404 | 许可证不存在 | 检查许可证密钥是否正确 |
| `LICENSE_EXPIRED` | 400 | 许可证已过期 | 联系管理员续期或更新许可证 |
| `LICENSE_SUSPENDED` | 403 | 许可证被挂起 | 联系管理员了解挂起原因 |
| `LICENSE_REVOKED` | 403 | 许可证被撤销 | 许可证已永久停用，需要新许可证 |
| `MAX_ACTIVATIONS_EXCEEDED` | 400 | 超过最大激活次数 | 联系管理员增加激活次数或解绑设备 |
| `MACHINE_NOT_BOUND` | 400 | 设备未绑定 | 需要先激活许可证 |
| `INVALID_FINGERPRINT` | 400 | 无效的设备指纹 | 检查设备指纹生成逻辑 |

## 使用示例

### JavaScript/Node.js示例
```javascript
class LicenseClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.activationCode = null;
        this.machineFingerprint = this.generateFingerprint();
    }
    
    generateFingerprint() {
        // 简化的指纹生成示例
        const os = require('os');
        const crypto = require('crypto');
        
        const machineInfo = {
            hostname: os.hostname(),
            platform: os.platform(),
            arch: os.arch(),
            cpus: os.cpus().length,
            totalmem: os.totalmem()
        };
        
        return crypto.createHash('sha256')
            .update(JSON.stringify(machineInfo))
            .digest('hex');
    }
    
    async activate(licenseKey) {
        const response = await fetch(`${this.baseURL}/activate/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                license_key: licenseKey,
                machine_fingerprint: this.machineFingerprint,
                machine_name: require('os').hostname(),
                hardware_info: this.getHardwareInfo()
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            this.activationCode = result.data.activation_code;
            console.log('激活成功:', result.data.license_info);
        } else {
            throw new Error(`激活失败: ${result.error}`);
        }
        
        return result;
    }
    
    async verify() {
        if (!this.activationCode) {
            throw new Error('尚未激活');
        }
        
        const response = await fetch(`${this.baseURL}/verify/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                activation_code: this.activationCode,
                machine_fingerprint: this.machineFingerprint
            })
        });
        
        return await response.json();
    }
    
    async heartbeat() {
        if (!this.activationCode) return;
        
        const response = await fetch(`${this.baseURL}/heartbeat/`, {
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                activation_code: this.activationCode,
                machine_fingerprint: this.machineFingerprint,
                status: 'online'
            })
        });
        
        return await response.json();
    }
    
    getHardwareInfo() {
        const os = require('os');
        return {
            platform: os.platform(),
            arch: os.arch(),
            cpu_count: os.cpus().length,
            total_memory: os.totalmem(),
            hostname: os.hostname()
        };
    }
    
    startHeartbeat(interval = 60000) {
        setInterval(async () => {
            try {
                await this.heartbeat();
                console.log('心跳发送成功');
            } catch (error) {
                console.error('心跳发送失败:', error);
            }
        }, interval);
    }
}

// 使用示例
const client = new LicenseClient('https://api.example.com/api/v1/licenses');

async function initializeLicense() {
    try {
        // 激活许可证
        await client.activate('MYAPP-PRO-XXXX-XXXX-XXXX-XXXX');
        
        // 验证激活状态
        const verification = await client.verify();
        console.log('验证结果:', verification);
        
        // 启动心跳
        client.startHeartbeat(60000); // 每分钟发送一次心跳
        
    } catch (error) {
        console.error('许可证初始化失败:', error);
    }
}

initializeLicense();
```

### Python示例
```python
import hashlib
import json
import platform
import requests
import time
import threading

class LicenseClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.activation_code = None
        self.machine_fingerprint = self._generate_fingerprint()
        self.heartbeat_thread = None
        self.heartbeat_running = False
    
    def _generate_fingerprint(self):
        """生成机器指纹"""
        machine_info = {
            'hostname': platform.node(),
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
        
        return hashlib.sha256(
            json.dumps(machine_info, sort_keys=True).encode()
        ).hexdigest()
    
    def activate(self, license_key):
        """激活许可证"""
        data = {
            'license_key': license_key,
            'machine_fingerprint': self.machine_fingerprint,
            'machine_name': platform.node(),
            'hardware_info': self._get_hardware_info()
        }
        
        response = requests.post(f'{self.base_url}/activate/', json=data)
        result = response.json()
        
        if result['success']:
            self.activation_code = result['data']['activation_code']
            print(f"激活成功: {result['data']['license_info']}")
        else:
            raise Exception(f"激活失败: {result['error']}")
        
        return result
    
    def verify(self):
        """验证激活状态"""
        if not self.activation_code:
            raise Exception('尚未激活')
        
        data = {
            'activation_code': self.activation_code,
            'machine_fingerprint': self.machine_fingerprint
        }
        
        response = requests.post(f'{self.base_url}/verify/', json=data)
        return response.json()
    
    def heartbeat(self):
        """发送心跳"""
        if not self.activation_code:
            return
        
        data = {
            'activation_code': self.activation_code,
            'machine_fingerprint': self.machine_fingerprint,
            'status': 'online'
        }
        
        response = requests.post(f'{self.base_url}/heartbeat/', json=data)
        return response.json()
    
    def _get_hardware_info(self):
        """获取硬件信息"""
        return {
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node()
        }
    
    def start_heartbeat(self, interval=60):
        """启动心跳线程"""
        def heartbeat_worker():
            while self.heartbeat_running:
                try:
                    self.heartbeat()
                    print('心跳发送成功')
                except Exception as e:
                    print(f'心跳发送失败: {e}')
                time.sleep(interval)
        
        self.heartbeat_running = True
        self.heartbeat_thread = threading.Thread(target=heartbeat_worker)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
    
    def stop_heartbeat(self):
        """停止心跳"""
        self.heartbeat_running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join()

# 使用示例
client = LicenseClient('https://api.example.com/api/v1/licenses')

try:
    # 激活许可证
    client.activate('MYAPP-PRO-XXXX-XXXX-XXXX-XXXX')
    
    # 验证激活状态
    verification = client.verify()
    print(f"验证结果: {verification}")
    
    # 启动心跳
    client.start_heartbeat(60)  # 每60秒发送一次心跳
    
    # 应用程序主逻辑
    print("应用程序运行中...")
    time.sleep(300)  # 运行5分钟
    
    # 停止心跳
    client.stop_heartbeat()
    
except Exception as e:
    print(f"许可证处理失败: {e}")
```

## 最佳实践

### 1. 指纹生成
- 使用稳定的硬件特征
- 避免使用易变的系统信息
- 实现指纹缓存机制

### 2. 错误处理
- 实现重试机制
- 优雅处理网络异常
- 提供离线模式

### 3. 安全考虑
- 加密存储激活信息
- 验证服务器证书
- 防止调试和篡改

### 4. 性能优化
- 缓存验证结果
- 合理设置心跳间隔
- 异步处理网络请求

## 相关API文档
- [API概览](./01_api_overview.md) - 了解整体API架构
- [认证和权限详解](./02_authentication.md) - 了解安全机制
