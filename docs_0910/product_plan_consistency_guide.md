# 产品-方案一致性处理指南

## 问题描述

在 License 模型中，同时存在 `product` 和 `plan` 字段，而 `plan` 已经关联了 `product`。为了保证数据一致性，需要确保用户选择的 `product` 与 `plan.product` 一致。

## 解决方案概览

我们采用多层次防护策略：

### 1. 前端层面 (推荐的用户体验)

#### 方案A：级联选择（推荐）
```javascript
// 当用户选择产品时，动态加载该产品下的方案
function onProductChange(productId) {
    // 清空方案选择
    $('#plan-select').empty().append('<option value="">请选择方案</option>');
    
    // 加载该产品下的方案
    if (productId) {
        fetch(`/api/v1/licenses/admin/plans/?product=${productId}`)
            .then(response => response.json())
            .then(data => {
                data.data.results.forEach(plan => {
                    $('#plan-select').append(`
                        <option value="${plan.id}">${plan.name} - ¥${plan.price}</option>
                    `);
                });
            });
    }
}

// 当用户选择方案时，自动设置产品
function onPlanChange(planId) {
    if (planId) {
        fetch(`/api/v1/licenses/admin/plans/${planId}/`)
            .then(response => response.json())
            .then(data => {
                // 自动设置产品，并禁用产品选择
                $('#product-select').val(data.data.product).prop('disabled', true);
            });
    } else {
        $('#product-select').prop('disabled', false);
    }
}
```

#### 方案B：只选择方案（最简单）
```javascript
// 隐藏产品选择，只让用户选择方案
// 后端会自动从方案中获取产品信息

<div class="form-group">
    <label>选择许可方案</label>
    <select id="plan-select" name="plan" required>
        <option value="">请选择方案</option>
        <!-- 显示所有方案，格式：产品名 - 方案名 - 价格 -->
    </select>
</div>
```

#### 方案C：实时验证提示
```javascript
function validateProductPlan() {
    const productId = $('#product-select').val();
    const planId = $('#plan-select').val();
    
    if (productId && planId) {
        fetch(`/api/v1/licenses/admin/plans/${planId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.data.product != productId) {
                    showError('所选方案与产品不匹配，请重新选择');
                    $('#plan-select').addClass('is-invalid');
                } else {
                    hideError();
                    $('#plan-select').removeClass('is-invalid');
                }
            });
    }
}
```

### 2. 后端验证层面

#### 序列化器验证
```python
def validate(self, data):
    """验证product和plan的一致性"""
    product = data.get('product')
    plan = data.get('plan')
    
    if product and plan:
        if plan.product != product:
            raise serializers.ValidationError({
                'plan': f'所选方案({plan.name})属于产品({plan.product.name})，与所选产品({product.name})不一致。'
            })
    
    # 如果只有plan没有product，自动设置product
    if plan and not product:
        data['product'] = plan.product
    
    return data
```

#### 模型验证
```python
def clean(self):
    """模型级别的数据验证"""
    if self.plan and self.product:
        if self.plan.product != self.product:
            raise ValidationError({
                'product': f'所选产品与方案所属产品不一致',
                'plan': f'方案属于产品({self.plan.product.name})，不能用于产品({self.product.name})'
            })
    
    # 自动设置product
    if self.plan and not self.product:
        self.product = self.plan.product
```

### 3. 数据库约束

```sql
-- 添加CHECK约束
ALTER TABLE licenses_license 
ADD CONSTRAINT check_product_plan_consistency 
CHECK (
    product_id = (
        SELECT product_id 
        FROM licenses_license_plan 
        WHERE id = plan_id
    )
);
```

## API 响应示例

### 成功情况
```json
{
    "success": true,
    "message": "许可证创建成功",
    "data": {
        "id": 1,
        "product": 1,
        "product_name": "SuperApp Pro",
        "plan": 2,
        "plan_name": "专业版",
        "license_key": "SAPP-PRO-2024-ABCD",
        "status": "generated"
    }
}
```

### 验证失败情况
```json
{
    "success": false,
    "code": "4000",
    "message": "请求参数错误",
    "data": {
        "plan": ["所选方案(基础版)属于产品(SuperApp Basic)，与所选产品(SuperApp Pro)不一致，请重新选择正确的方案。"]
    }
}
```

## 最佳实践建议

### 1. 用户体验优先
- **推荐使用级联选择**：先选产品，再选该产品下的方案
- **提供清晰的提示**：在界面上明确显示方案属于哪个产品
- **实时验证反馈**：用户输入时即时检查并提示错误

### 2. 数据安全优先
- **多层验证**：前端验证 + 后端序列化器验证 + 模型验证 + 数据库约束
- **自动修复**：当只提供plan时，自动设置对应的product
- **详细错误信息**：帮助用户理解和修正错误

### 3. 开发效率考虑
- **统一错误处理**：在所有相关序列化器中添加相同的验证逻辑
- **完整测试覆盖**：测试各种边界情况和错误场景
- **文档说明**：为API用户提供清晰的使用说明

## 测试验证

运行测试确保验证逻辑正常工作：

```bash
# 运行一致性测试
python manage.py test licenses.tests.test_product_plan_consistency

# 运行所有许可证相关测试
python manage.py test licenses.tests
```

## 总结

通过这套多层次的验证机制，我们确保了：

1. **数据一致性** - 杜绝product和plan不匹配的情况
2. **用户体验** - 提供友好的错误提示和自动修复
3. **系统健壮性** - 在多个层面防止数据错误
4. **开发友好** - 清晰的错误信息便于调试和集成

这种设计在保证数据完整性的同时，也提供了良好的用户体验和开发体验。
