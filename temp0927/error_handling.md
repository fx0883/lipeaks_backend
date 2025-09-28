# 错误处理指南

## 🎯 错误处理概述

在集成许可证创建API时，正确的错误处理是确保用户体验的关键。本指南详细说明各种错误情况及其处理方法。

## 📋 HTTP状态码说明

| 状态码 | 说明 | 触发条件 |
|--------|------|----------|
| 200 | 成功 | 请求处理成功 |
| 201 | 创建成功 | 许可证创建成功 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 认证失败 | JWT令牌无效或过期 |
| 403 | 权限不足 | 用户权限不够 |
| 404 | 资源不存在 | 方案或租户不存在 |
| 429 | 请求过频 | API调用频率超限 |
| 500 | 服务器错误 | 内部系统错误 |

## 🚨 常见错误类型及处理

### 1. 参数验证错误 (400)

#### 错误响应示例
```javascript
{
  "detail": "验证失败",
  "errors": {
    "plan": ["必需字段"],
    "customer_info": {
      "name": ["此字段不能为空"],
      "email": ["请输入有效的邮箱地址"]
    },
    "max_activations": ["确保该值大于等于1"]
  }
}
```

#### 处理方法
```javascript
const handleValidationError = (errorResponse) => {
  const errors = errorResponse.errors;
  const fieldErrors = {};
  
  // 递归处理嵌套错误
  const processErrors = (errorObj, prefix = '') => {
    for (const [field, messages] of Object.entries(errorObj)) {
      const fieldName = prefix ? `${prefix}.${field}` : field;
      
      if (Array.isArray(messages)) {
        fieldErrors[fieldName] = messages.join(', ');
      } else if (typeof messages === 'object') {
        processErrors(messages, fieldName);
      }
    }
  };
  
  processErrors(errors);
  return fieldErrors;
};

// 使用示例
try {
  const response = await createLicense(licenseData);
} catch (error) {
  if (error.status === 400) {
    const fieldErrors = handleValidationError(error.data);
    
    // 显示字段错误
    Object.entries(fieldErrors).forEach(([field, message]) => {
      showFieldError(field, message);
    });
  }
}
```

#### React表单错误显示
```jsx
const CreateLicenseForm = () => {
  const [fieldErrors, setFieldErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  
  const handleSubmit = async (formData) => {
    try {
      setFieldErrors({});
      setGeneralError('');
      
      const license = await createLicense(formData);
      // 处理成功...
    } catch (error) {
      if (error.status === 400) {
        const errors = handleValidationError(error.data);
        setFieldErrors(errors);
      } else {
        setGeneralError('创建许可证失败，请稍后重试');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <input name="customer_name" />
        {fieldErrors['customer_info.name'] && (
          <div className="error">{fieldErrors['customer_info.name']}</div>
        )}
      </div>
      
      <div className="form-group">
        <input type="email" name="customer_email" />
        {fieldErrors['customer_info.email'] && (
          <div className="error">{fieldErrors['customer_info.email']}</div>
        )}
      </div>
      
      {generalError && (
        <div className="general-error">{generalError}</div>
      )}
      
      <button type="submit">创建许可证</button>
    </form>
  );
};
```

### 2. 认证错误 (401)

#### 错误响应示例
```javascript
{
  "detail": "身份验证凭据无效。",
  "code": "token_not_valid"
}
```

#### 处理方法
```javascript
const handleAuthError = async (error) => {
  if (error.status === 401) {
    // 尝试刷新令牌
    try {
      const newToken = await refreshAuthToken();
      updateAuthToken(newToken);
      
      // 重试原始请求
      return await retryOriginalRequest();
    } catch (refreshError) {
      // 刷新失败，重定向到登录页
      redirectToLogin();
    }
  }
};

const createLicenseWithRetry = async (licenseData, retryCount = 0) => {
  try {
    const response = await fetch('/api/v1/licenses/admin/licenses/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify(licenseData)
    });
    
    if (response.status === 401 && retryCount === 0) {
      // 尝试刷新令牌并重试
      await handleAuthError({ status: 401 });
      return createLicenseWithRetry(licenseData, 1);
    }
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    throw error;
  }
};
```

### 3. 权限错误 (403)

#### 错误响应示例
```javascript
{
  "detail": "您没有权限执行此操作。",
  "code": "permission_denied"
}
```

#### 处理方法
```javascript
const handlePermissionError = (error) => {
  if (error.status === 403) {
    // 显示权限不足提示
    showMessage({
      type: 'error',
      title: '权限不足',
      message: '您没有创建许可证的权限，请联系管理员。',
      actions: [
        {
          label: '联系管理员',
          action: () => openSupportDialog()
        },
        {
          label: '返回',
          action: () => history.goBack()
        }
      ]
    });
    
    // 记录权限错误日志
    logSecurityEvent({
      event: 'permission_denied',
      resource: 'license_creation',
      user: getCurrentUser(),
      timestamp: new Date().toISOString()
    });
  }
};
```

