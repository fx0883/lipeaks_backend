# 查看我的许可证 API

本文档详细说明查看Member许可证列表的API接口。

---

## API概述

### 基本信息

```
GET /api/v1/licenses/member/my-licenses/
```

**功能**：获取当前Member用户的所有许可证列表及统计信息

**权限要求**：
- 需要JWT认证
- 必须是Member用户身份
- 只能查看自己的许可证

**频率限制**：100次/小时

**内容类型**：`application/json`

---

## 请求说明

### 请求头

```http
Authorization: Bearer <access_token>
```

### 查询参数

| 参数 | 类型 | 必填 | 说明 | 可选值 |
|------|------|------|------|--------|
| status | string | 否 | 过滤许可证状态 | active, expired, revoked, pending |
| plan_type | string | 否 | 过滤方案类型 | trial, basic, professional, enterprise |

### 请求示例

#### 示例1：获取所有许可证

```http
GET /api/v1/licenses/member/my-licenses/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/member/my-licenses/" \
  -H "Authorization: Bearer <your_token>"
```

#### 示例2：只获取有效的许可证

```http
GET /api/v1/licenses/member/my-licenses/?status=active
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 示例3：只获取试用版许可证

```http
GET /api/v1/licenses/member/my-licenses/?plan_type=trial
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 示例4：组合筛选

