# 许可证更新表单集成指南

## 📋 概述

本文档专门针对前端开发人员，提供许可证更新表单的完整集成方案，包括表单设计、数据验证、用户交互和错误处理。

## 🎨 表单设计规范

### 表单布局结构

```html
<!-- 许可证更新表单HTML结构 -->
<form id="licenseUpdateForm" class="license-update-form">
    <div class="form-header">
        <h2>许可证信息更新</h2>
        <p class="form-description">请填写需要更新的许可证信息</p>
    </div>
    
    <!-- 基本信息区域 -->
    <div class="form-section">
        <h3>基本信息</h3>
        
        <div class="form-row">
            <div class="form-group">
                <label for="customer_name">客户姓名 <span class="required">*</span></label>
                <input type="text" id="customer_name" name="customer_name" 
                       placeholder="请输入客户姓名" required>
                <div class="field-error" id="customer_name_error"></div>
            </div>
            
            <div class="form-group">
                <label for="customer_email">客户邮箱 <span class="required">*</span></label>
                <input type="email" id="customer_email" name="customer_email" 
                       placeholder="customer@example.com" required>
                <div class="field-error" id="customer_email_error"></div>
            </div>
        </div>
    </div>
    
    <!-- 许可配置区域 -->
    <div class="form-section">
        <h3>许可配置</h3>
        
        <div class="form-row">
            <div class="form-group">
                <label for="max_activations">最大激活数</label>
                <input type="number" id="max_activations" name="max_activations" 
                       min="1" max="1000" placeholder="5">
                <div class="field-help">当前已激活: <span id="current_activations">0</span></div>
                <div class="field-error" id="max_activations_error"></div>
            </div>
            
            <div class="form-group">
                <label for="expires_at">过期时间</label>
                <input type="datetime-local" id="expires_at" name="expires_at">
                <div class="field-help">当前剩余: <span id="days_remaining">0</span> 天</div>
                <div class="field-error" id="expires_at_error"></div>
            </div>
        </div>
        
        <div class="form-row">
            <div class="form-group">
                <label for="status">许可状态</label>
                <select id="status" name="status">
                    <option value="generated">已生成</option>
                    <option value="activated">已激活</option>
                    <option value="suspended">已挂起</option>
                    <option value="revoked">已撤销</option>
                    <option value="expired">已过期</option>
                </select>
                <div class="field-error" id="status_error"></div>
            </div>
        </div>
    </div>
    
    <!-- 产品方案区域 -->
    <div class="form-section">
        <h3>产品方案</h3>
        
        <div class="form-row">
            <div class="form-group">
                <label for="product">所属产品</label>
                <select id="product" name="product">
                    <option value="">请选择产品...</option>
                    <!-- 动态加载产品列表 -->
                </select>
                <div class="field-error" id="product_error"></div>
            </div>
            
            <div class="form-group">
                <label for="plan">许可方案</label>
                <select id="plan" name="plan" disabled>
                    <option value="">请先选择产品...</option>
                    <!-- 根据产品动态加载方案 -->
                </select>
                <div class="field-error" id="plan_error"></div>
            </div>
        </div>
    </div>
    
    <!-- 备注和元数据区域 -->
    <div class="form-section">
        <h3>附加信息</h3>
        
        <div class="form-group">
            <label for="notes">备注信息</label>
            <textarea id="notes" name="notes" rows="3" 
                      placeholder="请输入相关备注信息..."></textarea>
            <div class="field-error" id="notes_error"></div>
        </div>
        
        <div class="form-group">
            <label>元数据</label>
            <div id="metadata-container" class="metadata-container">
                <!-- 动态添加的元数据键值对 -->
            </div>
            <button type="button" id="add-metadata" class="btn-secondary">
                + 添加元数据
            </button>
        </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="form-actions">
        <button type="button" id="cancel-btn" class="btn-cancel">取消</button>
        <button type="submit" id="submit-btn" class="btn-primary" disabled>
            <span class="btn-text">更新许可证</span>
            <span class="btn-loading" style="display: none;">
                <i class="spinner"></i> 更新中...
            </span>
        </button>
    </div>
</form>
```

