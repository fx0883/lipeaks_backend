# 前端集成指南 - 统一异常处理系统

## 概述

本目录包含前端团队集成 Lipeaks Backend 统一异常处理系统的完整文档。**这些文档与前端框架和编程语言无关**，提供通用的集成方案。

无论您使用 React、Vue、Angular、jQuery 或其他任何前端技术栈，都可以根据这些文档实现统一的错误处理。

## 为什么需要统一的前端错误处理？

后端已经实现了统一的异常处理系统，所有API错误响应都遵循相同的格式。前端需要：

✅ **一致的错误处理** - 统一处理所有API错误  
✅ **用户友好** - 将技术错误转换为用户可理解的消息  
✅ **调试友好** - 开发环境显示详细错误信息  
✅ **可维护性** - 集中管理错误处理逻辑  
✅ **框架无关** - 适用于任何前端技术栈  

## 文档结构

### 1. [错误响应格式详解](./01_error_response_format.md)
- 标准错误响应结构
- 字段说明和示例
- 不同类型错误的响应格式
- 与旧版本的对比

### 2. [前端错误处理架构](./02_frontend_error_architecture.md)
- 前端错误处理流程图
- 错误拦截设计原则
- 错误分类和处理策略
- 架构最佳实践（框架无关）

### 3. [错误处理策略](./03_error_handling_strategies.md)
- 错误分级处理策略
- 不同错误类型的处理方案
- 用户提示设计原则
- 错误恢复机制

### 4. [HTTP客户端集成指南](./04_http_client_integration.md)
- 请求拦截器设计
- 响应拦截器设计
- Token管理方案
- 重试机制设计

### 5. [常见场景处理方案](./05_common_scenarios.md)
- 用户登录场景
- 表单提交场景
- 列表加载场景
- 文件上传场景
- 批量操作场景

### 6. [用户界面设计指南](./06_ui_design_guide.md)
- 错误提示UI设计
- Loading状态设计
- 错误页面设计
- 用户引导设计

## 快速开始

### 标准错误响应格式

所有API错误都遵循以下JSON格式：

```json
{
  "success": false,
  "code": 4101,
  "message": "租户不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

### 核心处理流程（伪代码）

```
1. 发起HTTP请求
   ↓
2. 检查HTTP响应状态
   ↓
3. 解析JSON响应体
   ↓
4. 判断 success 字段
   ├─ true → 处理成功数据
   └─ false → 进入错误处理流程
       ↓
5. 根据 code 字段分类：
   ├─ 4001-4004 → 认证错误：清除Token，跳转登录
   ├─ 4003,4303 → 权限错误：显示权限提示
   ├─ 4000 → 验证错误：显示字段错误
   ├─ 41XX-46XX → 业务错误：显示错误消息
   └─ 5XXX → 服务器错误：显示通用提示，可重试
```

### 错误处理示例（伪代码）

```
function handleApiError(response) {
  // 检查是否成功
  if (response.success === false) {
    
    // 根据错误码分类处理
    if (response.code === 4001 || response.code === 4004) {
      // 清除本地存储的认证信息
      clearAuthToken()
      
      // 跳转到登录页
      redirectTo('/login')
      
      // 显示提示
      showMessage('登录已过期，请重新登录', 'warning')
    }
    
    else if (response.code === 4003 || response.code === 4303) {
      // 显示权限错误
      showDialog('权限不足', response.message, 'warning')
    }
    
    else if (response.error_code === 'VALIDATION_ERROR') {
      // 显示字段错误
      displayFieldErrors(response.data)
    }
    
    else if (response.code >= 5000) {
      // 服务器错误，可以重试
      showMessage('服务器错误，请稍后重试', 'error')
    }
    
    else {
      // 其他业务错误
      showMessage(response.message, 'error')
    }
  }
}
```

## 核心概念

### 错误响应结构

所有API错误都遵循以下结构：

```json
{
  "success": false,           // 固定为 false
  "code": 4101,              // 业务错误码（4位数字）
  "message": "租户不存在",    // 人类可读的错误消息
  "data": null,              // 错误详情（通常为null，验证错误时包含字段信息）
  "error_code": "TENANT_NOT_FOUND"  // 错误标识符（字符串常量）
}
```

### 错误码分类

| 范围 | 模块 | 说明 |
|------|------|------|
| 4001-4099 | 认证授权 | 未登录、权限不足等 |
| 4100-4199 | 租户管理 | 租户不存在、未激活等 |
| 4200-4299 | 许可证管理 | 许可证过期、配额超限等 |
| 4300-4399 | 用户管理 | 用户不存在、未激活等 |
| 4400-4499 | 积分系统 | 积分不足、已过期等 |
| 4500-4599 | CMS系统 | 文章不存在等 |
| 5000-5099 | 服务器错误 | 系统内部错误 |

### 处理策略（概念）

```
根据错误码范围分类处理：

