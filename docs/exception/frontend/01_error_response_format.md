# 错误响应格式详解

## 概述

本文档详细说明后端API返回的标准错误响应格式，帮助前端开发者正确解析和处理错误。

## 标准错误响应结构

### 基本格式

所有API错误都遵循以下JSON格式：

```json
{
  "success": false,
  "code": 4101,
  "message": "租户ID 123 不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

### 字段详解

| 字段 | 类型 | 必需 | 说明 | 示例值 |
|------|------|------|------|--------|
| `success` | boolean | ✅ | 请求是否成功，错误时固定为 `false` | `false` |
| `code` | number | ✅ | 业务错误码（4位数字） | `4101` |
| `message` | string | ✅ | 人类可读的错误消息（中文） | `"租户不存在"` |
| `data` | any | ✅ | 错误详情数据，通常为 `null` | `null` 或 `{字段错误}` |
| `error_code` | string | ✅ | 错误标识符（大写字母+下划线） | `"TENANT_NOT_FOUND"` |

### 数据类型说明

| 字段 | 数据类型 | 可能的值 |
|------|---------|---------|
| `success` | Boolean | 固定为 `false` |
| `code` | Number/Integer | 4位整数：4000-4999（客户端错误）、5000-5999（服务器错误） |
| `message` | String | 中文错误消息，如"租户不存在" |
| `data` | Any | 通常为 `null`，验证错误时为对象（字段名→错误消息数组） |
| `error_code` | String | 大写字母+下划线，如"TENANT_NOT_FOUND" |

## 不同类型错误的响应格式

### 1. 业务错误（最常见）

当业务规则验证失败时返回：

```json
{
  "success": false,
  "code": 4201,
  "message": "许可证已于 2024-01-15 过期",
  "data": null,
  "error_code": "LICENSE_EXPIRED"
}
```

**前端处理逻辑（伪代码）：**
```
IF response.success === false:
  IF response.error_code === 'LICENSE_EXPIRED':
    跳转到续费页面
  ELSE:
    显示错误消息: response.message