```http
GET /api/v1/licenses/member/my-licenses/?status=active&plan_type=trial
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### JavaScript/Axios

```javascript
// 获取所有许可证
const response = await axios.get('/api/v1/licenses/member/my-licenses/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});

// 只获取有效的试用许可证
const response = await axios.get('/api/v1/licenses/member/my-licenses/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  },
  params: {
    status: 'active',
    plan_type: 'trial'
  }
});
```

---

## 响应说明

### 成功响应

**状态码**：`200 OK`

**响应体**：

```json
{
  "success": true,
  "data": {
    "count": 2,
    "active_count": 1,
    "trial_count": 1,
    "expiring_soon_count": 0,
    "licenses": [
      {
        "id": 456,
        "product_name": "PDF压缩工具",
        "product_code": "pdf_compress",
        "product_version": "1.2.0",
        "plan_name": "试用版",
        "plan_type": "trial",
        "license_key_preview": "ABCDE...VWXYZ",
        "status": "active",
        "status_display": "有效",
        "assignment_type": "direct",
        "assigned_at": "2025-10-06T10:30:00Z",
        "activated_at": "2025-10-06T10:30:00Z",
        "expires_at": "2025-11-05T10:30:00Z",
        "days_until_expiry": 29,
        "assignment_reason": "试用版申请",
        "can_activate_license": true,
        "activation_info": {
          "current_activations": 0,
          "max_activations": 1,
          "available_slots": 1
        },
        "usage_count": 5,
        "last_used_at": "2025-10-06T14:25:30Z",
        "last_heartbeat": "2025-10-06T14:25:30Z",
        "can_activate": true,
        "can_deactivate": false,
        "can_share": false,
        "max_devices_per_user": 1
      },
      {
        "id": 457,
        "product_name": "图片处理工具",
        "product_code": "image_editor",
        "product_version": "2.0.1",
        "plan_name": "专业版",
        "plan_type": "professional",
        "license_key_preview": "FGHIJ...ABCDE",
        "status": "expired",
        "status_display": "已过期",
        "assignment_type": "direct",
        "assigned_at": "2025-09-01T10:00:00Z",
        "activated_at": "2025-09-01T11:00:00Z",
        "expires_at": "2025-10-01T10:00:00Z",
        "days_until_expiry": 0,
        "assignment_reason": "购买",
        "can_activate_license": false,
        "activation_info": {
          "current_activations": 1,
          "max_activations": 3,
          "available_slots": 2
        },
        "usage_count": 150,
        "last_used_at": "2025-09-30T18:45:00Z",
        "last_heartbeat": "2025-09-30T18:45:00Z",
        "can_activate": false,
        "can_deactivate": true,
        "can_share": true,
        "max_devices_per_user": 3
      }
    ]
  }
}
```

### 响应字段说明

#### 统计信息字段

| 字段 | 类型 | 说明 |
|------|------|------|
| count | integer | 许可证总数 |
| active_count | integer | 有效许可证数量 |
| trial_count | integer | 试用版许可证数量 |
| expiring_soon_count | integer | 即将过期许可证数量（7天内） |
| licenses | array | 许可证对象数组 |

#### License对象字段（详细）

**基本信息**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 许可证分配ID |
| product_name | string | 产品名称 |
| product_code | string | 产品代码 |
| product_version | string | 产品版本 |
| plan_name | string | 方案名称 |
| plan_type | string | 方案类型：trial/basic/professional/enterprise |

**许可证密钥**：

| 字段 | 类型 | 说明 |
|------|------|------|
| license_key_preview | string | 密钥预览（部分显示，如"ABCDE...VWXYZ"） |

**状态信息**：

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 状态：active/expired/revoked/pending |
| status_display | string | 状态显示文本（中文） |
| assignment_type | string | 分配类型 |
| assignment_reason | string | 分配原因 |

**时间信息**：

| 字段 | 类型 | 说明 |
|------|------|------|
| assigned_at | string | 分配时间（ISO 8601） |
| activated_at | string\|null | 激活时间 |
| expires_at | string\|null | 过期时间 |
| days_until_expiry | integer\|null | 距离过期天数 |

**激活信息**：

| 字段 | 类型 | 说明 |
|------|------|------|
| can_activate_license | boolean | 是否可以激活许可证 |
| activation_info | object | 激活详细信息 |
| activation_info.current_activations | integer | 当前激活设备数 |
| activation_info.max_activations | integer | 最大可激活设备数 |
| activation_info.available_slots | integer | 剩余可激活配额 |

**使用统计**：

| 字段 | 类型 | 说明 |
|------|------|------|
| usage_count | integer | 使用次数 |
| last_used_at | string\|null | 最后使用时间 |
| last_heartbeat | string\|null | 最后心跳时间 |

**权限配置**：

| 字段 | 类型 | 说明 |
|------|------|------|
| can_activate | boolean | 是否有激活权限 |
| can_deactivate | boolean | 是否有停用权限 |
| can_share | boolean | 是否可以共享 |
| max_devices_per_user | integer | 每个用户最大设备数 |

---

## 错误响应

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

### 500 服务器内部错误

```json
{
  "success": false,
  "error": "获取许可证列表失败，请稍后重试",
  "code": "FETCH_LICENSES_FAILED"
}
```

---

## 前端实现示例

### Vue 3 完整示例

```vue
<template>
  <div class="my-licenses-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>我的许可证</h2>
      <el-button type="primary" @click="goToApply">
        申请新许可证
      </el-button>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="许可证总数" :value="stats.count" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="有效许可证"
            :value="stats.active_count"
            :value-style="{ color: '#67C23A' }"
          />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="试用许可证" :value="stats.trial_count" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="即将过期"
            :value="stats.expiring_soon_count"
            :value-style="stats.expiring_soon_count > 0 ? { color: '#F56C6C' } : {}"
          />
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 筛选器 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="状态">
          <el-select
            v-model="filters.status"
            placeholder="全部状态"
            clearable
            @change="fetchLicenses"
            style="width: 150px;"
          >
            <el-option label="有效" value="active" />
            <el-option label="已过期" value="expired" />
            <el-option label="已撤销" value="revoked" />
            <el-option label="待处理" value="pending" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="方案类型">
          <el-select
            v-model="filters.plan_type"
            placeholder="全部类型"
            clearable
            @change="fetchLicenses"
            style="width: 150px;"
          >
            <el-option label="试用版" value="trial" />
            <el-option label="基础版" value="basic" />
            <el-option label="专业版" value="professional" />
            <el-option label="企业版" value="enterprise" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- Loading状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>
    
    <!-- 许可证列表 -->
    <div v-else class="licenses-list">
      <el-empty v-if="licenses.length === 0" description="暂无许可证" />
      
      <el-card
        v-for="license in licenses"
        :key="license.id"
        class="license-card"
      >
        <!-- 头部：产品名称和状态 -->
        <template #header>
          <div class="card-header">
            <div>
              <h3 class="product-name">{{ license.product_name }}</h3>
              <span class="product-version">v{{ license.product_version }}</span>
            </div>
            <div>
              <el-tag :type="getStatusType(license.status)" size="large">
                {{ license.status_display }}
              </el-tag>
              <el-tag
                :type="license.plan_type === 'trial' ? 'warning' : 'success'"
                size="large"
                style="margin-left: 8px;"
              >
                {{ getPlanTypeName(license.plan_type) }}
              </el-tag>
            </div>
          </div>
        </template>
        
        <!-- 许可证信息 -->
        <el-descriptions :column="2" border>
          <el-descriptions-item label="许可证密钥">
            <div class="license-key">
              <code>{{ license.license_key_preview }}</code>
              <el-tooltip content="密钥已隐藏部分，申请时已提供完整密钥">
                <el-icon><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
          </el-descriptions-item>
          
          <el-descriptions-item label="方案">
            {{ license.plan_name }}
          </el-descriptions-item>
          
          <el-descriptions-item label="分配时间">
            {{ formatDate(license.assigned_at) }}
          </el-descriptions-item>
          
          <el-descriptions-item label="激活时间">
            {{ license.activated_at ? formatDate(license.activated_at) : '未激活' }}
          </el-descriptions-item>
          
          <el-descriptions-item label="过期时间">
            <span :class="getExpiryClass(license.days_until_expiry)">
              {{ license.expires_at ? formatDate(license.expires_at) : '永久' }}
            </span>
          </el-descriptions-item>
          
          <el-descriptions-item label="剩余天数">
            <span :class="getExpiryClass(license.days_until_expiry)">
              {{ license.days_until_expiry !== null ? `${license.days_until_expiry} 天` : '永久' }}
              <el-tag
                v-if="license.days_until_expiry !== null && license.days_until_expiry < 7"
                type="danger"
                size="small"
                effect="dark"
                style="margin-left: 8px;"
              >
                即将过期
              </el-tag>
            </span>
          </el-descriptions-item>
          
          <el-descriptions-item label="激活配额">
            <el-progress
              :percentage="getActivationPercentage(license.activation_info)"
              :status="getActivationStatus(license.activation_info)"
            />
            <span style="margin-left: 10px;">
              {{ license.activation_info.current_activations }}/{{ license.activation_info.max_activations }}
            </span>
          </el-descriptions-item>
          
          <el-descriptions-item label="使用次数">
            {{ license.usage_count }}
          </el-descriptions-item>
          
          <el-descriptions-item label="最后使用">
            {{ license.last_used_at ? formatDate(license.last_used_at) : '从未使用' }}
          </el-descriptions-item>
          
          <el-descriptions-item label="最后心跳">
            {{ license.last_heartbeat ? formatDate(license.last_heartbeat) : '-' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 操作按钮 -->
        <template #footer>
          <div class="card-footer">
            <div class="permissions">
              <el-tag v-if="license.can_activate" type="success" size="small">
                可激活
              </el-tag>
              <el-tag v-if="license.can_deactivate" type="warning" size="small">
                可停用
              </el-tag>
              <el-tag v-if="license.can_share" type="info" size="small">
                可共享
              </el-tag>
            </div>
            <div class="actions">
              <el-button
                size="small"
                @click="showLicenseDetail(license)"
              >
                查看详情
              </el-button>
              <el-button
                v-if="license.can_activate_license"
                size="small"
                type="primary"
                @click="showActivationGuide(license)"
              >
                激活指南
              </el-button>
            </div>
          </div>
        </template>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { QuestionFilled } from '@element-plus/icons-vue';
import axios from 'axios';
import dayjs from 'dayjs';

const router = useRouter();

// 数据
const loading = ref(false);
const licenses = ref([]);
const stats = ref({
  count: 0,
  active_count: 0,
  trial_count: 0,
  expiring_soon_count: 0
});

// 筛选器
const filters = ref({
  status: '',
  plan_type: ''
});

// 获取许可证列表
const fetchLicenses = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/v1/licenses/member/my-licenses/', {
      params: {
        status: filters.value.status || undefined,
        plan_type: filters.value.plan_type || undefined
      }
    });
    
    if (response.data.success) {
      const data = response.data.data;
      licenses.value = data.licenses;
      stats.value = {
        count: data.count,
        active_count: data.active_count,
        trial_count: data.trial_count,
        expiring_soon_count: data.expiring_soon_count
      };
    }
  } catch (error) {
    console.error('获取许可证列表失败:', error);
    
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录');
        router.push('/login');
      } else if (status === 403) {
        ElMessage.error('权限不足');
      } else {
        ElMessage.error(data.error || '获取许可证列表失败');
      }
    } else {
      ElMessage.error('网络连接失败');
    }
  } finally {
    loading.value = false;
  }
};

