# 会员账号注销 API 文档

## 概述

会员注销 API 允许普通用户（Member）永久删除自己的账号及所有关联数据。此操作不可逆。

---

## API 端点

```
POST /api/v1/members/me/deactivate/
```

---

## 认证要求

| 项目 | 说明 |
|------|------|
| 认证方式 | Bearer Token (JWT) |
| 用户类型 | 仅限 Member 用户 |
| 权限要求 | 已登录的普通用户 |

---

## 请求头

| Header | 必填 | 说明 |
|--------|------|------|
| `Authorization` | 是 | Bearer Token，格式: `Bearer <token>` |
| `Content-Type` | 是 | `application/json` |
| `X-Tenant-ID` | 是 | 租户ID |

---

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `password` | string | 是 | 当前账号密码，用于确认注销操作 |
| `reason` | string | 否 | 注销原因（最多500字符），用于统计分析 |

### 请求示例

```json
{
    "password": "your_current_password",
    "reason": "不再使用此服务"
}
```

---

## 响应参数

### 成功响应 (200 OK)

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `success` | boolean | 是否成功，固定为 `true` |
| `code` | integer | 状态码，成功为 `2000` |
| `message` | string | 响应消息 |
| `data` | object | 删除统计数据 |
| `data.deleted_articles` | integer | 删除的文章数量 |
| `data.deleted_article_likes` | integer | 删除的文章点赞数量 |
| `data.deleted_member_likes` | integer | 删除的用户点赞数量 |
| `data.deleted_follows` | integer | 删除的关注关系数量 |
| `data.deleted_points_records` | integer | 删除的积分记录数量 |
| `data.deleted_sub_accounts` | integer | 删除的子账号数量 |

### 成功响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "账号已成功注销",
    "data": {
        "deleted_articles": 5,
        "deleted_article_likes": 10,
        "deleted_member_likes": 3,
        "deleted_follows": 8,
        "deleted_points_records": 15,
        "deleted_sub_accounts": 2
    }
}
```

---

## 错误响应

### 400 Bad Request - 密码错误

```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "password": ["密码错误"]
    }
}
```

### 400 Bad Request - 缺少密码

```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "password": ["This field is required."]
    }
}
```

### 401 Unauthorized - 未认证

```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden - 非Member用户

```json
{
    "detail": "此接口仅适用于普通用户"
}
```

### 500 Internal Server Error - 服务器错误

```json
{
    "detail": "注销失败: <错误详情>"
}
```

---

## 删除的数据范围

注销账号时，以下数据将被**永久删除**：

| 模块 | 数据类型 | 说明 |
|------|----------|------|
| **用户** | Member | 主账号及所有子账号 |
| | PasswordResetToken | 密码重置令牌 |
| **互动** | MemberLike | 发出和收到的用户点赞 |
| | MemberFollow | 关注和被关注关系 |
| | ArticleLike | 文章点赞记录 |
| **内容** | Article | 用户发布的所有文章 |
| **积分** | TenantUserProfile | 租户用户档案 |
| | TenantUserPoints | 积分变动记录 |
| | TenantUserTypeTag | 用户标签关联 |

---

## Curl 测试示例

### 1. 获取登录 Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

### 2. 测试密码错误情况

```bash
TOKEN="your_jwt_token_here"

curl -X POST http://localhost:8000/api/v1/members/me/deactivate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "password": "wrong_password"
  }'
```

**预期响应：**
```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "password": ["密码错误"]
    }
}
```

### 3. 正确注销账号

```bash
TOKEN="your_jwt_token_here"

curl -X POST http://localhost:8000/api/v1/members/me/deactivate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "password": "your_correct_password",
    "reason": "不再使用此服务"
  }'
```

**预期响应：**
```json
{
    "success": true,
    "code": 2000,
    "message": "账号已成功注销",
    "data": {
        "deleted_articles": 0,
        "deleted_article_likes": 0,
        "deleted_member_likes": 0,
        "deleted_follows": 0,
        "deleted_points_records": 0,
        "deleted_sub_accounts": 0
    }
}
```

---

## 完整测试流程

```bash
# 步骤1: 登录获取 Token
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{"username": "test_user", "password": "TestPassword123!"}')

echo "登录响应: $LOGIN_RESPONSE"

# 提取 Token (需要 jq 工具)
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.token')
echo "Token: $TOKEN"

# 步骤2: 注销账号
curl -X POST http://localhost:8000/api/v1/members/me/deactivate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 3" \
  -d '{"password": "TestPassword123!", "reason": "测试注销功能"}'
```

---

## 注意事项

1. **不可逆操作**：注销后无法恢复账号和数据
2. **子账号处理**：主账号注销时，所有子账号也会被一并删除
3. **Token 失效**：注销后，原有的 JWT Token 将无法使用（用户已不存在）
4. **数据备份**：建议用户在注销前自行备份重要数据

---

## 前端集成建议

1. **二次确认**：在调用 API 前，显示确认对话框，明确告知用户此操作不可逆
2. **密码输入**：要求用户输入密码进行身份验证
3. **成功处理**：注销成功后，清除本地存储的 Token 并跳转到登录页或首页
4. **错误处理**：针对不同错误码显示相应的错误提示

### 前端示例代码 (JavaScript)

```javascript
async function deactivateAccount(password, reason = '') {
  const token = localStorage.getItem('token');
  const tenantId = localStorage.getItem('tenantId');
  
  try {
    const response = await fetch('/api/v1/members/me/deactivate/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': tenantId
      },
      body: JSON.stringify({ password, reason })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // 清除本地存储
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      // 跳转到首页
      window.location.href = '/';
    } else {
      // 显示错误信息
      alert(data.data?.password?.[0] || data.message);
    }
  } catch (error) {
    console.error('注销失败:', error);
  }
}
```

---

## 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2024-12-09 | v1.0 | 初始版本，实现会员注销功能 |
