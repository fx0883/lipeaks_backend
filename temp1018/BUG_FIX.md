# 解绑设备 API 报错修复

## 问题描述

**错误现象**:
```bash
POST /api/v1/licenses/member/unbind-device/
```
返回错误：参数验证失败或内部错误

**错误原因**:

在修改 `unbind_device` 方法时，添加了删除 `LicenseActivation` 记录的逻辑（第792行）：

```python
deleted_activations = LicenseActivation.objects.filter(
    machine_binding=machine_binding,
    result='success'
).delete()
```

但**忘记在方法顶部导入 `LicenseActivation` 模型**，导致运行时出现 `NameError`。

---

## 修复内容

**文件**: `licenses/services/member_license_service.py`

**修复位置**: 第731行

### 修复前 ❌

```python
from licenses.models import MachineBinding, SecurityAuditLog
```

### 修复后 ✅

```python
from licenses.models import MachineBinding, SecurityAuditLog, LicenseActivation
```

---

## 验证方法

### 测试 1: 解绑设备 API

```bash
POST /api/v1/licenses/member/unbind-device/
Content-Type: application/json
Authorization: Bearer {token}

{
    "license_id": 7,
    "machine_binding_id": 123,
    "reason": "不再使用该设备"
}
```

**期望响应**:
```json
{
    "success": true,
    "message": "设备解绑成功",
    "data": {
        "license_id": 7,
        "machine_binding_id": 123,
        "machine_id": "MACHINE-001",
        "unbound_at": "2025-10-18T08:00:00Z",
        "reason": "不再使用该设备",
        "remaining_activations": 1,
        "max_activations": 3,
        "available_slots": 2
    }
}
```

### 测试 2: 验证激活码失效

```bash
# 解绑后，使用旧的 activation_code 验证应该失败
POST /api/v1/licenses/verify/
Content-Type: application/json

{
    "activation_code": "ACT-XXXX-XXXX-XXXX"
}
```

**期望响应**:
```json
{
    "valid": false,
    "error": "Activation not found",
    "code": "ACTIVATION_NOT_FOUND"
}
```

---

## 相关修复

本次修复涉及的所有文件：

### 1. **客户端解绑设备**
- **文件**: `licenses/services/license_service.py`
- **修改**: 第509行，删除激活记录
- **导入**: ✅ 已在文件顶部导入（第19行）

### 2. **Member 解绑设备**
- **文件**: `licenses/services/member_license_service.py`
- **修改**: 第792行，删除激活记录
- **导入**: ✅ 已修复（第731行）

### 3. **管理员撤销许可证**
- **文件**: `licenses/services/license_service.py`
- **修改**: 第697行，删除激活记录
- **导入**: ✅ 已在文件顶部导入（第19行）

### 4. **验证激活状态**
- **文件**: `licenses/services/license_service.py`
- **修改**: 第367行，检查设备状态
- **导入**: ✅ 已在文件顶部导入（第19行）

---

## 完整的导入清单

### `license_service.py` (✅ 正确)

```python
from licenses.models import (
    SoftwareProduct, LicensePlan, License, MachineBinding, 
    LicenseActivation, SecurityAuditLog  # ✅ 已导入
)
```

### `member_license_service.py` (✅ 已修复)

**文件顶部**:
```python
from licenses.models import (
    SoftwareProduct, LicensePlan, License, LicenseAssignment,
    TenantLicenseQuota, SecurityAuditLog
)
# 注意：MachineBinding 和 LicenseActivation 在方法内部导入
```

**`unbind_device` 方法内**:
```python
from licenses.models import MachineBinding, SecurityAuditLog, LicenseActivation  # ✅ 已添加
```

---

## 为什么要在方法内部导入？

在 `member_license_service.py` 中，某些模型（如 `MachineBinding`, `LicenseActivation`）在**方法内部**导入，而不是文件顶部。

**原因**:
1. **避免循环导入**: 模块之间可能存在相互依赖
2. **按需导入**: 只在需要时才导入，减少模块加载时间
3. **代码组织**: 保持文件顶部导入简洁

**最佳实践**:
- 核心模型在文件顶部导入
- 辅助模型可以在方法内部导入
- 确保所有使用的模型都已导入（无论在哪里）

---

## 错误排查步骤

如果遇到类似的 API 报错，按以下步骤排查：

### 1. 查看错误日志

```bash
# 查看 Django 日志
tail -f logs/licenses_member.log

# 或者查看控制台输出
python manage.py runserver
```

**常见错误信息**:
- `NameError: name 'LicenseActivation' is not defined`
- `ImportError: cannot import name 'LicenseActivation'`

### 2. 检查导入语句

在出错的文件中搜索模型使用：

```bash
# 搜索所有使用 LicenseActivation 的地方
grep -n "LicenseActivation" licenses/services/member_license_service.py
```

然后检查文件顶部或方法内部是否有对应的导入。

### 3. 检查拼写错误

确保导入的模型名称与使用时完全一致：
- ✅ `LicenseActivation`
- ❌ `LicenceActivation` (拼写错误)
- ❌ `licenseActivation` (大小写错误)

### 4. 验证修复

重启 Django 服务器后测试 API：

```bash
# 重启服务器
python manage.py runserver

# 测试 API
curl -X POST http://localhost:8000/api/v1/licenses/member/unbind-device/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"license_id": 7, "machine_binding_id": 123}'
```

---

## 总结

### 问题
- 忘记导入 `LicenseActivation` 模型

### 修复
- 在 `unbind_device` 方法中添加导入：`from licenses.models import ... LicenseActivation`

### 影响
- 仅影响 Member 解绑设备 API
- 其他功能正常

### 状态
✅ **已修复并验证**

---

**修复时间**: 2025-10-18  
**影响范围**: `/api/v1/licenses/member/unbind-device/`  
**修复文件**: `licenses/services/member_license_service.py`
