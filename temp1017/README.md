# Member 许可证 API 前端集成文档

## 📚 文档导航

本目录包含完整的 Member 许可证管理 API 前端集成文档，每个 API 都有详细的说明、参数解释和代码示例。

### 📖 文档列表

1. **[API-1-获取可申请的试用产品列表.md](./API-1-获取可申请的试用产品列表.md)**
   - GET `/api/v1/licenses/member/available-products/`
   - 浏览可申请的软件产品和试用方案

2. **[API-2-申请试用许可证.md](./API-2-申请试用许可证.md)**
   - POST `/api/v1/licenses/member/apply/`
   - 提交试用许可证申请，获取许可证密钥

3. **[API-3-查看我的许可证.md](./API-3-查看我的许可证.md)**
   - GET `/api/v1/licenses/member/my-licenses/`
   - 查看用户拥有的所有许可证

4. **[API-4-查看许可证的设备列表.md](./API-4-查看许可证的设备列表.md)**
   - GET `/api/v1/licenses/member/my-licenses/{license_id}/devices/`
   - 查看指定许可证已激活的设备列表

5. **[API-5-解绑设备.md](./API-5-解绑设备.md)**
   - POST `/api/v1/licenses/member/unbind-device/`
   - 解绑不使用的设备，释放激活配额

---

## 🚀 快速开始

### 基础配置

**Base URL**
```
https://backend.espressox.online/api/v1/licenses
```

**通用请求头**
```javascript
{
  'Authorization': `Bearer ${jwt_token}`,
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}
```

### Axios 配置示例

```javascript
import axios from 'axios';

// 创建 Axios 实例
const apiClient = axios.create({
  baseURL: 'https://backend.espressox.online/api/v1/licenses',
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器 - 自动添加 Token
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token 过期，跳转登录
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      // 频率限制
      alert('请求过于频繁，请稍后再试');
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## 🔐 认证说明

所有 API 都需要 JWT 认证：

1. 用户登录后获取 JWT Token
2. 将 Token 存储在 localStorage 或其他安全位置
3. 每次请求在 Authorization 头中携带 Token
4. Token 格式：`Bearer <your_jwt_token>`

**示例**
```javascript
const token = localStorage.getItem('jwt_token');
axios.get('/api/v1/licenses/member/my-licenses/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

---

## 📋 业务流程图

```
┌─────────────────────────────────────────────────┐
│                 用户访问产品页面                   │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  API 1: 获取可申请的试用产品列表                   │
│  GET /member/available-products/                 │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│              前端展示产品和试用方案                  │
│         用户选择产品和方案，填写申请表单              │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  API 2: 申请试用许可证                            │
│  POST /member/apply/                             │
│  → 返回许可证密钥                                  │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│           用户复制许可证密钥，下载软件              │
│              在软件中输入密钥激活                   │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  API 3: 查看我的许可证                            │
│  GET /member/my-licenses/                        │
│  → 显示所有许可证和激活状态                         │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  API 4: 查看许可证的设备列表                       │
│  GET /member/my-licenses/{id}/devices/          │
│  → 显示已激活的设备列表                            │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│       用户需要更换设备或释放激活配额                │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  API 5: 解绑设备                                  │
│  POST /member/unbind-device/                     │
│  → 释放设备激活配额                                │
└─────────────────────────────────────────────────┘
```

---

## ⚠️ 常见错误处理

### 401 Unauthorized
```javascript
// Token 无效或过期
if (error.response?.status === 401) {
  localStorage.removeItem('jwt_token');
  window.location.href = '/login';
}
```

### 403 Forbidden
```javascript
// 权限不足（非 Member 用户）
if (error.response?.status === 403) {
  alert('您没有权限执行此操作');
}
```

### 429 Too Many Requests
```javascript
// 请求频率限制
if (error.response?.status === 429) {
  const retryAfter = error.response.headers['retry-after'] || 3600;
  alert(`请求过于频繁，请在 ${retryAfter} 秒后重试`);
}
```

### 400 Bad Request
```javascript
// 业务错误
if (error.response?.status === 400) {
  const errorData = error.response.data;
  switch (errorData.code) {
    case 'LICENSE_ALREADY_ASSIGNED':
      alert('您已拥有该产品的许可证');
      break;
    case 'LICENSE_QUOTA_EXCEEDED':
      alert('试用许可证配额已用完');
      break;
    default:
      alert(errorData.error || '请求失败');
  }
}
```

---

## 🎯 最佳实践

### 1. 错误处理
- 始终使用 try-catch 包裹异步请求
- 为不同的错误状态码提供友好的用户提示
- 记录错误日志便于调试

### 2. 加载状态
- 请求期间显示 loading 状态
- 防止重复提交
- 提供取消请求的选项

### 3. 数据缓存
- 产品列表可缓存 5-10 分钟
- 许可证列表缓存 1-2 分钟
- 使用 SWR 或 React Query 等工具

### 4. 用户体验
- 提供清晰的操作提示和反馈
- 重要操作前显示确认对话框
- 许可证密钥支持一键复制

### 5. 安全考虑
- Token 安全存储
- HTTPS 传输
- 不在 URL 中暴露敏感信息
- 定期刷新 Token

---

## 📱 完整代码示例

请查看各个 API 的详细文档，每个文档都包含完整的：
- 请求/响应示例
- JavaScript/Axios 代码
- React Hooks 实现
- Vue Composition API 示例
- 错误处理代码
- cURL 命令

---

## 📞 技术支持

如有问题，请联系：
- **API 文档**: https://backend.espressox.online/api/schema/swagger-ui/
- **技术支持**: support@espressox.online
