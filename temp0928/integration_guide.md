# 客户端许可证集成指南

## 概述

本指南详细说明了客户端软件如何与许可证服务器进行完整的交互流程，从软件启动到正常运行的全过程。

## 完整激活流程

### 1. 软件启动流程图

```
┌─────────────────┐
│   软件启动      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ 检查本地激活信息  │
└─────────┬───────┘
          │
          ▼
    ┌─────────┐    是    ┌──────────────┐
    │ 已激活？ ├────────→│   验证激活     │
    └────┬────┘         └──────┬───────┘
         │否                   │
         ▼                     ▼
┌─────────────────┐    ┌──────────────┐
│  显示激活界面    │    │  验证是否通过？│
└─────────┬───────┘    └──────┬───────┘
          │                   │是
          ▼                   ▼
┌─────────────────┐    ┌──────────────┐
│  用户输入许可证   │    │   正常使用    │
│     密钥        │    └──────────────┘
└─────────┬───────┘           ▲
          │                   │
          ▼                   │
┌─────────────────┐           │
│  获取许可证信息   │           │
└─────────┬───────┘           │
          │                   │
          ▼                   │
┌─────────────────┐           │
│   收集硬件信息   │           │
└─────────┬───────┘           │
          │                   │
          ▼                   │
┌─────────────────┐           │
│   调用激活API   │           │
└─────────┬───────┘           │
          │                   │
          ▼                   │
┌─────────────────┐    成功    │
│   激活成功？    ├───────────┘
└─────────┬───────┘
          │失败
          ▼
┌─────────────────┐
│   显示错误信息   │
└─────────────────┘
```

### 2. 详细步骤说明

#### 步骤1：检查本地激活信息

客户端启动时，首先检查本地是否存在有效的激活信息：

**检查内容：**
- 激活码 (activation_code)
- 机器指纹 (machine_fingerprint)
- 许可证信息 (license_info)
- 最后验证时间 (last_verified)

**实现建议：**
```
// 伪代码示例
function checkLocalActivation() {
    activationCode = readFromLocal("activation_code")
    machineFingerprint = readFromLocal("machine_fingerprint")
    
    if (activationCode && machineFingerprint) {
        return {
            isActivated: true,
            activationCode: activationCode,
            machineFingerprint: machineFingerprint
        }
    }
    
    return { isActivated: false }
}
```

#### 步骤2：在线验证激活状态

如果本地存在激活信息，需要向服务器验证其有效性：

**API调用：** `POST /api/v1/licenses/verify/`

**请求头：**
```
Content-Type: application/json
X-Tenant-ID: <你的租户ID>
```

**请求体：**
```json
{
    "activation_code": "ACT-12345678-ABCD-EFGH",
    "machine_fingerprint": "abc123def456..."
}
```

**成功响应 (200)：**
```json
{
    "valid": true,
    "license_info": {
        "product": "MyProduct 1.0",
        "plan": "Standard",
        "expires_at": "2024-12-31T23:59:59Z",
        "features": {
            "feature1": true,
            "feature2": false
        }
    },
    "last_verified": "2024-01-15T10:30:00Z"
}
```

#### 步骤3：显示激活界面（如果需要）

如果本地没有激活信息或验证失败，显示激活界面让用户输入许可证密钥。

**界面设计建议：**
- 许可证密钥输入框（支持格式化显示：XXXXX-XXXXX-XXXXX-XXXXX-XXXXX）
- 激活按钮
- 错误信息显示区域
- 取消或退出选项

#### 步骤4：获取许可证基本信息

用户输入许可证密钥后，先获取许可证基本信息进行验证：

**API调用：** `GET /api/v1/licenses/info/<license_key>/`

**请求头：**
```
X-Tenant-ID: <你的租户ID>
```

**成功响应 (200)：**
```json
{
    "success": true,
    "license_info": {
        "product": {
            "name": "MyProduct",
            "version": "1.0"
        },
        "plan": {
            "name": "Standard",
            "type": "standard",
            "default_max_activations": 5
        },
        "status": "issued",
        "issued_at": "2024-01-01T00:00:00Z",
        "expires_at": "2024-12-31T23:59:59Z",
        "max_activations": 5
    }
}
```

#### 步骤5：收集硬件信息

激活前需要收集本机的硬件信息用于生成机器指纹：

**必需的硬件信息：**

