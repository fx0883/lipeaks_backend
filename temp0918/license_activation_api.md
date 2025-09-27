# 许可证激活 API 详细文档

## 📋 系统概述

许可证激活API为软件客户端提供了完整的许可证生命周期管理功能，包括许可证激活、状态验证和使用监控。这些API专为软件客户端设计，用于实现软件授权验证、使用统计和安全监控。

### 🔄 重要变更说明 (v1.3)

**字段名称更新**: 为了明确区分许可证方案的模板配置与实际许可证的使用值，已对相关字段进行重命名：

| 旧字段名 | 新字段名 | 含义说明 |
|---------|---------|----------|
| `max_machines` | `default_max_activations` | 许可证方案的默认最大激活设备数（模板值） |
| `validity_days` | `default_validity_days` | 许可证方案的默认有效天数（模板值） |

**注意**: License对象的实际使用字段（`max_activations`、`expires_at`）保持不变。

### 📊 数据结构对比

#### 许可证方案 (LicensePlan) - 模板配置
```json
{
  "id": 1,
  "name": "专业版",
  "code": "PRO",
  "plan_type": "professional",
  "default_max_activations": 5,    // 新字段：模板默认最大激活数
  "default_validity_days": 365,    // 新字段：模板默认有效天数
  "price": "999.00",
  "status": "active"
}
```

#### 许可证实例 (License) - 实际使用值（无变更）
```json
{
  "id": 123,
  "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
  "max_activations": 5,            // 实际最大激活数（从模板继承或自定义）
  "expires_at": "2025-09-26T10:00:00Z",  // 实际过期时间
  "status": "activated",
  "plan": {
    "name": "专业版",
    "default_max_activations": 5    // 引用方案的模板值
  }
}
```

### 🔄 客户端迁移指南

如果您的客户端代码之前使用了许可证方案信息，请按照以下步骤进行迁移：

#### 1. 更新字段引用
```python
# 旧代码 (需要更新)
max_devices = license_plan['max_machines']
validity_period = license_plan['validity_days']

# 新代码 (推荐)
max_devices = license_plan['default_max_activations']
validity_period = license_plan['default_validity_days']
```

#### 2. 兼容性处理
```python
def get_max_activations(license_plan):
    """获取最大激活数，兼容新旧字段名"""
    return (license_plan.get('default_max_activations') or 
            license_plan.get('max_machines', 1))

def get_validity_days(license_plan):
    """获取有效期天数，兼容新旧字段名"""
    return (license_plan.get('default_validity_days') or 
            license_plan.get('validity_days', 365))
```

#### 3. 语义理解
- **方案字段**（`default_max_activations`）：表示该方案的默认模板值
- **许可证字段**（`max_activations`）：表示具体许可证实例的实际使用值
- 许可证创建时通常从方案模板继承，但可以被个性化覆盖

### 🎯 核心功能
- **许可证激活** - 将许可证与特定设备绑定并激活
- **激活状态验证** - 定期验证许可证激活状态是否有效
- **使用心跳监控** - 实时监控软件使用状态和系统信息
- **许可证信息查询** - 获取许可证基本信息和状态
- **服务器状态检查** - 检查许可证服务器运行状态

### 🔒 安全特性
- **频率限制** - 每小时最多10次激活请求
- **可疑活动检测** - 自动检测异常激活行为
- **IP地址追踪** - 记录所有激活请求的IP地址
- **硬件指纹验证** - 确保激活设备的唯一性
- **加密数据传输** - 所有敏感信息加密存储
- **设备数量控制** - 严格限制每个许可证的最大激活设备数

## 🚀 API端点详情

### 基础信息

**基础URL**: `http://localhost:8000/api/v1/licenses/`

**认证要求**: 无需认证（公开API）

**内容类型**: `application/json`

**字符编码**: UTF-8

### 🍎 macOS 平台特殊说明

#### 权限要求
- **系统信息访问**: 需要访问系统硬件信息，可能需要用户授权
- **网络访问**: 需要网络权限进行许可证验证和心跳通信
- **文件系统访问**: 需要在 `~/Library/Application Support/` 下创建配置文件

#### macOS 特定的硬件标识符
- **Hardware UUID**: 通过 `system_profiler SPHardwareDataType` 获取
- **序列号**: Mac 设备的唯一序列号
- **Platform UUID**: 通过 `ioreg` 命令获取的平台标识符

#### 安全沙盒考虑
如果应用程序在 Mac App Store 发布，需要考虑沙盒限制：
- 配置文件路径可能需要调整到容器目录
- 某些系统命令可能被限制
- 网络访问需要在 entitlements 中声明

#### Apple Silicon 兼容性
- 代码已针对 ARM64 (Apple Silicon) 和 x64 (Intel) 架构进行优化
- 硬件指纹生成考虑了不同架构的差异
- 系统状态收集适配了 Apple Silicon 的特性

---

## 1. POST /api/v1/licenses/activate/

**激活许可证**

将许可证密钥与当前设备绑定并激活，这是软件首次运行时的必要步骤。

### 功能说明

- **主要用途**: 软件首次安装或重新安装后激活许可证
- **触发时机**: 用户输入许可证密钥并点击激活时
- **执行频率**: 通常只在软件首次安装时执行一次
- **安全机制**: 具有频率限制和可疑活动检测

### 请求参数

#### Request Body (JSON)

| 字段名 | 类型 | 必填 | 描述 | 获取方式 | 示例值 |
|-------|------|------|------|----------|-------|
| `license_key` | string | 是 | 许可证密钥 | 用户手动输入或从购买凭证中复制 | `"SAPP-PRO-2024-ABCD-EFGH-1234"` |
| `hardware_info` | object | 是 | 硬件信息对象 | 系统API自动收集 | 见下表 |
| `client_info` | object | 否 | 客户端信息对象 | 软件客户端自动填充 | 见下表 |

#### hardware_info 对象结构

| 字段名 | 类型 | 必填 | 描述 | 获取方式 | 示例值 |
|-------|------|------|------|----------|-------|
| `hardware_uuid` | string | 是 | 硬件唯一标识符 | 通过系统API获取主板序列号、CPU ID等 | `"550e8400-e29b-41d4-a716-446655440000"` |
| `system_info` | object | 是 | 系统信息对象 | 系统API获取 | 见下表 |
| `cpu_info` | object | 否 | CPU信息 | 通过cpuid指令或系统API | `{"model": "Intel i7-10700K", "cores": 8}` |
| `memory_info` | object | 否 | 内存信息 | 系统内存查询API | `{"total": "32GB", "available": "16GB"}` |
| `storage_info` | object | 否 | 存储信息 | 磁盘查询API | `{"drives": [{"letter": "C:", "size": "1TB"}]}` |
| `network_info` | object | 否 | 网络信息 | 网络适配器API | `{"mac_addresses": ["00:1A:2B:3C:4D:5E"]}` |

#### system_info 对象结构

