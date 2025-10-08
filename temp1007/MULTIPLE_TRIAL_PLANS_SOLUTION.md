# 多试用方案处理方案

## 📋 业务场景

### 问题描述

一个产品可以有**多个活跃的试用方案**，例如：

```
产品: Leaks_compress
├── 试用方案1: Trial (3天，12个激活)
└── 试用方案2: hello2 (11天，11个激活)
```

**问题**：当有多个试用方案时，应该如何处理？

---

## 🎯 解决方案对比

### 方案A：返回所有试用方案（让用户选择）

**适用场景**：
- 希望给用户更多选择
- 不同方案有明显差异（功能、时长不同）
- 产品经理希望A/B测试不同方案

**优点**：
- ✅ 灵活性高，用户可选择
- ✅ 适合差异化方案
- ✅ 用户体验好

**缺点**：
- ⚠️ 前端需要修改UI
- ⚠️ 增加用户选择成本
- ⚠️ API响应数据稍大

**实现方式**：

```python
class AvailableProductSerializer(serializers.ModelSerializer):
    trial_plans = serializers.SerializerMethodField()  # 改为复数
    
    def get_trial_plans(self, obj):
        """返回所有试用方案"""
        trial_plans = obj.license_plans.filter(
            plan_type='trial', 
            status='active'
        ).order_by('-default_validity_days')
        
        return [
            {
                'id': plan.id,
                'name': plan.name,
                'default_validity_days': plan.default_validity_days,
                'default_max_activations': plan.default_max_activations,
                'features': plan.features,
                'is_recommended': index == 0  # 第一个标记为推荐
            }
            for index, plan in enumerate(trial_plans)
        ]
```

**前端实现**：

```vue
<template>
  <div class="product-card">
    <h3>{{ product.name }}</h3>
    
    <!-- 方案选择 -->
    <div v-if="product.trial_plans && product.trial_plans.length > 1">
      <h4>选择试用方案：</h4>
      <el-radio-group v-model="selectedPlanId">
        <el-radio
          v-for="plan in product.trial_plans"
          :key="plan.id"
          :label="plan.id"
          class="plan-option"
        >
          <div class="plan-info">
            <span class="plan-name">{{ plan.name }}</span>
            <el-tag v-if="plan.is_recommended" type="success" size="small">
              推荐
            </el-tag>
          </div>
          <div class="plan-details">
            {{ plan.default_validity_days }}天 · 
            {{ plan.default_max_activations }}个设备
          </div>
        </el-radio>
      </el-radio-group>
    </div>
    
    <!-- 单个方案直接显示 -->
    <div v-else-if="product.trial_plans && product.trial_plans.length === 1">
      <p class="single-plan">
        试用期限：{{ product.trial_plans[0].default_validity_days }}天 · 
        可激活：{{ product.trial_plans[0].default_max_activations }}个设备
      </p>
    </div>
  </div>
</template>
```

---

### 方案B：返回最优方案（自动选择）⭐ 已采用

**适用场景**：
- 希望简化用户选择
- 有明确的"最优"标准（如有效期最长）
- 快速上线，减少前端改动

**优点**：
- ✅ 用户体验简单
- ✅ 前端无需修改
- ✅ 自动返回最优方案

**缺点**：
- ⚠️ 用户无法选择其他方案
- ⚠️ 可能隐藏其他方案

**实现方式**（已实现）：

```python
def get_trial_plan(self, obj):
    """获取最优试用方案（有效期最长的）"""
    trial_plan = obj.license_plans.filter(
        plan_type='trial', 
        status='active'
    ).order_by(
        '-default_validity_days',  # 优先：有效期从长到短
        '-default_max_activations'  # 其次：激活数从多到少
    ).first()
    
    if trial_plan:
        return {
            'id': trial_plan.id,
            'name': trial_plan.name,
            'default_validity_days': trial_plan.default_validity_days,
            'default_max_activations': trial_plan.default_max_activations,
            'features': trial_plan.features,
            'price': float(trial_plan.price) if trial_plan.price else 0,
            'currency': trial_plan.currency
        }
    return None
```

**测试结果**：

```
产品: Leaks_compress
试用方案:
  - hello2: 11天，11个激活  ← ✅ 返回这个（有效期最长）
  - Trial: 3天，12个激活
```

---

### 方案C：添加is_default字段

**适用场景**：
- 需要管理员手动指定默认方案
- 不同产品的"最优"标准不同
- 长期规划，灵活性最高

