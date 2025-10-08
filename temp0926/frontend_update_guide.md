# 许可证系统前端更新指南 - 方案A重构

## 📋 概述

本文档详细描述了许可证系统方案A重构后的字段变更，帮助前端开发者快速适配新的API接口和数据结构。

**重构日期：** 2025年9月26日  
**重构版本：** RIPER-5 方案A  
**影响范围：** LicensePlan模型字段重命名 + 事件驱动更新机制

---

## 🔄 字段变更汇总

### 1. LicensePlan 模型字段重命名

| 原字段名 | 新字段名 | 数据类型 | 说明 |
|---------|---------|----------|------|
| `max_machines` | `default_max_activations` | `PositiveIntegerField` | 模板默认最大激活数 |
| `validity_days` | `default_validity_days` | `PositiveIntegerField` | 模板默认有效天数 |

### 2. License 模型（无变更）

License模型的字段保持不变，继续使用：
- `max_activations` - 实际最大激活数
- `expires_at` - 实际过期时间

---

## 🚀 API接口变更

### 1. LicensePlan 相关API

#### GET /api/licenses/plans/
**响应数据变更：**

```javascript
// ❌ 旧版本响应
{
  "id": 1,
  "name": "专业版",
  "max_machines": 5,        // 已重命名
  "validity_days": 365,     // 已重命名
  "price": 999.00
}

// ✅ 新版本响应
{
  "id": 1,
  "name": "专业版", 
  "default_max_activations": 5,  // 新字段名
  "default_validity_days": 365,   // 新字段名
  "price": 999.00
}
```

#### POST /api/licenses/plans/
**请求数据变更：**

```javascript
// ❌ 旧版本请求
{
  "name": "企业版",
  "max_machines": 10,       // 已重命名
  "validity_days": 730,     // 已重命名
  "price": 1999.00
}

// ✅ 新版本请求
{
  "name": "企业版",
  "default_max_activations": 10,  // 新字段名
  "default_validity_days": 730,   // 新字段名
  "price": 1999.00
}
```

#### PUT/PATCH /api/licenses/plans/{id}/
请求和响应数据格式同上。

### 2. License 相关API（无变更）

License相关的API接口保持不变，仍然使用：
- `max_activations`
- `expires_at`

---

## 💻 前端代码更新指南

### 1. 组件属性更新

#### Vue.js 示例

```vue
<template>
  <!-- ❌ 旧版本 -->
  <div class="plan-card">
    <h3>{{ plan.name }}</h3>
    <p>最大设备数: {{ plan.max_machines }}</p>
    <p>有效期: {{ plan.validity_days }}天</p>
  </div>

  <!-- ✅ 新版本 -->
  <div class="plan-card">
    <h3>{{ plan.name }}</h3>
    <p>默认最大激活数: {{ plan.default_max_activations }}</p>
    <p>默认有效天数: {{ plan.default_validity_days }}天</p>
  </div>
</template>

<script>
export default {
  data() {
    return {
      plan: {
        id: 1,
        name: '专业版',
        // ❌ 旧字段
        // max_machines: 5,
        // validity_days: 365,
        
        // ✅ 新字段
        default_max_activations: 5,
        default_validity_days: 365,
        price: 999.00
      }
    }
  }
}
</script>
```

#### React 示例

```jsx
// ❌ 旧版本组件
const PlanCard = ({ plan }) => (
  <div className="plan-card">
    <h3>{plan.name}</h3>
    <p>最大设备数: {plan.max_machines}</p>
    <p>有效期: {plan.validity_days}天</p>
  </div>
);

// ✅ 新版本组件
const PlanCard = ({ plan }) => (
  <div className="plan-card">
    <h3>{plan.name}</h3>
    <p>默认最大激活数: {plan.default_max_activations}</p>
    <p>默认有效天数: {plan.default_validity_days}天</p>
  </div>
);
```

### 2. 表单处理更新

#### Vue.js 表单示例

