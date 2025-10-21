# already_applied 问题排查指南

## 问题描述

删除许可证后，调用 `/api/v1/licenses/member/available-products/` API 时，`already_applied` 字段仍然显示为 `true`，但期望应该是 `false`。

---

## 问题分析

### 1. **API 判断逻辑**

`already_applied` 字段的判断逻辑（`licenses/serializers.py:833-859`）：

```python
def get_already_applied(self, obj):
    assignments = LicenseAssignment.objects.filter(
        member=request.user,
        license__product=obj,
        license__is_deleted=False,
        status__in=['active', 'pending']  # ← 只包含这两种状态
    )
    return assignments.exists()
```

**逻辑说明**：
- ✅ 只有 `active`（有效）或 `pending`（待激活）状态才算"已申请"
- ❌ `revoked`（已撤销）、`expired`（已过期）、`suspended`（已挂起）等状态不算

### 2. **删除操作**

删除许可证时调用 `assignment.revoke()`（`licenses/models.py:722-747`）：

```python
def revoke(self, reason="", operator=None):
    self.status = 'revoked'  # ← 状态变为 revoked
    self.revoked_at = timezone.now()
    self.save()
```

**预期行为**：
- 删除后，状态变为 `revoked`
- `already_applied` 应该变为 `false`

---

## 可能的原因

### 原因 1: 数据库中有多个同产品的许可证分配 ⭐️ **最可能**

用户可能有多个该产品的许可证分配记录：

| 分配ID | 产品 | 状态 | 说明 |
|--------|------|------|------|
| 7 | Lipeaks | revoked | **刚刚删除的** |
| 8 | Lipeaks | active | **另一个有效的** ← 导致 already_applied=true |

**验证方法**：
```sql
SELECT id, status, license_id, created_at, revoked_at
FROM licenses_licenseassignment
WHERE member_id = 1
  AND license_id IN (
    SELECT id FROM licenses_license WHERE product_id = 10
  )
ORDER BY created_at DESC;
```

### 原因 2: 事务未提交或缓存问题

- Django 事务可能还未提交到数据库
- 可能存在查询缓存

**验证方法**：
- 等待几秒后重新请求
- 检查日志中的调试信息

### 原因 3: 数据不一致

- 删除操作可能失败
- 状态未正确更新

**验证方法**：
- 直接查询数据库检查状态

---

## 诊断步骤

### 步骤 1: 运行诊断脚本

```bash
# 在项目根目录执行
python manage.py shell
```

然后在 shell 中运行：

```python
from temp1018.check_license_status import check_user_licenses

# 检查特定用户（替换为实际用户名）
check_user_licenses('fx0883')
```

**脚本会输出**：
- 用户的所有许可证分配记录
- 每个产品的状态统计
- `already_applied` 的计算结果
- 详细的分配信息

### 步骤 2: 查看日志

调用 `/api/v1/licenses/member/available-products/` API 后，查看日志：

```bash
# 查看最新日志
tail -f logs/licenses_member.log
```

如果 `already_applied=true`，日志会显示：

```
[already_applied=True] Member fx0883 对产品 Lipeaks(ID:10) 
有 1 个有效许可证分配: [{'id': 8, 'status': 'active', 'license_id': 32, ...}]
```

### 步骤 3: 直接查询数据库

```sql
-- 查看用户的所有许可证分配
SELECT 
    la.id AS assignment_id,
    la.status,
    la.created_at,
    la.revoked_at,
    l.id AS license_id,
    l.license_key,
    p.id AS product_id,
    p.name AS product_name
FROM 
    licenses_licenseassignment la
    JOIN licenses_license l ON la.license_id = l.id
    JOIN licenses_softwareproduct p ON l.product_id = p.id
WHERE 
    la.member_id = 1  -- 替换为实际用户ID
    AND p.id = 10     -- 替换为实际产品ID
    AND l.is_deleted = FALSE
ORDER BY 
    la.created_at DESC;
```

---

## 解决方案

### 情况 1: 确实有多个有效许可证

**原因**：数据库中存在多个 `active` 或 `pending` 状态的许可证分配

**解决方案**：
1. 这是**正常行为**，`already_applied=true` 是正确的
2. 用户需要删除**所有**该产品的许可证才能使 `already_applied` 变为 `false`