```

### 2. 数据验证错误

当请求数据格式或内容不正确时返回：

```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "name": ["该字段不能为空"],
    "email": ["请输入有效的邮箱地址"],
    "age": ["必须是正整数"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

**注意：** `data` 字段包含字段级错误信息，键是字段名，值是错误消息数组。

**前端处理逻辑（伪代码）：**
```
IF response.error_code === 'VALIDATION_ERROR' AND response.data 存在:
  FOR EACH 字段 in response.data:
    获取该字段的错误消息数组
    在表单中该字段下显示第一条错误消息
    高亮该字段
```

### 3. 认证错误

当用户未登录或Token无效时返回：

```json
{
  "success": false,
  "code": 4001,
  "message": "认证失败，请登录",
  "data": null,
  "error_code": "AUTH_NOT_AUTHENTICATED"
}
```

**前端处理逻辑（伪代码）：**
```
IF response.code in [4001, 4004]:
  清除本地存储的Token
  清除用户信息
  跳转到登录页面
  显示提示: "登录已过期，请重新登录"
```

### 4. 权限错误

当用户没有执行某操作的权限时返回：

```json
{
  "success": false,
  "code": 4003,
  "message": "您没有执行该操作的权限",
  "data": null,
  "error_code": "AUTH_PERMISSION_DENIED"
}
```

**前端处理逻辑（伪代码）：**
```
IF response.code in [4003, 4303]:
  显示对话框:
    标题: "权限不足"
    内容: response.message
    按钮: "我知道了"
```

### 5. 配额超限错误

当资源配额达到上限时返回：

```json
{
  "success": false,
  "code": 4203,
  "message": "您的试用许可证数量已达上限（1个）",
  "data": null,
  "error_code": "LICENSE_QUOTA_EXCEEDED"
}
```

**前端处理逻辑（伪代码）：**
```
IF response.error_code === 'LICENSE_QUOTA_EXCEEDED':
  显示信息对话框:
    标题: "配额已满"
    内容: response.message
    确认按钮: "升级套餐"
    点击确认后: 跳转到 /upgrade 页面
```

### 6. 服务器错误

当服务器内部错误时返回：

```json
{
  "success": false,
  "code": 5000,
  "message": "服务器内部错误",
  "data": null,
  "error_code": "INTERNAL_SERVER_ERROR"
}
```

**前端处理逻辑（伪代码）：**
```
IF response.code >= 5000:
  显示错误提示: "服务器暂时不可用，请稍后重试"
  
  记录错误日志:
    错误类型: "server_error"
    错误码: response.code
    错误消息: response.message
    请求URL: request.url
  
  可选: 上报到错误监控系统
```

## 常见错误码速查表

### 认证授权（40XX）

| 错误码 | 错误标识符 | HTTP状态 | 说明 | 前端处理 |
|-------|-----------|---------|------|---------|
| 4001 | `AUTH_NOT_AUTHENTICATED` | 401 | 未认证 | 跳转登录页 |
| 4002 | `AUTH_TOKEN_INVALID` | 401 | Token无效 | 清除Token，跳转登录 |
| 4003 | `AUTH_PERMISSION_DENIED` | 403 | 权限不足 | 显示权限提示 |
| 4004 | `AUTH_TOKEN_EXPIRED` | 401 | Token过期 | 刷新Token或重新登录 |

### 租户管理（41XX）

| 错误码 | 错误标识符 | HTTP状态 | 说明 | 前端处理 |
|-------|-----------|---------|------|---------|
| 4101 | `TENANT_NOT_FOUND` | 404 | 租户不存在 | 显示错误提示 |
| 4102 | `TENANT_INACTIVE` | 403 | 租户未激活 | 显示账户状态提示 |
| 4103 | `TENANT_QUOTA_EXCEEDED` | 429 | 租户配额超限 | 提示升级套餐 |
| 4104 | `TENANT_ACCESS_DENIED` | 403 | 租户访问拒绝 | 显示权限错误 |

### 许可证管理（42XX）

| 错误码 | 错误标识符 | HTTP状态 | 说明 | 前端处理 |
|-------|-----------|---------|------|---------|
| 4201 | `LICENSE_EXPIRED` | 400 | 许可证过期 | 跳转续费页面 |
| 4202 | `LICENSE_NOT_FOUND` | 404 | 许可证不存在 | 显示错误提示 |
| 4203 | `LICENSE_QUOTA_EXCEEDED` | 429 | 配额超限 | 提示升级或联系管理员 |
| 4206 | `LICENSE_ALREADY_ASSIGNED` | 400 | 已拥有许可证 | 显示已拥有提示 |

### 用户管理（43XX）

| 错误码 | 错误标识符 | HTTP状态 | 说明 | 前端处理 |
|-------|-----------|---------|------|---------|
| 4301 | `USER_NOT_FOUND` | 404 | 用户不存在 | 显示错误提示 |
| 4302 | `USER_INACTIVE` | 403 | 用户未激活 | 显示账户状态提示 |
| 4303 | `USER_PERMISSION_DENIED` | 403 | 用户权限拒绝 | 显示权限错误 |

### 积分系统（44XX）

| 错误码 | 错误标识符 | HTTP状态 | 说明 | 前端处理 |
|-------|-----------|---------|------|---------|
| 4401 | `POINTS_INSUFFICIENT` | 400 | 积分不足 | 显示当前积分，提示获取积分 |
| 4402 | `POINTS_EXPIRED` | 400 | 积分过期 | 显示过期提示 |
| 4404 | `POINTS_DAILY_LIMIT_EXCEEDED` | 429 | 每日上限 | 显示今日已达上限 |

## 响应示例集合

### 示例1：租户不存在

**HTTP状态码：** 404  
**业务错误码：** 4101

```json
{
  "success": false,
  "code": 4101,
  "message": "租户ID 123 不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

### 示例2：许可证配额超限

**HTTP状态码：** 429  
**业务错误码：** 4203

```json
{
  "success": false,
  "code": 4203,
  "message": "您的试用许可证数量已达上限（1个）",
  "data": null,
  "error_code": "LICENSE_QUOTA_EXCEEDED"
}
```

### 示例3：表单验证失败

**HTTP状态码：** 400  
**业务错误码：** 4000

```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "name": ["该字段不能为空"],
    "email": ["请输入有效的邮箱地址", "该邮箱已被注册"],
    "password": ["密码长度至少8位"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

### 示例4：用户权限不足

**HTTP状态码：** 403  
**业务错误码：** 4303

```json
{
  "success": false,
  "code": 4303,
  "message": "无权限更改其他租户的用户角色",
  "data": null,
  "error_code": "USER_PERMISSION_DENIED"
}
```

### 示例5：积分余额不足

**HTTP状态码：** 400  
**业务错误码：** 4401

```json
{
  "success": false,
  "code": 4401,
  "message": "积分余额不足，当前可用: 100，需要: 500",
  "data": null,
  "error_code": "POINTS_INSUFFICIENT"
}
```

## 与成功响应的对比

### 成功响应格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 123,
    "name": "测试租户",
    "status": "active"
  }
}
```

### 错误响应格式

```json
{
  "success": false,
  "code": 4101,
  "message": "租户不存在",
  "data": null,
  "error_code": "TENANT_NOT_FOUND"
}
```

### 判断成功与失败

**方法1：通过 success 字段判断（推荐）**
```
IF response.success === true:
  处理成功数据: response.data
ELSE:
  调用错误处理函数: handleError(response)
```

**方法2：通过 code 字段判断**
```
IF response.code === 2000:
  处理成功
ELSE IF response.code >= 4000:
  处理错误
```

**方法3：通过 error_code 字段存在性判断**
```
IF response.error_code 存在:
  说明是错误响应
  调用错误处理函数
