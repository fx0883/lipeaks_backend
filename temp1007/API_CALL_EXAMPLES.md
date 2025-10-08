# API调用示例和常见问题

本文档提供实际的API调用示例和常见问题解决方案。

---

## 📞 实际调用示例

### 1. 获取可申请产品列表

#### cURL命令

```bash
curl -X GET 'http://localhost:8000/api/v1/licenses/member/available-products/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

#### 成功响应

```json
{
  "success": true,
  "data": {
    "count": 1,
    "products": [
      {
        "id": 6,
        "name": "Leaks_compress",
        "code": "Leaks_compress_001",
        "description": "Leaks_compress",
        "version": "1.0.0",
        "trial_plan": {
          "id": 12,
          "name": "Trial",
          "default_validity_days": 3,
          "default_max_activations": 12,
          "features": {},
          "price": 0,
          "currency": "CNY"
        },
        "already_applied": true
      }
    ]
  }
}
```

---

### 2. 申请试用许可证

#### cURL命令

```bash
curl -X POST 'http://localhost:8000/api/v1/licenses/member/apply/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{
    "product_id": 6,
    "reason": "试用申请",
    "user_info": {
      "company": "我的公司",
      "job_title": "开发工程师"
    }
  }'
```

#### 成功响应

```json
{
  "success": true,
  "message": "试用许可证申请成功",
  "data": {
    "license_id": 123,
    "assignment_id": 456,
    "license_key": "ABCDE-FGHIJ-KLMNO-PQRST-UVWXY",
    "expires_at": "2025-11-05T10:30:00Z",
    "product_name": "Leaks_compress",
    "plan_name": "Trial",
    "max_activations": 12
  }
}
```

#### 错误响应：重复申请

```json
{
  "success": false,
  "error": "您已经拥有该产品的有效许可证",
  "code": "APPLICATION_FAILED"
}
```

**原因**：用户已经有该产品的有效许可证（status为active或pending）

**解决方案**：
1. 检查 `already_applied` 字段
2. 提示用户查看现有许可证
3. 引导到"我的许可证"页面

---

### 3. 查看我的许可证

#### cURL命令

```bash
curl -X GET 'http://localhost:8000/api/v1/licenses/member/my-licenses/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

#### 带筛选参数

```bash
curl -X GET 'http://localhost:8000/api/v1/licenses/member/my-licenses/?status=active&plan_type=trial' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

---

## ❗ 常见错误和解决方案

### 错误1：重复申请

**请求**：
```json
{
  "product_id": 6,
  "reason": "申请"
}
```

**响应**：
```json
{
  "success": false,
  "error": "您已经拥有该产品的有效许可证",
  "code": "APPLICATION_FAILED"
}
```

**原因**：用户已经申请过该产品，且许可证状态为`active`或`pending`

**前端解决方案**：

```javascript
// 方法1：使用already_applied字段（推荐）
async function checkBeforeApply(productId) {
  const response = await axios.get('/api/v1/licenses/member/available-products/');
  const product = response.data.data.products.find(p => p.id === productId);
  
  if (product && product.already_applied) {
    ElMessage.warning('您已经申请过该产品');
    router.push('/member/my-licenses');
    return false;
  }
  
  return true;
}

// 使用
if (await checkBeforeApply(productId)) {
  // 可以申请
  await submitApplication();
}
```

---

### 错误2：频率限制

**响应**：
```json
{
  "detail": "Request was throttled. Expected available in 86400 seconds."
}
```

**原因**：
- 超过5次/天的申请限制（API级别）
- 或24小时内申请超过3次（业务级别）

**前端解决方案**：

```javascript
function handleThrottleError(error) {
  if (error.response && error.response.status === 429) {
    const detail = error.response.data.detail;
    const match = detail.match(/(\d+) seconds/);
    
    if (match) {
      const seconds = parseInt(match[1]);
      const hours = Math.floor(seconds / 3600);
      
      ElNotification({
        title: '请求过于频繁',
        message: `申请次数已达上限，请在${hours}小时后重试`,
        type: 'warning',
        duration: 0  // 不自动关闭
      });
      
      // 可以存储下次可申请时间
      const nextAvailableTime = new Date(Date.now() + seconds * 1000);
      localStorage.setItem('next_apply_time', nextAvailableTime.toISOString());
    }
  }
}
```

---

### 错误3：配额已满

**响应**：
```json
{
  "success": false,
  "errors": {
    "non_field_errors": ["您的试用许可证数量已达上限（1个）"]
  }
}
```

**原因**：用户已有1个活跃的试用许可证（默认限制为1个）

**前端解决方案**：

```javascript
async function checkTrialQuota() {
  const response = await axios.get('/api/v1/licenses/member/my-licenses/', {
    params: { status: 'active', plan_type: 'trial' }
  });
  
  const activeTrials = response.data.data.licenses.filter(l => 
    l.status === 'active' && l.plan_type === 'trial'
  );
  
  if (activeTrials.length >= 1) {
    ElMessageBox.alert(
      '您已有一个试用许可证，如需申请新产品，请先等待现有许可证过期。',
      '试用配额已满',
      {
        confirmButtonText: '查看许可证',
        callback: () => {
          router.push('/member/my-licenses');
        }
      }
    );
    return false;
  }
  
  return true;
}
```

---

### 错误4：产品没有试用方案

**响应**：
```json
{
  "success": false,
  "errors": {
    "product_id": ["该产品没有可用的试用方案"]
  }
}
```

**原因**：产品存在但没有活跃的试用方案

**前端解决方案**：

```javascript
// 预防措施：使用available-products API
// 该API已修复，不会返回没有试用方案的产品
const response = await axios.get('/api/v1/licenses/member/available-products/');
const products = response.data.data.products;

