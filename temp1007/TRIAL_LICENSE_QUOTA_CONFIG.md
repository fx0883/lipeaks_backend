# 试用许可证配额配置指南

**配置项**: Member用户试用许可证数量上限  
**字段名**: `max_trial_licenses`  
**默认值**: 1个  
**配置日期**: 2025-10-06

---

## 📋 问题说明

### 错误信息

```json
{
    "success": false,
    "errors": {
        "non_field_errors": [
            "您的试用许可证数量已达上限（1个）"
        ]
    }
}
```

### 原因

用户 `fx0883` (Member ID: 1) 已经拥有1个活跃的试用许可证，达到了默认上限（1个）。

### 业务规则

- **默认限制**：每个Member用户最多持有 **1个** 活跃的试用许可证
- **可配置**：可以为每个Member单独设置配额
- **字段**：`member.max_trial_licenses`

---

## ⚙️ 配置方法

### 方法1：运行数据库迁移（首次配置必须）

#### Step 1: 检查迁移状态

```bash
cd /Users/fengxuan/Documents/Github/lipeaks_backend
python manage.py showmigrations users
```

**输出**：
```
users
 [X] 0001_initial
 [X] 0002_passwordresettoken_member_and_more
 [ ] 0003_add_max_trial_licenses_to_member  ← ⚠️ 这个还没运行
```

#### Step 2: 运行迁移

```bash
python manage.py migrate users
```

**预期输出**：
```
Running migrations:
  Applying users.0003_add_max_trial_licenses_to_member... OK
```

**效果**：
- ✅ 在Member表中添加 `max_trial_licenses` 字段
- ✅ 所有现有Member的默认值设置为1
- ✅ 后续可以单独为每个Member配置

---

### 方法2：Django Admin后台配置

迁移完成后，可以在Django Admin中为特定Member设置配额。

#### Step 1: 登录Django Admin

访问：`http://localhost:8000/admin/`

使用超级管理员账号登录。

#### Step 2: 找到Member管理

导航：`首页` → `用户管理` → `普通成员 (Members)`

#### Step 3: 编辑Member

1. 找到要修改配额的Member（如 `fx0883`）
2. 点击进入编辑页面
3. 找到 **"试用许可证配额"** 字段
4. 修改数值（例如改为 `3`）
5. 点击 **"保存"**

**字段说明**：
- **字段名**：试用许可证配额
- **英文名**：max_trial_licenses
- **类型**：正整数
- **默认值**：1
- **说明**：该用户最多可以同时持有的试用许可证数量

---

### 方法3：使用Django Shell配置

#### 为单个用户配置

```bash
python manage.py shell
```

```python
from users.models import Member

# 获取Member
member = Member.objects.get(username='fx0883')

# 查看当前配额
print(f"当前配额: {member.max_trial_licenses}")

# 修改配额（例如改为3个）
member.max_trial_licenses = 3
member.save()

print(f"新配额: {member.max_trial_licenses}")
```

#### 批量配置（为所有Member）

```python
from users.models import Member

# 为所有Member设置配额为3
Member.objects.all().update(max_trial_licenses=3)

print("已更新所有Member的试用许可证配额为3")
```

#### 为特定租户的Member配置

```python
from users.models import Member

# 为租户ID=1的所有Member设置配额为5
Member.objects.filter(tenant_id=1).update(max_trial_licenses=5)

print("已更新租户1的所有Member配额为5")
```

---

### 方法4：直接修改数据库（高级）

⚠️ **警告**：直接修改数据库有风险，建议使用方法2或3！

#### MySQL命令

```sql
-- 连接数据库
mysql -u root -p lipeaks_backend

-- 查看Member表结构（确认字段存在）
DESCRIBE member;

-- 查看特定用户的配额
SELECT id, username, max_trial_licenses 
FROM member 
WHERE username = 'fx0883';

-- 修改特定用户的配额
UPDATE member 
SET max_trial_licenses = 3 
WHERE username = 'fx0883';

-- 批量修改所有Member
UPDATE member 
SET max_trial_licenses = 3;

-- 为特定租户的Member修改
UPDATE member 
SET max_trial_licenses = 5 
WHERE tenant_id = 1;
```

