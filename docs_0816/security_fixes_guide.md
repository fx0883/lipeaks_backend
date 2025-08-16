# 安全修复指南

## 1. CORS配置修复

### 问题
`CORS_ALLOW_ALL_ORIGINS = True` 允许所有源访问API

### 修复
```python
# settings.py
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

## 2. SECRET_KEY安全修复

### 问题
SECRET_KEY有默认值，生产环境可能使用默认密钥

### 修复
```python
# settings.py
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")
```

## 3. DEBUG模式安全修复

### 问题
DEBUG模式可能在生产环境被意外启用

### 修复
```python
# settings.py
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
if DEBUG and not os.getenv('ALLOW_DEBUG_IN_PROD'):
    raise ValueError("DEBUG mode not allowed in production")
```

## 4. 数据库连接安全修复

### 问题
缺少SSL连接和连接池配置

### 修复
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
            'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'",
            'autocommit': True,
        },
        'CONN_MAX_AGE': 600,  # 连接池
    }
}
```

## 5. 安全头部配置

### 修复
```python
# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

## 部署检查清单

- [ ] SECRET_KEY已设置为强密钥
- [ ] DEBUG模式已关闭
- [ ] CORS配置已限制允许的源
- [ ] 数据库SSL连接已配置
- [ ] 安全头部已配置
- [ ] HTTPS已启用