```vue
<template>
  <form @submit="submitPlan">
    <input 
      v-model="form.name" 
      placeholder="方案名称"
    />
    
    <!-- ❌ 旧版本 -->
    <!-- <input 
      v-model="form.max_machines" 
      type="number"
      placeholder="最大设备数"
    />
    <input 
      v-model="form.validity_days" 
      type="number"
      placeholder="有效天数"
    /> -->
    
    <!-- ✅ 新版本 -->
    <input 
      v-model="form.default_max_activations" 
      type="number"
      placeholder="默认最大激活数"
    />
    <input 
      v-model="form.default_validity_days" 
      type="number"
      placeholder="默认有效天数"
    />
    
    <button type="submit">创建方案</button>
  </form>
</template>

<script>
export default {
  data() {
    return {
      form: {
        name: '',
        // ❌ 旧字段
        // max_machines: 1,
        // validity_days: 365,
        
        // ✅ 新字段
        default_max_activations: 1,
        default_validity_days: 365,
        price: 0
      }
    }
  },
  methods: {
    async submitPlan() {
      try {
        const response = await fetch('/api/licenses/plans/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(this.form)
        });
        
        if (response.ok) {
          console.log('方案创建成功');
        }
      } catch (error) {
        console.error('创建失败:', error);
      }
    }
  }
}
</script>
```

### 3. 表格列配置更新

#### Element UI / Ant Design 表格示例

```javascript
// ❌ 旧版本表格列配置
const oldColumns = [
  {
    title: '方案名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '最大设备数',
    dataIndex: 'max_machines',      // 已重命名
    key: 'max_machines'
  },
  {
    title: '有效天数',
    dataIndex: 'validity_days',     // 已重命名
    key: 'validity_days'
  },
  {
    title: '价格',
    dataIndex: 'price',
    key: 'price'
  }
];

// ✅ 新版本表格列配置
const newColumns = [
  {
    title: '方案名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '默认最大激活数',
    dataIndex: 'default_max_activations',  // 新字段名
    key: 'default_max_activations'
  },
  {
    title: '默认有效天数',
    dataIndex: 'default_validity_days',    // 新字段名
    key: 'default_validity_days'
  },
  {
    title: '价格',
    dataIndex: 'price',
    key: 'price'
  }
];
```

### 4. API调用函数更新

#### JavaScript/TypeScript API函数

```typescript
// ❌ 旧版本接口类型定义
interface OldLicensePlan {
  id: number;
  name: string;
  max_machines: number;        // 已重命名
  validity_days: number;       // 已重命名
  price: number;
}

// ✅ 新版本接口类型定义
interface LicensePlan {
  id: number;
  name: string;
  default_max_activations: number;  // 新字段名
  default_validity_days: number;    // 新字段名
  price: number;
}

// API函数示例
class LicensePlanAPI {
  // 获取方案列表
  static async getPlans(): Promise<LicensePlan[]> {
    const response = await fetch('/api/licenses/plans/');
    return response.json();
  }
  
  // 创建方案
  static async createPlan(planData: Omit<LicensePlan, 'id'>): Promise<LicensePlan> {
    const response = await fetch('/api/licenses/plans/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(planData)
    });
    return response.json();
  }
  
  // 更新方案
  static async updatePlan(id: number, planData: Partial<LicensePlan>): Promise<LicensePlan> {
    const response = await fetch(`/api/licenses/plans/${id}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(planData)
    });
    return response.json();
  }
}
```

---

## 🧪 测试更新指南

### 1. 单元测试更新

```javascript
// ❌ 旧版本测试
describe('LicensePlan Component', () => {
  test('should display plan details correctly', () => {
    const plan = {
      id: 1,
      name: '专业版',
      max_machines: 5,
      validity_days: 365,
      price: 999.00
    };
    
    const wrapper = mount(PlanCard, { props: { plan } });
    expect(wrapper.text()).toContain('最大设备数: 5');
    expect(wrapper.text()).toContain('有效期: 365天');
  });
});

