# 机器绑定许可证系统部署指南

## 📖 概述

本文档介绍如何部署和配置机器绑定许可证系统，包括环境准备、数据库迁移、基础配置和系统测试。

## 🔧 环境要求

### 系统依赖
- Python 3.8+
- Django 4.0+
- PostgreSQL 12+ (推荐) 或 MySQL 8.0+
- Redis 6.0+ (用于缓存)

### Python包依赖
系统已集成到现有项目，使用现有的依赖配置：
- `cryptography` - RSA和AES加密
- `base58` - 许可证密钥编码
- `djangorestframework` - API框架
- `django-cors-headers` - CORS支持

## 🚀 部署步骤

### 1. 数据库迁移

```bash
# 创建迁移文件（如果还未创建）
python manage.py makemigrations licenses

# 执行迁移
python manage.py migrate

# 验证迁移
python manage.py showmigrations licenses
```

### 2. 创建初始数据

#### 2.1 创建软件产品

```bash
# 使用Django shell创建产品
python manage.py shell

# 在shell中执行
from licenses.models import SoftwareProduct
from tenants.models import Tenant

# 获取或创建租户
tenant = Tenant.objects.first()  # 或创建新租户

# 创建软件产品
product = SoftwareProduct.objects.create(
    name="MyMacApp",
    version="1.0.0",
    description="我的macOS应用程序",
    tenant=tenant,
    status='active'
)
```

#### 2.2 创建许可证方案

```python
from licenses.models import LicensePlan

# 创建基础方案
basic_plan = LicensePlan.objects.create(
    name="基础版",
    description="单机器许可证",
    product=product,
    plan_type="basic",
    max_machines=1,
    duration_days=365,  # 1年有效期
    price=99.00,
    currency="CNY",
    features={
        "core_features": True,
        "advanced_features": False,
        "priority_support": False
    },
    is_active=True
)

# 创建专业版方案
pro_plan = LicensePlan.objects.create(
    name="专业版",
    description="多机器许可证",
    product=product,
    plan_type="professional", 
    max_machines=3,
    duration_days=365,
    price=299.00,
    currency="CNY",
    features={
        "core_features": True,
        "advanced_features": True,
        "priority_support": True,
        "multi_device": True
    },
    is_active=True
)
```

### 3. 生成许可证

#### 3.1 使用管理命令生成

```bash
# 生成单个许可证
python manage.py generate_license_keys \
    --product "MyMacApp" \
    --plan "基础版" \
    --issued-to-name "张三" \
    --issued-to-email "zhangsan@example.com" \
    --notes "测试许可证"

# 批量生成许可证
python manage.py generate_license_keys \
    --product "MyMacApp" \
    --plan "专业版" \
    --count 10 \
    --output licenses_batch.json
```

#### 3.2 使用API生成

```bash
# 获取JWT令牌
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@example.com",
    "password": "your_password"
  }'

# 创建许可证
curl -X POST http://localhost:8000/api/v1/licenses/admin/licenses/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product": 1,
    "plan": 1,
    "issued_to_name": "客户姓名",
    "issued_to_email": "customer@example.com",
    "max_activations": 1
  }'
```

## 📋 配置说明

### 1. Django设置

确保在 `settings.py` 中已添加：

```python
INSTALLED_APPS = [
    # ... 其他应用
    'licenses',
]

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'licenses': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'licenses.security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
    # ... 其他日志配置
}
```

### 2. 安全配置

```python
# 设置强密钥（生产环境）
SECRET_KEY = 'your-very-secure-secret-key'

# CORS配置（如果需要前端访问）
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
]

# API限流配置
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'activation': '10/hour',  # 许可证激活限流
    }
}
```

### 3. 缓存配置

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## 🔐 安全部署建议

### 1. 生产环境密钥管理

```python
# 使用环境变量或密钥管理服务
import os
from django.core.exceptions import ImproperlyConfigured

def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = f"Set the {var_name} environment variable"
        raise ImproperlyConfigured(error_msg)

# 在生产环境中设置
SECRET_KEY = get_env_variable('DJANGO_SECRET_KEY')
DATABASE_PASSWORD = get_env_variable('DATABASE_PASSWORD')
```

### 2. HTTPS配置

```python
# 生产环境安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 3. 数据库安全

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env_variable('DB_NAME'),
        'USER': get_env_variable('DB_USER'),
        'PASSWORD': get_env_variable('DB_PASSWORD'),
        'HOST': get_env_variable('DB_HOST'),
        'PORT': get_env_variable('DB_PORT'),
        'OPTIONS': {
            'sslmode': 'require',  # 要求SSL连接
        },
    }
}
```

## 🧪 系统测试

### 1. 功能测试

```bash
# 测试许可证生成
python manage.py generate_license_keys --product "MyMacApp" --plan "基础版" --count 1

# 测试许可证验证
python manage.py verify_license_integrity --product "MyMacApp"

# 测试密钥轮换
python manage.py rotate_product_keys --product "MyMacApp" --dry-run
```

### 2. API测试

```bash
# 测试服务器状态
curl http://localhost:8000/api/v1/licenses/status/

# 测试许可证信息获取
curl http://localhost:8000/api/v1/licenses/info/YOUR_LICENSE_KEY/

# 测试激活API（需要有效的硬件信息）
curl -X POST http://localhost:8000/api/v1/licenses/activate/ \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "YOUR_LICENSE_KEY",
    "hardware_info": {
      "system_info": {
        "os_version": "macOS 13.0",
        "hostname": "MacBook-Pro.local",
        "architecture": "arm64"
      },
      "hardware_uuid": "test-uuid-12345"
    }
  }'
```

## 📊 监控和维护

### 1. 系统监控

```bash
# 查看许可证使用统计
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/v1/licenses/reports/dashboard/

# 生成使用报告
curl -X POST -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "summary"}' \
  http://localhost:8000/api/v1/licenses/reports/generate/
```

### 2. 定期维护

```bash
# 清理过期许可证（每月执行）
python manage.py cleanup_expired_licenses --days 30

# 验证许可证完整性（每周执行）
python manage.py verify_license_integrity

# 轮换产品密钥（按需执行）
python manage.py rotate_product_keys --product "MyMacApp"
```

### 3. 备份策略

```bash
# 数据库备份
pg_dump -h localhost -U username -d database_name > backup_$(date +%Y%m%d).sql

# 重要配置备份
cp settings.py settings_backup_$(date +%Y%m%d).py
```

## 🚨 故障排除

### 常见问题

1. **迁移失败**
   ```bash
   # 查看详细错误
   python manage.py migrate --verbosity=2
   
   # 回滚迁移
   python manage.py migrate licenses 0001
   ```

2. **许可证验证失败**
   ```bash
   # 检查产品密钥
   python manage.py shell
   >>> from licenses.models import SoftwareProduct
   >>> product = SoftwareProduct.objects.get(name="MyMacApp")
   >>> print(product.public_key_fingerprint)
   ```

3. **激活API错误**
   - 检查硬件信息格式
   - 验证许可证状态
   - 查看API日志

## 📞 技术支持

如遇到部署问题，请检查：
1. Django版本兼容性
2. 数据库权限配置
3. 网络防火墙设置
4. SSL证书配置

系统日志位置：
- 应用日志：`/var/log/licenses/`
- Django日志：根据 `LOGGING` 配置
- 数据库日志：数据库系统日志目录