```json
{
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
        "mac_addresses": ["00:11:22:33:44:55", "66:77:88:99:AA:BB"]
    },
    "system_info": {
        "os_version": "Windows 10 Pro",
        "kernel_version": "10.0.19041",
        "hostname": "USER-DESKTOP"
    }
}
```

**实现提示：**

不同操作系统的硬件信息收集方式：

**Windows:**
- CPU信息：WMI查询 `Win32_Processor`
- 内存信息：WMI查询 `Win32_PhysicalMemory`
- 磁盘信息：WMI查询 `Win32_DiskDrive`
- 网卡信息：WMI查询 `Win32_NetworkAdapter`

**macOS/Linux:**
- CPU信息：读取 `/proc/cpuinfo` 或使用系统命令
- 内存信息：读取 `/proc/meminfo` 或使用系统命令
- 磁盘信息：使用 `df`, `fdisk` 等命令
- 网卡信息：使用 `ifconfig`, `ip` 等命令

#### 步骤6：调用激活API

收集完硬件信息后，调用激活API：

**API调用：** `POST /api/v1/licenses/activate/`

**请求头：**
```
Content-Type: application/json
X-Tenant-ID: <你的租户ID>
```

**请求体：**
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
            "cloud_sync": false
        }
    }
}
```

#### 步骤7：保存激活信息

激活成功后，将激活信息保存到本地：

**保存内容：**
```json
{
    "activation_code": "ACT-12345678-ABCD-EFGH",
    "machine_fingerprint": "生成的机器指纹",
    "license_key": "7C162-2DC76-F944D-D9AA4-F408E",
    "machine_id": "MACHINE-ID-12345",
    "expires_at": "2024-12-31T23:59:59Z",
    "features": {
        "advanced_features": true,
        "export_function": true,
        "cloud_sync": false
    },
    "activated_at": "2024-01-15T10:30:00Z",
    "last_verified": "2024-01-15T10:30:00Z"
}
```

**实现建议：**
- 使用加密存储激活信息
- 定期验证激活状态
- 处理激活信息损坏的情况

### 3. 运行时管理

#### 定期验证

软件运行期间应定期验证激活状态：

**验证频率建议：**
- 软件启动时：必须验证
- 运行期间：每24小时验证一次
- 网络恢复后：立即验证
- 系统时间变化后：立即验证

#### 心跳检测

激活后的软件应定期发送心跳检测：

**API调用：** `POST /api/v1/licenses/heartbeat/`

**请求体：**
```json
{
    "activation_code": "ACT-12345678-ABCD-EFGH",
    "event_type": "heartbeat",
    "event_data": {
        "feature_usage": {
            "advanced_features": 15,
            "export_function": 3
        }
    },
    "software_version": "1.0.0",
    "session_id": "SESSION-12345",
    "system_status": {
        "cpu_usage": 25.5,
        "memory_usage": 68.2
    }
}
```

**心跳频率建议：**
- 正常模式：每小时1次
- 活跃使用：每30分钟1次
- 后台运行：每2小时1次

### 4. 异常处理

#### 网络异常

当网络不可用时：
1. 使用本地缓存的验证结果
2. 记录验证失败日志
3. 在网络恢复后立即重新验证
4. 如果超过72小时无法验证，显示警告

#### 许可证过期

许可证即将过期或已过期时：
1. 提前30天显示续费提醒
2. 过期后允许7天宽限期
3. 宽限期后限制功能使用
4. 提供续费购买链接

#### 激活数量超限

当达到最大激活数量时：
1. 显示明确的错误信息
2. 提供现有激活设备列表（如果可用）
3. 提供购买更多激活数的选项
4. 允许管理员撤销其他设备的激活

## 安全考虑

### 1. 数据保护
- 加密存储本地激活信息
- 不在日志中记录完整的许可证密钥
- 使用HTTPS进行所有API通信

### 2. 防止绕过
- 验证机器指纹的完整性
- 检测系统时间篡改
- 监控异常的激活行为

### 3. 隐私保护
- 只收集必要的硬件信息
- 不收集个人身份信息
- 遵循数据保护法规

## 性能优化

### 1. 缓存策略
- 缓存验证结果减少网络请求
- 使用ETag进行条件请求
- 实现智能重试机制

### 2. 用户体验
- 异步执行网络请求
- 显示进度指示器
- 提供离线工作模式

---

**下一步：** 查看 [API参考文档](./api_reference.md) 了解具体API调用详情
