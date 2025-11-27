# 登录认证 API

## 用户登录

### 接口信息

- **URL**: `/api/v1/auth/login/`
- **方法**: `POST`
- **认证**: 不需要
- **描述**: 用户登录获取访问令牌

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `username` | string | 是 | 用户名或邮箱 |
| `password` | string | 是 | 用户密码 |

### 请求头

| 请求头 | 必需 | 说明 |
|--------|------|------|
| `Content-Type` | 是 | `application/json` |
| `X-Tenant-ID` | 是 | 租户 ID |

### 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `token` | string | 访问令牌 (JWT) |
| `refresh_token` | string | 刷新令牌 |
| `user` | object | 用户信息对象 |
| `user.id` | integer | 用户 ID |
| `user.username` | string | 用户名 |
| `user.email` | string | 邮箱 |
| `user.nick_name` | string | 昵称 |
| `user.avatar` | string | 头像完整 URL（包含 domain） |
| `user.is_admin` | boolean | 是否为管理员 |
| `user.is_super_admin` | boolean | 是否为超级管理员 |
| `user.is_member` | boolean | 是否为 Member 用户 |
| `user.is_sub_account` | boolean | 是否为子账号 |
| `user.tenant_id` | integer | 租户 ID |
| `user.tenant_name` | string | 租户名称 |

### curl 示例

```bash
curl -X POST "http://192.168.1.14:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "username": "test02@qq.com",
    "password": "Fengxuan_0027337"
  }'
```

### 成功响应示例 (200)

```json
{
    "success": true,
    "code": 2000,
    "message": "登录成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user": {
            "id": 10,
            "username": "test02@qq.com",
            "email": "test02@qq.com",
            "nick_name": "Nihao",
            "avatar": "http://192.168.1.14:8000/media/avatars/c7e4e047-62d5-4002-b9b8-0f5e480ace78.jpg",
            "is_admin": false,
            "is_super_admin": false,
            "is_member": true,
            "is_sub_account": false,
            "tenant_id": 3,
            "tenant_name": "填色"
        }
    }
}
```

### 错误响应示例

#### 用户名或密码错误 (401)

```json
{
    "success": false,
    "code": 4001,
    "message": "用户名或密码错误",
    "data": null
}
```

#### 参数缺失 (400)

```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "username": ["该字段是必填项。"],
        "password": ["该字段是必填项。"]
    }
}
```

## Token 有效期

| Token 类型 | 有效期 |
|------------|--------|
| 访问令牌 (token) | 60 秒（开发环境）/ 7 天（生产环境） |
| 刷新令牌 (refresh_token) | 28 天 |

> **注意**: 访问令牌过期后，需要使用刷新令牌获取新的访问令牌。
