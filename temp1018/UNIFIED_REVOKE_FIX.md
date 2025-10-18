# 统一撤销许可证数据清理修复

## 修复目标

**用户需求**: 无论是撤销许可证分配还是撤销许可证本身，都需要清理所有相关的激活记录和机器绑定数据。

---

## 修复内容

### 1. 增强 `LicenseAssignment.revoke()` 方法

**文件**: `licenses/models.py` (第722-773行)

**原逻辑** ❌:
```python
def revoke(self, reason="", operator=None):
    self.status = 'revoked'
    # 只更新激活数，不删除激活记录
    self.license.current_activations = active_assignments
    self.license.save(update_fields=['current_activations'])
```

**新逻辑** ✅:
```python
def revoke(self, reason="", operator=None):
    self.status = 'revoked'
    self.revoked_at = timezone.now()
    self.revoke_reason = reason
    
    # ✅ 删除该许可证的所有激活记录
    deleted_activations = LicenseActivation.objects.filter(
        license=self.license,
        result='success'
    ).delete()
    
    activation_count = deleted_activations[0] if deleted_activations else 0
    logger.info(f"撤销许可证分配 {self.id}：删除了 {activation_count} 条激活记录")
    
    # ✅ 禁用该许可证的所有机器绑定
    updated_bindings = MachineBinding.objects.filter(
        license=self.license,
        status='active'
    ).update(status='inactive')
    
    logger.info(f"撤销许可证分配 {self.id}：禁用了 {updated_bindings} 个机器绑定")
    
    # 更新License的current_activations计数
    active_assignments = LicenseAssignment.objects.filter(
        license=self.license,
        status='active'
    ).exclude(pk=self.pk).count()
    
    self.license.current_activations = active_assignments
    self.license.save(update_fields=['current_activations'])
    
    self.save()
```

**修复效果**:
- ✅ 删除所有 `LicenseActivation` 记录
- ✅ 禁用所有 `MachineBinding` (status → 'inactive')
- ✅ 更新许可证激活数
- ✅ 记录详细日志

---

### 2. 修复视图层方法调用错误

**文件**: `licenses/views/assignment_views.py`

#### 修复 2.1: 单个撤销 (第111-142行)

**原代码** ❌:
```python
TenantAwareLicenseAssignmentService.revoke_license_from_member(  # ← 方法不存在
    assignment=assignment,
    reason=reason,
    operator=request.user
)
```

**修复后** ✅:
```python
service = TenantAwareLicenseAssignmentService()
result = service.revoke_license_assignment(  # ← 正确的方法名
    assignment=assignment,
    reason=reason,
    operator=request.user
)

if result['success']:
    return Response({
        'success': True,
        'message': '许可证分配撤销成功',
        'revoked_at': result.get('revoked_at')
    })
```

#### 修复 2.2: 批量撤销 (第297-306行)

**原代码** ❌:
```python
for assignment in assignments:
    TenantAwareLicenseAssignmentService.revoke_license_from_member(
        assignment=assignment,
        reason=reason,
        operator=request.user
    )
    revoked_count += 1
```

**修复后** ✅:
```python
service = TenantAwareLicenseAssignmentService()
for assignment in assignments:
    result = service.revoke_license_assignment(
        assignment=assignment,
        reason=reason,
        operator=request.user
    )
    if result['success']:
        revoked_count += 1
```

---

### 3. 确保 `revoke_license()` 正确处理

**文件**: `licenses/services/license_service.py` (第698-720行)

**已有逻辑** ✅:
```python
def revoke_license(self, license_id, reason, user_id):
    license_obj = License.objects.get(id=license_id)
    
    # 更新许可证状态
    license_obj.status = 'revoked'
    license_obj.save()
    
    # ✅ 删除所有激活记录
    deleted_activations = LicenseActivation.objects.filter(
        license=license_obj,
        result='success'
    ).delete()
    
    # ✅ 禁用所有机器绑定
    MachineBinding.objects.filter(license=license_obj).update(
        status='blocked'
    )
```