---

## 🔍 验证配置

### 检查配置是否生效

```bash
python manage.py shell
```

```python
from users.models import Member

member = Member.objects.get(username='fx0883')
print(f"用户: {member.username}")
print(f"试用许可证配额: {member.max_trial_licenses}")

# 检查当前已有的试用许可证数量
from licenses.models import LicenseAssignment

active_trials = LicenseAssignment.objects.filter(
    member=member,
    license__plan__plan_type='trial',
    status='active'
).count()

print(f"当前活跃的试用许可证: {active_trials}个")
print(f"配额上限: {member.max_trial_licenses}个")
print(f"还可以申请: {member.max_trial_licenses - active_trials}个")
```

---

## 📊 推荐配置方案

### 按用户类型配置

| 用户类型 | 建议配额 | 说明 |
|---------|---------|------|
| **普通用户** | 1-2个 | 基础试用 |
| **VIP用户** | 3-5个 | 可以试用更多产品 |
| **企业用户** | 5-10个 | 企业批量试用 |
| **内部测试** | 99个 | 不限制 |

### 按租户配置

```python
# VIP租户的用户配额设置为5
Member.objects.filter(tenant__name='VIP租户').update(max_trial_licenses=5)

# 普通租户保持默认1
Member.objects.filter(tenant__name='普通租户').update(max_trial_licenses=1)
```

---

## 🎯 快速解决当前问题

针对用户 `fx0883` 的问题，有3个选择：

### 选择1：增加该用户的配额（推荐）

```bash
python manage.py shell -c "
from users.models import Member
member = Member.objects.get(username='fx0883')
member.max_trial_licenses = 3  # 增加到3个
member.save()
print(f'✅ 已将用户 {member.username} 的配额增加到 3 个')
"
```

### 选择2：撤销现有的试用许可证

```bash
python manage.py shell -c "
from users.models import Member
from licenses.models import LicenseAssignment

member = Member.objects.get(username='fx0883')

# 查看现有许可证
assignments = LicenseAssignment.objects.filter(
    member=member,
    license__plan__plan_type='trial',
    status='active'
)

for a in assignments:
    print(f'许可证: {a.license.product.name}, 过期时间: {a.expires_at}')
    print(f'要撤销这个许可证吗？如果是，请手动执行：')
    print(f'  assignment = LicenseAssignment.objects.get(id={a.id})')
    print(f'  assignment.status = \"revoked\"')
    print(f'  assignment.save()')
"
```

### 选择3：等待现有许可证过期

查看过期时间：
```bash
python manage.py shell -c "
from users.models import Member
from licenses.models import LicenseAssignment
from django.utils import timezone

member = Member.objects.get(username='fx0883')
assignments = LicenseAssignment.objects.filter(
    member=member,
    license__plan__plan_type='trial',
    status='active'
)

for a in assignments:
    print(f'产品: {a.license.product.name}')
    print(f'过期时间: {a.expires_at}')
    
    if a.expires_at:
        days_left = (a.expires_at - timezone.now()).days
        print(f'还有 {days_left} 天过期')
        print()
"
```

---

## 💡 推荐配置策略

### 全局默认值

**当前默认值**：1个（通过迁移文件设置）

**修改全局默认值**：
```python
# 迁移文件：users/migrations/0003_add_max_trial_licenses_to_member.py
field=models.PositiveIntegerField(
    default=1,  # ← 这里可以改，但需要新迁移
    ...
)
```

⚠️ **注意**：修改迁移文件后需要重新迁移！

### 按需配置（推荐）

**建议**：保持全局默认值为1，为需要更多配额的用户单独配置。

**配置脚本**：
```python
# scripts/set_trial_quota.py
from users.models import Member

# VIP用户列表
vip_usernames = ['user1', 'user2', 'user3']

for username in vip_usernames:
    try:
        member = Member.objects.get(username=username)
        member.max_trial_licenses = 5
        member.save()
        print(f'✅ {username}: 配额已设置为5')
    except Member.DoesNotExist:
        print(f'❌ {username}: 用户不存在')
```

---

## 📝 配置记录模板

建议记录每次配置变更：

