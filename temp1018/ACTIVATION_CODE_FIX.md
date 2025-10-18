# 激活码验证问题修复文档

## 问题描述

**问题**：设备解绑后，仍然可以使用旧的 `activation_code` 通过验证。

### 复现步骤

1. 客户端激活许可证，获得 `activation_code`
2. 调用解绑 API 解绑设备
3. 再次使用旧的 `activation_code` 调用验证 API
4. **问题**：验证仍然成功，但应该失败

---

## 根本原因

### 数据模型关系

```
License (许可证)
  ↓
MachineBinding (机器绑定)
  ↓
LicenseActivation (激活记录) - 包含 activation_code
```

### 原有逻辑缺陷

#### 1. **解绑逻辑**（`unbind_license` 和 `unbind_device`）

```python
# ❌ 旧逻辑：只更新 MachineBinding 状态
machine_binding.status = 'inactive'
machine_binding.save()

# 问题：LicenseActivation 记录仍然存在且有效
# - activation_code 仍在数据库中
# - result = 'success' 状态未改变
```

#### 2. **验证逻辑**（`verify_activation`）

```python
# ❌ 旧逻辑：只检查激活记录存在性
activation = LicenseActivation.objects.filter(
    activation_code=activation_code,
    result='success'
).first()

# 问题：没有检查 machine_binding.status
# 即使设备已解绑（status='inactive'），验证仍通过
```

---

## 修复方案

### ✅ 双重保护机制

#### 修复 1: 解绑时删除激活记录（主动防御）

**文件**：`licenses/services/license_service.py`

**修改位置**：`unbind_license` 方法（第502-515行）

```python
# ✅ 新增：删除激活记录
activation.delete()
logger.info(f"已删除激活记录: {activation_code}")
```

**效果**：
- 删除 `LicenseActivation` 记录
- `activation_code` 从数据库中移除
- 验证时找不到记录，直接失败

**文件**：`licenses/services/member_license_service.py`

**修改位置**：`unbind_device` 方法（第791-802行）

```python
# ✅ 新增：删除该设备的所有激活记录
deleted_activations = LicenseActivation.objects.filter(
    machine_binding=machine_binding,
    result='success'
).delete()

deleted_count = deleted_activations[0] if deleted_activations else 0
if deleted_count > 0:
    logger.info(f"已删除 {deleted_count} 条激活记录")
```

#### 修复 2: 验证时检查设备状态（被动防御）

**文件**：`licenses/services/license_service.py`

**修改位置**：`verify_activation` 方法（第366-377行）

```python
# ✅ 新增：检查机器绑定状态
if activation.machine_binding.status != 'active':
    logger.warning(
        f"激活验证失败: 设备已解绑 - activation_code: {activation_code}, "
        f"machine_binding status: {activation.machine_binding.status}"
    )
    return {
        'valid': False,
        'error': 'Device has been unbound',
        'code': 'DEVICE_UNBOUND',
        'binding_status': activation.machine_binding.status
    }
```

**效果**：
- 即使激活记录存在，也检查设备状态
- 如果设备已解绑（`status='inactive'`），验证失败
- 防御性编程，确保数据一致性

---

## 修复后的完整流程

### 场景 1: 客户端主动解绑（`/api/v1/licenses/unbind/`）

```
1. 客户端调用解绑 API
   ↓
2. 验证 activation_code 和 license_key
   ↓
3. 更新 MachineBinding.status = 'inactive'
   ↓
4. ✅ 删除 LicenseActivation 记录
   ↓
5. 更新 License.current_activations
   ↓
6. 记录审计日志
```

**结果**：
- `activation_code` 被删除
- 验证时返回 `ACTIVATION_NOT_FOUND`

### 场景 2: Member 用户解绑设备（`/api/v1/licenses/member/unbind-device/`）

```
1. Member 用户调用解绑 API
   ↓
2. 验证许可证归属和权限
   ↓
3. 更新 MachineBinding.status = 'inactive'
   ↓
4. ✅ 删除该设备的所有 LicenseActivation 记录
   ↓
5. 更新 License.current_activations
   ↓
6. 记录审计日志
```

**结果**：
- 所有相关 `activation_code` 被删除
- 验证时返回 `ACTIVATION_NOT_FOUND`

### 场景 3: 验证激活状态（`/api/v1/licenses/verify/`）

```
1. 客户端提交 activation_code
   ↓
2. 查找 LicenseActivation 记录
   ↓
3. ✅ 检查 machine_binding.status
   ↓
   - 如果 status != 'active'
     → 返回 'DEVICE_UNBOUND' 错误
   ↓
4. 检查许可证状态和过期时间
   ↓
5. 返回验证结果
```

**结果**：
- 即使激活记录存在，设备已解绑也会验证失败
- 双重保护，确保安全

---

## 测试验证

### 测试用例 1: 解绑后验证失败

