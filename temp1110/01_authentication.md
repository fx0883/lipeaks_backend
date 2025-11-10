# 1. 认证系统 API 集成指南

## 🎯 概述

认证系统提供完整的用户身份验证功能，包括注册、登录、Token管理等。支持Member（会员用户）和Admin（管理员）两种用户类型。

## 📋 API 列表

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| [用户注册](#用户注册) | POST | `/auth/member/register/` | Member用户注册 |
| [用户登录](#用户登录) | POST | `/auth/login/` | 用户登录（支持Member/Admin） |
| [Token刷新](#token刷新) | POST | `/auth/refresh/` | 刷新Access Token |
| [Token验证](#token验证) | GET | `/auth/verify/` | 验证Token有效性 |
| [密码重置请求](#密码重置请求) | POST | `/auth/password-reset/request/` | 请求密码重置邮件 |

---

## 用户注册

### 接口信息
- **接口地址**: `POST /api/v1/auth/member/register/`
- **权限要求**: 无需认证，匿名访问
- **功能说明**: Member用户在指定租户下注册账号

### 请求头
```bash
X-Tenant-ID: {tenant_id}  # Member用户注册时必须指定租户
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|----------|
| username | string | 是 | 用户名，全局唯一 | "member001" | 3-30字符，只能包含字母、数字、下划线 |
| email | string | 是 | 邮箱地址，全局唯一 | "member001@example.com" | 有效的邮箱格式 |
| password | string | 是 | 登录密码 | "password123" | 最少8字符，包含大小写字母和数字 |
| password_confirm | string | 是 | 密码确认 | "password123" | 必须与password完全相同 |
| phone | string | 否 | 手机号码，租户内唯一 | "13800138000" | 有效的手机号码格式 |
| nick_name | string | 否 | 昵称 | "测试用户" | 最长50字符 |
| wechat_id | string | 否 | 微信ID | "wechat123" | 最长100字符 |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/auth/member/register/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "username": "member001",
    "email": "member001@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "phone": "13800138000",
    "nick_name": "测试用户"
  }'
```

#### JavaScript (Fetch API)
```javascript
const registerUser = async (userData) => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/auth/member/register/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': '1'
      },
      body: JSON.stringify({
        username: 'member001',
        email: 'member001@example.com',
        password: 'password123',
        password_confirm: 'password123',
        phone: '13800138000',
        nick_name: '测试用户'
      })
    });

    const result = await response.json();

    if (result.success) {
      console.log('注册成功:', result.data);
      // 保存token
      localStorage.setItem('access_token', result.data.token);
      localStorage.setItem('refresh_token', result.data.refresh_token);
    } else {
      console.error('注册失败:', result.message);
    }
  } catch (error) {
    console.error('网络错误:', error);
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "注册成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo4LCJ1c2VybmFtZSI6InRlc3R1c2VyNDU2IiwiZXhwIjoxNzYzMzYxODMyLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.zNcPDHIE4saKExOnE081DJj1UDEJMZ0pAeWpMZZdlS4",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo4LCJtb2RlbF90eXBlIjoibWVtYmVyIiwiZXhwIjoxNzY1MTc2MjMyLCJ0b2tlbl90eXBlIjoicmVmcmVzaCJ9.g-nlMbFqGUsfocoUuHu2cMjAR9yZcHxY5pAnF8v96So",
    "user": {
      "id": 8,
      "username": "testuser456",
      "email": "test456@example.com",
      "nick_name": "",
      "avatar": "",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
      "tenant_id": 1,
      "tenant_name": "金sir"
    }
  }
}
```

### 错误响应
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "username": ["Username already used in this tenant"],
    "email": ["Email already exists"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

---

## 用户登录

### 接口信息
- **接口地址**: `POST /api/v1/auth/login/`
- **权限要求**: 无需认证，匿名访问
- **功能说明**: 用户登录，支持Member和Admin用户

### 请求头
```bash
X-Tenant-ID: {tenant_id}  # Member用户必填，Admin用户禁止
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| username | string | 是 | 用户名或邮箱 | "member001" 或 "admin@example.com" | 有效的用户名或邮箱格式 |
| password | string | 是 | 登录密码 | "password123" | 最少1字符 |
| tenant_id | integer | 否 | 租户ID（当X-Tenant-ID缺失时使用） | 1 | 有效的租户ID |

### 使用示例

#### cURL 命令 - Member登录
```bash
curl -X POST "https://your-domain.com/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "username": "member001",
    "password": "password123"
  }'
```

#### cURL 命令 - Admin登录
```bash
curl -X POST "https://your-domain.com/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

#### JavaScript 登录函数
```javascript
const loginUser = async (username, password, isAdmin = false) => {
  const headers = {
    'Content-Type': 'application/json'
  };

  // Member用户需要租户ID，Admin用户不需要
  if (!isAdmin) {
    headers['X-Tenant-ID'] = '1';
  }

  try {
    const response = await fetch('https://your-domain.com/api/v1/auth/login/', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        username: username,
        password: password
      })
    });

    const result = await response.json();

    if (result.success) {
      // 保存token
      localStorage.setItem('access_token', result.data.token);
      localStorage.setItem('refresh_token', result.data.refresh_token);
      localStorage.setItem('user_info', JSON.stringify(result.data.user));

      console.log('登录成功:', result.data.user);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('登录失败:', error.message);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 10,
      "username": "member001",
      "email": "member001@example.com",
      "nick_name": "测试用户",
      "avatar": "/media/avatars/avatar_10.jpg",
      "is_member": true,
      "is_admin": false,
      "is_super_admin": false,
      "is_sub_account": false,
      "tenant_id": 1,
      "tenant_name": "测试租户"
    }
  }
}
```

---

## Token刷新

### 接口信息
- **接口地址**: `POST /api/v1/auth/refresh/`
- **权限要求**: 无需认证，匿名访问
- **功能说明**: 使用Refresh Token刷新Access Token

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| refresh_token | string | 是 | 刷新令牌 | "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | 有效的JWT refresh token |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/auth/refresh/" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

#### JavaScript Token刷新函数
```javascript
const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');

  if (!refreshToken) {
    throw new Error('没有找到刷新令牌');
  }

  try {
    const response = await fetch('https://your-domain.com/api/v1/auth/refresh/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        refresh_token: refreshToken
      })
    });

    const result = await response.json();

    if (result.success) {
      // 更新本地存储的token
      localStorage.setItem('access_token', result.data.token);
      localStorage.setItem('refresh_token', result.data.refresh_token);

      console.log('Token刷新成功');
      return result.data.token;
    } else {
      // 刷新失败，清除本地存储
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_info');

      throw new Error(result.message);
    }
  } catch (error) {
    console.error('Token刷新失败:', error.message);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "Token refreshed successfully",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...new",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...new"
  }
}
```

---

## Token验证

### 接口信息
- **接口地址**: `GET /api/v1/auth/verify/`
- **权限要求**: 需要有效的Access Token
- **功能说明**: 验证Access Token有效性并返回用户信息

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}  # Member用户必填
```

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/auth/verify/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript Token验证函数
```javascript
const verifyToken = async () => {
  const token = localStorage.getItem('access_token');

  if (!token) {
    return { valid: false, reason: 'no_token' };
  }

  try {
    const response = await fetch('https://your-domain.com/api/v1/auth/verify/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': '1'  // Member用户需要
      }
    });

    const result = await response.json();

    if (result.success) {
      // Token有效，更新用户信息
      localStorage.setItem('user_info', JSON.stringify(result.data));
      return { valid: true, user: result.data };
    } else {
      // Token无效，清除本地存储
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      return { valid: false, reason: result.message };
    }
  } catch (error) {
    console.error('Token验证失败:', error);
    return { valid: false, reason: 'network_error' };
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "Token is valid",
  "data": {
    "id": 10,
    "username": "member001",
    "email": "member001@example.com",
    "nick_name": "测试用户",
    "avatar": "/media/avatars/avatar_10.jpg",
    "is_member": true,
    "is_admin": false,
    "is_super_admin": false,
    "is_sub_account": false,
    "tenant_id": 1,
    "tenant_name": "测试租户"
  }
}
```

---

## 密码重置请求

### 接口信息
- **接口地址**: `POST /api/v1/auth/password-reset/request/`
- **权限要求**: 无需认证，匿名访问
- **功能说明**: 请求密码重置邮件/短信

### 请求头
```bash
X-Tenant-ID: {tenant_id}  # Member用户必填，Admin用户禁止
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| username | string | 否 | 用户名或邮箱 | "member001" | 有效的用户名或邮箱格式 |
| email | string | 否 | 邮箱地址 | "user@example.com" | 有效的邮箱格式 |
| phone | string | 否 | 手机号码 | "13800138000" | 有效的手机号码格式 |
| tenant_id | integer | 否 | 租户ID（当X-Tenant-ID缺失时使用） | 1 | 有效的租户ID |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/auth/password-reset/request/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "email": "member001@example.com"
  }'
```

#### JavaScript 密码重置请求函数
```javascript
const requestPasswordReset = async (identifier) => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/auth/password-reset/request/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': '1'  // Member用户需要
      },
      body: JSON.stringify({
        email: identifier  // 或 username 或 phone
      })
    });

    const result = await response.json();

    // 注意：无论用户是否存在都会返回成功，避免用户名枚举攻击
    if (result.success) {
      console.log('密码重置邮件已发送，请检查邮箱');
      return true;
    } else {
      console.error('请求失败:', result.message);
      return false;
    }
  } catch (error) {
    console.error('网络错误:', error);
    return false;
  }
};
```

### 响应说明
无论用户是否存在，接口都会返回成功响应，这是为了防止用户名枚举攻击。

```json
{
  "success": true,
  "code": 2000,
  "message": "如果账号存在，重置邮件已发送",
  "data": null
}
```

---

## 🔧 前端集成最佳实践

### 1. Token管理
```javascript
class AuthManager {
  constructor() {
    this.baseURL = 'https://your-domain.com/api/v1';
    this.tenantId = '1'; // 从配置文件获取
  }