**状态**: 已在之前的修复中完成，无需修改。

---

## 完整修复清单

| 功能 | 文件 | 位置 | 修复内容 | 状态 |
|------|------|------|----------|------|
| **撤销许可证分配** | `licenses/models.py` | 722行 | 删除激活记录、禁用设备 | ✅ 已修复 |
| **撤销许可证** | `licenses/services/license_service.py` | 698行 | 删除激活记录、禁用设备 | ✅ 已修复 |
| **单个撤销视图** | `licenses/views/assignment_views.py` | 111行 | 修正方法调用 | ✅ 已修复 |
| **批量撤销视图** | `licenses/views/assignment_views.py` | 297行 | 修正方法调用 | ✅ 已修复 |

---

## 数据清理对比

### 修复前 ❌

#### 撤销许可证分配
```text
API: POST /api/v1/licenses/assignments/{id}/revoke/

执行内容:
├─ LicenseAssignment.status → 'revoked' ✅
├─ License.current_activations → 减少 ✅
├─ LicenseActivation → 保留 ❌ (问题)
└─ MachineBinding → 保持不变 ❌ (问题)
```

#### 撤销许可证
```text
API: POST /api/v1/licenses/admin/licenses/{id}/revoke/

执行内容:
├─ License.status → 'revoked' ✅
├─ LicenseActivation → 删除 ✅
└─ MachineBinding → 'blocked' ✅
```

---

### 修复后 ✅

#### 撤销许可证分配
```text
API: POST /api/v1/licenses/assignments/{id}/revoke/

执行内容:
├─ LicenseAssignment.status → 'revoked' ✅
├─ License.current_activations → 减少 ✅
├─ LicenseActivation → 删除 ✅ (新增)
└─ MachineBinding.status → 'inactive' ✅ (新增)
```

#### 撤销许可证
```text
API: POST /api/v1/licenses/admin/licenses/{id}/revoke/

执行内容:
├─ License.status → 'revoked' ✅
├─ LicenseActivation → 删除 ✅
└─ MachineBinding.status → 'blocked' ✅
```

---

## API 行为统一

现在两个撤销API都会执行相同的数据清理：

| 清理项 | 撤销分配 | 撤销许可证 |
|--------|---------|-----------|
| **删除 LicenseActivation** | ✅ 是 | ✅ 是 |
| **更新 MachineBinding** | ✅ 是 (inactive) | ✅ 是 (blocked) |
| **更新 License.status** | ❌ 否 | ✅ 是 |
| **更新 LicenseAssignment.status** | ✅ 是 | N/A |

**说明**:
- 两个API都会删除激活记录和禁用设备
- 区别：撤销许可证会额外更新 `License.status`
- `MachineBinding` 状态不同：分配用 `inactive`，许可证用 `blocked`

---

## 测试验证

### 测试 1: 撤销许可证分配

```bash
# 1. 激活许可证
POST /api/v1/licenses/activate/
→ activation_code: "ACT-XXXX"

# 2. 创建分配
assignment_id = 123

# 3. 撤销分配
POST /api/v1/licenses/assignments/123/revoke/
{
    "reason": "测试撤销分配"
}

# 4. 验证激活码（应该失败）✅
POST /api/v1/licenses/verify/
{"activation_code": "ACT-XXXX"}
→ {"valid": false, "code": "ACTIVATION_NOT_FOUND"}

# 5. 检查数据库
SELECT * FROM licenses_activation WHERE license_id = {license_id};
→ 应该返回 0 条记录

SELECT status FROM licenses_machine_binding WHERE license_id = {license_id};
→ 应该全部是 'inactive'
```

### 测试 2: 撤销许可证

