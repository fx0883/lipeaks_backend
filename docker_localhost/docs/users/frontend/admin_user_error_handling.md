# 管理员用户模块错误处理指南

本文档提供管理员用户模块在前端开发中的错误处理最佳实践，帮助开发人员实现健壮、用户友好的错误处理机制。

## 目录

1. [API响应错误码](#API响应错误码)
2. [常见错误场景及处理](#常见错误场景及处理)
3. [表单验证错误处理](#表单验证错误处理)
4. [全局错误处理](#全局错误处理)
5. [用户反馈机制](#用户反馈机制)
6. [错误日志与监控](#错误日志与监控)

## API响应错误码

管理员用户模块API可能返回的错误码及其含义：

| 错误码 | 错误消息 | 说明 |
|-------|---------|-----|
| 4001 | 认证失败 | 用户未登录或token无效 |
| 4002 | 权限不足 | 当前用户没有执行操作的权限 |
| 4003 | 参数错误 | 请求参数不符合要求 |
| 4004 | 资源不存在 | 请求的管理员用户不存在 |
| 4005 | 用户名已存在 | 创建或修改时使用了已存在的用户名 |
| 4006 | 邮箱已存在 | 创建或修改时使用了已存在的邮箱 |
| 4007 | 密码不符合要求 | 密码不符合安全要求 |
| 4008 | 旧密码不正确 | 修改密码时输入的旧密码不正确 |
| 4009 | 超级管理员不可删除 | 尝试删除系统唯一的超级管理员 |
| 5001 | 服务器内部错误 | 服务器处理请求时发生内部错误 |

## 常见错误场景及处理

### 1. 认证与授权错误

#### 1.1 认证失败（4001）

**场景**：用户未登录、登录已过期或token无效

**处理方式**：
- 重定向到登录页面
- 清除本地存储的认证信息
- 显示友好提示："您的登录已过期，请重新登录"

```
# 伪代码示例（非实际代码）

function handleAuthError() {
  // 清除认证信息
  clearAuthToken();
  
  // 显示提示
  showToast('您的登录已过期，请重新登录');
  
  // 重定向到登录页面
  redirectToLogin();
}
```

#### 1.2 权限不足（4002）

**场景**：当前用户尝试执行没有权限的操作

**处理方式**：
- 显示权限不足提示
- 隐藏或禁用相关功能按钮
- 记录错误日志以便排查问题

```
# 伪代码示例（非实际代码）

function handlePermissionError() {
  // 显示提示
  showToast('您没有执行此操作的权限');
  
  // 记录日志
  logError('Permission denied for user operation');
  
  // 可选：重定向到安全页面
  redirectToDashboard();
}
```

### 2. 数据操作错误

#### 2.1 资源不存在（4004）

**场景**：请求的管理员用户不存在

**处理方式**：
- 显示"用户不存在"提示
- 提供返回列表页的选项
- 刷新管理员列表

```
# 伪代码示例（非实际代码）

function handleResourceNotFoundError() {
  // 显示提示
  showError('您请求的管理员用户不存在或已被删除');
  
  // 提供操作选项
  showActionButton('返回列表', () => navigateToList());
  
  // 刷新列表数据
  refreshAdminUserList();
}
```

#### 2.2 数据冲突（4005/4006）

**场景**：创建或更新管理员时，用户名或邮箱已存在

**处理方式**：
- 在相应字段下方显示具体错误提示
- 保留用户已输入的其他数据
- 将焦点设置到错误字段

```
# 伪代码示例（非实际代码）

function handleDuplicateFieldError(error) {
  const errorData = error.response.data;
  
  if (errorData.code === 4005) {
    // 用户名已存在
    setFieldError('username', '此用户名已被使用，请选择其他用户名');
    focusField('username');
  } else if (errorData.code === 4006) {
    // 邮箱已存在
    setFieldError('email', '此邮箱已被使用，请使用其他邮箱');
    focusField('email');
  }
}
```

## 表单验证错误处理

### 1. 客户端验证

**最佳实践**：
- 实施实时客户端验证，在提交前就发现错误
- 为每个字段提供明确的验证规则和错误消息
- 在错误状态下禁用提交按钮

**字段验证规则示例**：

| 字段 | 验证规则 | 错误消息 |
|------|---------|---------|
| 用户名 | 必填，3-20个字符，字母、数字、下划线 | "用户名为必填项"/"用户名必须是3-20个字符"/"用户名只能包含字母、数字和下划线" |
| 邮箱 | 必填，有效的邮箱格式 | "邮箱为必填项"/"请输入有效的邮箱地址" |
| 密码 | 必填，8-20个字符，包含字母和数字 | "密码为必填项"/"密码必须是8-20个字符"/"密码必须同时包含字母和数字" |
| 确认密码 | 必填，与密码一致 | "请确认密码"/"两次输入的密码不一致" |

### 2. 服务器端验证错误处理

**最佳实践**：
- 解析API返回的错误字段及消息
- 将错误映射到表单中对应的字段
- 显示详细的错误提示

```
# 伪代码示例（非实际代码）

function handleFormErrors(error) {
  if (!error.response || !error.response.data) {
    // 处理网络错误或意外错误
    showFormError('提交表单时发生错误，请稍后重试');
    return;
  }
  
  const errorData = error.response.data;
  
  if (errorData.code === 4003 && errorData.data) {
    // 参数错误，通常包含字段级错误
    const fieldErrors = errorData.data;
    
    // 遍历并设置字段错误
    Object.keys(fieldErrors).forEach(field => {
      setFieldError(field, fieldErrors[field]);
    });
    
    // 将焦点设置到第一个错误字段
    focusFirstErrorField();
    
    // 显示一般提示
    showFormError('表单填写有误，请检查错误提示');
  } else {
    // 其他错误
    showFormError(errorData.message || '提交表单时发生错误，请稍后重试');
  }
}
```

## 全局错误处理

### 1. 统一错误处理拦截器

**最佳实践**：
- 配置API请求拦截器统一处理错误
- 根据错误类型执行相应的处理逻辑
- 记录错误日志

```
# 伪代码示例（非实际代码）

// 配置Axios拦截器
axios.interceptors.response.use(
  response => response,
  error => {
    // 处理网络错误
    if (!error.response) {
      showToast('网络连接失败，请检查网络连接');
      return Promise.reject(error);
    }
    
    const { status, data } = error.response;
    
    // 处理认证错误
    if (status === 401) {
      handleAuthError();
      return Promise.reject(error);
    }
    
    // 处理权限错误
    if (status === 403) {
      handlePermissionError();
      return Promise.reject(error);
    }
    
    // 处理资源不存在
    if (status === 404) {
      handleResourceNotFoundError();
      return Promise.reject(error);
    }
    
    // 处理服务器错误
    if (status >= 500) {
      showToast('服务器暂时无法响应，请稍后重试');
      logServerError(error);
      return Promise.reject(error);
    }
    
    // 其他错误
    return Promise.reject(error);
  }
);
```

### 2. 错误状态页面

**最佳实践**：
- 为常见错误状态提供专门的错误页面
- 在错误页面提供帮助信息和后续操作选项
- 自动记录错误信息以便分析和改进

**典型错误页面**：

1. **401 未授权页面**
   - 提示用户登录已过期
   - 提供"返回登录"按钮
   - 简要说明原因

2. **403 权限不足页面**
   - 说明用户无权访问该资源
   - 提供"返回首页"按钮
   - 可选提供"联系管理员"选项

3. **404 资源不存在页面**
   - 说明请求的资源不存在
   - 提供"返回列表"按钮
   - 可选提供搜索功能

## 用户反馈机制

### 1. 错误提示设计

**最佳实践**：
- 使用一致的错误提示样式
- 根据错误严重性使用不同的视觉提示（颜色、图标）
- 提供清晰的错误描述和可能的解决方案

**提示类型**：

1. **轻量级提示**
   - 用于非阻断性错误
   - 通常以toast或snackbar形式显示
   - 自动消失，不中断用户操作

2. **表单内提示**
   - 用于表单验证错误
   - 显示在相关字段附近
   - 提供具体的修正建议

3. **模态对话框**
   - 用于严重或需要用户确认的错误
   - 要求用户确认后才能继续
   - 提供明确的后续步骤

### 2. 友好的错误消息

**最佳实践**：
- 使用简单、非技术性的语言
- 解释发生了什么以及为什么会发生
- 告诉用户应该采取什么措施

**错误消息模板**：

```
[问题描述] + [原因] + [解决方案]
```

**示例**：
- ❌ "错误4005：用户名重复"
- ✅ "此用户名已被使用。请选择一个不同的用户名继续。"

## 错误日志与监控

### 1. 客户端错误日志

**最佳实践**：
- 记录用户遇到的错误
- 包含错误类型、发生时间、用户操作等信息
- 定期分析错误模式以改进系统

```
# 伪代码示例（非实际代码）

function logError(error, context = {}) {
  const errorLog = {
    timestamp: new Date().toISOString(),
    user: getCurrentUser()?.id,
    error: {
      message: error.message,
      stack: error.stack,
      code: error.response?.data?.code
    },
    context: {
      url: window.location.href,
      operation: context.operation,
      ...context
    }
  };
  
  // 发送到日志服务器
  sendErrorLog(errorLog);
  
  // 可选：存储到本地以便稍后上传
  storeErrorLog(errorLog);
}
```

### 2. 错误监控与分析

**最佳实践**：
- 实施前端错误监控系统
- 设置关键错误的警报机制
- 定期分析错误趋势并进行改进

**监控重点**：
1. 高频错误：频繁出现的同类错误
2. 关键流程错误：影响核心功能的错误
3. 用户体验指标：错误对用户行为的影响

通过本指南中的最佳实践，前端开发人员可以构建健壮的错误处理机制，提高管理员用户模块的可用性和用户体验。 