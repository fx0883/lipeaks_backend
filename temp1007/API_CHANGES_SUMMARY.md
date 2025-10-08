# API变更总结：多试用方案支持

**变更日期**: 2025-10-06  
**版本**: v2.0  
**类型**: 🔴 破坏性变更（Breaking Change）

---

## 📢 变更概述

支持一个产品拥有多个试用方案，用户可以选择不同的试用期限和激活配额。

---

## 🔄 API变更详情

### 1. 获取可申请产品列表 API

**端点**: `GET /api/v1/licenses/member/available-products/`

#### 响应结构变更

**字段变化**：`trial_plan` (单个对象) → `trial_plans` (数组)

##### 旧版本响应

```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": 6,
        "name": "Leaks_compress",
        "trial_plan": {              // ← 单个对象
          "id": 12,
          "name": "Trial",
          "default_validity_days": 3
        }
      }
    ]
  }
}
```

##### 新版本响应

```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": 6,
        "name": "Leaks_compress",
        "trial_plans": [             // ← 改为数组
          {
            "id": 13,
            "name": "hello2",
            "default_validity_days": 11,
            "default_max_activations": 11,
            "features": {},
            "price": 0,
            "currency": "CNY",
            "is_recommended": true   // ← 新增字段
          },
          {
            "id": 12,
            "name": "Trial",
            "default_validity_days": 3,
            "default_max_activations": 12,
            "features": {},
            "price": 0,
            "currency": "CNY",
            "is_recommended": false
          }
        ]
      }
    ]
  }
}
```

#### 新增字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| trial_plans | array | 所有活跃的试用方案列表（按有效期从长到短排序） |
| is_recommended | boolean | 是否为推荐方案（第一个为true，即有效期最长的） |

---

### 2. 申请试用许可证 API

**端点**: `POST /api/v1/licenses/member/apply/`

#### 请求参数变更

##### 新增参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| plan_id | integer | 否 | 方案ID。如果产品有多个试用方案，可以指定要申请的方案；如果不指定，系统自动选择有效期最长的方案 |

##### 旧版本请求

```json
{
  "product_id": 6,
  "reason": "申请原因"
}
```

##### 新版本请求

```json
{
  "product_id": 6,
  "plan_id": 13,           // ← 新增：可选参数
  "reason": "申请原因",
  "user_info": {...}
}
```

#### 使用场景

**场景1：产品只有1个试用方案**
```json
{
  "product_id": 6
  // 不需要指定plan_id，系统自动使用唯一的方案
}
```

**场景2：产品有多个试用方案，使用推荐方案**
```json
{
  "product_id": 6
  // 不指定plan_id，系统自动选择有效期最长的（推荐方案）
}
```

**场景3：产品有多个试用方案，用户指定方案**
```json
{
  "product_id": 6,
  "plan_id": 12  // 用户选择了ID=12的方案
}
```

---

## 🚨 Breaking Changes（破坏性变更）

### 影响范围

所有使用 `GET /api/v1/licenses/member/available-products/` API的前端代码都需要修改。

### 必须修改的代码

#### 1. 数据访问

```javascript
// ❌ 旧代码
product.trial_plan.default_validity_days

// ✅ 新代码
product.trial_plans[0].default_validity_days
// 或
product.trial_plans.find(p => p.is_recommended)?.default_validity_days
```

#### 2. 空值检查

```javascript
// ❌ 旧代码
if (product.trial_plan) {
  // ...
}

// ✅ 新代码
if (product.trial_plans && product.trial_plans.length > 0) {
  // ...
}
```

#### 3. 条件渲染

```vue
<!-- ❌ 旧代码 -->
<div v-if="product.trial_plan">
  试用{{ product.trial_plan.default_validity_days }}天
</div>

<!-- ✅ 新代码 -->
<div v-if="product.trial_plans && product.trial_plans.length > 0">
  试用{{ product.trial_plans[0].default_validity_days }}天
</div>
```

---

## ✅ 向后兼容方案

### 创建适配函数（推荐）

```javascript
/**
 * 获取产品的试用方案（兼容新旧API）
 * @param {object} product - 产品对象
 * @returns {array} 试用方案数组
 */
function getTrialPlans(product) {
  if (!product) return [];
  
  // 新版本：trial_plans数组
  if (product.trial_plans) {
    return Array.isArray(product.trial_plans) 
      ? product.trial_plans 
      : [product.trial_plans];
  }
  
  // 旧版本兼容：trial_plan对象
  if (product.trial_plan) {
    return [product.trial_plan];
  }
  
  return [];
}

/**
 * 获取推荐的试用方案
 * @param {object} product - 产品对象
 * @returns {object|null} 推荐的试用方案
 */
function getRecommendedPlan(product) {
  const plans = getTrialPlans(product);
  if (plans.length === 0) return null;
  
  // 查找标记为推荐的方案
  const recommended = plans.find(p => p.is_recommended);
  
  // 如果没有标记，返回第一个（最优）
  return recommended || plans[0];
}

// 使用示例
const plans = getTrialPlans(product);
const recommended = getRecommendedPlan(product);

console.log(`该产品有${plans.length}个试用方案`);
console.log(`推荐方案：${recommended.name}，${recommended.default_validity_days}天`);
```

---

## 📊 数据流对比

### 旧流程

```
1. 调用API → 获取产品
2. 每个产品有1个trial_plan
3. 直接显示trial_plan信息
4. 提交申请（不需要plan_id）
```

### 新流程

```
1. 调用API → 获取产品
2. 每个产品有trial_plans数组（可能有多个）
3. 如果只有1个：直接显示
   如果有多个：提供选择器
4. 提交申请时：
   - 单个方案：可以不传plan_id
   - 多个方案：传递选中的plan_id
```

---

## 🎯 推荐的UI设计

### 单个试用方案UI

```
┌─────────────────────────┐
│ PDF压缩工具              │
│ 高效的PDF压缩工具         │
│                         │
│ 试用方案：标准试用        │
│ ⏰ 30天 · 💻 1个设备    │
│                         │
│ [申请试用]              │
└─────────────────────────┘
```

### 多个试用方案UI

```
┌─────────────────────────┐
│ PDF压缩工具              │
│ 高效的PDF压缩工具         │
│                         │
│ 选择试用方案：           │
│ ◉ 长期试用 [推荐]        │
│   ⏰ 30天 · 💻 2个设备  │
│                         │
│ ○ 快速体验              │
│   ⏰ 7天 · 💻 1个设备   │
│                         │
│ [申请试用]              │
└─────────────────────────┘
```

---

## 🔍 常见问题

### Q1: 为什么要改成数组？

**A**: 因为一个产品可以有多个试用方案（不同时长、不同激活数），让用户选择更灵活。

### Q2: 是否必须指定plan_id？

**A**: 不是必须的。如果不指定，系统会自动选择有效期最长的方案。

### Q3: 如何快速适配？

**A**: 使用提供的`getTrialPlans()`和`getRecommendedPlan()`适配函数，可以快速兼容新旧版本。

### Q4: 单个方案的产品会受影响吗？

**A**: 不会。单个方案的产品，`trial_plans`数组只有1个元素，UI可以简化显示。

---

## ✅ 迁移完成标准

前端完成以下内容即可上线：

- [x] 修改数据访问代码（使用`trial_plans`数组）
- [x] 更新UI组件（支持多方案展示和选择）
- [x] 修改申请API调用（添加`plan_id`参数）
- [x] 测试单个方案产品
- [x] 测试多个方案产品
- [x] 测试不指定plan_id的申请
- [x] 测试指定plan_id的申请

---

**变更已完成，请前端团队尽快适配！** 🎉
