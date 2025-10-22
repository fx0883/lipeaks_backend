# Redis配置快速参考卡

## 🎯 三种Redis配置方案速查

---

## 方案1：Upstash（推荐⭐⭐⭐⭐⭐）

### 特点
- ✅ **完全免费**（10,000操作/天）
- ✅ **5分钟设置**
- ✅ **无需服务器权限**
- ✅ **高可用性**（99.99%在线）

### 配置步骤

#### 第1步：注册和创建
```
1. 访问：https://upstash.com
2. 用GitHub/Google登录
3. 点击"Create Database"
4. 选择区域（选择China或Hong Kong）
5. 点击"Create"
```

#### 第2步：获取连接信息
```
进入数据库 → Copy → Redis Connect URL
格式：rediss://:password@endpoint.upstash.io:6379
```

#### 第3步：配置Django
```bash
# .env文件
REDIS_URL=rediss://:AR8EAAImcDIyNDM5Y2MwOWY0OWU0ZDFmYTdkOWNhOWJjMDAxNTA2OXAyNzk0MA@classic-salmon-7940.upstash.io:6379
```

```python
# core/settings.py
from dotenv import load_dotenv
load_dotenv()

CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')
```

#### 第4步：验证
```bash
python manage.py check_health
# 期望输出：[OK] Redis: Available
```

---

## 方案2：数据库Broker（备选⭐⭐⭐⭐）

### 特点
- ✅ **无需Redis**
- ✅ **配置简单**
- ⚠️ **性能一般**（50-100请求/秒）
- ⚠️ **数据库负载增加**

### 配置步骤

#### 第1步：修改settings.py
```python
# core/settings.py

# 使用数据库作为broker
CELERY_BROKER_URL = 'django-db'
CELERY_RESULT_BACKEND = 'django-db'

# 必须添加此app
INSTALLED_APPS = [
    # ... 其他apps
    'django_celery_results',  # 必须
    'feedbacks',
]

# 性能配置
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30分钟超时
```

#### 第2步：数据库迁移
```bash
python manage.py migrate django_celery_results
python manage.py migrate
```

#### 第3步：验证
```bash
python manage.py check_health
# 期望输出：[WARN] Redis: Not configured (using database)
```

---

## 方案3：本地Redis（开发环境⭐⭐⭐）

### 特点
- ✅ **最佳性能**
- ✅ **完整功能**
- ❌ **需要安装Redis**
- ❌ **需要服务器权限**

### 安装和配置

#### Windows（Docker）
```bash
# 安装Docker Desktop后
docker run -d -p 6379:6379 --name redis redis:latest
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### macOS
```bash
brew install redis
brew services start redis
```

#### 配置Django
```python
# core/settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

#### 验证
```bash
redis-cli ping  # 应返回PONG
python manage.py check_health  # 应显示Redis Available
```

---

## 🔧 配置文件位置总览

### 主要配置文件

| 文件 | 位置 | 用途 |
|------|------|------|
| **settings.py** | `core/settings.py` | 主配置文件，包含Redis/Celery配置 |
| **.env** | 项目根目录 | 敏感信息（Redis URL、邮箱密码） |
| **requirements.txt** | 项目根目录 | 依赖包（已包含Celery） |
| **celery.py** | `core/celery.py` | Celery应用配置 |

### 关键配置片段

