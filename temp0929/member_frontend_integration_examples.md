# Member试用许可证API前端集成示例

## 概述

本文档提供了Member试用许可证API在各种前端框架中的集成示例，包括原生JavaScript、React、Vue.js和Angular的实现代码。

---

## 通用配置

### API基础配置

```javascript
// 配置常量
const API_CONFIG = {
    BASE_URL: 'https://your-api-domain.com/api/v1/licenses',
    TIMEOUT: 30000, // 30秒超时
    RETRY_ATTEMPTS: 3
};

// API端点
const API_ENDPOINTS = {
    AVAILABLE_PRODUCTS: '/member/available-products/',
    APPLY_TRIAL: '/member/apply/',
    MY_LICENSES: '/member/my-licenses/'
};
```

### 认证配置

```javascript
// JWT令牌管理
class AuthManager {
    static getToken() {
        return localStorage.getItem('jwt_token');
    }
    
    static setToken(token) {
        localStorage.setItem('jwt_token', token);
    }
    
    static removeToken() {
        localStorage.removeItem('jwt_token');
    }
    
    static getAuthHeaders() {
        const token = this.getToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }
    
    static isAuthenticated() {
        return !!this.getToken();
    }
}
```

### 通用HTTP客户端

```javascript
class APIClient {
    constructor(baseURL = API_CONFIG.BASE_URL) {
        this.baseURL = baseURL;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...AuthManager.getAuthHeaders(),
                ...options.headers
            },
            timeout: API_CONFIG.TIMEOUT,
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            // 处理认证错误
            if (response.status === 401) {
                AuthManager.removeToken();
                throw new Error('认证失败，请重新登录');
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }
    
    get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }
    
    post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

const apiClient = new APIClient();
```

---

## 原生JavaScript实现

