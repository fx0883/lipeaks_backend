# 激活场景与处理指南

## 概述

本文档详细说明了各种不同的许可证激活场景，以及每种场景的处理流程和最佳实践。

## 场景分类

### 1. 首次激活场景

#### 1.1 标准首次激活

**适用情况：** 用户首次在新设备上安装和使用软件

**流程步骤：**

1. **软件启动检查**
   ```
   启动 → 检查本地激活信息 → 无激活信息 → 显示激活界面
   ```

2. **用户输入许可证密钥**
   - 显示格式化输入框（XXXXX-XXXXX-XXXXX-XXXXX-XXXXX）
   - 实时验证格式
   - 支持粘贴和自动格式化

3. **预激活验证**
   ```
   API调用: GET /info/{license_key}/
   目的: 验证许可证有效性和获取基本信息
   ```

4. **收集硬件信息**
   - 自动收集系统硬件信息
   - 生成唯一的硬件UUID
   - 创建机器指纹

5. **执行激活**
   ```
   API调用: POST /activate/
   结果: 获取激活码和授权功能列表
   ```

6. **保存激活信息**
   - 本地存储激活码
   - 保存机器指纹
   - 记录激活时间和过期时间

**示例代码流程：**
```
function firstTimeActivation(licenseKey) {
    // 1. 验证许可证
    licenseInfo = await getLicenseInfo(licenseKey)
    if (!licenseInfo.success) {
        showError(licenseInfo.error)
        return
    }
    
    // 2. 收集硬件信息
    hardwareInfo = collectHardwareInfo()
    
    // 3. 执行激活
    result = await activateLicense(licenseKey, hardwareInfo)
    if (result.success) {
        saveActivationInfo(result.data)
        showSuccessMessage()
        startApplication()
    } else {
        showError(result.error)
    }
}
```

#### 1.2 企业批量激活

**适用情况：** 企业环境中的批量部署

**特点：**
- 使用企业版许可证（支持多次激活）
- 可能需要企业内部认证
- 支持静默激活

**流程差异：**

1. **配置文件激活**
   ```json
   // activation_config.json
   {
       "license_key": "7C162-2DC76-F944D-D9AA4-F408E",
       "tenant_id": "123",
       "server_url": "https://license.company.com",
       "silent_mode": true
   }
   ```

2. **自动激活流程**
   ```
   启动 → 读取配置文件 → 自动收集硬件信息 → 后台激活 → 记录日志
   ```

3. **集中管理**
   - 企业管理员可查看所有激活设备
   - 支持远程撤销激活
   - 统一的许可证池管理

### 2. 重新激活场景

#### 2.1 硬件升级后重新激活

**适用情况：** 用户升级了关键硬件组件

**检测标准：**
- CPU更换
- 主板更换
- 硬盘更换
- 内存大幅变化

**处理流程：**

1. **检测硬件变化**
   ```
   当前指纹 vs 存储的指纹 → 差异超过阈值 → 触发重新激活
   ```

2. **验证现有激活**
   ```
   API调用: POST /verify/
   结果: 验证失败（机器指纹不匹配）
   ```

3. **显示重新激活界面**
   - 说明检测到硬件变化
   - 要求用户确认重新激活
   - 提供联系支持的选项

4. **执行重新激活**
   - 使用相同的许可证密钥
   - 更新硬件信息
   - 生成新的激活码

**界面提示示例：**
```
检测到硬件变化

我们检测到您的计算机硬件发生了重大变化。
为了继续使用软件，需要重新激活您的许可证。

[重新激活] [联系支持] [取消]

注意：重新激活不会影响您的数据和设置。
```

#### 2.2 系统重装后激活

**适用情况：** 用户重装操作系统或迁移到新设备

**挑战：**
- 可能无法访问原有的激活信息
- 需要验证用户身份
- 可能触发安全检查

**处理流程：**

1. **尝试使用原许可证密钥**
   ```
   用户输入许可证密钥 → 收集新系统硬件信息 → 尝试激活
   ```

