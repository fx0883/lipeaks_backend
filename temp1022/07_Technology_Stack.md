# 用户反馈系统技术选型

## 文档信息
- **版本**: v1.0
- **创建日期**: 2025-10-22
- **选型原则**: 复用现有技术栈、稳定可靠、易于维护

## 1. 技术栈概览

### 1.1 总体架构

```
┌─────────────────────────────────────────┐
│           前端 (未包含)                  │
│      React / Vue / Angular              │
└──────────────┬──────────────────────────┘
               │ HTTP/HTTPS
               ↓
┌─────────────────────────────────────────┐
│         Web服务器                        │
│      Nginx (反向代理 + 静态文件)         │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│      应用服务器                          │
│    Gunicorn + Django 5.2                │
│  (Python 3.9+)                          │
│                                         │
│  Apps:                                  │
│  ├─ feedbacks (反馈系统) ✨NEW          │
│  ├─ licenses (许可证系统)                │
│  ├─ users (用户系统)                    │
│  ├─ tenants (租户系统)                  │
│  └─ ...                                 │
└──────────────┬──────────────────────────┘
               │
     ┌─────────┼─────────┐
     │         │         │
     ↓         ↓         ↓
┌─────────┐ ┌────────┐ ┌────────┐
│  MySQL  │ │ Redis  │ │ Email  │
│ (数据库) │ │ (缓存) │ │(SMTP)  │
└─────────┘ └────────┘ └────────┘
     ↑         ↑
     │         │
     └────┬────┘
          │
     ┌────┴─────┐
     │  Celery  │
     │ (异步任务)│
     └──────────┘
```

---

## 2. 核心技术选型

### 2.1 后端框架

**选择**: Django 5.2 + Django REST Framework

**理由**:
- ✅ 项目现有技术栈，无需引入新框架
- ✅ 成熟稳定，社区活跃
- ✅ 内置ORM，开发效率高
- ✅ 完善的Admin后台
- ✅ 丰富的第三方包生态

**版本**:
```
Django==5.2
djangorestframework==3.14.0
```

**优势**:
1. **快速开发**: 内置admin、ORM、认证系统
2. **安全性**: 内置CSRF、XSS、SQL注入防护
3. **可扩展**: 插件化设计，易于扩展
4. **文档完善**: 官方文档详细

**劣势**:
1. **性能**: 相比Go/Node.js略低（但满足需求）
2. **异步**: 原生异步支持不如Node.js（通过Celery解决）

---

### 2.2 数据库

**选择**: MySQL 5.7+

**理由**:
- ✅ 项目现有数据库
- ✅ 支持事务、外键约束
- ✅ 性能稳定可靠
- ✅ 运维经验丰富

**配置建议**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'CONN_MAX_AGE': 600,  # 连接池
    }
}
```

**索引策略**:
- 频繁查询字段添加索引
- 联合索引优化查询
- 定期分析慢查询

**备选方案**:
- PostgreSQL: 功能更强大，但需迁移成本
- MongoDB: NoSQL，不适合关系型数据

---

### 2.3 缓存系统

**选择**: Redis

**理由**:
- ✅ 高性能键值存储
- ✅ 支持多种数据结构
- ✅ 可用于缓存、消息队列
- ✅ 易于集成Celery

**使用场景**:
1. **数据缓存**: 热门反馈、统计数据
2. **Session存储**: 用户会话
3. **Celery Broker**: 任务队列
4. **限流**: 频率限制

**配置**:
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

# Session使用Redis
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
```

---

### 2.4 异步任务

**选择**: Celery + Redis

**理由**:
- ✅ Python最流行的异步任务框架
- ✅ 支持定时任务
- ✅ 支持失败重试
- ✅ 监控和管理工具完善

**使用场景**:
1. **邮件发送**: 异步发送，不阻塞API
2. **定时任务**: 清理过期数据、自动关闭反馈
3. **批量处理**: 批量导入、批量通知

**配置**:
```python
# Celery配置
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'

# 任务路由
CELERY_TASK_ROUTES = {
    'feedbacks.tasks.email_tasks.*': {'queue': 'email'},
    'feedbacks.tasks.cleanup_tasks.*': {'queue': 'cleanup'},
}

# 重试配置
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 300  # 5分钟
```