### 4. 资源不存在错误 (404)

#### 错误响应示例
```javascript
{
  "detail": "未找到指定的许可证方案。",
  "code": "not_found"
}
```

#### 处理方法
```javascript
const handleNotFoundError = async (error, field) => {
  if (error.status === 404) {
    switch (field) {
      case 'plan':
        // 刷新方案列表
        await refreshPlansList();
        showMessage({
          type: 'warning',
          message: '选择的方案不存在，请重新选择方案。'
        });
        break;
        
      case 'tenant':
        // 刷新租户列表
        await refreshTenantsList();
        showMessage({
          type: 'warning',
          message: '选择的租户不存在，请重新选择租户。'
        });
        break;
        
      default:
        showMessage({
          type: 'error',
          message: '请求的资源不存在，请刷新页面后重试。'
        });
    }
  }
};
```

### 5. 频率限制错误 (429)

#### 错误响应示例
```javascript
{
  "detail": "请求过于频繁，请稍后再试。",
  "retry_after": 60
}
```

#### 处理方法
```javascript
const handleRateLimitError = (error) => {
  if (error.status === 429) {
    const retryAfter = error.data.retry_after || 60;
    
    showMessage({
      type: 'warning',
      title: '请求过于频繁',
      message: `请等待 ${retryAfter} 秒后再次尝试。`,
      duration: retryAfter * 1000
    });
    
    // 设置重试定时器
    setTimeout(() => {
      enableRetryButton();
    }, retryAfter * 1000);
    
    return { shouldRetry: true, retryAfter };
  }
};
```

### 6. 服务器错误 (500)

#### 错误响应示例
```javascript
{
  "detail": "许可证创建失败，请联系系统管理员。",
  "code": "internal_server_error",
  "request_id": "req_123456789"
}
```

#### 处理方法
```javascript
const handleServerError = (error) => {
  if (error.status === 500) {
    const requestId = error.data.request_id;
    
    showMessage({
      type: 'error',
      title: '服务器错误',
      message: '服务器出现错误，请稍后重试或联系技术支持。',
      details: requestId ? `错误ID: ${requestId}` : null,
      actions: [
        {
          label: '重试',
          action: () => retryRequest()
        },
        {
          label: '联系技术支持',
          action: () => openSupportDialog(requestId)
        }
      ]
    });
    
    // 自动上报错误
    reportError({
      type: 'server_error',
      requestId,
      url: error.url,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent
    });
  }
};
```

## 🔧 完整错误处理框架

### 1. 统一错误处理类
```javascript
class LicenseAPIError extends Error {
  constructor(status, data, url) {
    super(data.detail || '未知错误');
    this.status = status;
    this.data = data;
    this.url = url;
    this.timestamp = new Date().toISOString();
  }
}

class LicenseAPIClient {
  constructor(baseUrl, getToken) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
    this.retryConfig = {
      maxRetries: 3,
      backoffMultiplier: 2,
      baseDelay: 1000
    };
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    let lastError;
    
    for (let attempt = 0; attempt < this.retryConfig.maxRetries; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.getToken()}`,
            ...options.headers
          }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          throw new LicenseAPIError(response.status, data, url);
        }
        
        return data;
      } catch (error) {
        lastError = error;
        
        // 判断是否应该重试
        if (!this.shouldRetry(error, attempt)) {
          break;
        }
        
        // 等待后重试
        const delay = this.calculateDelay(attempt);
        await this.sleep(delay);
      }
    }
    
    throw lastError;
  }
  
  shouldRetry(error, attempt) {
    // 最后一次尝试不重试
    if (attempt >= this.retryConfig.maxRetries - 1) {
      return false;
    }
    
    // 网络错误重试
    if (!error.status) {
      return true;
    }
    
    // 服务器错误重试
    if (error.status >= 500) {
      return true;
    }
    
    // 认证错误尝试一次刷新
    if (error.status === 401 && attempt === 0) {
      return true;
    }
    
    return false;
  }
  
  calculateDelay(attempt) {
    return this.retryConfig.baseDelay * 
           Math.pow(this.retryConfig.backoffMultiplier, attempt);
  }
  
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  async createLicense(licenseData) {
    return await this.request('/licenses/', {
      method: 'POST',
      body: JSON.stringify(licenseData)
    });
  }
}
```

### 2. React错误边界组件
```jsx
class LicenseErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error, errorInfo) {
    // 上报错误
    this.reportError(error, errorInfo);
  }
  
  reportError(error, errorInfo) {
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent
    };
    
    // 发送到错误监控系统
    fetch('/api/errors/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorReport)
    });
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>许可证创建组件出现错误</h2>
          <p>我们已经记录了这个错误，请刷新页面重试。</p>
          <button onClick={() => window.location.reload()}>
            刷新页面
          </button>
          <button onClick={() => this.setState({ hasError: false })}>
            重试
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

