# 前端更新指南：多试用方案支持

**更新日期**: 2025-10-06  
**重要程度**: 🔴 高（API响应结构变更）  
**影响范围**: 产品列表和申请流程

---

## 📢 重要变更

### API响应结构变更

**影响的API**: `GET /api/v1/licenses/member/available-products/`

#### 变更前（旧版本）

```json
{
  "id": 6,
  "name": "Leaks_compress",
  "trial_plan": {                    // ← 单个对象
    "id": 12,
    "name": "Trial",
    "default_validity_days": 3
  }
}
```

#### 变更后（新版本）

```json
{
  "id": 6,
  "name": "Leaks_compress",
  "trial_plans": [                   // ← 改为数组
    {
      "id": 13,
      "name": "hello2",
      "default_validity_days": 11,
      "is_recommended": true         // ← 新增：推荐标记
    },
    {
      "id": 12,
      "name": "Trial",
      "default_validity_days": 3,
      "is_recommended": false
    }
  ]
}
```

### 申请API新增参数

**影响的API**: `POST /api/v1/licenses/member/apply/`

#### 新增参数

```json
{
  "product_id": 6,
  "plan_id": 13,        // ← 新增：可选参数，指定要申请的方案ID
  "reason": "申请原因",
  "user_info": {...}
}
```

**说明**：
- `plan_id` 为可选参数
- 如果不提供，系统自动选择有效期最长的方案
- 如果产品只有1个试用方案，可以不提供

---

## 🔧 前端必须修改的代码

### 1. 数据结构适配

#### 旧代码（需要修改）

```javascript
// ❌ 旧代码：假设trial_plan是对象
const product = response.data.data.products[0];

if (product.trial_plan) {
  const days = product.trial_plan.default_validity_days;
  console.log(`试用期：${days}天`);
}
```

#### 新代码（兼容两种情况）

```javascript
// ✅ 新代码：兼容单个和多个方案
const product = response.data.data.products[0];

// 获取试用方案（兼容数组和对象）
const trialPlans = Array.isArray(product.trial_plans) 
  ? product.trial_plans 
  : (product.trial_plans ? [product.trial_plans] : []);

if (trialPlans.length > 0) {
  console.log(`该产品有${trialPlans.length}个试用方案`);
  
  // 获取推荐方案
  const recommendedPlan = trialPlans.find(p => p.is_recommended) || trialPlans[0];
  console.log(`推荐方案：${recommendedPlan.name}，${recommendedPlan.default_validity_days}天`);
}
```

---

### 2. UI展示修改

#### 方案A：简单展示（显示推荐方案）

```vue
<template>
  <div class="product-card">
    <h3>{{ product.name }}</h3>
    <p>{{ product.description }}</p>
    
    <!-- 显示推荐方案 -->
    <div v-if="recommendedPlan" class="trial-info">
      <el-tag type="success">推荐方案</el-tag>
      <p>{{ recommendedPlan.name }}</p>
      <p>
        <el-icon><Clock /></el-icon>
        {{ recommendedPlan.default_validity_days }}天试用
      </p>
      <p>
        <el-icon><Monitor /></el-icon>
        {{ recommendedPlan.default_max_activations }}个设备
      </p>
      
      <!-- 如果有多个方案，显示提示 -->
      <el-link
        v-if="trialPlans.length > 1"
        type="primary"
        @click="showAllPlans = !showAllPlans"
      >
        {{ showAllPlans ? '收起' : `查看其他${trialPlans.length - 1}个方案` }}
      </el-link>
    </div>
    
    <el-button
      type="primary"
      @click="applyWithRecommended"
      :disabled="product.already_applied"
    >
      {{ product.already_applied ? '已申请' : '申请试用' }}
    </el-button>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';

const props = defineProps(['product']);
const showAllPlans = ref(false);

// 获取所有试用方案
const trialPlans = computed(() => {
  if (!props.product.trial_plans) return [];
  return Array.isArray(props.product.trial_plans) 
    ? props.product.trial_plans 
    : [props.product.trial_plans];
});

// 获取推荐方案
const recommendedPlan = computed(() => {
  return trialPlans.value.find(p => p.is_recommended) || trialPlans.value[0];
});

// 使用推荐方案申请
const applyWithRecommended = () => {
  if (recommendedPlan.value) {
    emit('apply', props.product.id, recommendedPlan.value.id);
  }
};
</script>
```

