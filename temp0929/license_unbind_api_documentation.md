# 许可证解绑API文档

## 概述

许可证解绑API允许客户端主动解除机器与许可证的绑定关系，释放激活配额供其他设备使用。这是一个无需认证的公开API，但包含多重安全验证机制。

## 基本信息

- **接口地址**: `POST /api/v1/licenses/unbind/`
- **请求方式**: `POST`
- **认证方式**: 无需token认证
- **内容类型**: `application/json`
- **频率限制**: 100次/小时

## 请求参数

### 必需参数

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `activation_code` | string | ✅ | 激活码，格式：XXXX-XXXX-XXXX-XXXX |
| `license_key` | string | ✅ | 许可证密钥，格式：XXXXX-XXXXX-XXXXX-XXXXX-XXXXX |
| `machine_fingerprint` | string | ✅ | 机器指纹，64位哈希字符串 |

### 可选参数

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `hardware_info` | object | ❌ | `{}` | 机器硬件信息，用于额外验证 |
| `reason` | string | ❌ | "用户主动解绑" | 解绑原因，最大500字符 |

### 参数详细说明

#### activation_code
- **格式**: `XXXX-XXXX-XXXX-XXXX`
- **示例**: `"ABCD-1234-EFGH-5678"`
- **说明**: 设备激活时获得的激活码
- **验证**: 自动移除格式化字符，最少8个字符

#### license_key
- **格式**: `XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`
- **示例**: `"A1B2C-D3E4F-G5H6I-J7K8L-M9N0P"`
- **说明**: 软件许可证密钥
- **验证**: 自动移除格式化字符，最少10个字符

#### machine_fingerprint
- **格式**: 64位十六进制字符串
- **示例**: `"a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd"`
- **说明**: 机器硬件指纹，用于设备身份验证
- **验证**: 严格64位长度

#### hardware_info (可选)
```json
{
  "hardware_uuid": "00112233-4455-6677-8899-aabbccddeeff",
  "cpu_info": {
    "processor": "Intel Core i7-9700K",
    "cores": 8,
    "threads": 8
  },
  "memory_info": {
    "total": 17179869184,
    "available": 8589934592
  },
  "disk_info": {
    "serial": "DISK001234567890",
    "total": 549755813888
  },
  "system_info": {
    "os_version": "Windows 10 Pro",
    "hostname": "WORKSTATION-001"
  }
}
```

#### reason (可选)
- **格式**: 字符串，最大500字符
- **示例**: `"更换新设备"`, `"设备故障"`, `"重新安装系统"`
- **说明**: 记录解绑原因，用于审计和统计

## 请求示例

### 基本解绑请求

```bash
curl -X POST "https://api.example.com/api/v1/licenses/unbind/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 123" \
  -d '{
    "activation_code": "ABCD-1234-EFGH-5678",
    "license_key": "A1B2C-D3E4F-G5H6I-J7K8L-M9N0P",
    "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd"
  }'
```

### 完整解绑请求（含可选参数）

```bash
curl -X POST "https://api.example.com/api/v1/licenses/unbind/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 123" \
  -d '{
    "activation_code": "ABCD-1234-EFGH-5678",
    "license_key": "A1B2C-D3E4F-G5H6I-J7K8L-M9N0P",
    "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
    "hardware_info": {
      "hardware_uuid": "00112233-4455-6677-8899-aabbccddeeff",
      "system_info": {
        "os_version": "Windows 10 Pro",
        "hostname": "WORKSTATION-001"
      }
    },
    "reason": "更换新设备"
  }'
```

## 响应格式

### 成功响应 (200 OK)

```json
{
  "success": true,
  "message": "License unbound successfully",
  "data": {
    "license_id": 123,
    "machine_id": "MACHINE-ABCD1234",
    "unbound_at": "2024-01-15T10:30:00Z",
    "remaining_activations": 2,
    "max_activations": 5,
    "reason": "更换新设备"
  }
}
```