1. 认证错误 (4001-4004)
   → 清除本地认证信息
   → 跳转到登录页面
   → 显示提示消息

2. 权限错误 (4003, 4303)
   → 显示权限不足提示
   → 提供返回或申请权限的入口

3. 验证错误 (4000)
   → 解析 data 字段中的字段错误
   → 在对应表单字段下显示错误
   → 高亮第一个错误字段

4. 业务错误 (4100-4699)
   → 显示后端返回的 message
   → 根据 error_code 提供操作建议

5. 服务器错误 (5000+)
   → 显示通用错误提示
   → 提供重试选项
   → 记录错误日志
```

## 与旧版本的兼容性

如果您的前端代码仍在使用旧的错误响应格式，不用担心：

**旧格式（部分API可能仍在使用）：**
```json
{
  "detail": "租户不存在"
}
```

**新格式（推荐）：**
```json
{
  "success": false,
  "code": 4101,
  "message": "租户不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

建议更新前端代码以使用新格式，可以享受更好的错误处理体验。

## 技术栈支持

**本文档与前端技术栈无关**，适用于：

- ✅ **任何JavaScript框架** (React, Vue, Angular, Svelte等)
- ✅ **任何HTTP客户端** (Axios, Fetch, jQuery Ajax, XMLHttpRequest等)
- ✅ **任何编程语言** (JavaScript, TypeScript, Dart, Kotlin等)
- ✅ **移动端** (React Native, Flutter, iOS, Android原生)
- ✅ **小程序** (微信、支付宝、抖音等小程序)

## 实施要点

无论使用什么技术栈，都需要实现以下功能：

### 1. HTTP响应拦截

```
在HTTP客户端的响应拦截器/回调中：
  1. 获取响应的JSON数据
  2. 检查 success 字段
  3. 如果 success === false，调用错误处理函数
  4. 传递 code, message, error_code 给错误处理器
```

### 2. 错误分类处理

```
创建错误处理函数：
  输入: response对象 (包含 success, code, message, error_code)
  
  处理逻辑:
    IF code in [4001, 4002, 4004]:
      处理认证错误
      
    ELSE IF code in [4003, 4303]:
      处理权限错误
      
    ELSE IF error_code === 'VALIDATION_ERROR':
      处理验证错误
      
    ELSE IF code >= 5000:
      处理服务器错误
      
    ELSE:
      处理业务错误
```

### 3. 用户提示

```
根据错误严重程度选择提示方式：
  - 轻微错误 → 轻量提示（Toast/Snackbar）
  - 重要错误 → 对话框提示（Modal/Dialog）
  - 阻断性错误 → 错误页面（全屏错误页）
```

## 实施步骤

1. **阅读错误响应格式** - 了解后端返回的标准格式
2. **设计错误分类器** - 根据错误码分类处理
3. **实现HTTP拦截** - 在HTTP客户端中拦截错误响应
4. **实现错误处理器** - 创建统一的错误处理函数
5. **设计UI组件** - 创建错误提示组件
6. **测试验证** - 测试各种错误场景

## 集成检查清单

前端集成时需要确认：

- [ ] HTTP客户端能够拦截所有错误响应
- [ ] 正确解析JSON响应中的 success, code, message, error_code 字段
- [ ] 认证错误（4001, 4004）会清除Token并跳转登录
- [ ] 权限错误（4003, 4303）有明确提示
- [ ] 验证错误（4000）能显示字段级错误
- [ ] 业务错误显示后端返回的message
- [ ] 服务器错误（5000+）提供重试选项
- [ ] 所有错误都有用户友好的提示
- [ ] 开发环境记录详细的错误日志

## 相关资源

- [后端异常处理文档](../README.md)
- [错误码完整列表](../03_error_code_specification.md)
- [迁移指南](../05_migration_guide.md)

## 贡献

如果您在集成过程中发现任何问题或有改进建议，请联系后端团队或提交Issue。

---

**维护者**: Lipeaks Frontend & Backend Team  
**最后更新**: 2025-01-08  
**版本**: 1.0.0

