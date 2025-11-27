# Lipeaks Coloring - 认证 API 文档

> 适用于 Member 用户登录、注册和Token刷新
> 基础URL: `http://localhost:8000`
> 必须Header: `X-Tenant-ID: {租户ID}` (Member用户登录必须)

---

## 1. 用户登录

**接口**: `POST /api/v1/auth/login/`

**描述**: Member用户登录，获取访问Token

### 请求Headers
| Header | 必填 | 说明 |
|--------|------|------|
| Content-Type | 是 | `application/json` |
| X-Tenant-ID | 是 | 租户ID（Member用户必须） |

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名或邮箱 |
| password | string | 是 | 密码 |

### 响应参数
| 参数 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| code | integer | 响应代码，2000=成功 |
| message | string | 响应消息 |
| data.token | string | JWT访问Token（有效期24小时） |
| data.refresh_token | string | 刷新Token（有效期7天） |
| data.user | object | 用户信息对象 |
| data.user.id | integer | 用户ID |
| data.user.username | string | 用户名 |
| data.user.email | string | 邮箱 |
| data.user.nick_name | string | 昵称 |
| data.user.avatar | string | 头像URL |
| data.user.is_admin | boolean | 是否管理员 |
| data.user.is_member | boolean | 是否会员 |
| data.user.is_sub_account | boolean | 是否子账号 |
| data.user.tenant_id | integer | 租户ID |
| data.user.tenant_name | string | 租户名称 |

### curl 示例
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "username": "7548155@qq.com",
    "password": "Fengxuan_0027337"
  }'
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 12,
      "username": "7548155",
      "email": "7548155@qq.com",
      "nick_name": "Whahaha",
      "avatar": "http://localhost:8000/media/avatars/xxx.jpg",
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

### 错误响应
| code | message | 说明 |
|------|---------|------|
| 4001 | 缺少租户ID | Member登录需要X-Tenant-ID Header |
| 4002 | Invalid username/email or password | 用户名或密码错误 |
| 4100 | Tenant operation failed | 租户操作失败 |

---

## 2. 用户注册

**接口**: `POST /api/v1/auth/member/register/`

**描述**: Member用户注册新账号

### 请求Headers
| Header | 必填 | 说明 |
|--------|------|------|
| Content-Type | 是 | `application/json` |
| X-Tenant-ID | 是 | 租户ID |

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（唯一） |
| email | string | 是 | 邮箱地址（唯一） |
| password | string | 是 | 密码（需符合复杂度要求） |
| password_confirm | string | 是 | 确认密码（必须与password一致） |

### 响应参数
| 参数 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| code | integer | 响应代码 |
| message | string | 响应消息 |
| data.token | string | JWT访问Token |
| data.refresh_token | string | 刷新Token |
| data.user | object | 新注册用户信息 |

### curl 示例
```bash
curl -X POST http://localhost:8000/api/v1/auth/member/register/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "username": "new_user",
    "email": "newuser@example.com",
    "password": "Test123456!",
    "password_confirm": "Test123456!"
  }'
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "注册成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 15,
      "username": "new_user",
      "email": "newuser@example.com",
      "nick_name": "",
      "avatar": "",
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

### 错误响应
| code | message | 说明 |
|------|---------|------|
| 4000 | 注册失败 | 验证失败，查看data字段了解详情 |

---

## 3. 刷新Token

**接口**: `POST /api/v1/auth/refresh/`

**描述**: 使用refresh_token获取新的access token

### 请求Headers
| Header | 必填 | 说明 |
|--------|------|------|
| Content-Type | 是 | `application/json` |
| X-Tenant-ID | 是 | 租户ID |

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | 登录时获取的刷新Token |

### 响应参数
| 参数 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| code | integer | 响应代码 |
| message | string | 响应消息 |
| data.token | string | 新的JWT访问Token |
| data.refresh_token | string | 新的刷新Token |

### curl 示例
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "Token refreshed successfully",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

## 通用说明

### Token使用方式
在后续需要认证的API请求中，将token放入Authorization Header：
```
Authorization: Bearer {token}
```

### 错误码说明
| code | 说明 |
|------|------|
| 2000 | 成功 |
| 4000 | 请求参数错误 |
| 4001 | 缺少必要参数 |
| 4002 | 认证失败 |
| 4100 | 租户操作失败 |
| 5000 | 服务器内部错误 |