**优点**：
- ✅ 灵活性最高
- ✅ 管理员可控
- ✅ 支持复杂业务场景

**缺点**：
- ⚠️ 需要数据库迁移
- ⚠️ 需要在管理后台添加配置
- ⚠️ 实施成本高

---

## ✅ 当前采用方案

**已实施：方案B - 返回最优方案**

### 排序规则

```python
.order_by(
    '-default_validity_days',   # 第一优先级：有效期从长到短
    '-default_max_activations'  # 第二优先级：激活数从多到少
)
```

### 实际效果

对于产品`Leaks_compress`的2个试用方案：

| 方案 | 有效期 | 激活数 | 是否返回 |
|------|--------|--------|---------|
| hello2 (ID:13) | 11天 | 11个 | ✅ 返回（有效期最长） |
| Trial (ID:12) | 3天 | 12个 | ❌ 不返回 |

---

## 🔄 如果需要切换到方案A

如果业务需要返回所有方案让用户选择，可以这样修改：

### 后端修改

```python
class AvailableProductSerializer(serializers.ModelSerializer):
    trial_plans = serializers.SerializerMethodField()  # 改为复数
    
    class Meta:
        model = SoftwareProduct
        fields = [
            'id', 'name', 'code', 'description', 'version', 
            'trial_plans',  # 改为复数
            'already_applied'
        ]
    
    def get_trial_plans(self, obj):
        """返回所有试用方案"""
        trial_plans = obj.license_plans.filter(
            plan_type='trial', 
            status='active'
        ).order_by('-default_validity_days')
        
        plans_data = []
        for index, plan in enumerate(trial_plans):
            plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'default_validity_days': plan.default_validity_days,
                'default_max_activations': plan.default_max_activations,
                'features': plan.features,
                'price': float(plan.price) if plan.price else 0,
                'currency': plan.currency,
                'is_recommended': index == 0  # 第一个标记为推荐
            })
        
        return plans_data if plans_data else None
```

### 前端适配

```vue
<template>
  <div class="product-card">
    <!-- 单个方案 -->
    <div v-if="!Array.isArray(product.trial_plans)">
      <p>试用期限：{{ product.trial_plan?.default_validity_days }}天</p>
      <el-button @click="apply(product.id, product.trial_plan?.id)">
        申请试用
      </el-button>
    </div>
    
    <!-- 多个方案 -->
    <div v-else>
      <h4>选择试用方案：</h4>
      <el-select v-model="selectedPlanId">
        <el-option
          v-for="plan in product.trial_plans"
          :key="plan.id"
          :label="`${plan.name} - ${plan.default_validity_days}天`"
          :value="plan.id"
        >
          <span>{{ plan.name }}</span>
          <el-tag v-if="plan.is_recommended" size="small">推荐</el-tag>
          <span style="float: right; color: #8492a6;">
            {{ plan.default_validity_days }}天 / {{ plan.default_max_activations }}设备
          </span>
        </el-option>
      </el-select>
      
      <el-button @click="apply(product.id, selectedPlanId)">
        申请试用
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps(['product']);
const selectedPlanId = ref(null);

// 如果是数组，默认选择推荐的（第一个）
if (Array.isArray(props.product.trial_plans) && props.product.trial_plans.length > 0) {
  selectedPlanId.value = props.product.trial_plans[0].id;
}
</script>
```

### 申请API也需要修改

如果采用方案A，申请API需要支持指定`plan_id`：

```python
class LicenseApplicationSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(help_text="产品ID")
    plan_id = serializers.IntegerField(
        required=False,
        help_text="方案ID（可选，如果产品有多个试用方案可以指定）"
    )
    reason = serializers.CharField(max_length=500, required=False)
    user_info = serializers.JSONField(required=False)
```

---

## 📊 方案对比总结

| 维度 | 方案A：返回所有 | 方案B：返回最优（✅已采用） | 方案C：is_default字段 |
|------|---------------|------------------------|---------------------|
| **用户体验** | 可选择，但复杂 | 简单，自动最优 | 简单，管理员控制 |
| **前端改动** | 需要修改UI | 无需修改 | 无需修改 |
| **后端复杂度** | 低 | 低 | 中（需迁移） |
| **灵活性** | 高 | 中 | 高 |
| **实施成本** | 中 | 低 ✅ | 高 |
| **推荐度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ ✅ | ⭐⭐⭐ |

---

## 💡 我的建议

### 当前方案（方案B）适用于：

- ✅ 快速上线
- ✅ 简化用户选择
- ✅ 有明确的"最优"标准