```bash
# 1. 激活许可证
POST /api/v1/licenses/activate/
{
    "license_key": "ABC-123-XYZ",
    "machine_id": "MACHINE-001",
    ...
}

# 响应
{
    "success": true,
    "data": {
        "activation_code": "ACT-12345678-ABCD-EFGH"
    }
}

# 2. 验证激活（成功）
POST /api/v1/licenses/verify/
{
    "activation_code": "ACT-12345678-ABCD-EFGH"
}

# 响应
{
    "valid": true,
    "license_info": {...}
}

# 3. 解绑设备
POST /api/v1/licenses/unbind/
{
    "activation_code": "ACT-12345678-ABCD-EFGH",
    "license_key": "ABC-123-XYZ",
    ...
}

# 响应
{
    "success": true,
    "message": "License unbound successfully"
}

# 4. 再次验证激活（应该失败）✅
POST /api/v1/licenses/verify/
{
    "activation_code": "ACT-12345678-ABCD-EFGH"
}

# ✅ 期望响应（修复后）
{
    "valid": false,
    "error": "Activation not found",
    "code": "ACTIVATION_NOT_FOUND"
}

# ❌ 原来的响应（修复前）
{
    "valid": true,  # 错误！应该是 false
    "license_info": {...}
}
```

### 测试用例 2: Member 用户解绑设备

```bash
# 1. Member 用户查看设备列表
GET /api/v1/licenses/member/my-licenses/7/devices/

# 2. 解绑指定设备
POST /api/v1/licenses/member/unbind-device/
{
    "license_id": 7,
    "machine_binding_id": 123,
    "reason": "不再使用该设备"
}

# 响应
{
    "success": true,
    "message": "设备解绑成功",
    "data": {
        "deleted_activation_records": 1  # ✅ 新增字段
    }
}

# 3. 客户端使用旧的 activation_code 验证（应该失败）
POST /api/v1/licenses/verify/
{
    "activation_code": "ACT-XXXXXXXX-XXXX-XXXX"
}

# ✅ 期望响应
{
    "valid": false,
    "error": "Activation not found",
    "code": "ACTIVATION_NOT_FOUND"
}
```

---

## 数据库影响

### 级联删除机制

```python
# models.py
class LicenseActivation(BaseModel):
    machine_binding = models.ForeignKey(
        MachineBinding, 
        on_delete=models.CASCADE,  # ← 级联删除
        related_name='activations'
    )
```

**说明**：
- 删除 `MachineBinding` 时，自动删除关联的 `LicenseActivation` 记录
- 删除许可证时，自动删除所有设备绑定和激活记录
- 数据一致性由数据库保证

### 审计日志增强

解绑操作的审计日志中新增字段：

```python
{
    "event": "member_unbind_device",
    "deleted_activation_records": 1,  # ✅ 新增：记录删除的激活记录数
    "machine_binding_id": 123,
    "reason": "用户主动解绑",
    ...
}
```

---

## 安全性增强

### 1. **防止激活码泄露后滥用**

- 解绑后立即删除 `activation_code`
- 即使激活码泄露，也无法继续使用

### 2. **双重验证机制**

- 主动删除：解绑时删除激活记录
- 被动检查：验证时检查设备状态
- 双重保护，确保安全

### 3. **完整的审计追踪**

- 记录激活码删除操作
- 记录删除的记录数量
- 便于安全审计和问题排查

---

## 兼容性说明

### ✅ 向后兼容

- API 接口没有变化
- 响应格式没有变化
- 新增错误码：`DEVICE_UNBOUND`

### ⚠️ 行为变化

**修复前**：
- 解绑后仍可使用旧的 `activation_code` 验证

**修复后**：
- 解绑后无法使用旧的 `activation_code` 验证
- 返回 `ACTIVATION_NOT_FOUND` 或 `DEVICE_UNBOUND` 错误

### 📋 客户端适配

客户端应处理新的错误码：

```javascript
// 验证激活
const response = await verifyActivation(activationCode);

if (!response.valid) {
    switch (response.code) {
        case 'ACTIVATION_NOT_FOUND':
            // 激活记录不存在（已被删除）
            showError('激活已失效，请重新激活');
            break;
        
        case 'DEVICE_UNBOUND':
            // 设备已解绑
            showError('设备已解绑，请重新激活');
            break;
        
        case 'ACTIVATION_EXPIRED':
            // 激活已过期
            showError('激活已过期');
            break;
        
        default:
            showError('验证失败');
    }
}
```

---

## 总结

### 修改的文件

1. **`licenses/services/license_service.py`**
   - `unbind_license` 方法：删除激活记录
   - `verify_activation` 方法：检查设备状态

2. **`licenses/services/member_license_service.py`**
   - `unbind_device` 方法：删除激活记录
   - 审计日志：记录删除数量

### 核心改进

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| **解绑操作** | 只更新 MachineBinding 状态 | 删除 LicenseActivation 记录 |
| **验证逻辑** | 只检查激活记录存在 | 检查设备状态 + 激活记录 |
| **安全性** | ⚠️ 激活码可重复使用 | ✅ 激活码立即失效 |
| **审计追踪** | 基本记录 | 详细记录（含删除数量） |

### 预期效果

✅ **解决问题**：解绑后无法使用旧的 `activation_code` 验证  
✅ **安全增强**：双重验证机制  
✅ **数据一致性**：激活记录与设备状态同步  
✅ **审计完整性**：详细的操作日志

---

**修复版本**: 1.0.0  
**修复日期**: 2025-10-18  
**影响范围**: 许可证激活和验证模块
