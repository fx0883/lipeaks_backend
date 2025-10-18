# 撤销许可证相关问题分析

## 问题描述

用户反馈：**撤销许可证的时候许可证表里面的状态没有改变**

---

## 根本原因

系统中有**两个不同的"撤销"操作**，用户可能混淆了：

### 1. 撤销许可证分配 (Revoke License Assignment)

**API**: 
```
POST /api/v1/licenses/assignments/{id}/revoke/
```

**代码位置**: `licenses/views/assignment_views.py` (第111行)

**调用逻辑**:
```python
assignment.revoke(reason=reason, operator=request.user)
```

**执行内容** (`licenses/models.py` 第722-747行):
```python
def revoke(self, reason="", operator=None):
    # 更新分配状态
    self.status = 'revoked'  # ← 只更新 LicenseAssignment.status
    self.revoked_at = timezone.now()
    self.revoke_reason = reason
    
    # 更新许可证的激活数
    active_assignments = LicenseAssignment.objects.filter(
        license=self.license,
        status='active'
    ).exclude(pk=self.pk).count()
    
    self.license.current_activations = active_assignments
    self.license.save(update_fields=['current_activations'])  # ← 只更新激活数
    
    self.save()
```

**结果**:
- ✅ `LicenseAssignment.status` → `'revoked'`
- ✅ `License.current_activations` → 减少
- ❌ `License.status` → **保持不变**
- ❌ `LicenseActivation` → **不删除**

---

### 2. 撤销许可证 (Revoke License)

**API**:
```
POST /api/v1/licenses/admin/licenses/{id}/revoke/
```

**代码位置**: `licenses/views/admin_views.py` (第668行)

**调用逻辑**:
```python
management_service = LicenseManagementService()
success = management_service.revoke_license(
    license_id=license_obj.id,
    reason=reason,
    user_id=request.user.id
)
```

**执行内容** (`licenses/services/license_service.py` 第698-720行):
```python
def revoke_license(self, license_id, reason, user_id):
    license_obj = License.objects.get(id=license_id)
    
    # 更新许可证状态
    license_obj.status = 'revoked'  # ✅ 更新 License.status
    license_obj.notes = f"撤销原因: {reason}"
    license_obj.save()
    
    # 删除所有激活记录
    deleted_activations = LicenseActivation.objects.filter(
        license=license_obj,
        result='success'
    ).delete()  # ✅ 删除激活记录
    
    # 禁用所有机器绑定
    MachineBinding.objects.filter(license=license_obj).update(
        status='blocked'
    )  # ✅ 禁用设备
```

**结果**:
- ✅ `License.status` → `'revoked'`
- ✅ `LicenseActivation` → 删除
- ✅ `MachineBinding.status` → `'blocked'`

---

## 两者对比

| 操作项 | 撤销许可证分配 | 撤销许可证 |
|--------|---------------|-----------|
| **API** | `/assignments/{id}/revoke/` | `/licenses/{id}/revoke/` |
| **权限** | Assignment 管理权限 | License 管理权限 |
| **更新 LicenseAssignment.status** | ✅ 是 | ❌ 否 (无关) |
| **更新 License.status** | ❌ **否** | ✅ **是** |
| **删除 LicenseActivation** | ❌ 否 | ✅ 是 |
| **更新 MachineBinding** | ❌ 否 | ✅ 是 (blocked) |
| **更新激活数** | ✅ 是 | ✅ 是 |

---

## 业务场景区分

### 场景 1: 撤回用户的许可证使用权

**需求**: Member A 不再需要使用这个许可证，但许可证本身可以分配给其他人

**应该使用**: **撤销许可证分配** (Revoke Assignment)

**效果**:
- Member A 的分配记录标记为 `revoked`
- 许可证本身仍然有效 (`status='activated'`)
- 许可证可以重新分配给 Member B

```
License (status=activated)
  ├─ Assignment A (status=revoked)  ← 撤销
  └─ Assignment B (status=active)   ← 可以新建
```

---

### 场景 2: 彻底作废许可证

**需求**: 这个许可证本身有问题或需要永久作废，所有使用者都不能再用

**应该使用**: **撤销许可证** (Revoke License)

**效果**:
- 许可证状态变为 `revoked`
- 所有激活记录被删除
- 所有设备绑定被禁用
- 无法再激活或使用

```
License (status=revoked)  ← 许可证作废
  ├─ Assignment A (status=active) → 实际无法使用
  └─ Activation Records → 全部删除
  └─ MachineBinding → 全部 blocked
```

---

## 问题所在

如果用户希望**彻底作废许可证**，但使用了**撤销许可证分配** API，会导致：

```python
# 用户期望
License.status = 'revoked'  ❌ 没有发生

# 实际结果
LicenseAssignment.status = 'revoked'  ✅ 发生了
License.status = 'activated'  ❌ 保持不变
```

---

## 修复方案

### 方案 A: 增强"撤销许可证分配"逻辑 (推荐)

在 `LicenseAssignment.revoke()` 方法中添加删除激活记录的逻辑：

**文件**: `licenses/models.py` (第722-747行)