---

#### 方案B：完整展示（让用户选择）

```vue
<template>
  <div class="product-card">
    <h3>{{ product.name }}</h3>
    <p>{{ product.description }}</p>
    
    <!-- 单个方案：直接显示 -->
    <div v-if="trialPlans.length === 1" class="single-plan">
      <div class="plan-info">
        <h4>{{ trialPlans[0].name }}</h4>
        <p>
          <el-icon><Clock /></el-icon>
          试用期限：{{ trialPlans[0].default_validity_days }}天
        </p>
        <p>
          <el-icon><Monitor /></el-icon>
          可激活设备：{{ trialPlans[0].default_max_activations }}个
        </p>
      </div>
    </div>
    
    <!-- 多个方案：提供选择 -->
    <div v-else-if="trialPlans.length > 1" class="multiple-plans">
      <h4>选择试用方案：</h4>
      
      <el-radio-group v-model="selectedPlanId" class="plan-selector">
        <el-radio
          v-for="plan in trialPlans"
          :key="plan.id"
          :label="plan.id"
          class="plan-option"
        >
          <div class="plan-card">
            <div class="plan-header">
              <span class="plan-name">{{ plan.name }}</span>
              <el-tag
                v-if="plan.is_recommended"
                type="success"
                size="small"
                effect="dark"
              >
                推荐
              </el-tag>
            </div>
            
            <div class="plan-details">
              <div class="detail-item">
                <el-icon><Clock /></el-icon>
                <span>{{ plan.default_validity_days }} 天</span>
              </div>
              <div class="detail-item">
                <el-icon><Monitor /></el-icon>
                <span>{{ plan.default_max_activations }} 设备</span>
              </div>
            </div>
            
            <!-- 显示功能差异（如果有） -->
            <div v-if="plan.features && Object.keys(plan.features).length > 0" class="features">
              <el-tag
                v-for="(value, key) in plan.features"
                :key="key"
                size="small"
              >
                {{ key }}: {{ value }}
              </el-tag>
            </div>
          </div>
        </el-radio>
      </el-radio-group>
    </div>
    
    <el-button
      type="primary"
      @click="handleApply"
      :disabled="product.already_applied || !selectedPlanId"
      style="width: 100%; margin-top: 15px;"
    >
      {{ product.already_applied ? '已申请' : '立即申请' }}
    </el-button>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { Clock, Monitor } from '@element-plus/icons-vue';

const props = defineProps({
  product: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['apply']);

// 获取所有试用方案
const trialPlans = computed(() => {
  if (!props.product.trial_plans) return [];
  return Array.isArray(props.product.trial_plans) 
    ? props.product.trial_plans 
    : [props.product.trial_plans];
});

// 选中的方案ID
const selectedPlanId = ref(null);

// 默认选择推荐方案
watch(() => trialPlans.value, (plans) => {
  if (plans.length > 0) {
    const recommended = plans.find(p => p.is_recommended);
    selectedPlanId.value = recommended ? recommended.id : plans[0].id;
  }
}, { immediate: true });

// 申请
const handleApply = () => {
  emit('apply', props.product.id, selectedPlanId.value);
};
</script>

<style scoped>
.product-card {
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  padding: 20px;
}

.single-plan {
  background-color: #F5F7FA;
  padding: 15px;
  border-radius: 4px;
  margin: 15px 0;
}

.multiple-plans h4 {
  margin: 15px 0 10px 0;
  font-size: 14px;
  color: #606266;
}

.plan-selector {
  width: 100%;
}

.plan-option {
  width: 100%;
  margin: 10px 0;
}

.plan-card {
  border: 1px solid #DCDFE6;
  border-radius: 4px;
  padding: 12px;
  width: 100%;
  background-color: #FAFAFA;
  transition: all 0.3s;
}

.plan-option.is-checked .plan-card {
  border-color: #409EFF;
  background-color: #ECF5FF;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.plan-name {
  font-weight: 600;
  font-size: 15px;
}

.plan-details {
  display: flex;
  gap: 20px;
  margin: 8px 0;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
  font-size: 14px;
}

.features {
  margin-top: 10px;
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}
</style>
```