#### settings.py中的Redis配置（完整版）
```python
# core/settings.py

# ==================== Redis/Celery配置 ====================

from dotenv import load_dotenv
import os

load_dotenv()

# 方案选择（三选一）
# 方案1：Upstash（推荐）
CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')

# 方案2：本地Redis
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# 方案3：数据库broker
# CELERY_BROKER_URL = 'django-db'
# CELERY_RESULT_BACKEND = 'django-db'
# INSTALLED_APPS += ['django_celery_results']

# 基础配置
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# 连接配置（重要！）
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
CELERY_BROKER_CONNECTION_TIMEOUT = 30

# 安全配置（生产环境）
if not DEBUG:
    CELERY_BROKER_USE_SSL = {
        'ssl_cert_reqs': 'CERT_REQUIRED',
    }

# 性能配置
CELERY_BROKER_POOL_LIMIT = 10
CELERY_TASK_ROUTES = {
    'feedbacks.tasks.*': {'queue': 'feedbacks'},
}

# 定时任务
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'cleanup-old-email-logs': {
        'task': 'feedbacks.tasks.cleanup_old_email_logs',
        'schedule': crontab(hour=2, minute=0),
        'args': (90,)
    },
}

# ==================== 邮件配置 ====================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# 前端URL（用于邮件链接）
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# ==================== 容错中间件（可选）====================

MIDDLEWARE = [
    # ... 其他中间件
    'feedbacks.middleware.RedisMonitoringMiddleware',  # Redis监控
    'feedbacks.middleware.EmailFallbackMiddleware',    # 邮件降级提示
]
```

---

## 🧪 配置验证

### 验证命令
```bash
# 完整健康检查
python manage.py check_health --verbose

# Redis专用检查
python -c "from feedbacks.utils import RedisHealthChecker; print('Redis可用:', RedisHealthChecker.is_redis_available())"

# 邮件配置检查
python manage.py shell -c "from django.core.mail import send_mail; print('邮件配置正常')"
```

### 期望输出

#### Redis可用时
```
[OK] Redis: Available
   Version: 7.0.0
   Mode: redis

[OK] Celery: Configured with Redis
[OK] Primary mode: Async (via Redis)
[OK] System is running optimally
```

#### Redis不可用时（自动降级）
```
[FAIL] Redis: Unavailable
   Error: Connection refused

[WARN] Fallback mode: Synchronous
[WARN] System is running in degraded mode
```

---

## ⚡ 常用配置模板

### cPanel环境配置
```python
# core/settings.py

# 使用Upstash（推荐）
CELERY_BROKER_URL = os.getenv('REDIS_URL')  
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')

# 或使用数据库（备选）
# CELERY_BROKER_URL = 'django-db'
# CELERY_RESULT_BACKEND = 'django-db'
# INSTALLED_APPS += ['django_celery_results']

# 基础配置（必需）
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = True

# 容错配置（重要）
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
```

### Docker环境配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  web:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  celery:
    build: .
    command: celery -A core worker -l info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
```

---

## 📞 配置问题求助

### 常见配置错误

#### 错误1：ModuleNotFoundError: No module named 'celery'
```bash
# 解决方案
pip install -r requirements.txt
# 或
pip install celery==5.3.4 redis==5.0.1
```

#### 错误2：Redis连接被拒绝
```bash
# 检查Redis是否运行
docker ps | grep redis
redis-cli ping

# 检查防火墙
telnet localhost 6379

# 使用Upstash替代
# 见方案1配置
```

#### 错误3：邮件发送失败
```python
# 检查邮件配置
print(settings.EMAIL_HOST)
print(settings.EMAIL_HOST_USER)
# 确认使用应用专用密码，非登录密码
```

### 获取帮助

1. **运行诊断**：`python manage.py check_health --verbose`
2. **查看文档**：`反馈系统使用手册_ZH.md`
3. **检查日志**：Django和Celery错误日志
4. **测试API**：http://localhost:8000/api/v1/docs/

---

## ✅ 配置确认清单

- [ ] **Redis配置**：CELERY_BROKER_URL已设置
- [ ] **环境变量**：.env文件已创建并配置
- [ ] **应用添加**：'feedbacks'已加入INSTALLED_APPS
- [ ] **URL配置**：feedbacks路由已包含
- [ ] **邮件配置**：SMTP设置已完成
- [ ] **依赖安装**：requirements.txt已安装
- [ ] **数据迁移**：migrate已执行
- [ ] **健康检查**：check_health命令通过

**完成以上清单，系统即可正常运行！** 🚀
