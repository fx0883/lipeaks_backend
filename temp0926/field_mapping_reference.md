# 字段映射快速参考

## 🔄 LicensePlan字段映射表

| 旧字段名 | 新字段名 | 查找替换命令 |
|---------|---------|-------------|
| `max_machines` | `default_max_activations` | `s/max_machines/default_max_activations/g` |
| `validity_days` | `default_validity_days` | `s/validity_days/default_validity_days/g` |

## 🔍 批量查找替换命令

### VS Code
```
查找: max_machines
替换: default_max_activations

查找: validity_days  
替换: default_validity_days
```

### 命令行(bash/grep)
```bash
# 查找所有包含旧字段的文件
grep -r "max_machines" src/
grep -r "validity_days" src/

# 批量替换(请先备份!)
find src/ -type f -name "*.js" -o -name "*.vue" -o -name "*.ts" -o -name "*.tsx" | xargs sed -i 's/max_machines/default_max_activations/g'
find src/ -type f -name "*.js" -o -name "*.vue" -o -name "*.ts" -o -name "*.tsx" | xargs sed -i 's/validity_days/default_validity_days/g'
```

## 📱 常见前端框架代码片段

### Vue.js
```javascript
// 旧版本
plan.max_machines → plan.default_max_activations
plan.validity_days → plan.default_validity_days

// 表单绑定
v-model="form.max_machines" → v-model="form.default_max_activations"
v-model="form.validity_days" → v-model="form.default_validity_days"
```

### React
```javascript
// Props访问
{plan.max_machines} → {plan.default_max_activations}
{plan.validity_days} → {plan.default_validity_days}

// State更新
setMaxMachines → setDefaultMaxActivations
setValidityDays → setDefaultValidityDays
```

### Angular
```typescript
// 模板绑定
{{plan.max_machines}} → {{plan.default_max_activations}}
{{plan.validity_days}} → {{plan.default_validity_days}}

// FormControl
maxMachines: new FormControl() → defaultMaxActivations: new FormControl()
validityDays: new FormControl() → defaultValidityDays: new FormControl()
```

## 🧪 测试数据模板

```javascript
// 测试用的LicensePlan数据结构
const mockLicensePlan = {
  id: 1,
  name: "专业版",
  code: "PRO", 
  plan_type: "professional",
  default_max_activations: 5,    // 新字段
  default_validity_days: 365,    // 新字段
  features: {},
  price: 999.00,
  currency: "CNY",
  status: "active"
};
```

## ⚠️ 注意事项

1. **License模型无变更** - 只有LicensePlan模型的字段发生了变化
2. **数据类型不变** - 都是PositiveIntegerField，前端处理方式相同
3. **API路径不变** - 只是响应/请求数据结构中的字段名变化
4. **向后兼容** - 旧版本前端暂时仍可工作，但建议尽快更新
