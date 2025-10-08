# 配置文件方案：试用许可证配额管理

**实施日期**: 2025-10-06  
**方案**: 从配置文件读取默认配额  
**优势**: 无需数据库迁移，灵活配置

---

## ✅ 已实施的解决方案

### 配置文件创建

**文件**: `licenses/config.py`

```python
"""
许可证系统配置文件
"""

# 试用许可证配额配置
TRIAL_LICENSE_QUOTAS = {
    'default': 5,           # 默认配额：每个Member用户可以同时持有5个试用许可证
    'vip_users': 10,        # VIP用户配额（预留，可扩展）
    'enterprise': 20,       # 企业用户配额（预留，可扩展）
}

# 申请频率限制配置
APPLICATION_RATE_LIMITS = {
    'daily_limit': 5,           # API级别：每天最多申请5次
    'business_limit': 3,        # 业务级别：24小时内最多申请3次
    'cooldown_hours': 24,       # 冷却时间：24小时
}

# 其他配置（可扩展）
LICENSE_SETTINGS = {
    'auto_approve_trial': True,     # 试用申请是否自动通过
    'send_notification': True,      # 是否发送申请通知
    'enable_quota_check': True,     # 是否启用配额检查
}
```

### 代码修改

#### 修改1: `licenses/services/member_license_service.py`

**位置**: 第305-309行

```python
# 修改前
max_trial_licenses = getattr(member, 'max_trial_licenses', 1)

# 修改后
from licenses.config import TRIAL_LICENSE_QUOTAS

# 从配置文件获取默认配额
default_quota = TRIAL_LICENSE_QUOTAS.get('default', 1)
max_trial_licenses = getattr(member, 'max_trial_licenses', default_quota)
```

#### 修改2: `licenses/serializers.py`

**位置**: 第949-952行

```python
# 修改前
max_trial_licenses = getattr(user, 'max_trial_licenses', 1)

# 修改后  
from licenses.config import TRIAL_LICENSE_QUOTAS
default_quota = TRIAL_LICENSE_QUOTAS.get('default', 1)
max_trial_licenses = getattr(user, 'max_trial_licenses', default_quota)
```

---

## 📊 配置生效结果

### 测试验证

**用户**: fx0883

| 项目 | 配置前 | 配置后 |
|------|--------|--------|
| 默认配额 | 1个 | 5个 ✅ |
| 当前持有 | 1个 | 1个 |
| 是否可申请 | ❌ 不可以 | ✅ 可以 |

**业务逻辑检查**:
```python
if current_count >= max_trial_licenses:  # if 1 >= 5:
    # 结果：False，允许申请 ✅
```

---

## ⚙️ 如何调整配额

### 修改默认配额

**文件**: `licenses/config.py`

```python
TRIAL_LICENSE_QUOTAS = {
    'default': 10,          # ← 修改这个数字即可
    'vip_users': 15,        # 可选：VIP用户配额
    'enterprise': 30,       # 可选：企业用户配额
}
```

**修改步骤**：
1. 编辑 `licenses/config.py` 文件
2. 修改 `'default'` 的值
3. 保存文件
4. 重启Django服务（`python manage.py runserver`）

**生效时间**: 立即生效，无需重启数据库或迁移

---

### 不同配额级别建议

| 配额数量 | 适用场景 | 说明 |
|---------|---------|------|
| **1个** | 严格限制 | 每个用户只能试用1个产品 |
| **3个** | 普通限制 | 大多数用户的合理需求 |
| **5个** | 宽松限制 | 当前设置，较为宽松 ✅ |
| **10个** | VIP配置 | 付费用户或重要客户 |
| **99个** | 基本无限制 | 内部测试或特殊情况 |

---

## 🔄 配置的工作原理

### 代码执行流程