**启动命令**:
```bash
# 邮件队列
celery -A core worker -l info -Q email -c 4

# 清理队列
celery -A core worker -l info -Q cleanup -c 2

# 定时任务
celery -A core beat -l info

# 监控(可选)
celery -A core flower
```

**备选方案**:
- RQ (Redis Queue): 更轻量，但功能较少
- Django-Q: Django原生，但不如Celery成熟

---

### 2.5 邮件服务

**选择**: Django内置邮件 + QQ邮箱SMTP

**理由**:
- ✅ 项目已配置QQ邮箱
- ✅ 免费额度充足
- ✅ 配置简单
- ✅ 稳定可靠

**配置**:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'your_email@qq.com'
EMAIL_HOST_PASSWORD = 'your_auth_code'  # QQ邮箱授权码
DEFAULT_FROM_EMAIL = 'your_email@qq.com'
```

**发送限制**:
- 单日发送限额: 500封
- 单次发送限制: 50个收件人

**备选方案**:
- **SendGrid**: 专业邮件服务，免费100封/天
- **阿里云邮件推送**: 国内稳定，按量付费
- **腾讯云邮件服务**: 与QQ邮箱同源，更稳定

**升级路径**:
```python
# 如需升级到SendGrid
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = 'your_api_key'

# 或阿里云
EMAIL_BACKEND = 'aliyun_email.AliyunEmailBackend'
ALIYUN_ACCESS_KEY_ID = 'your_key'
ALIYUN_ACCESS_KEY_SECRET = 'your_secret'
```

---

### 2.6 文件存储

**选择**: 本地存储 (开发) → 对象存储 (生产)

**开发环境**:
```python
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

**生产环境建议**:
```python
# 使用阿里云OSS / 腾讯云COS
DEFAULT_FILE_STORAGE = 'django_oss_storage.backends.OssMediaStorage'
OSS_ACCESS_KEY_ID = 'your_key'
OSS_ACCESS_KEY_SECRET = 'your_secret'
OSS_BUCKET_NAME = 'your_bucket'
OSS_ENDPOINT = 'oss-cn-hangzhou.aliyuncs.com'
```

**备选方案**:
- **AWS S3**: 国际化项目首选
- **七牛云**: 免费额度大
- **本地 + CDN**: 自建存储 + CDN加速

---

### 2.7 API文档

**选择**: drf-spectacular

**理由**:
- ✅ 项目已使用
- ✅ OpenAPI 3.0标准
- ✅ 自动生成文档
- ✅ Swagger UI集成

**配置**:
```python
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': '用户反馈系统 API',
    'DESCRIPTION': '反馈收集和管理系统',
    'VERSION': '1.0.0',
}
```

**访问**:
- Swagger UI: `/api/v1/docs/`
- ReDoc: `/api/v1/redoc/`
- OpenAPI Schema: `/api/v1/schema/`

---

### 2.8 权限认证

**选择**: JWT (现有系统)

**理由**:
- ✅ 项目已实现JWT认证
- ✅ 无状态，易于扩展
- ✅ 支持跨域
- ✅ 适合前后端分离

**配置**:
```python
JWT_AUTH = {
    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_ALGORITHM': 'HS256',
    'JWT_EXPIRATION_DELTA': 7 * 24 * 3600,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'common.authentication.api_auth.APIJWTAuthentication',
    ),
}
```

---

## 3. 开发工具

### 3.1 代码质量

```bash
# 代码格式化
pip install black
black feedbacks/

# 代码检查
pip install flake8
flake8 feedbacks/

# 类型检查
pip install mypy
mypy feedbacks/

# 安全检查
pip install bandit
bandit -r feedbacks/
```

### 3.2 测试工具

```bash
# 单元测试
python manage.py test feedbacks

# 覆盖率
pip install coverage
coverage run --source='feedbacks' manage.py test
coverage report
coverage html

# 压力测试
pip install locust
locust -f locustfile.py
```

### 3.3 开发环境