  // 自动刷新Token
  async refreshTokenIfNeeded() {
    const token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    if (!token || !refreshToken) {
      throw new Error('未登录');
    }

    // 检查token是否即将过期（这里可以添加过期时间检查逻辑）
    try {
      const response = await fetch(`${this.baseURL}/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
      });

      const result = await response.json();

      if (result.success) {
        localStorage.setItem('access_token', result.data.token);
        localStorage.setItem('refresh_token', result.data.refresh_token);
        return result.data.token;
      } else {
        // 刷新失败，清除登录状态
        this.logout();
        throw new Error('登录已过期，请重新登录');
      }
    } catch (error) {
      this.logout();
      throw error;
    }
  }

  // 通用API请求方法（自动处理认证和token刷新）
  async apiRequest(url, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    // 添加认证头
    const token = localStorage.getItem('access_token');
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    // Member用户添加租户头
    const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
    if (userInfo.is_member) {
      headers['X-Tenant-ID'] = this.tenantId;
    }

    try {
      let response = await fetch(url, { ...options, headers });

      // 如果token过期，尝试刷新
      if (response.status === 401) {
        try {
          await this.refreshTokenIfNeeded();
          // 重新获取token并重试请求
          const newToken = localStorage.getItem('access_token');
          headers.Authorization = `Bearer ${newToken}`;
          response = await fetch(url, { ...options, headers });
        } catch (refreshError) {
          throw new Error('登录已过期，请重新登录');
        }
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message || '请求失败');
      }

      return result;
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  }

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');
    // 重定向到登录页面
    window.location.href = '/login';
  }
}

// 使用示例
const auth = new AuthManager();

// 登录
await auth.apiRequest('/auth/login/', {
  method: 'POST',
  body: JSON.stringify({ username: 'user', password: 'pass' })
});

// 获取用户信息
const userInfo = await auth.apiRequest('/members/me/');
```

### 2. 错误处理
```javascript
const handleApiError = (error, context) => {
  console.error(`${context}失败:`, error.message);

  // 根据错误类型处理
  if (error.message.includes('登录已过期')) {
    // 重定向到登录页面
    window.location.href = '/login';
  } else if (error.message.includes('网络错误')) {
    // 显示网络错误提示
    showToast('网络连接失败，请检查网络后重试', 'error');
  } else {
    // 显示通用错误提示
    showToast(error.message, 'error');
  }
};
```

### 3. 登录状态检查
```javascript
const checkLoginStatus = async () => {
  const token = localStorage.getItem('access_token');

  if (!token) {
    return { loggedIn: false };
  }

  try {
    const response = await fetch('/api/v1/auth/verify/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      return {
        loggedIn: true,
        user: result.data
      };
    } else {
      // Token无效，清除登录状态
      localStorage.clear();
      return { loggedIn: false };
    }
  } catch (error) {
    console.error('登录状态检查失败:', error);
    return { loggedIn: false };
  }
};
```