// 重置筛选
const resetFilters = () => {
  filters.value = {
    status: '',
    plan_type: ''
  };
  fetchLicenses();
};

// 跳转到申请页面
const goToApply = () => {
  router.push('/member/apply-license');
};

// 状态类型映射
const getStatusType = (status) => {
  const map = {
    active: 'success',
    expired: 'info',
    revoked: 'danger',
    pending: 'warning'
  };
  return map[status] || 'info';
};

// 方案类型名称
const getPlanTypeName = (planType) => {
  const map = {
    trial: '试用版',
    basic: '基础版',
    professional: '专业版',
    enterprise: '企业版'
  };
  return map[planType] || planType;
};

// 过期时间样式
const getExpiryClass = (days) => {
  if (days === null || days === undefined) return '';
  if (days === 0) return 'expiry-today';
  if (days < 3) return 'expiry-urgent';
  if (days < 7) return 'expiry-warning';
  return 'expiry-normal';
};

// 激活百分比
const getActivationPercentage = (activationInfo) => {
  if (!activationInfo || activationInfo.max_activations === 0) return 0;
  return Math.round((activationInfo.current_activations / activationInfo.max_activations) * 100);
};

// 激活状态
const getActivationStatus = (activationInfo) => {
  const percentage = getActivationPercentage(activationInfo);
  if (percentage >= 100) return 'exception';
  if (percentage >= 80) return 'warning';
  return 'success';
};