### 3. Vue.js错误处理插件
```javascript
const LicenseErrorHandler = {
  install(Vue) {
    // 全局错误处理器
    Vue.config.errorHandler = (error, vm, info) => {
      console.error('Vue Error:', error);
      
      // 上报错误
      this.reportError(error, {
        component: vm?.$options.name,
        info,
        route: vm?.$route?.path
      });
      
      // 显示用户友好的错误提示
      this.showUserError(error);
    };
    
    // 添加全局方法
    Vue.prototype.$handleLicenseError = this.handleError;
  },
  
  handleError(error) {
    if (error instanceof LicenseAPIError) {
      switch (error.status) {
        case 400:
          this.handleValidationError(error);
          break;
        case 401:
          this.handleAuthError(error);
          break;
        case 403:
          this.handlePermissionError(error);
          break;
        default:
          this.showGenericError(error);
      }
    } else {
      this.showGenericError(error);
    }
  }
};
```

## 📊 错误监控和分析

### 1. 错误统计收集
```javascript
class ErrorAnalytics {
  constructor() {
    this.errors = [];
    this.config = {
      maxErrors: 1000,
      reportInterval: 300000 // 5分钟
    };
    
    // 定期上报错误统计
    setInterval(() => {
      this.reportErrorStats();
    }, this.config.reportInterval);
  }
  
  recordError(error) {
    const errorRecord = {
      timestamp: new Date().toISOString(),
      type: error.constructor.name,
      status: error.status,
      message: error.message,
      url: error.url,
      userAgent: navigator.userAgent,
      userId: getCurrentUserId()
    };
    
    this.errors.push(errorRecord);
    
    // 限制内存使用
    if (this.errors.length > this.config.maxErrors) {
      this.errors = this.errors.slice(-this.config.maxErrors);
    }
  }
  
  async reportErrorStats() {
    if (this.errors.length === 0) return;
    
    const stats = this.generateErrorStats();
    
    try {
      await fetch('/api/analytics/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(stats)
      });
      
      // 清空已上报的错误
      this.errors = [];
    } catch (error) {
      console.error('错误统计上报失败:', error);
    }
  }
  
  generateErrorStats() {
    const statusCounts = {};
    const messageCounts = {};
    const hourlyDistribution = new Array(24).fill(0);
    
    this.errors.forEach(error => {
      // 统计状态码分布
      statusCounts[error.status] = (statusCounts[error.status] || 0) + 1;
      
      // 统计错误消息分布
      messageCounts[error.message] = (messageCounts[error.message] || 0) + 1;
      
      // 统计时间分布
      const hour = new Date(error.timestamp).getHours();
      hourlyDistribution[hour]++;
    });
    
    return {
      totalErrors: this.errors.length,
      statusCounts,
      messageCounts,
      hourlyDistribution,
      timeRange: {
        start: this.errors[0]?.timestamp,
        end: this.errors[this.errors.length - 1]?.timestamp
      }
    };
  }
}

const errorAnalytics = new ErrorAnalytics();
```

### 2. 用户体验指标
```javascript
const trackUserExperience = {
  // 记录许可证创建成功率
  recordCreationAttempt(success, error = null) {
    const metric = {
      timestamp: new Date().toISOString(),
      success,
      error: error ? {
        status: error.status,
        type: error.constructor.name
      } : null,
      userId: getCurrentUserId(),
      sessionId: getSessionId()
    };
    
    // 发送到分析系统
    this.sendMetric('license_creation_attempt', metric);
  },
  
  // 记录用户重试行为
  recordRetryAttempt(originalError, retryCount) {
    this.sendMetric('license_creation_retry', {
      originalError: originalError.status,
      retryCount,
      timestamp: new Date().toISOString()
    });
  },
  
  // 记录用户放弃操作
  recordAbandon(lastError) {
    this.sendMetric('license_creation_abandon', {
      lastError: lastError?.status,
      timestamp: new Date().toISOString()
    });
  },
  
  sendMetric(event, data) {
    fetch('/api/analytics/metrics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event, data })
    });
  }
};
```

## 🎯 最佳实践总结

### 1. 错误处理原则
- **用户友好**: 显示易懂的错误信息
- **可操作性**: 提供明确的解决方案
- **容错性**: 优雅处理异常情况
- **可追踪**: 记录详细的错误信息

### 2. 实现建议
- 统一错误处理入口
- 区分用户错误和系统错误
- 实现自动重试机制
- 提供错误恢复方案

### 3. 用户体验优化
- 显示详细但不技术化的错误信息
- 提供具体的操作指导
- 实现错误状态的可视化反馈
- 支持一键重试和求助功能

### 4. 开发调试
- 在开发环境显示详细错误
- 在生产环境隐藏敏感信息
- 实现错误边界和降级方案
- 建立错误监控和告警机制

---

**下一步**: 查看 [代码示例](code_examples.md) 获取完整的实现代码。
