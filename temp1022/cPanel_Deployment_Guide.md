
# 数据库作为Celery Broker的配置方案

## ⚠️ 重要警告

**此方案仅适用于以下情况：**
- 开发/测试环境
- 极低流量（每小时<100个任务）
- 无法使用Redis或RabbitMQ
- 临时解决方案

**不推荐原因：**
- ❌ 性能差（数据库不是为消息队列设计的）
- ❌ 数据库负载增加
- ❌ 可能导致锁表问题
- ❌ 扩展性差
- ❌ 官方不推荐

## 配置步骤

### 1. 安装依赖
```bash
pip install django-celery-results
# 不需要 redis
```

### 2. 修改 requirements.txt
```python
# 移除或注释掉：
# celery==5.3.4
# redis==5.0.1
# django-celery-beat==2.5.0

# 改为：
celery==5.3.4  # 保留
django-celery-results==2.5.1  # 保留
# redis==5.0.1  # 注释掉
```

### 3. 修改 Django settings.py

```python
# core/settings.py

# 注释掉Redis配置
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# 使用数据库作为broker
CELERY_BROKER_URL = 'django-db'  # 使用Django数据库作为broker
CELERY_RESULT_BACKEND = 'django-db'  # 使用Django数据库存储结果

# 或者使用更详细的配置：
# CELERY_BROKER_URL = 'sqla+mysql://user:password@localhost/dbname'
# CELERY_RESULT_BACKEND = 'db+mysql://user:password@localhost/dbname'

# 添加到 INSTALLED_APPS
INSTALLED_APPS = [
    # ... 其他apps
    'django_celery_results',  # 必须添加
]

# Celery配置
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# 数据库broker特定配置
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30分钟超时

# 定期清理任务结果（重要！）
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'cleanup-old-results': {
        'task': 'django_celery_results.tasks.cleanup_expired_results',
        'schedule': crontab(hour=4, minute=0),  # 每天凌晨4点
    },
}
```

### 4. 运行迁移
```bash
python manage.py migrate django_celery_results
```

### 5. 修改 Celery 配置文件

```python
# core/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('lipeaks_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')

# 对于数据库broker，需要添加：
app.conf.broker_connection_retry_on_startup = True

app.autodiscover_tasks()
```

### 6. 启动 Celery

```bash
# 开发环境
celery -A core worker -l info

# 生产环境（使用更少并发）
celery -A core worker -l info --concurrency=2 --max-tasks-per-child=100
```

## 性能优化建议

### 1. 定期清理任务表
```python
# 手动清理（Django shell）
from django_celery_results.models import TaskResult
from datetime import timedelta
from django.utils import timezone

# 删除7天前的任务结果
cutoff = timezone.now() - timedelta(days=7)
TaskResult.objects.filter(date_done__lt=cutoff).delete()
```

### 2. 数据库索引
确保任务表有适当的索引：
```sql
-- MySQL
CREATE INDEX idx_task_name ON celery_taskresult(task_name);
CREATE INDEX idx_status ON celery_taskresult(status);
CREATE INDEX idx_date_done ON celery_taskresult(date_done);
```

### 3. 限制任务队列大小
```python
# settings.py
CELERY_TASK_QUEUE_MAX_PRIORITY = 10
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # 一次只取一个任务
```

### 4. 监控数据库大小
```bash
# 检查任务表大小
python manage.py dbshell
```

```sql
-- MySQL
SELECT 
    COUNT(*) as total_tasks,
    SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) as success,
    SUM(CASE WHEN status='FAILURE' THEN 1 ELSE 0 END) as failure,
    SUM(CASE WHEN status='PENDING' THEN 1 ELSE 0 END) as pending
FROM celery_taskresult;
```

## 迁移到Redis方案

当条件允许时，建议迁移到Redis：

### 迁移步骤
1. 安装Redis（见主文档）
2. 更新settings.py配置
3. 重启Celery worker
4. 清理旧的数据库任务表

```bash
# 1. 停止Celery worker
pkill -f "celery worker"

# 2. 更新配置为Redis
# 编辑 settings.py

# 3. 重启worker
celery -A core worker -l info

# 4. 清理数据库（可选）
python manage.py shell
>>> from django_celery_results.models import TaskResult
>>> TaskResult.objects.all().delete()
```

## 故障排查

### 问题1：任务堆积
```python
# 检查待处理任务数量
from django_celery_results.models import TaskResult
pending = TaskResult.objects.filter(status='PENDING').count()
print(f"待处理任务: {pending}")

# 如果数量过多，可以清理：
TaskResult.objects.filter(status='PENDING').delete()
```

### 问题2：数据库锁
```python
# 减少并发worker数量
celery -A core worker -l info --concurrency=1
```

### 问题3：任务超时
```python
# settings.py
CELERY_TASK_TIME_LIMIT = 300  # 5分钟
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4分钟警告
```

## cPanel 特定配置

### 使用 cPanel Cron Jobs

1. 登录 cPanel
2. 找到 "Cron Jobs"
3. 添加以下任务：

```bash
# Celery Worker（保持运行）
* * * * * cd /home/username/lipeaks_backend && /home/username/virtualenv/bin/celery -A core worker -l info --detach

# 清理任务结果（每天）
0 4 * * * cd /home/username/lipeaks_backend && /home/username/virtualenv/bin/python manage.py shell -c "from django_celery_results.models import TaskResult; from datetime import timedelta; from django.utils import timezone; TaskResult.objects.filter(date_done__lt=timezone.now()-timedelta(days=7)).delete()"
```

### Passenger 配置

如果使用 Passenger：

```python
# passenger_wsgi.py
import sys
import os

# Celery 自动启动
def application(environ, start_response):
    # 启动 Celery worker（如果未运行）
    import subprocess
    result = subprocess.run(['pgrep', '-f', 'celery worker'], capture_output=True)
    if not result.stdout:
        subprocess.Popen([
            'celery', '-A', 'core', 'worker',
            '-l', 'info',
            '--detach'
        ])
    
    # 正常 WSGI 应用
    from core.wsgi import application as django_app
    return django_app(environ, start_response)
```

## 性能对比

| 指标 | Redis | 数据库 |
|------|-------|--------|
| 任务处理速度 | >1000/秒 | <10/秒 |
| 延迟 | <1ms | 10-100ms |
| 数据库负载 | 无影响 | 显著增加 |
| 扩展性 | 优秀 | 差 |
| 可靠性 | 高 | 中等 |

## 最终建议

1. **首选**：使用外部Redis服务（Upstash免费版）
2. **备选**：在VPS上安装Redis
3. **临时**：数据库broker（仅用于测试）

**千万不要在生产环境长期使用数据库作为broker！**
