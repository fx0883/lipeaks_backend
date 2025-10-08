# 申请试用许可证 API

本文档详细说明申请试用许可证的API接口。

---

## API概述

### 基本信息

```
POST /api/v1/licenses/member/apply/
```

**功能**：Member用户申请指定产品的试用许可证

**权限要求**：
- 需要JWT认证
- 必须是Member用户身份  
- 具有试用许可证申请权限
- 用户和租户状态必须为活跃

**频率限制**：5次/天

**内容类型**：`application/json`

---

## 请求说明

### 请求头

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 请求参数

#### 必填字段

| 字段 | 类型 | 说明 | 验证规则 |
|------|------|------|---------|
| product_id | integer | 产品ID | 必须是存在的产品ID，且该产品有可用的试用方案 |

#### 可选字段

| 字段 | 类型 | 说明 | 验证规则 |
|------|------|------|---------|
| reason | string | 申请原因 | 最多500个字符，默认为"试用版申请" |
| user_info | object | 用户补充信息 | JSON对象，包含公司、职位、用途等 |

#### user_info对象（可选）

| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|---------|
| company | string | 否 | 公司名称 | 最多100个字符 |
| job_title | string | 否 | 职位 | 无限制 |
| phone | string | 否 | 联系电话 | 最多20个字符 |
| intended_use | string | 否 | 使用用途 | 最多500个字符 |

### 请求体示例

#### 示例1：最简申请（仅产品ID）

```json
{
  "product_id": 1
}
```

#### 示例2：带申请原因

```json
{
  "product_id": 1,
  "reason": "我想试用这个PDF压缩工具来处理项目文档"
}
```

#### 示例3：完整信息申请

```json
{
  "product_id": 1,
  "reason": "用于公司项目开发测试",
  "user_info": {
    "company": "ABC科技有限公司",
    "job_title": "前端开发工程师",
    "phone": "13900139000",
    "intended_use": "用于开发PDF文档处理功能，需要测试压缩效果和兼容性"
  }
}
```

### cURL示例

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/member/apply/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "reason": "试用申请",
    "user_info": {
      "company": "我的公司",
      "job_title": "开发工程师"
    }
  }'
