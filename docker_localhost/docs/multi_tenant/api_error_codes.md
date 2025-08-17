# API 错误码文档

## 概述

本文档列出了 API 接口可能返回的错误码及其描述，帮助前端开发人员更有效地处理错误情况。

## HTTP 状态码

系统使用标准的 HTTP 状态码来表示请求结果：

| 状态码 | 描述 | 处理方法 |
| ----- | ---- | ------- |
| 200 OK | 请求成功 | 正常处理返回的数据 |
| 201 Created | 资源创建成功 | 正常处理返回的数据 |
| 204 No Content | 删除成功 | 无需处理，通常表示删除操作成功 |
| 400 Bad Request | 请求参数错误 | 检查请求参数，根据返回的错误信息修正请求 |
| 401 Unauthorized | 认证失败 | 用户未登录或 Token 已过期，引导用户重新登录 |
| 403 Forbidden | 权限不足 | 用户无权进行当前操作，显示适当的权限提示 |
| 404 Not Found | 资源不存在 | 检查请求的资源 ID 是否正确 |
| 500 Internal Server Error | 服务器内部错误 | 服务端出现错误，可以尝试重试或联系管理员 |

## 错误响应格式

所有API响应（包括错误响应）都遵循统一的标准格式：

```json
{
  "success": false,       // 布尔值，错误时为false
  "code": 4001,           // 业务状态码，表示具体错误类型
  "message": "认证失败，请登录", // 错误描述信息
  "data": null            // 错误时通常为null，某些情况下可能包含错误详情
}
```

### 字段验证错误示例

