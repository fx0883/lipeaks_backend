# Member 许可证 API 通用说明

本文档包含Member许可证API的通用说明，包括认证、业务规则、错误码和数据模型。

---

## 目录

- [认证说明](#认证说明)
- [权限要求](#权限要求)
- [业务规则](#业务规则)
- [错误码说明](#错误码说明)
- [数据模型](#数据模型)
- [频率限制](#频率限制)

---

## 认证说明

### JWT令牌认证

所有API请求必须在请求头中携带有效的JWT访问令牌：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 获取令牌

Member用户通过登录API获取令牌：

```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "username": "member@example.com",
  "password": "member_password",
  "tenant_id": 1
}
```

响应：
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 10,
      "username": "member",
      "is_member": true,
      "tenant_id": 1
    }
  }
}
```

---

## 权限要求

### Member用户身份验证

系统会验证以下条件：

1. ✅ **已认证**：携带有效的JWT令牌
2. ✅ **Member身份**：`is_member = true`，不能是管理员
3. ✅ **用户活跃**：`is_active = true`，`status = 'active'`
4. ✅ **租户活跃**：所属租户状态为活跃
5. ✅ **申请权限**：具有试用许可证申请权限

### 身份识别

后端通过以下方式识别Member用户：

```python
# 权限类
permission_classes = [IsAuthenticated, IsMemberUser, CanApplyTrialLicense]
```

前端无需特殊处理，只要使用Member用户登录获得的token即可。

---

## 业务规则

### 试用许可证申请规则

#### 1. 重复申请限制

- **规则**：每个产品只能申请一次试用许可证
- **检查范围**：`active`和`pending`状态的许可证
- **错误提示**：`您已经申请过该产品的许可证`

```javascript
// 前端可以通过 already_applied 字段判断
if (product.already_applied) {
  showMessage('您已经申请过该产品');
  disableApplyButton();
}
```

#### 2. 申请频率限制

- **API级别**：5次/天（`MemberTrialApplicationThrottle`）
- **业务级别**：24小时内最多3次申请
- **错误提示**：`24小时内申请次数过多，请稍后再试`

```javascript
// 前端建议：记录申请次数
const today申请次数 = localStorage.getItem('today_apply_count') || 0;
if (today申请次数 >= 3) {
  showWarning('今日申请次数已达上限，请明天再试');
}
```

#### 3. 试用配额限制

- **规则**：用户最多持有1个活跃的试用许可证
- **可配置**：通过`max_trial_licenses`字段配置
- **错误提示**：`您的试用许可证数量已达上限（1个）`

```javascript
// 前端可以先查询现有许可证
const myLicenses = await getLicenses();
const activeTrial = myLicenses.filter(l => 
  l.status === 'active' && l.plan_type === 'trial'
);

if (activeTrial.length >= 1) {
  showWarning('您已有一个试用许可证，无法继续申请');
}
```

#### 4. 产品可用性

- **规则**：产品必须有可用的试用方案
- **检查条件**：
  - 产品状态为`active`
  - 存在`plan_type='trial'`且`status='active'`的方案
- **错误提示**：`该产品没有可用的试用方案`

---

## 频率限制

### API频率限制

| API | 限制 | Throttle类 |
|-----|------|-----------|
| 申请试用许可证 | 5次/天 | MemberTrialApplicationThrottle |
| 获取产品列表 | 100次/小时 | MemberAPIThrottle |
| 查看我的许可证 | 100次/小时 | MemberAPIThrottle |

### 超出限制的响应

**状态码**：`429 Too Many Requests`

**响应体**：
```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

### 前端处理建议

```javascript
function handleAPIError(error) {
  if (error.response && error.response.status === 429) {
    const retryAfter = error.response.data.detail.match(/\d+/);
    const seconds = retryAfter ? parseInt(retryAfter[0]) : 3600;
    const minutes = Math.ceil(seconds / 60);
    
    showError(`请求过于频繁，请在${minutes}分钟后重试`);
    
    // 禁用申请按钮一段时间
    disableApplyButton(seconds * 1000);
  }
}
```

---

## 错误码说明

### HTTP状态码

| 状态码 | 说明 | 处理建议 |
|--------|------|---------|
| 200 | 请求成功 | 正常处理响应数据 |
| 201 | 创建成功 | 显示成功提示，跳转到许可证页面 |
| 400 | 请求参数错误 | 显示具体错误信息 |
| 401 | 未认证 | 跳转到登录页 |
| 403 | 权限不足 | 显示"需要Member身份"提示 |
| 429 | 请求频率限制 | 显示频率限制提示 |
| 500 | 服务器内部错误 | 显示服务器错误提示 |

### 业务错误码

| 错误码 | 说明 | 触发场景 |
|--------|------|---------|
| `APPLICATION_FAILED` | 申请失败 | 违反业务规则 |
| `FETCH_PRODUCTS_FAILED` | 获取产品失败 | 服务器错误 |
| `FETCH_LICENSES_FAILED` | 获取许可证失败 | 服务器错误 |
| `APPLICATION_ERROR` | 申请处理错误 | 系统异常 |
| `INTERNAL_ERROR` | 内部错误 | 系统异常 |

---

## 数据模型

### 产品对象 (Product)

```typescript
interface Product {
  id: number;                    // 产品ID
  name: string;                  // 产品名称
  code: string;                  // 产品代码
  description: string;           // 产品描述
  version: string;               // 产品版本
  trial_plan: TrialPlan | null;  // 试用方案信息
  already_applied: boolean;      // 是否已申请
}
```

### 试用方案对象 (TrialPlan)

```typescript
interface TrialPlan {
  id: number;                      // 方案ID
  name: string;                    // 方案名称（如"试用版"）
  default_validity_days: number;   // 默认有效期（天数）
  default_max_activations: number; // 默认最大激活数
  features: object;                // 功能配置（JSON）
  price: number;                   // 价格（试用版通常为0）
  currency: string;                // 货币（如"CNY"）
}
```

### 许可证对象 (License)

```typescript
interface License {
  // 基本信息
  id: number;                      // 许可证分配ID
  product_name: string;            // 产品名称
  product_code: string;            // 产品代码
  product_version: string;         // 产品版本
  plan_name: string;               // 方案名称
  plan_type: string;               // 方案类型：trial/basic/professional/enterprise
  
  // 许可证密钥
  license_key_preview: string;     // 密钥预览（如"ABCDE...VWXYZ"）
  
  // 状态信息
  status: string;                  // 状态：active/expired/revoked/pending
  status_display: string;          // 状态显示文本
  assignment_type: string;         // 分配类型
  assignment_reason: string;       // 分配原因
  
  // 时间信息
  assigned_at: string;             // 分配时间（ISO 8601）
  activated_at: string | null;     // 激活时间
  expires_at: string | null;       // 过期时间
  days_until_expiry: number | null;// 距离过期天数
  
  // 激活信息
  can_activate_license: boolean;   // 是否可以激活
  activation_info: ActivationInfo; // 激活详细信息
  
  // 使用统计
  usage_count: number;             // 使用次数
  last_used_at: string | null;     // 最后使用时间
  last_heartbeat: string | null;   // 最后心跳时间
  
  // 权限配置
  can_activate: boolean;           // 是否有激活权限
  can_deactivate: boolean;         // 是否有停用权限
  can_share: boolean;              // 是否可以共享
  max_devices_per_user: number;    // 每个用户最大设备数
}
```

### 激活信息对象 (ActivationInfo)

```typescript
interface ActivationInfo {
  current_activations: number;  // 当前激活数
  max_activations: number;      // 最大激活数
  available_slots: number;      // 可用配额
}
```

### 申请响应对象 (ApplicationResult)

```typescript
interface ApplicationResult {
  license_id: number;           // 许可证ID
  assignment_id: number;        // 分配关系ID
  license_key: string;          // 完整的许可证密钥
  expires_at: string;           // 过期时间
  product_name: string;         // 产品名称
  plan_name: string;            // 方案名称
  max_activations: number;      // 最大激活数
}
```

---

## 字段详细说明

### license_key_preview (string)

许可证密钥的部分显示，用于列表展示：

- **格式**：`"ABCDE...VWXYZ"`（首5位...尾5位）
- **用途**：在列表中识别许可证，不暴露完整密钥
- **完整密钥**：仅在申请成功时返回一次

### status (string)

许可证状态：

| 值 | 说明 | UI建议 |
|----|------|--------|
| `active` | 有效 | 绿色标签 |
| `expired` | 已过期 | 灰色标签 |
| `revoked` | 已撤销 | 红色标签 |
| `pending` | 待处理 | 黄色标签 |

### plan_type (string)

方案类型：

| 值 | 说明 | 特点 |
|----|------|------|
| `trial` | 试用版 | 免费，有时间限制 |
| `basic` | 基础版 | 付费，基本功能 |
| `professional` | 专业版 | 付费，高级功能 |
| `enterprise` | 企业版 | 付费，全部功能 |

### days_until_expiry (number | null)

距离过期的天数：

- **>= 7天**：正常显示
- **< 7天**：用醒目颜色提示
- **< 3天**：用红色警告
- **= 0**：今天过期
- **null**：永久有效或未设置

```javascript
// 前端显示建议
function getExpiryWarning(days) {
  if (days === null) return null;
  if (days === 0) return { text: '今天过期', color: 'red' };
  if (days < 3) return { text: `还有${days}天过期`, color: 'red' };
  if (days < 7) return { text: `还有${days}天过期`, color: 'orange' };
  return { text: `还有${days}天过期`, color: 'green' };
}
```

### activation_info (object)

激活配额信息：

```javascript
{
  current_activations: 0,    // 当前已激活设备数
  max_activations: 1,        // 最大可激活设备数
  available_slots: 1         // 剩余可激活配额
}
```

前端可以用进度条展示：

```vue
<el-progress 
  :percentage="(current_activations / max_activations) * 100"
  :color="current_activations >= max_activations ? 'red' : 'green'"
/>
<span>已激活 {{ current_activations }}/{{ max_activations }} 个设备</span>
```

---

## 业务规则详解

### 1. 产品筛选规则

获取可申请产品时，后端会自动过滤：

- ✅ 产品状态为`active`
- ✅ 产品未被删除（`is_deleted=false`）
- ✅ 产品属于当前用户的租户
- ✅ 产品有可用的试用方案（`plan_type='trial'`, `status='active'`）

### 2. 申请验证流程

```
请求申请
  ↓
验证产品ID是否存在
  ↓
检查产品是否有试用方案
  ↓
检查是否重复申请（同一产品）
  ↓
检查24小时内申请次数（<3次）
  ↓
检查当前试用许可证数量（<1个）
  ↓
创建许可证
  ↓
创建分配关系
  ↓
返回许可证信息
```

### 3. 自动化处理

#### 自动审批
- 试用申请**无需审批**，立即通过
- 许可证**立即生成**，可直接使用
- 分配关系**自动创建**

#### 自动配置
- **有效期**：根据`default_validity_days`自动计算
- **激活数**：根据`default_max_activations`自动设置
- **状态**：自动设置为`active`

### 4. 许可证有效期计算

```python
# 后端计算逻辑
expires_at = timezone.now() + timedelta(days=trial_plan.default_validity_days)
```

```javascript
// 前端显示示例
const expiresAt = new Date(license.expires_at);
const now = new Date();
const daysLeft = Math.ceil((expiresAt - now) / (1000 * 60 * 60 * 24));

console.log(`许可证将在${daysLeft}天后过期`);
```

---

## 错误处理

### 常见错误及处理

#### 1. 重复申请

**错误响应**：
```json
{
  "success": false,
  "errors": {
    "non_field_errors": ["您已经申请过该产品的许可证"]
  }
}
```

**前端处理**：
```javascript
if (error.response.data.errors?.non_field_errors) {
  showError(error.response.data.errors.non_field_errors[0]);
}
```

#### 2. 配额已满

**错误响应**：
```json
{
  "success": false,
  "errors": {
    "non_field_errors": ["您的试用许可证数量已达上限（1个）"]
  }
}
```

**前端处理**：
```javascript
// 建议：引导用户查看现有许可证
showError('您已有一个试用许可证');
router.push('/member/licenses');  // 跳转到许可证列表
```

#### 3. 频率限制（业务级别）

**错误响应**：
```json
{
  "success": false,
  "errors": {
    "non_field_errors": ["24小时内申请次数过多，请稍后再试"]
  }
}
```

#### 4. 频率限制（API级别）

**状态码**：`429`

**错误响应**：
```json
{
  "detail": "Request was throttled. Expected available in 86400 seconds."
}
```

**前端处理**：
```javascript
if (error.response && error.response.status === 429) {
  const message = error.response.data.detail;
  const match = message.match(/(\d+) seconds/);
  
  if (match) {
    const seconds = parseInt(match[1]);
    const hours = Math.floor(seconds / 3600);
    showError(`请求过于频繁，请在${hours}小时后重试`);
  }
}
```

---

## 统一错误处理示例

### JavaScript/Axios

```javascript
function handleLicenseAPIError(error) {
  if (!error.response) {
    return '网络连接失败，请检查网络设置';
  }
  
  const { status, data } = error.response;
  
  switch (status) {
    case 400:
      // 参数验证错误
      if (data.errors) {
        // 字段级别错误
        const errorMessages = [];
        for (const [field, messages] of Object.entries(data.errors)) {
          if (field === 'non_field_errors') {
            errorMessages.push(...messages);
          } else {
            errorMessages.push(`${field}: ${messages.join(', ')}`);
          }
        }
        return errorMessages.join('\n');
      }
      return data.error || '请求参数错误';
      
    case 401:
      // 未认证
      localStorage.removeItem('access_token');
      window.location.href = '/login';
      return '登录已过期，请重新登录';
      
    case 403:
      return '权限不足，此功能仅限Member用户使用';
      
    case 429:
      const match = data.detail.match(/(\d+) seconds/);
      if (match) {
        const hours = Math.floor(parseInt(match[1]) / 3600);
        return `请求过于频繁，请在${hours}小时后重试`;
      }
      return '请求过于频繁，请稍后重试';
      
    case 500:
      return data.error || '服务器错误，请稍后重试';
      
    default:
      return data.message || data.error || '操作失败';
  }
}
```

### Vue 3示例

```javascript
import { ElMessage } from 'element-plus';

async function applyLicense(productId) {
  try {
    const response = await axios.post('/api/v1/licenses/member/apply/', {
      product_id: productId
    });
    
    ElMessage.success('申请成功！');
    return response.data;
    
  } catch (error) {
    const errorMessage = handleLicenseAPIError(error);
    ElMessage.error(errorMessage);
    throw error;
  }
}
```

---

## 最佳实践

### 1. 状态管理

```javascript
// Vuex/Pinia Store示例
const licenseStore = {
  state: {
    availableProducts: [],       // 可申请产品列表
    myLicenses: [],             // 我的许可证列表
    licenseStats: {             // 许可证统计
      count: 0,
      active_count: 0,
      trial_count: 0,
      expiring_soon_count: 0
    }
  },
  
  actions: {
    async fetchAvailableProducts() {
      const response = await axios.get('/api/v1/licenses/member/available-products/');
      this.availableProducts = response.data.data.products;
    },
    
    async applyLicense(productId, reason, userInfo) {
      const response = await axios.post('/api/v1/licenses/member/apply/', {
        product_id: productId,
        reason,
        user_info: userInfo
      });
      return response.data;
    },
    
    async fetchMyLicenses(filters = {}) {
      const response = await axios.get('/api/v1/licenses/member/my-licenses/', {
        params: filters
      });
      this.myLicenses = response.data.data.licenses;
      this.licenseStats = {
        count: response.data.data.count,
        active_count: response.data.data.active_count,
        trial_count: response.data.data.trial_count,
        expiring_soon_count: response.data.data.expiring_soon_count
      };
    }
  }
};
```

### 2. 防抖和缓存

```javascript
import { debounce } from 'lodash';

// 使用防抖避免频繁请求
const fetchProducts = debounce(async () => {
  const response = await axios.get('/api/v1/licenses/member/available-products/');
  return response.data;
}, 300);

// 使用缓存减少请求
const cachedProducts = ref(null);
const cacheTime = ref(null);
const CACHE_DURATION = 5 * 60 * 1000; // 5分钟

async function getAvailableProducts() {
  const now = Date.now();
  
  // 如果缓存有效，直接返回
  if (cachedProducts.value && cacheTime.value && (now - cacheTime.value < CACHE_DURATION)) {
    return cachedProducts.value;
  }
  
  // 否则重新获取
  const response = await axios.get('/api/v1/licenses/member/available-products/');
  cachedProducts.value = response.data.data;
  cacheTime.value = now;
  
  return cachedProducts.value;
}
```

### 3. Loading状态

```javascript
const loading = ref(false);

async function applyLicense(productId) {
  loading.value = true;
  try {
    const result = await axios.post('/api/v1/licenses/member/apply/', {
      product_id: productId
    });
    return result.data;
  } finally {
    loading.value = false;
  }
}
```

---

## 下一步

请继续阅读具体的API文档：

- 📗 **available_products_api.md** - 获取可申请产品列表
- 📙 **apply_license_api.md** - 申请试用许可证
- 📕 **my_licenses_api.md** - 查看我的许可证
- 📔 **integration_guide.md** - 完整集成指南