```markdown
## 配置变更记录

### 2025-10-06

**操作**: 增加用户试用许可证配额

| 用户 | 原配额 | 新配额 | 原因 | 操作人 |
|------|--------|--------|------|--------|
| fx0883 | 1 | 3 | VIP用户，需要试用多个产品 | admin |
| user2 | 1 | 5 | 企业客户，批量试用 | admin |
```

---

## 🚨 注意事项

### 1. 先运行迁移

⚠️ **重要**：必须先运行迁移才能使用这个字段！

```bash
python manage.py migrate users
```

### 2. 配额不能小于当前持有数

如果用户已有3个试用许可证，不能将配额设置为2，否则会导致逻辑混乱。

### 3. 配额只限制试用版

`max_trial_licenses` 只限制 `plan_type='trial'` 的许可证，不影响付费版许可证。

### 4. 只计算active状态

只有 `status='active'` 的试用许可证计入配额，已过期或已撤销的不计入。

---

## 🎯 快速操作指南

### 立即解决 fx0883 用户的问题

```bash
# 方法1：增加配额到3个（推荐）
cd /Users/fengxuan/Documents/Github/lipeaks_backend

# 第一步：运行迁移（如果还没运行）
python manage.py migrate users

# 第二步：修改配额
python manage.py shell -c "
from users.models import Member
member = Member.objects.get(username='fx0883')
member.max_trial_licenses = 3
member.save()
print('✅ 配额已增加到3个')
"

# 第三步：验证
python manage.py shell -c "
from users.models import Member
member = Member.objects.get(username='fx0883')
print(f'用户: {member.username}')
print(f'配额: {member.max_trial_licenses}个')
"
```

---

## 📖 相关代码位置

### 配额检查逻辑

**文件**: `licenses/services/member_license_service.py`  
**方法**: `_check_quota_limits()`  
**行数**: 275-313

```python
# 检查用户个人配额（试用许可证限制）
max_trial_licenses = getattr(member, 'max_trial_licenses', 1)
user_trial_count = LicenseAssignment.objects.filter(
    member=member,
    license__plan__plan_type='trial',
    status='active'
).count()

if user_trial_count >= max_trial_licenses:
    raise ValueError(f"您的试用许可证数量已达上限（{max_trial_licenses}个）")
```

**说明**：
- 使用 `getattr(member, 'max_trial_licenses', 1)`
- 如果Member对象有 `max_trial_licenses` 字段，使用该值
- 如果没有，使用默认值 `1`

### 数据库迁移文件

**文件**: `users/migrations/0003_add_max_trial_licenses_to_member.py`

```python
migrations.AddField(
    model_name='member',
    name='max_trial_licenses',
    field=models.PositiveIntegerField(
        default=1,
        help_text='该用户最多可以同时持有的试用许可证数量',
        verbose_name='试用许可证配额'
    ),
)
```

---

## 📊 查询和统计

### 查询所有Member的配额

```bash
python manage.py shell -c "
from users.models import Member

members = Member.objects.all()
print('用户配额统计:')
print('-' * 60)

for member in members:
    quota = getattr(member, 'max_trial_licenses', 1)
    print(f'{member.username:20s} | 配额: {quota}个')
"
```

### 统计配额分布

```bash
python manage.py shell -c "
from users.models import Member
from django.db.models import Count

# 按配额分组统计
from collections import defaultdict
quota_stats = defaultdict(int)

for member in Member.objects.all():
    quota = getattr(member, 'max_trial_licenses', 1)
    quota_stats[quota] += 1

print('配额分布统计:')
for quota, count in sorted(quota_stats.items()):
    print(f'配额{quota}个: {count}个用户')
"
```

---

## 🔧 高级配置

### 按租户批量配置

```python
from users.models import Member

# 为"金sir"租户的所有Member设置配额为5
Member.objects.filter(tenant__name='金sir').update(max_trial_licenses=5)

print("✅ 已更新")
```

### 按注册时间配置

```python
from users.models import Member
from datetime import datetime, timedelta
from django.utils import timezone

# 为最近30天注册的新用户设置配额为2
thirty_days_ago = timezone.now() - timedelta(days=30)
Member.objects.filter(date_joined__gte=thirty_days_ago).update(max_trial_licenses=2)
```