---

### 3. API调用修改

#### 申请许可证

```javascript
// 旧代码
async function applyLicense(productId, reason, userInfo) {
  const response = await axios.post('/api/v1/licenses/member/apply/', {
    product_id: productId,
    reason,
    user_info: userInfo
  });
  return response.data;
}

// ✅ 新代码：支持指定方案ID
async function applyLicense(productId, planId, reason, userInfo) {
  const requestData = {
    product_id: productId,
    reason,
    user_info: userInfo
  };
  
  // 如果指定了方案ID，添加到请求中
  if (planId) {
    requestData.plan_id = planId;
  }
  
  const response = await axios.post('/api/v1/licenses/member/apply/', requestData);
  return response.data;
}

// 使用示例
// 方式1：指定方案ID
await applyLicense(6, 13, '申请原因', {...});

// 方式2：不指定方案（自动选择最优）
await applyLicense(6, null, '申请原因', {...});
```

---

### 4. 完整的产品列表组件

```vue
<template>
  <div class="available-products-page">
    <el-page-header @back="goBack">
      <template #content>
        <span class="page-title">可申请的试用产品</span>
      </template>
    </el-page-header>
    
    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>
    
    <!-- 产品列表 -->
    <div v-else class="products-container">
      <el-empty v-if="products.length === 0" description="暂无可申请的试用产品" />
      
      <el-row :gutter="20">
        <el-col
          v-for="product in validProducts"
          :key="product.id"
          :xs="24"
          :sm="12"
          :md="8"
        >
          <el-card class="product-card" shadow="hover">
            <!-- 产品头部 -->
            <template #header>
              <div class="card-header">
                <span class="product-name">{{ product.name }}</span>
                <el-tag v-if="product.already_applied" type="success">
                  已申请
                </el-tag>
              </div>
            </template>
            
            <!-- 产品信息 -->
            <div class="product-info">
              <p class="version">版本：{{ product.version }}</p>
              <p class="description">{{ product.description }}</p>
            </div>
            
            <!-- 试用方案 -->
            <div v-if="getTrialPlans(product).length > 0" class="plans-section">
              <el-divider />
              
              <!-- 单个方案 -->
              <div v-if="getTrialPlans(product).length === 1" class="single-plan">
                <h4>试用方案</h4>
                <div class="plan-item">
                  <p>{{ getTrialPlans(product)[0].name }}</p>
                  <p class="plan-detail">
                    <el-icon><Clock /></el-icon>
                    {{ getTrialPlans(product)[0].default_validity_days }} 天 · 
                    <el-icon><Monitor /></el-icon>
                    {{ getTrialPlans(product)[0].default_max_activations }} 设备
                  </p>
                </div>
              </div>
              
              <!-- 多个方案 -->
              <div v-else class="multiple-plans">
                <h4>选择试用方案</h4>
                <el-select
                  v-model="selectedPlans[product.id]"
                  placeholder="选择方案"
                  style="width: 100%;"
                  @change="onPlanChange(product.id)"
                >
                  <el-option
                    v-for="plan in getTrialPlans(product)"
                    :key="plan.id"
                    :label="plan.name"
                    :value="plan.id"
                  >
                    <div class="option-content">
                      <span>{{ plan.name }}</span>
                      <el-tag v-if="plan.is_recommended" size="small" type="success">
                        推荐
                      </el-tag>
                    </div>
                    <div class="option-detail">
                      {{ plan.default_validity_days }}天 / 
                      {{ plan.default_max_activations }}设备
                    </div>
                  </el-option>
                </el-select>
                
                <!-- 选中方案的详细信息 -->
                <div v-if="getSelectedPlan(product)" class="selected-plan-info">
                  <el-alert type="info" :closable="false">
                    <p>
                      <strong>{{ getSelectedPlan(product).name }}</strong>
                    </p>
                    <p>
                      试用期限：{{ getSelectedPlan(product).default_validity_days }}天 · 
                      可激活：{{ getSelectedPlan(product).default_max_activations }}个设备
                    </p>
                  </el-alert>
                </div>
              </div>
            </div>
            
            <!-- 申请按钮 -->
            <template #footer>
              <el-button
                type="primary"
                :disabled="product.already_applied"
                @click="handleApply(product)"
                style="width: 100%;"
              >
                {{ product.already_applied ? '已申请' : '申请试用' }}
              </el-button>
            </template>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Clock, Monitor } from '@element-plus/icons-vue';
import axios from 'axios';

const router = useRouter();

// 数据
const loading = ref(false);
const products = ref([]);
const selectedPlans = ref({});  // 存储每个产品选中的方案ID

// 过滤出有试用方案的产品
const validProducts = computed(() => {
  return products.value.filter(p => {
    const plans = getTrialPlans(p);
    return plans.length > 0;
  });
});

// 获取产品的试用方案（兼容数组和对象）
const getTrialPlans = (product) => {
  if (!product.trial_plans) return [];
  return Array.isArray(product.trial_plans) 
    ? product.trial_plans 
    : [product.trial_plans];
};

// 获取选中的方案
const getSelectedPlan = (product) => {
  const planId = selectedPlans.value[product.id];
  if (!planId) return null;
  
  const plans = getTrialPlans(product);
  return plans.find(p => p.id === planId);
};

// 获取产品列表
const fetchProducts = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/v1/licenses/member/available-products/');
    
    if (response.data.success) {
      products.value = response.data.data.products;
      
      // 初始化选中的方案（默认选择推荐方案）
      products.value.forEach(product => {
        const plans = getTrialPlans(product);
        if (plans.length > 0) {
          const recommended = plans.find(p => p.is_recommended);
          selectedPlans.value[product.id] = recommended ? recommended.id : plans[0].id;
        }
      });
    }
  } catch (error) {
    console.error('获取产品列表失败:', error);
    ElMessage.error('获取产品列表失败');
  } finally {
    loading.value = false;
  }
};

// 方案选择变化
const onPlanChange = (productId) => {
  console.log(`产品${productId}选择了方案${selectedPlans.value[productId]}`);
};

// 申请产品
const handleApply = (product) => {
  const planId = selectedPlans.value[product.id];
  
  if (!planId) {
    ElMessage.warning('请选择试用方案');
    return;
  }
  
  router.push({
    name: 'ApplyLicense',
    params: { productId: product.id },
    query: { 
      planId: planId,
      productName: product.name 
    }
  });
};

// 返回
const goBack = () => {
  router.back();
};

onMounted(() => {
  fetchProducts();
});
</script>

<style scoped>
.available-products-page {
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.loading-container {
  padding: 40px 0;
  text-align: center;
}

.products-container {
  margin-top: 20px;
}

.product-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-name {
  font-size: 16px;
  font-weight: 600;
}

.product-info .version {
  color: #909399;
  font-size: 12px;
  margin: 0 0 5px 0;
}

.product-info .description {
  margin: 0 0 10px 0;
  line-height: 1.6;
  color: #606266;
}

.plans-section h4 {
  margin: 10px 0;
  font-size: 14px;
  color: #303133;
}

.single-plan .plan-info {
  background-color: #F5F7FA;
  padding: 12px;
  border-radius: 4px;
}

.single-plan .plan-info h4 {
  margin: 0 0 8px 0;
  color: #409EFF;
}

.single-plan .plan-info p {
  margin: 5px 0;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
}

.multiple-plans {
  margin-top: 10px;
}

.plan-selector {
  width: 100%;
}

.plan-option {
  width: 100%;
  margin: 8px 0;
}

.plan-card {
  width: 100%;
  padding: 12px;
  border: 1px solid #DCDFE6;
  border-radius: 4px;
  background-color: #FAFAFA;
  transition: all 0.3s;
}

.plan-option.is-checked .plan-card {
  border-color: #409EFF;
  background-color: #ECF5FF;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.plan-name {
  font-weight: 600;
  color: #303133;
}

.plan-details {
  display: flex;
  gap: 15px;
  margin: 8px 0;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
  font-size: 13px;
}

.features {
  margin-top: 8px;
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.selected-plan-info {
  margin-top: 10px;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-detail {
  color: #909399;
  font-size: 12px;
  margin-top: 2px;
}
</style>
```