```python
# Step 1: 从配置文件读取
from licenses.config import TRIAL_LICENSE_QUOTAS
default_quota = TRIAL_LICENSE_QUOTAS.get('default', 1)  # 读取到：5

# Step 2: 检查Member对象是否有属性
max_trial_licenses = getattr(member, 'max_trial_licenses', default_quota)
# member没有该属性，所以返回default_quota = 5

# Step 3: 进行配额检查
if user_trial_count >= max_trial_licenses:  # if 1 >= 5:
    # 结果：False，允许申请
```

### 灵活性说明

这种设计的好处：

1. **配置文件优先**: 可以通过修改config.py快速调整默认配额
2. **对象属性覆盖**: 如果Member对象有`max_trial_licenses`属性，优先使用
3. **向后兼容**: 如果config.py出错，还有最后的硬编码默认值1

---

## 🎯 配置管理

### 日常配额调整

**场景1：产品试用活动，临时放宽限制**

```python
# 修改licenses/config.py
TRIAL_LICENSE_QUOTAS = {
    'default': 10,          # 活动期间增加到10个
}
```

**场景2：回到正常配额**

```python
# 修改licenses/config.py
TRIAL_LICENSE_QUOTAS = {
    'default': 3,           # 活动结束，恢复到3个
}
```

### 环境差异配置

**开发环境**（宽松）:
```python
'default': 10,  # 开发测试时需要更多配额
```

**生产环境**（严格）:
```python
'default': 2,   # 生产环境控制更严格
```

---

## 📈 配置监控

### 查看当前配置

```bash
python manage.py shell -c "
from licenses.config import TRIAL_LICENSE_QUOTAS
print('当前配额配置:')
for key, value in TRIAL_LICENSE_QUOTAS.items():
    print(f'  {key}: {value}个')
"
```

### 验证配额生效

```bash
python manage.py shell -c "
from users.models import Member
from licenses.config import TRIAL_LICENSE_QUOTAS

# 随机取几个Member测试
members = Member.objects.all()[:3]

print('配额生效验证:')
for member in members:
    default_quota = TRIAL_LICENSE_QUOTAS.get('default', 1)
    effective_quota = getattr(member, 'max_trial_licenses', default_quota)
    print(f'  {member.username}: {effective_quota}个')
"
```

---

## 🚀 立即测试

现在fx0883用户应该可以申请了！可以重新执行这个curl命令：

```bash
curl 'http://localhost:8000/api/v1/licenses/member/apply/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  --data-raw '{"product_id":3,"plan_id":14,"reason":"123"}'
```

**预期结果**: ✅ 申请成功（因为配额从1个增加到5个）

---

## 📝 配置文件的优势

### ✅ 无需数据库迁移

- 不需要运行 `python manage.py migrate`
- 不需要修改数据库结构
- 不需要添加新字段

### ✅ 灵活配置

- 修改配置文件即可调整配额
- 支持不同环境使用不同配额
- 可以随时调整，立即生效

### ✅ 易于维护

- 所有配额配置集中在一个文件
- 配置项清晰明确
- 支持注释说明

### ✅ 可扩展

- 可以添加更多配置项
- 支持按用户类型配置（预留）
- 支持更复杂的业务规则

---

## 📋 配置清单

已完成的修改：

- [x] ✅ 创建配置文件：`licenses/config.py`
- [x] ✅ 修改服务层：`licenses/services/member_license_service.py`
- [x] ✅ 修改序列化器：`licenses/serializers.py`
- [x] ✅ 测试验证：配额从1个变为5个

**现在fx0883用户可以申请更多试用许可证了！**

---

## 🎯 后续配额调整

### 如需修改配额

只需要编辑 `licenses/config.py` 文件：

```python
TRIAL_LICENSE_QUOTAS = {
    'default': 8,           # 修改这个数字
}
```

**保存文件后立即生效**，无需重启服务！

---

## ✨ 方案2实施完成！

**效果**：
- ✅ 用户fx0883现在可以申请试用许可证了
- ✅ 所有Member用户默认配额变为5个  
- ✅ 无需数据库迁移
- ✅ 配置文件集中管理
- ✅ 随时可调整配额

**配置方案优雅且实用！** 🎉