### 完整的试用申请页面

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>试用申请</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .product-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .product-applied { opacity: 0.6; background-color: #f0f0f0; }
        .btn { padding: 10px 15px; margin: 5px; border: none; border-radius: 3px; cursor: pointer; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-success { background-color: #28a745; color: white; }
        .btn-disabled { background-color: #6c757d; color: white; cursor: not-allowed; }
        .loading { color: #666; }
        .error { color: #dc3545; }
        .success { color: #28a745; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: white; margin: 15% auto; padding: 20px; border-radius: 5px; width: 80%; max-width: 500px; }
    </style>
</head>
<body>
    <h1>试用许可证申请</h1>
    
    <!-- 产品列表 -->
    <div id="products-section">
        <h2>可申请产品</h2>
        <div id="products-loading" class="loading">正在加载产品列表...</div>
        <div id="products-error" class="error" style="display: none;"></div>
        <div id="products-list"></div>
    </div>
    
    <!-- 我的许可证 -->
    <div id="licenses-section" style="margin-top: 30px;">
        <h2>我的许可证</h2>
        <div id="licenses-loading" class="loading">正在加载许可证列表...</div>
        <div id="licenses-error" class="error" style="display: none;"></div>
        <div id="licenses-list"></div>
    </div>
    
    <!-- 申请表单模态框 -->
    <div id="apply-modal" class="modal">
        <div class="modal-content">
            <h3>申请试用许可证</h3>
            <form id="apply-form">
                <div>
                    <label>申请原因:</label>
                    <textarea id="reason" rows="3" style="width: 100%; margin-top: 5px;"></textarea>
                </div>
                <div style="margin-top: 10px;">
                    <label>公司名称:</label>
                    <input type="text" id="company" style="width: 100%; margin-top: 5px;">
                </div>
                <div style="margin-top: 10px;">
                    <label>职位:</label>
                    <input type="text" id="job_title" style="width: 100%; margin-top: 5px;">
                </div>
                <div style="margin-top: 10px;">
                    <label>手机号:</label>
                    <input type="text" id="phone" style="width: 100%; margin-top: 5px;">
                </div>
                <div style="margin-top: 10px;">
                    <label>使用用途:</label>
                    <textarea id="intended_use" rows="3" style="width: 100%; margin-top: 5px;"></textarea>
                </div>
                <div style="margin-top: 15px;">
                    <button type="submit" class="btn btn-primary">提交申请</button>
                    <button type="button" class="btn" onclick="closeApplyModal()">取消</button>
                </div>
            </form>
            <div id="apply-loading" class="loading" style="display: none;">正在提交申请...</div>
            <div id="apply-error" class="error" style="display: none;"></div>
        </div>
    </div>

    <script>
        // 全局变量
        let currentProductId = null;
        
        // API服务类
        class LicenseAPIService {
            async getAvailableProducts() {
                return await apiClient.get(API_ENDPOINTS.AVAILABLE_PRODUCTS);
            }
            
            async applyTrialLicense(productId, reason, userInfo) {
                return await apiClient.post(API_ENDPOINTS.APPLY_TRIAL, {
                    product_id: productId,
                    reason: reason,
                    user_info: userInfo
                });
            }
            
            async getMyLicenses(filters = {}) {
                return await apiClient.get(API_ENDPOINTS.MY_LICENSES, filters);
            }
        }
        
        const licenseAPI = new LicenseAPIService();
        
        // 页面初始化
        document.addEventListener('DOMContentLoaded', function() {
            loadAvailableProducts();
            loadMyLicenses();
        });
        
        // 加载可申请产品
        async function loadAvailableProducts() {
            const loadingEl = document.getElementById('products-loading');
            const errorEl = document.getElementById('products-error');
            const listEl = document.getElementById('products-list');
            
            try {
                loadingEl.style.display = 'block';
                errorEl.style.display = 'none';
                
                const response = await licenseAPI.getAvailableProducts();
                
                if (response.success) {
                    renderProductsList(response.data.products);
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                errorEl.textContent = `加载失败: ${error.message}`;
                errorEl.style.display = 'block';
            } finally {
                loadingEl.style.display = 'none';
            }
        }
        
        // 渲染产品列表
        function renderProductsList(products) {
            const listEl = document.getElementById('products-list');
            
            if (products.length === 0) {
                listEl.innerHTML = '<p>暂无可申请的产品</p>';
                return;
            }
            
            const html = products.map(product => `
                <div class="product-card ${product.already_applied ? 'product-applied' : ''}">
                    <h3>${product.name} (${product.version})</h3>
                    <p>${product.description}</p>
                    <div>
                        <strong>试用方案:</strong> ${product.trial_plan.name} 
                        (${product.trial_plan.default_validity_days}天, 
                        最多${product.trial_plan.default_max_activations}个设备)
                    </div>
                    <div style="margin-top: 10px;">
                        ${product.already_applied ? 
                            '<button class="btn btn-disabled" disabled>已申请</button>' :
                            `<button class="btn btn-primary" onclick="openApplyModal(${product.id})">申请试用</button>`
                        }
                    </div>
                </div>
            `).join('');
            
            listEl.innerHTML = html;
        }
        
        // 打开申请模态框
        function openApplyModal(productId) {
            currentProductId = productId;
            document.getElementById('apply-modal').style.display = 'block';
        }
        
        // 关闭申请模态框
        function closeApplyModal() {
            document.getElementById('apply-modal').style.display = 'none';
            document.getElementById('apply-form').reset();
            document.getElementById('apply-error').style.display = 'none';
        }
        
        // 处理申请表单提交
        document.getElementById('apply-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const loadingEl = document.getElementById('apply-loading');
            const errorEl = document.getElementById('apply-error');
            
            try {
                loadingEl.style.display = 'block';
                errorEl.style.display = 'none';
                
                const formData = new FormData(this);
                const userInfo = {
                    company: document.getElementById('company').value,
                    job_title: document.getElementById('job_title').value,
                    phone: document.getElementById('phone').value,
                    intended_use: document.getElementById('intended_use').value
                };
                
                const response = await licenseAPI.applyTrialLicense(
                    currentProductId,
                    document.getElementById('reason').value || '试用版申请',
                    userInfo
                );
                
                if (response.success) {
                    alert('申请成功！许可证密钥: ' + response.data.license_key);
                    closeApplyModal();
                    loadAvailableProducts(); // 刷新产品列表
                    loadMyLicenses(); // 刷新许可证列表
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                errorEl.textContent = `申请失败: ${error.message}`;
                errorEl.style.display = 'block';
            } finally {
                loadingEl.style.display = 'none';
            }
        });
        
        // 加载我的许可证
        async function loadMyLicenses() {
            const loadingEl = document.getElementById('licenses-loading');
            const errorEl = document.getElementById('licenses-error');
            const listEl = document.getElementById('licenses-list');
            
            try {
                loadingEl.style.display = 'block';
                errorEl.style.display = 'none';
                
                const response = await licenseAPI.getMyLicenses();
                
                if (response.success) {
                    renderLicensesList(response.data);
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                errorEl.textContent = `加载失败: ${error.message}`;
                errorEl.style.display = 'block';
            } finally {
                loadingEl.style.display = 'none';
            }
        }
        
        // 渲染许可证列表
        function renderLicensesList(data) {
            const listEl = document.getElementById('licenses-list');
            
            if (data.licenses.length === 0) {
                listEl.innerHTML = '<p>您还没有任何许可证</p>';
                return;
            }
            
            const statsHtml = `
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin-bottom: 15px;">
                    <strong>统计信息:</strong> 
                    总计 ${data.count} 个, 
                    有效 ${data.active_count} 个, 
                    试用版 ${data.trial_count} 个, 
                    即将过期 ${data.expiring_soon_count} 个
                </div>
            `;
            
            const licensesHtml = data.licenses.map(license => `
                <div class="product-card">
                    <h3>${license.product_name} ${license.product_version} - ${license.plan_name}</h3>
                    <div><strong>许可证密钥:</strong> ${license.license_key_preview}</div>
                    <div><strong>状态:</strong> ${license.status_display}</div>
                    <div><strong>分配时间:</strong> ${new Date(license.assigned_at).toLocaleString()}</div>
                    <div><strong>过期时间:</strong> ${new Date(license.expires_at).toLocaleString()}</div>
                    <div><strong>剩余天数:</strong> ${license.days_until_expiry} 天</div>
                    <div><strong>激活信息:</strong> ${license.activation_info.current_activations}/${license.activation_info.max_activations} (可用: ${license.activation_info.available_slots})</div>
                    <div><strong>使用次数:</strong> ${license.usage_count}</div>
                    ${license.can_activate_license ? 
                        '<div style="color: green;">✓ 可以激活</div>' : 
                        '<div style="color: red;">✗ 无法激活</div>'
                    }
                </div>
            `).join('');
            
            listEl.innerHTML = statsHtml + licensesHtml;
        }
    </script>
</body>
</html>
```

---

## React实现

### Hooks和组件

```jsx
// hooks/useLicenseAPI.js
import { useState, useCallback } from 'react';
import { apiClient, API_ENDPOINTS } from '../utils/api';

export const useLicenseAPI = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const getAvailableProducts = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await apiClient.get(API_ENDPOINTS.AVAILABLE_PRODUCTS);
            return response.success ? response.data : null;
        } catch (err) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const applyTrialLicense = useCallback(async (productId, reason, userInfo) => {
        setLoading(true);
        setError(null);
        try {
            const response = await apiClient.post(API_ENDPOINTS.APPLY_TRIAL, {
                product_id: productId,
                reason,
                user_info: userInfo
            });
            return response.success ? response.data : null;
        } catch (err) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const getMyLicenses = useCallback(async (filters = {}) => {
        setLoading(true);
        setError(null);
        try {
            const response = await apiClient.get(API_ENDPOINTS.MY_LICENSES, filters);
            return response.success ? response.data : null;
        } catch (err) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        loading,
        error,
        getAvailableProducts,
        applyTrialLicense,
        getMyLicenses
    };
};
```

```jsx
// components/ProductsList.jsx
import React, { useState, useEffect } from 'react';
import { useLicenseAPI } from '../hooks/useLicenseAPI';
import { ApplyModal } from './ApplyModal';

export const ProductsList = ({ onApplySuccess }) => {
    const [products, setProducts] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const { loading, error, getAvailableProducts } = useLicenseAPI();

    useEffect(() => {
        loadProducts();
    }, []);

    const loadProducts = async () => {
        const data = await getAvailableProducts();
        if (data) {
            setProducts(data.products);
        }
    };

    const handleApplyClick = (product) => {
        setSelectedProduct(product);
        setShowModal(true);
    };

    const handleApplySuccess = (result) => {
        setShowModal(false);
        loadProducts(); // 刷新列表
        onApplySuccess && onApplySuccess(result);
    };

    if (loading) return <div className="loading">正在加载产品列表...</div>;
    if (error) return <div className="error">加载失败: {error}</div>;

    return (
        <div className="products-list">
            <h2>可申请产品 ({products.length})</h2>
            {products.length === 0 ? (
                <p>暂无可申请的产品</p>
            ) : (
                products.map(product => (
                    <div key={product.id} className={`product-card ${product.already_applied ? 'applied' : ''}`}>
                        <h3>{product.name} ({product.version})</h3>
                        <p>{product.description}</p>
                        <div className="trial-info">
                            <strong>试用方案:</strong> {product.trial_plan.name} 
                            ({product.trial_plan.default_validity_days}天, 
                            最多{product.trial_plan.default_max_activations}个设备)
                        </div>
                        {product.trial_plan.features && (
                            <div className="features">
                                <strong>功能:</strong> 
                                {Object.entries(product.trial_plan.features).map(([key, value]) => (
                                    <span key={key} className="feature-tag">
                                        {key}: {typeof value === 'boolean' ? (value ? '是' : '否') : value}
                                    </span>
                                ))}
                            </div>
                        )}
                        <div className="actions">
                            {product.already_applied ? (
                                <button className="btn btn-disabled" disabled>
                                    已申请
                                </button>
                            ) : (
                                <button 
                                    className="btn btn-primary" 
                                    onClick={() => handleApplyClick(product)}
                                >
                                    申请试用
                                </button>
                            )}
                        </div>
                    </div>
                ))
            )}
            
            {showModal && selectedProduct && (
                <ApplyModal 
                    product={selectedProduct}
                    onClose={() => setShowModal(false)}
                    onSuccess={handleApplySuccess}
                />
            )}
        </div>
    );
};
```

```jsx
// components/ApplyModal.jsx
import React, { useState } from 'react';
import { useLicenseAPI } from '../hooks/useLicenseAPI';

export const ApplyModal = ({ product, onClose, onSuccess }) => {
    const [formData, setFormData] = useState({
        reason: '',
        company: '',
        job_title: '',
        phone: '',
        intended_use: ''
    });
    const { loading, error, applyTrialLicense } = useLicenseAPI();

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        const userInfo = {
            company: formData.company,
            job_title: formData.job_title,
            phone: formData.phone,
            intended_use: formData.intended_use
        };

        const result = await applyTrialLicense(
            product.id,
            formData.reason || '试用版申请',
            userInfo
        );

        if (result) {
            onSuccess(result);
        }
    };

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h3>申请试用许可证 - {product.name}</h3>
                
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>申请原因:</label>
                        <textarea
                            value={formData.reason}
                            onChange={(e) => handleChange('reason', e.target.value)}
                            rows={3}
                            placeholder="请简述申请试用的原因..."
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>公司名称:</label>
                        <input
                            type="text"
                            value={formData.company}
                            onChange={(e) => handleChange('company', e.target.value)}
                            placeholder="请输入公司名称"
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>职位:</label>
                        <input
                            type="text"
                            value={formData.job_title}
                            onChange={(e) => handleChange('job_title', e.target.value)}
                            placeholder="请输入您的职位"
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>手机号:</label>
                        <input
                            type="text"
                            value={formData.phone}
                            onChange={(e) => handleChange('phone', e.target.value)}
                            placeholder="请输入手机号"
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>使用用途:</label>
                        <textarea
                            value={formData.intended_use}
                            onChange={(e) => handleChange('intended_use', e.target.value)}
                            rows={3}
                            placeholder="请描述您的具体使用用途..."
                        />
                    </div>
                    
                    {error && <div className="error">申请失败: {error}</div>}
                    
                    <div className="form-actions">
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? '申请中...' : '提交申请'}
                        </button>
                        <button type="button" className="btn btn-secondary" onClick={onClose}>
                            取消
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
```

```jsx
// components/LicensesList.jsx
import React, { useState, useEffect } from 'react';
import { useLicenseAPI } from '../hooks/useLicenseAPI';

export const LicensesList = () => {
    const [licenses, setLicenses] = useState([]);
    const [stats, setStats] = useState({});
    const [filters, setFilters] = useState({
        status: '',
        plan_type: ''
    });
    const { loading, error, getMyLicenses } = useLicenseAPI();

    useEffect(() => {
        loadLicenses();
    }, [filters]);

    const loadLicenses = async () => {
        const cleanFilters = Object.fromEntries(
            Object.entries(filters).filter(([_, value]) => value !== '')
        );
        
        const data = await getMyLicenses(cleanFilters);
        if (data) {
            setLicenses(data.licenses);
            setStats({
                count: data.count,
                active_count: data.active_count,
                trial_count: data.trial_count,
                expiring_soon_count: data.expiring_soon_count
            });
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('zh-CN');
    };

    if (loading) return <div className="loading">正在加载许可证列表...</div>;
    if (error) return <div className="error">加载失败: {error}</div>;

    return (
        <div className="licenses-list">
            <div className="licenses-header">
                <h2>我的许可证</h2>
                
                {/* 统计信息 */}
                <div className="stats-card">
                    <div className="stats-item">
                        <span className="stats-number">{stats.count}</span>
                        <span className="stats-label">总计</span>
                    </div>
                    <div className="stats-item">
                        <span className="stats-number">{stats.active_count}</span>
                        <span className="stats-label">有效</span>
                    </div>
                    <div className="stats-item">
                        <span className="stats-number">{stats.trial_count}</span>
                        <span className="stats-label">试用版</span>
                    </div>
                    <div className="stats-item">
                        <span className="stats-number">{stats.expiring_soon_count}</span>
                        <span className="stats-label">即将过期</span>
                    </div>
                </div>
                
                {/* 过滤器 */}
                <div className="filters">
                    <select 
                        value={filters.status}
                        onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                    >
                        <option value="">所有状态</option>
                        <option value="active">有效</option>
                        <option value="pending">待激活</option>
                        <option value="expired">已过期</option>
                        <option value="revoked">已撤销</option>
                    </select>
                    
                    <select 
                        value={filters.plan_type}
                        onChange={(e) => setFilters(prev => ({ ...prev, plan_type: e.target.value }))}
                    >
                        <option value="">所有类型</option>
                        <option value="trial">试用版</option>
                        <option value="basic">基础版</option>
                        <option value="professional">专业版</option>
                        <option value="enterprise">企业版</option>
                    </select>
                </div>
            </div>
            
            {/* 许可证列表 */}
            <div className="licenses-grid">
                {licenses.length === 0 ? (
                    <p>没有找到匹配的许可证</p>
                ) : (
                    licenses.map(license => (
                        <div key={license.id} className={`license-card ${license.status}`}>
                            <div className="license-header">
                                <h3>{license.product_name} {license.product_version}</h3>
                                <span className={`status-badge ${license.status}`}>
                                    {license.status_display}
                                </span>
                            </div>
                            
                            <div className="license-details">
                                <div className="detail-row">
                                    <span className="label">方案:</span>
                                    <span className="value">{license.plan_name}</span>
                                </div>
                                
                                <div className="detail-row">
                                    <span className="label">许可证密钥:</span>
                                    <span className="value monospace">{license.license_key_preview}</span>
                                </div>
                                
                                <div className="detail-row">
                                    <span className="label">分配时间:</span>
                                    <span className="value">{formatDate(license.assigned_at)}</span>
                                </div>
                                
                                <div className="detail-row">
                                    <span className="label">过期时间:</span>
                                    <span className="value">{formatDate(license.expires_at)}</span>
                                </div>
                                
                                <div className="detail-row">
                                    <span className="label">剩余天数:</span>
                                    <span className={`value ${license.days_until_expiry <= 7 ? 'warning' : ''}`}>
                                        {license.days_until_expiry} 天
                                    </span>
                                </div>
                                
                                <div className="detail-row">
                                    <span className="label">激活情况:</span>
                                    <span className="value">
                                        {license.activation_info.current_activations}/
                                        {license.activation_info.max_activations}
                                        (可用: {license.activation_info.available_slots})
                                    </span>
                                </div>
                                
                                <div className="detail-row">
                                    <span className="label">使用次数:</span>
                                    <span className="value">{license.usage_count}</span>
                                </div>
                                
                                {license.last_used_at && (
                                    <div className="detail-row">
                                        <span className="label">最后使用:</span>
                                        <span className="value">{formatDate(license.last_used_at)}</span>
                                    </div>
                                )}
                            </div>
                            
                            <div className="license-actions">
                                {license.can_activate_license ? (
                                    <span className="status-indicator success">可以激活</span>
                                ) : (
                                    <span className="status-indicator error">无法激活</span>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
```

```jsx
// App.jsx
import React, { useState } from 'react';
import { ProductsList } from './components/ProductsList';
import { LicensesList } from './components/LicensesList';
import './styles/app.css';

function App() {
    const [activeTab, setActiveTab] = useState('products');

    const handleApplySuccess = (result) => {
        alert(`申请成功！许可证密钥: ${result.license_key}`);
        setActiveTab('licenses'); // 切换到许可证列表
    };

    return (
        <div className="app">
            <header className="app-header">
                <h1>许可证管理</h1>
                <nav className="nav-tabs">
                    <button 
                        className={`nav-tab ${activeTab === 'products' ? 'active' : ''}`}
                        onClick={() => setActiveTab('products')}
                    >
                        申请试用
                    </button>
                    <button 
                        className={`nav-tab ${activeTab === 'licenses' ? 'active' : ''}`}
                        onClick={() => setActiveTab('licenses')}
                    >
                        我的许可证
                    </button>
                </nav>
            </header>
            
            <main className="app-content">
                {activeTab === 'products' && (
                    <ProductsList onApplySuccess={handleApplySuccess} />
                )}
                {activeTab === 'licenses' && (
                    <LicensesList />
                )}
            </main>
        </div>
    );
}

export default App;
```

---

## Vue.js实现

### Composables和组件

```javascript
// composables/useLicenseAPI.js
import { ref, reactive } from 'vue';
import { apiClient, API_ENDPOINTS } from '../utils/api';

export function useLicenseAPI() {
    const loading = ref(false);
    const error = ref(null);

    const getAvailableProducts = async () => {
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.get(API_ENDPOINTS.AVAILABLE_PRODUCTS);
            return response.success ? response.data : null;
        } catch (err) {
            error.value = err.message;
            return null;
        } finally {
            loading.value = false;
        }
    };

    const applyTrialLicense = async (productId, reason, userInfo) => {
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.post(API_ENDPOINTS.APPLY_TRIAL, {
                product_id: productId,
                reason,
                user_info: userInfo
            });
            return response.success ? response.data : null;
        } catch (err) {
            error.value = err.message;
            return null;
        } finally {
            loading.value = false;
        }
    };

    const getMyLicenses = async (filters = {}) => {
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.get(API_ENDPOINTS.MY_LICENSES, filters);
            return response.success ? response.data : null;
        } catch (err) {
            error.value = err.message;
            return null;
        } finally {
            loading.value = false;
        }
    };

    return {
        loading: readonly(loading),
        error: readonly(error),
        getAvailableProducts,
        applyTrialLicense,
        getMyLicenses
    };
}
```

```vue
<!-- components/ProductsList.vue -->
<template>
    <div class="products-list">
        <h2>可申请产品 ({{ products.length }})</h2>
        
        <div v-if="loading" class="loading">
            正在加载产品列表...
        </div>
        
        <div v-else-if="error" class="error">
            加载失败: {{ error }}
        </div>
        
        <div v-else-if="products.length === 0" class="empty">
            暂无可申请的产品
        </div>
        
        <div v-else class="products-grid">
            <div 
                v-for="product in products" 
                :key="product.id"
                :class="['product-card', { applied: product.already_applied }]"
            >
                <h3>{{ product.name }} ({{ product.version }})</h3>
                <p>{{ product.description }}</p>
                
                <div class="trial-info">
                    <strong>试用方案:</strong> {{ product.trial_plan.name }}
                    ({{ product.trial_plan.default_validity_days }}天,
                    最多{{ product.trial_plan.default_max_activations }}个设备)
                </div>
                
                <div v-if="product.trial_plan.features" class="features">
                    <strong>功能:</strong>
                    <span 
                        v-for="[key, value] in Object.entries(product.trial_plan.features)" 
                        :key="key"
                        class="feature-tag"
                    >
                        {{ key }}: {{ formatFeatureValue(value) }}
                    </span>
                </div>
                
                <div class="actions">
                    <button 
                        v-if="product.already_applied"
                        class="btn btn-disabled" 
                        disabled
                    >
                        已申请
                    </button>
                    <button 
                        v-else
                        class="btn btn-primary" 
                        @click="openApplyModal(product)"
                    >
                        申请试用
                    </button>
                </div>
            </div>
        </div>
        
        <ApplyModal 
            v-if="showModal"
            :product="selectedProduct"
            @close="closeApplyModal"
            @success="handleApplySuccess"
        />
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useLicenseAPI } from '../composables/useLicenseAPI';
import ApplyModal from './ApplyModal.vue';

// Props & Emits
const emit = defineEmits(['applySuccess']);

// State
const products = ref([]);
const selectedProduct = ref(null);
const showModal = ref(false);

// Composables
const { loading, error, getAvailableProducts } = useLicenseAPI();

// Methods
const loadProducts = async () => {
    const data = await getAvailableProducts();
    if (data) {
        products.value = data.products;
    }
};

const openApplyModal = (product) => {
    selectedProduct.value = product;
    showModal.value = true;
};

const closeApplyModal = () => {
    showModal.value = false;
    selectedProduct.value = null;
};

const handleApplySuccess = (result) => {
    closeApplyModal();
    loadProducts(); // 刷新列表
    emit('applySuccess', result);
};

const formatFeatureValue = (value) => {
    if (typeof value === 'boolean') {
        return value ? '是' : '否';
    }
    return value;
};

// Lifecycle
onMounted(() => {
    loadProducts();
});
</script>
```

```vue
<!-- components/ApplyModal.vue -->
<template>
    <div class="modal-overlay" @click.self="$emit('close')">
        <div class="modal-content">
            <h3>申请试用许可证 - {{ product.name }}</h3>
            
            <form @submit.prevent="handleSubmit">
                <div class="form-group">
                    <label>申请原因:</label>
                    <textarea
                        v-model="formData.reason"
                        rows="3"
                        placeholder="请简述申请试用的原因..."
                    />
                </div>
                
                <div class="form-group">
                    <label>公司名称:</label>
                    <input
                        v-model="formData.company"
                        type="text"
                        placeholder="请输入公司名称"
                    />
                </div>
                
                <div class="form-group">
                    <label>职位:</label>
                    <input
                        v-model="formData.job_title"
                        type="text"
                        placeholder="请输入您的职位"
                    />
                </div>
                
                <div class="form-group">
                    <label>手机号:</label>
                    <input
                        v-model="formData.phone"
                        type="text"
                        placeholder="请输入手机号"
                    />
                </div>
                
                <div class="form-group">
                    <label>使用用途:</label>
                    <textarea
                        v-model="formData.intended_use"
                        rows="3"
                        placeholder="请描述您的具体使用用途..."
                    />
                </div>
                
                <div v-if="error" class="error">
                    申请失败: {{ error }}
                </div>
                
                <div class="form-actions">
                    <button 
                        type="submit" 
                        class="btn btn-primary" 
                        :disabled="loading"
                    >
                        {{ loading ? '申请中...' : '提交申请' }}
                    </button>
                    <button 
                        type="button" 
                        class="btn btn-secondary" 
                        @click="$emit('close')"
                    >
                        取消
                    </button>
                </div>
            </form>
        </div>
    </div>
</template>

<script setup>
import { reactive } from 'vue';
import { useLicenseAPI } from '../composables/useLicenseAPI';

// Props & Emits
const props = defineProps({
    product: {
        type: Object,
        required: true
    }
});

const emit = defineEmits(['close', 'success']);

// State
const formData = reactive({
    reason: '',
    company: '',
    job_title: '',
    phone: '',
    intended_use: ''
});

// Composables
const { loading, error, applyTrialLicense } = useLicenseAPI();

// Methods
const handleSubmit = async () => {
    const userInfo = {
        company: formData.company,
        job_title: formData.job_title,
        phone: formData.phone,
        intended_use: formData.intended_use
    };

    const result = await applyTrialLicense(
        props.product.id,
        formData.reason || '试用版申请',
        userInfo
    );

    if (result) {
        emit('success', result);
    }
};
</script>
```

```vue
<!-- components/LicensesList.vue -->
<template>
    <div class="licenses-list">
        <div class="licenses-header">
            <h2>我的许可证</h2>
            
            <!-- 统计信息 -->
            <div class="stats-card">
                <div class="stats-item">
                    <span class="stats-number">{{ stats.count }}</span>
                    <span class="stats-label">总计</span>
                </div>
                <div class="stats-item">
                    <span class="stats-number">{{ stats.active_count }}</span>
                    <span class="stats-label">有效</span>
                </div>
                <div class="stats-item">
                    <span class="stats-number">{{ stats.trial_count }}</span>
                    <span class="stats-label">试用版</span>
                </div>
                <div class="stats-item">
                    <span class="stats-number">{{ stats.expiring_soon_count }}</span>
                    <span class="stats-label">即将过期</span>
                </div>
            </div>
            
            <!-- 过滤器 -->
            <div class="filters">
                <select v-model="filters.status">
                    <option value="">所有状态</option>
                    <option value="active">有效</option>
                    <option value="pending">待激活</option>
                    <option value="expired">已过期</option>
                    <option value="revoked">已撤销</option>
                </select>
                
                <select v-model="filters.plan_type">
                    <option value="">所有类型</option>
                    <option value="trial">试用版</option>
                    <option value="basic">基础版</option>
                    <option value="professional">专业版</option>
                    <option value="enterprise">企业版</option>
                </select>
            </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="loading">
            正在加载许可证列表...
        </div>
        
        <div v-else-if="error" class="error">
            加载失败: {{ error }}
        </div>
        
        <!-- 许可证列表 -->
        <div v-else-if="licenses.length === 0" class="empty">
            没有找到匹配的许可证
        </div>
        
        <div v-else class="licenses-grid">
            <div 
                v-for="license in licenses" 
                :key="license.id"
                :class="['license-card', license.status]"
            >
                <div class="license-header">
                    <h3>{{ license.product_name }} {{ license.product_version }}</h3>
                    <span :class="['status-badge', license.status]">
                        {{ license.status_display }}
                    </span>
                </div>
                
                <div class="license-details">
                    <div class="detail-row">
                        <span class="label">方案:</span>
                        <span class="value">{{ license.plan_name }}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label">许可证密钥:</span>
                        <span class="value monospace">{{ license.license_key_preview }}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label">分配时间:</span>
                        <span class="value">{{ formatDate(license.assigned_at) }}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label">过期时间:</span>
                        <span class="value">{{ formatDate(license.expires_at) }}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label">剩余天数:</span>
                        <span :class="['value', { warning: license.days_until_expiry <= 7 }]">
                            {{ license.days_until_expiry }} 天
                        </span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label">激活情况:</span>
                        <span class="value">
                            {{ license.activation_info.current_activations }}/
                            {{ license.activation_info.max_activations }}
                            (可用: {{ license.activation_info.available_slots }})
                        </span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label">使用次数:</span>
                        <span class="value">{{ license.usage_count }}</span>
                    </div>
                    
                    <div v-if="license.last_used_at" class="detail-row">
                        <span class="label">最后使用:</span>
                        <span class="value">{{ formatDate(license.last_used_at) }}</span>
                    </div>
                </div>
                
                <div class="license-actions">
                    <span 
                        :class="['status-indicator', license.can_activate_license ? 'success' : 'error']"
                    >
                        {{ license.can_activate_license ? '可以激活' : '无法激活' }}
                    </span>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue';
import { useLicenseAPI } from '../composables/useLicenseAPI';

// State
const licenses = ref([]);
const stats = reactive({
    count: 0,
    active_count: 0,
    trial_count: 0,
    expiring_soon_count: 0
});
const filters = reactive({
    status: '',
    plan_type: ''
});

// Composables
const { loading, error, getMyLicenses } = useLicenseAPI();

// Methods
const loadLicenses = async () => {
    const cleanFilters = Object.fromEntries(
        Object.entries(filters).filter(([_, value]) => value !== '')
    );
    
    const data = await getMyLicenses(cleanFilters);
    if (data) {
        licenses.value = data.licenses;
        Object.assign(stats, {
            count: data.count,
            active_count: data.active_count,
            trial_count: data.trial_count,
            expiring_soon_count: data.expiring_soon_count
        });
    }
};

const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('zh-CN');
};

// Watchers
watch(filters, loadLicenses, { deep: true });

// Lifecycle
onMounted(() => {
    loadLicenses();
});
</script>
```

```vue
<!-- App.vue -->
<template>
    <div class="app">
        <header class="app-header">
            <h1>许可证管理</h1>
            <nav class="nav-tabs">
                <button 
                    :class="['nav-tab', { active: activeTab === 'products' }]"
                    @click="activeTab = 'products'"
                >
                    申请试用
                </button>
                <button 
                    :class="['nav-tab', { active: activeTab === 'licenses' }]"
                    @click="activeTab = 'licenses'"
                >
                    我的许可证
                </button>
            </nav>
        </header>
        
        <main class="app-content">
            <ProductsList 
                v-if="activeTab === 'products'"
                @apply-success="handleApplySuccess"
            />
            <LicensesList v-else-if="activeTab === 'licenses'" />
        </main>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import ProductsList from './components/ProductsList.vue';
import LicensesList from './components/LicensesList.vue';

const activeTab = ref('products');

const handleApplySuccess = (result) => {
    alert(`申请成功！许可证密钥: ${result.license_key}`);
    activeTab.value = 'licenses'; // 切换到许可证列表
};
</script>
```

---

## Angular实现

### 服务和组件

```typescript
// services/license-api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  code?: string;
  errors?: any;
}

export interface Product {
  id: number;
  name: string;
  code: string;
  description: string;
  version: string;
  trial_plan: {
    id: number;
    name: string;
    default_validity_days: number;
    default_max_activations: number;
    features: { [key: string]: any };
    price: number;
    currency: string;
  };
  already_applied: boolean;
}

export interface License {
  id: number;
  product_name: string;
  product_code: string;
  product_version: string;
  plan_name: string;
  plan_type: string;
  license_key_preview: string;
  status: string;
  status_display: string;
  assigned_at: string;
  expires_at: string;
  days_until_expiry: number;
  activation_info: {
    current_activations: number;
    max_activations: number;
    available_slots: number;
  };
  usage_count: number;
  last_used_at?: string;
  can_activate_license: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class LicenseApiService {
  private readonly baseUrl = 'https://your-api-domain.com/api/v1/licenses';

  constructor(private http: HttpClient) {}

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('jwt_token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    });
  }

  private handleError(error: any): Observable<never> {
    console.error('API Error:', error);
    const message = error.error?.error || error.message || 'Unknown error';
    return throwError(() => new Error(message));
  }

  getAvailableProducts(): Observable<{ count: number; products: Product[] }> {
    return this.http.get<ApiResponse<{ count: number; products: Product[] }>>(
      `${this.baseUrl}/member/available-products/`,
      { headers: this.getAuthHeaders() }
    ).pipe(
      map(response => {
        if (!response.success) {
          throw new Error(response.error || 'Failed to fetch products');
        }
        return response.data!;
      }),
      catchError(this.handleError)
    );
  }

  applyTrialLicense(productId: number, reason: string, userInfo: any): Observable<any> {
    const payload = {
      product_id: productId,
      reason,
      user_info: userInfo
    };

    return this.http.post<ApiResponse>(
      `${this.baseUrl}/member/apply/`,
      payload,
      { headers: this.getAuthHeaders() }
    ).pipe(
      map(response => {
        if (!response.success) {
          throw new Error(response.error || 'Application failed');
        }
        return response.data;
      }),
      catchError(this.handleError)
    );
  }

  getMyLicenses(filters: any = {}): Observable<{
    count: number;
    active_count: number;
    trial_count: number;
    expiring_soon_count: number;
    licenses: License[];
  }> {
    let params = new HttpParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) {
        params = params.set(key, filters[key]);
      }
    });

    return this.http.get<ApiResponse<{
      count: number;
      active_count: number;
      trial_count: number;
      expiring_soon_count: number;
      licenses: License[];
    }>>(
      `${this.baseUrl}/member/my-licenses/`,
      { headers: this.getAuthHeaders(), params }
    ).pipe(
      map(response => {
        if (!response.success) {
          throw new Error(response.error || 'Failed to fetch licenses');
        }
        return response.data!;
      }),
      catchError(this.handleError)
    );
  }
}
```

```typescript
// components/products-list/products-list.component.ts
import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { LicenseApiService, Product } from '../../services/license-api.service';

@Component({
  selector: 'app-products-list',
  templateUrl: './products-list.component.html',
  styleUrls: ['./products-list.component.scss']
})
export class ProductsListComponent implements OnInit {
  @Output() applySuccess = new EventEmitter<any>();

  products: Product[] = [];
  loading = false;
  error: string | null = null;
  showModal = false;
  selectedProduct: Product | null = null;

  constructor(private licenseApiService: LicenseApiService) {}

  ngOnInit(): void {
    this.loadProducts();
  }

  async loadProducts(): Promise<void> {
    this.loading = true;
    this.error = null;

    try {
      const data = await this.licenseApiService.getAvailableProducts().toPromise();
      if (data) {
        this.products = data.products;
      }
    } catch (error: any) {
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  }

  openApplyModal(product: Product): void {
    this.selectedProduct = product;
    this.showModal = true;
  }

  closeApplyModal(): void {
    this.showModal = false;
    this.selectedProduct = null;
  }

  onApplySuccess(result: any): void {
    this.closeApplyModal();
    this.loadProducts(); // 刷新列表
    this.applySuccess.emit(result);
  }

  getFeatureValue(value: any): string {
    if (typeof value === 'boolean') {
      return value ? '是' : '否';
    }
    return String(value);
  }
}
```

```html
<!-- components/products-list/products-list.component.html -->
<div class="products-list">
    <h2>可申请产品 ({{ products.length }})</h2>

    <div *ngIf="loading" class="loading">
        正在加载产品列表...
    </div>

    <div *ngIf="error" class="error">
        加载失败: {{ error }}
    </div>

    <div *ngIf="!loading && !error && products.length === 0" class="empty">
        暂无可申请的产品
    </div>

    <div *ngIf="!loading && !error && products.length > 0" class="products-grid">
        <div 
            *ngFor="let product of products"
            [class]="'product-card' + (product.already_applied ? ' applied' : '')"
        >
            <h3>{{ product.name }} ({{ product.version }})</h3>
            <p>{{ product.description }}</p>

            <div class="trial-info">
                <strong>试用方案:</strong> {{ product.trial_plan.name }}
                ({{ product.trial_plan.default_validity_days }}天,
                最多{{ product.trial_plan.default_max_activations }}个设备)
            </div>

            <div *ngIf="product.trial_plan.features" class="features">
                <strong>功能:</strong>
                <span 
                    *ngFor="let feature of product.trial_plan.features | keyvalue"
                    class="feature-tag"
                >
                    {{ feature.key }}: {{ getFeatureValue(feature.value) }}
                </span>
            </div>

            <div class="actions">
                <button 
                    *ngIf="product.already_applied"
                    class="btn btn-disabled" 
                    disabled
                >
                    已申请
                </button>
                <button 
                    *ngIf="!product.already_applied"
                    class="btn btn-primary" 
                    (click)="openApplyModal(product)"
                >
                    申请试用
                </button>
            </div>
        </div>
    </div>

    <app-apply-modal 
        *ngIf="showModal && selectedProduct"
        [product]="selectedProduct"
        (close)="closeApplyModal()"
        (success)="onApplySuccess($event)"
    ></app-apply-modal>
</div>
```

```typescript
// components/apply-modal/apply-modal.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { LicenseApiService, Product } from '../../services/license-api.service';

@Component({
  selector: 'app-apply-modal',
  templateUrl: './apply-modal.component.html',
  styleUrls: ['./apply-modal.component.scss']
})
export class ApplyModalComponent {
  @Input() product!: Product;
  @Output() close = new EventEmitter<void>();
  @Output() success = new EventEmitter<any>();

  applyForm: FormGroup;
  loading = false;
  error: string | null = null;

  constructor(
    private fb: FormBuilder,
    private licenseApiService: LicenseApiService
  ) {
    this.applyForm = this.fb.group({
      reason: [''],
      company: [''],
      job_title: [''],
      phone: [''],
      intended_use: ['']
    });
  }

  async onSubmit(): Promise<void> {
    if (this.loading) return;

    this.loading = true;
    this.error = null;

    try {
      const formValue = this.applyForm.value;
      const userInfo = {
        company: formValue.company,
        job_title: formValue.job_title,
        phone: formValue.phone,
        intended_use: formValue.intended_use
      };

      const result = await this.licenseApiService.applyTrialLicense(
        this.product.id,
        formValue.reason || '试用版申请',
        userInfo
      ).toPromise();

      this.success.emit(result);
    } catch (error: any) {
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  }

  onClose(): void {
    this.close.emit();
  }
}
```

```html
<!-- components/apply-modal/apply-modal.component.html -->
<div class="modal-overlay" (click)="onClose()">
    <div class="modal-content" (click)="$event.stopPropagation()">
        <h3>申请试用许可证 - {{ product.name }}</h3>

        <form [formGroup]="applyForm" (ngSubmit)="onSubmit()">
            <div class="form-group">
                <label>申请原因:</label>
                <textarea
                    formControlName="reason"
                    rows="3"
                    placeholder="请简述申请试用的原因..."
                ></textarea>
            </div>

            <div class="form-group">
                <label>公司名称:</label>
                <input
                    formControlName="company"
                    type="text"
                    placeholder="请输入公司名称"
                />
            </div>

            <div class="form-group">
                <label>职位:</label>
                <input
                    formControlName="job_title"
                    type="text"
                    placeholder="请输入您的职位"
                />
            </div>

            <div class="form-group">
                <label>手机号:</label>
                <input
                    formControlName="phone"
                    type="text"
                    placeholder="请输入手机号"
                />
            </div>

            <div class="form-group">
                <label>使用用途:</label>
                <textarea
                    formControlName="intended_use"
                    rows="3"
                    placeholder="请描述您的具体使用用途..."
                ></textarea>
            </div>

            <div *ngIf="error" class="error">
                申请失败: {{ error }}
            </div>

            <div class="form-actions">
                <button 
                    type="submit" 
                    class="btn btn-primary" 
                    [disabled]="loading"
                >
                    {{ loading ? '申请中...' : '提交申请' }}
                </button>
                <button 
                    type="button" 
                    class="btn btn-secondary" 
                    (click)="onClose()"
                >
                    取消
                </button>
            </div>
        </form>
    </div>
</div>
```

---

## 通用CSS样式

```css
/* styles/common.css */

/* 基础样式 */
.loading {
    color: #666;
    text-align: center;
    padding: 20px;
    font-style: italic;
}

.error {
    color: #dc3545;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    padding: 10px;
    margin: 10px 0;
}

.success {
    color: #155724;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 4px;
    padding: 10px;
    margin: 10px 0;
}

.empty {
    text-align: center;
    color: #666;
    padding: 40px 20px;
    font-style: italic;
}

/* 按钮样式 */
.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: background-color 0.2s;
    margin: 5px;
}

.btn-primary {
    background-color: #007bff;
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background-color: #0056b3;
}

.btn-secondary {
    background-color: #6c757d;
    color: white;
}

.btn-secondary:hover:not(:disabled) {
    background-color: #545b62;
}

.btn-disabled {
    background-color: #e9ecef;
    color: #6c757d;
    cursor: not-allowed;
}

/* 产品卡片样式 */
.products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.product-card {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 20px;
    background-color: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.product-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.product-card.applied {
    opacity: 0.6;
    background-color: #f8f9fa;
}

.product-card h3 {
    margin-top: 0;
    margin-bottom: 10px;
    color: #333;
}

.product-card p {
    color: #666;
    margin-bottom: 15px;
    line-height: 1.4;
}

.trial-info {
    background-color: #e3f2fd;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 10px;
    font-size: 14px;
}

.features {
    margin-bottom: 15px;
}

.feature-tag {
    display: inline-block;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 12px;
    padding: 2px 8px;
    margin: 2px;
    font-size: 12px;
    color: #495057;
}

.actions {
    text-align: right;
}

/* 许可证列表样式 */
.licenses-header {
    margin-bottom: 20px;
}

.stats-card {
    display: flex;
    gap: 20px;
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
}

.stats-item {
    text-align: center;
    flex: 1;
}

.stats-number {
    display: block;
    font-size: 24px;
    font-weight: bold;
    color: #007bff;
}

.stats-label {
    display: block;
    font-size: 12px;
    color: #666;
    margin-top: 4px;
}

.filters {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.filters select {
    padding: 8px 12px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    background-color: white;
}

.licenses-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 20px;
}

.license-card {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 20px;
    background-color: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.license-card.active {
    border-left: 4px solid #28a745;
}

.license-card.pending {
    border-left: 4px solid #ffc107;
}

.license-card.expired {
    border-left: 4px solid #dc3545;
}

.license-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 15px;
}

.license-header h3 {
    margin: 0;
    color: #333;
    flex: 1;
}

.status-badge {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
}

.status-badge.active {
    background-color: #d4edda;
    color: #155724;
}

.status-badge.pending {
    background-color: #fff3cd;
    color: #856404;
}

.status-badge.expired {
    background-color: #f8d7da;
    color: #721c24;
}

.license-details {
    margin-bottom: 15px;
}

.detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f8f9fa;
}

.detail-row:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}

.detail-row .label {
    font-weight: 500;
    color: #495057;
    flex-shrink: 0;
    margin-right: 10px;
}

.detail-row .value {
    text-align: right;
    color: #212529;
    flex: 1;
}

.detail-row .value.warning {
    color: #dc3545;
    font-weight: bold;
}

.detail-row .value.monospace {
    font-family: 'Courier New', monospace;
    font-size: 13px;
}

.license-actions {
    text-align: center;
    padding-top: 10px;
    border-top: 1px solid #f8f9fa;
}

.status-indicator {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
}

.status-indicator.success {
    background-color: #d4edda;
    color: #155724;
}

.status-indicator.error {
    background-color: #f8d7da;
    color: #721c24;
}

/* 模态框样式 */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    background-color: white;
    border-radius: 8px;
    padding: 24px;
    width: 90%;
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.modal-content h3 {
    margin-top: 0;
    margin-bottom: 20px;
    color: #333;
}

.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #495057;
}

.form-group input,
.form-group textarea,
.form-group select {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 14px;
    box-sizing: border-box;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid #f8f9fa;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .products-grid,
    .licenses-grid {
        grid-template-columns: 1fr;
    }
    
    .stats-card {
        flex-direction: column;
        gap: 10px;
    }
    
    .stats-item {
        text-align: left;
    }
    
    .detail-row {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .detail-row .value {
        text-align: left;
        margin-top: 4px;
    }
    
    .license-header {
        flex-direction: column;
        gap: 10px;
    }
    
    .modal-content {
        width: 95%;
        margin: 20px;
    }
    
    .form-actions {
        flex-direction: column;
    }
    
    .filters {
        flex-direction: column;
    }
}
```

---

## 总结

本文档提供了Member试用许可证API在各种前端框架中的完整实现示例，包括：

1. **通用配置**: API客户端、认证管理、错误处理
2. **原生JavaScript**: 完整的HTML页面实现
3. **React**: 使用Hooks和现代React模式
4. **Vue.js**: 使用Composition API和现代Vue语法
5. **Angular**: 使用服务、组件和响应式表单

每个实现都包含了：
- 完整的API调用逻辑
- 错误处理和加载状态
- 用户友好的界面
- 响应式设计
- 最佳实践指导

开发者可以根据项目需要选择合适的框架实现，所有代码都经过精心设计，确保可维护性和扩展性。