### CSS样式规范

```css
/* 许可证更新表单样式 */
.license-update-form {
    max-width: 800px;
    margin: 0 auto;
    padding: 24px;
    background: #ffffff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-header {
    text-align: center;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e8e8e8;
}

.form-header h2 {
    margin: 0 0 8px 0;
    color: #1a1a1a;
    font-size: 24px;
    font-weight: 600;
}

.form-description {
    margin: 0;
    color: #666666;
    font-size: 14px;
}

.form-section {
    margin-bottom: 32px;
}

.form-section h3 {
    margin: 0 0 16px 0;
    color: #1a1a1a;
    font-size: 18px;
    font-weight: 500;
    border-bottom: 1px solid #f0f0f0;
    padding-bottom: 8px;
}

.form-row {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
}

.form-row .form-group {
    flex: 1;
}

.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    margin-bottom: 6px;
    color: #333333;
    font-size: 14px;
    font-weight: 500;
}

.required {
    color: #ff4d4f;
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    font-size: 14px;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
    outline: none;
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.form-group input:disabled,
.form-group select:disabled {
    background-color: #f5f5f5;
    color: #999999;
    cursor: not-allowed;
}

.field-help {
    margin-top: 4px;
    font-size: 12px;
    color: #666666;
}

.field-error {
    margin-top: 4px;
    font-size: 12px;
    color: #ff4d4f;
    display: none;
}

.field-error.show {
    display: block;
}

.metadata-container {
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 8px;
    min-height: 60px;
    background-color: #fafafa;
}

.metadata-item {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
    align-items: center;
}

.metadata-item input {
    flex: 1;
    margin: 0;
}

.metadata-item .remove-metadata {
    color: #ff4d4f;
    cursor: pointer;
    padding: 4px;
}

.form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 24px;
    border-top: 1px solid #e8e8e8;
}

.btn-primary,
.btn-secondary,
.btn-cancel {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary {
    background-color: #1890ff;
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background-color: #40a9ff;
}

.btn-primary:disabled {
    background-color: #d9d9d9;
    cursor: not-allowed;
}

.btn-secondary {
    background-color: #ffffff;
    color: #1890ff;
    border: 1px solid #1890ff;
}

.btn-cancel {
    background-color: #ffffff;
    color: #666666;
    border: 1px solid #d9d9d9;
}

.spinner {
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid #ffffff;
    border-top: 2px solid transparent;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
    .form-row {
        flex-direction: column;
    }
    
    .form-actions {
        flex-direction: column-reverse;
    }
    
    .form-actions button {
        width: 100%;
    }
}
```

## 📝 JavaScript表单处理

### 表单初始化和数据加载

