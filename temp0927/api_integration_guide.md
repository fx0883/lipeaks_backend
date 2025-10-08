# 许可证创建API集成指南

## 🎯 API概述

**端点**: `POST /api/v1/licenses/admin/licenses/`  
**功能**: 为指定的许可证方案创建新的许可证  
**权限**: 需要管理员权限（超级管理员或租户管理员）  
**认证**: JWT Bearer Token

## 🔧 基础集成流程

### 1. 准备工作

#### 获取JWT Token
```javascript
// 登录获取token
const loginResponse = await fetch('/api/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'password'
  })
});
const { access_token } = await loginResponse.json();
```

#### 获取可用的许可证方案
```javascript
// 获取许可证方案列表
const plansResponse = await fetch('/api/v1/licenses/admin/plans/', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
const plans = await plansResponse.json();
```

### 2. 创建许可证请求

#### 基础请求结构
```javascript
const createLicense = async (licenseData) => {
  try {
    const response = await fetch('/api/v1/licenses/admin/licenses/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${access_token}`
      },
      body: JSON.stringify(licenseData)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const license = await response.json();
    return license;
  } catch (error) {
    console.error('创建许可证失败:', error);
    throw error;
  }
};
```

### 3. 请求数据结构

#### 最简单的请求（仅必需字段）
```javascript
const minimalRequest = {
  plan: 2,  // 许可证方案ID
  customer_info: {
    name: '张三',
    email: 'zhangsan@example.com'
  }
};

// 创建许可证
const license = await createLicense(minimalRequest);
```

#### 完整请求（包含所有可选字段）
```javascript
const fullRequest = {
  plan: 3,                    // 必需：许可证方案ID
  tenant: 1,                  // 可选：租户ID（默认使用当前用户租户）
  customer_info: {            // 必需：客户信息对象
    name: '王五',             // 必需：客户姓名
    email: 'wangwu@corp.com', // 必需：客户邮箱
    company: '某某公司',      // 可选：公司名称
    phone: '138-0013-8000',   // 可选：联系电话
    address: '北京市朝阳区',  // 可选：地址
    contact_person: '技术部'   // 可选：联系人
  },
  max_activations: 10,        // 可选：最大激活数（默认使用方案设置）
  validity_days: 365,         // 可选：有效天数（默认使用方案设置）
  notes: '特殊客户许可证'     // 可选：备注信息
};