// ✅ 新版本测试
describe('LicensePlan Component', () => {
  test('should display plan details correctly', () => {
    const plan = {
      id: 1,
      name: '专业版',
      default_max_activations: 5,
      default_validity_days: 365,
      price: 999.00
    };
    
    const wrapper = mount(PlanCard, { props: { plan } });
    expect(wrapper.text()).toContain('默认最大激活数: 5');
    expect(wrapper.text()).toContain('默认有效天数: 365天');
  });
});
```

### 2. E2E测试更新

```javascript
// Cypress 测试示例更新
describe('License Plan Management', () => {
  it('should create a new license plan', () => {
    cy.visit('/license-plans');
    cy.get('[data-testid="create-plan-btn"]').click();
    
    cy.get('[data-testid="plan-name"]').type('测试方案');
    
    // ❌ 旧版本测试选择器
    // cy.get('[data-testid="max-machines"]').type('10');
    // cy.get('[data-testid="validity-days"]').type('365');
    
    // ✅ 新版本测试选择器
    cy.get('[data-testid="default-max-activations"]').type('10');
    cy.get('[data-testid="default-validity-days"]').type('365');
    
    cy.get('[data-testid="submit-btn"]').click();
    cy.contains('方案创建成功').should('be.visible');
  });
});
```

---

## 🔍 数据迁移验证

### 1. 后端数据迁移状态

数据库迁移已完成，字段重命名生效：
```sql
-- 迁移文件: 0004_rename_licenseplan_fields.py
-- 已执行的SQL操作:
ALTER TABLE `licenses_license_plan` CHANGE `max_machines` `default_max_activations` int unsigned NOT NULL;
ALTER TABLE `licenses_license_plan` CHANGE `validity_days` `default_validity_days` int unsigned NOT NULL;
```

### 2. 前端验证方法

```javascript
// 验证API响应格式的函数
async function validateAPIResponse() {
  try {
    const response = await fetch('/api/licenses/plans/');
    const plans = await response.json();
    
    if (plans.length > 0) {
      const firstPlan = plans[0];
      
      // 检查新字段是否存在
      if ('default_max_activations' in firstPlan && 'default_validity_days' in firstPlan) {
        console.log('✅ API响应格式已更新');
      } else {
        console.error('❌ API响应格式未更新，请检查后端部署');
      }
      
      // 检查旧字段是否已移除
      if ('max_machines' in firstPlan || 'validity_days' in firstPlan) {
        console.warn('⚠️  检测到旧字段，可能存在缓存问题');
      }
    }
  } catch (error) {
    console.error('API验证失败:', error);
  }
}

// 在应用启动时调用验证
validateAPIResponse();
```

---

## 📝 更新检查清单

### 前端代码审查清单

- [ ] **组件模板更新**
  - [ ] 搜索并替换所有 `max_machines` 为 `default_max_activations`
  - [ ] 搜索并替换所有 `validity_days` 为 `default_validity_days`
  - [ ] 更新相关的显示文本和标签

- [ ] **表单处理更新**
  - [ ] 更新表单字段名称
  - [ ] 更新表单验证规则
  - [ ] 更新表单提交数据结构

- [ ] **数据模型更新**
  - [ ] 更新 TypeScript 接口定义
  - [ ] 更新 PropTypes 定义（React）
  - [ ] 更新 JSON Schema 验证

- [ ] **API调用更新**
  - [ ] 更新API请求数据结构
  - [ ] 更新API响应数据处理
  - [ ] 更新错误处理逻辑

- [ ] **测试代码更新**
  - [ ] 更新单元测试用例
  - [ ] 更新集成测试用例
  - [ ] 更新E2E测试用例

- [ ] **文档更新**
  - [ ] 更新API文档
  - [ ] 更新组件文档
  - [ ] 更新用户手册

### 部署验证清单

- [ ] **开发环境验证**
  - [ ] 确认API响应格式正确
  - [ ] 确认表单提交功能正常
  - [ ] 确认数据显示正确

- [ ] **测试环境验证**
  - [ ] 运行完整的测试套件
  - [ ] 验证用户工作流程
  - [ ] 检查错误处理

- [ ] **生产环境部署**
  - [ ] 确认数据库迁移完成
  - [ ] 确认API兼容性
  - [ ] 监控错误日志

---

## 🆘 故障排除

### 常见问题及解决方案

#### 1. API响应中仍然出现旧字段名

**问题：** 前端收到的API响应中仍然包含 `max_machines` 和 `validity_days`

**解决方案：**
- 检查后端是否已正确部署
- 清除API缓存
- 验证数据库迁移状态

#### 2. 表单提交失败

**问题：** 使用新字段名提交表单时收到400错误

**解决方案：**
- 确认后端API已更新
- 检查请求数据格式
- 查看后端错误日志

#### 3. 类型错误

**问题：** TypeScript报告字段不存在的错误

**解决方案：**
- 更新接口类型定义
- 重新编译TypeScript代码
- 更新类型声明文件

---

## 📞 技术支持

如果在更新过程中遇到问题，请联系：

- **后端团队：** 负责API接口和数据库迁移
- **测试团队：** 负责功能验证和回归测试  
- **DevOps团队：** 负责部署和环境配置

**更新完成后请及时反馈，确保系统稳定运行。**

---

*文档版本：v1.0*  
*最后更新：2025年9月26日*
