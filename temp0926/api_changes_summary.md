# API变更摘要 - 方案A重构

## 📊 受影响的API端点

### ✅ 有变更的API

| API端点 | 方法 | 变更类型 | 影响字段 |
|--------|------|----------|----------|
| `/api/licenses/plans/` | GET | 响应字段重命名 | `max_machines` → `default_max_activations`<br/>`validity_days` → `default_validity_days` |
| `/api/licenses/plans/` | POST | 请求字段重命名 | 同上 |
| `/api/licenses/plans/{id}/` | GET | 响应字段重命名 | 同上 |
| `/api/licenses/plans/{id}/` | PUT | 请求/响应字段重命名 | 同上 |
| `/api/licenses/plans/{id}/` | PATCH | 请求/响应字段重命名 | 同上 |

### ⚪ 无变更的API

| API端点 | 说明 |
|--------|------|
| `/api/licenses/licenses/` | License模型API无变更 |
| `/api/licenses/activations/` | 激活相关API无变更 |
| `/api/licenses/products/` | 产品相关API无变更 |
| 其他所有API | 均无变更 |

## 📝 具体变更示例

### GET /api/licenses/plans/

#### 旧版本响应
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "基础版",
      "code": "BASIC",
      "plan_type": "basic",
      "max_machines": 1,
      "validity_days": 365,
      "price": "299.00",
      "currency": "CNY"
    }
  ]
}
```

#### 新版本响应
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "基础版", 
      "code": "BASIC",
      "plan_type": "basic",
      "default_max_activations": 1,
      "default_validity_days": 365,
      "price": "299.00",
      "currency": "CNY"
    }
  ]
}
```

### POST /api/licenses/plans/

#### 旧版本请求
```json
{
  "name": "企业版",
  "code": "ENTERPRISE", 
  "plan_type": "enterprise",
  "max_machines": 50,
  "validity_days": 730,
  "price": "4999.00"
}
```

#### 新版本请求
```json
{
  "name": "企业版",
  "code": "ENTERPRISE",
  "plan_type": "enterprise", 
  "default_max_activations": 50,
  "default_validity_days": 730,
  "price": "4999.00"
}
```

## 🔧 前端适配工作量评估

### 低风险变更 ✅
- 纯展示组件：只需更新字段名引用
- 表格显示：更新列配置
- 详情页面：更新数据绑定

### 中风险变更 ⚠️ 
- 表单组件：需更新字段名和验证
- API调用：需更新请求/响应处理
- 状态管理：需更新store字段

### 高风险变更 ❌
- 复杂业务逻辑：可能需要重新测试
- 数据计算：确保使用正确字段
- 第三方集成：检查数据同步

## 🚀 建议更新策略

### 阶段1：准备阶段
1. 备份现有代码
2. 创建专门的更新分支
3. 确认后端API已部署

### 阶段2：代码更新
1. 更新类型定义/接口
2. 批量替换字段名引用
3. 更新API调用代码
4. 更新表单处理逻辑

### 阶段3：测试验证
1. 运行单元测试
2. 手动功能测试  
3. 集成测试验证
4. 用户验收测试

### 阶段4：部署上线
1. 部署到测试环境
2. 回归测试
3. 生产环境部署
4. 监控运行状态

## 📋 前端更新任务清单

### 必须更新的文件类型
- [ ] 组件文件 (*.vue, *.jsx, *.tsx)
- [ ] 类型定义文件 (*.d.ts, interfaces/)
- [ ] API调用文件 (api/, services/)
- [ ] 状态管理文件 (store/, reducers/)
- [ ] 表单配置文件
- [ ] 表格配置文件

### 可选更新的文件
- [ ] 文档文件
- [ ] 注释内容
- [ ] 变量命名
- [ ] 函数命名

## 🎯 测试重点

### 功能测试重点
1. **方案创建** - 确保新字段能正确提交
2. **方案编辑** - 确保更新操作正常
3. **方案列表** - 确保数据正确显示
4. **表单验证** - 确保验证规则正确
5. **数据排序/筛选** - 确保基于新字段的操作正常

### 兼容性测试
1. **API版本兼容** - 确保新旧版本API不冲突
2. **数据格式兼容** - 确保历史数据正确显示
3. **浏览器兼容** - 确保各浏览器正常运行

## 📞 支持联系

如需技术支持，请联系：
- **后端团队** - API接口问题
- **前端组长** - 代码更新指导  
- **测试团队** - 功能验证协助
- **项目经理** - 进度协调

---
*更新完成后请在团队群确认，确保所有人员了解变更情况。*