---

### 5. 申请表单组件修改

```vue
<template>
  <div class="apply-form-page">
    <h2>申请试用许可证</h2>
    
    <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
      <!-- 产品选择 -->
      <el-form-item label="产品" prop="product_id">
        <el-select
          v-model="formData.product_id"
          placeholder="选择产品"
          @change="onProductChange"
          style="width: 100%;"
        >
          <el-option
            v-for="product in products"
            :key="product.id"
            :label="product.name"
            :value="product.id"
            :disabled="product.already_applied"
          />
        </el-select>
      </el-form-item>
      
      <!-- 方案选择（当产品有多个试用方案时显示） -->
      <el-form-item
        v-if="currentProduct && getTrialPlans(currentProduct).length > 1"
        label="试用方案"
        prop="plan_id"
      >
        <el-radio-group v-model="formData.plan_id" class="plan-radio-group">
          <el-radio
            v-for="plan in getTrialPlans(currentProduct)"
            :key="plan.id"
            :label="plan.id"
            class="plan-radio"
          >
            <div class="plan-option-card">
              <div class="plan-title">
                <span>{{ plan.name }}</span>
                <el-tag v-if="plan.is_recommended" type="success" size="small">
                  推荐
                </el-tag>
              </div>
              <div class="plan-info">
                <span>试用{{ plan.default_validity_days }}天</span>
                <span>最多{{ plan.default_max_activations }}个设备</span>
              </div>
            </div>
          </el-radio>
        </el-radio-group>
      </el-form-item>
      
      <!-- 如果只有一个方案，显示提示 -->
      <el-alert
        v-if="currentProduct && getTrialPlans(currentProduct).length === 1"
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        <template #title>
          试用方案：{{ getTrialPlans(currentProduct)[0].name }}
        </template>
        试用期限 {{ getTrialPlans(currentProduct)[0].default_validity_days }} 天，
        可激活 {{ getTrialPlans(currentProduct)[0].default_max_activations }} 个设备
      </el-alert>
      
      <!-- 其他字段 -->
      <el-form-item label="申请原因">
        <el-input
          v-model="formData.reason"
          type="textarea"
          :rows="3"
          placeholder="请简要说明申请原因（可选）"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
      
      <!-- 补充信息 -->
      <el-collapse style="margin-bottom: 20px;">
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
              :rows="2"
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
          :disabled="!canSubmit"
        >
          {{ submitting ? '提交中...' : '提交申请' }}
        </el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Clock, Monitor } from '@element-plus/icons-vue';
import axios from 'axios';

const router = useRouter();
const route = useRoute();

// 数据
const loading = ref(false);
const submitting = ref(false);
const products = ref([]);
const formRef = ref(null);
const selectedPlans = ref({});

// 表单数据
const formData = ref({
  product_id: route.params.productId ? parseInt(route.params.productId) : null,
  plan_id: route.query.planId ? parseInt(route.query.planId) : null,
  reason: '',
  user_info: {
    company: '',
    job_title: '',
    phone: '',
    intended_use: ''
  }
});

// 验证规则
const rules = {
  product_id: [
    { required: true, message: '请选择产品', trigger: 'change' }
  ],
  plan_id: [
    { 
      required: false,  // 可选
      message: '请选择试用方案', 
      trigger: 'change' 
    }
  ]
};

// 当前选中的产品
const currentProduct = computed(() => {
  if (!formData.value.product_id) return null;
  return products.value.find(p => p.id === formData.value.product_id);
});

// 是否可以提交
const canSubmit = computed(() => {
  if (!formData.value.product_id) return false;
  
  const plans = getTrialPlans(currentProduct.value);
  
  // 如果有多个方案，必须选择一个
  if (plans.length > 1 && !formData.value.plan_id) {
    return false;
  }
  
  return true;
});

// 获取试用方案
const getTrialPlans = (product) => {
  if (!product || !product.trial_plans) return [];
  return Array.isArray(product.trial_plans) 
    ? product.trial_plans 
    : [product.trial_plans];
};

// 获取选中的方案
const getSelectedPlan = (product) => {
  if (!product || !formData.value.plan_id) return null;
  const plans = getTrialPlans(product);
  return plans.find(p => p.id === formData.value.plan_id);
};

// 获取产品列表
const fetchProducts = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/v1/licenses/member/available-products/');
    products.value = response.data.data.products;
  } catch (error) {
    ElMessage.error('获取产品列表失败');
  } finally {
    loading.value = false;
  }
};

// 产品选择变化
const onProductChange = (productId) => {
  const product = products.value.find(p => p.id === productId);
  
  if (!product) return;
  
  // 检查是否已申请
  if (product.already_applied) {
    ElMessage.warning('您已经申请过该产品');
    formData.value.product_id = null;
    return;
  }
  
  const plans = getTrialPlans(product);
  
  // 如果只有一个方案，自动选择
  if (plans.length === 1) {
    formData.value.plan_id = plans[0].id;
  } 
  // 如果有多个方案，选择推荐的
  else if (plans.length > 1) {
    const recommended = plans.find(p => p.is_recommended);
    formData.value.plan_id = recommended ? recommended.id : plans[0].id;
  }
};

// 提交申请
const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    
    // 二次确认
    const product = currentProduct.value;
    const plan = getSelectedPlan(product);
    
    await ElMessageBox.confirm(
      `确定要申请 "${product.name}" 的试用许可证吗？\n方案：${plan.name}\n试用期限：${plan.default_validity_days}天`,
      '确认申请',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    );
    
    submitting.value = true;
    
    // 准备请求数据
    const requestData = {
      product_id: formData.value.product_id
    };
    
    // 如果有多个方案，必须指定plan_id
    const plans = getTrialPlans(product);
    if (plans.length > 1 || formData.value.plan_id) {
      requestData.plan_id = formData.value.plan_id;
    }
    
    if (formData.value.reason) {
      requestData.reason = formData.value.reason;
    }
    
    // user_info只发送有值的字段
    const userInfo = formData.value.user_info;
    const hasUserInfo = Object.values(userInfo).some(v => v && v.trim());
    if (hasUserInfo) {
      requestData.user_info = {};
      for (const [key, value] of Object.entries(userInfo)) {
        if (value && value.trim()) {
          requestData.user_info[key] = value.trim();
        }
      }
    }
    
    // 发送请求
    const response = await axios.post('/api/v1/licenses/member/apply/', requestData);
    
    if (response.data.success) {
      // 申请成功
      showSuccessDialog(response.data.data);
    } else {
      ElMessage.error(response.data.error || '申请失败');
    }
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('申请失败:', error);
      
      if (error.response) {
        const { status, data } = error.response;
        
        if (status === 400 && data.errors) {
          const messages = [];
          for (const [field, errors] of Object.entries(data.errors)) {
            if (field === 'non_field_errors') {
              messages.push(...errors);
            } else {
              messages.push(`${field}: ${errors.join(', ')}`);
            }
          }
          ElMessage.error(messages.join('\n'));
        } else {
          ElMessage.error(data.error || '申请失败');
        }
      } else {
        ElMessage.error('网络连接失败');
      }
    }
  } finally {
    submitting.value = false;
  }
};

// 显示成功对话框
const showSuccessDialog = (result) => {
  ElMessageBox.alert(
    `
    <div style="text-align: center;">
      <h2 style="color: #67C23A;">申请成功！</h2>
      <p style="margin: 15px 0;">您的许可证密钥：</p>
      <div style="background: #F5F7FA; padding: 15px; margin: 15px 0; border-radius: 4px;">
        <code style="font-size: 18px; font-weight: bold; color: #409EFF;">
          ${result.license_key}
        </code>
      </div>
      <p style="color: #F56C6C; font-weight: bold;">⚠️ 请妥善保管此密钥，后续不再显示完整密钥！</p>
      <div style="margin-top: 15px; color: #606266;">
        <p>产品：${result.product_name}</p>
        <p>方案：${result.plan_name}</p>
        <p>过期时间：${new Date(result.expires_at).toLocaleString('zh-CN')}</p>
        <p>可激活设备：${result.max_activations} 个</p>
      </div>
    </div>
    `,
    '申请成功',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '复制密钥并查看许可证',
      callback: async () => {
        // 复制密钥
        try {
          await navigator.clipboard.writeText(result.license_key);
          ElMessage.success('密钥已复制');
        } catch (error) {
          console.error('复制失败:', error);
        }
        
        // 跳转到许可证列表
        router.push('/member/my-licenses');
      }
    }
  );
};

// 重置表单
const resetForm = () => {
  formRef.value.resetFields();
};

// 监听product_id变化，自动选择方案
watch(() => formData.value.product_id, (newVal) => {
  if (newVal) {
    onProductChange(newVal);
  }
});

onMounted(() => {
  fetchProducts();
});
</script>

<style scoped>
.apply-form-page {
  max-width: 700px;
  margin: 20px auto;
  padding: 20px;
}

.plan-radio-group {
  width: 100%;
}

.plan-radio {
  width: 100%;
  margin: 10px 0;
}

.plan-option-card {
  width: 100%;
  padding: 15px;
  border: 1px solid #DCDFE6;
  border-radius: 4px;
  background-color: #FAFAFA;
}

.plan-radio.is-checked .plan-option-card {
  border-color: #409EFF;
  background-color: #ECF5FF;
}

.plan-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 600;
}

.plan-info {
  display: flex;
  gap: 20px;
  color: #606266;
  font-size: 14px;
}
</style>
```