const license = await createLicense(fullRequest);
```

## 🔄 业务逻辑说明

### 自动字段处理

1. **产品自动关联**: 不需要传入product字段，系统自动从plan获取
2. **租户自动关联**: 如果不传入tenant，系统使用当前用户的租户
3. **密钥自动生成**: 系统自动生成25位格式的许可证密钥
4. **时间戳自动设置**: issued_at, created_at等时间戳自动设置

### 默认值处理

- **max_activations**: 如未指定，使用plan.default_max_activations
- **expires_at**: 根据validity_days计算，如未指定validity_days则使用plan.default_validity_days
- **status**: 新创建的许可证状态默认为'active'

## 📊 响应数据结构

### 成功响应 (HTTP 201)
```javascript
{
  "id": 123,
  "product": 1,
  "product_name": "SuperApp Pro",
  "plan": 2,
  "plan_name": "企业版",
  "tenant": 1,
  "tenant_name": "示例公司",
  "license_key": "ABC12-DEF34-GHI56-JKL78-MNO90",
  "customer_name": "张三",
  "customer_email": "zhangsan@example.com",
  "max_activations": 10,
  "current_activations": 0,
  "issued_at": "2024-09-27T10:30:00Z",
  "expires_at": "2025-09-27T10:30:00Z",
  "last_verified_at": null,
  "status": "active",
  "machine_bindings_count": 0,
  "days_until_expiry": 365,
  "notes": "客户申请的标准版许可证",
  "machine_bindings": [],
  "recent_activations": [],
  "usage_stats": {
    "total_usage_logs": 0,
    "recent_usage_logs": 0
  },
  "metadata": {
    "created_by": "admin",
    "creation_source": "admin_panel",
    "ip_address": "192.168.1.100"
  }
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 许可证唯一标识符 |
| `license_key` | String | 25位格式的许可证密钥 |
| `product_name` | String | 产品名称（只读） |
| `plan_name` | String | 方案名称（只读） |
| `tenant_name` | String | 租户名称（只读） |
| `max_activations` | Integer | 最大激活设备数 |
| `current_activations` | Integer | 当前激活设备数 |
| `days_until_expiry` | Integer | 距离过期天数 |
| `machine_bindings_count` | Integer | 绑定设备数量 |
| `usage_stats` | Object | 使用统计信息 |

## ⚠️ 重要注意事项

### 字段废弃说明
- **product字段**: 已废弃，不要在请求中包含此字段
- **系统自动获取**: product会从plan.product自动获取

### 权限限制
- **租户管理员**: 只能为自己租户创建许可证
- **超级管理员**: 可以为任意租户创建许可证
- **普通用户**: 无权限调用此API

### 数据验证
- **plan存在性**: plan必须存在且未被删除
- **租户权限**: 如果指定tenant，必须有权限访问该租户
- **邮箱格式**: customer_info.email必须是有效邮箱格式
- **数值范围**: max_activations和validity_days必须是正整数

## 🔗 集成示例

### React组件示例
```jsx
import React, { useState } from 'react';

const CreateLicenseForm = ({ plans, onSuccess }) => {
  const [formData, setFormData] = useState({
    plan: '',
    customer_info: {
      name: '',
      email: '',
      company: '',
      phone: ''
    },
    max_activations: '',
    validity_days: '',
    notes: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        plan: parseInt(formData.plan),
        customer_info: formData.customer_info
      };

      // 只有非空值才添加到payload
      if (formData.max_activations) {
        payload.max_activations = parseInt(formData.max_activations);
      }
      if (formData.validity_days) {
        payload.validity_days = parseInt(formData.validity_days);
      }
      if (formData.notes.trim()) {
        payload.notes = formData.notes.trim();
      }

      const license = await createLicense(payload);
      onSuccess(license);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* 表单字段... */}
      <button type="submit" disabled={loading}>
        {loading ? '创建中...' : '创建许可证'}
      </button>
      {error && <div className="error">{error}</div>}
    </form>
  );
};
```

### Vue.js组件示例
```vue
<template>
  <form @submit.prevent="createLicense">
    <div class="form-group">
      <label>许可证方案*</label>
      <select v-model="form.plan" required>
        <option value="">请选择方案</option>
        <option v-for="plan in plans" :key="plan.id" :value="plan.id">
          {{ plan.name }}
        </option>
      </select>
    </div>
    
    <div class="form-group">
      <label>客户姓名*</label>
      <input v-model="form.customer_info.name" required>
    </div>
    
    <div class="form-group">
      <label>客户邮箱*</label>
      <input v-model="form.customer_info.email" type="email" required>
    </div>
    
    <button type="submit" :disabled="loading">
      {{ loading ? '创建中...' : '创建许可证' }}
    </button>
  </form>
</template>

<script>
export default {
  data() {
    return {
      form: {
        plan: '',
        customer_info: {
          name: '',
          email: '',
          company: '',
          phone: ''
        },
        max_activations: '',
        validity_days: '',
        notes: ''
      },
      loading: false
    };
  },
  methods: {
    async createLicense() {
      this.loading = true;
      try {
        const license = await this.callCreateAPI(this.form);
        this.$emit('success', license);
      } catch (error) {
        this.$emit('error', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

## 📝 下一步

- 阅读 [字段参考文档](field_reference.md) 了解每个字段的详细用法
- 查看 [业务场景示例](business_scenarios.md) 学习实际业务场景
- 参考 [错误处理指南](error_handling.md) 学习错误处理
- 查看 [代码示例](code_examples.md) 获取更多实现参考

---

**需要帮助？** 请查看相关文档或联系技术支持团队。
