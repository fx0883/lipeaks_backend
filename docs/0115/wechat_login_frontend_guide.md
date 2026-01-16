# 微信小程序登录 - 前端接入文档

> 版本：v1.0 | 更新时间：2026-01-15

## 概述

本文档说明如何在微信小程序前端接入后端登录 API。

---

## 接口信息

| 项目 | 说明 |
|------|------|
| 接口地址 | `POST /api/v1/wechat/login/` |
| 请求格式 | `application/json` |
| 认证 | 无需认证（公开接口） |

---

## 登录流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  小程序端   │────▶│   后端服务   │────▶│   微信服务   │
│             │     │             │     │             │
│ 1. wx.login │     │ 2. code2Sess│     │ 3. 返回     │
│    获取code │◀────│    换取信息 │◀────│    openid   │
│             │     │             │     │             │
│ 4. 收到JWT  │◀────│ 5. 返回token│     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 请求参数

```typescript
interface WechatLoginRequest {
  code: string;        // 必填，wx.login() 返回的临时登录凭证
  tenant_id?: number;  // 可选，首次登录时指定租户ID
}
```

---

## 响应格式

### 成功响应

```json
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 123,
      "username": "wx_abc123_xyz789",
      "email": "wx_abc123_xyz789@wechat.placeholder",
      "nick_name": "",
      "avatar": "",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
      "wechat_bindded": true,
      "tenant_id": 1,
      "tenant_name": "默认租户"
    },
    "is_new_user": true
  }
}
```

### 错误响应

```json
{
  "success": false,
  "code": 4000,
  "message": "登录失败",
  "data": {
    "code": ["登录凭证无效，请重新获取"]
  }
}
```

---

## 代码示例

### 基础登录

```javascript
// utils/auth.js

/**
 * 微信登录并获取 token
 * @returns {Promise<object>} 用户信息和 token
 */
export function wechatLogin() {
  return new Promise((resolve, reject) => {
    // 1. 调用 wx.login 获取 code
    wx.login({
      success: (loginRes) => {
        if (!loginRes.code) {
          reject(new Error('获取登录凭证失败'));
          return;
        }
        
        // 2. 发送 code 到后端
        wx.request({
          url: 'https://your-api-domain.com/api/v1/wechat/login/',
          method: 'POST',
          header: {
            'Content-Type': 'application/json'
          },
          data: {
            code: loginRes.code
          },
          success: (res) => {
            if (res.data.success) {
              // 3. 保存 token
              const { token, refresh_token, user } = res.data.data;
              wx.setStorageSync('token', token);
              wx.setStorageSync('refresh_token', refresh_token);
              wx.setStorageSync('user', user);
              resolve(res.data.data);
            } else {
              reject(new Error(res.data.message || '登录失败'));
            }
          },
          fail: (err) => {
            reject(new Error('网络请求失败'));
          }
        });
      },
      fail: (err) => {
        reject(new Error('wx.login 调用失败'));
      }
    });
  });
}
```

### 封装请求函数

```javascript
// utils/request.js

const BASE_URL = 'https://your-api-domain.com';

/**
 * 带认证的请求封装
 */
export function request(options) {
  const token = wx.getStorageSync('token');
  
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header
      },
      success: (res) => {
        if (res.statusCode === 401) {
          // Token 过期，重新登录
          wx.removeStorageSync('token');
          wx.navigateTo({ url: '/pages/login/login' });
          reject(new Error('登录已过期'));
          return;
        }
        resolve(res.data);
      },
      fail: reject
    });
  });
}
```

### 页面中使用

```javascript
// pages/login/login.js
import { wechatLogin } from '../../utils/auth';

Page({
  data: {
    loading: false
  },
  
  async handleLogin() {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    try {
      const result = await wechatLogin();
      
      wx.showToast({
        title: result.is_new_user ? '注册成功' : '登录成功',
        icon: 'success'
      });
      
      // 跳转到首页
      wx.switchTab({ url: '/pages/home/home' });
      
    } catch (error) {
      wx.showToast({
        title: error.message,
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  }
});
```

---

## 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 40029 | code 无效 | 重新调用 wx.login() 获取新 code |
| 40163 | code 已使用 | code 只能用一次，需重新获取 |
| 45011 | 请求过于频繁 | 等待一段时间后重试 |
| 5000 | 服务器内部错误 | 联系后端开发排查 |

---

## 注意事项

1. **code 有效期**：wx.login() 返回的 code 有效期为 **5 分钟**，且只能使用 **1 次**
2. **Token 存储**：建议使用 `wx.setStorageSync` 持久化存储 token
3. **Token 刷新**：当 access_token 过期时，使用 refresh_token 调用刷新接口
4. **HTTPS**：生产环境必须使用 HTTPS 协议
5. **域名配置**：在微信公众平台配置合法的请求域名

---

## Token 刷新

当 token 过期时（401 响应），使用 refresh_token 刷新：

```javascript
// utils/auth.js

export async function refreshToken() {
  const refresh = wx.getStorageSync('refresh_token');
  if (!refresh) {
    throw new Error('无刷新令牌');
  }
  
  const res = await request({
    url: '/api/v1/auth/refresh/',
    method: 'POST',
    data: { refresh_token: refresh }
  });
  
  if (res.success) {
    wx.setStorageSync('token', res.data.token);
    return res.data.token;
  }
  
  throw new Error('刷新失败');
}
```

---

## 技术支持

如有问题，请联系后端开发团队。