---

## 📝 API Service层封装

```javascript
// src/api/services/licenseService.js

class LicenseService {
  baseURL = '/api/v1/licenses/member';
  
  /**
   * 获取可申请产品列表
   * @returns {Promise}
   */
  async getAvailableProducts() {
    const response = await axios.get(`${this.baseURL}/available-products/`);
    return response.data.data;
  }
  
  /**
   * 申请试用许可证
   * @param {number} productId - 产品ID
   * @param {number} planId - 方案ID（可选）
   * @param {string} reason - 申请原因
   * @param {object} userInfo - 用户补充信息
   * @returns {Promise}
   */
  async applyTrialLicense(productId, planId, reason, userInfo) {
    const requestData = {
      product_id: productId
    };
    
    // 如果指定了方案ID，添加到请求
    if (planId) {
      requestData.plan_id = planId;
    }
    
    if (reason) requestData.reason = reason;
    if (userInfo) requestData.user_info = userInfo;
    
    const response = await axios.post(`${this.baseURL}/apply/`, requestData);
    return response.data;
  }
  
  /**
   * 获取我的许可证
   * @param {object} filters - 筛选条件
   * @returns {Promise}
   */
  async getMyLicenses(filters = {}) {
    const response = await axios.get(`${this.baseURL}/my-licenses/`, {
      params: filters
    });
    return response.data.data;
  }
}

export default new LicenseService();
```

