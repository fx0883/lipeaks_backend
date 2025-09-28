# 错误处理与故障排除指南

## 概述

本文档详细说明了许可证激活和验证过程中可能遇到的各种错误，以及相应的处理策略和故障排除方法。

## 错误分类体系

### 1. 网络相关错误

#### 1.1 网络连接失败

**错误特征：**
- 无法连接到许可证服务器
- DNS解析失败
- 连接超时

**错误代码：** `NETWORK_ERROR`

**处理策略：**

```
function handleNetworkError(error) {
    // 1. 检查网络连接
    if (!isNetworkAvailable()) {
        showMessage("请检查网络连接", "warning")
        return enableOfflineMode()
    }
    
    // 2. 尝试备用服务器
    if (hasBackupServers()) {
        return retryWithBackupServer()
    }
    
    // 3. 启用离线模式
    return enableOfflineMode()
}
```

**用户界面提示：**
```
网络连接问题

无法连接到许可证服务器，这可能是由于：
• 网络连接不稳定
• 防火墙阻止了连接
• 服务器临时不可用

建议解决方案：
[检查网络] [配置代理] [离线工作] [联系支持]
```

#### 1.2 防火墙阻止

**检测方式：**
- 连接被拒绝（Connection refused）
- 连接超时但基本网络正常

**解决指南：**

```
防火墙配置指南

请确保以下端口和域名未被阻止：

端口：
• HTTPS: 443
• HTTP: 80 (仅用于重定向)

域名白名单：
• license-server.yourcompany.com
• api.licensingsystem.com

企业防火墙配置：
• 允许出站HTTPS连接
• 信任SSL证书颁发机构
• 配置代理服务器设置（如需要）
```

#### 1.3 代理服务器问题

**常见场景：**
- 企业网络需要代理
- 代理需要身份验证
- 代理配置错误

**处理流程：**

```
function configureProxy() {
    // 1. 自动检测代理设置
    proxySettings = detectSystemProxy()
    
    // 2. 如果检测失败，提示用户手动配置
    if (!proxySettings) {
        return showProxyConfigDialog()
    }
    
    // 3. 测试代理连接
    if (testProxyConnection(proxySettings)) {
        saveProxySettings(proxySettings)
        return true
    } else {
        return promptForProxyAuth()
    }
}
```

**代理配置界面：**
```
代理服务器设置

代理类型: [HTTP] [HTTPS] [SOCKS5]
服务器地址: [________________]
端口: [____]

身份验证:
□ 需要身份验证
用户名: [________________]
密码: [________________]

[测试连接] [保存设置] [取消]
```

### 2. 许可证相关错误

#### 2.1 许可证无效

**错误代码：** `INVALID_LICENSE`

**可能原因：**
- 许可证密钥格式错误
- 许可证不存在
- 许可证已被删除

**处理方式：**

```json
{
    "success": false,
    "error": "Invalid license key format",
    "code": "INVALID_LICENSE",
    "details": {
        "validation_errors": [
            "License key must be 25 characters long",
            "Invalid characters detected"
        ]
    }
}
```

**用户界面：**
```
许可证密钥无效

请检查您输入的许可证密钥是否正确：
• 密钥应为25个字符，格式：XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
• 请确认没有输入错误的字符（如0和O，1和I）
• 密钥区分大小写

[重新输入] [联系销售] [查看购买记录]
```

#### 2.2 许可证已过期

**错误代码：** `LICENSE_EXPIRED`

**处理策略：**

```
function handleExpiredLicense(licenseInfo) {
    expiredDate = licenseInfo.expires_at
    daysSinceExpired = calculateDaysSince(expiredDate)
    
    if (daysSinceExpired <= 7) {
        // 宽限期内
        return showGracePeriodMessage(7 - daysSinceExpired)
    } else {
        // 超出宽限期
        return showRenewalDialog()
    }
}
```

