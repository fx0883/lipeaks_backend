# Member 许可证完整集成指南

本文档提供从申请许可证到客户端软件激活的完整流程指导。

---

## 目录

- [业务流程概览](#业务流程概览)
- [第一步：展示可申请产品](#第一步展示可申请产品)
- [第二步：申请试用许可证](#第二步申请试用许可证)
- [第三步：查看许可证列表](#第三步查看许可证列表)
- [第四步：客户端软件激活](#第四步客户端软件激活)
- [第五步：保持在线状态](#第五步保持在线状态)
- [完整代码示例](#完整代码示例)
- [错误处理指南](#错误处理指南)

---

## 业务流程概览

### 完整流程图

```
┌─────────────────┐
│  1. Member登录   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 浏览产品列表  │ ← GET /api/v1/licenses/member/available-products/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 选择产品申请  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. 填写申请信息  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. 提交申请     │ ← POST /api/v1/licenses/member/apply/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. 获取许可证密钥│ ← 重要：保存license_key
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 7. 下载客户端软件│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 8. 在软件中输入  │
│    许可证密钥    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 9. 软件调用激活API│ ← POST /api/v1/licenses/activate/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 10. 获取激活码   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 11. 软件正常使用 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 12. 定期心跳    │ ← POST /api/v1/licenses/heartbeat/
└─────────────────┘
```

---

## 第一步：展示可申请产品

### API调用

```javascript
async function getAvailableProducts() {
  const response = await axios.get('/api/v1/licenses/member/available-products/');
  return response.data.data.products;
}
```

### 前端展示

```vue
<template>
  <div class="products-showcase">
    <h2>可申请的试用产品</h2>
    
    <div class="products-grid">
      <div
        v-for="product in products"
        :key="product.id"
        class="product-card"
        :class="{ disabled: product.already_applied }"
      >
        <h3>{{ product.name }}</h3>
        <p>{{ product.description }}</p>
        
        <div v-if="product.trial_plan" class="trial-info">
          <span class="trial-badge">
            {{ product.trial_plan.default_validity_days }}天免费试用
          </span>
          <span class="devices-badge">
            {{ product.trial_plan.default_max_activations }}个设备
          </span>
        </div>
        
        <button
          @click="applyProduct(product)"
          :disabled="product.already_applied"
        >
          {{ product.already_applied ? '已申请' : '立即申请' }}
        </button>
      </div>
    </div>
  </div>
</template>
```

### 关键要点

- ✅ 显示产品的试用方案信息
- ✅ 禁用已申请的产品
- ✅ 醒目展示试用天数和设备数

---

## 第二步：申请试用许可证

### API调用

```javascript
async function applyTrialLicense(productId, reason, userInfo) {
  const requestData = {
    product_id: productId,
    reason: reason || '试用申请'
  };
  
  // 只在有值时添加user_info
  if (userInfo && Object.values(userInfo).some(v => v)) {
    requestData.user_info = userInfo;
  }
  
  const response = await axios.post(
    '/api/v1/licenses/member/apply/',
    requestData
  );
  
  return response.data;
}
```

### 申请表单示例

```vue
<template>
  <el-form ref="formRef" :model="formData" :rules="rules">
    <!-- 产品选择 -->
    <el-form-item label="产品" prop="product_id">
      <el-select v-model="formData.product_id">
        <el-option
          v-for="product in availableProducts"
          :key="product.id"
          :label="product.name"
          :value="product.id"
        />
      </el-select>
    </el-form-item>
    
    <!-- 申请原因 -->
    <el-form-item label="申请原因">
      <el-input
        v-model="formData.reason"
        type="textarea"
        placeholder="请简要说明申请原因"
        maxlength="500"
      />
    </el-form-item>
    
    <!-- 补充信息 -->
    <el-collapse>
      <el-collapse-item title="补充信息（可选）" name="1">
        <el-form-item label="公司">
          <el-input v-model="formData.user_info.company" maxlength="100" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="formData.user_info.job_title" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="formData.user_info.phone" maxlength="20" />
        </el-form-item>
        <el-form-item label="用途">
          <el-input
            v-model="formData.user_info.intended_use"
            type="textarea"
            maxlength="500"
          />
        </el-form-item>
      </el-collapse-item>
    </el-collapse>
    
    <!-- 提交按钮 -->
    <el-form-item>
      <el-button
        type="primary"
        @click="handleSubmit"
        :loading="submitting"
      >
        提交申请
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
const formData = ref({
  product_id: null,
  reason: '',
  user_info: {
    company: '',
    job_title: '',
    phone: '',
    intended_use: ''
  }
});

const handleSubmit = async () => {
  try {
    const result = await applyTrialLicense(
      formData.value.product_id,
      formData.value.reason,
      formData.value.user_info
    );
    
    // 显示成功对话框，展示许可证密钥
    showSuccessDialog(result.data);
  } catch (error) {
    handleError(error);
  }
};
</script>
```

### 成功后的处理

```javascript
function showSuccessDialog(applicationResult) {
  ElMessageBox.alert(
    `
    <div style="text-align: center;">
      <h2>申请成功！</h2>
      <p>您的许可证密钥：</p>
      <div style="background: #f5f7fa; padding: 15px; margin: 15px 0; border-radius: 4px;">
        <code style="font-size: 18px; font-weight: bold;">
          ${applicationResult.license_key}
        </code>
      </div>
      <p style="color: #F56C6C;">⚠️ 请妥善保管此密钥，后续不再显示完整密钥！</p>
      <p>过期时间：${formatDate(applicationResult.expires_at)}</p>
      <p>可激活设备：${applicationResult.max_activations} 个</p>
    </div>
    `,
    '申请成功',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '复制密钥',
      callback: () => {
        copyToClipboard(applicationResult.license_key);
      }
    }
  );
}
```

---

## 第三步：查看许可证列表

### API调用

```javascript
async function getMyLicenses(filters = {}) {
  const response = await axios.get('/api/v1/licenses/member/my-licenses/', {
    params: filters
  });
  
  return response.data.data;
}

// 使用示例
const licenseData = await getMyLicenses({ status: 'active' });

console.log('总数:', licenseData.count);
console.log('有效数:', licenseData.active_count);
console.log('许可证:', licenseData.licenses);
```

### 列表展示建议

```javascript
// 按状态分组展示
function renderLicensesByGroup(licenses) {
  const groups = {
    active: [],
    expiring_soon: [],
    expired: [],
    others: []
  };
  
  licenses.forEach(license => {
    if (license.status === 'expired') {
      groups.expired.push(license);
    } else if (license.status === 'active') {
      if (license.days_until_expiry !== null && license.days_until_expiry <= 7) {
        groups.expiring_soon.push(license);
      } else {
        groups.active.push(license);
      }
    } else {
      groups.others.push(license);
    }
  });
  
  return groups;
}
```

---

## 第四步：客户端软件激活

### 激活流程说明

Member申请到许可证后，需要在客户端软件中激活才能使用。激活流程如下：

### 激活API

```
POST /api/v1/licenses/activate/
```

**注意**：这个API是客户端软件调用的，不是Web前端调用！

### 激活请求参数

```json
{
  "license_key": "ABCDE-FGHIJ-KLMNO-PQRST-UVWXY",
  "hardware_info": {
    "hardware_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "system_info": {
      "os": "Windows 10",
      "os_version": "10.0.19041",
      "cpu": "Intel Core i7",
      "memory": "16GB",
      "mac_address": "00:1B:44:11:3A:B7"
    }
  },
  "client_info": {
    "app_version": "1.2.0",
    "app_name": "PDF Compressor"
  }
}
```

### 激活响应

**成功**：
```json
{
  "success": true,
  "message": "许可证激活成功",
  "data": {
    "activation_code": "XXXX-XXXX-XXXX-XXXX",
    "expires_at": "2025-11-05T10:30:00Z",
    "max_activations": 1,
    "current_activations": 1,
    "product_info": {
      "name": "PDF压缩工具",
      "version": "1.2.0"
    }
  }
}
```

**activation_code** 是激活成功后的激活码，客户端需要保存，用于后续的心跳和验证。

### Web前端的角色

Web前端需要提供：

1. **激活指南页面**：告诉用户如何在软件中激活

```vue
<template>
  <el-dialog v-model="visible" title="激活指南" width="700px">
    <el-steps :active="currentStep" align-center>
      <el-step title="下载软件" />
      <el-step title="安装软件" />
      <el-step title="输入许可证" />
      <el-step title="开始使用" />
    </el-steps>
    
    <div class="guide-content">
      <!-- 步骤1：下载软件 -->
      <div v-if="currentStep === 0" class="step-content">
        <h3>第一步：下载客户端软件</h3>
        <p>请根据您的操作系统下载对应版本：</p>
        <div class="download-links">
          <el-button type="primary" @click="downloadWindows">
            Windows版下载
          </el-button>
          <el-button @click="downloadMac">
            macOS版下载
          </el-button>
          <el-button @click="downloadLinux">
            Linux版下载
          </el-button>
        </div>
      </div>
      
      <!-- 步骤2：安装软件 -->
      <div v-if="currentStep === 1" class="step-content">
        <h3>第二步：安装软件</h3>
        <ol>
          <li>双击下载的安装包</li>
          <li>按照安装向导完成安装</li>
          <li>启动软件</li>
        </ol>
      </div>
      
      <!-- 步骤3：输入许可证 -->
      <div v-if="currentStep === 2" class="step-content">
        <h3>第三步：输入许可证密钥</h3>
        <p>在软件中找到"激活许可证"或"输入许可证"功能</p>
        
        <el-alert
          title="您的许可证密钥"
          type="success"
          :closable="false"
        >
          <div class="license-key-display">
            <code>{{ licenseInfo.license_key_preview }}</code>
            <el-button
              type="primary"
              size="small"
              @click="showFullKey"
            >
              查看完整密钥
            </el-button>
          </div>
        </el-alert>
        
        <el-alert
          title="重要提示"
          type="warning"
          :closable="false"
          style="margin-top: 15px;"
        >
          <p>如果您未保存完整的许可证密钥，请在"我的许可证"页面查看。</p>
          <p>激活时请确保网络连接正常。</p>
        </el-alert>
      </div>
      
      <!-- 步骤4：开始使用 -->
      <div v-if="currentStep === 3" class="step-content">
        <h3>第四步：开始使用</h3>
        <p>激活成功后，您可以开始使用软件的全部功能！</p>
        
        <el-result icon="success" title="激活完成">
          <template #extra>
            <p>试用期限：{{ licenseInfo.trial_days }}天</p>
            <p>可激活设备：{{ licenseInfo.max_activations }}个</p>
          </template>
        </el-result>
      </div>
    </div>
    
    <template #footer>
      <el-button v-if="currentStep > 0" @click="currentStep--">
        上一步
      </el-button>
      <el-button
        v-if="currentStep < 3"
        type="primary"
        @click="currentStep++"
      >
        下一步
      </el-button>
      <el-button v-if="currentStep === 3" type="primary" @click="finish">
        完成
      </el-button>
    </template>
  </el-dialog>
</template>
```

2. **下载链接页面**：提供软件下载链接

```vue
<template>
  <div class="download-page">
    <h2>下载 {{ productName }}</h2>
    
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="os-header">
              <i class="fab fa-windows"></i>
              <span>Windows</span>
            </div>
          </template>
          <p>支持 Windows 10/11</p>
          <p class="version">版本：{{ version }}</p>
          <p class="size">大小：45.2 MB</p>
          <el-button type="primary" @click="download('windows')">
            下载 Windows 版
          </el-button>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="os-header">
              <i class="fab fa-apple"></i>
              <span>macOS</span>
            </div>
          </template>
          <p>支持 macOS 11+</p>
          <p class="version">版本：{{ version }}</p>
          <p class="size">大小：38.7 MB</p>
          <el-button type="primary" @click="download('mac')">
            下载 macOS 版
          </el-button>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="os-header">
              <i class="fab fa-linux"></i>
              <span>Linux</span>
            </div>
          </template>
          <p>支持 Ubuntu 20.04+</p>
          <p class="version">版本：{{ version }}</p>
          <p class="size">大小：42.1 MB</p>
          <el-button type="primary" @click="download('linux')">
            下载 Linux 版
          </el-button>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 许可证密钥提示 -->
    <el-alert
      title="您的许可证密钥"
      type="info"
      style="margin-top: 30px;"
    >
      <p>请在软件安装后使用以下许可证密钥激活：</p>
      <div class="license-key-box">
        <el-input
          v-model="licenseKey"
          readonly
        >
          <template #append>
            <el-button @click="copyKey">复制密钥</el-button>
          </template>
        </el-input>
      </div>
    </el-alert>
  </div>
</template>
```

---

## 第四步：客户端软件激活

### 客户端激活流程

**注意**：以下API是**客户端软件**调用的，不是Web前端！

#### 1. 激活许可证

```javascript
// 客户端代码（JavaScript/Electron示例）
async function activateLicense(licenseKey) {
  // 1. 收集硬件信息
  const hardwareInfo = await collectHardwareInfo();
  
  // 2. 调用激活API
  const response = await axios.post('http://your-server.com/api/v1/licenses/activate/', {
    license_key: licenseKey,
    hardware_info: hardwareInfo,
    client_info: {
      app_version: '1.2.0',
      app_name: 'PDF Compressor'
    }
  });
  
  if (response.data.success) {
    // 3. 保存激活码
    const activationCode = response.data.data.activation_code;
    saveActivationCode(activationCode);
    
    // 4. 保存过期时间
    const expiresAt = response.data.data.expires_at;
    saveExpiryDate(expiresAt);
    
    return {
      success: true,
      activationCode,
      expiresAt
    };
  }
  
  return {
    success: false,
    error: response.data.error
  };
}

// 收集硬件信息
async function collectHardwareInfo() {
  // 使用node-machine-id或类似库
  const { machineIdSync } = require('node-machine-id');
  const os = require('os');
  const { networkInterfaces } = os;
  
  // 获取MAC地址
  const interfaces = networkInterfaces();
  const macAddress = Object.values(interfaces)
    .flat()
    .find(i => i.mac && i.mac !== '00:00:00:00:00:00')?.mac || '';
  
  return {
    hardware_uuid: machineIdSync(),
    system_info: {
      os: os.type(),
      os_version: os.release(),
      cpu: os.cpus()[0].model,
      memory: `${Math.round(os.totalmem() / 1024 / 1024 / 1024)}GB`,
      mac_address: macAddress
    }
  };
}
```

#### 2. 验证激活状态

```javascript
// 客户端定期验证（每次启动时）
async function verifyActivation(activationCode) {
  const response = await axios.post('http://your-server.com/api/v1/licenses/verify/', {
    activation_code: activationCode
  });
  
  if (response.data.success && response.data.data.is_valid) {
    return true;
  }
  
  return false;
}
```

---

## 第五步：保持在线状态

### 心跳API

客户端软件需要定期发送心跳，保持在线状态：

```javascript
// 客户端代码：定期发送心跳（每5分钟）
async function sendHeartbeat(activationCode) {
  const response = await axios.post('http://your-server.com/api/v1/licenses/heartbeat/', {
    activation_code: activationCode,
    event_type: 'heartbeat',
    event_data: {},
    software_version: '1.2.0',
    session_id: getCurrentSessionId(),
    system_status: {
      cpu_usage: getCPUUsage(),
      memory_usage: getMemoryUsage()
    }
  });
  
  return response.data;
}

// 启动心跳定时器
let heartbeatInterval;

function startHeartbeat(activationCode) {
  // 每5分钟发送一次心跳
  heartbeatInterval = setInterval(() => {
    sendHeartbeat(activationCode).catch(error => {
      console.error('心跳发送失败:', error);
    });
  }, 5 * 60 * 1000);
}

function stopHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
  }
}
```

---

## 完整代码示例

### Web前端完整流程

```javascript
// licenseService.js - 许可证服务封装
import axios from 'axios';

class LicenseService {
  baseURL = '/api/v1/licenses/member';
  
  // 1. 获取可申请产品列表
  async getAvailableProducts() {
    const response = await axios.get(`${this.baseURL}/available-products/`);
    return response.data.data;
  }
  
  // 2. 申请试用许可证
  async applyTrialLicense(productId, reason, userInfo) {
    const requestData = { product_id: productId };
    
    if (reason) requestData.reason = reason;
    if (userInfo) requestData.user_info = userInfo;
    
    const response = await axios.post(`${this.baseURL}/apply/`, requestData);
    return response.data;
  }
  
  // 3. 获取我的许可证
  async getMyLicenses(filters = {}) {
    const response = await axios.get(`${this.baseURL}/my-licenses/`, {
      params: filters
    });
    return response.data.data;
  }
}

export default new LicenseService();
```

### 使用示例

```javascript
import licenseService from '@/api/services/licenseService';

// === 完整流程示例 ===

async function completeLicenseFlow() {
  try {
    // 步骤1：获取可申请产品
    console.log('步骤1：获取可申请产品...');
    const productsData = await licenseService.getAvailableProducts();
    console.log('可申请产品:', productsData.products);
    
    // 步骤2：用户选择产品
    const selectedProduct = productsData.products[0];
    console.log('选择产品:', selectedProduct.name);
    
    // 步骤3：申请许可证
    console.log('步骤3：申请许可证...');
    const applicationResult = await licenseService.applyTrialLicense(
      selectedProduct.id,
      '我想试用这个产品',
      {
        company: '我的公司',
        job_title: '开发工程师',
        intended_use: '用于项目开发'
      }
    );
    
    console.log('申请成功！');
    console.log('许可证密钥:', applicationResult.data.license_key);
    console.log('过期时间:', applicationResult.data.expires_at);
    
    // ⚠️ 重要：提示用户保存许可证密钥
    alert(`许可证申请成功！\n密钥：${applicationResult.data.license_key}\n请妥善保管！`);
    
    // 步骤4：查看我的许可证
    console.log('步骤4：查看我的许可证...');
    const myLicenses = await licenseService.getMyLicenses();
    
    console.log('许可证总数:', myLicenses.count);
    console.log('有效许可证:', myLicenses.active_count);
    console.log('许可证列表:', myLicenses.licenses);
    
    // 步骤5：引导用户下载和激活软件
    console.log('步骤5：引导用户下载软件并在软件中激活...');
    showDownloadGuide(selectedProduct, applicationResult.data.license_key);
    
  } catch (error) {
    console.error('流程失败:', error);
    
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 400 && data.errors) {
        // 显示字段错误
        for (const [field, messages] of Object.entries(data.errors)) {
          console.error(`${field}: ${messages.join(', ')}`);
        }
      } else {
        console.error('错误:', data.error || data.detail);
      }
    }
  }
}
```

---

## 错误处理指南

### 统一错误处理函数

```javascript
function handleLicenseError(error, context = '') {
  if (!error.response) {
    return {
      message: '网络连接失败，请检查网络设置',
      type: 'network'
    };
  }
  
  const { status, data } = error.response;
  
  switch (status) {
    case 400:
      // 参数或业务规则错误
      if (data.errors) {
        const errorMessages = [];
        
        for (const [field, messages] of Object.entries(data.errors)) {
          if (field === 'non_field_errors') {
            errorMessages.push(...messages);
          } else if (field === 'product_id') {
            errorMessages.push(`产品选择错误: ${messages.join(', ')}`);
          } else {
            errorMessages.push(`${field}: ${messages.join(', ')}`);
          }
        }
        
        return {
          message: errorMessages.join('\n'),
          type: 'validation'
        };
      }
      
      return {
        message: data.error || '请求参数错误',
        type: 'validation'
      };
      
    case 401:
      return {
        message: '登录已过期，请重新登录',
        type: 'auth',
        action: 'redirect_login'
      };
      
    case 403:
      return {
        message: '权限不足，此功能仅限Member用户使用',
        type: 'permission'
      };
      
    case 429:
      const match = data.detail?.match(/(\d+) seconds/);
      let waitTime = '一段时间';
      
      if (match) {
        const seconds = parseInt(match[1]);
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (hours > 0) {
          waitTime = `${hours}小时`;
        } else if (minutes > 0) {
          waitTime = `${minutes}分钟`;
        } else {
          waitTime = `${seconds}秒`;
        }
      }
      
      return {
        message: `请求过于频繁，请在${waitTime}后重试`,
        type: 'throttle',
        retryAfter: match ? parseInt(match[1]) : 3600
      };
      
    case 500:
      return {
        message: data.error || '服务器错误，请稍后重试',
        type: 'server'
      };
      
    default:
      return {
        message: data.message || data.error || '操作失败',
        type: 'unknown'
      };
  }
}

// 使用示例
try {
  await licenseService.applyTrialLicense(productId);
} catch (error) {
  const errorInfo = handleLicenseError(error, 'apply');
  
  // 根据错误类型处理
  switch (errorInfo.type) {
    case 'auth':
      // 跳转登录
      router.push('/login');
      break;
      
    case 'throttle':
      // 显示倒计时
      showCountdown(errorInfo.retryAfter);
      break;
      
    default:
      // 显示错误消息
      ElMessage.error(errorInfo.message);
  }
}
```

### 常见错误处理

#### 1. 重复申请

```javascript
// 错误响应
{
  "success": false,
  "errors": {
    "non_field_errors": ["您已经申请过该产品的许可证"]
  }
}

// 前端处理
if (error.response.data.errors?.non_field_errors?.[0].includes('已经申请')) {
  ElMessageBox.confirm(
    '您已经申请过该产品，是否要查看现有许可证？',
    '提示',
    {
      confirmButtonText: '查看许可证',
      cancelButtonText: '取消'
    }
  ).then(() => {
    router.push('/member/my-licenses');
  });
}
```

#### 2. 配额已满

```javascript
// 错误响应
{
  "success": false,
  "errors": {
    "non_field_errors": ["您的试用许可证数量已达上限（1个）"]
  }
}

// 前端处理
if (error.response.data.errors?.non_field_errors?.[0].includes('已达上限')) {
  ElMessageBox.alert(
    '您已有一个试用许可证，如需申请新产品，请先等待现有试用许可证过期。',
    '试用配额已满',
    {
      confirmButtonText: '查看现有许可证',
      callback: () => {
        router.push('/member/my-licenses');
      }
    }
  );
}
```

#### 3. 频率限制

```javascript
// API级别频率限制（429）
if (error.response.status === 429) {
  const detail = error.response.data.detail;
  const match = detail.match(/(\d+) seconds/);
  
  if (match) {
    const seconds = parseInt(match[1]);
    const hours = Math.floor(seconds / 3600);
    
    ElNotification({
      title: '请求过于频繁',
      message: `今日申请次数已达上限（5次），请在${hours}小时后重试`,
      type: 'warning',
      duration: 0  // 不自动关闭
    });
  }
}
```

---

## Web前端开发清单

### 必须实现的功能

- [x] **产品列表页面**
  - 获取可申请产品列表
  - 展示产品信息和试用方案
  - 标记已申请状态
  - 申请按钮

- [x] **申请表单页面**
  - 产品选择
  - 申请原因输入
  - 用户补充信息输入
  - 表单验证
  - 提交申请

- [x] **申请成功页面**
  - 显示许可证密钥（完整）
  - 提供复制功能
  - 显示过期时间和激活配额
  - 引导下载软件

- [x] **许可证列表页面**
  - 显示所有许可证
  - 统计信息（总数、有效数等）
  - 状态筛选
  - 过期提醒

- [x] **激活指南页面**
  - 分步指导
  - 下载链接
  - 激活说明
  - 常见问题

### 可选功能

- [ ] 许可证详情页面
- [ ] 激活设备列表
- [ ] 使用统计图表
- [ ] 续费提醒
- [ ] 导出许可证信息

---

## 前端路由配置

```javascript
// Vue Router 示例
const routes = [
  {
    path: '/member/licenses',
    component: MemberLayout,
    meta: { requiresAuth: true, requiresMember: true },
    children: [
      {
        path: 'available',
        name: 'AvailableProducts',
        component: () => import('@/views/member/licenses/AvailableProducts.vue'),
        meta: { title: '可申请产品' }
      },
      {
        path: 'apply/:productId?',
        name: 'ApplyLicense',
        component: () => import('@/views/member/licenses/ApplyLicense.vue'),
        meta: { title: '申请试用' }
      },
      {
        path: 'my-licenses',
        name: 'MyLicenses',
        component: () => import('@/views/member/licenses/MyLicenses.vue'),
        meta: { title: '我的许可证' }
      },
      {
        path: 'activation-guide/:licenseId',
        name: 'ActivationGuide',
        component: () => import('@/views/member/licenses/ActivationGuide.vue'),
        meta: { title: '激活指南' }
      }
    ]
  }
];
```

---

## 状态管理建议

### Vuex/Pinia Store

```javascript
// stores/licenseStore.js
import { defineStore } from 'pinia';
import licenseService from '@/api/services/licenseService';

export const useLicenseStore = defineStore('license', {
  state: () => ({
    availableProducts: [],
    myLicenses: [],
    licenseStats: {
      count: 0,
      active_count: 0,
      trial_count: 0,
      expiring_soon_count: 0
    },
    loading: false
  }),
  
  getters: {
    activeLicenses: (state) => {
      return state.myLicenses.filter(l => l.status === 'active');
    },
    
    expiringSoonLicenses: (state) => {
      return state.myLicenses.filter(l => 
        l.status === 'active' && 
        l.days_until_expiry !== null && 
        l.days_until_expiry <= 7
      );
    },
    
    hasActiveTrial: (state) => {
      return state.myLicenses.some(l => 
        l.status === 'active' && l.plan_type === 'trial'
      );
    }
  },
  
  actions: {
    async fetchAvailableProducts() {
      this.loading = true;
      try {
        const data = await licenseService.getAvailableProducts();
        this.availableProducts = data.products;
      } finally {
        this.loading = false;
      }
    },
    
    async applyLicense(productId, reason, userInfo) {
      const result = await licenseService.applyTrialLicense(productId, reason, userInfo);
      
      // 申请成功后刷新许可证列表
      if (result.success) {
        await this.fetchMyLicenses();
      }
      
      return result;
    },
    
    async fetchMyLicenses(filters = {}) {
      this.loading = true;
      try {
        const data = await licenseService.getMyLicenses(filters);
        this.myLicenses = data.licenses;
        this.licenseStats = {
          count: data.count,
          active_count: data.active_count,
          trial_count: data.trial_count,
          expiring_soon_count: data.expiring_soon_count
        };
      } finally {
        this.loading = false;
      }
    }
  }
});
```

---

## 导航和提示

### 顶部提醒

在应用顶部显示即将过期的许可证提醒：

```vue
<template>
  <el-alert
    v-if="expiringSoonCount > 0"
    type="warning"
    :closable="false"
    show-icon
  >
    <template #title>
      您有 {{ expiringSoonCount }} 个许可证即将过期
      <el-link type="primary" @click="goToLicenses">
        查看详情
      </el-link>
    </template>
  </el-alert>
</template>

<script setup>
import { computed } from 'vue';
import { useLicenseStore } from '@/stores/licenseStore';
import { useRouter } from 'vue-router';

const licenseStore = useLicenseStore();
const router = useRouter();

const expiringSoonCount = computed(() => 
  licenseStore.licenseStats.expiring_soon_count
);

const goToLicenses = () => {
  router.push('/member/my-licenses');
};

// 组件挂载时获取许可证数据
onMounted(() => {
  licenseStore.fetchMyLicenses();
});
</script>
```

---

## 客户端软件开发建议

如果你需要开发配套的客户端软件（Electron/Qt/等），建议实现以下功能：

### 1. 许可证输入界面

```javascript
// Electron示例：许可证输入窗口
function createLicenseInputWindow() {
  const win = new BrowserWindow({
    width: 500,
    height: 300,
    webPreferences: {
      nodeIntegration: true
    }
  });
  
  win.loadFile('license-input.html');
}
```

### 2. 激活逻辑

```javascript
// 主进程处理激活
ipcMain.handle('activate-license', async (event, licenseKey) => {
  try {
    // 收集硬件信息
    const hardwareInfo = await collectHardwareInfo();
    
    // 调用激活API
    const response = await axios.post('http://server.com/api/v1/licenses/activate/', {
      license_key: licenseKey,
      hardware_info: hardwareInfo,
      client_info: {
        app_version: app.getVersion(),
        app_name: app.getName()
      }
    });
    
    if (response.data.success) {
      // 保存激活码到本地
      const activationCode = response.data.data.activation_code;
      await saveToConfig('activation_code', activationCode);
      await saveToConfig('license_expires_at', response.data.data.expires_at);
      
      return { success: true };
    }
    
    return { success: false, error: response.data.error };
  } catch (error) {
    return { success: false, error: error.message };
  }
});
```

### 3. 启动时验证

```javascript
// 应用启动时验证许可证
app.on('ready', async () => {
  const activationCode = await loadFromConfig('activation_code');
  
  if (!activationCode) {
    // 未激活，显示激活窗口
    createLicenseInputWindow();
    return;
  }
  
  // 验证激活状态
  const isValid = await verifyActivation(activationCode);
  
  if (isValid) {
    // 许可证有效，启动主窗口
    createMainWindow();
    
    // 启动心跳
    startHeartbeat(activationCode);
  } else {
    // 许可证无效，显示重新激活窗口
    createLicenseInputWindow();
  }
});
```

---

## 完成！

恭喜！您已经了解了Member许可证API的完整集成流程。

### 快速检查清单

Web前端：
- [ ] 产品列表页面
- [ ] 申请表单页面
- [ ] 许可证列表页面
- [ ] 激活指南页面
- [ ] 错误处理

客户端软件（如需开发）：
- [ ] 许可证输入界面
- [ ] 硬件信息收集
- [ ] 激活API调用
- [ ] 激活状态验证
- [ ] 心跳定时器
- [ ] 本地配置存储

### 后续支持

- Swagger文档：`http://localhost:8000/api/v1/docs/`
- ReDoc文档：`http://localhost:8000/api/v1/redoc/`
- 联系后端团队

祝开发顺利！🎉