2. **处理激活数量限制**
   - 如果达到最大激活数，显示详细错误信息
   - 提供现有激活设备的信息（如果可用）
   - 引导用户进行设备管理

3. **自助式设备管理**
   ```
   显示消息: "您的许可证已在以下设备上激活："
   
   设备1: Windows 10 - USER-DESKTOP - 最后使用: 2024-01-10
   [撤销激活]
   
   设备2: macOS 14 - MacBook-Pro - 最后使用: 2024-01-15
   [撤销激活]
   ```

### 3. 验证场景

#### 3.1 定期验证

**验证时机：**
- 软件启动时（每次）
- 运行期间（每24小时）
- 网络连接恢复后
- 检测到系统时间变化后

**验证流程：**

```
读取本地激活信息 → 调用验证API → 更新验证时间戳 → 处理验证结果
```

**验证结果处理：**

1. **验证成功**
   ```json
   {
       "valid": true,
       "license_info": {...},
       "last_verified": "2024-01-15T10:30:00Z"
   }
   ```
   - 更新本地验证时间
   - 正常运行

2. **验证失败**
   ```json
   {
       "valid": false,
       "error": "License has expired",
       "code": "LICENSE_EXPIRED"
   }
   ```
   - 根据错误类型采取不同措施
   - 可能需要重新激活或升级许可证

#### 3.2 离线验证

**适用情况：** 网络不可用或用户选择离线模式

**验证策略：**

1. **宽限期验证**
   ```
   最后在线验证时间 + 72小时 > 当前时间 → 允许离线使用
   ```

2. **功能限制模式**
   ```
   离线超过7天 → 限制高级功能 → 仅允许基本操作
   ```

3. **完全离线模式**
   ```
   离线超过30天 → 显示续费提醒 → 提供紧急联系方式
   ```

**实现示例：**
```
function offlineVerification() {
    lastVerified = getLastVerifiedTime()
    currentTime = getCurrentTime()
    
    offlineHours = (currentTime - lastVerified) / (1000 * 60 * 60)
    
    if (offlineHours < 72) {
        return { status: "full_access", message: "离线模式，完整功能" }
    } else if (offlineHours < 168) {  // 7天
        return { status: "limited_access", message: "离线模式，功能受限" }
    } else {
        return { status: "renewal_required", message: "需要续费或联网验证" }
    }
}
```

### 4. 异常场景处理

#### 4.1 许可证过期

**检测方式：**
- 验证API返回过期错误
- 本地检查过期时间

**处理策略：**

1. **提前通知（30天前）**
   ```
   显示温馨提醒: "您的许可证将在30天后过期，请及时续费。"
   [立即续费] [稍后提醒] [不再提醒]
   ```

2. **临近过期（7天前）**
   ```
   每次启动显示: "许可证即将过期！还有X天到期。"
   [立即续费] [查看详情]
   ```

3. **已过期**
   ```
   阻止启动，显示: "许可证已过期，请续费后继续使用。"
   [购买许可证] [输入新密钥] [联系销售]
   ```

#### 4.2 网络连接问题

**场景分析：**

1. **临时网络中断**
   - 使用缓存的验证结果
   - 显示离线工作提示
   - 自动重试连接

2. **防火墙阻止**
   - 提供防火墙配置指南
   - 显示需要开放的端口和域名
   - 提供代理设置选项

3. **服务器维护**
   - 显示维护通知
   - 估计恢复时间
   - 允许离线继续工作

**网络诊断工具：**
```
function networkDiagnostics() {
    // 1. 检查基本网络连接
    if (!isNetworkAvailable()) {
        return "无网络连接"
    }
    
    // 2. 检查DNS解析
    if (!canResolveDNS("license-server.com")) {
        return "DNS解析失败"
    }
    
    // 3. 检查服务器可达性
    if (!canReachServer()) {
        return "服务器不可达，可能被防火墙阻止"
    }
    
    // 4. 检查API响应
    status = checkServerStatus()
    return status
}
```