当请求的字段验证失败时，错误响应可能包含详细字段错误：

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "username": ["该用户名已被使用"],
    "email": ["请输入有效的电子邮件地址"]
  }
}
```

## 业务状态码说明

系统使用三层业务状态码：

| 业务状态码范围 | 描述 |
| ------------- | --- |
| 2000-2999 | 成功响应 |
| 4000-4999 | 客户端错误 |
| 5000-5999 | 服务器错误 |

### 通用业务状态码

| 业务状态码 | 描述 | HTTP状态码 |
| --------- | ---- | --------- |
| 2000      | 操作成功 | 200 OK |
| 4000      | 请求参数错误 | 400 Bad Request |
| 4001      | 认证失败 | 401 Unauthorized |
| 4003      | 权限不足 | 403 Forbidden |
| 4004      | 资源不存在 | 404 Not Found |
| 4005      | 方法不允许 | 405 Method Not Allowed |
| 4006      | 不可接受的请求 | 406 Not Acceptable |
| 4029      | 请求过于频繁 | 429 Too Many Requests |
| 5000      | 服务器内部错误 | 500 Internal Server Error |

### 业务特定状态码

| 业务状态码 | 描述 | HTTP状态码 |
| --------- | ---- | --------- |
| 4100      | 租户不存在 | 404 Not Found |
| 4101      | 租户未激活 | 403 Forbidden |
| 4110      | 租户配额超限 | 429 Too Many Requests |

## 常见错误码和解释

### 认证相关错误 (401)

| 错误信息 | 描述 | 处理方法 |
| ------- | ---- | ------- |
| "认证失败。凭证未提供。" | 未提供 Token | 确保请求头中包含有效的 Authorization 字段 |
| "Token 无效或已过期" | 提供的 Token 无效或已过期 | 使用 refresh_token 获取新的 access_token，或引导用户重新登录 |
| "用户不存在" | 登录时提供的用户名不存在 | 提示用户检查用户名 |
| "无法使用提供的凭据登录" | 登录时密码错误 | 提示用户检查密码 |

### 权限相关错误 (403)

| 错误信息 | 描述 | 处理方法 |
| ------- | ---- | ------- |
| "您没有执行该操作的权限" | 通用权限错误 | 提示用户无权执行当前操作 |
| "无权限查看其他租户的用户列表" | 租户管理员尝试查看其他租户的用户 | 提示用户只能查看自己租户的用户 |
| "无权限更改其他租户的用户角色" | 尝试修改其他租户用户的角色 | 提示用户只能修改自己租户内用户的角色 |
| "不能删除当前登录的用户账号" | 尝试删除自己的账号 | 提示用户不能删除当前登录的账号 |
| "不能撤销自己的超级管理员权限" | 超级管理员尝试撤销自己的权限 | 提示超级管理员不能撤销自己的权限 |
| "不能修改超级管理员的角色" | 尝试修改超级管理员的角色 | 提示用户超级管理员的角色不能被修改 |

### 请求参数错误 (400)

| 错误信息 | 描述 | 处理方法 |
| ------- | ---- | ------- |
| "该租户下此邮箱已被注册" | 创建用户时，邮箱在租户内已存在 | 提示用户使用其他邮箱地址 |
| "该租户下此用户名已被使用" | 创建用户时，用户名在租户内已存在 | 提示用户使用其他用户名 |
| "该租户下此电话号码已被使用" | 创建用户时，电话号码在租户内已存在 | 提示用户使用其他电话号码 |
| "两次输入的密码不一致" | 密码和确认密码不匹配 | 提示用户重新输入并确保两次密码一致 |
| "旧密码不正确" | 修改密码时，提供的旧密码错误 | 提示用户输入正确的当前密码 |
| "密码过于简单" | 密码不符合安全要求 | 提示用户设置更复杂的密码，包含字母、数字和特殊字符 |
| "该用户已经是超级管理员" | 尝试将已是超级管理员的用户设为超级管理员 | 提示用户该账号已具有超级管理员权限 |
| "该用户不是超级管理员" | 尝试撤销非超级管理员用户的超级管理员权限 | 提示用户该账号不是超级管理员 |

### 资源不存在错误 (404)

| 错误信息 | 描述 | 处理方法 |
| ------- | ---- | ------- |
| "未找到" | 请求的资源不存在 | 检查资源 ID 是否正确，或者资源可能已被删除 |
| "未找到与所提供的查询参数匹配的用户" | 查询的用户不存在 | 检查用户 ID 是否正确 |
| "未找到与所提供的查询参数匹配的租户" | 查询的租户不存在 | 检查租户 ID 是否正确 |

### 租户相关错误

| 错误信息 | 描述 | 处理方法 |
| ------- | ---- | ------- |
| "租户已达到最大用户数限制" | 创建用户时，租户已达到用户配额上限 | 提示需要升级租户配额或删除一些用户 |
| "租户已达到最大管理员数限制" | 创建管理员时，租户已达到管理员配额上限 | 提示需要升级租户配额或删除一些管理员 |
| "租户已被暂停，无法执行此操作" | 尝试在被暂停的租户上执行操作 | 提示用户租户已被暂停，需联系超级管理员 |

## 处理错误的最佳实践

1. **全局错误处理**：在前端应用中设置全局错误处理器，统一处理常见错误。

2. **优雅降级**：在遇到错误时，提供用户友好的提示，避免显示技术性错误信息。

3. **自动重试**：对于网络错误，可以实现自动重试机制。

4. **Token 刷新**：当收到 401 错误且原因是 Token 过期时，尝试使用 refresh_token 自动获取新的 access_token。

5. **日志记录**：在前端记录错误信息，方便后续分析和调试。

## 错误处理示例代码

```javascript
// 全局 Axios 错误处理示例
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      const { status, data } = error.response;
      
      // 处理 401 错误
      if (status === 401) {
        // Token 过期，尝试刷新
        if (data.detail === "Token 无效或已过期" && refreshToken) {
          return refreshTokenAndRetry(error);
        }
        // 其他认证错误，重定向到登录页
        store.dispatch('auth/logout');
        router.push('/login');
      }
      
      // 处理 403 错误
      if (status === 403) {
        notification.error({
          message: '权限不足',
          description: data.detail || '您没有权限执行此操作'
        });
      }
      
      // 处理 400 错误
      if (status === 400) {
        const errorMessages = [];
        // 处理字段错误
        if (typeof data === 'object' && !data.detail) {
          Object.keys(data).forEach(key => {
            errorMessages.push(`${key}: ${data[key].join(', ')}`);
          });
        } else if (data.detail) {
          errorMessages.push(data.detail);
        }
        
        notification.error({
          message: '请求参数错误',
          description: errorMessages.join('\n')
        });
      }
      
      // 处理 404 错误
      if (status === 404) {
        notification.error({
          message: '资源不存在',
          description: data.detail || '请求的资源不存在'
        });
      }
      
      // 处理 500 错误
      if (status === 500) {
        notification.error({
          message: '服务器错误',
          description: '服务器内部错误，请稍后重试或联系管理员'
        });
      }
    } else if (error.request) {
      // 请求已发出但未收到响应
      notification.error({
        message: '网络错误',
        description: '无法连接到服务器，请检查您的网络连接'
      });
    } else {
      // 请求设置时出错
      notification.error({
        message: '请求错误',
        description: error.message
      });
    }
    
    return Promise.reject(error);
  }
);

// 刷新 Token 并重试请求
async function refreshTokenAndRetry(error) {
  try {
    // 刷新 Token
    const response = await axios.post('/auth/token/refresh/', {
      refresh_token: refreshToken
    });
    
    // 更新 Token
    const { access, refresh } = response.data;
    store.dispatch('auth/updateTokens', { access, refresh });
    
    // 使用新 Token 重试之前的请求
    const config = error.config;
    config.headers['Authorization'] = `Bearer ${access}`;
    return axios(config);
  } catch (refreshError) {
    // 刷新 Token 失败，重定向到登录页
    store.dispatch('auth/logout');
    router.push('/login');
    return Promise.reject(refreshError);
  }
}
``` 