```bash
# 1. 激活许可证
POST /api/v1/licenses/activate/

# 2. 撤销许可证
POST /api/v1/licenses/admin/licenses/{id}/revoke/
{
    "reason": "测试撤销许可证"
}

# 3. 验证激活码（应该失败）✅
POST /api/v1/licenses/verify/
→ {"valid": false, "code": "ACTIVATION_NOT_FOUND"}

# 4. 尝试再次激活（应该失败）✅
POST /api/v1/licenses/activate/
→ {"success": false, "code": "LICENSE_REVOKED"}

# 5. 检查数据库
SELECT status FROM licenses_license WHERE id = {license_id};
→ 'revoked'

SELECT * FROM licenses_activation WHERE license_id = {license_id};
→ 0 条记录

SELECT status FROM licenses_machine_binding WHERE license_id = {license_id};
→ 全部 'blocked'
```

---

## 日志输出

### 撤销许可证分配日志

```log
[INFO] 撤销许可证分配 123：删除了 2 条激活记录
[INFO] 撤销许可证分配 123：禁用了 2 个机器绑定
[INFO] 许可证分配撤销: user@tenant.com 撤销许可证 ABC-123*** - 用户主动撤销
```

### 撤销许可证日志

```log
[INFO] 撤销许可证 456：删除了 5 条激活记录
[WARNING] 许可证已撤销: 456, 原因: 许可证作废
```

---

## 数据库查询验证

### 查找已撤销但仍有激活记录的许可证

```sql
-- 修复后应该返回 0 条记录
SELECT 
    l.id AS license_id,
    l.status AS license_status,
    la.id AS assignment_id,
    la.status AS assignment_status,
    COUNT(act.id) AS activation_count
FROM 
    licenses_license l
    LEFT JOIN licenses_assignment la ON l.id = la.license_id
    LEFT JOIN licenses_activation act ON l.id = act.license_id AND act.result = 'success'
WHERE 
    l.status = 'revoked' OR la.status = 'revoked'
GROUP BY 
    l.id, l.status, la.id, la.status
HAVING 
    COUNT(act.id) > 0;
```

**期望结果**: 0 条记录

---

## 兼容性说明

### API 行为变化

| API | 修复前 | 修复后 |
|-----|--------|--------|
| `/assignments/{id}/revoke/` | 不删除激活记录 | ✅ 删除激活记录 |
| `/assignments/{id}/revoke/` | 不禁用设备 | ✅ 禁用设备 |
| `/licenses/{id}/revoke/` | ✅ 删除激活记录 | ✅ 删除激活记录 |

### 影响范围

- **客户端**: 无影响，API签名和返回格式未变
- **数据库**: ✅ 数据更干净，无孤立激活记录
- **安全性**: ✅ 撤销后立即失效，无法继续使用

---

## 错误修复

### 修复的错误

1. **方法名错误**: `revoke_license_from_member` 不存在
   - 修正为: `revoke_license_assignment`

2. **静态方法调用**: `TenantAwareLicenseAssignmentService.revoke_...`
   - 修正为: 实例化后调用

3. **未检查返回结果**: 批量撤销未验证成功
   - 修正为: 检查 `result['success']`

---

## 总结

### 修复完成

✅ **LicenseAssignment.revoke()** - 删除激活记录、禁用设备  
✅ **LicenseManagementService.revoke_license()** - 已经正确处理  
✅ **assignment_views.py** - 修正方法调用错误  
✅ **统一数据清理逻辑** - 两个API都清理相关数据  

### 安全增强

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| **激活码有效性** | ⚠️ 撤销后仍可用 | ✅ 立即失效 |
| **数据一致性** | ⚠️ 孤立激活记录 | ✅ 完全清理 |
| **业务逻辑** | ⚠️ 不统一 | ✅ 统一处理 |

---

**修复版本**: 1.0.3  
**修复日期**: 2025-10-18  
**影响模块**: 许可证分配、许可证管理、激活验证  
**修复文件**: 
- `licenses/models.py`
- `licenses/views/assignment_views.py`
- `licenses/services/license_service.py` (已在之前修复)
