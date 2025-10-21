# API 2: 申请试用许可证

## 📌 API 概述

用户选择产品后，提交试用许可证申请。系统会验证申请资格、配额限制，生成许可证并分配给用户。

---

## 🔗 请求信息

- **HTTP Method**: `POST`
- **URL**: `/api/v1/licenses/member/apply/`
- **完整URL**: `https://backend.espressox.online/api/v1/licenses/member/apply/`
- **认证**: 必需（JWT Bearer Token）
- **权限要求**: Member 用户
- **频率限制**: 每小时最多 5 次请求

---

## 📥 请求参数

### Request Body (JSON)

```json
{
  "product_id": 1,
  "plan_id": 10,
  "reason": "我想试用PDF压缩工具，用于工作文档处理",
  "user_info": {
    "company": "科技有限公司",
    "phone": "13800138000",
    "job_title": "产品经理",
    "intended_use": "用于处理公司内部PDF文档，提高工作效率"
  }
}
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `product_id` | Integer | **是** | 产品ID（从 API 1 获取） |
| `plan_id` | Integer | 否 | 试用方案ID。**如果不指定，系统自动选择有效期最长的方案** |
| `reason` | String | 否 | 申请原因，最多500字符 |
| `user_info` | Object | 否 | 用户补充信息对象 |
| `user_info.company` | String | 否 | 公司名称 |
| `user_info.phone` | String | 否 | 联系电话 |
| `user_info.job_title` | String | 否 | 职位/职称 |
| `user_info.intended_use` | String | 否 | 预期用途说明 |

### 请求头

```http
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
Accept: application/json
```

---

## 📤 响应格式

### ✅ 成功响应 (200 OK)

```json
{
  "success": true,
  "message": "试用许可证申请成功",
  "data": {
    "license_id": 12345,
    "assignment_id": 67890,
    "license_key": "ABCDE-12345-FGHIJ-67890-KLMNO",
    "expires_at": "2024-02-15T10:30:00Z",
    "product_name": "PDF压缩工具专业版",
    "plan_name": "14天试用版",
    "max_activations": 2
  }
}
```

### 📋 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | Boolean | 请求是否成功（true） |
| `message` | String | 成功消息 |
| `license_id` | Integer | 许可证ID（用于后续查询） |
| `assignment_id` | Integer | 许可证分配记录ID |
| `license_key` | String | **许可证密钥**（用于激活软件，请妥善保存） |
| `expires_at` | String (ISO 8601) | 许可证过期时间 |
| `product_name` | String | 产品名称 |
| `plan_name` | String | 试用方案名称 |
| `max_activations` | Integer | 最大可激活设备数量 |

---

## ❌ 错误响应

### 400 Bad Request - 业务错误

#### 1. 重复申请

```json
{
  "success": false,
  "error": "您已经拥有该产品的有效许可证",
  "code": "LICENSE_ALREADY_ASSIGNED"
}
```

**说明**: 用户已经拥有该产品的活跃许可证，无法重复申请。

---

#### 2. 配额超限

```json
{
  "success": false,
  "error": "Your trial license quota has been reached（1个）",
  "code": "LICENSE_QUOTA_EXCEEDED"
}
```

**说明**: 用户的试用许可证配额已用完（默认每个用户最多1个试用许可证）。

---

#### 3. 申请频率超限

```json
{
  "success": false,
  "error": "24hours. Too many applications, please try again later（Current limit: 3次）",
  "code": "APPLICATION_RATE_LIMIT_EXCEEDED"
}
```

**说明**: 24小时内申请次数超过限制（默认3次）。

---

#### 4. 产品不存在

```json
{
  "success": false,
  "error": "产品ID 999 不存在或不可用",
  "code": "PRODUCT_NOT_FOUND"
}
```

**说明**: 指定的产品ID不存在或已被禁用。

---

#### 5. 试用方案不存在

```json
{
  "success": false,
  "error": "试用方案ID 999 不存在或不可用",
  "code": "TRIAL_PLAN_NOT_FOUND"
}
```

**说明**: 指定的试用方案ID不存在或已被禁用。

---

#### 6. 参数验证错误

```json
{
  "success": false,
  "errors": {
    "product_id": ["This field is required."],
    "reason": ["Ensure this field has no more than 500 characters."]
  }
}
```

**说明**: 请求参数格式或内容不符合要求。

---

### 401 Unauthorized - 未认证

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 403 Forbidden - 权限不足

```json
{
  "success": false,
  "error": "您的账户已被禁止申请许可证",
  "code": "LICENSE_APPLICATION_BANNED"
}
```

**说明**: 用户账户被禁止申请许可证。

---

### 429 Too Many Requests - 频率限制

```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