### 如果未来需要升级到方案A：

1. 修改序列化器返回`trial_plans`数组
2. 前端添加方案选择UI
3. 申请API支持`plan_id`参数

这样可以渐进式升级，不影响现有功能。

---

## 🔧 已实施的修复

### 1. 产品查询优化

**文件**: `licenses/services/member_license_service.py`

```python
# 使用Exists子查询，确保产品有试用方案
from django.db.models import Exists, OuterRef

has_active_trial_plan = LicensePlan.objects.filter(
    product=OuterRef('pk'),
    plan_type='trial',
    status='active'
)

available_products = SoftwareProduct.objects.filter(
    status='active',
    is_deleted=False
).filter(
    Exists(has_active_trial_plan)
)
```

### 2. 最优方案选择

**文件**: `licenses/serializers.py`

```python
def get_trial_plan(self, obj):
    """返回有效期最长的试用方案"""
    trial_plan = obj.license_plans.filter(
        plan_type='trial', 
        status='active'
    ).order_by(
        '-default_validity_days',   # 优先：有效期
        '-default_max_activations'  # 其次：激活数
    ).first()
```

---

## 📈 测试结果

### 修复前

```json
{
  "trial_plan": {
    "id": 12,
    "name": "Trial",
    "default_validity_days": 3  ← 返回有效期短的
  }
}
```

### 修复后

```json
{
  "trial_plan": {
    "id": 13,
    "name": "hello2",
    "default_validity_days": 11  ← ✅ 返回有效期长的
  }
}
```

---

## 🎓 技术要点

### Django查询优化规则

#### 1. 多对多关系查询

```python
# ❌ 不推荐：可能不准确
Product.objects.filter(
    plans__type='trial'
).distinct()

# ✅ 推荐：使用Exists确保准确
has_trial = Plan.objects.filter(
    product=OuterRef('pk'),
    type='trial'
)
Product.objects.filter(Exists(has_trial))
```

#### 2. 多记录排序选择

```python
# ❌ 不明确：返回哪个不确定
.filter(...).first()

# ✅ 明确：按业务规则排序后返回
.filter(...).order_by('-priority', '-created_at').first()
```

### 为什么选择有效期最长？

**业务逻辑**：
1. **用户价值最大化**：更长的试用期
2. **转化率更高**：有更多时间评估产品
3. **用户满意度**：获得最优方案
4. **竞争优势**：展示最好的试用条件

---

## 📋 前端适配建议

### 当前方案（方案B）

前端**无需修改**，API返回单个最优方案：

```javascript
// 原有代码无需修改
const product = products.find(p => p.id === productId);

if (product.trial_plan) {
  console.log(`试用期限：${product.trial_plan.default_validity_days}天`);
  applyLicense(product.id);
}
```

### 如果升级到方案A

需要修改UI支持多方案选择：

```javascript
// 处理单个或多个方案
const trialPlans = Array.isArray(product.trial_plans) 
  ? product.trial_plans 
  : [product.trial_plan];

// 默认选择推荐方案
const recommendedPlan = trialPlans.find(p => p.is_recommended) || trialPlans[0];
```

---

## 🔄 未来扩展建议

### 1. 添加方案优先级

在LicensePlan模型中添加：

```python
priority = models.IntegerField(
    _("优先级"), 
    default=0,
    help_text=_("数值越大优先级越高，用于多方案排序")
)
```

### 2. 添加方案标签

```python
tags = models.JSONField(
    _("方案标签"),
    default=list,
    help_text=_("如：['recommended', 'popular', 'new']")
)
```

### 3. 支持方案对比

前端可以展示方案对比表：

| 方案 | 有效期 | 激活数 | 功能 |
|------|--------|--------|------|
| hello2 ⭐ | 11天 | 11个 | 标准 |
| Trial | 3天 | 12个 | 基础 |

---

## ✅ 总结

### 已完成的优化

1. ✅ **修复查询逻辑**：使用Exists子查询
2. ✅ **优化方案选择**：自动返回有效期最长的方案
3. ✅ **明确排序规则**：有效期 > 激活数
4. ✅ **测试验证**：返回正确的最优方案

### 业务效果

- ✅ 产品列表只显示有试用方案的产品
- ✅ 自动返回最优的试用方案
- ✅ 用户获得最佳体验
- ✅ 前端无需修改

### 如果需要支持用户选择方案

可以采用方案A，让我知道，我可以帮你实现！

**当前方案已经很好地解决了问题！** ✨
