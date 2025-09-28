# JavaScript/TypeScript代码示例

## 🎯 代码示例概述

本文档提供许可证创建API的完整JavaScript/TypeScript实现代码，包括原生JavaScript、React、Vue.js、Angular等框架的具体实现。

## 📋 目录

1. [原生JavaScript实现](#1-原生javascript实现)
2. [TypeScript类型定义](#2-typescript类型定义)
3. [React实现](#3-react实现)
4. [Vue.js实现](#4-vuejs实现)
5. [Angular实现](#5-angular实现)
6. [Node.js后端集成](#6-nodejs后端集成)
7. [工具函数库](#7-工具函数库)
8. [测试代码](#8-测试代码)

## 1. 原生JavaScript实现

### 基础API客户端
```javascript
class LicenseAPIClient {
  constructor(config = {}) {
    this.baseUrl = config.baseUrl || '/api/v1/licenses/admin';
    this.tokenProvider = config.tokenProvider || (() => localStorage.getItem('auth_token'));
    this.onError = config.onError || console.error;
    this.onSuccess = config.onSuccess || console.log;
  }

  async createLicense(licenseData) {
    try {
      this.validateLicenseData(licenseData);
      
      const response = await fetch(`${this.baseUrl}/licenses/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.tokenProvider()}`
        },
        body: JSON.stringify(licenseData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      this.onSuccess('许可证创建成功', data);
      return data;
    } catch (error) {
      this.onError('许可证创建失败', error);
      throw error;
    }
  }

  validateLicenseData(data) {
    const required = ['plan', 'customer_info'];
    const customerRequired = ['name', 'email'];

    // 检查必需字段
    for (const field of required) {
      if (!data[field]) {
        throw new Error(`缺少必需字段: ${field}`);
      }
    }

    // 检查客户信息必需字段
    for (const field of customerRequired) {
      if (!data.customer_info[field]) {
        throw new Error(`客户信息缺少必需字段: ${field}`);
      }
    }

    // 验证邮箱格式
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.customer_info.email)) {
      throw new Error('客户邮箱格式不正确');
    }

    // 验证数值字段
    if (data.max_activations && (data.max_activations < 1 || !Number.isInteger(data.max_activations))) {
      throw new Error('最大激活数必须是大于0的整数');
    }

    if (data.validity_days && (data.validity_days < 1 || !Number.isInteger(data.validity_days))) {
      throw new Error('有效天数必须是大于0的整数');
    }
  }

  async getPlans() {
    const response = await fetch(`${this.baseUrl}/plans/`, {
      headers: {
        'Authorization': `Bearer ${this.tokenProvider()}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`获取方案列表失败: ${response.status}`);
    }
    
    return await response.json();
  }

  async getLicense(licenseId) {
    const response = await fetch(`${this.baseUrl}/licenses/${licenseId}/`, {
      headers: {
        'Authorization': `Bearer ${this.tokenProvider()}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`获取许可证失败: ${response.status}`);
    }
    
    return await response.json();
  }
}

// 使用示例
const apiClient = new LicenseAPIClient({
  baseUrl: '/api/v1/licenses/admin',
  tokenProvider: () => localStorage.getItem('jwt_token'),
  onSuccess: (message, data) => {
    console.log(message, data);
    showSuccessNotification(message);
  },
  onError: (message, error) => {
    console.error(message, error);
    showErrorNotification(message);
  }
});

// 创建许可证
const licenseData = {
  plan: 2,
  customer_info: {
    name: '张三',
    email: 'zhangsan@example.com',
    company: '示例公司'
  },
  max_activations: 5,
  validity_days: 365,
  notes: '标准企业许可证'
};

apiClient.createLicense(licenseData)
  .then(license => {
    console.log('创建成功:', license);
    // 处理成功逻辑
  })
  .catch(error => {
    console.error('创建失败:', error);
    // 处理错误逻辑
  });
```

### 表单处理工具
```javascript
class LicenseFormManager {
  constructor(formElement, apiClient) {
    this.form = formElement;
    this.api = apiClient;
    this.validators = new Map();
    this.setupEventListeners();
  }

  setupEventListeners() {
    this.form.addEventListener('submit', this.handleSubmit.bind(this));
    
    // 实时验证
    const inputs = this.form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      input.addEventListener('blur', this.validateField.bind(this, input));
      input.addEventListener('input', this.clearFieldError.bind(this, input));
    });
  }

  async handleSubmit(event) {
    event.preventDefault();
    
    const formData = this.getFormData();
    
    if (!this.validateForm(formData)) {
      return;
    }

    this.setLoading(true);
    
    try {
      const licenseData = this.formatLicenseData(formData);
      const license = await this.api.createLicense(licenseData);
      
      this.handleSuccess(license);
    } catch (error) {
      this.handleError(error);
    } finally {
      this.setLoading(false);
    }
  }

  getFormData() {
    const formData = new FormData(this.form);
    const data = {};
    
    for (const [key, value] of formData.entries()) {
      data[key] = value;
    }
    
    return data;
  }

  formatLicenseData(formData) {
    return {
      plan: parseInt(formData.plan),
      customer_info: {
        name: formData.customer_name,
        email: formData.customer_email,
        company: formData.customer_company || '',
        phone: formData.customer_phone || '',
        address: formData.customer_address || '',
        contact_person: formData.contact_person || ''
      },
      max_activations: formData.max_activations ? parseInt(formData.max_activations) : undefined,
      validity_days: formData.validity_days ? parseInt(formData.validity_days) : undefined,
      notes: formData.notes || ''
    };
  }

  validateForm(formData) {
    let isValid = true;
    
    // 验证必需字段
    const requiredFields = ['plan', 'customer_name', 'customer_email'];
    requiredFields.forEach(field => {
      if (!formData[field] || formData[field].trim() === '') {
        this.showFieldError(field, '此字段为必填项');
        isValid = false;
      }
    });
    
    // 验证邮箱
    if (formData.customer_email && !this.isValidEmail(formData.customer_email)) {
      this.showFieldError('customer_email', '请输入有效的邮箱地址');
      isValid = false;
    }
    
    return isValid;
  }

  validateField(input) {
    const value = input.value.trim();
    const name = input.name;
    
    if (input.required && !value) {
      this.showFieldError(name, '此字段为必填项');
      return false;
    }
    
    if (name === 'customer_email' && value && !this.isValidEmail(value)) {
      this.showFieldError(name, '请输入有效的邮箱地址');
      return false;
    }
    
    this.clearFieldError(input);
    return true;
  }

  isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  }

  showFieldError(fieldName, message) {
    const field = this.form.querySelector(`[name="${fieldName}"]`);
    if (!field) return;
    
    field.classList.add('error');
    
    let errorElement = field.parentNode.querySelector('.field-error');
    if (!errorElement) {
      errorElement = document.createElement('div');
      errorElement.className = 'field-error';
      field.parentNode.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
  }

  clearFieldError(input) {
    input.classList.remove('error');
    const errorElement = input.parentNode.querySelector('.field-error');
    if (errorElement) {
      errorElement.remove();
    }
  }

  setLoading(loading) {
    const submitButton = this.form.querySelector('button[type="submit"]');
    const inputs = this.form.querySelectorAll('input, select, textarea, button');
    
    if (loading) {
      submitButton.textContent = '创建中...';
      inputs.forEach(input => input.disabled = true);
    } else {
      submitButton.textContent = '创建许可证';
      inputs.forEach(input => input.disabled = false);
    }
  }

  handleSuccess(license) {
    // 显示成功消息
    this.showMessage('success', `许可证创建成功！许可证密钥：${license.license_key}`);
    
    // 重置表单
    this.form.reset();
    
    // 触发自定义事件
    this.form.dispatchEvent(new CustomEvent('licenseCreated', {
      detail: { license }
    }));
  }

  handleError(error) {
    if (error.status === 400 && error.data && error.data.errors) {
      // 处理字段验证错误
      this.handleValidationErrors(error.data.errors);
    } else {
      // 显示通用错误消息
      this.showMessage('error', '创建许可证失败，请稍后重试');
    }
  }

  handleValidationErrors(errors) {
    const processErrors = (errorObj, prefix = '') => {
      for (const [field, messages] of Object.entries(errorObj)) {
        const fieldName = prefix ? `${prefix}_${field}` : field;
        
        if (Array.isArray(messages)) {
          this.showFieldError(fieldName, messages.join(', '));
        } else if (typeof messages === 'object') {
          processErrors(messages, fieldName);
        }
      }
    };
    
    processErrors(errors);
  }

  showMessage(type, message) {
    // 实现消息显示逻辑
    const messageElement = document.createElement('div');
    messageElement.className = `message message-${type}`;
    messageElement.textContent = message;
    
    this.form.parentNode.insertBefore(messageElement, this.form);
    
    setTimeout(() => {
      messageElement.remove();
    }, 5000);
  }
}

// 使用示例
const form = document.getElementById('license-form');
const apiClient = new LicenseAPIClient();
const formManager = new LicenseFormManager(form, apiClient);

// 监听许可证创建成功事件
form.addEventListener('licenseCreated', (event) => {
  const license = event.detail.license;
  console.log('新许可证创建:', license);
  
  // 可以在这里添加其他处理逻辑
  // 比如跳转到许可证详情页面
  // window.location.href = `/licenses/${license.id}`;
});
```

## 2. TypeScript类型定义

### 完整类型定义
```typescript
// 许可证相关类型定义
export interface CustomerInfo {
  name: string;
  email: string;
  company?: string;
  phone?: string;
  address?: string;
  contact_person?: string;
  department?: string;
}

export interface LicenseCreateRequest {
  plan: number;
  customer_info: CustomerInfo;
  tenant?: number;
  max_activations?: number;
  validity_days?: number;
  notes?: string;
}

export interface LicenseResponse {
  id: number;
  product: number;
  product_name: string;
  plan: number;
  plan_name: string;
  tenant: number;
  tenant_name: string;
  license_key: string;
  customer_name: string;
  customer_email: string;
  max_activations: number;
  current_activations: number;
  issued_at: string;
  expires_at: string;
  last_verified_at: string | null;
  status: 'active' | 'inactive' | 'expired' | 'revoked';
  machine_bindings_count: number;
  days_until_expiry: number;
  notes: string;
  machine_bindings: MachineBinding[];
  recent_activations: Activation[];
  usage_stats: UsageStats;
  metadata?: Record<string, any>;
}

export interface MachineBinding {
  id: number;
  machine_id: string;
  bound_at: string;
  last_seen_at: string;
  status: 'active' | 'inactive';
}

export interface Activation {
  id: number;
  activated_at: string;
  activation_type: string;
  result: 'success' | 'failed';
  ip_address: string;
}

export interface UsageStats {
  total_usage_logs: number;
  recent_usage_logs: number;
}

export interface LicensePlan {
  id: number;
  name: string;
  code: string;
  plan_type: string;
  default_max_activations: number;
  default_validity_days: number;
  price: string;
  currency: string;
  description: string;
  features: Record<string, any>;
  status: 'active' | 'inactive';
}

// API错误类型
export interface APIError {
  detail: string;
  code?: string;
  errors?: Record<string, string[] | Record<string, string[]>>;
}

// API响应类型
export interface APIResponse<T> {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: T[];
}

// 配置类型
export interface APIClientConfig {
  baseUrl?: string;
  tokenProvider?: () => string | null;
  onError?: (message: string, error: any) => void;
  onSuccess?: (message: string, data: any) => void;
  timeout?: number;
  retryConfig?: RetryConfig;
}

export interface RetryConfig {
  maxRetries: number;
  backoffMultiplier: number;
  baseDelay: number;
}

// TypeScript API客户端实现
export class TypedLicenseAPIClient {
  private config: Required<APIClientConfig>;

  constructor(config: APIClientConfig = {}) {
    this.config = {
      baseUrl: config.baseUrl || '/api/v1/licenses/admin',
      tokenProvider: config.tokenProvider || (() => localStorage.getItem('auth_token')),
      onError: config.onError || console.error,
      onSuccess: config.onSuccess || console.log,
      timeout: config.timeout || 30000,
      retryConfig: config.retryConfig || {
        maxRetries: 3,
        backoffMultiplier: 2,
        baseDelay: 1000
      }
    };
  }

  async createLicense(data: LicenseCreateRequest): Promise<LicenseResponse> {
    this.validateCreateRequest(data);
    
    const response = await this.makeRequest<LicenseResponse>('/licenses/', {
      method: 'POST',
      body: JSON.stringify(data)
    });

    this.config.onSuccess('许可证创建成功', response);
    return response;
  }

  async getPlans(): Promise<APIResponse<LicensePlan>> {
    return this.makeRequest<APIResponse<LicensePlan>>('/plans/');
  }

  async getLicense(id: number): Promise<LicenseResponse> {
    return this.makeRequest<LicenseResponse>(`/licenses/${id}/`);
  }

  private validateCreateRequest(data: LicenseCreateRequest): void {
    if (!data.plan || typeof data.plan !== 'number') {
      throw new Error('plan字段是必需的，且必须是数字类型');
    }

    if (!data.customer_info) {
      throw new Error('customer_info字段是必需的');
    }

    if (!data.customer_info.name || data.customer_info.name.trim() === '') {
      throw new Error('客户姓名是必需的');
    }

    if (!data.customer_info.email || !this.isValidEmail(data.customer_info.email)) {
      throw new Error('请提供有效的客户邮箱地址');
    }

    if (data.max_activations !== undefined && (data.max_activations < 1 || !Number.isInteger(data.max_activations))) {
      throw new Error('max_activations必须是大于0的整数');
    }

    if (data.validity_days !== undefined && (data.validity_days < 1 || !Number.isInteger(data.validity_days))) {
      throw new Error('validity_days必须是大于0的整数');
    }
  }

  private isValidEmail(email: string): boolean {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const token = this.config.tokenProvider();
    
    if (!token) {
      throw new Error('认证令牌不存在，请先登录');
    }

    const requestOptions: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
      }
    };

    let lastError: Error;
    
    for (let attempt = 0; attempt < this.config.retryConfig.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
        
        const response = await fetch(url, {
          ...requestOptions,
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
          const errorData: APIError = await response.json().catch(() => ({}));
          const error = new Error(errorData.detail || `HTTP ${response.status}`);
          (error as any).status = response.status;
          (error as any).data = errorData;
          throw error;
        }

        return await response.json();
      } catch (error) {
        lastError = error as Error;
        
        // 判断是否应该重试
        if (!this.shouldRetry(error as any, attempt)) {
          break;
        }
        
        // 等待后重试
        const delay = this.calculateDelay(attempt);
        await this.sleep(delay);
      }
    }
    
    this.config.onError('请求失败', lastError!);
    throw lastError!;
  }

  private shouldRetry(error: any, attempt: number): boolean {
    if (attempt >= this.config.retryConfig.maxRetries - 1) {
      return false;
    }
    
    // 网络错误重试
    if (error.name === 'AbortError' || !error.status) {
      return true;
    }
    
    // 服务器错误重试
    if (error.status >= 500) {
      return true;
    }
    
    return false;
  }

  private calculateDelay(attempt: number): number {
    return this.config.retryConfig.baseDelay * 
           Math.pow(this.config.retryConfig.backoffMultiplier, attempt);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// 使用示例
const typedClient = new TypedLicenseAPIClient({
  baseUrl: '/api/v1/licenses/admin',
  tokenProvider: () => sessionStorage.getItem('jwt_token'),
  onError: (message: string, error: any) => {
    console.error(`[License API] ${message}:`, error);
  },
  onSuccess: (message: string, data: any) => {
    console.log(`[License API] ${message}:`, data);
  }
});

// TypeScript中的使用示例
async function createEnterpriseQuote(): Promise<void> {
  try {
    const licenseData: LicenseCreateRequest = {
      plan: 3,
      customer_info: {
        name: '大型企业集团',
        email: 'admin@enterprise.com',
        company: '大型企业集团有限公司',
        phone: '+86-10-88888888',
        contact_person: 'IT总监'
      },
      max_activations: 100,
      validity_days: 365,
      notes: '企业年度许可证合同'
    };

    const license: LicenseResponse = await typedClient.createLicense(licenseData);
    
    console.log('企业许可证创建成功:', {
      id: license.id,
      key: license.license_key,
      expiry: license.expires_at,
      maxActivations: license.max_activations
    });
  } catch (error) {
    console.error('创建企业许可证失败:', error);
  }
}
```

## 3. React实现

### React Hooks实现
```tsx
import React, { useState, useEffect, useCallback } from 'react';
import { TypedLicenseAPIClient, LicenseCreateRequest, LicenseResponse, LicensePlan } from './types';

// 自定义Hook：许可证API
export function useLicenseAPI() {
  const [apiClient] = useState(() => new TypedLicenseAPIClient({
    onError: (message, error) => {
      console.error(message, error);
    }
  }));

  const createLicense = useCallback(async (data: LicenseCreateRequest): Promise<LicenseResponse> => {
    return await apiClient.createLicense(data);
  }, [apiClient]);

  const getPlans = useCallback(async () => {
    const response = await apiClient.getPlans();
    return response.results || [];
  }, [apiClient]);

  return {
    createLicense,
    getPlans
  };
}

// 许可证创建表单组件
interface LicenseFormData {
  plan: string;
  customerName: string;
  customerEmail: string;
  customerCompany: string;
  customerPhone: string;
  maxActivations: string;
  validityDays: string;
  notes: string;
}

export const CreateLicenseForm: React.FC = () => {
  const { createLicense, getPlans } = useLicenseAPI();
  const [plans, setPlans] = useState<LicensePlan[]>([]);
  const [formData, setFormData] = useState<LicenseFormData>({
    plan: '',
    customerName: '',
    customerEmail: '',
    customerCompany: '',
    customerPhone: '',
    maxActivations: '',
    validityDays: '',
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState<LicenseResponse | null>(null);

  // 加载许可证方案
  useEffect(() => {
    const loadPlans = async () => {
      try {
        const planList = await getPlans();
        setPlans(planList);
      } catch (error) {
        console.error('加载方案失败:', error);
      }
    };
    
    loadPlans();
  }, [getPlans]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // 清除字段错误
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.plan) {
      newErrors.plan = '请选择许可证方案';
    }
    
    if (!formData.customerName.trim()) {
      newErrors.customerName = '请输入客户姓名';
    }
    
    if (!formData.customerEmail.trim()) {
      newErrors.customerEmail = '请输入客户邮箱';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.customerEmail)) {
      newErrors.customerEmail = '请输入有效的邮箱地址';
    }
    
    if (formData.maxActivations && (isNaN(Number(formData.maxActivations)) || Number(formData.maxActivations) < 1)) {
      newErrors.maxActivations = '最大激活数必须是大于0的整数';
    }
    
    if (formData.validityDays && (isNaN(Number(formData.validityDays)) || Number(formData.validityDays) < 1)) {
      newErrors.validityDays = '有效天数必须是大于0的整数';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setSuccess(null);
    
    try {
      const licenseData: LicenseCreateRequest = {
        plan: parseInt(formData.plan),
        customer_info: {
          name: formData.customerName,
          email: formData.customerEmail,
          company: formData.customerCompany,
          phone: formData.customerPhone
        },
        max_activations: formData.maxActivations ? parseInt(formData.maxActivations) : undefined,
        validity_days: formData.validityDays ? parseInt(formData.validityDays) : undefined,
        notes: formData.notes
      };

      const license = await createLicense(licenseData);
      setSuccess(license);
      
      // 重置表单
      setFormData({
        plan: '',
        customerName: '',
        customerEmail: '',
        customerCompany: '',
        customerPhone: '',
        maxActivations: '',
        validityDays: '',
        notes: ''
      });
    } catch (error: any) {
      if (error.status === 400 && error.data?.errors) {
        handleValidationErrors(error.data.errors);
      } else {
        setErrors({ general: '创建许可证失败，请稍后重试' });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleValidationErrors = (apiErrors: any) => {
    const newErrors: Record<string, string> = {};
    
    const processErrors = (errorObj: any, prefix = '') => {
      for (const [field, messages] of Object.entries(errorObj)) {
        const fieldName = prefix ? `${prefix}.${field}` : field;
        
        if (Array.isArray(messages)) {
          newErrors[fieldName] = (messages as string[]).join(', ');
        } else if (typeof messages === 'object') {
          processErrors(messages, fieldName);
        }
      }
    };
    
    processErrors(apiErrors);
    setErrors(newErrors);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">创建许可证</h2>
      
      {success && (
        <div className="mb-6 p-4 bg-green-100 border border-green-400 rounded">
          <h3 className="font-bold text-green-800">许可证创建成功！</h3>
          <p className="text-green-700">
            许可证密钥：<code className="bg-green-200 px-2 py-1 rounded">{success.license_key}</code>
          </p>
          <p className="text-green-700 text-sm mt-2">
            客户：{success.customer_name} | 有效期至：{new Date(success.expires_at).toLocaleDateString()}
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {errors.general && (
          <div className="p-4 bg-red-100 border border-red-400 rounded text-red-700">
            {errors.general}
          </div>
        )}
        
        <div>
          <label className="block text-sm font-medium mb-2">
            许可证方案 <span className="text-red-500">*</span>
          </label>
          <select
            name="plan"
            value={formData.plan}
            onChange={handleInputChange}
            className={`w-full p-3 border rounded-lg ${errors.plan ? 'border-red-500' : 'border-gray-300'}`}
          >
            <option value="">请选择方案</option>
            {plans.map(plan => (
              <option key={plan.id} value={plan.id}>
                {plan.name} - ¥{plan.price} ({plan.default_max_activations}设备, {plan.default_validity_days}天)
              </option>
            ))}
          </select>
          {errors.plan && <p className="text-red-500 text-sm mt-1">{errors.plan}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            客户姓名 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="customerName"
            value={formData.customerName}
            onChange={handleInputChange}
            placeholder="请输入客户姓名"
            className={`w-full p-3 border rounded-lg ${errors.customerName ? 'border-red-500' : 'border-gray-300'}`}
          />
          {errors.customerName && <p className="text-red-500 text-sm mt-1">{errors.customerName}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            客户邮箱 <span className="text-red-500">*</span>
          </label>
          <input
            type="email"
            name="customerEmail"
            value={formData.customerEmail}
            onChange={handleInputChange}
            placeholder="请输入客户邮箱"
            className={`w-full p-3 border rounded-lg ${errors.customerEmail ? 'border-red-500' : 'border-gray-300'}`}
          />
          {errors.customerEmail && <p className="text-red-500 text-sm mt-1">{errors.customerEmail}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">公司名称</label>
          <input
            type="text"
            name="customerCompany"
            value={formData.customerCompany}
            onChange={handleInputChange}
            placeholder="请输入公司名称（可选）"
            className="w-full p-3 border border-gray-300 rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">联系电话</label>
          <input
            type="tel"
            name="customerPhone"
            value={formData.customerPhone}
            onChange={handleInputChange}
            placeholder="请输入联系电话（可选）"
            className="w-full p-3 border border-gray-300 rounded-lg"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">最大激活数</label>
            <input
              type="number"
              name="maxActivations"
              value={formData.maxActivations}
              onChange={handleInputChange}
              placeholder="留空使用方案默认值"
              min="1"
              className={`w-full p-3 border rounded-lg ${errors.maxActivations ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.maxActivations && <p className="text-red-500 text-sm mt-1">{errors.maxActivations}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">有效天数</label>
            <input
              type="number"
              name="validityDays"
              value={formData.validityDays}
              onChange={handleInputChange}
              placeholder="留空使用方案默认值"
              min="1"
              className={`w-full p-3 border rounded-lg ${errors.validityDays ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.validityDays && <p className="text-red-500 text-sm mt-1">{errors.validityDays}</p>}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">备注信息</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleInputChange}
            placeholder="请输入备注信息（可选）"
            rows={3}
            className="w-full p-3 border border-gray-300 rounded-lg"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-3 px-4 rounded-lg text-white font-medium ${
            loading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? '创建中...' : '创建许可证'}
        </button>
      </form>
    </div>
  );
};

export default CreateLicenseForm;
```

### React Context Provider
```tsx
import React, { createContext, useContext, useState, ReactNode } from 'react';
import { TypedLicenseAPIClient, LicenseResponse } from './types';

interface LicenseContextType {
  apiClient: TypedLicenseAPIClient;
  licenses: LicenseResponse[];
  loading: boolean;
  createLicense: (data: any) => Promise<LicenseResponse>;
  refreshLicenses: () => Promise<void>;
}

const LicenseContext = createContext<LicenseContextType | undefined>(undefined);

export const LicenseProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [apiClient] = useState(() => new TypedLicenseAPIClient());
  const [licenses, setLicenses] = useState<LicenseResponse[]>([]);
  const [loading, setLoading] = useState(false);

  const createLicense = async (data: any): Promise<LicenseResponse> => {
    setLoading(true);
    try {
      const license = await apiClient.createLicense(data);
      setLicenses(prev => [license, ...prev]);
      return license;
    } finally {
      setLoading(false);
    }
  };

  const refreshLicenses = async (): Promise<void> => {
    setLoading(true);
    try {
      // 假设有获取许可证列表的方法
      // const response = await apiClient.getLicenses();
      // setLicenses(response.results || []);
    } finally {
      setLoading(false);
    }
  };

  const value: LicenseContextType = {
    apiClient,
    licenses,
    loading,
    createLicense,
    refreshLicenses
  };

  return (
    <LicenseContext.Provider value={value}>
      {children}
    </LicenseContext.Provider>
  );
};

export const useLicenseContext = (): LicenseContextType => {
  const context = useContext(LicenseContext);
  if (!context) {
    throw new Error('useLicenseContext must be used within a LicenseProvider');
  }
  return context;
};
```

## 4. Vue.js实现

### Vue 3 Composition API实现
```vue
<template>
  <div class="max-w-2xl mx-auto p-6">
    <h2 class="text-2xl font-bold mb-6">创建许可证</h2>
    
    <div v-if="success" class="mb-6 p-4 bg-green-100 border border-green-400 rounded">
      <h3 class="font-bold text-green-800">许可证创建成功！</h3>
      <p class="text-green-700">
        许可证密钥：<code class="bg-green-200 px-2 py-1 rounded">{{ success.license_key }}</code>
      </p>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-6">
      <div v-if="errors.general" class="p-4 bg-red-100 border border-red-400 rounded text-red-700">
        {{ errors.general }}
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-2">
          许可证方案 <span class="text-red-500">*</span>
        </label>
        <select
          v-model="form.plan"
          :class="['w-full p-3 border rounded-lg', errors.plan ? 'border-red-500' : 'border-gray-300']"
        >
          <option value="">请选择方案</option>
          <option v-for="plan in plans" :key="plan.id" :value="plan.id">
            {{ plan.name }} - ¥{{ plan.price }} ({{ plan.default_max_activations }}设备, {{ plan.default_validity_days }}天)
          </option>
        </select>
        <p v-if="errors.plan" class="text-red-500 text-sm mt-1">{{ errors.plan }}</p>
      </div>

      <div>
        <label class="block text-sm font-medium mb-2">
          客户姓名 <span class="text-red-500">*</span>
        </label>
        <input
          v-model="form.customer_info.name"
          type="text"
          placeholder="请输入客户姓名"
          :class="['w-full p-3 border rounded-lg', errors['customer_info.name'] ? 'border-red-500' : 'border-gray-300']"
        />
        <p v-if="errors['customer_info.name']" class="text-red-500 text-sm mt-1">
          {{ errors['customer_info.name'] }}
        </p>
      </div>

      <div>
        <label class="block text-sm font-medium mb-2">
          客户邮箱 <span class="text-red-500">*</span>
        </label>
        <input
          v-model="form.customer_info.email"
          type="email"
          placeholder="请输入客户邮箱"
          :class="['w-full p-3 border rounded-lg', errors['customer_info.email'] ? 'border-red-500' : 'border-gray-300']"
        />
        <p v-if="errors['customer_info.email']" class="text-red-500 text-sm mt-1">
          {{ errors['customer_info.email'] }}
        </p>
      </div>

      <div>
        <label class="block text-sm font-medium mb-2">公司名称</label>
        <input
          v-model="form.customer_info.company"
          type="text"
          placeholder="请输入公司名称（可选）"
          class="w-full p-3 border border-gray-300 rounded-lg"
        />
      </div>

      <div>
        <label class="block text-sm font-medium mb-2">联系电话</label>
        <input
          v-model="form.customer_info.phone"
          type="tel"
          placeholder="请输入联系电话（可选）"
          class="w-full p-3 border border-gray-300 rounded-lg"
        />
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium mb-2">最大激活数</label>
          <input
            v-model.number="form.max_activations"
            type="number"
            placeholder="留空使用方案默认值"
            min="1"
            :class="['w-full p-3 border rounded-lg', errors.max_activations ? 'border-red-500' : 'border-gray-300']"
          />
          <p v-if="errors.max_activations" class="text-red-500 text-sm mt-1">
            {{ errors.max_activations }}
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium mb-2">有效天数</label>
          <input
            v-model.number="form.validity_days"
            type="number"
            placeholder="留空使用方案默认值"
            min="1"
            :class="['w-full p-3 border rounded-lg', errors.validity_days ? 'border-red-500' : 'border-gray-300']"
          />
          <p v-if="errors.validity_days" class="text-red-500 text-sm mt-1">
            {{ errors.validity_days }}
          </p>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium mb-2">备注信息</label>
        <textarea
          v-model="form.notes"
          placeholder="请输入备注信息（可选）"
          rows="3"
          class="w-full p-3 border border-gray-300 rounded-lg"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        :class="[
          'w-full py-3 px-4 rounded-lg text-white font-medium',
          loading 
            ? 'bg-gray-400 cursor-not-allowed' 
            : 'bg-blue-600 hover:bg-blue-700'
        ]"
      >
        {{ loading ? '创建中...' : '创建许可证' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue';
import { TypedLicenseAPIClient, type LicenseCreateRequest, type LicenseResponse, type LicensePlan } from './types';

// API客户端
const apiClient = new TypedLicenseAPIClient();

// 响应式数据
const plans = ref<LicensePlan[]>([]);
const loading = ref(false);
const success = ref<LicenseResponse | null>(null);
const errors = ref<Record<string, string>>({});

const form = reactive<LicenseCreateRequest>({
  plan: 0,
  customer_info: {
    name: '',
    email: '',
    company: '',
    phone: ''
  },
  max_activations: undefined,
  validity_days: undefined,
  notes: ''
});

// 加载许可证方案
const loadPlans = async () => {
  try {
    const response = await apiClient.getPlans();
    plans.value = response.results || [];
  } catch (error) {
    console.error('加载方案失败:', error);
  }
};

// 验证表单
const validateForm = (): boolean => {
  const newErrors: Record<string, string> = {};
  
  if (!form.plan) {
    newErrors.plan = '请选择许可证方案';
  }
  
  if (!form.customer_info.name?.trim()) {
    newErrors['customer_info.name'] = '请输入客户姓名';
  }
  
  if (!form.customer_info.email?.trim()) {
    newErrors['customer_info.email'] = '请输入客户邮箱';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.customer_info.email)) {
    newErrors['customer_info.email'] = '请输入有效的邮箱地址';
  }
  
  if (form.max_activations && form.max_activations < 1) {
    newErrors.max_activations = '最大激活数必须大于0';
  }
  
  if (form.validity_days && form.validity_days < 1) {
    newErrors.validity_days = '有效天数必须大于0';
  }
  
  errors.value = newErrors;
  return Object.keys(newErrors).length === 0;
};

// 处理表单提交
const handleSubmit = async () => {
  if (!validateForm()) {
    return;
  }

  loading.value = true;
  success.value = null;
  
  try {
    const license = await apiClient.createLicense(form);
    success.value = license;
    
    // 重置表单
    Object.assign(form, {
      plan: 0,
      customer_info: {
        name: '',
        email: '',
        company: '',
        phone: ''
      },
      max_activations: undefined,
      validity_days: undefined,
      notes: ''
    });
  } catch (error: any) {
    if (error.status === 400 && error.data?.errors) {
      handleValidationErrors(error.data.errors);
    } else {
      errors.value = { general: '创建许可证失败，请稍后重试' };
    }
  } finally {
    loading.value = false;
  }
};

// 处理API验证错误
const handleValidationErrors = (apiErrors: any) => {
  const newErrors: Record<string, string> = {};
  
  const processErrors = (errorObj: any, prefix = '') => {
    for (const [field, messages] of Object.entries(errorObj)) {
      const fieldName = prefix ? `${prefix}.${field}` : field;
      
      if (Array.isArray(messages)) {
        newErrors[fieldName] = (messages as string[]).join(', ');
      } else if (typeof messages === 'object') {
        processErrors(messages, fieldName);
      }
    }
  };
  
  processErrors(apiErrors);
  errors.value = newErrors;
};

// 清除字段错误
watch(() => form.plan, () => {
  if (errors.value.plan) {
    delete errors.value.plan;
  }
});

watch(() => form.customer_info.name, () => {
  if (errors.value['customer_info.name']) {
    delete errors.value['customer_info.name'];
  }
});

watch(() => form.customer_info.email, () => {
  if (errors.value['customer_info.email']) {
    delete errors.value['customer_info.email'];
  }
});

// 组件挂载时加载数据
onMounted(() => {
  loadPlans();
});
</script>
```

### Vue 3 Composable
```typescript
// composables/useLicense.ts
import { ref, reactive } from 'vue';
import { TypedLicenseAPIClient, type LicenseCreateRequest, type LicenseResponse, type LicensePlan } from '../types';

export function useLicense() {
  const apiClient = new TypedLicenseAPIClient();
  const loading = ref(false);
  const error = ref<string | null>(null);

  const createLicense = async (data: LicenseCreateRequest): Promise<LicenseResponse | null> => {
    loading.value = true;
    error.value = null;
    
    try {
      const license = await apiClient.createLicense(data);
      return license;
    } catch (err: any) {
      error.value = err.message || '创建许可证失败';
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const getPlans = async (): Promise<LicensePlan[]> => {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await apiClient.getPlans();
      return response.results || [];
    } catch (err: any) {
      error.value = err.message || '获取方案列表失败';
      return [];
    } finally {
      loading.value = false;
    }
  };

  return {
    loading: readonly(loading),
    error: readonly(error),
    createLicense,
    getPlans
  };
}
```

## 5. Angular实现

### Angular服务
```typescript
import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, retry } from 'rxjs/operators';
import { 
  LicenseCreateRequest, 
  LicenseResponse, 
  LicensePlan, 
  APIResponse 
} from './types';

@Injectable({
  providedIn: 'root'
})
export class LicenseService {
  private readonly baseUrl = '/api/v1/licenses/admin';

  constructor(private http: HttpClient) {}

  createLicense(data: LicenseCreateRequest): Observable<LicenseResponse> {
    return this.http.post<LicenseResponse>(`${this.baseUrl}/licenses/`, data)
      .pipe(
        retry(2),
        catchError(this.handleError)
      );
  }

  getPlans(): Observable<APIResponse<LicensePlan>> {
    return this.http.get<APIResponse<LicensePlan>>(`${this.baseUrl}/plans/`)
      .pipe(
        retry(2),
        catchError(this.handleError)
      );
  }

  getLicense(id: number): Observable<LicenseResponse> {
    return this.http.get<LicenseResponse>(`${this.baseUrl}/licenses/${id}/`)
      .pipe(
        retry(2),
        catchError(this.handleError)
      );
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = '未知错误';
    
    if (error.error instanceof ErrorEvent) {
      // 客户端错误
      errorMessage = `错误: ${error.error.message}`;
    } else {
      // 服务器端错误
      errorMessage = error.error?.detail || `HTTP ${error.status}: ${error.statusText}`;
    }
    
    console.error('License API Error:', error);
    return throwError(() => new Error(errorMessage));
  }
}
```

### Angular组件
```typescript
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { LicenseService } from './license.service';
import { LicensePlan, LicenseResponse } from './types';

@Component({
  selector: 'app-create-license',
  template: `
    <div class="max-w-2xl mx-auto p-6">
      <h2 class="text-2xl font-bold mb-6">创建许可证</h2>
      
      <div *ngIf="success" class="mb-6 p-4 bg-green-100 border border-green-400 rounded">
        <h3 class="font-bold text-green-800">许可证创建成功！</h3>
        <p class="text-green-700">
          许可证密钥：<code class="bg-green-200 px-2 py-1 rounded">{{ success.license_key }}</code>
        </p>
      </div>

      <form [formGroup]="licenseForm" (ngSubmit)="onSubmit()" class="space-y-6">
        <div *ngIf="generalError" class="p-4 bg-red-100 border border-red-400 rounded text-red-700">
          {{ generalError }}
        </div>

        <div>
          <label class="block text-sm font-medium mb-2">
            许可证方案 <span class="text-red-500">*</span>
          </label>
          <select 
            formControlName="plan"
            [class]="getFieldClass('plan')"
          >
            <option value="">请选择方案</option>
            <option *ngFor="let plan of plans" [value]="plan.id">
              {{ plan.name }} - ¥{{ plan.price }} ({{ plan.default_max_activations }}设备, {{ plan.default_validity_days }}天)
            </option>
          </select>
          <div *ngIf="getFieldError('plan')" class="text-red-500 text-sm mt-1">
            {{ getFieldError('plan') }}
          </div>
        </div>

        <div formGroupName="customer_info">
          <div>
            <label class="block text-sm font-medium mb-2">
              客户姓名 <span class="text-red-500">*</span>
            </label>
            <input 
              type="text" 
              formControlName="name"
              placeholder="请输入客户姓名"
              [class]="getFieldClass('customer_info.name')"
            />
            <div *ngIf="getFieldError('customer_info.name')" class="text-red-500 text-sm mt-1">
              {{ getFieldError('customer_info.name') }}
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-2">
              客户邮箱 <span class="text-red-500">*</span>
            </label>
            <input 
              type="email" 
              formControlName="email"
              placeholder="请输入客户邮箱"
              [class]="getFieldClass('customer_info.email')"
            />
            <div *ngIf="getFieldError('customer_info.email')" class="text-red-500 text-sm mt-1">
              {{ getFieldError('customer_info.email') }}
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-2">公司名称</label>
            <input 
              type="text" 
              formControlName="company"
              placeholder="请输入公司名称（可选）"
              class="w-full p-3 border border-gray-300 rounded-lg"
            />
          </div>

          <div>
            <label class="block text-sm font-medium mb-2">联系电话</label>
            <input 
              type="tel" 
              formControlName="phone"
              placeholder="请输入联系电话（可选）"
              class="w-full p-3 border border-gray-300 rounded-lg"
            />
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-2">最大激活数</label>
            <input 
              type="number" 
              formControlName="max_activations"
              placeholder="留空使用方案默认值"
              min="1"
              [class]="getFieldClass('max_activations')"
            />
            <div *ngIf="getFieldError('max_activations')" class="text-red-500 text-sm mt-1">
              {{ getFieldError('max_activations') }}
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-2">有效天数</label>
            <input 
              type="number" 
              formControlName="validity_days"
              placeholder="留空使用方案默认值"
              min="1"
              [class]="getFieldClass('validity_days')"
            />
            <div *ngIf="getFieldError('validity_days')" class="text-red-500 text-sm mt-1">
              {{ getFieldError('validity_days') }}
            </div>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium mb-2">备注信息</label>
          <textarea 
            formControlName="notes"
            placeholder="请输入备注信息（可选）"
            rows="3"
            class="w-full p-3 border border-gray-300 rounded-lg"
          ></textarea>
        </div>

        <button 
          type="submit" 
          [disabled]="loading || licenseForm.invalid"
          [class]="getSubmitButtonClass()"
        >
          {{ loading ? '创建中...' : '创建许可证' }}
        </button>
      </form>
    </div>
  `
})
export class CreateLicenseComponent implements OnInit {
  licenseForm: FormGroup;
  plans: LicensePlan[] = [];
  loading = false;
  success: LicenseResponse | null = null;
  generalError = '';

  constructor(
    private fb: FormBuilder,
    private licenseService: LicenseService
  ) {
    this.licenseForm = this.createForm();
  }

  ngOnInit() {
    this.loadPlans();
  }

  private createForm(): FormGroup {
    return this.fb.group({
      plan: ['', Validators.required],
      customer_info: this.fb.group({
        name: ['', Validators.required],
        email: ['', [Validators.required, Validators.email]],
        company: [''],
        phone: ['']
      }),
      max_activations: ['', [Validators.min(1)]],
      validity_days: ['', [Validators.min(1)]],
      notes: ['']
    });
  }

  private loadPlans() {
    this.licenseService.getPlans().subscribe({
      next: (response) => {
        this.plans = response.results || [];
      },
      error: (error) => {
        console.error('加载方案失败:', error);
      }
    });
  }

  onSubmit() {
    if (this.licenseForm.valid) {
      this.loading = true;
      this.success = null;
      this.generalError = '';

      const formValue = this.licenseForm.value;
      const licenseData = {
        ...formValue,
        plan: parseInt(formValue.plan),
        max_activations: formValue.max_activations ? parseInt(formValue.max_activations) : undefined,
        validity_days: formValue.validity_days ? parseInt(formValue.validity_days) : undefined
      };

      this.licenseService.createLicense(licenseData).subscribe({
        next: (license) => {
          this.success = license;
          this.licenseForm.reset();
          this.loading = false;
        },
        error: (error) => {
          this.generalError = error.message || '创建许可证失败';
          this.loading = false;
        }
      });
    }
  }

  getFieldClass(fieldName: string): string {
    const field = this.getFormControl(fieldName);
    const hasError = field?.invalid && field?.touched;
    return `w-full p-3 border rounded-lg ${hasError ? 'border-red-500' : 'border-gray-300'}`;
  }

  getFieldError(fieldName: string): string | null {
    const field = this.getFormControl(fieldName);
    if (field?.invalid && field?.touched) {
      const errors = field.errors;
      if (errors?.['required']) return '此字段为必填项';
      if (errors?.['email']) return '请输入有效的邮箱地址';
      if (errors?.['min']) return `值必须大于等于 ${errors['min'].min}`;
    }
    return null;
  }

  private getFormControl(fieldName: string) {
    const nameParts = fieldName.split('.');
    let control = this.licenseForm;
    
    for (const part of nameParts) {
      control = control.get(part);
      if (!control) break;
    }
    
    return control;
  }

  getSubmitButtonClass(): string {
    const isDisabled = this.loading || this.licenseForm.invalid;
    return `w-full py-3 px-4 rounded-lg text-white font-medium ${
      isDisabled 
        ? 'bg-gray-400 cursor-not-allowed' 
        : 'bg-blue-600 hover:bg-blue-700'
    }`;
  }
}
```

## 6. Node.js后端集成

### Express.js中间件集成
```javascript
const express = require('express');
const axios = require('axios');

class LicenseAPIMiddleware {
  constructor(config) {
    this.apiBaseUrl = config.apiBaseUrl;
    this.getToken = config.getToken;
    this.onError = config.onError || console.error;
  }

  // 创建许可证的Express路由处理器
  createLicenseHandler = async (req, res) => {
    try {
      const licenseData = req.body;
      
      // 验证请求数据
      const validation = this.validateLicenseData(licenseData);
      if (!validation.valid) {
        return res.status(400).json({
          error: 'Validation failed',
          details: validation.errors
        });
      }

      // 调用许可证创建API
      const response = await axios.post(
        `${this.apiBaseUrl}/licenses/`,
        licenseData,
        {
          headers: {
            'Authorization': `Bearer ${this.getToken(req)}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // 记录成功日志
      console.log(`License created successfully: ${response.data.license_key}`);

      res.status(201).json(response.data);
    } catch (error) {
      this.handleError(error, res);
    }
  };

  validateLicenseData(data) {
    const errors = [];

    if (!data.plan || typeof data.plan !== 'number') {
      errors.push('plan field is required and must be a number');
    }

    if (!data.customer_info) {
      errors.push('customer_info field is required');
    } else {
      if (!data.customer_info.name) {
        errors.push('customer_info.name is required');
      }
      if (!data.customer_info.email || !this.isValidEmail(data.customer_info.email)) {
        errors.push('customer_info.email must be a valid email address');
      }
    }

    if (data.max_activations && (data.max_activations < 1 || !Number.isInteger(data.max_activations))) {
      errors.push('max_activations must be a positive integer');
    }

    if (data.validity_days && (data.validity_days < 1 || !Number.isInteger(data.validity_days))) {
      errors.push('validity_days must be a positive integer');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  }

  handleError(error, res) {
    if (error.response) {
      // API响应错误
      const status = error.response.status;
      const data = error.response.data;
      
      this.onError('API Error:', { status, data });
      
      res.status(status).json(data);
    } else if (error.request) {
      // 网络错误
      this.onError('Network Error:', error.message);
      
      res.status(503).json({
        error: 'Service unavailable',
        message: 'Unable to connect to license service'
      });
    } else {
      // 其他错误
      this.onError('Unknown Error:', error.message);
      
      res.status(500).json({
        error: 'Internal server error',
        message: 'An unexpected error occurred'
      });
    }
  }
}

// 使用示例
const app = express();
app.use(express.json());

const licenseMiddleware = new LicenseAPIMiddleware({
  apiBaseUrl: 'http://localhost:8000/api/v1/licenses/admin',
  getToken: (req) => req.headers.authorization?.replace('Bearer ', ''),
  onError: (message, details) => {
    console.error(`[License API] ${message}`, details);
  }
});

// 路由定义
app.post('/api/licenses', licenseMiddleware.createLicenseHandler);

// 批量创建许可证
app.post('/api/licenses/batch', async (req, res) => {
  const { licenses } = req.body;
  
  if (!Array.isArray(licenses)) {
    return res.status(400).json({
      error: 'licenses must be an array'
    });
  }

  const results = [];
  const errors = [];

  for (let i = 0; i < licenses.length; i++) {
    try {
      const license = licenses[i];
      const mockReq = { body: license, headers: req.headers };
      
      // 模拟响应对象
      const mockRes = {
        status: (code) => mockRes,
        json: (data) => {
          if (code === 201) {
            results.push({ index: i, license: data });
          } else {
            errors.push({ index: i, error: data });
          }
          return mockRes;
        }
      };

      await licenseMiddleware.createLicenseHandler(mockReq, mockRes);
      
      // 添加延迟避免API限流
      if (i < licenses.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    } catch (error) {
      errors.push({ index: i, error: error.message });
    }
  }

  res.json({
    total: licenses.length,
    successful: results.length,
    failed: errors.length,
    results,
    errors
  });
});

app.listen(3000, () => {
  console.log('License API proxy server running on port 3000');
});
```

## 7. 工具函数库

### 验证工具函数
```javascript
export const LicenseValidationUtils = {
  // 验证邮箱格式
  isValidEmail(email) {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return regex.test(email);
  },

  // 验证电话号码格式
  isValidPhone(phone) {
    // 支持中国手机号和固话格式
    const mobileRegex = /^1[3-9]\d{9}$/;
    const landlineRegex = /^0\d{2,3}-?\d{7,8}$/;
    const internationalRegex = /^\+\d{1,4}[- ]?\d{3,4}[- ]?\d{4,8}$/;
    
    return mobileRegex.test(phone) || 
           landlineRegex.test(phone) || 
           internationalRegex.test(phone);
  },

  // 验证许可证数据完整性
  validateLicenseData(data) {
    const errors = {};
    
    // 必需字段验证
    if (!data.plan || typeof data.plan !== 'number') {
      errors.plan = '请选择有效的许可证方案';
    }
    
    if (!data.customer_info) {
      errors.customer_info = '客户信息是必需的';
    } else {
      if (!data.customer_info.name?.trim()) {
        errors['customer_info.name'] = '客户姓名不能为空';
      }
      
      if (!data.customer_info.email?.trim()) {
        errors['customer_info.email'] = '客户邮箱不能为空';
      } else if (!this.isValidEmail(data.customer_info.email)) {
        errors['customer_info.email'] = '请输入有效的邮箱地址';
      }
      
      if (data.customer_info.phone && !this.isValidPhone(data.customer_info.phone)) {
        errors['customer_info.phone'] = '请输入有效的电话号码';
      }
    }
    
    // 可选字段验证
    if (data.max_activations !== undefined) {
      if (!Number.isInteger(data.max_activations) || data.max_activations < 1) {
        errors.max_activations = '最大激活数必须是大于0的整数';
      }
    }
    
    if (data.validity_days !== undefined) {
      if (!Number.isInteger(data.validity_days) || data.validity_days < 1) {
        errors.validity_days = '有效天数必须是大于0的整数';
      }
    }
    
    if (data.notes && data.notes.length > 1000) {
      errors.notes = '备注信息不能超过1000个字符';
    }
    
    return {
      isValid: Object.keys(errors).length === 0,
      errors
    };
  },

  // 格式化许可证数据
  formatLicenseData(formData) {
    const data = {
      plan: parseInt(formData.plan),
      customer_info: {
        name: formData.customer_info.name?.trim(),
        email: formData.customer_info.email?.trim().toLowerCase()
      }
    };
    
    // 添加可选字段
    if (formData.customer_info.company?.trim()) {
      data.customer_info.company = formData.customer_info.company.trim();
    }
    
    if (formData.customer_info.phone?.trim()) {
      data.customer_info.phone = formData.customer_info.phone.trim();
    }
    
    if (formData.customer_info.address?.trim()) {
      data.customer_info.address = formData.customer_info.address.trim();
    }
    
    if (formData.customer_info.contact_person?.trim()) {
      data.customer_info.contact_person = formData.customer_info.contact_person.trim();
    }
    
    if (formData.max_activations) {
      data.max_activations = parseInt(formData.max_activations);
    }
    
    if (formData.validity_days) {
      data.validity_days = parseInt(formData.validity_days);
    }
    
    if (formData.notes?.trim()) {
      data.notes = formData.notes.trim();
    }
    
    return data;
  },

  // 生成许可证摘要信息
  generateLicenseSummary(license) {
    return {
      key: license.license_key,
      customer: license.customer_name,
      product: license.product_name,
      plan: license.plan_name,
      activations: `${license.current_activations}/${license.max_activations}`,
      expires: new Date(license.expires_at).toLocaleDateString('zh-CN'),
      daysLeft: license.days_until_expiry,
      status: this.getStatusText(license.status)
    };
  },

  getStatusText(status) {
    const statusMap = {
      'active': '激活',
      'inactive': '未激活',
      'expired': '已过期',
      'revoked': '已撤销'
    };
    return statusMap[status] || status;
  }
};
```

### 日期工具函数
```javascript
export const DateUtils = {
  // 计算过期日期
  calculateExpiryDate(validityDays) {
    const now = new Date();
    const expiryDate = new Date(now.getTime() + (validityDays * 24 * 60 * 60 * 1000));
    return expiryDate;
  },

  // 格式化日期显示
  formatDate(dateString, format = 'full') {
    const date = new Date(dateString);
    
    switch (format) {
      case 'short':
        return date.toLocaleDateString('zh-CN');
      case 'medium':
        return date.toLocaleDateString('zh-CN', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        });
      case 'full':
      default:
        return date.toLocaleDateString('zh-CN', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
    }
  },

  // 计算剩余天数
  getDaysUntilExpiry(expiryDate) {
    const now = new Date();
    const expiry = new Date(expiryDate);
    const timeDiff = expiry.getTime() - now.getTime();
    const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));
    return Math.max(0, daysDiff);
  },

  // 获取过期状态
  getExpiryStatus(expiryDate) {
    const daysLeft = this.getDaysUntilExpiry(expiryDate);
    
    if (daysLeft <= 0) {
      return { status: 'expired', class: 'text-red-600', text: '已过期' };
    } else if (daysLeft <= 7) {
      return { status: 'warning', class: 'text-yellow-600', text: `${daysLeft}天后过期` };
    } else if (daysLeft <= 30) {
      return { status: 'caution', class: 'text-orange-600', text: `${daysLeft}天后过期` };
    } else {
      return { status: 'normal', class: 'text-green-600', text: `${daysLeft}天后过期` };
    }
  }
};
```

## 8. 测试代码

### Jest单元测试
```javascript
// __tests__/LicenseAPIClient.test.js
import { TypedLicenseAPIClient } from '../src/LicenseAPIClient';
import fetchMock from 'jest-fetch-mock';

describe('LicenseAPIClient', () => {
  let client;
  
  beforeEach(() => {
    fetchMock.resetMocks();
    client = new TypedLicenseAPIClient({
      baseUrl: '/api/test',
      tokenProvider: () => 'test-token'
    });
  });

  describe('createLicense', () => {
    test('should create license successfully', async () => {
      const mockLicense = {
        id: 1,
        license_key: 'TEST1-ABCDE-FGHIJ-KLMNO-PQRST',
        customer_name: '测试客户',
        customer_email: 'test@example.com'
      };

      fetchMock.mockResponseOnce(JSON.stringify(mockLicense), {
        status: 201
      });

      const licenseData = {
        plan: 2,
        customer_info: {
          name: '测试客户',
          email: 'test@example.com'
        }
      };

      const result = await client.createLicense(licenseData);

      expect(result).toEqual(mockLicense);
      expect(fetchMock).toHaveBeenCalledWith('/api/test/licenses/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token'
        },
        body: JSON.stringify(licenseData)
      });
    });

    test('should handle validation errors', async () => {
      const mockError = {
        detail: '验证失败',
        errors: {
          customer_info: {
            email: ['请输入有效的邮箱地址']
          }
        }
      };

      fetchMock.mockResponseOnce(JSON.stringify(mockError), {
        status: 400
      });

      const licenseData = {
        plan: 2,
        customer_info: {
          name: '测试客户',
          email: 'invalid-email'
        }
      };

      await expect(client.createLicense(licenseData)).rejects.toThrow();
    });

    test('should validate required fields', async () => {
      const invalidData = {
        customer_info: {
          name: '',
          email: ''
        }
      };

      await expect(client.createLicense(invalidData)).rejects.toThrow('plan字段是必需的');
    });
  });

  describe('getPlans', () => {
    test('should fetch plans successfully', async () => {
      const mockPlans = {
        count: 2,
        results: [
          { id: 1, name: '基础版', price: '299.00' },
          { id: 2, name: '专业版', price: '599.00' }
        ]
      };

      fetchMock.mockResponseOnce(JSON.stringify(mockPlans));

      const result = await client.getPlans();

      expect(result).toEqual(mockPlans);
    });
  });
});
```

### React组件测试
```javascript
// __tests__/CreateLicenseForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CreateLicenseForm from '../src/components/CreateLicenseForm';
import { TypedLicenseAPIClient } from '../src/LicenseAPIClient';

jest.mock('../src/LicenseAPIClient');

describe('CreateLicenseForm', () => {
  const mockCreateLicense = jest.fn();
  const mockGetPlans = jest.fn();

  beforeEach(() => {
    (TypedLicenseAPIClient as jest.Mock).mockImplementation(() => ({
      createLicense: mockCreateLicense,
      getPlans: mockGetPlans
    }));

    mockGetPlans.mockResolvedValue({
      results: [
        { id: 1, name: '基础版', price: '299.00', default_max_activations: 1, default_validity_days: 365 },
        { id: 2, name: '专业版', price: '599.00', default_max_activations: 5, default_validity_days: 365 }
      ]
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render form fields correctly', async () => {
    render(<CreateLicenseForm />);

    await waitFor(() => {
      expect(screen.getByLabelText(/许可证方案/)).toBeInTheDocument();
      expect(screen.getByLabelText(/客户姓名/)).toBeInTheDocument();
      expect(screen.getByLabelText(/客户邮箱/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /创建许可证/ })).toBeInTheDocument();
    });
  });

  test('should load plans on mount', async () => {
    render(<CreateLicenseForm />);

    await waitFor(() => {
      expect(mockGetPlans).toHaveBeenCalled();
      expect(screen.getByText('基础版 - ¥299.00 (1设备, 365天)')).toBeInTheDocument();
      expect(screen.getByText('专业版 - ¥599.00 (5设备, 365天)')).toBeInTheDocument();
    });
  });

  test('should submit form with valid data', async () => {
    const user = userEvent.setup();
    const mockLicense = {
      id: 1,
      license_key: 'TEST1-ABCDE-FGHIJ-KLMNO-PQRST',
      customer_name: '测试客户',
      customer_email: 'test@example.com'
    };

    mockCreateLicense.mockResolvedValue(mockLicense);

    render(<CreateLicenseForm />);

    await waitFor(() => {
      expect(screen.getByText('基础版 - ¥299.00 (1设备, 365天)')).toBeInTheDocument();
    });

    // 填写表单
    await user.selectOptions(screen.getByLabelText(/许可证方案/), '1');
    await user.type(screen.getByLabelText(/客户姓名/), '测试客户');
    await user.type(screen.getByLabelText(/客户邮箱/), 'test@example.com');

    // 提交表单
    await user.click(screen.getByRole('button', { name: /创建许可证/ }));

    await waitFor(() => {
      expect(mockCreateLicense).toHaveBeenCalledWith({
        plan: 1,
        customer_info: {
          name: '测试客户',
          email: 'test@example.com',
          company: '',
          phone: ''
        },
        notes: ''
      });
    });

    // 验证成功消息
    await waitFor(() => {
      expect(screen.getByText('许可证创建成功！')).toBeInTheDocument();
      expect(screen.getByText(/TEST1-ABCDE-FGHIJ-KLMNO-PQRST/)).toBeInTheDocument();
    });
  });

  test('should display validation errors', async () => {
    const user = userEvent.setup();

    render(<CreateLicenseForm />);

    // 提交空表单
    await user.click(screen.getByRole('button', { name: /创建许可证/ }));

    await waitFor(() => {
      expect(screen.getByText('请选择许可证方案')).toBeInTheDocument();
      expect(screen.getByText('请输入客户姓名')).toBeInTheDocument();
      expect(screen.getByText('请输入客户邮箱')).toBeInTheDocument();
    });
  });

  test('should handle API errors', async () => {
    const user = userEvent.setup();
    const mockError = new Error('创建许可证失败');
    mockError.status = 500;

    mockCreateLicense.mockRejectedValue(mockError);

    render(<CreateLicenseForm />);

    await waitFor(() => {
      expect(screen.getByText('基础版 - ¥299.00 (1设备, 365天)')).toBeInTheDocument();
    });

    // 填写表单
    await user.selectOptions(screen.getByLabelText(/许可证方案/), '1');
    await user.type(screen.getByLabelText(/客户姓名/), '测试客户');
    await user.type(screen.getByLabelText(/客户邮箱/), 'test@example.com');

    // 提交表单
    await user.click(screen.getByRole('button', { name: /创建许可证/ }));

    await waitFor(() => {
      expect(screen.getByText('创建许可证失败，请稍后重试')).toBeInTheDocument();
    });
  });
});
```

### End-to-End测试 (Cypress)
```javascript
// cypress/integration/create-license.spec.js
describe('Create License', () => {
  beforeEach(() => {
    // 模拟登录
    cy.login('admin', 'password');
    cy.visit('/licenses/create');
  });

  it('should create license successfully', () => {
    // 等待方案加载
    cy.get('[data-cy=plan-select]').should('exist');
    cy.get('[data-cy=plan-select] option').should('have.length.greaterThan', 1);

    // 选择方案
    cy.get('[data-cy=plan-select]').select('2');

    // 填写客户信息
    cy.get('[data-cy=customer-name]').type('端到端测试客户');
    cy.get('[data-cy=customer-email]').type('e2e@example.com');
    cy.get('[data-cy=customer-company]').type('测试公司');
    cy.get('[data-cy=customer-phone]').type('138-0000-0000');

    // 填写可选字段
    cy.get('[data-cy=max-activations]').type('10');
    cy.get('[data-cy=validity-days]').type('365');
    cy.get('[data-cy=notes]').type('端到端测试许可证');

    // 提交表单
    cy.get('[data-cy=submit-button]').click();

    // 验证成功消息
    cy.get('[data-cy=success-message]').should('be.visible');
    cy.get('[data-cy=license-key]').should('contain', '-');

    // 验证表单重置
    cy.get('[data-cy=customer-name]').should('have.value', '');
    cy.get('[data-cy=customer-email]').should('have.value', '');
  });

  it('should display validation errors', () => {
    // 直接提交空表单
    cy.get('[data-cy=submit-button]').click();

    // 验证错误消息
    cy.get('[data-cy=plan-error]').should('contain', '请选择许可证方案');
    cy.get('[data-cy=customer-name-error]').should('contain', '请输入客户姓名');
    cy.get('[data-cy=customer-email-error]').should('contain', '请输入客户邮箱');
  });

  it('should handle server errors gracefully', () => {
    // 模拟服务器错误
    cy.intercept('POST', '/api/v1/licenses/admin/licenses/', {
      statusCode: 500,
      body: { detail: '服务器内部错误' }
    });

    // 填写有效数据
    cy.get('[data-cy=plan-select]').select('2');
    cy.get('[data-cy=customer-name]').type('测试客户');
    cy.get('[data-cy=customer-email]').type('test@example.com');

    // 提交表单
    cy.get('[data-cy=submit-button]').click();

    // 验证错误处理
    cy.get('[data-cy=error-message]').should('contain', '创建许可证失败');
  });
});
```

---

这份完整的代码示例文档涵盖了从原生JavaScript到各种现代框架的实现，以及完整的测试策略。开发者可以根据自己的技术栈选择合适的实现方案。

**下一步**: 根据您的实际项目需求，选择合适的代码示例进行集成和定制。