```javascript
class LicenseUpdateForm {
    constructor(containerId, licenseId, options = {}) {
        this.container = document.getElementById(containerId);
        this.licenseId = licenseId;
        this.options = {
            apiBaseUrl: '/api/v1',
            onSuccess: null,
            onCancel: null,
            ...options
        };
        
        this.form = null;
        this.originalData = null;
        this.isLoading = false;
        this.isDirty = false;
        
        this.init();
    }
    
    async init() {
        // 创建表单HTML
        this.createFormHTML();
        
        // 绑定事件监听器
        this.bindEventListeners();
        
        // 加载许可证数据
        await this.loadLicenseData();
        
        // 加载产品和方案数据
        await this.loadProductsAndPlans();
        
        // 初始化表单验证
        this.initValidation();
    }
    
    createFormHTML() {
        // 插入上面的HTML结构
        this.container.innerHTML = `<!-- 上面的HTML表单结构 -->`;
        this.form = this.container.querySelector('#licenseUpdateForm');
    }
    
    async loadLicenseData() {
        try {
            this.setLoading(true);
            
            const token = this.getAuthToken();
            const response = await fetch(`${this.options.apiBaseUrl}/licenses/admin/licenses/${this.licenseId}/`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const licenseData = await response.json();
            this.originalData = licenseData;
            
            // 填充表单数据
            this.populateForm(licenseData);
            
        } catch (error) {
            console.error('加载许可证数据失败:', error);
            this.showError('加载许可证数据失败，请刷新页面重试');
        } finally {
            this.setLoading(false);
        }
    }
    
    populateForm(data) {
        // 填充基本信息
        this.setFieldValue('customer_name', data.customer_name);
        this.setFieldValue('customer_email', data.customer_email);
        this.setFieldValue('max_activations', data.max_activations);
        this.setFieldValue('status', data.status);
        this.setFieldValue('notes', data.notes || '');
        
        // 处理过期时间格式转换
        if (data.expires_at) {
            const date = new Date(data.expires_at);
            const localDateTime = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
                .toISOString().slice(0, 19);
            this.setFieldValue('expires_at', localDateTime);
        }
        
        // 设置产品和方案
        this.setFieldValue('product', data.product);
        this.setFieldValue('plan', data.plan);
        
        // 显示当前激活数
        document.getElementById('current_activations').textContent = data.current_activations;
        
        // 显示剩余天数
        if (data.days_until_expiry !== null) {
            document.getElementById('days_remaining').textContent = 
                data.days_until_expiry >= 0 ? data.days_until_expiry : '已过期';
        }
        
        // 填充元数据
        this.populateMetadata(data.metadata || {});
        
        // 重置脏数据标记
        this.isDirty = false;
        this.updateSubmitButton();
    }
    
    async loadProductsAndPlans() {
        try {
            const token = this.getAuthToken();
            
            // 加载产品列表
            const productsResponse = await fetch(`${this.options.apiBaseUrl}/licenses/admin/products/`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (productsResponse.ok) {
                const productsData = await productsResponse.json();
                this.populateProductSelect(productsData.results || productsData);
            }
            
        } catch (error) {
            console.error('加载产品数据失败:', error);
        }
    }
    
    populateProductSelect(products) {
        const productSelect = document.getElementById('product');
        const currentValue = productSelect.value;
        
        // 清空现有选项（保留第一个默认选项）
        while (productSelect.children.length > 1) {
            productSelect.removeChild(productSelect.lastChild);
        }
        
        // 添加产品选项
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = `${product.name} (${product.code})`;
            productSelect.appendChild(option);
        });
        
        // 恢复选中值
        if (currentValue) {
            productSelect.value = currentValue;
            this.onProductChange(); // 加载对应的方案
        }
    }
    
    async onProductChange() {
        const productId = document.getElementById('product').value;
        const planSelect = document.getElementById('plan');
        
        if (!productId) {
            planSelect.disabled = true;
            planSelect.innerHTML = '<option value="">请先选择产品...</option>';
            return;
        }
        
        try {
            const token = this.getAuthToken();
            const response = await fetch(
                `${this.options.apiBaseUrl}/licenses/admin/plans/?product=${productId}`, 
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );
            
            if (response.ok) {
                const plansData = await response.json();
                this.populatePlanSelect(plansData.results || plansData);
            }
            
        } catch (error) {
            console.error('加载方案数据失败:', error);
        }
    }
    
    populatePlanSelect(plans) {
        const planSelect = document.getElementById('plan');
        const currentValue = planSelect.value;
        
        planSelect.disabled = false;
        planSelect.innerHTML = '<option value="">请选择方案...</option>';
        
        plans.forEach(plan => {
            const option = document.createElement('option');
            option.value = plan.id;
            option.textContent = `${plan.name} (${plan.plan_type})`;
            planSelect.appendChild(option);
        });
        
        // 恢复选中值
        if (currentValue) {
            planSelect.value = currentValue;
        }
    }
    
    populateMetadata(metadata) {
        const container = document.getElementById('metadata-container');
        container.innerHTML = '';
        
        Object.entries(metadata).forEach(([key, value]) => {
            this.addMetadataItem(key, value);
        });
        
        if (Object.keys(metadata).length === 0) {
            container.innerHTML = '<p class="empty-metadata">暂无元数据</p>';
        }
    }
    
    addMetadataItem(key = '', value = '') {
        const container = document.getElementById('metadata-container');
        const emptyMsg = container.querySelector('.empty-metadata');
        if (emptyMsg) {
            emptyMsg.remove();
        }
        
        const item = document.createElement('div');
        item.className = 'metadata-item';
        item.innerHTML = `
            <input type="text" placeholder="键" value="${key}" class="metadata-key">
            <input type="text" placeholder="值" value="${value}" class="metadata-value">
            <span class="remove-metadata" title="删除">×</span>
        `;
        
        container.appendChild(item);
        
        // 绑定删除事件
        item.querySelector('.remove-metadata').addEventListener('click', () => {
            item.remove();
            this.markDirty();
            
            // 如果没有元数据项了，显示空消息
            if (container.children.length === 0) {
                container.innerHTML = '<p class="empty-metadata">暂无元数据</p>';
            }
        });
        
        // 绑定输入事件
        item.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', () => this.markDirty());
        });
    }
    
    bindEventListeners() {
        // 表单提交
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
        
        // 取消按钮
        document.getElementById('cancel-btn').addEventListener('click', () => {
            this.handleCancel();
        });
        
        // 添加元数据按钮
        document.getElementById('add-metadata').addEventListener('click', () => {
            this.addMetadataItem();
            this.markDirty();
        });
        
        // 产品选择变化
        document.getElementById('product').addEventListener('change', () => {
            this.onProductChange();
            this.markDirty();
        });
        
        // 监听所有表单字段变化
        const formFields = this.form.querySelectorAll('input, select, textarea');
        formFields.forEach(field => {
            field.addEventListener('input', () => this.markDirty());
            field.addEventListener('change', () => this.markDirty());
        });
        
        // 防止页面意外关闭
        window.addEventListener('beforeunload', (e) => {
            if (this.isDirty) {
                e.preventDefault();
                e.returnValue = '您有未保存的更改，确定要离开吗？';
            }
        });
    }
    
    initValidation() {
        // 实时验证
        const customerEmail = document.getElementById('customer_email');
        customerEmail.addEventListener('blur', () => {
            this.validateEmail(customerEmail.value);
        });
        
        const maxActivations = document.getElementById('max_activations');
        maxActivations.addEventListener('blur', () => {
            this.validateMaxActivations(parseInt(maxActivations.value));
        });
        
        const expiresAt = document.getElementById('expires_at');
        expiresAt.addEventListener('blur', () => {
            this.validateExpiryDate(expiresAt.value);
        });
    }
    
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const errorElement = document.getElementById('customer_email_error');
        
        if (email && !emailRegex.test(email)) {
            this.showFieldError('customer_email', '请输入有效的邮箱地址');
            return false;
        } else {
            this.hideFieldError('customer_email');
            return true;
        }
    }
    
    validateMaxActivations(value) {
        const currentActivations = this.originalData?.current_activations || 0;
        
        if (value < currentActivations) {
            this.showFieldError('max_activations', 
                `最大激活数不能小于当前激活数 (${currentActivations})`);
            return false;
        } else {
            this.hideFieldError('max_activations');
            return true;
        }
    }
    
    validateExpiryDate(dateString) {
        if (!dateString) return true;
        
        const selectedDate = new Date(dateString);
        const now = new Date();
        
        if (selectedDate <= now) {
            this.showFieldError('expires_at', '过期时间必须晚于当前时间');
            return false;
        } else {
            this.hideFieldError('expires_at');
            return true;
        }
    }
    
    async handleSubmit() {
        if (this.isLoading) return;
        
        // 验证表单
        if (!this.validateForm()) {
            return;
        }
        
        // 收集表单数据
        const formData = this.collectFormData();
        
        try {
            this.setLoading(true);
            
            const token = this.getAuthToken();
            const response = await fetch(`${this.options.apiBaseUrl}/licenses/admin/licenses/${this.licenseId}/`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP ${response.status}`);
            }
            
            const updatedData = await response.json();
            
            // 成功处理
            this.isDirty = false;
            this.showSuccess('许可证更新成功！');
            
            if (typeof this.options.onSuccess === 'function') {
                this.options.onSuccess(updatedData);
            }
            
        } catch (error) {
            console.error('更新失败:', error);
            this.handleSubmitError(error);
        } finally {
            this.setLoading(false);
        }
    }
    
    validateForm() {
        let isValid = true;
        
        // 必填字段验证
        const requiredFields = ['customer_name', 'customer_email'];
        requiredFields.forEach(fieldName => {
            const field = document.getElementById(fieldName);
            if (!field.value.trim()) {
                this.showFieldError(fieldName, '此字段为必填项');
                isValid = false;
            } else {
                this.hideFieldError(fieldName);
            }
        });
        
        // 邮箱验证
        const email = document.getElementById('customer_email').value;
        if (!this.validateEmail(email)) isValid = false;
        
        // 最大激活数验证
        const maxActivations = parseInt(document.getElementById('max_activations').value);
        if (maxActivations && !this.validateMaxActivations(maxActivations)) isValid = false;
        
        // 过期时间验证
        const expiresAt = document.getElementById('expires_at').value;
        if (!this.validateExpiryDate(expiresAt)) isValid = false;
        
        return isValid;
    }
    
    collectFormData() {
        const formData = {};
        
        // 基本字段
        const fields = [
            'customer_name', 'customer_email', 'max_activations', 
            'status', 'notes', 'product', 'plan'
        ];
        
        fields.forEach(fieldName => {
            const field = document.getElementById(fieldName);
            const value = field.value;
            
            if (value !== '') {
                if (fieldName === 'max_activations') {
                    formData[fieldName] = parseInt(value);
                } else if (fieldName === 'product' || fieldName === 'plan') {
                    formData[fieldName] = parseInt(value) || null;
                } else {
                    formData[fieldName] = value;
                }
            }
        });
        
        // 过期时间处理
        const expiresAt = document.getElementById('expires_at').value;
        if (expiresAt) {
            formData.expires_at = new Date(expiresAt).toISOString();
        }
        
        // 元数据处理
        const metadataItems = document.querySelectorAll('.metadata-item');
        const metadata = {};
        
        metadataItems.forEach(item => {
            const key = item.querySelector('.metadata-key').value.trim();
            const value = item.querySelector('.metadata-value').value.trim();
            if (key && value) {
                metadata[key] = value;
            }
        });
        
        if (Object.keys(metadata).length > 0) {
            formData.metadata = metadata;
        }
        
        return formData;
    }
    
    handleSubmitError(error) {
        if (error.response) {
            const { status, data } = error.response;
            
            if (status === 400 && data.data) {
                // 显示字段级错误
                Object.entries(data.data).forEach(([field, errors]) => {
                    this.showFieldError(field, Array.isArray(errors) ? errors[0] : errors);
                });
            } else {
                this.showError(data.message || '更新失败，请重试');
            }
        } else {
            this.showError(error.message || '网络错误，请检查连接');
        }
    }
    
    handleCancel() {
        if (this.isDirty) {
            if (confirm('您有未保存的更改，确定要取消吗？')) {
                this.resetForm();
                if (typeof this.options.onCancel === 'function') {
                    this.options.onCancel();
                }
            }
        } else {
            if (typeof this.options.onCancel === 'function') {
                this.options.onCancel();
            }
        }
    }
    
    // 工具方法
    setFieldValue(fieldName, value) {
        const field = document.getElementById(fieldName);
        if (field && value !== null && value !== undefined) {
            field.value = value;
        }
    }
    
    markDirty() {
        this.isDirty = true;
        this.updateSubmitButton();
    }
    
    updateSubmitButton() {
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = !this.isDirty || this.isLoading;
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        const submitBtn = document.getElementById('submit-btn');
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoading = submitBtn.querySelector('.btn-loading');
        
        if (loading) {
            btnText.style.display = 'none';
            btnLoading.style.display = 'inline';
            submitBtn.disabled = true;
        } else {
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
            this.updateSubmitButton();
        }
    }
    
    showFieldError(fieldName, message) {
        const errorElement = document.getElementById(`${fieldName}_error`);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.add('show');
        }
    }
    
    hideFieldError(fieldName) {
        const errorElement = document.getElementById(`${fieldName}_error`);
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }
    
    showError(message) {
        // 可以使用通知库或自定义弹窗
        alert(`错误: ${message}`);
    }
    
    showSuccess(message) {
        // 可以使用通知库或自定义弹窗
        alert(`成功: ${message}`);
    }
    
    getAuthToken() {
        return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    }
    
    resetForm() {
        if (this.originalData) {
            this.populateForm(this.originalData);
        }
        this.isDirty = false;
        this.updateSubmitButton();
    }
}