| 字段名 | 类型 | 必填 | 描述 | 获取方式 | 示例值 |
|-------|------|------|------|----------|-------|
| `os_name` | string | 是 | 操作系统名称 | `Environment.OSVersion.Platform` (C#) | `"Windows"` |
| `os_version` | string | 是 | 操作系统版本 | `Environment.OSVersion.Version` (C#) | `"10.0.22000"` |
| `hostname` | string | 是 | 计算机名称 | `Environment.MachineName` (C#) | `"DESKTOP-ABC123"` |
| `username` | string | 否 | 当前用户名 | `Environment.UserName` (C#) | `"john_doe"` |
| `architecture` | string | 否 | 系统架构 | `Environment.ProcessorCount` (C#) | `"x64"` |
| `dotnet_version` | string | 否 | .NET版本 | `Environment.Version` (C#) | `"8.0.0"` |

#### client_info 对象结构

| 字段名 | 类型 | 必填 | 描述 | 获取方式 | 示例值 |
|-------|------|------|------|----------|-------|
| `version` | string | 否 | 客户端软件版本 | 应用程序版本常量 | `"2.1.0"` |
| `build` | string | 否 | 构建版本号 | 编译时生成的版本号 | `"20240915.1"` |
| `language` | string | 否 | 界面语言 | 系统或用户设置的语言 | `"zh-CN"` |
| `install_path` | string | 否 | 安装路径 | 应用程序安装目录 | `"C:\\Program Files\\MyApp\\"` |

### 硬件信息收集代码示例

#### Python 跨平台代码示例
```python
import platform
import uuid
import psutil
import hashlib
import subprocess
import os

def get_hardware_info():
    return {
        "hardware_uuid": generate_hardware_uuid(),
        "system_info": {
            "os_name": platform.system(),
            "os_version": platform.version(),
            "hostname": platform.node(),
            "username": os.getlogin() if hasattr(os, 'getlogin') else 'unknown',
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "platform": platform.platform()
        },
        "cpu_info": get_cpu_info(),
        "memory_info": get_memory_info(),
        "storage_info": get_storage_info(),
        "network_info": get_network_info()
    }

def generate_hardware_uuid():
    """生成跨平台的硬件UUID"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return get_macos_hardware_uuid()
    elif system == "Windows":
        return get_windows_hardware_uuid()
    elif system == "Linux":
        return get_linux_hardware_uuid()
    else:
        # 降级方案
        machine_id = f"{platform.node()}-{uuid.getnode()}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, machine_id))

def get_macos_hardware_uuid():
    """获取macOS硬件UUID"""
    try:
        # 获取硬件UUID
        hardware_uuid = subprocess.check_output([
            "system_profiler", "SPHardwareDataType"
        ], text=True)
        
        # 解析硬件UUID
        for line in hardware_uuid.split('\n'):
            if 'Hardware UUID' in line:
                uuid_value = line.split(':')[-1].strip()
                if uuid_value:
                    return uuid_value
        
        # 备选方案：获取序列号
        serial_number = subprocess.check_output([
            "system_profiler", "SPHardwareDataType"
        ], text=True)
        
        for line in serial_number.split('\n'):
            if 'Serial Number' in line:
                serial = line.split(':')[-1].strip()
                if serial and serial != "Not Available":
                    # 基于序列号生成UUID
                    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"macos-{serial}"))
        
        # 最后的降级方案
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"macos-{platform.node()}-{uuid.getnode()}"))
        
    except Exception:
        # 降级方案
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"macos-{platform.node()}-{uuid.getnode()}"))

def get_windows_hardware_uuid():
    """获取Windows硬件UUID"""
    try:
        # 尝试获取主板序列号
        result = subprocess.check_output([
            "wmic", "baseboard", "get", "serialnumber", "/value"
        ], text=True)
        
        for line in result.split('\n'):
            if line.startswith('SerialNumber='):
                serial = line.split('=')[1].strip()
                if serial:
                    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"windows-{serial}"))
        
        # 降级方案
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"windows-{platform.node()}-{uuid.getnode()}"))
        
    except Exception:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"windows-{platform.node()}-{uuid.getnode()}"))

def get_linux_hardware_uuid():
    """获取Linux硬件UUID"""
    try:
        # 尝试读取机器ID
        with open('/etc/machine-id', 'r') as f:
            machine_id = f.read().strip()
            if machine_id:
                return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"linux-{machine_id}"))
    except Exception:
        pass
    
    try:
        # 尝试读取DMI产品UUID
        with open('/sys/class/dmi/id/product_uuid', 'r') as f:
            product_uuid = f.read().strip()
            if product_uuid:
                return product_uuid
    except Exception:
        pass
    
    # 降级方案
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"linux-{platform.node()}-{uuid.getnode()}"))

def get_cpu_info():
    """获取CPU信息"""
    try:
        if platform.system() == "Darwin":
            # macOS
            brand_string = subprocess.check_output([
                "sysctl", "-n", "machdep.cpu.brand_string"
            ], text=True).strip()
            
            cores = subprocess.check_output([
                "sysctl", "-n", "hw.ncpu"
            ], text=True).strip()
            
            return {
                "model": brand_string,
                "cores": int(cores) if cores.isdigit() else psutil.cpu_count()
            }
        else:
            # Windows/Linux 使用psutil
            return {
                "model": platform.processor() or "Unknown",
                "cores": psutil.cpu_count()
            }
    except Exception:
        return {
            "model": platform.processor() or "Unknown",
            "cores": psutil.cpu_count()
        }

def get_memory_info():
    """获取内存信息"""
    try:
        if platform.system() == "Darwin":
            # macOS - 获取精确的内存信息
            memsize = subprocess.check_output([
                "sysctl", "-n", "hw.memsize"
            ], text=True).strip()
            
            total_bytes = int(memsize)
            total_gb = round(total_bytes / 1024**3, 1)
            
            # 获取可用内存 (简化版本)
            vm_stat = subprocess.check_output(["vm_stat"], text=True)
            # 这里可以解析vm_stat来获取更精确的可用内存
            # 为简化起见，使用psutil的数据
            available_gb = round(psutil.virtual_memory().available / 1024**3, 1)
            
            return {
                "total": f"{total_gb}GB",
                "available": f"{available_gb}GB"
            }
        else:
            # Windows/Linux
            memory = psutil.virtual_memory()
            return {
                "total": f"{round(memory.total / 1024**3, 1)}GB",
                "available": f"{round(memory.available / 1024**3, 1)}GB"
            }
    except Exception:
        # 降级到psutil
        memory = psutil.virtual_memory()
        return {
            "total": f"{round(memory.total / 1024**3, 1)}GB",
            "available": f"{round(memory.available / 1024**3, 1)}GB"
        }

def get_storage_info():
    """获取存储信息"""
    drives = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            drives.append({
                "mount": part.mountpoint,
                "size": f"{round(usage.total / 1024**3)}GB",
                "type": part.fstype
            })
        except Exception:
            continue
    
    return {"drives": drives}

def get_network_info():
    """获取网络信息"""
    mac_addresses = []
    
    try:
        if platform.system() == "Darwin":
            # macOS - 使用ifconfig获取MAC地址
            result = subprocess.check_output(["ifconfig"], text=True)
            import re
            macs = re.findall(r'ether ([a-fA-F0-9:]{17})', result)
            mac_addresses = [mac.replace(':', '') for mac in macs if mac != '00:00:00:00:00:00']
        else:
            # Windows/Linux - 使用psutil
            for name, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if hasattr(addr, 'family') and addr.family == psutil.AF_LINK:
                        mac = addr.address.replace(':', '').replace('-', '')
                        if mac and mac != '000000000000':
                            mac_addresses.append(mac)
    except Exception:
        # 降级到psutil
        try:
            for name, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if hasattr(addr, 'family') and addr.family == psutil.AF_LINK:
                        mac = addr.address.replace(':', '').replace('-', '')
                        if mac and mac != '000000000000':
                            mac_addresses.append(mac)
        except Exception:
            pass
    
    return {"mac_addresses": list(set(mac_addresses))}  # 去重
```

### 请求示例

#### Windows 平台请求示例
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/activate/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyApp/2.1.0" \
  -d '{
    "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
    "hardware_info": {
      "hardware_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "system_info": {
        "os_name": "Windows",
        "os_version": "10.0.22000",
        "hostname": "DESKTOP-ABC123",
        "username": "john_doe",
        "architecture": "x64",
        "dotnet_version": "8.0.0",
        "platform": "win-x64"
      },
      "cpu_info": {
        "model": "Intel Core i7-10700K",
        "cores": 8
      },
      "memory_info": {
        "total": "32GB",
        "available": "16GB"
      },
      "storage_info": {
        "drives": [
          {
            "name": "C:\\",
            "size": "1TB",
            "type": "Fixed"
          }
        ]
      },
      "network_info": {
        "mac_addresses": ["001A2B3C4D5E"]
      }
    },
    "client_info": {
      "version": "2.1.0",
      "build": "20240915.1",
      "language": "zh-CN",
      "install_path": "C:\\Program Files\\MyApp\\"
    }
  }'
```

#### macOS 平台请求示例
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/activate/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyApp/2.1.0" \
  -d '{
    "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
    "hardware_info": {
      "hardware_uuid": "12345678-1234-5678-9ABC-DEF012345678",
      "system_info": {
        "os_name": "macOS",
        "os_version": "14.0",
        "hostname": "MacBook-Pro.local",
        "username": "john_doe",
        "architecture": "arm64",
        "dotnet_version": "8.0.0",
        "platform": "osx-arm64"
      },
      "cpu_info": {
        "model": "Apple M2 Pro",
        "cores": 12
      },
      "memory_info": {
        "total": "32GB",
        "available": "18GB"
      },
      "storage_info": {
        "drives": [
          {
            "name": "/",
            "size": "1TB",
            "type": "apfs"
          }
        ]
      },
      "network_info": {
        "mac_addresses": ["A1B2C3D4E5F6", "12345678ABCD"]
      }
    },
    "client_info": {
      "version": "2.1.0",
      "build": "20240915.1",
      "language": "zh-CN",
      "install_path": "/Applications/MyApp.app/"
    }
  }'
```

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "message": "License activated successfully",
  "data": {
    "activation_code": "ACT-20240915-WXYZ-1234-ABCD",
    "machine_id": "DESKTOP-ABC123-550e8400",
    "expires_at": "2025-09-15T14:30:00Z",
    "features": {
      "advanced_features": true,
      "premium_support": true,
      "api_access": true,
      "concurrent_users": 100
    },
    "activation_info": {
      "max_activations": 5,
      "current_activations": 1,
      "available_slots": 4,
      "activation_percentage": 20
    }
  }
}
```

#### 错误响应示例

```json
// 许可证不存在或无效 (400 Bad Request)
{
  "success": false,
  "error": "License not found or invalid",
  "code": "LICENSE_NOT_FOUND"
}

// 许可证已过期 (400 Bad Request)  
{
  "success": false,
  "error": "License has expired",
  "code": "LICENSE_EXPIRED"
}

// 超过最大激活数 (400 Bad Request)
{
  "success": false,
  "error": "Maximum activations (5) reached",
  "code": "MAX_ACTIVATIONS_REACHED",
  "details": {
    "max_allowed": 5,
    "current_active": 5,
    "available_slots": 0,
    "active_devices": [
      "DESKTOP-ABC123",
      "MacBook-Pro", 
      "LAPTOP-XYZ789"
    ]
  },
  "suggestions": [
    "停用不再使用的设备以释放激活槽位",
    "联系管理员增加许可证的设备数量限制"
  ]
}

// 许可证已被撤销 (400 Bad Request)
{
  "success": false,
  "error": "License has been revoked", 
  "code": "LICENSE_REVOKED"
}

// 频率限制 (429 Too Many Requests)
{
  "success": false,
  "error": "Too many activation attempts. Please try again later.",
  "code": "RATE_LIMITED"
}

// 可疑活动 (403 Forbidden)
{
  "success": false,
  "error": "Activation request flagged for review",
  "code": "SUSPICIOUS_ACTIVITY"
}

// 参数验证错误 (400 Bad Request)
{
  "success": false,
  "errors": {
    "license_key": ["许可证密钥格式无效"],
    "hardware_info": ["硬件信息缺少必要字段: hardware_uuid"]
  }
}
```

### 客户端处理逻辑

可以使用Python的requests库来实现许可证激活：

```python
import requests
import json
import os
from pathlib import Path

class LicenseActivator:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MyApp/2.1.0',
            'Content-Type': 'application/json'
        })
    
    def activate_license(self, license_key):
        try:
            hardware_info = get_hardware_info()
            client_info = {
                "version": "2.1.0",
                "build": "20240915.1", 
                "language": "zh-CN",
                "install_path": str(Path.cwd())
            }
            
            request_data = {
                "license_key": license_key,
                "hardware_info": hardware_info,
                "client_info": client_info
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/licenses/activate/",
                json=request_data,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('success'):
                # 保存激活信息到本地配置
                self.save_activation_info(result['data'])
                return {"success": True, "data": result['data']}
            else:
                return {"success": False, "error": result.get('error', 'Activation failed')}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": "网络连接失败", "code": "NETWORK_ERROR"}
        except Exception as e:
            return {"success": False, "error": "激活过程出现异常", "code": "UNKNOWN_ERROR"}
    
    def save_activation_info(self, data):
        config = {
            "activation_code": data.get('activation_code'),
            "machine_id": data.get('machine_id'),
            "expires_at": data.get('expires_at'),
            "features": data.get('features'),
            "activated_at": "2024-09-18T10:00:00Z"
        }
        
        # 跨平台配置文件路径
        if platform.system() == "Windows":
            config_dir = Path.home() / "AppData" / "Roaming" / "MyApp"
        elif platform.system() == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "MyApp"
        else:  # Linux
            config_dir = Path.home() / ".config" / "MyApp"
        
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "license.json"
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
```

---

## 2. POST /api/v1/licenses/verify/

**验证激活状态**

验证已激活许可证的当前状态，确保许可证仍然有效且未被撤销。

### 功能说明

- **主要用途**: 定期验证许可证激活状态的有效性
- **触发时机**: 软件启动时、功能使用前、定时检查
- **执行频率**: 建议每24小时至少验证一次
- **缓存机制**: 验证结果缓存5分钟，减少服务器负载

### 请求参数

#### Request Body (JSON)

| 字段名 | 类型 | 必填 | 描述 | 获取方式 | 示例值 |
|-------|------|------|------|----------|-------|
| `activation_code` | string | 是 | 激活码 | 从激活响应中保存的激活码 | `"ACT-20240915-WXYZ-1234-ABCD"` |
| `machine_fingerprint` | string | 是 | 机器指纹 | 通过硬件信息生成的唯一指纹 | `"fp_550e8400e29b41d4a716446655440000"` |

### 机器指纹生成方法

机器指纹是基于硬件信息生成的唯一标识符，用于验证激活设备的一致性。可以使用上面的Python代码中的`generate_hardware_uuid()`函数来生成机器指纹。

### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/verify/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyApp/2.1.0" \
  -d '{
    "activation_code": "ACT-20240915-WXYZ-1234-ABCD",
    "machine_fingerprint": "fp_550e8400e29b41d4a716446655440000"
  }'
```

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "valid": true,
  "license_info": {
    "product": "SuperApp Pro",
    "plan": "专业版",
    "expires_at": "2025-09-15T14:30:00Z",
    "features": {
      "advanced_features": true,
      "premium_support": true,
      "api_access": true,
      "concurrent_users": 100
    }
  },
  "last_verified": "2024-09-15T10:30:00Z"
}
```

#### 错误响应示例

```json
// 激活码无效 (400 Bad Request)
{
  "valid": false,
  "error": "Activation not found",
  "code": "ACTIVATION_NOT_FOUND"
}

// 机器指纹不匹配 (400 Bad Request)
{
  "valid": false,
  "error": "Machine fingerprint mismatch",
  "code": "FINGERPRINT_MISMATCH",
  "similarity": 0.75
}

// 许可证已失效 (400 Bad Request)
{
  "valid": false,
  "error": "License status: revoked",
  "code": "LICENSE_INACTIVE"
}

// 激活已过期 (400 Bad Request)
{
  "valid": false,
  "error": "Activation has expired",
  "code": "ACTIVATION_EXPIRED"
}
```

### 客户端处理逻辑

使用Python实现许可证验证：

```python
import time
from datetime import datetime, timedelta

class LicenseVerifier:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MyApp/2.1.0',
            'Content-Type': 'application/json'
        })
        self.last_verification_time = None
        self.verification_interval = timedelta(hours=24)
    
    def verify_license(self):
        # 检查是否需要验证
        now = datetime.now()
        if (self.last_verification_time and 
            now - self.last_verification_time < self.verification_interval):
            return True  # 使用缓存的验证结果
        
        try:
            activation_code = self.load_activation_code()
            machine_fingerprint = self.generate_machine_fingerprint()
            
            request_data = {
                "activation_code": activation_code,
                "machine_fingerprint": machine_fingerprint
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/licenses/verify/",
                json=request_data,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('valid'):
                self.last_verification_time = now
                self.update_license_info(result.get('license_info'))
                return True
            else:
                self.handle_verification_failure(result.get('error'), result.get('code'))
                return False
                
        except Exception as e:
            # 网络错误时，允许软件继续运行一段时间
            if self.last_verification_time:
                time_since_last = now - self.last_verification_time
                return time_since_last < timedelta(days=7)  # 7天宽限期
            return False
    
    def generate_machine_fingerprint(self):
        # 使用前面定义的generate_hardware_uuid函数
        hardware_uuid = generate_hardware_uuid()
        import hashlib
        fingerprint = hashlib.sha256(hardware_uuid.encode()).hexdigest()
        return f"fp_{fingerprint[:32]}"
    
    def load_activation_code(self):
        # 从本地配置文件加载激活码
        config_file = self.get_config_file_path()
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('activation_code')
        return None
    
    def get_config_file_path(self):
        if platform.system() == "Windows":
            config_dir = Path.home() / "AppData" / "Roaming" / "MyApp"
        elif platform.system() == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "MyApp"
        else:  # Linux
            config_dir = Path.home() / ".config" / "MyApp"
        
        return config_dir / "license.json"
```

---

## 3. POST /api/v1/licenses/heartbeat/

**许可证心跳**

定期发送软件使用状态信息，更新最后使用时间并收集使用统计数据。

### 功能说明

- **主要用途**: 监控软件使用状态、收集使用统计、维持激活状态
- **触发时机**: 软件启动、功能使用、定时心跳、软件关闭
- **执行频率**: 建议每5-15分钟发送一次心跳
- **数据用途**: 使用统计、异常监控、许可证管理

### 请求参数

#### Request Body (JSON)

| 字段名 | 类型 | 必填 | 描述 | 获取方式 | 示例值 |
|-------|------|------|------|----------|-------|
| `activation_code` | string | 是 | 激活码 | 从激活响应中保存的激活码 | `"ACT-20240915-WXYZ-1234-ABCD"` |
| `event_type` | string | 是 | 事件类型 | 根据软件状态选择对应类型 | `"heartbeat"` |
| `event_data` | object | 否 | 事件数据 | 事件相关的额外信息 | `{"feature": "export", "items": 100}` |
| `software_version` | string | 否 | 软件版本 | 应用程序版本号 | `"2.1.0"` |
| `session_id` | string | 否 | 会话ID | 软件启动时生成的唯一会话标识 | `"sess_20240915_103000_abc123"` |
| `system_status` | object | 否 | 系统状态 | 当前系统资源使用情况 | 见下表 |

#### event_type 枚举值

| 值 | 描述 | 使用场景 | 建议频率 |
|---|------|----------|----------|
| `startup` | 软件启动 | 软件启动完成时 | 每次启动一次 |
| `heartbeat` | 心跳检测 | 定期状态更新 | 每5-15分钟 |
| `feature_use` | 功能使用 | 用户使用关键功能时 | 按功能使用触发 |
| `shutdown` | 软件关闭 | 软件正常退出时 | 每次关闭一次 |
| `verification` | 在线验证 | 执行许可证验证时 | 与验证API同步 |

#### system_status 对象结构

| 字段名 | 类型 | 必填 | 描述 | 获取方式 | 示例值 |
|-------|------|------|------|----------|-------|
| `cpu_usage` | float | 否 | CPU使用率(0-1) | 性能计数器或系统API | `0.35` |
| `memory_usage` | float | 否 | 内存使用率(0-1) | 内存状态API | `0.67` |
| `disk_usage` | float | 否 | 磁盘使用率(0-1) | 磁盘空间API | `0.82` |
| `uptime` | integer | 否 | 软件运行时间(秒) | 应用程序计时器 | `3600` |
| `active_features` | array | 否 | 当前活跃功能列表 | 应用程序状态跟踪 | `["export", "analysis"]` |

#### event_data 使用示例

```javascript
// 功能使用事件
{
  "event_type": "feature_use",
  "event_data": {
    "feature_name": "data_export",
    "feature_params": {
      "format": "excel",
      "rows": 5000,
      "columns": 25
    },
    "execution_time_ms": 2500,
    "success": true
  }
}

// 软件启动事件
{
  "event_type": "startup",
  "event_data": {
    "startup_time_ms": 3200,
    "loaded_modules": ["core", "ui", "export", "analysis"],
    "configuration": {
      "theme": "dark",
      "language": "zh-CN"
    }
  }
}

// 错误事件
{
  "event_type": "heartbeat",
  "event_data": {
    "errors_since_last": 2,
    "warnings_since_last": 5,
    "last_error": {
      "type": "FileNotFoundException",
      "message": "Template file not found",
      "timestamp": "2024-09-15T10:25:00Z"
    }
  }
}
```

### 系统状态收集代码示例

#### Python 跨平台系统状态收集

```python
import psutil
import time
import platform
import subprocess
from datetime import datetime

def get_system_status():
    """获取系统状态信息"""
    return {
        "cpu_usage": get_cpu_usage(),
        "memory_usage": get_memory_usage(),
        "disk_usage": get_disk_usage(),
        "uptime": get_application_uptime(),
        "active_features": get_active_features()
    }

def get_cpu_usage():
    """获取CPU使用率"""
    try:
        if platform.system() == "Darwin":  # macOS
            return get_macos_cpu_usage()
        else:
            # Windows/Linux使用psutil
            return psutil.cpu_percent(interval=1) / 100.0
    except Exception:
        return 0.0

def get_macos_cpu_usage():
    """获取macOS CPU使用率"""
    try:
        # 使用top命令获取CPU使用率
        result = subprocess.check_output([
            "bash", "-c", 
            "top -l 1 -s 0 | grep 'CPU usage' | awk '{print $3}' | sed 's/%//'"
        ], text=True)
        
        if result.strip():
            return float(result.strip()) / 100.0
        
        # 备选方案：使用psutil
        return psutil.cpu_percent(interval=1) / 100.0
        
    except Exception:
        return psutil.cpu_percent(interval=1) / 100.0

def get_memory_usage():
    """获取内存使用率"""
    try:
        memory = psutil.virtual_memory()
        return memory.percent / 100.0
    except Exception:
        return 0.0

def get_disk_usage():
    """获取磁盘使用率"""
    try:
        # 获取主磁盘使用率
        if platform.system() == "Windows":
            disk = psutil.disk_usage('C:')
        else:
            disk = psutil.disk_usage('/')
        
        return disk.percent / 100.0
    except Exception:
        return 0.0

# 应用程序启动时间（全局变量）
app_start_time = time.time()

def get_application_uptime():
    """获取应用程序运行时间（秒）"""
    try:
        return int(time.time() - app_start_time)
    except Exception:
        return 0

# 模拟的活跃功能状态（实际应用中替换为真实的模块状态）
active_modules = {
    "export": False,
    "analysis": False, 
    "reporting": False
}

def get_active_features():
    """获取当前活跃的功能列表"""
    try:
        features = []
        for module, is_active in active_modules.items():
            if is_active:
                features.append(module)
        return features
    except Exception:
        return []

def set_module_active(module_name, is_active):
    """设置模块活跃状态"""
    if module_name in active_modules:
        active_modules[module_name] = is_active
```

### 请求示例

#### 心跳请求示例
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/heartbeat/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyApp/2.1.0" \
  -d '{
    "activation_code": "ACT-20240915-WXYZ-1234-ABCD",
    "event_type": "heartbeat",
    "event_data": {
      "features_used_since_last": ["export", "analysis"],
      "operations_count": 25,
      "data_processed_mb": 150.5
    },
    "software_version": "2.1.0",
    "session_id": "sess_20240915_103000_abc123",
    "system_status": {
      "cpu_usage": 0.35,
      "memory_usage": 0.67,
      "disk_usage": 0.82,
      "uptime": 3600,
      "active_features": ["export", "analysis"]
    }
  }'
```

#### 功能使用请求示例
```bash
curl -X POST "http://localhost:8000/api/v1/licenses/heartbeat/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyApp/2.1.0" \
  -d '{
    "activation_code": "ACT-20240915-WXYZ-1234-ABCD",
    "event_type": "feature_use",
    "event_data": {
      "feature_name": "data_export",
      "feature_params": {
        "format": "excel",
        "rows": 5000,
        "columns": 25
      },
      "execution_time_ms": 2500,
      "success": true
    },
    "software_version": "2.1.0",
    "session_id": "sess_20240915_103000_abc123"
  }'
```

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "message": "Heartbeat recorded",
  "license_status": {
    "status": "activated",
    "expires_at": "2025-09-15T14:30:00Z",
    "days_until_expiry": 365
  },
  "timestamp": "2024-09-15T10:30:00Z"
}
```

#### 带警告的成功响应 (200 OK)

```json
{
  "success": true,
  "message": "Heartbeat recorded",
  "license_status": {
    "status": "activated",
    "expires_at": "2024-10-15T14:30:00Z",
    "days_until_expiry": 30
  },
  "warnings": [
    "License will expire in 30 days"
  ],
  "timestamp": "2024-09-15T10:30:00Z"
}
```

#### 错误响应示例

```json
// 激活码无效 (400 Bad Request)
{
  "success": false,
  "error": "Invalid activation code",
  "code": "INVALID_ACTIVATION"
}