### 创建配置管理脚本

创建文件：`scripts/manage_trial_quota.py`

```python
#!/usr/bin/env python
"""
试用许可证配额管理脚本
用法：python manage.py shell < scripts/manage_trial_quota.py
"""

from users.models import Member

def set_quota_for_user(username, quota):
    """为指定用户设置配额"""
    try:
        member = Member.objects.get(username=username)
        old_quota = member.max_trial_licenses
        member.max_trial_licenses = quota
        member.save()
        print(f'✅ {username}: {old_quota} → {quota}')
        return True
    except Member.DoesNotExist:
        print(f'❌ {username}: 用户不存在')
        return False

def set_quota_for_tenant(tenant_id, quota):
    """为整个租户设置配额"""
    count = Member.objects.filter(tenant_id=tenant_id).update(max_trial_licenses=quota)
    print(f'✅ 已为租户{tenant_id}的{count}个Member设置配额为{quota}')
    return count

# 使用示例
if __name__ == '__main__':
    # 为fx0883设置配额为3
    set_quota_for_user('fx0883', 3)
    
    # 为租户1的所有用户设置配额为5
    # set_quota_for_tenant(1, 5)
```

**使用**：
```bash
python manage.py shell < scripts/manage_trial_quota.py
```

---

## 🎯 最佳实践

### 1. 分层配置策略

```
默认配额: 1个（普通用户）
  ↓
VIP用户: 3个（付费用户）
  ↓
企业用户: 5-10个（企业客户）
  ↓
内部测试: 99个（测试账号）
```

### 2. 动态调整

根据用户行为动态调整：
- 活跃用户：增加配额
- 恶意申请：降低配额或禁止
- 付费用户：适当增加

### 3. 监控和审计

定期检查配额使用情况：

```python
from users.models import Member
from licenses.models import LicenseAssignment

# 查找超额用户（不应该存在，但可以检查）
for member in Member.objects.all():
    quota = member.max_trial_licenses
    count = LicenseAssignment.objects.filter(
        member=member,
        license__plan__plan_type='trial',
        status='active'
    ).count()
    
    if count > quota:
        print(f'⚠️  {member.username}: 持有{count}个，超过配额{quota}')
```

---

## 📞 常见问题

### Q1: 迁移失败怎么办？

**A**: 检查数据库连接和权限，确保Django可以修改数据库结构。

### Q2: 修改配额后立即生效吗？

**A**: 是的，配额修改后立即生效，用户下次申请时就会使用新配额。

### Q3: 可以设置为0吗？

**A**: 可以，设置为0表示该用户不能申请试用许可证。

### Q4: 配额包括已过期的许可证吗？

**A**: 不包括。只计算 `status='active'` 的许可证。

### Q5: 能否通过API配置？

**A**: 目前没有专门的API。可以：
- 在Django Admin中配置（推荐）
- 使用Django Shell配置
- 或让后端团队开发管理API

---

## ✅ 操作步骤总结

### 首次配置（必须）

```bash
# 1. 运行迁移
cd /Users/fengxuan/Documents/Github/lipeaks_backend
python manage.py migrate users

# 2. 验证迁移
python manage.py showmigrations users
# 应该看到：[X] 0003_add_max_trial_licenses_to_member
```

### 日常配置

**方式A：Django Admin**（推荐）
1. 访问 `http://localhost:8000/admin/`
2. 进入 `普通成员` 管理
3. 编辑指定Member
4. 修改 `试用许可证配额` 字段
5. 保存

**方式B：Django Shell**（快速）
```bash
python manage.py shell -c "
from users.models import Member
Member.objects.filter(username='fx0883').update(max_trial_licenses=3)
"
```

---

## 📋 配置清单

解决当前问题请依次执行：

- [ ] 运行数据库迁移：`python manage.py migrate users`
- [ ] 为fx0883增加配额：设置为3个
- [ ] 验证配置：检查max_trial_licenses值
- [ ] 测试申请：重新尝试申请

---

**配置完成后，用户fx0883就可以申请更多试用许可证了！** ✅