**宽限期提示：**
```
许可证已过期 (宽限期)

您的许可证于 2024-01-01 过期，但您仍有 3 天的宽限期。

在宽限期内，您可以继续使用所有功能。
宽限期结束后，功能将受到限制。

[立即续费] [查看续费选项] [稍后提醒]
```

**续费界面：**
```
许可证续费

您的许可证已过期 15 天。
当前产品：MyProduct Professional
原许可证：XXXXX-XXXXX-XXXXX-XXXXX-XXXXX

续费选项：
• 1年续费 - $299
• 2年续费 - $499 (节省$99)
• 升级到企业版 - $599

[在线续费] [输入新密钥] [联系销售]
```

#### 2.3 许可证已撤销

**错误代码：** `LICENSE_REVOKED`

**可能原因：**
- 违反使用条款
- 退款请求
- 安全问题

**处理方式：**
```
许可证已撤销

您的许可证已被撤销，无法继续使用。

撤销原因：超出允许的使用范围
撤销时间：2024-01-15 10:30:00

如果您认为这是错误，请联系我们的支持团队。

[联系支持] [查看详情] [购买新许可证]

支持邮箱：support@yourcompany.com
支持电话：1-800-123-4567
```

### 3. 激活相关错误

#### 3.1 达到最大激活数量

**错误代码：** `MAX_ACTIVATIONS_REACHED`

**详细错误信息：**
```json
{
    "success": false,
    "error": "Maximum activations (5) reached",
    "code": "MAX_ACTIVATIONS_REACHED",
    "details": {
        "max_allowed": 5,
        "current_count": 5,
        "active_devices": [
            {
                "machine_id": "MACHINE-001",
                "os": "Windows 10",
                "hostname": "DESKTOP-ABC",
                "last_seen": "2024-01-15T10:30:00Z"
            }
        ]
    }
}
```

**设备管理界面：**
```
激活数量已达上限

您的许可证最多允许在 5 个设备上激活，当前已全部使用。

当前激活的设备：
┌────────────────────────────────────────────────────────┐
│ Windows 10 - DESKTOP-ABC    最后使用: 2小时前           │
│ [撤销激活]                                              │
├────────────────────────────────────────────────────────┤
│ macOS 14 - MacBook-Pro     最后使用: 1天前             │
│ [撤销激活]                                              │
├────────────────────────────────────────────────────────┤
│ Ubuntu 22.04 - SERVER-01   最后使用: 3天前             │
│ [撤销激活]                                              │
└────────────────────────────────────────────────────────┘

您可以：
[撤销闲置设备] [购买更多激活数] [升级许可证]
```

#### 3.2 硬件指纹不匹配

**错误代码：** `FINGERPRINT_MISMATCH`

**检测场景：**
- 硬件组件更换
- 虚拟机配置变化
- 系统重装

**处理流程：**

```
function handleFingerprintMismatch(error) {
    // 1. 分析硬件变化程度
    changeLevel = analyzeHardwareChanges(error.details)
    
    if (changeLevel === "minor") {
        // 轻微变化，自动重新绑定
        return autoReactivate()
    } else if (changeLevel === "major") {
        // 重大变化，需要用户确认
        return showReactivationDialog()
    } else {
        // 可疑变化，需要额外验证
        return requestAdditionalVerification()
    }
}
```

**重新激活界面：**
```
检测到硬件变化

我们检测到您的计算机硬件发生了变化：

变化详情：
• CPU: Intel i5-8400 → Intel i7-9700
• 内存: 8GB → 16GB
• 硬盘: HDD 1TB → SSD 512GB

这可能是由于硬件升级造成的。
为了继续使用软件，需要重新激活您的许可证。

□ 我确认这是我的设备，只是进行了硬件升级

[重新激活] [这不是我的设备] [联系支持]
```

### 4. 服务器相关错误

#### 4.1 服务器维护

**错误代码：** `MAINTENANCE_MODE`