#### 成功响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `success` | boolean | 操作是否成功，固定为 `true` |
| `message` | string | 操作结果消息 |
| `data.license_id` | integer | 许可证内部ID |
| `data.machine_id` | string | 机器标识符 |
| `data.unbound_at` | string | 解绑时间 (ISO 8601格式) |
| `data.remaining_activations` | integer | 剩余可用激活数 |
| `data.max_activations` | integer | 最大激活数限制 |
| `data.reason` | string | 解绑原因 |

### 错误响应格式

所有错误响应都包含以下基本结构：

```json
{
  "success": false,
  "error": "错误描述",
  "code": "错误代码"
}
```

## 错误代码及处理

### 400 Bad Request - 请求参数错误

#### 1. 激活记录不存在
```json
{
  "success": false,
  "error": "Activation record not found",
  "code": "ACTIVATION_NOT_FOUND"
}
```
**原因**: 提供的激活码无效或不存在  
**处理**: 检查激活码是否正确，或联系技术支持

#### 2. 许可证密钥不匹配
```json
{
  "success": false,
  "error": "License key mismatch",
  "code": "LICENSE_KEY_MISMATCH"
}
```
**原因**: 许可证密钥与激活记录不匹配  
**处理**: 确认许可证密钥正确

#### 3. 机器指纹不匹配
```json
{
  "success": false,
  "error": "Machine fingerprint mismatch",
  "code": "FINGERPRINT_MISMATCH",
  "similarity": 0.65
}
```
**原因**: 机器指纹相似度低于80%阈值  
**处理**: 检查是否在正确的设备上操作，如硬件变化较大可联系支持

#### 4. 绑定状态无效
```json
{
  "success": false,
  "error": "Machine binding is not active (current: inactive)",
  "code": "BINDING_NOT_ACTIVE"
}
```
**原因**: 机器绑定已经是非活跃状态  
**处理**: 设备可能已经解绑，无需重复操作

#### 5. 参数验证错误
```json
{
  "success": false,
  "errors": {
    "activation_code": ["激活码格式无效"],
    "license_key": ["许可证密钥格式无效"],
    "machine_fingerprint": ["机器指纹长度必须为64位"]
  }
}
```
**原因**: 输入参数格式不正确  
**处理**: 检查并修正参数格式

### 403 Forbidden - 可疑活动

```json
{
  "success": false,
  "error": "Unbind request flagged for review",
  "code": "SUSPICIOUS_ACTIVITY"
}
```
**原因**: 触发了可疑活动检测机制  
**处理**: 等待一段时间后重试，或联系技术支持

### 429 Too Many Requests - 频率限制

```json
{
  "success": false,
  "error": "Too many unbind attempts. Please try again later.",
  "code": "RATE_LIMITED"
}
```
**原因**: 超过了频率限制（100次/小时）  
**处理**: 等待一段时间后重试

### 500 Internal Server Error - 服务器错误

```json
{
  "success": false,
  "error": "Internal server error",
  "code": "INTERNAL_ERROR"
}
```
**原因**: 服务器内部错误  
**处理**: 联系技术支持

## HTTP头部要求

### 必需头部

| 头部名称 | 值 | 说明 |
|----------|---|------|
| `Content-Type` | `application/json` | 请求内容类型 |

### 可选头部

| 头部名称 | 示例值 | 说明 |
|----------|--------|------|
| `X-Tenant-ID` | `123` | 租户ID，用于多租户环境 |
| `User-Agent` | `MyApp/1.0.0` | 客户端标识 |

## 安全机制

### 多重验证
1. **激活码验证** - 确保激活记录存在
2. **许可证密钥匹配** - 防止跨许可证操作
3. **机器指纹验证** - 确认设备身份（80%相似度阈值）
4. **绑定状态检查** - 只能解绑活跃状态的绑定

