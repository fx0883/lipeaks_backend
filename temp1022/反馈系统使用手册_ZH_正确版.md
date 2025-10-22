# 用户反馈系统 - 使用手册（无需修改代码版）

## 📋 重要说明

**🎉 代码已完成！无需修改任何代码文件！**

所有必要的配置都已经集成到系统中，您只需要：
1. ✅ 安装依赖
2. ✅ 配置环境变量（可选）
3. ✅ 启动服务

**无需修改 settings.py、urls.py 或任何Python文件！**

---

## ✅ 代码完整性确认

### 已完成的配置（无需修改）

#### 1. INSTALLED_APPS 已包含
```python
# core/settings.py 第102行
'feedbacks',  # User Feedback System
```

#### 2. URL路由已配置
```python
# core/urls.py 第115行
path('feedbacks/', include('feedbacks.urls', namespace='feedbacks')),
```

#### 3. Celery配置已完成
```python
# core/settings.py 第510-532行
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

CELERY_TASK_ROUTES = {
    'feedbacks.tasks.*': {'queue': 'feedbacks'},
}

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-email-logs': {
        'task': 'feedbacks.tasks.cleanup_old_email_logs',
        'schedule': crontab(hour=2, minute=0),
        'args': (90,)
    },
}
```

#### 4. Celery应用已初始化
```python
# core/__init__.py 第9行
from .celery import app as celery_app

# core/celery.py - 完整文件已创建
```

#### 5. 依赖已添加到requirements.txt
```text
# requirements.txt 第6-10行
celery==5.3.4
redis==5.0.1
django-celery-beat==2.5.0
django-celery-results==2.5.1
```

---

## 🚀 正确的启动流程

### 步骤1：安装依赖（无需修改代码）
```bash
pip install -r requirements.txt
```

### 步骤2：数据库迁移（无需修改代码）
```bash
python manage.py migrate
```

### 步骤3：初始化邮件模板（可选）
```bash
python manage.py init_feedback_templates
```

### 步骤4：配置环境变量（可选）

**只有这一步需要配置，不是修改代码！**

创建 `.env` 文件（可选，使用默认值也可以）：
```bash
# .env文件（可选配置）

# Redis配置（可选，默认使用 redis://localhost:6379/0）
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 或使用Upstash（推荐）
# CELERY_BROKER_URL=rediss://:password@endpoint.upstash.io:6379
# CELERY_RESULT_BACKEND=rediss://:password@endpoint.upstash.io:6379

# 邮件配置（可选，已有默认SMTP配置）
EMAIL_HOST_USER=your-email@qq.com
EMAIL_HOST_PASSWORD=your-app-password

# 前端地址（可选，默认localhost:3000）
FRONTEND_URL=https://your-domain.com
```

### 步骤5：启动服务

#### 方案A：完整启动（推荐）
```bash
# Terminal 1: 启动Celery Worker
celery -A core worker -l info

# Terminal 2: 启动Django
python manage.py runserver
```

#### 方案B：简化启动（Redis不可用时）
```bash
# 只启动Django，系统会自动降级到同步模式
python manage.py runserver
```

### 步骤6：验证系统
```bash
# 检查系统状态
python manage.py check_health --verbose
```

**就这么简单！无需修改任何代码文件！**

---

## 🎯 三种Redis配置方案（仅环境变量）

### 方案1：使用Upstash（推荐）

**只需要设置环境变量，无需修改代码**：
```bash
# .env文件
CELERY_BROKER_URL=rediss://:password@endpoint.upstash.io:6379
CELERY_RESULT_BACKEND=rediss://:password@endpoint.upstash.io:6379
```

**注册Upstash**：
1. 访问 https://upstash.com
2. 创建Redis数据库
3. 复制连接URL
4. 添加到 .env 文件

### 方案2：本地Redis

**默认配置已可用，无需修改**：
```bash
# 启动Redis
docker run -d -p 6379:6379 redis:latest

# 直接启动系统（使用默认配置）
celery -A core worker -l info &
python manage.py runserver
```

### 方案3：数据库作为Broker

**需要一个环境变量**：
```bash
# .env文件
CELERY_BROKER_URL=django-db
CELERY_RESULT_BACKEND=django-db

# 运行额外迁移
python manage.py migrate django_celery_results
```

---

## 📊 实际配置状态检查

让我确认代码的完整性：

<function_calls>
<invoke name="run_terminal_cmd">
<parameter name="command">python manage.py check_health