// 使用示例
document.addEventListener('DOMContentLoaded', () => {
    const licenseId = 123; // 从URL或其他地方获取
    
    const form = new LicenseUpdateForm('license-update-container', licenseId, {
        onSuccess: (updatedData) => {
            console.log('许可证更新成功:', updatedData);
            // 可以跳转到详情页或列表页
            // window.location.href = `/licenses/${updatedData.id}`;
        },
        onCancel: () => {
            // 返回上一页或关闭弹窗
            // window.history.back();
        }
    });
});
```

## 🚀 高级功能

### 实时数据验证

```javascript
// 扩展表单类，增加实时验证功能
class AdvancedLicenseUpdateForm extends LicenseUpdateForm {
    
    initAdvancedValidation() {
        // 防抖延迟验证
        this.debounceValidation = this.debounce((field, value) => {
            this.validateFieldAsync(field, value);
        }, 500);
        
        // 监听输入事件
        const validatedFields = ['customer_email', 'max_activations'];
        validatedFields.forEach(fieldName => {
            const field = document.getElementById(fieldName);
            field.addEventListener('input', (e) => {
                this.debounceValidation(fieldName, e.target.value);
            });
        });
    }
    
    async validateFieldAsync(fieldName, value) {
        try {
            switch (fieldName) {
                case 'customer_email':
                    await this.validateEmailUnique(value);
                    break;
                case 'max_activations':
                    await this.validateActivationQuota(value);
                    break;
            }
        } catch (error) {
            console.error(`异步验证失败 ${fieldName}:`, error);
        }
    }
    