// 许可证不活跃 (400 Bad Request)
{
  "success": false,
  "error": "License is revoked",
  "code": "LICENSE_INACTIVE"
}

// 参数验证错误 (400 Bad Request)
{
  "success": false,
  "errors": {
    "event_type": ["请选择一个有效的事件类型。"]
  }
}
```

### 客户端心跳管理器

使用Python实现心跳管理：

```python
import threading
import time
import uuid
from datetime import datetime

class HeartbeatManager:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MyApp/2.1.0',
            'Content-Type': 'application/json'
        })
        self.session_id = self.generate_session_id()
        self.heartbeat_interval = 600  # 10分钟
        self.heartbeat_thread = None
        self.running = False
    
    def start(self):
        """启动心跳管理器"""
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def stop(self):
        """停止心跳管理器"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        
        # 发送关闭事件
        self.send_shutdown_event()
    
    def send_feature_usage(self, feature_name, parameters, execution_time, success):
        """发送功能使用心跳"""
        try:
            activation_code = self.load_activation_code()
            
            request_data = {
                "activation_code": activation_code,
                "event_type": "feature_use",
                "event_data": {
                    "feature_name": feature_name,
                    "feature_params": parameters,
                    "execution_time_ms": execution_time,
                    "success": success
                },
                "software_version": "2.1.0",
                "session_id": self.session_id,
                "system_status": get_system_status()
            }
            
            self._send_heartbeat_request(request_data)
            
        except Exception as e:
            print(f"Failed to send feature usage heartbeat: {e}")
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                self._send_regular_heartbeat()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                print(f"Heartbeat failed: {e}")
                time.sleep(60)  # 出错后等待1分钟再试
    
    def _send_regular_heartbeat(self):
        """发送常规心跳"""
        try:
            activation_code = self.load_activation_code()
            
            request_data = {
                "activation_code": activation_code,
                "event_type": "heartbeat",
                "event_data": {
                    "features_used_since_last": self.get_used_features_since_last(),
                    "operations_count": self.get_operations_count(),
                    "errors_since_last": self.get_error_count()
                },
                "software_version": "2.1.0",
                "session_id": self.session_id,
                "system_status": get_system_status()
            }
            
            response = self._send_heartbeat_request(request_data)
            
            # 检查许可证状态警告
            if response and response.get('warnings'):
                for warning in response['warnings']:
                    self.show_license_warning(warning)
                    
        except Exception as e:
            print(f"Regular heartbeat failed: {e}")
    
    def send_shutdown_event(self):
        """发送关闭事件"""
        try:
            activation_code = self.load_activation_code()
            
            request_data = {
                "activation_code": activation_code,
                "event_type": "shutdown",
                "event_data": {
                    "session_duration_seconds": self.get_session_duration(),
                    "clean_shutdown": True
                },
                "software_version": "2.1.0",
                "session_id": self.session_id
            }
            
            self._send_heartbeat_request(request_data)
            
        except Exception as e:
            print(f"Shutdown event failed: {e}")
    
    def _send_heartbeat_request(self, request_data):
        """发送心跳请求"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/licenses/heartbeat/",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Heartbeat request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Heartbeat request error: {e}")
            return None
    
    def generate_session_id(self):
        """生成会话ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = str(uuid.uuid4())[:6]
        return f"sess_{timestamp}_{random_id}"
    
    def load_activation_code(self):
        """加载激活码"""
        # 这里使用与LicenseVerifier相同的方法
        config_file = self.get_config_file_path()
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('activation_code')
        return None
    
    def get_config_file_path(self):
        """获取配置文件路径"""
        if platform.system() == "Windows":
            config_dir = Path.home() / "AppData" / "Roaming" / "MyApp"
        elif platform.system() == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "MyApp"
        else:  # Linux
            config_dir = Path.home() / ".config" / "MyApp"
        
        return config_dir / "license.json"
    
    def get_used_features_since_last(self):
        """获取上次心跳以来使用的功能"""
        # 实际应用中应该记录和跟踪功能使用
        return list(active_modules.keys())
    
    def get_operations_count(self):
        """获取操作计数"""
        # 实际应用中应该记录和跟踪操作次数
        return 0
    
    def get_error_count(self):
        """获取错误计数"""
        # 实际应用中应该记录和跟踪错误次数
        return 0
    
    def get_session_duration(self):
        """获取会话持续时间"""
        return get_application_uptime()
    
    def show_license_warning(self, warning):
        """显示许可证警告"""
        print(f"License Warning: {warning}")
```

---

## 4. GET /api/v1/licenses/info/{license_key}/

**获取许可证信息**

根据许可证密钥获取许可证的基本信息和状态，用于激活前的信息预览。

### 功能说明

- **主要用途**: 激活前预览许可证信息、验证许可证有效性
- **触发时机**: 用户输入许可证密钥后、激活前验证
- **执行频率**: 按需调用，通常在激活流程中使用
- **返回信息**: 不包含敏感信息，只提供基本的产品和方案信息

### 请求参数

#### Query Parameters

| 参数名 | 类型 | 必填 | 描述 | 获取方式 | 示例值 |
|-------|------|------|------|----------|-------|
| `license_key` | string | 是 | 许可证密钥 | 用户输入或从文件读取 | `SAPP-PRO-2024-ABCD-EFGH-1234` |

### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/info/SAPP-PRO-2024-ABCD-EFGH-1234/" \
  -H "Accept: application/json" \
  -H "User-Agent: MyApp/2.1.0"
```

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "license_info": {
    "product": {
      "name": "SuperApp Pro",
      "version": "2.0"
    },
    "plan": {
      "name": "专业版",
      "type": "professional",
      "default_max_activations": 5
    },
    "status": "generated",
    "issued_at": "2024-09-01T10:00:00Z",
    "expires_at": "2025-09-01T10:00:00Z",
    "max_activations": 5
  }
}
```

#### 错误响应示例

```json
// 许可证未找到 (404 Not Found)
{
  "success": false,
  "error": "License not found"
}

// 许可证密钥格式无效 (400 Bad Request)
{
  "success": false,
  "error": "Invalid license key format"
}

// 许可证密钥验证失败 (400 Bad Request)
{
  "success": false,
  "error": "Invalid key signature"
}
```

---

## 5. GET /api/v1/licenses/status/

**获取服务器状态**

检查许可证服务器的运行状态和可用性。

### 功能说明

- **主要用途**: 服务器健康检查、网络连接测试
- **触发时机**: 软件启动时、网络连接异常时
- **执行频率**: 按需调用或定期检查
- **无需参数**: 无需任何认证或参数

### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/status/" \
  -H "Accept: application/json" \
  -H "User-Agent: MyApp/2.1.0"
```

### 响应格式

#### 服务器正常 (200 OK)

```json
{
  "status": "healthy",
  "timestamp": "2024-09-15T10:30:00Z",
  "services": {
    "database": "ok",
    "cache": "ok"
  },
  "version": "1.0.0"
}
```

#### 服务器异常 (503 Service Unavailable)

```json
{
  "status": "unhealthy",
  "error": "Database connection failed",
  "timestamp": "2024-09-15T10:30:00Z"
}
```

---

## 🎛️ 设备绑定数量控制

### 控制机制概述

许可证系统通过多层次的机制来严格控制每个许可证允许绑定的设备数量，确保合规使用并防止滥用。

### 核心控制架构

#### 1. 许可证级别控制

每个许可证都有一个 `max_activations` 字段，定义了该许可证最多可以激活的设备数量：

```python
# 许可证模型中的关键字段
{
    "max_activations": 5,        # 最大激活数
    "current_activations": 2,    # 当前激活数
    "available_slots": 3         # 可用槽位数
}
```

#### 2. 激活验证流程

在设备激活时，系统会执行以下验证步骤：

```python
def check_activation_limit(license_key, hardware_info):
    """检查激活数量限制"""
    
    # 1. 获取许可证信息
    license = get_license(license_key)
    
    # 2. 计算当前活跃设备数
    active_devices = count_active_devices(license)
    
    # 3. 验证是否超出限制
    if active_devices >= license.max_activations:
        return {
            "allowed": False,
            "error": f"Maximum activations ({license.max_activations}) reached",
            "current_count": active_devices,
            "max_allowed": license.max_activations
        }
    
    return {"allowed": True}
```

### 设备状态管理

#### 设备绑定状态类型

每个绑定的设备都有以下状态之一：

| 状态 | 描述 | 计入激活数 | 说明 |
|------|------|-----------|------|
| `active` | 活跃 | ✅ 是 | 正常使用的设备 |
| `inactive` | 非活跃 | ❌ 否 | 已停用的设备 |
| `blocked` | 已阻止 | ❌ 否 | 被管理员阻止的设备 |
| `expired` | 已过期 | ❌ 否 | 绑定已过期的设备 |

#### 设备解绑释放槽位

当设备不再使用时，可以解绑释放激活槽位：

```python
# POST /api/v1/licenses/deactivate/
{
    "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
    "machine_fingerprint": "fp_550e8400e29b41d4a716446655440000"
}

# 响应
{
    "success": true,
    "message": "Device deactivated successfully",
    "available_slots": 4,
    "remaining_activations": 1
}
```

### 数量控制的层级设置

#### 1. 产品级默认值

每个软件产品可以设置默认的最大激活数：

```json
{
    "product": {
        "name": "SuperApp Pro",
        "default_max_activations": 5
    }
}
```

#### 2. 方案级配置

不同的许可证方案可以有不同的设备数限制：

```json
{
    "plans": [
        {
            "name": "试用版",
            "type": "trial",
            "default_max_activations": 1
        },
        {
            "name": "基础版", 
            "type": "basic",
            "default_max_activations": 3
        },
        {
            "name": "专业版",
            "type": "professional", 
            "default_max_activations": 10
        },
        {
            "name": "企业版",
            "type": "enterprise",
            "default_max_activations": 50
        }
    ]
}
```

#### 3. 许可证级个性化

单个许可证可以覆盖方案的默认设置：

```json
{
    "license": {
        "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
        "plan_default_max_activations": 10,
        "custom_max_activations": 15,  // 个性化设置
        "reason": "客户特殊需求"
    }
}
```

### 实时监控和管理

#### 激活状态查询

```python
# GET /api/v1/licenses/activation-status/{license_key}/
{
    "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
    "max_activations": 5,
    "current_activations": 3,
    "available_slots": 2,
    "active_devices": [
        {
            "machine_id": "DESKTOP-ABC123-550e8400",
            "machine_fingerprint": "fp_550e8400e29b41d4a716446655440000",
            "first_seen": "2024-09-15T10:30:00Z",
            "last_seen": "2024-09-18T14:20:00Z",
            "os_info": {
                "os_name": "macOS",
                "os_version": "14.0",
                "hostname": "MacBook-Pro.local"
            }
        }
    ]
}
```

#### 批量设备管理

```python
# POST /api/v1/licenses/bulk-deactivate/
{
    "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
    "machine_fingerprints": [
        "fp_550e8400e29b41d4a716446655440000",
        "fp_123456789abcdef0123456789abcdef"
    ],
    "reason": "设备更换"
}

# 响应
{
    "success": true,
    "deactivated_count": 2,
    "available_slots": 4,
    "remaining_activations": 1
}
```

### 防滥用机制

#### 1. 设备指纹验证

系统生成唯一的设备指纹来防止虚拟化滥用：

```python
def generate_device_fingerprint(hardware_info):
    """生成设备指纹"""
    fingerprint_data = {
        "hardware_uuid": hardware_info["hardware_uuid"],
        "cpu_model": hardware_info["cpu_info"]["model"],
        "mac_addresses": hardware_info["network_info"]["mac_addresses"]
    }
    
    # 生成SHA256哈希
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_data, sort_keys=True).encode()
    ).hexdigest()
    
    return f"fp_{fingerprint[:32]}"
```

#### 2. 激活频率限制

```python
# 每个IP地址每小时最多10次激活尝试
rate_limit_config = {
    "max_attempts": 10,
    "time_window": 3600,  # 1小时
    "block_duration": 7200  # 2小时封锁
}
```

#### 3. 异常检测

系统会检测以下异常行为：

- 短时间内大量激活请求
- 相同硬件指纹的重复激活
- 来自可疑IP地址的激活
- 虚拟机环境的频繁激活

### 错误处理

#### 激活数量超限错误

```json
{
    "success": false,
    "error": "Maximum activations (5) reached",
    "code": "MAX_ACTIVATIONS_REACHED",
    "details": {
        "max_allowed": 5,
        "current_active": 5,
        "available_slots": 0,
        "active_devices": [
            "DESKTOP-ABC123",
            "MacBook-Pro",
            "LAPTOP-XYZ789",
            "SERVER-001",
            "WORKSTATION-456"
        ]
    },
    "suggestions": [
        "停用不再使用的设备以释放激活槽位",
        "联系管理员增加许可证的设备数量限制",
        "升级到更高级别的许可证方案"
    ]
}
```

### 管理员控制功能

#### 动态调整激活限制

管理员可以实时调整许可证的激活数量限制：

```python
# PUT /api/v1/licenses/admin/licenses/{id}/activation-limit/
{
    "new_max_activations": 20,
    "reason": "客户业务扩展需求",
    "effective_date": "2024-09-18T10:00:00Z"
}

# 响应
{
    "success": true,
    "old_limit": 10,
    "new_limit": 20,
    "change_logged": true,
    "audit_id": "audit_20240918_001"
}
```

#### 强制设备解绑

管理员可以强制解绑特定设备：

```python
# DELETE /api/v1/licenses/admin/force-deactivate/
{
    "license_key": "SAPP-PRO-2024-ABCD-EFGH-1234",
    "machine_fingerprint": "fp_550e8400e29b41d4a716446655440000",
    "reason": "设备被盗或丢失"
}
```

### 最佳实践建议

#### 1. 合理设置激活数量

```python
# 根据许可证类型推荐的激活数量
RECOMMENDED_LIMITS = {
    "trial": 1,          # 试用版：单设备体验
    "personal": 2,       # 个人版：个人电脑+笔记本
    "small_business": 5, # 小企业版：小团队使用
    "enterprise": 50,    # 企业版：大规模部署
    "unlimited": 999     # 无限制版：特殊客户
}
```

#### 2. 设备生命周期管理

```python
# 定期清理过期设备绑定
def cleanup_expired_devices():
    """清理长时间未活跃的设备绑定"""
    
    # 超过90天未活跃的设备自动标记为非活跃
    expired_threshold = datetime.now() - timedelta(days=90)
    
    expired_bindings = MachineBinding.objects.filter(
        status='active',
        last_seen_at__lt=expired_threshold
    )
    
    expired_bindings.update(status='inactive')
    
    return expired_bindings.count()
```

#### 3. 客户端优化

```python
class OptimizedLicenseClient:
    def __init__(self):
        self.activation_cache = {}
        self.last_check_time = None
    
    def check_activation_availability(self, license_key):
        """检查激活可用性（带缓存）"""
        cache_key = f"activation_check_{license_key}"
        
        # 检查缓存（5分钟有效期）
        if cache_key in self.activation_cache:
            cached_data, cache_time = self.activation_cache[cache_key]
            if datetime.now() - cache_time < timedelta(minutes=5):
                return cached_data
        
        # 从服务器获取最新状态
        result = self.get_activation_status(license_key)
        self.activation_cache[cache_key] = (result, datetime.now())
        
        return result
```

通过这套完整的设备绑定数量控制机制，系统可以有效防止许可证滥用，确保每个许可证在授权范围内合规使用。

---

## 📚 集成最佳实践

### 1. 客户端库设计

#### 完整的许可证客户端类 (Python)

```python
import logging
from pathlib import Path

class LicenseClient:
    def __init__(self, base_url, logger=None):
        self.base_url = base_url
        self.logger = logger or logging.getLogger(__name__)
        
        # 初始化组件
        self.activator = LicenseActivator(base_url)
        self.verifier = LicenseVerifier(base_url)
        self.heartbeat_manager = HeartbeatManager(base_url)
    
    def initialize(self):
        """初始化许可证客户端"""
        try:
            # 1. 检查服务器状态
            server_status = self.check_server_status()
            if not server_status.get('healthy'):
                self.logger.warning("License server is not healthy")
                return False
            
            # 2. 检查本地激活信息
            activation_info = self.load_activation_info()
            if not activation_info:
                self.logger.info("No activation found, need to activate")
                return False
            
            # 3. 验证激活状态
            is_valid = self.verifier.verify_license()
            if not is_valid:
                self.logger.warning("License verification failed")
                return False
            
            # 4. 启动心跳管理器
            self.heartbeat_manager.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"License initialization failed: {e}")
            return False
    
    def activate(self, license_key):
        """激活许可证"""
        return self.activator.activate_license(license_key)
    
    def get_license_info(self, license_key):
        """获取许可证信息"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/licenses/info/{license_key}/",
                headers={'User-Agent': 'MyApp/2.1.0'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('license_info') if result.get('success') else None
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get license info: {e}")
            return None
    
    def check_server_status(self):
        """检查服务器状态"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/licenses/status/",
                headers={'User-Agent': 'MyApp/2.1.0'},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'healthy': False}
                
        except Exception as e:
            self.logger.error(f"Server status check failed: {e}")
            return {'healthy': False}
    
    def load_activation_info(self):
        """加载激活信息"""
        config_file = self.get_config_file_path()
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load activation info: {e}")
        return None
    
    def get_config_file_path(self):
        """获取配置文件路径"""
        if platform.system() == "Windows":
            config_dir = Path.home() / "AppData" / "Roaming" / "MyApp"
        elif platform.system() == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "MyApp"
        else:  # Linux
            config_dir = Path.home() / ".config" / "MyApp"
        
        return config_dir / "license.json"
    
    def shutdown(self):
        """关闭客户端"""
        if self.heartbeat_manager:
            self.heartbeat_manager.stop()
```

### 2. 错误处理策略

#### 网络错误处理 (Python)

```python
import logging
from datetime import datetime, timedelta
import requests.exceptions

class LicenseErrorHandler:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.consecutive_failures = 0
        self.last_successful_contact = datetime.now()
    
    def should_allow_operation(self, error):
        """判断是否应该允许操作继续"""
        self.consecutive_failures += 1
        now = datetime.now()
        
        if isinstance(error, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
            # 网络错误：允许7天宽限期
            time_since_last_contact = now - self.last_successful_contact
            if time_since_last_contact < timedelta(days=7):
                self.logger.warning(f"Network error, grace period active: {error}")
                return True
        
        elif isinstance(error, requests.exceptions.Timeout):
            # 超时错误：允许3天宽限期
            time_since_last_contact = now - self.last_successful_contact
            if time_since_last_contact < timedelta(days=3):
                self.logger.warning("Request timeout, grace period active")
                return True
        
        # 连续失败超过10次，降低验证频率
        if self.consecutive_failures > 10:
            time_since_last_contact = now - self.last_successful_contact
            return time_since_last_contact < timedelta(days=1)
        
        return False
    
    def record_success(self):
        """记录成功操作"""
        self.consecutive_failures = 0
        self.last_successful_contact = datetime.now()
    
    def get_retry_delay(self):
        """获取重试延迟时间（秒）"""
        if self.consecutive_failures <= 3:
            return 60  # 1分钟
        elif self.consecutive_failures <= 10:
            return 300  # 5分钟
        else:
            return 1800  # 30分钟
```

### 3. 本地配置管理

#### 安全的本地存储 (Python)

```python
import json
import hashlib
import platform
from pathlib import Path
from cryptography.fernet import Fernet
import base64

class SecureLicenseStorage:
    def __init__(self):
        self.config_path = self.get_config_path()
        self.encryption_key = self.derive_key_from_machine()
        self.fernet = Fernet(self.encryption_key)
    
    def get_config_path(self):
        """获取跨平台配置文件路径"""
        if platform.system() == "Windows":
            # Windows: %APPDATA%\MyApp\license.dat
            base_dir = Path.home() / "AppData" / "Roaming"
        elif platform.system() == "Darwin":  # macOS
            # macOS: ~/Library/Application Support/MyApp/license.dat
            base_dir = Path.home() / "Library" / "Application Support"
        else:
            # Linux: ~/.config/MyApp/license.dat
            base_dir = Path.home() / ".config"
        
        return base_dir / "MyApp" / "license.dat"
    
    def save_activation_info(self, data):
        """保存激活信息"""
        try:
            config = {
                "activation_code": data.get('activation_code'),
                "machine_id": data.get('machine_id'),
                "expires_at": data.get('expires_at'),
                "features": data.get('features'),
                "activated_at": datetime.now().isoformat(),
                "checksum": self.calculate_checksum(data)
            }
            
            # 序列化和加密
            json_data = json.dumps(config).encode('utf-8')
            encrypted_data = self.fernet.encrypt(json_data)
            
            # 创建目录并保存文件
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'wb') as f:
                f.write(encrypted_data)
                
            return True
            
        except Exception as e:
            print(f"Failed to save activation info: {e}")
            return False
    
    def load_activation_info(self):
        """加载激活信息"""
        try:
            if not self.config_path.exists():
                return None
            
            # 读取和解密
            with open(self.config_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            config = json.loads(decrypted_data.decode('utf-8'))
            
            # 验证校验和
            if not self.verify_checksum(config):
                self.config_path.unlink()  # 删除损坏的文件
                return None
            
            return {
                "activation_code": config.get('activation_code'),
                "machine_id": config.get('machine_id'),
                "expires_at": config.get('expires_at'),
                "features": config.get('features')
            }
            
        except Exception as e:
            print(f"Failed to load activation info: {e}")
            return None
    
    def derive_key_from_machine(self):
        """从机器信息派生加密密钥"""
        try:
            machine_info = f"{platform.node()}-{platform.processor()}-{platform.system()}"
            # 生成SHA256哈希
            hash_digest = hashlib.sha256(machine_info.encode()).digest()
            # 转换为Fernet兼容的密钥
            return base64.urlsafe_b64encode(hash_digest)
        except Exception:
            # 降级方案
            fallback = "fallback-key-for-encryption-purposes"
            hash_digest = hashlib.sha256(fallback.encode()).digest()
            return base64.urlsafe_b64encode(hash_digest)
    
    def calculate_checksum(self, data):
        """计算数据校验和"""
        try:
            # 创建数据的字符串表示用于校验
            checksum_data = f"{data.get('activation_code', '')}-{data.get('machine_id', '')}"
            return hashlib.md5(checksum_data.encode()).hexdigest()
        except Exception:
            return ""
    
    def verify_checksum(self, config):
        """验证校验和"""
        try:
            stored_checksum = config.get('checksum', '')
            if not stored_checksum:
                return False
            
            # 重新计算校验和
            data = {
                'activation_code': config.get('activation_code'),
                'machine_id': config.get('machine_id')
            }
            calculated_checksum = self.calculate_checksum(data)
            
            return stored_checksum == calculated_checksum
            
        except Exception:
            return False
    
    def clear_activation_info(self):
        """清除激活信息"""
        try:
            if self.config_path.exists():
                self.config_path.unlink()
            return True
        except Exception as e:
            print(f"Failed to clear activation info: {e}")
            return False
```

### 4. 用户界面集成

#### 激活对话框示例 (Python/tkinter)

```python
import tkinter as tk
from tkinter import ttk, messagebox
import threading

class ActivationDialog:
    def __init__(self, license_client):
        self.license_client = license_client
        self.root = tk.Toplevel()
        self.root.title("许可证激活")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        self.setup_ui()
        self.result = None
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 许可证密钥输入
        ttk.Label(main_frame, text="许可证密钥:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.license_key_var = tk.StringVar()
        self.license_key_entry = ttk.Entry(main_frame, textvariable=self.license_key_var, width=50)
        self.license_key_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.license_key_var.trace('w', self.on_license_key_changed)
        
        # 许可证信息显示
        ttk.Label(main_frame, text="许可证信息:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.info_text = tk.Text(main_frame, height=8, width=60, state=tk.DISABLED)
        self.info_text.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 状态标签
        self.status_var = tk.StringVar(value="请输入许可证密钥")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.activate_button = ttk.Button(button_frame, text="激活", command=self.on_activate_click, state=tk.DISABLED)
        self.activate_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.cancel_button = ttk.Button(button_frame, text="取消", command=self.on_cancel_click)
        self.cancel_button.pack(side=tk.RIGHT)
    
    def on_license_key_changed(self, *args):
        """许可证密钥变更事件"""
        license_key = self.license_key_var.get().strip()
        
        if not license_key:
            self.clear_license_info()
            return
        
        # 异步获取许可证信息
        threading.Thread(target=self.fetch_license_info, args=(license_key,), daemon=True).start()
    
    def fetch_license_info(self, license_key):
        """获取许可证信息"""
        try:
            self.root.after(0, lambda: self.status_var.set("正在查询许可证信息..."))
            self.root.after(0, lambda: self.activate_button.config(state=tk.DISABLED))
            
            license_info = self.license_client.get_license_info(license_key)
            
            if license_info:
                self.root.after(0, lambda: self.display_license_info(license_info))
                self.root.after(0, lambda: self.activate_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.status_var.set("许可证有效，可以激活"))
            else:
                self.root.after(0, self.clear_license_info)
                self.root.after(0, lambda: self.status_var.set("许可证无效或不存在"))
                
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"查询失败：{e}"))
    
    def display_license_info(self, license_info):
        """显示许可证信息"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        info_text = f"""产品: {license_info.get('product', {}).get('name', 'N/A')}
版本: {license_info.get('product', {}).get('version', 'N/A')}
方案: {license_info.get('plan', {}).get('name', 'N/A')}
类型: {license_info.get('plan', {}).get('type', 'N/A')}
最大设备数: {license_info.get('max_activations', 'N/A')}
有效期至: {license_info.get('expires_at', 'N/A')}
状态: {license_info.get('status', 'N/A')}"""
        
        self.info_text.insert(tk.END, info_text)
        self.info_text.config(state=tk.DISABLED)
    
    def clear_license_info(self):
        """清除许可证信息"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
        self.activate_button.config(state=tk.DISABLED)
    
    def on_activate_click(self):
        """激活按钮点击事件"""
        license_key = self.license_key_var.get().strip()
        if not license_key:
            return
        
        # 异步激活
        threading.Thread(target=self.activate_license, args=(license_key,), daemon=True).start()
    
    def activate_license(self, license_key):
        """激活许可证"""
        try:
            self.root.after(0, lambda: self.activate_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.progress.start())
            self.root.after(0, lambda: self.status_var.set("正在激活许可证..."))
            
            result = self.license_client.activate(license_key)
            
            if result.get('success'):
                self.root.after(0, lambda: messagebox.showinfo("激活成功", "许可证激活成功！"))
                self.result = True
                self.root.after(0, self.root.destroy)
            else:
                error_message = self.get_user_friendly_error(
                    result.get('error', '激活失败'), 
                    result.get('code', '')
                )
                self.root.after(0, lambda: messagebox.showerror("激活失败", error_message))
                self.root.after(0, lambda: self.status_var.set("激活失败"))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"激活过程中发生错误：{e}"))
            self.root.after(0, lambda: self.status_var.set("激活失败"))
        
        finally:
            self.root.after(0, lambda: self.activate_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.progress.stop())
    
    def get_user_friendly_error(self, error, code):
        """获取用户友好的错误信息"""
        error_messages = {
            "LICENSE_NOT_FOUND": "许可证不存在，请检查密钥是否正确。",
            "LICENSE_EXPIRED": "许可证已过期，请联系供应商续费。",
            "MAX_ACTIVATIONS_REACHED": "已达到最大激活数限制，请先停用其他设备。",
            "LICENSE_REVOKED": "许可证已被撤销，请联系供应商。",
            "RATE_LIMITED": "激活请求过于频繁，请稍后再试。",
            "SUSPICIOUS_ACTIVITY": "激活请求被安全系统标记，请联系技术支持。"
        }
        
        return error_messages.get(code, f"激活失败：{error}")
    
    def on_cancel_click(self):
        """取消按钮点击事件"""
        self.result = False
        self.root.destroy()
    
    def show(self):
        """显示对话框"""
        self.root.grab_set()
        self.root.wait_window()
        return self.result

