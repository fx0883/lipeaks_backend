# Member 认证 API 文档

本文档详细说明 Member 用户相关的认证 API 接口。

## 文档目录

1. [登录认证](./01_login.md) - 用户登录相关 API
2. [Token 管理](./02_token.md) - Token 验证和刷新 API
3. [密码管理](./03_password.md) - 修改密码和重置密码 API
4. [用户注册](./04_register.md) - Member 用户注册 API

## 通用说明

### 请求头

所有 API 请求都需要包含以下请求头：

| 请求头 | 必需 | 说明 |
|--------|------|------|
| `Content-Type` | 是 | `application/json` |
| `X-Tenant-ID` | 是 | 租户 ID |
| `Authorization` | 部分 | `Bearer {token}`，需要认证的接口必须提供 |

### 响应格式

所有 API 响应都遵循统一格式：

```json
{
    "success": true/false,
    "code": 2000,
    "message": "响应消息",
    "data": { ... }
}
```

### 响应码说明

| Code | 说明 |
|------|------|
| 2000 | 成功 |
| 4000 | 请求参数错误 |
| 4001 | 未认证 |
| 4003 | 权限不足 |
| 5000 | 服务器内部错误 |

## 测试环境

- **服务器地址**: `http://192.168.1.14:8000`
- **测试租户 ID**: `3`
- **测试用户**: `test02@qq.com`