    async validateEmailUnique(email) {
        if (!email || !this.validateEmail(email)) return;
        
        try {
            const token = this.getAuthToken();
            const response = await fetch(`${this.options.apiBaseUrl}/licenses/admin/licenses/check-email/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    email, 
                    exclude_id: this.licenseId 
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.exists) {
                    this.showFieldError('customer_email', '该邮箱已被其他许可证使用');
                } else {
                    this.hideFieldError('customer_email');
                }
            }
        } catch (error) {
            console.error('邮箱唯一性验证失败:', error);
        }
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}
```

### 自动保存草稿

```javascript
// 增加自动保存功能
class AutoSaveLicenseUpdateForm extends AdvancedLicenseUpdateForm {
    
    constructor(containerId, licenseId, options = {}) {
        super(containerId, licenseId, {
            autoSave: true,
            autoSaveInterval: 30000, // 30秒
            ...options
        });
        
        this.autoSaveTimer = null;
        this.draftKey = `license_draft_${licenseId}`;
    }
    
    init() {
        super.init();
        
        if (this.options.autoSave) {
            this.initAutoSave();
        }
    }
    
    initAutoSave() {
        // 加载草稿数据
        this.loadDraft();
        
        // 开始自动保存
        this.startAutoSave();
        
        // 页面卸载时清理
        window.addEventListener('beforeunload', () => {
            this.stopAutoSave();
        });
    }
    
    startAutoSave() {
        this.autoSaveTimer = setInterval(() => {
            if (this.isDirty) {
                this.saveDraft();
            }
        }, this.options.autoSaveInterval);
    }
    
    stopAutoSave() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
            this.autoSaveTimer = null;
        }
    }
    
    saveDraft() {
        try {
            const formData = this.collectFormData();
            localStorage.setItem(this.draftKey, JSON.stringify({
                data: formData,
                timestamp: Date.now()
            }));
            
            // 显示保存提示
            this.showDraftSaved();
        } catch (error) {
            console.error('保存草稿失败:', error);
        }
    }
    
    loadDraft() {
        try {
            const draftData = localStorage.getItem(this.draftKey);
            if (draftData) {
                const { data, timestamp } = JSON.parse(draftData);
                
                // 检查草稿时效（24小时）
                if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
                    if (confirm('发现未保存的草稿数据，是否要恢复？')) {
                        this.populateFormWithDraft(data);
                        this.markDirty();
                    }
                } else {
                    // 清除过期草稿
                    this.clearDraft();
                }
            }
        } catch (error) {
            console.error('加载草稿失败:', error);
        }
    }
    
    clearDraft() {
        localStorage.removeItem(this.draftKey);
    }
    
    showDraftSaved() {
        // 显示自动保存提示
        const indicator = document.getElementById('auto-save-indicator');
        if (indicator) {
            indicator.textContent = '草稿已自动保存';
            indicator.style.display = 'block';
            
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 2000);
        }
    }
    
    async handleSubmit() {
        const result = await super.handleSubmit();
        
        // 提交成功后清除草稿
        if (result) {
            this.clearDraft();
        }
        
        return result;
    }
}
```

## 📱 响应式和可访问性

### 移动端优化

```css
/* 移动端专用样式 */
@media (max-width: 480px) {
    .license-update-form {
        padding: 16px;
        margin: 0 8px;
    }
    
    .form-row {
        flex-direction: column;
        gap: 12px;
    }
    
    .form-group input,
    .form-group select,
    .form-group textarea {
        font-size: 16px; /* 防止iOS缩放 */
        padding: 12px;
    }
    
    .metadata-item {
        flex-direction: column;
        gap: 8px;
    }
    
    .form-actions {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 16px 0;
        border-top: 1px solid #e8e8e8;
        margin: 0 -16px -16px -16px;
    }
}
```

### 键盘导航支持

```javascript
// 添加键盘导航功能
initKeyboardNavigation() {
    this.form.addEventListener('keydown', (e) => {
        // Ctrl+S 保存
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            if (this.isDirty && !this.isLoading) {
                this.handleSubmit();
            }
        }
        
        // Escape 取消
        if (e.key === 'Escape') {
            this.handleCancel();
        }
        
        // 方向键在表单字段间导航
        if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
            this.handleArrowKeyNavigation(e);
        }
    });
}

handleArrowKeyNavigation(e) {
    const focusableElements = this.form.querySelectorAll(
        'input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])'
    );
    
    const currentIndex = Array.from(focusableElements).indexOf(document.activeElement);
    
    if (currentIndex !== -1) {
        let nextIndex;
        if (e.key === 'ArrowUp') {
            nextIndex = currentIndex > 0 ? currentIndex - 1 : focusableElements.length - 1;
        } else {
            nextIndex = currentIndex < focusableElements.length - 1 ? currentIndex + 1 : 0;
        }
        
        focusableElements[nextIndex].focus();
        e.preventDefault();
    }
}
```

---

*文档版本: v1.0*  
*更新时间: 2024-09-30*  
*维护者: 开发团队*