**批量删除所有该产品的许可证**：

```python
from licenses.models import LicenseAssignment
from users.models import User

user = User.objects.get(username='fx0883', model_type='member')
product_id = 10  # Lipeaks 的产品ID

# 获取所有该产品的有效许可证分配
assignments = LicenseAssignment.objects.filter(
    member=user,
    license__product_id=product_id,
    license__is_deleted=False,
    status__in=['active', 'pending']
)

# 逐个撤销
for assignment in assignments:
    assignment.revoke(reason='批量清理')
    print(f"已撤销分配ID: {assignment.id}")
```

### 情况 2: 删除操作未生效

**原因**：删除时发生错误，状态未更新

**解决方案**：手动修复数据

```python
from licenses.models import LicenseAssignment

# 查找该分配
assignment = LicenseAssignment.objects.get(id=7)

# 检查状态
print(f"Current status: {assignment.status}")

# 如果状态不是 revoked，手动撤销
if assignment.status != 'revoked':
    assignment.revoke(reason='手动修复')
    print("已手动撤销")
```

### 情况 3: 防止重复申请（推荐）

为了避免用户重复申请同一产品，应该在前端添加提示：

```javascript
// 前端示例代码
if (product.already_applied) {
    alert(`您已经拥有 ${product.name} 的有效许可证，无法重复申请`);
    return;
}
```

---

## 预防措施

### 1. 添加唯一约束（可选）

如果业务要求每个用户每个产品只能有一个有效许可证，可以在数据库层面添加约束：

```python
# 在 LicenseAssignment 模型中添加
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['member', 'license__product'],
            condition=models.Q(status__in=['active', 'pending']),
            name='unique_active_assignment_per_product'
        )
    ]
```

### 2. 在删除前检查

删除许可证前，告知用户将要删除的许可证信息：

```javascript
// 前端确认对话框
const confirmMessage = `
确认删除许可证？
产品: ${license.product_name}
方案: ${license.plan_name}
绑定设备: ${license.devices_count} 个

⚠️ 此操作不可逆，所有绑定的设备也会被删除
`;

if (confirm(confirmMessage)) {
    deleteLicense(license.id);
}
```

### 3. 定期清理过期数据

创建定时任务，自动清理过期的许可证：

```python
# management/commands/cleanup_expired_licenses.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from licenses.models import LicenseAssignment

class Command(BaseCommand):
    help = '清理过期的许可证分配'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # 查找过期但状态仍为 active 的分配
        expired_assignments = LicenseAssignment.objects.filter(
            status='active',
            expires_at__lt=now
        )
        
        count = 0
        for assignment in expired_assignments:
            assignment.status = 'expired'
            assignment.save()
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'成功清理 {count} 个过期许可证分配')
        )
```

---

## 常见问题 FAQ

### Q1: 为什么允许用户有多个同产品的许可证？

**A**: 当前系统设计允许用户拥有多个许可证，这在以下场景中是合理的：
- 试用版 + 正式版
- 不同方案的许可证
- 历史许可证记录

但如果业务要求不允许重复，可以添加唯一约束。

### Q2: 删除许可证后能恢复吗？

**A**: 不能。删除操作会：
1. 将状态改为 `revoked`（不可逆）
2. 删除所有设备绑定（永久删除）
3. 记录审计日志

许可证分配记录会保留用于审计，但无法恢复到可用状态。

### Q3: `suspended` 状态算不算"已申请"？

**A**: **不算**。当前逻辑中，只有 `active` 和 `pending` 状态才算"已申请"。

`suspended`（已挂起）状态表示许可证临时不可用，用户可以重新申请。

### Q4: 如何查看用户是否真的删除成功？

**A**: 运行诊断脚本或直接查询数据库：

```bash
python manage.py shell
>>> from temp1018.check_license_status import check_user_licenses
>>> check_user_licenses('fx0883')
```

查看输出中该许可证的状态是否为 `revoked`。

---

## 联系支持

如果问题仍未解决，请提供以下信息：

1. 用户名
2. 产品ID
3. 诊断脚本的完整输出
4. 相关日志（`logs/licenses_member.log`）
5. API 请求和响应的完整内容

---

**最后更新**: 2025-10-18