// 格式化日期
const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm');
};

// 查看许可证详情
const showLicenseDetail = (license) => {
  router.push(`/member/licenses/${license.id}`);
};

// 显示激活指南
const showActivationGuide = (license) => {
  router.push({
    name: 'ActivationGuide',
    params: { licenseId: license.id }
  });
};

// 组件挂载时获取数据
onMounted(() => {
  fetchLicenses();
});
</script>

<style scoped>
.my-licenses-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.filter-card {
  margin-bottom: 20px;
}

.licenses-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.license-card {
  transition: all 0.3s;
}

.license-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-name {
  margin: 0;
  font-size: 16px;
}

.product-version {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}

.license-key {
  display: flex;
  align-items: center;
  gap: 8px;
}

.license-key code {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  padding: 4px 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.permissions {
  display: flex;
  gap: 8px;
}

.actions {
  display: flex;
  gap: 8px;
}

/* 过期时间样式 */
.expiry-normal {
  color: #67C23A;
}

.expiry-warning {
  color: #E6A23C;
  font-weight: bold;
}

.expiry-urgent {
  color: #F56C6C;
  font-weight: bold;
}

.expiry-today {
  color: #F56C6C;
  font-weight: bold;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50%, 100% { opacity: 1; }
  25%, 75% { opacity: 0.5; }
}

.loading-container {
  padding: 40px 0;
}
</style>
```

---

## 使用场景

### 场景1：许可证中心

展示用户所有的许可证，提供筛选和查看功能：

```javascript
async function loadMyLicenses(filters = {}) {
  const response = await axios.get('/api/v1/licenses/member/my-licenses/', {
    params: filters
  });
  
  return response.data.data;
}
```

### 场景2：即将过期提醒

在首页或导航栏显示即将过期的许可证提醒：

```vue
<el-badge
  :value="expiringSoonCount"
  :hidden="expiringSoonCount === 0"
  type="danger"
>
  <el-button>我的许可证</el-button>
</el-badge>
```

### 场景3：激活状态监控

显示许可证的激活设备情况：

```javascript
function renderActivationStatus(activationInfo) {
  const { current_activations, max_activations, available_slots } = activationInfo;
  
  return `
    已激活 ${current_activations}/${max_activations} 个设备
    ${available_slots > 0 ? `（还可激活 ${available_slots} 个）` : '（已满）'}
  `;
}
```

---

## 前端开发建议

### 功能清单

- [x] 统计信息展示（卡片）
- [x] 许可证列表展示
- [x] 状态筛选
- [x] 方案类型筛选
- [x] 许可证详情卡片
- [x] 过期提醒（高亮显示）
- [x] 激活配额进度条
- [x] 密钥展示（部分）
- [x] 操作按钮
- [x] Loading状态
- [x] 空状态处理

### UI/UX建议

1. **统计面板**：用卡片展示总数、有效数、试用数、即将过期数
2. **视觉警示**：
   - 即将过期（<7天）：橙色提示
   - 今天过期：红色闪烁
   - 已过期：灰色
3. **激活配额**：用进度条直观展示
4. **快速筛选**：状态和类型筛选器
5. **引导操作**：清晰的"激活指南"按钮

### 数据处理建议

```javascript
// 1. 分组显示
function groupLicensesByStatus(licenses) {
  return {
    active: licenses.filter(l => l.status === 'active'),
    expired: licenses.filter(l => l.status === 'expired'),
    others: licenses.filter(l => !['active', 'expired'].includes(l.status))
  };
}

// 2. 排序（按过期时间）
function sortByExpiry(licenses) {
  return [...licenses].sort((a, b) => {
    if (a.days_until_expiry === null) return 1;
    if (b.days_until_expiry === null) return -1;
    return a.days_until_expiry - b.days_until_expiry;
  });
}

// 3. 计算统计信息（如果后端未过滤）
function calculateStats(licenses) {
  return {
    count: licenses.length,
    active_count: licenses.filter(l => l.status === 'active').length,
    trial_count: licenses.filter(l => l.plan_type === 'trial').length,
    expiring_soon_count: licenses.filter(l => 
      l.status === 'active' && 
      l.days_until_expiry !== null && 
      l.days_until_expiry <= 7
    ).length
  };
}
```

### 自动刷新

```javascript
import { ref, onMounted, onUnmounted } from 'vue';

const refreshInterval = ref(null);

// 自动刷新（每30秒）
function startAutoRefresh() {
  refreshInterval.value = setInterval(() => {
    fetchLicenses();
  }, 30000);  // 30秒
}

function stopAutoRefresh() {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value);
    refreshInterval.value = null;
  }
}

onMounted(() => {
  fetchLicenses();
  startAutoRefresh();
});

onUnmounted(() => {
  stopAutoRefresh();
});
```

---

## 下一步

继续阅读：

📔 **integration_guide.md** - 完整集成指南（含客户端激活流程）