---

## 📋 前端开发检查清单

### 必须修改的内容

- [ ] **数据结构适配**：`trial_plan` 改为 `trial_plans` 数组
- [ ] **产品列表UI**：支持显示多个试用方案
- [ ] **方案选择UI**：当有多个方案时提供选择
- [ ] **申请API调用**：添加 `plan_id` 参数
- [ ] **默认方案选择**：自动选择推荐方案
- [ ] **兼容性处理**：处理单个和多个方案的情况

### 建议添加的功能

- [ ] **方案对比**：当有多个方案时，提供对比视图
- [ ] **推荐标识**：醒目显示推荐方案
- [ ] **方案说明**：解释不同方案的差异
- [ ] **自动选择**：默认选中推荐方案

---

## 🧪 测试用例

### 测试1：单个试用方案的产品

**期望行为**：
- 自动选择该方案
- 不显示方案选择器
- 直接显示方案信息

### 测试2：多个试用方案的产品

**期望行为**：
- 显示所有方案
- 默认选中推荐方案（is_recommended=true）
- 用户可以切换选择
- 提交时发送plan_id

### 测试3：不指定plan_id申请

**期望行为**：
- 后端自动选择有效期最长的方案
- 申请成功

### 测试4：指定plan_id申请

**期望行为**：
- 使用指定的方案
- 申请成功

---

## 📞 技术支持

如有疑问：
- 查看 Swagger 文档：`http://localhost:8000/api/v1/docs/`
- 查看本文档的代码示例
- 联系后端团队

---

**更新完成，请前端团队按此指南进行适配！** 🚀