#### 4.3 激活数量超限

**错误信息：**
```json
{
    "success": false,
    "error": "Maximum activations (5) reached",
    "code": "MAX_ACTIVATIONS_REACHED"
}
```

**处理界面：**
```
激活数量已达上限

您的许可证最多支持5个设备同时激活，
当前已在5个设备上激活。

当前激活的设备：
1. Windows 10 - DESKTOP-001 (最后使用: 2024-01-10)
2. macOS 14 - MacBook-Pro (最后使用: 2024-01-15)
3. Ubuntu 22.04 - Server-001 (最后使用: 2024-01-12)
4. Windows 11 - LAPTOP-456 (最后使用: 2024-01-14)
5. macOS 13 - iMac-Studio (最后使用: 2024-01-13)

您可以：
[撤销闲置设备] [购买更多激活数] [联系支持]
```

### 5. 特殊场景

#### 5.1 虚拟机环境

**挑战：**
- 虚拟机的硬件信息可能变化
- 虚拟机克隆导致重复激活
- 虚拟化层的影响

**检测方式：**
```
function detectVirtualization() {
    indicators = [
        checkCPUBrand(),      // "VMware", "VirtualBox", "QEMU"
        checkSystemModel(),   // "VMware Virtual Platform"
        checkDrivers(),       // 虚拟化相关驱动
        checkMAC()           // 虚拟化厂商的MAC地址段
    ]
    
    return analyzeVirtualizationIndicators(indicators)
}
```

**处理策略：**
- 对虚拟机使用更宽松的硬件指纹策略
- 提醒用户虚拟机环境的限制
- 提供专用的虚拟机许可证类型

#### 5.2 云环境部署

**特点：**
- 实例可能随时重启
- 硬件标识符可能变化
- 需要持久化存储激活信息

**解决方案：**

1. **云实例标识**
   ```json
   {
       "cloud_provider": "AWS",
       "instance_id": "i-1234567890abcdef0",
       "instance_type": "t3.large",
       "availability_zone": "us-west-2a"
   }
   ```

2. **持久化激活**
   - 使用云存储保存激活信息
   - 实例重启后自动恢复激活状态
   - 支持弹性扩缩容

#### 5.3 开发测试环境

**需求：**
- 开发者需要频繁重装系统
- 测试环境需要隔离
- 可能需要多版本并存

**特殊处理：**

1. **开发者许可证**
   - 更高的激活次数限制
   - 快速重新激活机制
   - 开发工具集成

2. **测试环境标识**
   ```json
   {
       "environment_type": "development",
       "developer_id": "dev001",
       "project_id": "project-abc"
   }
   ```

## 最佳实践建议

### 1. 用户体验优化

**友好的错误消息：**
```
❌ 技术性错误: "FINGERPRINT_MISMATCH"
✅ 用户友好: "检测到硬件变化，需要重新激活许可证"
```

**进度指示：**
```
正在激活许可证...
[▓▓▓▓▓░░░] 60% - 验证许可证信息
```

**上下文帮助：**
```
需要帮助？
• 如何找到我的许可证密钥？
• 什么是硬件指纹？
• 为什么需要重新激活？
```

### 2. 安全考虑

**防止滥用：**
- 限制激活频率
- 检测可疑激活模式
- 记录详细的审计日志

**数据保护：**
- 加密存储敏感信息
- 不记录完整的许可证密钥
- 遵循数据隐私法规

### 3. 性能优化

**缓存策略：**
- 缓存验证结果
- 预加载许可证信息
- 智能重试机制

**异步处理：**
```
// 后台验证
async function backgroundVerification() {
    try {
        result = await verifyActivation()
        updateLocalCache(result)
    } catch (error) {
        scheduleRetry(error)
    }
}
```

---

**下一步：** 查看 [错误处理指南](./error_handling.md) 了解完整的错误处理机制
