# 密码管理 API

本文档详细描述了与成员(Member)密码管理相关的API端点。

## 1. 修改当前成员密码

修改当前登录成员的密码。

- **URL**: `/api/v1/members/me/password/`
- **Method**: `POST`
- **权限要求**: 需要成员身份验证

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| old_password | string | 是 | 当前密码 |
| new_password | string | 是 | 新密码 |
| new_password_confirm | string | 是 | 确认新密码，必须与new_password一致 |

### 请求示例

```json
{
  "old_password": "current_password123",
  "new_password": "new_password456",
  "new_password_confirm": "new_password456"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "密码修改成功",
  "data": {
    "detail": "密码已成功更新"
  }
}
```

### 错误响应

#### 400 请求参数错误

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "old_password": [
      "当前密码不正确"
    ]
  }
}
```

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "new_password_confirm": [
      "两次输入的新密码不一致"
    ]
  }
}
```

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "new_password": [
      "密码太简单",
      "密码必须包含至少8个字符",
      "密码不能与用户名太相似",
      "密码不能是常见密码"
    ]
  }
}
```

#### 403 权限不足

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": {
    "detail": "该接口仅适用于普通用户"
  }
}
```

## 密码策略

系统对密码有以下要求：

1. 密码长度至少为8个字符
2. 密码不能与用户名太相似
3. 密码不能是常见密码（如"password"、"123456"等）
4. 建议密码包含大小写字母、数字和特殊字符的组合

## 技术实现说明

1. 密码在数据库中以哈希形式存储，使用Django的默认密码哈希机制
2. 密码验证使用Django的密码验证器进行检查
3. 修改密码成功后，系统会自动使用户的其他会话失效，需要重新登录 