# 使用示例
def show_activation_dialog(license_client):
    dialog = ActivationDialog(license_client)
    return dialog.show()
```

---

## 🔧 故障排除指南

### 常见错误及解决方案

#### 1. 网络连接问题
**症状**: 请求超时或连接失败
**解决方案**:
- 检查网络连接
- 验证服务器URL是否正确
- 检查防火墙设置
- 尝试使用代理服务器

#### 2. 许可证验证失败
**症状**: 返回`LICENSE_NOT_FOUND`错误
**解决方案**:
- 验证许可证密钥格式是否正确
- 检查许可证是否已过期或被撤销
- 确认许可证服务器版本兼容性

#### 3. 机器指纹不匹配
**症状**: 返回`FINGERPRINT_MISMATCH`错误
**解决方案**:
- 检查硬件是否有重大变更
- 重新生成机器指纹
- 联系管理员重置许可证绑定

#### 4. 频率限制
**症状**: 返回`RATE_LIMITED`错误
**解决方案**:
- 等待限制时间过后再试
- 检查是否有重复的激活请求
- 优化心跳发送频率

#### 5. macOS 特定问题

##### 5.1 权限拒绝问题
**症状**: 无法访问硬件信息或系统命令失败
**解决方案**:
- 检查应用程序是否有必要的权限
- 在系统偏好设置中授权应用程序访问系统信息
- 对于沙盒应用，确保 entitlements 文件包含必要权限

##### 5.2 命令行工具不可用
**症状**: `system_profiler` 或 `ioreg` 命令执行失败
**解决方案**:
- 确保命令行工具可用（通常预装在 macOS 中）
- 检查应用程序是否有执行外部命令的权限
- 使用降级方案（基于 Environment 类的信息）

##### 5.3 Apple Silicon 兼容性问题
**症状**: 在 M1/M2 Mac 上硬件指纹不一致
**解决方案**:
- 确保使用 ARM64 版本的 .NET 运行时
- 验证硬件信息收集代码支持 Apple Silicon
- 检查架构特定的硬件标识符

##### 5.4 App Store 沙盒限制
**症状**: 在 Mac App Store 版本中某些功能不工作
**解决方案**:
- 调整配置文件路径到沙盒容器目录
- 使用沙盒兼容的硬件信息获取方式
- 在 entitlements 中声明网络和文件系统权限

### 调试工具

#### 网络请求调试 (Python)

```python
import logging
import json