```

---

## 响应说明

### 成功响应

**状态码**：`201 Created`

**响应体**：

```json
{
  "success": true,
  "message": "试用许可证申请成功",
  "data": {
    "license_id": 123,
    "assignment_id": 456,
    "license_key": "ABCDE-FGHIJ-KLMNO-PQRST-UVWXY",
    "expires_at": "2025-11-05T10:30:00Z",
    "product_name": "PDF压缩工具",
    "plan_name": "试用版",
    "max_activations": 1
  }
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 成功消息 |
| data | object | 许可证数据对象 |

#### data对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| license_id | integer | 许可证ID |
| assignment_id | integer | 分配关系ID |
| license_key | string | **完整的许可证密钥**（重要！仅此处返回） |
| expires_at | string | 过期时间（ISO 8601格式） |
| product_name | string | 产品名称 |
| plan_name | string | 方案名称 |
| max_activations | integer | 最大可激活设备数 |

⚠️ **重要**：`license_key`是完整的许可证密钥，仅在申请成功时返回一次，前端必须妥善保存或提示用户记录！

---

## 错误响应

### 400 参数验证错误

#### 场景1：缺少产品ID

```json
{
  "success": false,
  "errors": {
    "product_id": ["该字段为必填项。"]
  }
}
```

#### 场景2：产品不存在或不可用

```json
{
  "success": false,
  "errors": {
    "product_id": ["产品不存在或不可用"]
  }
}
```

#### 场景3：产品没有试用方案

```json
{
  "success": false,
  "errors": {
    "product_id": ["该产品没有可用的试用方案"]
  }
}
```

#### 场景4：user_info字段过长

```json
{
  "success": false,
  "errors": {
    "user_info": ["公司名称过长"]
  }
}
```

### 400 业务规则限制

#### 场景1：重复申请

```json
{
  "success": false,
  "errors": {
    "non_field_errors": ["您已经申请过该产品的许可证"]
  }
}
```

#### 场景2：24小时内申请次数过多

```json
{
  "success": false,
  "errors": {
    "non_field_errors": ["24小时内申请次数过多，请稍后再试"]
  }
}
```

#### 场景3：试用许可证配额已满

```json
{
  "success": false,
  "errors": {
    "non_field_errors": ["您的试用许可证数量已达上限（1个）"]
  }
}
```

### 401 未认证

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 权限不足

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**可能原因**：
- 不是Member用户
- 用户状态不活跃
- 没有申请权限

### 429 请求频率限制

```json
{
  "detail": "Request was throttled. Expected available in 86400 seconds."
}
```

**说明**：超过5次/天的申请限制，需要等待24小时

### 500 服务器内部错误

```json
{
  "success": false,
  "error": "申请处理失败，请稍后重试",
  "code": "APPLICATION_ERROR"
}
```

---

## 前端实现示例

### Vue 3 完整示例

```vue
<template>
  <div class="apply-license-page">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="page-title">申请试用许可证</span>
      </template>
    </el-page-header>
    
    <el-card class="apply-form-card">
      <el-form
        :model="formData"
        :rules="rules"
        ref="formRef"
        label-width="120px"
      >
        <el-form-item label="选择产品" prop="product_id">
          <el-select
            v-model="formData.product_id"
            placeholder="请选择要申请的产品"
            @change="onProductChange"
            style="width: 100%;"
          >
            <el-option
              v-for="product in products"
              :key="product.id"
              :label="product.name"
              :value="product.id"
              :disabled="product.already_applied"
            >
              <div class="product-option">
                <span>{{ product.name }}</span>
                <el-tag v-if="product.already_applied" size="small" type="info">
                  已申请
                </el-tag>
                <span v-else class="trial-days">
                  {{ product.trial_plan?.default_validity_days }}天试用
                </span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <!-- 产品信息预览 -->
        <el-alert
          v-if="selectedProduct"
          :title="`${selectedProduct.name} - ${selectedProduct.trial_plan?.name}`"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <p>{{ selectedProduct.description }}</p>
          <p v-if="selectedProduct.trial_plan">
            <strong>试用期限：</strong>{{ selectedProduct.trial_plan.default_validity_days }}天 |
            <strong>可激活设备：</strong>{{ selectedProduct.trial_plan.default_max_activations }}个
          </p>
        </el-alert>
        
        <el-form-item label="申请原因" prop="reason">
          <el-input
            v-model="formData.reason"
            type="textarea"
            :rows="3"
            placeholder="请简要说明申请原因（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-divider content-position="left">补充信息（可选）</el-divider>
        
        <el-form-item label="公司名称">
          <el-input
            v-model="formData.user_info.company"
            placeholder="请输入公司名称"
            maxlength="100"
          />
        </el-form-item>
        
        <el-form-item label="职位">
          <el-input
            v-model="formData.user_info.job_title"
            placeholder="请输入您的职位"
          />
        </el-form-item>
        
        <el-form-item label="联系电话">
          <el-input
            v-model="formData.user_info.phone"
            placeholder="请输入联系电话"
            maxlength="20"
          />
        </el-form-item>
        
        <el-form-item label="使用用途">
          <el-input
            v-model="formData.user_info.intended_use"
            type="textarea"
            :rows="3"
            placeholder="请描述您的使用用途"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            @click="submitApplication"
            :loading="submitting"
            :disabled="!formData.product_id"
          >
            {{ submitting ? '提交中...' : '提交申请' }}
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 成功对话框 -->
    <el-dialog
      v-model="successDialogVisible"
      title="申请成功"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-result icon="success" title="试用许可证申请成功！">
        <template #sub-title>
          <p>您的许可证密钥如下，请妥善保管：</p>
        </template>
        <template #extra>
          <div class="license-key-box">
            <el-input
              v-model="licenseKey"
              readonly
              size="large"
            >
              <template #append>
                <el-button @click="copyLicenseKey" :icon="DocumentCopy">
                  复制
                </el-button>
              </template>
            </el-input>
          </div>
          
          <el-descriptions :column="2" border style="margin-top: 20px;">
            <el-descriptions-item label="产品">
              {{ applicationResult.product_name }}
            </el-descriptions-item>
            <el-descriptions-item label="方案">
              {{ applicationResult.plan_name }}
            </el-descriptions-item>
            <el-descriptions-item label="过期时间">
              {{ formatDate(applicationResult.expires_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="可激活设备">
              {{ applicationResult.max_activations }} 个
            </el-descriptions-item>
          </el-descriptions>
          
          <div style="margin-top: 20px;">
            <el-button type="primary" @click="goToMyLicenses">
              查看我的许可证
            </el-button>
            <el-button @click="successDialogVisible = false">
              关闭
            </el-button>
          </div>
        </template>
      </el-result>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { DocumentCopy } from '@element-plus/icons-vue';
import axios from 'axios';
import dayjs from 'dayjs';

const router = useRouter();
const route = useRoute();

// 数据
const products = ref([]);
const formRef = ref(null);
const submitting = ref(false);
const successDialogVisible = ref(false);
const licenseKey = ref('');
const applicationResult = ref(null);

// 表单数据
const formData = ref({
  product_id: route.params.productId ? parseInt(route.params.productId) : null,
  reason: '',
  user_info: {
    company: '',
    job_title: '',
    phone: '',
    intended_use: ''
  }
});

// 表单验证规则
const rules = {
  product_id: [
    { required: true, message: '请选择产品', trigger: 'change' }
  ],
  reason: [
    { max: 500, message: '申请原因不能超过500个字符', trigger: 'blur' }
  ]
};

// 选中的产品
const selectedProduct = computed(() => {
  if (!formData.value.product_id) return null;
  return products.value.find(p => p.id === formData.value.product_id);
});

// 获取产品列表
const fetchProducts = async () => {
  try {
    const response = await axios.get('/api/v1/licenses/member/available-products/');
    products.value = response.data.data.products;
  } catch (error) {
    ElMessage.error('获取产品列表失败');
  }
};

// 产品选择变化
const onProductChange = (productId) => {
  const product = products.value.find(p => p.id === productId);
  
  if (product && product.already_applied) {
    ElMessage.warning('您已经申请过该产品');
    formData.value.product_id = null;
  }
};

// 提交申请
const submitApplication = async () => {
  try {
    // 表单验证
    await formRef.value.validate();
    
    // 二次确认
    await ElMessageBox.confirm(
      `确定要申请 "${selectedProduct.value.name}" 的试用许可证吗？`,
      '确认申请',
      {
        confirmButtonText: '确定申请',
        cancelButtonText: '取消',
        type: 'info'
      }
    );
    
    submitting.value = true;
    
    // 准备请求数据（移除空字段）
    const requestData = {
      product_id: formData.value.product_id
    };
    
    if (formData.value.reason) {
      requestData.reason = formData.value.reason;
    }
    
    // 检查user_info是否有值
    const userInfo = formData.value.user_info;
    const hasUserInfo = Object.values(userInfo).some(v => v && v.trim());
    
    if (hasUserInfo) {
      // 只发送有值的字段
      requestData.user_info = {};
      for (const [key, value] of Object.entries(userInfo)) {
        if (value && value.trim()) {
          requestData.user_info[key] = value.trim();
        }
      }
    }
    
    // 发送申请请求
    const response = await axios.post(
      '/api/v1/licenses/member/apply/',
      requestData
    );
    
    // 保存结果
    applicationResult.value = response.data.data;
    licenseKey.value = response.data.data.license_key;
    
    // 显示成功对话框
    successDialogVisible.value = true;
    
    ElMessage.success('申请成功！');
    
  } catch (error) {
    if (error === 'cancel') {
      // 用户取消确认
      return;
    }
    
    console.error('申请失败:', error);
    
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 400) {
        // 参数或业务规则错误
        if (data.errors) {
          // 显示字段错误
          const errorMessages = [];
          
          for (const [field, messages] of Object.entries(data.errors)) {
            if (field === 'non_field_errors') {
              errorMessages.push(...messages);
            } else {
              errorMessages.push(`${field}: ${messages.join(', ')}`);
            }
          }
          
          ElMessage.error(errorMessages.join('\n'));
        } else {
          ElMessage.error(data.error || '申请失败');
        }
      } else if (status === 401) {
        ElMessage.error('登录已过期，请重新登录');
        router.push('/login');
      } else if (status === 403) {
        ElMessage.error('权限不足，此功能仅限Member用户使用');
      } else if (status === 429) {
        const match = data.detail.match(/(\d+) seconds/);
        if (match) {
          const hours = Math.floor(parseInt(match[1]) / 3600);
          ElMessage.error(`申请过于频繁，请在${hours}小时后重试`);
        } else {
          ElMessage.error('申请过于频繁，请稍后重试');
        }
      } else {
        ElMessage.error(data.error || '申请失败');
      }
    } else {
      ElMessage.error('网络连接失败');
    }
  } finally {
    submitting.value = false;
  }
};

// 复制许可证密钥
const copyLicenseKey = async () => {
  try {
    await navigator.clipboard.writeText(licenseKey.value);
    ElMessage.success('许可证密钥已复制到剪贴板');
  } catch (error) {
    // 降级方案：使用传统方法
    const input = document.createElement('input');
    input.value = licenseKey.value;
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    document.body.removeChild(input);
    ElMessage.success('许可证密钥已复制');
  }
};

// 跳转到我的许可证
const goToMyLicenses = () => {
  successDialogVisible.value = false;
  router.push('/member/my-licenses');
};

// 重置表单
const resetForm = () => {
  formRef.value.resetFields();
  formData.value.user_info = {
    company: '',
    job_title: '',
    phone: '',
    intended_use: ''
  };
};

// 返回
const goBack = () => {
  router.back();
};

// 格式化日期
const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss');
};

// 组件挂载时获取产品列表
onMounted(() => {
  fetchProducts();
});
</script>

<style scoped>
.apply-license-page {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.apply-form-card {
  margin-top: 20px;
}

.product-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.trial-days {
  color: #409EFF;
  font-size: 12px;
}

.license-key-box {
  margin: 20px 0;
}

.license-key-box .el-input {
  font-family: 'Courier New', monospace;
  font-size: 16px;
  font-weight: bold;
}
</style>
```

---

## 使用流程

### 完整的申请流程

```javascript
// 1. 获取可申请产品列表
async function step1_getProducts() {
  const response = await axios.get('/api/v1/licenses/member/available-products/');
  const products = response.data.data.products;
  
  // 过滤出未申请的产品
  const availableProducts = products.filter(p => !p.already_applied && p.trial_plan);
  
  return availableProducts;
}

// 2. 用户选择产品并填写信息
function step2_fillForm(productId) {
  return {
    product_id: productId,
    reason: '试用申请',
    user_info: {
      company: '我的公司',
      job_title: '开发工程师',
      intended_use: '用于项目开发'
    }
  };
}

// 3. 提交申请
async function step3_submitApplication(formData) {
  try {
    const response = await axios.post('/api/v1/licenses/member/apply/', formData);
    
    if (response.data.success) {
      const result = response.data.data;
      
      // 重要：保存许可证密钥
      saveLicenseKey(result.license_key);
      
      // 显示成功信息
      showSuccess({
        message: '申请成功！',
        licenseKey: result.license_key,
        expiresAt: result.expires_at
      });
      
      return result;
    }
  } catch (error) {
    handleError(error);
    throw error;
  }
}

// 4. 保存许可证密钥（建议让用户主动复制）
function saveLicenseKey(licenseKey) {
  // 方案1：提供复制功能
  showCopyDialog(licenseKey);
  
  // 方案2：下载为文本文件
  downloadAsText(licenseKey, 'license-key.txt');
  
  // 方案3：显示二维码
  showQRCode(licenseKey);
}

// 复制到剪贴板
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('复制失败:', error);
    return false;
  }
}

// 下载为文本文件
function downloadAsText(content, filename) {
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
```

---

## 前端开发建议

### 功能清单

- [x] 产品选择器
- [x] 产品信息预览
- [x] 申请原因输入
- [x] 用户补充信息输入（可选）
- [x] 表单验证
- [x] 二次确认
- [x] Loading状态
- [x] 成功后显示许可证密钥
- [x] 密钥复制功能
- [x] 错误处理
- [x] 跳转到许可证列表

### UI/UX建议

1. **产品预览**：选择产品后立即展示产品详情和试用方案
2. **二次确认**：提交前弹窗确认，避免误操作
3. **密钥保护**：成功后突出显示许可证密钥，提供复制功能
4. **引导操作**：提示用户保存密钥，并引导下载软件
5. **友好提示**：清晰的错误提示和操作建议

### 防重复提交

```javascript
const submitLock = ref(false);

async function submitWithLock() {
  if (submitLock.value) {
    ElMessage.warning('请勿重复提交');
    return;
  }
  
  submitLock.value = true;
  try {
    await submitApplication();
  } finally {
    // 成功后保持锁定，防止重复申请
    // submitLock.value = false;
  }
}
```

---

## 下一步

继续阅读：

📕 **my_licenses_api.md** - 查看我的许可证API