**响应示例：**
```json
{
    "success": false,
    "error": "Server is under maintenance",
    "code": "MAINTENANCE_MODE",
    "details": {
        "maintenance_start": "2024-01-15T02:00:00Z",
        "estimated_completion": "2024-01-15T04:00:00Z",
        "message": "Scheduled maintenance for system upgrades"
    }
}
```

**用户通知：**
```
服务器维护通知

许可证服务器正在进行计划维护：
• 开始时间：2024年1月15日 10:00 (UTC+8)
• 预计结束：2024年1月15日 12:00 (UTC+8)
• 维护内容：系统升级和安全更新

在维护期间：
• 已激活的软件可正常使用
• 无法进行新的激活或验证
• 心跳检测将自动延期

我们为此带来的不便深表歉意。

[了解详情] [确定]
```

#### 4.2 服务器过载

**错误代码：** `SERVER_OVERLOADED`

**处理策略：**

```
function handleServerOverload(error) {
    retryAfter = error.details?.retry_after || 300  // 默认5分钟后重试
    
    // 显示友好提示
    showMessage(
        `服务器繁忙，将在${retryAfter}秒后自动重试`,
        "info"
    )
    
    // 自动重试
    setTimeout(() => {
        retryActivation()
    }, retryAfter * 1000)
}
```

### 5. 客户端相关错误

#### 5.1 硬件信息收集失败

**错误代码：** `HARDWARE_INFO_ERROR`

**可能原因：**
- 权限不足
- 系统API不可用
- 安全软件阻止

**处理方式：**

```
function collectHardwareInfoSafely() {
    try {
        return collectFullHardwareInfo()
    } catch (error) {
        if (error.type === "PERMISSION_DENIED") {
            return collectBasicHardwareInfo()  // 降级收集
        } else {
            return generateFallbackInfo()      // 生成备用信息
        }
    }
}
```

**权限请求界面：**
```
需要系统权限

为了生成设备指纹，软件需要访问以下系统信息：
• 处理器信息（型号、核心数）
• 内存配置（总量、类型）
• 存储设备（容量、序列号）
• 网络适配器（MAC地址）

这些信息仅用于许可证激活，不会上传个人数据。

[授予权限] [了解详情] [取消]
```

#### 5.2 本地存储失败

**错误代码：** `STORAGE_ERROR`

**处理策略：**

```
function saveActivationInfoSafely(data) {
    try {
        // 优先使用加密存储
        return saveToSecureStorage(data)
    } catch (error) {
        try {
            // 降级到普通文件存储
            return saveToFileSystem(data)
        } catch (fallbackError) {
            // 最后使用内存存储（临时）
            return saveToMemory(data)
        }
    }
}
```

### 6. 安全相关错误

#### 6.1 可疑活动检测

**错误代码：** `SUSPICIOUS_ACTIVITY`

**触发条件：**
- 短时间内多次激活尝试
- 来自可疑IP地址
- 异常的硬件模式

**处理流程：**

```
可疑活动检测

我们检测到以下可疑活动：
• 1小时内尝试激活5次
• 来源IP：192.168.1.100
• 检测时间：2024-01-15 10:30:00

为了保护您的许可证安全，我们已临时限制激活功能。

如果这是您的正常操作，请：
1. 等待1小时后重试
2. 或联系我们的支持团队验证身份

[联系支持] [了解详情] [确定]
```

#### 6.2 时间篡改检测

**错误代码：** `TIME_MANIPULATION`

**检测方式：**
- 系统时间与网络时间差异过大
- 时间倒退检测
- 时区异常变化

**处理方式：**

```
系统时间异常

检测到系统时间可能被人为修改：
• 系统时间：2023-06-15 10:30:00
• 网络时间：2024-01-15 10:30:00
• 时间差异：7个月

这可能导致许可证验证失败。
请确保系统时间准确，或联系支持团队。

[同步系统时间] [忽略警告] [联系支持]
```

## 错误恢复策略

### 1. 自动重试机制

**指数退避算法：**

