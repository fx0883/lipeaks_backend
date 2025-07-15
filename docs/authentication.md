# JWT认证系统

## JWTAuthentication类介绍

`JWTAuthentication` 是本系统中用于处理JWT(JSON Web Token)认证的核心类，它继承自Django REST Framework的`BaseAuthentication`，提供了安全可靠的用户认证机制。

## 工作原理

`JWTAuthentication`类主要完成以下工作：

1. **令牌提取**：从HTTP请求的`Authorization`头中提取Bearer令牌
2. **令牌验证**：使用配置的密钥和算法验证JWT令牌的有效性和完整性
3. **用户检索**：根据令牌中的用户ID从数据库中检索用户对象
4. **状态验证**：检查用户状态、租户状态等，确保只有有效用户才能通过认证

## 源码位置

该类定义在`common/authentication/jwt_auth.py`文件中，包含以下主要方法：

- `authenticate(request)`: 执行认证过程，成功返回(user, token)元组
- `authenticate_header(request)`: 返回认证头字符串
- `extend_schema()`: 为drf-spectacular提供认证模式信息

## 配置选项

JWT认证系统在`settings.py`中配置：

```python
# JWT 设置
JWT_AUTH = {
    'JWT_SECRET_KEY': SECRET_KEY,  # 用于签名的密钥
    'JWT_ALGORITHM': 'HS256',      # 签名算法
    'JWT_EXPIRATION_DELTA': 24 * 3600,  # 访问令牌有效期（秒）
    'JWT_REFRESH_EXPIRATION_DELTA': 7 * 24 * 3600,  # 刷新令牌有效期（秒）
}
```

## 如何使用

### 1. 在Django REST Framework中配置

在`settings.py`中配置REST Framework使用JWT认证：

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'common.authentication.jwt_auth.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    # 其他配置...
}
```

### 2. 生成令牌

用户登录时生成JWT令牌：

```python
from common.authentication.jwt_auth import generate_jwt_token

# 用户登录成功后
tokens = generate_jwt_token(user)
access_token = tokens['access_token']
refresh_token = tokens['refresh_token']

# 返回给客户端
return Response({
    'access_token': access_token,
    'refresh_token': refresh_token,
    'expires_in': settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
})
```

### 3. 刷新令牌

使用刷新令牌获取新的访问令牌：

```python
from common.authentication.jwt_auth import refresh_jwt_token

# 接收客户端发送的刷新令牌
refresh_token = request.data.get('refresh_token')

# 尝试刷新令牌
try:
    new_tokens = refresh_jwt_token(refresh_token)
    return Response(new_tokens)
except Exception as e:
    return Response({'error': str(e)}, status=401)
```

### 4. 在前端使用

前端使用JWT令牌的典型方式：

```javascript
// 存储令牌
localStorage.setItem('access_token', response.data.access_token)
localStorage.setItem('refresh_token', response.data.refresh_token)

// 在请求中使用令牌
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})
```

## 特殊功能

我们的`JWTAuthentication`类包含以下特殊功能：

1. **自动检查用户状态**：只有活跃用户才能通过认证
2. **检查租户状态**：如果用户属于租户，会验证租户是否处于活跃状态
3. **子账号限制**：子账号不允许直接登录系统
4. **令牌过期处理**：自动识别并处理令牌过期情况

## 安全考虑

1. **存储安全**：JWT密钥必须妥善保管，不能泄露
2. **传输安全**：所有API请求应使用HTTPS以保护令牌传输
3. **令牌有效期**：根据系统安全需求设置合适的令牌有效期
4. **刷新令牌保护**：刷新令牌应当更安全地存储，避免泄露

## 常见问题排查

1. **令牌无效**：检查令牌是否过期、是否被篡改、是否使用了正确的密钥签名
2. **权限问题**：JWT认证成功不等于有权限访问资源，权限控制通过权限类(如`TenantApiPermission`)单独处理
3. **前端问题**：确保前端正确存储和发送令牌，检查请求头格式是否为`Authorization: Bearer <token>`

## 日志与调试

系统会记录JWT认证相关的日志：

- 令牌验证失败
- 用户查找失败
- 用户状态异常
- 租户状态异常

查看日志可以帮助排查认证问题：

```python
# 日志示例
logger.warning("令牌已过期")
logger.warning("无效的令牌")
logger.warning(f"用户不存在或已被禁用: {user_id}")
``` 