class LicenseDebugger:
    def __init__(self, enabled=False):
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)
        
        if enabled:
            logging.basicConfig(level=logging.DEBUG)
    
    def log_request(self, method, url, data=None, headers=None):
        """记录请求信息"""
        if not self.enabled:
            return
            
        self.logger.debug(f"Request: {method} {url}")
        
        if headers:
            self.logger.debug(f"Request Headers: {json.dumps(headers, indent=2)}")
        
        if data:
            try:
                if isinstance(data, dict):
                    self.logger.debug(f"Request Body: {json.dumps(data, indent=2)}")
                else:
                    self.logger.debug(f"Request Body: {data}")
            except Exception:
                self.logger.debug(f"Request Body: {str(data)}")
    
    def log_response(self, response):
        """记录响应信息"""
        if not self.enabled:
            return
            
        self.logger.debug(f"Response Status: {response.status_code}")
        self.logger.debug(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            self.logger.debug(f"Response Body: {json.dumps(response_data, indent=2)}")
        except Exception:
            self.logger.debug(f"Response Body: {response.text}")
    
    def log_error(self, error, context=""):
        """记录错误信息"""
        if not self.enabled:
            return
            
        self.logger.error(f"Error {context}: {error}")
        if hasattr(error, '__traceback__'):
            import traceback
            self.logger.error(f"Traceback: {''.join(traceback.format_tb(error.__traceback__))}")

# 使用示例
debugger = LicenseDebugger(enabled=True)

class DebuggingLicenseClient(LicenseClient):
    def __init__(self, base_url, debug=False):
        super().__init__(base_url)
        self.debugger = LicenseDebugger(enabled=debug)
    
    def activate(self, license_key):
        """带调试功能的激活方法"""
        try:
            hardware_info = get_hardware_info()
            client_info = {
                "version": "2.1.0",
                "build": "20240915.1",
                "language": "zh-CN",
                "install_path": str(Path.cwd())
            }
            
            request_data = {
                "license_key": license_key,
                "hardware_info": hardware_info,
                "client_info": client_info
            }
            
            # 记录请求
            self.debugger.log_request(
                "POST", 
                f"{self.base_url}/api/v1/licenses/activate/",
                request_data,
                self.session.headers
            )
            
            response = self.session.post(
                f"{self.base_url}/api/v1/licenses/activate/",
                json=request_data,
                timeout=30
            )
            
            # 记录响应
            self.debugger.log_response(response)
            
            result = response.json()
            
            if result.get('success'):
                self.save_activation_info(result['data'])
                return {"success": True, "data": result['data']}
            else:
                return {"success": False, "error": result.get('error', 'Activation failed')}
                
        except Exception as e:
            self.debugger.log_error(e, "during license activation")
            return {"success": False, "error": "激活过程出现异常", "code": "UNKNOWN_ERROR"}
```

---

## 📊 监控和统计

### 客户端监控

建议在客户端实现以下监控功能：

1. **激活成功率监控**
2. **心跳发送成功率监控**
3. **网络延迟统计**
4. **错误类型统计**
5. **功能使用统计**

### 服务器端分析

服务器端可以基于收集的数据进行以下分析：

1. **用户活跃度分析**
2. **功能使用热点分析**
3. **设备性能统计**
4. **异常行为检测**
5. **许可证利用率分析**

---

## 📝 总结

本文档详细介绍了许可证激活API的使用方法，包括：

1. **完整的API规范** - 详细的请求/响应格式
2. **实际的代码示例** - 可直接使用的实现代码
3. **最佳实践指导** - 安全性和可靠性建议
4. **故障排除指南** - 常见问题的解决方案

### 🆕 v1.3 更新要点

本次更新主要针对RIPER-5方案A重构进行字段名称调整：

- **语义明确化**: 区分方案模板配置与许可证实际使用值
- **字段重命名**: `max_machines` → `default_max_activations`、`validity_days` → `default_validity_days`
- **向后兼容**: 提供迁移指南和兼容性处理方案
- **数据结构说明**: 增加详细的对比和解释

通过遵循本文档的指导，您可以构建一个稳定、安全、用户友好的许可证管理系统。

---

*文档版本: 1.3 - 方案A重构字段更新*  
*最后更新: 2024年9月26日*

### 📝 更新记录

- **v1.3** (2024-09-26): 更新字段名称以匹配RIPER-5方案A重构（max_machines → default_max_activations）
- **v1.2** (2024-09-18): 添加详细的设备绑定数量控制机制说明
- **v1.1** (2024-09-18): 完整的macOS跨平台支持和Python实现
- **v1.0** (2024-09-15): 初始版本，基础API文档

### 📱 平台支持矩阵

| 功能 | Windows | macOS | Linux | 说明 |
|------|---------|-------|-------|------|
| 硬件UUID生成 | ✅ WMI | ✅ system_profiler | ✅ machine-id | 多重降级方案 |
| CPU信息获取 | ✅ WMI | ✅ sysctl | ✅ /proc/cpuinfo | 跨平台兼容 |
| 内存使用监控 | ✅ WMI | ✅ vm_stat | ✅ /proc/meminfo | 平台特定实现 |
| 网络MAC地址 | ✅ 通用 | ✅ ifconfig | ✅ 通用 | .NET跨平台API |
| 配置文件存储 | ✅ %APPDATA% | ✅ ~/Library | ✅ ~/.config | 遵循平台规范 |
| 设备绑定控制 | ✅ 完整支持 | ✅ 完整支持 | ✅ 完整支持 | 统一的数量限制机制 |
| 沙盒兼容性 | ✅ | ⚠️ 有限制 | ✅ | App Store需特殊处理 |