### 频率限制
- 每小时最多100次请求
- 短时间内频繁请求会触发可疑活动检测

### 可疑活动检测
系统会监控以下行为模式：
- 10分钟内来自同一IP的超过5次解绑请求
- 1小时内同一激活码超过3次解绑尝试
- 6小时内同一许可证超过10次解绑操作

### 审计日志
所有解绑操作都会记录到安全审计日志中，包括：
- 操作时间和IP地址
- 激活码和许可证信息（部分哈希）
- 解绑原因和指纹相似度
- 操作结果和剩余激活数

## 最佳实践

### 1. 错误处理
```javascript
async function unbindLicense(activationCode, licenseKey, machineFingerprint, reason) {
  try {
    const response = await fetch('/api/v1/licenses/unbind/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': '123'
      },
      body: JSON.stringify({
        activation_code: activationCode,
        license_key: licenseKey,
        machine_fingerprint: machineFingerprint,
        reason: reason
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(`解绑失败: ${data.error} (${data.code})`);
    }

    if (data.success) {
      console.log('解绑成功:', data.data);
      return data.data;
    } else {
      throw new Error('解绑失败: 未知错误');
    }
  } catch (error) {
    console.error('解绑请求异常:', error);
    throw error;
  }
}
```

### 2. 重试机制
```javascript
async function unbindWithRetry(activationCode, licenseKey, machineFingerprint, reason, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await unbindLicense(activationCode, licenseKey, machineFingerprint, reason);
    } catch (error) {
      if (error.code === 'RATE_LIMITED' && attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000; // 指数退避
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
}
```

### 3. 用户提示
```javascript
function handleUnbindError(error) {
  const errorMessages = {
    'ACTIVATION_NOT_FOUND': '激活码无效，请检查是否输入正确',
    'LICENSE_KEY_MISMATCH': '许可证密钥与激活记录不匹配',
    'FINGERPRINT_MISMATCH': '设备验证失败，请确认在正确的设备上操作',
    'BINDING_NOT_ACTIVE': '设备已经解绑，无需重复操作',
    'SUSPICIOUS_ACTIVITY': '操作被安全系统拦截，请稍后重试',
    'RATE_LIMITED': '请求过于频繁，请稍后重试',
    'INTERNAL_ERROR': '服务器暂时不可用，请稍后重试'
  };

  return errorMessages[error.code] || error.error || '未知错误';
}
```

## 集成检查清单

在集成此API之前，请确认以下事项：

- [ ] 已获取必需的激活码、许可证密钥和机器指纹
- [ ] 实现了适当的错误处理机制
- [ ] 添加了重试逻辑（特别是频率限制情况）
- [ ] 配置了正确的请求头部
- [ ] 测试了各种错误场景
- [ ] 实现了用户友好的错误提示
- [ ] 考虑了网络异常情况的处理

## 常见问题

### Q: 解绑后多久可以在新设备上激活？
A: 解绑是即时生效的，可以立即在新设备上激活许可证。

### Q: 机器指纹发生变化怎么办？
A: 系统允许80%的相似度，轻微的硬件变化不会影响解绑。如果变化较大，请联系技术支持。

### Q: 可以批量解绑多个设备吗？
A: 当前API不支持批量操作，需要为每个设备单独调用解绑接口。

### Q: 解绑操作会被记录吗？
A: 是的，所有解绑操作都会记录到安全审计日志中，包括操作时间、设备信息和原因。

### Q: 解绑失败的设备是否还占用激活配额？
A: 只有成功解绑的设备才会释放激活配额，失败的解绑不会影响现有绑定状态。

## 技术支持

如遇到集成问题，请提供以下信息：
- 请求和响应的完整内容
- 错误代码和消息
- 操作时间和设备信息
- 复现步骤

联系方式：
- 技术支持邮箱：support@example.com
- 开发者文档：https://docs.example.com
- 问题追踪：https://github.com/example/issues