```
function exponentialBackoff(attempt, baseDelay = 1000, maxDelay = 30000) {
    delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay)
    jitter = Math.random() * 0.1 * delay  // 添加随机性
    return delay + jitter
}

async function retryWithBackoff(operation, maxAttempts = 5) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
            return await operation()
        } catch (error) {
            if (attempt === maxAttempts - 1) throw error
            
            delay = exponentialBackoff(attempt)
            await sleep(delay)
        }
    }
}
```

### 2. 降级处理

**功能降级策略：**

```
function gracefulDegradation(error) {
    switch (error.code) {
        case "NETWORK_ERROR":
            return enableOfflineMode()
        
        case "LICENSE_EXPIRED":
            return enableGracePeriodMode()
        
        case "FEATURE_RESTRICTED":
            return enableBasicMode()
        
        default:
            return showErrorDialog(error)
    }
}
```

### 3. 用户引导

**分步错误解决：**

```
错误解决向导

步骤 1/3: 检查网络连接
[●○○] 正在检查网络连接...
✓ 网络连接正常

步骤 2/3: 验证许可证
[●●○] 正在验证许可证...
✗ 许可证已过期

步骤 3/3: 解决方案
[●●●] 
建议操作：
• 联系管理员续费许可证
• 或输入新的许可证密钥

[续费许可证] [输入新密钥] [联系支持]
```

## 日志记录与诊断

### 1. 错误日志格式

```json
{
    "timestamp": "2024-01-15T10:30:00.123Z",
    "level": "ERROR",
    "category": "license_activation",
    "error_code": "MAX_ACTIVATIONS_REACHED",
    "message": "Maximum activations (5) reached",
    "context": {
        "license_key_hash": "abc123...",
        "machine_id": "MACHINE-12345",
        "user_id": "user@example.com",
        "session_id": "SESSION-789"
    },
    "stack_trace": "...",
    "user_agent": "MyApp/1.0.0",
    "ip_address": "192.168.1.100"
}
```

### 2. 诊断信息收集

```
诊断信息报告

系统信息：
• 操作系统：Windows 10 Pro (19041)
• 软件版本：MyApp v1.0.0 (Build 20240115)
• 许可证状态：已激活
• 最后验证：2024-01-15 10:25:00

网络信息：
• 公网IP：203.0.113.1
• 代理：无
• DNS服务器：8.8.8.8

错误历史（最近10条）：
1. 2024-01-15 10:30:00 - NETWORK_ERROR
2. 2024-01-15 10:25:00 - VERIFICATION_SUCCESS
...

[导出完整报告] [发送给支持] [清除历史]
```

## 用户支持

### 1. 自助服务

**常见问题解答：**

```
常见问题

Q: 为什么提示"激活数量已达上限"？
A: 您的许可证已在允许的最大设备数上激活。您可以：
   • 撤销不再使用的设备上的激活
   • 购买支持更多设备的许可证
   • 联系我们升级现有许可证

Q: 硬件升级后无法使用软件？
A: 这是正常现象。硬件变化会影响设备指纹，需要重新激活：
   • 使用原许可证密钥重新激活
   • 如果遇到问题，请联系技术支持
   
[查看更多] [联系支持]
```

### 2. 支持渠道

**联系方式：**

```
获取帮助

技术支持：
📧 support@yourcompany.com
📞 1-800-123-4567
💬 在线客服：周一至周五 9:00-18:00

销售咨询：
📧 sales@yourcompany.com
📞 1-800-987-6543

紧急支持（24小时）：
📧 emergency@yourcompany.com
📞 1-800-911-HELP

在线资源：
🌐 帮助文档：help.yourcompany.com
🎥 视频教程：youtube.com/yourcompany
💬 用户论坛：forum.yourcompany.com
```

---

**完成！** 现在您已经有了完整的客户端许可证激活与集成文档。每个文档都涵盖了不同的方面，为您的开发团队提供了详细的指导。