// 双重检查
const validProducts = products.filter(p => p.trial_plan !== null);

// 在UI中只显示有效产品
<div v-for="product in validProducts" :key="product.id">
  <!-- 产品卡片 -->
</div>
```

---

## 🎯 最佳实践

### 1. 申请前的完整检查流程

```javascript
async function safeApplyLicense(productId, reason, userInfo) {
  try {
    // 步骤1：检查产品是否可申请
    const productsResponse = await axios.get(
      '/api/v1/licenses/member/available-products/'
    );
    
    const product = productsResponse.data.data.products.find(
      p => p.id === productId
    );
    
    if (!product) {
      ElMessage.error('产品不存在或不可申请');
      return;
    }
    
    if (!product.trial_plan) {
      ElMessage.error('该产品没有试用方案');
      return;
    }
    
    if (product.already_applied) {
      ElMessageBox.confirm(
        '您已经申请过该产品，是否要查看现有许可证？',
        '提示',
        { confirmButtonText: '查看许可证', cancelButtonText: '取消' }
      ).then(() => {
        router.push('/member/my-licenses');
      });
      return;
    }
    
    // 步骤2：检查试用配额
    const licensesResponse = await axios.get(
      '/api/v1/licenses/member/my-licenses/',
      { params: { status: 'active', plan_type: 'trial' } }
    );
    
    const activeTrial = licensesResponse.data.data.licenses.filter(l =>
      l.status === 'active' && l.plan_type === 'trial'
    );
    
    if (activeTrial.length >= 1) {
      ElMessage.warning('您已有一个试用许可证，请等待过期后再申请');
      return;
    }
    
    // 步骤3：确认申请
    await ElMessageBox.confirm(
      `确定要申请 "${product.name}" 的试用许可证吗？\n试用期限：${product.trial_plan.default_validity_days}天`,
      '确认申请',
      { confirmButtonText: '确定', cancelButtonText: '取消' }
    );
    
    // 步骤4：提交申请
    const applyResponse = await axios.post(
      '/api/v1/licenses/member/apply/',
      { product_id: productId, reason, user_info: userInfo }
    );
    
    if (applyResponse.data.success) {
      // 成功：显示许可证密钥
      showLicenseKeyDialog(applyResponse.data.data);
    }
    
  } catch (error) {
    if (error !== 'cancel') {
      handleError(error);
    }
  }
}
```

### 2. 统一的错误处理

```javascript
function handleLicenseAPIError(error) {
  if (!error.response) {
    return { message: '网络连接失败', type: 'network' };
  }
  
  const { status, data } = error.response;
  
  switch (status) {
    case 400:
      if (data.errors) {
        const messages = [];
        for (const [field, errors] of Object.entries(data.errors)) {
          if (field === 'non_field_errors') {
            messages.push(...errors);
          } else {
            messages.push(`${field}: ${errors.join(', ')}`);
          }
        }
        return { message: messages.join('\n'), type: 'validation' };
      }
      return { message: data.error || '请求参数错误', type: 'business' };
      
    case 401:
      return { 
        message: '登录已过期，请重新登录', 
        type: 'auth',
        action: 'redirect_login'
      };
      
    case 403:
      return { message: '权限不足', type: 'permission' };
      
    case 429:
      const match = data.detail?.match(/(\d+) seconds/);
      const hours = match ? Math.floor(parseInt(match[1]) / 3600) : 24;
      return { 
        message: `请求过于频繁，请在${hours}小时后重试`, 
        type: 'throttle',
        retryAfter: match ? parseInt(match[1]) : 86400
      };
      
    case 500:
      return { message: '服务器错误，请稍后重试', type: 'server' };
      
    default:
      return { message: '操作失败', type: 'unknown' };
  }
}
```

---

## 🔧 调试技巧

### 1. 检查Token是否有效

```javascript
// 在发送请求前验证token
function getToken() {
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    console.error('❌ Token不存在');
    return null;
  }
  
  // 解析JWT payload（不验证签名）
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    console.log('Token信息:', payload);
    
    // 检查是否过期
    const exp = payload.exp * 1000;
    const now = Date.now();
    
    if (now >= exp) {
      console.error('❌ Token已过期');
      return null;
    }
    
    console.log(`✅ Token有效，还有${Math.floor((exp - now) / 1000 / 60)}分钟过期`);
    return token;
    
  } catch (error) {
    console.error('❌ Token格式错误');
    return null;
  }
}
```

### 2. 检查用户身份

```javascript
function checkUserRole(token) {
  const payload = JSON.parse(atob(token.split('.')[1]));
  
  console.log('用户信息:', {
    user_id: payload.user_id,
    username: payload.username,
    model_type: payload.model_type,
    is_admin: payload.is_admin,
    is_super_admin: payload.is_super_admin
  });
  
  // 检查是否是Member
  if (payload.model_type !== 'member') {
    console.error('❌ 不是Member用户，无法调用Member API');
    return false;
  }
  
  console.log('✅ 是Member用户');
  return true;
}
```

### 3. 完整的请求调试

```javascript
async function debugAPICall() {
  console.log('=== 开始调试API调用 ===');
  
  // 1. 检查Token
  const token = getToken();
  if (!token) {
    console.error('Token检查失败');
    return;
  }
  
  // 2. 检查用户身份
  if (!checkUserRole(token)) {
    console.error('用户身份检查失败');
    return;
  }
  
  // 3. 发送请求
  try {
    console.log('发送请求到: /api/v1/licenses/member/available-products/');
    
    const response = await axios.get(
      '/api/v1/licenses/member/available-products/',
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    console.log('✅ 请求成功');
    console.log('响应数据:', response.data);
    
    // 4. 验证响应数据
    const products = response.data.data.products;
    
    for (const product of products) {
      console.log(`\n产品: ${product.name}`);
      console.log(`  - ID: ${product.id}`);
      console.log(`  - 有试用方案: ${product.trial_plan !== null ? '是' : '否'}`);
      console.log(`  - 已申请: ${product.already_applied ? '是' : '否'}`);
      
      if (product.trial_plan) {
        console.log(`  - 试用天数: ${product.trial_plan.default_validity_days}`);
      }
    }
    
  } catch (error) {
    console.error('❌ 请求失败');
    console.error('错误详情:', error.response?.data || error.message);
  }
  
  console.log('\n=== 调试完成 ===');
}

// 执行调试
debugAPICall();
```

---

## 📋 测试检查清单

### 申请流程测试

- [ ] 获取产品列表成功
- [ ] 只显示有试用方案的产品（trial_plan不为null）
- [ ] already_applied字段准确
- [ ] 可以成功申请未申请过的产品
- [ ] 重复申请被正确拒绝
- [ ] 频率限制正常工作
- [ ] 配额限制正常工作
- [ ] 申请成功返回完整许可证密钥
- [ ] 可以查看已申请的许可证

---

## 💡 重要提示

### ⚠️ 已修复的Bug

**问题**: API返回没有试用方案的产品（trial_plan为null）

**状态**: ✅ 已修复

**修复内容**: 
- 文件：`licenses/services/member_license_service.py`
- 方法：`get_available_products()`
- 修改：使用`Exists`子查询确保产品有试用方案

**影响**: 修复后，API只返回真正有试用方案的产品

### ✅ 前端防御性编程

即使后端已修复，前端仍建议做保护性检查：

```javascript
// 过滤掉trial_plan为null的产品
const validProducts = products.filter(p => p.trial_plan !== null);

// 或在渲染时检查
<template v-if="product.trial_plan">
  <!-- 显示产品 -->
</template>
<template v-else>
  <p class="error">该产品暂无试用方案</p>
</template>
```

---

## 🆘 获取帮助

### Swagger文档

访问 `http://localhost:8000/api/v1/docs/` 可以：
- 查看所有API
- 在线测试API
- 查看请求/响应示例

### 常用调试命令

```bash
# 检查产品是否有试用方案
python manage.py shell -c "
from licenses.models import SoftwareProduct
product = SoftwareProduct.objects.get(id=6)
trial = product.license_plans.filter(plan_type='trial', status='active').first()
print(f'产品: {product.name}')
print(f'有试用方案: {trial is not None}')
if trial:
    print(f'方案名称: {trial.name}')
"

# 检查用户的许可证
python manage.py shell -c "
from users.models import Member
from licenses.models import LicenseAssignment
member = Member.objects.get(id=1)
licenses = LicenseAssignment.objects.filter(member=member, status='active')
print(f'用户 {member.username} 的有效许可证: {licenses.count()}个')
"
```

---

**文档更新日期**: 2025-10-06  
**包含Bug修复**: 是