```

## 分页响应的错误格式

### 列表API的错误响应

列表API错误时也遵循相同格式：

```json
{
  "success": false,
  "code": 4003,
  "message": "您没有权限查看此租户的用户列表",
  "data": null,
  "error_code": "USER_PERMISSION_DENIED"
}
```

### 列表API的成功响应

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 10,
    "next": "http://api.example.com/users/?page=2",
    "previous": null,
    "results": [
      { "id": 1, "name": "用户1" },
      { "id": 2, "name": "用户2" }
    ]
  }
}
```

## HTTP状态码与业务错误码的关系

### 映射关系

| HTTP状态码 | 业务错误码 | 说明 | 示例 |
|-----------|-----------|------|------|
| 400 | 4000 | 请求参数错误 | 验证失败 |
| 401 | 4001 | 未认证 | Token无效 |
| 403 | 4003 | 权限不足 | 无操作权限 |
| 404 | 4004, 41XX, 42XX等 | 资源不存在 | 租户不存在 |
| 429 | 4029, 4103, 4203等 | 请求频率限制或配额超限 | 配额已满 |
| 500 | 5000 | 服务器内部错误 | 系统异常 |

### 为什么需要两个错误码？

**HTTP状态码（status）：**
- 标准HTTP协议定义
- 浏览器和网络层使用
- 粗粒度分类（400、401、403等）

**业务错误码（code）：**
- 业务系统自定义
- 应用层使用
- 细粒度区分（4101、4102、4103等）

**错误标识符（error_code）：**
- 字符串常量，语义化
- 代码中使用，易读易维护
- 支持IDE自动补全

### 处理优先级

**推荐的错误判断优先级：error_code > code > HTTP status**

```
优先级1：使用 error_code 字段（最推荐）
  IF error_code === 'TENANT_NOT_FOUND':
    处理租户不存在
  ELSE IF error_code === 'LICENSE_EXPIRED':
    处理许可证过期
  ...

优先级2：使用 code 字段
  IF code === 4101:
    处理租户不存在
  ...

优先级3：使用 HTTP status（最后选择）
  IF httpStatus === 404:
    通用的404处理
  ...
```

**原因：**
- `error_code` 最语义化，易于理解和维护
- `code` 细粒度区分不同错误
- `HTTP status` 只能粗粒度分类

## 特殊情况处理

### 网络错误（无响应）

当网络断开或服务器无法访问时，不会收到JSON响应：

```
处理逻辑:
  IF 请求没有收到响应:
    显示提示: "网络连接失败，请检查您的网络"
    记录日志: 网络错误
  ELSE IF 收到响应:
    按照标准流程处理响应中的错误
```

### 超时错误

```
处理逻辑:
  IF 请求超时:
    显示提示: "请求超时，请稍后重试"
    可选: 提供重试按钮
```

### 请求取消

```
处理逻辑:
  IF 请求被用户取消:
    不显示错误提示
    记录日志: 请求已取消
```

## 开发环境vs生产环境

### 开发环境

开发环境可能返回更详细的错误信息（仅当DEBUG=True时）：

```json
{
  "success": false,
  "code": 5000,
  "message": "服务器内部错误",
  "data": {
    "exception_type": "DatabaseError",
    "traceback": "..."  // 仅开发环境
  },
  "error_code": "INTERNAL_SERVER_ERROR"
}
```

### 生产环境

生产环境不会暴露技术细节：

```json
{
  "success": false,
  "code": 5000,
  "message": "服务器内部错误",
  "data": null,
  "error_code": "INTERNAL_SERVER_ERROR"
}
```

### 前端处理建议

```
环境判断逻辑:
  IF 是开发环境:
    IF response.code >= 5000 AND response.data 包含技术信息:
      在控制台输出详细错误信息（包括堆栈）
    显示用户友好提示: "服务器错误，我们正在处理中"
  
  ELSE IF 是生产环境:
    只显示用户友好提示: "服务器错误，我们正在处理中"
    不显示任何技术细节
```

## 总结

### 关键要点

1. **统一格式** - 所有错误响应都包含 `success`, `code`, `message`, `data`, `error_code`
2. **类型安全** - 使用TypeScript类型定义
3. **优先使用error_code** - 比数字错误码更语义化
4. **验证错误特殊处理** - `data` 字段包含字段级错误信息
5. **HTTP状态码仅供参考** - 主要依赖业务错误码

### 前端checklist

- [ ] 定义完整的TypeScript类型
- [ ] 配置Axios拦截器
- [ ] 实现统一的错误处理函数
- [ ] 处理不同类型的错误（验证、权限、业务等）
- [ ] 区分开发环境和生产环境
- [ ] 提供用户友好的错误提示

---

**下一步**: 阅读 [前端错误处理架构](./02_frontend_error_architecture.md)

**维护者**: Lipeaks Backend Team  
**最后更新**: 2025-01-08