```bash
# 虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依赖管理
pip install -r requirements.txt
pip freeze > requirements.txt

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 启动开发服务器
python manage.py runserver

# Celery
celery -A core worker -l info
```

---

## 4. 生产部署

### 4.1 Web服务器

**选择**: Nginx

**配置**:
```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.example.com;
    
    # 静态文件
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    # 媒体文件
    location /media/ {
        alias /path/to/media/;
    }
    
    # API
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4.2 应用服务器

**选择**: Gunicorn

**配置**:
```bash
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 30
keepalive = 2
```

**启动**:
```bash
gunicorn core.wsgi:application -c gunicorn_config.py
```

### 4.3 进程管理

**选择**: Supervisor

**配置**:
```ini
[program:gunicorn]
command=/path/to/venv/bin/gunicorn core.wsgi:application -c gunicorn_config.py
directory=/path/to/project
user=www-data
autostart=true
autorestart=true

[program:celery_worker]
command=/path/to/venv/bin/celery -A core worker -l info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true

[program:celery_beat]
command=/path/to/venv/bin/celery -A core beat -l info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
```

---

## 5. 监控和日志

### 5.1 日志管理

**选择**: Python logging + ELK (可选)

**配置**:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/feedbacks.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'feedbacks': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 5.2 性能监控

**选择**: Django Debug Toolbar (开发) + Prometheus (生产)

```bash
# 开发环境
pip install django-debug-toolbar

# 生产环境
pip install django-prometheus
```

### 5.3 错误追踪

**选择**: Sentry (推荐)

```bash
pip install sentry-sdk

# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your_dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
)
```

---

## 6. 依赖包清单

### 6.1 核心依赖

```txt
# requirements.txt

# Django核心
Django==5.2
djangorestframework==3.14.0
django-cors-headers==4.0.0

# 数据库
pymysql==1.0.3
mysqlclient==2.1.1

# API文档
drf-spectacular==0.26.0
drf-spectacular-sidecar==2023.5.1

# 异步任务
celery==5.2.7
redis==4.5.5
django-redis==5.2.0

# 工具
python-dotenv==1.0.0
Pillow==10.0.0  # 图片处理
django-filter==23.2  # 过滤器

# 开发工具(可选)
django-debug-toolbar==4.1.0
django-extensions==3.2.3
```

### 6.2 测试依赖

```txt
# requirements-dev.txt

coverage==7.2.7
locust==2.15.1
faker==18.13.0
```

---

## 7. 技术债务管理

### 7.1 已知限制

1. **QQ邮箱限制**: 单日500封，需升级到专业邮件服务
2. **本地文件存储**: 生产环境应使用对象存储
3. **同步邮件发送**: 已通过Celery解决

### 7.2 未来优化

1. **数据库读写分离**: 流量增大后考虑
2. **消息队列**: 从Redis升级到RabbitMQ
3. **搜索引擎**: 引入Elasticsearch提升搜索性能
4. **API网关**: 引入Kong/Nginx Plus做API管理

---

## 8. 总结

### 8.1 技术栈总览

| 层次 | 技术选择 | 版本 |
|------|---------|------|
| 编程语言 | Python | 3.9+ |
| Web框架 | Django | 5.2 |
| API框架 | DRF | 3.14 |
| 数据库 | MySQL | 5.7+ |
| 缓存 | Redis | 6.0+ |
| 异步任务 | Celery | 5.2+ |
| Web服务器 | Nginx | 1.18+ |
| 应用服务器 | Gunicorn | 20.1+ |
| 邮件服务 | SMTP (QQ) | - |
| 文件存储 | 本地/OSS | - |

### 8.2 选型优势

✅ **复用现有技术栈**: 降低学习成本和维护成本
✅ **成熟稳定**: 所有技术都是生产环境验证的
✅ **易于扩展**: 模块化设计，便于未来扩展
✅ **开发效率高**: Django生态完善，开发快速
✅ **社区活跃**: 遇到问题容易找到解决方案

### 8.3 相关文档

- [00_方案概述.md](./00_方案概述.md) - 整体方案
- [06_实施计划.md](./06_实施计划.md) - 实施步骤
- [04_邮件系统设计.md](./04_邮件系统设计.md) - 邮件技术细节