**说明**: API 调用频率超限，需要等待3600秒（1小时）后重试。

---

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "系统内部错误，请稍后重试",
  "code": "INTERNAL_ERROR"
}
```

---

## 💻 前端集成代码

### JavaScript + Axios

```javascript
import axios from 'axios';

/**
 * 申请试用许可证
 * @param {number} productId - 产品ID
 * @param {number|null} planId - 试用方案ID（可选）
 * @param {object} options - 其他选项
 * @returns {Promise<object>} 许可证信息
 */
async function applyTrialLicense(productId, planId = null, options = {}) {
  try {
    const requestData = {
      product_id: productId,
      ...(planId && { plan_id: planId }), // plan_id 可选
      reason: options.reason || '试用申请',
      user_info: {
        company: options.company || '',
        phone: options.phone || '',
        job_title: options.jobTitle || '',
        intended_use: options.intendedUse || ''
      }
    };

    const response = await axios.post(
      '/api/v1/licenses/member/apply/',
      requestData,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (response.data.success) {
      const license = response.data.data;
      
      console.log('✅ 申请成功!');
      console.log('许可证密钥:', license.license_key);
      console.log('过期时间:', new Date(license.expires_at).toLocaleString());
      
      // 可选：保存到本地存储
      localStorage.setItem(`license_${license.license_id}`, license.license_key);
      
      return license;
    }
  } catch (error) {
    handleApplicationError(error);
    throw error;
  }
}

/**
 * 错误处理函数
 */
function handleApplicationError(error) {
  if (!error.response) {
    console.error('网络错误:', error.message);
    alert('网络连接失败，请检查网络后重试');
    return;
  }

  const status = error.response.status;
  const data = error.response.data;

  switch (status) {
    case 400:
      // 业务错误
      switch (data.code) {
        case 'LICENSE_ALREADY_ASSIGNED':
          alert('您已经拥有该产品的试用许可证，请勿重复申请');
          break;
        case 'LICENSE_QUOTA_EXCEEDED':
          alert('试用许可证配额已用完，请联系管理员');
          break;
        case 'APPLICATION_RATE_LIMIT_EXCEEDED':
          alert('申请过于频繁，请24小时后再试');
          break;
        case 'PRODUCT_NOT_FOUND':
          alert('产品不存在或已下架');
          break;
        case 'TRIAL_PLAN_NOT_FOUND':
          alert('试用方案不存在或已失效');
          break;
        default:
          alert(data.error || '申请失败，请检查输入');
      }
      break;

    case 401:
      // 未认证
      console.error('认证失败');
      localStorage.removeItem('jwt_token');
      window.location.href = '/login';
      break;

    case 403:
      // 权限不足
      alert('您的账户被限制申请许可证，请联系管理员');
      break;

    case 429:
      // 频率限制
      const retryAfter = error.response.headers['retry-after'] || 3600;
      alert(`请求过于频繁，请在 ${Math.ceil(retryAfter / 60)} 分钟后重试`);
      break;

    case 500:
      // 服务器错误
      alert('服务器暂时不可用，请稍后重试');
      break;

    default:
      console.error('未知错误:', error);
      alert('申请失败，请稍后重试');
  }
}

// 使用示例 1: 指定试用方案
applyTrialLicense(1, 10, {
  reason: '用于测试PDF压缩功能',
  company: '测试公司',
  phone: '13800138000',
  jobTitle: '开发工程师',
  intendedUse: '开发测试使用'
})
.then(license => {
  console.log('获得许可证:', license);
  // 显示成功页面
  showSuccessPage(license);
})
.catch(err => {
  console.error('申请失败:', err);
});

// 使用示例 2: 自动选择试用方案（不传 planId）
applyTrialLicense(1, null, {
  reason: '试用申请'
})
.then(license => {
  // 跳转到许可证详情页
  window.location.href = `/licenses/${license.license_id}`;
});
```

### React 完整申请表单组件

```javascript
import { useState } from 'react';
import axios from 'axios';

function TrialApplicationForm({ product, plan, onSuccess }) {
  const [formData, setFormData] = useState({
    reason: '',
    company: '',
    phone: '',
    jobTitle: '',
    intendedUse: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // 清除该字段的验证错误
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const errors = {};
    
    if (formData.reason && formData.reason.length > 500) {
      errors.reason = '申请原因不能超过500字符';
    }
    
    if (formData.phone && !/^1[3-9]\d{9}$/.test(formData.phone)) {
      errors.phone = '请输入有效的手机号码';
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        '/api/v1/licenses/member/apply/',
        {
          product_id: product.id,
          plan_id: plan.id,
          reason: formData.reason,
          user_info: {
            company: formData.company,
            phone: formData.phone,
            job_title: formData.jobTitle,
            intended_use: formData.intendedUse
          }
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
          }
        }
      );

      if (response.data.success) {
        // 调用成功回调
        onSuccess(response.data.data);
      }
    } catch (err) {
      const errorData = err.response?.data;
      
      if (errorData?.code) {
        // 业务错误
        const errorMessages = {
          'LICENSE_ALREADY_ASSIGNED': '您已拥有该产品的许可证',
          'LICENSE_QUOTA_EXCEEDED': '试用许可证配额已用完',
          'APPLICATION_RATE_LIMIT_EXCEEDED': '申请过于频繁，请稍后再试',
          'PRODUCT_NOT_FOUND': '产品不存在',
          'TRIAL_PLAN_NOT_FOUND': '试用方案不存在'
        };
        setError(errorMessages[errorData.code] || errorData.error);
      } else if (errorData?.errors) {
        // 参数验证错误
        setValidationErrors(errorData.errors);
      } else if (err.response?.status === 429) {
        setError('请求过于频繁，请1小时后再试');
      } else if (err.response?.status === 401) {
        window.location.href = '/login';
      } else {
        setError('申请失败，请稍后重试');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="trial-application-form">
      <div className="form-header">
        <h2>申请试用许可证</h2>
        <div className="product-info">
          <p><strong>产品:</strong> {product.name}</p>
          <p><strong>方案:</strong> {plan.name}</p>
          <p><strong>试用期:</strong> {plan.default_validity_days} 天</p>
          <p><strong>可激活设备:</strong> {plan.default_max_activations} 台</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="reason">申请原因 (可选)</label>
          <textarea
            id="reason"
            value={formData.reason}
            onChange={(e) => handleInputChange('reason', e.target.value)}
            placeholder="请简述您申请试用的原因..."
            maxLength={500}
            rows={3}
          />
          <div className="char-count">
            {formData.reason.length} / 500
          </div>
          {validationErrors.reason && (
            <span className="error-text">{validationErrors.reason}</span>
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="company">公司名称 (可选)</label>
            <input
              type="text"
              id="company"
              value={formData.company}
              onChange={(e) => handleInputChange('company', e.target.value)}
              placeholder="您的公司名称"
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">联系电话 (可选)</label>
            <input
              type="tel"
              id="phone"
              value={formData.phone}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              placeholder="手机号码"
            />
            {validationErrors.phone && (
              <span className="error-text">{validationErrors.phone}</span>
            )}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="jobTitle">职位 (可选)</label>
          <input
            type="text"
            id="jobTitle"
            value={formData.jobTitle}
            onChange={(e) => handleInputChange('jobTitle', e.target.value)}
            placeholder="您的职位"
          />
        </div>

        <div className="form-group">
          <label htmlFor="intendedUse">预期用途 (可选)</label>
          <textarea
            id="intendedUse"
            value={formData.intendedUse}
            onChange={(e) => handleInputChange('intendedUse', e.target.value)}
            placeholder="您计划如何使用该软件..."
            rows={3}
          />
        </div>

        {error && (
          <div className="alert alert-error">
            ⚠️ {error}
          </div>
        )}

        <div className="form-actions">
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                申请中...
              </>
            ) : (
              '提交申请'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

// 成功页面组件
function SuccessPage({ license }) {
  const [copied, setCopied] = useState(false);

  const copyLicenseKey = () => {
    navigator.clipboard.writeText(license.license_key)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
  };

  return (
    <div className="success-page">
      <div className="success-icon">✅</div>
      <h2>申请成功！</h2>
      <p>您的试用许可证已生成</p>

      <div className="license-details">
        <div className="detail-item">
          <label>产品名称</label>
          <span>{license.product_name}</span>
        </div>
        
        <div className="detail-item">
          <label>试用方案</label>
          <span>{license.plan_name}</span>
        </div>
        
        <div className="detail-item">
          <label>许可证密钥</label>
          <div className="license-key-box">
            <code className="license-key">{license.license_key}</code>
            <button onClick={copyLicenseKey} className="btn-copy">
              {copied ? '已复制' : '复制'}
            </button>
          </div>
        </div>
        
        <div className="detail-item">
          <label>过期时间</label>
          <span>{new Date(license.expires_at).toLocaleString('zh-CN')}</span>
        </div>
        
        <div className="detail-item">
          <label>可激活设备</label>
          <span>{license.max_activations} 台</span>
        </div>
      </div>

      <div className="next-steps">
        <h3>下一步</h3>
        <ol>
          <li>复制上方的许可证密钥</li>
          <li>下载并安装软件</li>
          <li>在软件中输入许可证密钥进行激活</li>
        </ol>
      </div>

      <div className="actions">
        <button className="btn btn-primary" onClick={() => window.location.href = '/downloads'}>
          下载软件
        </button>
        <button className="btn btn-secondary" onClick={() => window.location.href = '/licenses'}>
          查看我的许可证
        </button>
      </div>
    </div>
  );
}

// 使用示例
function App() {
  const [showSuccess, setShowSuccess] = useState(false);
  const [licenseData, setLicenseData] = useState(null);

  const handleSuccess = (license) => {
    setLicenseData(license);
    setShowSuccess(true);
  };

  if (showSuccess && licenseData) {
    return <SuccessPage license={licenseData} />;
  }

  return (
    <TrialApplicationForm
      product={{ id: 1, name: 'PDF压缩工具' }}
      plan={{ id: 10, name: '14天试用版', default_validity_days: 14, default_max_activations: 2 }}
      onSuccess={handleSuccess}
    />
  );
}
```

### cURL 示例

```bash
# 完整参数
curl -X POST "https://backend.espressox.online/api/v1/licenses/member/apply/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "plan_id": 10,
    "reason": "试用PDF压缩工具",
    "user_info": {
      "company": "测试公司",
      "phone": "13800138000",
      "job_title": "开发工程师",
      "intended_use": "开发测试使用"
    }
  }'

# 最简参数（自动选择试用方案）
curl -X POST "https://backend.espressox.online/api/v1/licenses/member/apply/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1
  }'
```

---

## 🔄 完整业务流程

```
用户在产品页面选择方案
    ↓
点击"申请试用"按钮
    ↓
显示申请表单（填写可选信息）
    ↓
用户填写并提交表单
    ↓
前端验证表单数据
    ↓
调用申请 API
    ↓
后端验证：
  ├─ 认证和权限检查
  ├─ 产品和方案存在性
  ├─ 重复申请检查
  ├─ 配额限制检查
  └─ 频率限制检查
    ↓
生成许可证密钥和分配记录
    ↓
返回许可证信息
    ↓
前端显示成功页面
    ↓
用户复制许可证密钥
    ↓
用户下载软件并激活
```

---

## 📝 重要注意事项

### 1. **plan_id 参数**
- 可选参数，如果不传系统自动选择有效期最长的方案
- 推荐做法：如果产品只有一个方案，不传此参数；如果有多个方案，让用户选择

### 2. **许可证密钥保管**
- 申请成功后立即获得许可证密钥
- 前端必须提供复制功能
- 建议发送确认邮件（后端处理）
- 用户可在"我的许可证"页面查看

### 3. **配额限制**
- 默认每个用户最多1个试用许可证
- 超过配额返回 `LICENSE_QUOTA_EXCEEDED` 错误
- 需要更多许可证请联系管理员

### 4. **频率限制**
- API 级别：每小时最多5次请求
- 业务级别：24小时内最多3次申请
- 超限需等待冷却时间

### 5. **重复申请**
- 同一产品只能申请一次试用
- 如需再次试用，需先删除或等待当前许可证过期

### 6. **有效期计算**
- 从申请成功时刻开始计算
- 不是从激活时刻开始
- 建议用户尽快激活使用

### 7. **错误处理**
- 所有业务错误都有明确的 `code` 字段
- 前端应根据不同错误码提供友好提示
- 401 错误自动跳转登录页

---

## 🎨 UI/UX 建议

### 表单设计
- 所有补充信息都是可选的，降低填写门槛
- 提供字符计数提示
- 实时验证手机号格式
- 提交按钮显示 loading 状态

### 成功页面
- 突出显示许可证密钥
- 提供一键复制功能
- 显示过期时间和激活限制
- 提供"下载软件"和"查看许可证"快捷入口

### 错误提示
- 配额超限：引导联系管理员
- 重复申请：引导查看现有许可证
- 频率限制：显示具体等待时间

---

[返回文档导航](./README.md) | [下一个API: 查看我的许可证](./API-3-查看我的许可证.md)