```python
def revoke(self, reason="", operator=None):
    """撤销分配"""
    if self.status in ['revoked', 'expired']:
        raise ValueError(f"无法撤销已撤销或已过期的分配")
    
    from django.utils import timezone
    from licenses.models import LicenseActivation, MachineBinding
    
    self.status = 'revoked'
    self.revoked_at = timezone.now()
    self.revoke_reason = reason
    if operator:
        self.revoked_by = operator
    
    # ✅ 新增：删除该用户的激活记录
    # 查找该分配关联的机器绑定
    member_bindings = MachineBinding.objects.filter(
        license=self.license,
        # 假设有字段关联到 member，或者通过其他方式筛选
    )
    
    # 删除该成员的激活记录
    deleted_activations = LicenseActivation.objects.filter(
        machine_binding__in=member_bindings,
        result='success'
    ).delete()
    
    logger.info(f"撤销分配 {self.id}：删除了 {deleted_activations[0]} 条激活记录")
    
    # 更新License的current_activations计数
    if self.license:
        active_assignments = LicenseAssignment.objects.filter(
            license=self.license,
            status='active'
        ).exclude(pk=self.pk).count()
        
        self.license.current_activations = active_assignments
        self.license.save(update_fields=['current_activations'])
    
    self.save()
    
    return True
```

**优点**:
- 撤销分配时也删除激活记录
- 防止已撤销的分配继续使用 `activation_code`
- 保持许可证本身的状态，可以重新分配

**缺点**:
- 需要明确 `MachineBinding` 和 `LicenseAssignment` 的关联关系
- 当前数据模型可能没有直接关联

---

### 方案 B: 保持现状，明确API使用场景

**不修改代码**，而是：

1. **文档说明**：明确两个API的区别
2. **命名优化**：考虑重命名API路径使其更清晰
3. **前端适配**：根据不同场景调用不同的API

**优点**:
- 保持现有逻辑不变
- 业务语义更清晰

**缺点**:
- 用户容易混淆

---

### 方案 C: 统一撤销逻辑

**创建新的统一撤销方法**：

```python
class LicenseAssignment:
    def revoke(self, reason="", operator=None, revoke_license=False):
        """
        撤销分配
        
        Args:
            reason: 撤销原因
            operator: 操作员
            revoke_license: 是否同时撤销许可证本身
        """
        # 撤销分配
        self.status = 'revoked'
        self.revoked_at = timezone.now()
        self.revoke_reason = reason
        
        # 删除激活记录
        # ...
        
        # 如果需要撤销许可证本身
        if revoke_license:
            self.license.status = 'revoked'
            self.license.save()
        
        self.save()
```

---

## 数据模型关系

```
License (许可证)
  │
  ├─► LicenseAssignment (分配) [member]
  │     └─ status: active/revoked
  │
  ├─► MachineBinding (设备绑定)
  │     ├─ license: FK
  │     └─► LicenseActivation (激活记录)
  │           ├─ activation_code
  │           └─ result: success/failed
  │
  └─ status: generated/activated/revoked
```

**当前问题**:
- `MachineBinding` 不直接关联 `LicenseAssignment`
- 无法直接找到"某个分配"对应的"某些激活记录"

---

## 建议

### 短期方案

如果用户需要**彻底作废许可证**，应该使用：

```bash
POST /api/v1/licenses/admin/licenses/{license_id}/revoke/
{
    "reason": "许可证作废"
}
```

而不是：

```bash
POST /api/v1/licenses/assignments/{assignment_id}/revoke/
{
    "reason": "撤销分配"
}
```

### 长期方案

考虑：
1. 在 `MachineBinding` 中添加 `assignment` 字段，关联到 `LicenseAssignment`
2. 或者在 `LicenseActivation` 中添加 `assignment` 字段
3. 这样撤销分配时可以准确删除对应的激活记录

---

## 测试验证

### 当前行为验证

```python
# 1. 创建许可证和分配
license = License.objects.create(...)
assignment = LicenseAssignment.objects.create(member=user, license=license)

# 2. 激活许可证
activation = LicenseActivation.objects.create(license=license, ...)

# 3. 撤销分配
assignment.revoke(reason="测试")

# 4. 检查状态
print(assignment.status)  # 'revoked' ✅
print(license.status)     # 'activated' ❌ 保持不变！
print(LicenseActivation.objects.filter(license=license).exists())  # True ❌ 仍然存在！
```

### 期望行为

```python
# 3. 撤销分配后
print(assignment.status)  # 'revoked' ✅
print(license.status)     # 'activated' ✅ (如果还有其他分配) 或 'revoked' (如果是最后一个)
print(LicenseActivation.objects.filter(...).exists())  # False ✅ 应该删除
```

---

## 总结

问题不是"bug"，而是**业务逻辑和API使用的理解差异**：

- "撤销许可证分配" ≠ "撤销许可证"
- 如果需要彻底作废许可证，应该使用许可证管理API
- 如果需要增强分配撤销逻辑，需要明确数据模型关联关系

**建议**: 请用户明确需求场景，然后选择合适的修复方案。
