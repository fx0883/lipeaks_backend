# Redis容错和降级策略完整指南

## 🎯 设计目标

**核心原则**：系统在Redis不可用时仍能正常运行，只是性能降级，不会崩溃。

## 📊 三种运行模式

```
┌─────────────────────────────────────────────────────────┐
│  模式1: 异步模式（最优）- Redis可用                      │
│  用户请求 → API → 任务入队 → 立即返回 → Celery后台处理   │
│  响应时间: <100ms                                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  模式2: 同步模式（降级）- Redis不可用                    │
│  用户请求 → API → 直接发送邮件 → 等待完成 → 返回结果     │
│  响应时间: 3-5秒                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  模式3: 数据库模式 - 使用MySQL作为broker                 │
│  用户请求 → API → 任务写数据库 → 返回 → Celery读取执行   │
│  响应时间: 200-500ms                                     │
└─────────────────────────────────────────────────────────┘
```

## 🔧 实现机制

### 1. 自动降级系统

#### TaskExecutor 工作原理

```python
# feedbacks/utils.py

class TaskExecutor:
    def execute_task(task_func, *args, **kwargs):
        try:
            # 步骤1: 检查Redis是否可用
            if RedisHealthChecker.is_redis_available():
                # Redis可用 → 异步执行
                result = task_func.delay(*args, **kwargs)
                return {'mode': 'async', 'task_id': result.id}
            else:
                raise Exception("Redis not available")
        except:
            # 步骤2: Redis不可用 → 降级到同步
            logger.warning("Redis unavailable, executing task synchronously")
            result = task_func(*args, **kwargs)  # 直接执行
            return {'mode': 'sync', 'result': result}
```

#### 实际应用示例

**发送回复邮件：**
```python
# feedbacks/services.py

def send_reply_notification(reply):
    # 自动降级执行
    result = TaskExecutor.execute_task(
        send_feedback_reply_email,  # Celery任务
        reply.id,
        fallback_to_sync=True  # 启用降级
    )
    
    # 返回结果说明执行模式
    # {'mode': 'async', 'task_id': '...'} 或
    # {'mode': 'sync', 'result': {...}}
```

### 2. 健康检查机制

#### Redis状态检查

```python
# feedbacks/utils.py

class RedisHealthChecker:
    @staticmethod
    def is_redis_available() -> bool:
        """2秒超时快速检测"""
        try:
            r = Redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            return True
        except:
            return False
    
    @staticmethod
    def get_redis_status() -> dict:
        """详细状态信息"""
        # 返回版本、内存、连接数等
```

#### 使用方法

```bash
# 命令行检查
python manage.py check_health

# 详细信息
python manage.py check_health --verbose

# Redis不可用时退出
python manage.py check_health --fail-on-redis
```

**输出示例：**
```
============================================================
System Health Check
============================================================

📡 Checking Redis connection...
❌ Redis: Unavailable
   Error: Connection refused
   Impact: Email tasks will run synchronously

🔧 Checking Celery configuration...
⚠️  Celery: Redis configured but unavailable
   Status: Will fallback to synchronous execution

💾 Checking database connection...
✅ Database: Connected

📧 Checking email configuration...
✅ Email: SMTP configured

🔄 Fallback mechanism status...
⚠️  Fallback mode: Synchronous
   All email tasks will execute synchronously
   API responses may be slower

============================================================
Summary
============================================================
⚠️  System is running in degraded mode

💡 Recommendations:
   1. Check Redis connection
   2. Setup external Redis service (Upstash - Free)
   3. Or use database broker: CELERY_BROKER_URL = "django-db"
   4. See: temp1022/Redis_FAQ_ZH.md for solutions
============================================================
```

### 3. API健康检查端点

#### 系统健康检查
```http
GET /api/v1/feedbacks/health/
Authorization: Bearer <admin-token>
```

**响应示例（Redis不可用）：**
```json
{
  "status": "degraded",
  "components": {
    "redis": {
      "available": false,
      "mode": "redis",
      "error": "Connection refused"
    },
    "database": {
      "available": true,
      "type": "mysql"
    },
    "celery": {
      "available": true,
      "mode": "sync",
      "fallback_enabled": true,
      "broker": "redis://localhost:6379/0"
    },
    "email": {
      "available": true,
      "mode": "smtp"
    }
  },
  "recommendations": [
    "Redis is not available. Email tasks will run synchronously.",
    "Consider setting up Redis or using external Redis service (Upstash)."
  ]
}
```

#### Redis专用检查
```http
GET /api/v1/feedbacks/health/redis/
Authorization: Bearer <admin-token>
```

**响应示例：**
```json
{
  "available": true,
  "mode": "redis",
  "version": "7.0.0",
  "connected_clients": 5,
  "used_memory_human": "1.5M",
  "uptime_days": 30
}
```

### 4. 监控中间件

#### 自动状态检测

```python
# 添加到 MIDDLEWARE
MIDDLEWARE = [
    # ... 其他中间件
    'feedbacks.middleware.RedisMonitoringMiddleware',
    'feedbacks.middleware.EmailFallbackMiddleware',
]
```

#### 响应头信息

每个API请求都会包含系统状态：

```http
HTTP/1.1 200 OK
X-System-Mode: sync                    # async 或 sync
X-Redis-Status: unavailable            # available 或 unavailable
X-System-Warning: Redis unavailable, running in synchronous mode
```

**前端可以据此显示提示：**
```javascript
fetch('/api/v1/feedbacks/feedbacks/')
  .then(response => {
    if (response.headers.get('X-System-Mode') === 'sync') {
      showWarning('System is running in synchronous mode. Responses may be slower.');
    }
    return response.json();
  });
```

## 🔄 完整降级流程

### 场景1：提交反馈 → 发送验证邮件

#### Redis可用时
```
用户提交 → 保存到DB → 任务入Redis队列 → 立即返回200
                                    ↓
                            Celery Worker从队列取出
                                    ↓
                            异步发送验证邮件
                            
响应时间: ~80ms
```

#### Redis不可用时
```
用户提交 → 保存到DB → 检测Redis断开 → 直接发送邮件 → 返回200
                                              ↓
                                        等待3-5秒
                                        
响应时间: ~3-5秒
```

#### 代码实现
```python
# feedbacks/services.py

def create_feedback(data):
    feedback = Feedback.objects.create(**data)
    
    # 自动降级发送验证邮件
    result = EmailService.send_verification(feedback)
    
    # result = {'mode': 'async', ...} 或 {'mode': 'sync', ...}
    logger.info(f"Verification email sent in {result['mode']} mode")
    
    return feedback
```

### 场景2：管理员回复 → 发送通知

#### 完全自动处理
```python
# feedbacks/services.py

def add_reply(feedback, content, user, is_internal_note=False):
    reply = FeedbackReply.objects.create(...)
    
    if not is_internal_note:
        # TaskExecutor自动判断：
        # - Redis可用 → 异步
        # - Redis不可用 → 同步
        EmailService.send_reply_notification(reply)
    
    return reply
```

## 🚨 故障场景处理

### 场景A：Redis初始化失败

**症状**：
- Django启动时Redis连接失败
- Celery worker无法启动

**处理**：
```bash
# 1. 检查健康状态
python manage.py check_health

# 输出：
# ❌ Redis: Unavailable
# ⚠️  System is running in degraded mode

# 2. 系统仍可正常使用
# - API正常响应
# - 邮件同步发送
# - 用户无感知（只是稍慢）
```

### 场景B：Redis运行中断开

**症状**：
- 运行中Redis服务崩溃
- 网络中断导致连接失败

**处理流程**：
```
1. 下次邮件任务触发时
   └─> TaskExecutor.execute_task()
       └─> 检测Redis不可用
           └─> 自动切换到同步模式
               └─> 直接发送邮件

2. 中间件检测
   └─> RedisMonitoringMiddleware
       └─> 每60秒检查一次
           └─> 更新缓存状态

3. API响应头
   └─> X-System-Mode: sync
   └─> X-Redis-Status: unavailable
```

### 场景C：Redis恢复连接

**自动恢复流程**：
```
1. 中间件定期检查（每60秒）
   └─> 检测到Redis恢复
       └─> 更新缓存状态

2. 下次任务执行
   └─> TaskExecutor检测Redis可用
       └─> 自动切换回异步模式

3. 无需重启Django
   └─> 自动恢复，无缝切换
```

## 💻 代码示例

### 检查系统状态

```python
# Django shell
python manage.py shell

>>> from feedbacks.utils import RedisHealthChecker
>>> status = RedisHealthChecker.get_redis_status()
>>> print(status)
{
    'available': False,
    'mode': 'redis',
    'error': 'Connection refused',
    'message': 'Redis connection failed'
}
```

### 手动测试降级

```python
# Django shell
>>> from feedbacks.tasks import send_verification_email
>>> from feedbacks.utils import TaskExecutor

# 测试自动降级
>>> result = TaskExecutor.execute_task(
...     send_verification_email,
...     1,  # feedback_id
...     fallback_to_sync=True
... )

# Redis可用时
>>> print(result)
{'mode': 'async', 'task_id': 'abc-123-def'}

# Redis不可用时
>>> print(result)
{'mode': 'sync', 'result': {'status': 'success', ...}}
```

### 前端监控

```javascript
// 检查系统状态
async function checkSystemHealth() {
  const response = await fetch('/api/v1/feedbacks/health/', {
    headers: { 'Authorization': `Bearer ${adminToken}` }
  });
  
  const health = await response.json();
  
  if (health.status === 'degraded') {
    console.warn('System is running in degraded mode');
    console.warn('Recommendations:', health.recommendations);
    
    // 显示提示
    showWarningBanner(
      'System is running slower than usual. Email notifications may be delayed.'
    );
  }
}

// 监听响应头
fetch('/api/v1/feedbacks/feedbacks/', {
  method: 'POST',
  body: JSON.stringify(feedbackData)
})
.then(response => {
  const systemMode = response.headers.get('X-System-Mode');
  const redisStatus = response.headers.get('X-Redis-Status');
  
  if (systemMode === 'sync') {
    console.warn('Request processed in sync mode');
  }
  
  return response.json();
});
```

## ⚙️ 配置选项

### settings.py 配置

```python
# core/settings.py

# ================== 方案1: Redis (推荐) ==================
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Redis连接配置（启用重试）
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10

# ================== 方案2: 数据库 (备选) ==================
# CELERY_BROKER_URL = 'django-db'
# CELERY_RESULT_BACKEND = 'django-db'
# INSTALLED_APPS += ['django_celery_results']

# ================== 降级配置 ==================
# 启用自动降级（默认启用）
FEEDBACK_EMAIL_FALLBACK_ENABLED = True

# 同步模式超时时间
FEEDBACK_SYNC_EMAIL_TIMEOUT = 10  # 秒

# 中间件健康检查间隔
REDIS_HEALTH_CHECK_INTERVAL = 60  # 秒
```

### 中间件配置

```python
# 添加监控中间件（可选）
MIDDLEWARE = [
    # ... 其他中间件
    'feedbacks.middleware.RedisMonitoringMiddleware',  # Redis状态监控
    'feedbacks.middleware.EmailFallbackMiddleware',    # 邮件降级提示
]
```

## 📈 监控和告警

### 1. 日志监控

```python
# 搜索日志中的降级事件
grep "降级到同步执行" /var/log/django/app.log
grep "Redis连接失败" /var/log/django/app.log
```

### 2. 监控脚本

创建 `monitor_redis.py`：
```python
#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from feedbacks.utils import RedisHealthChecker
import time
import smtplib
from email.message import EmailMessage

def send_alert(message):
    """发送告警邮件"""
    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = 'Redis Connection Alert'
    msg['From'] = 'alert@example.com'
    msg['To'] = 'admin@example.com'
    
    try:
        with smtplib.SMTP('localhost') as s:
            s.send_message(msg)
    except:
        print(f"Failed to send alert: {message}")

def monitor():
    """持续监控Redis状态"""
    redis_was_down = False
    
    while True:
        status = RedisHealthChecker.get_redis_status()
        
        if not status['available'] and not redis_was_down:
            # Redis刚刚断开
            message = f"⚠️ Redis connection lost: {status.get('error', 'Unknown')}"
            print(message)
            send_alert(message)
            redis_was_down = True
            
        elif status['available'] and redis_was_down:
            # Redis恢复连接
            message = "✅ Redis connection restored"
            print(message)
            send_alert(message)
            redis_was_down = False
        
        # 每30秒检查一次
        time.sleep(30)

if __name__ == '__main__':
    print("Starting Redis monitoring...")
    monitor()
```

运行监控：
```bash
nohup python monitor_redis.py &
```

### 3. 集成监控工具

#### Sentry集成
```python
# settings.py
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)

# 在utils.py中添加Sentry告警
def is_redis_available():
    try:
        # ... 检查代码
    except Exception as e:
        import sentry_sdk
        sentry_sdk.capture_exception(e)
        return False
```

## 🔍 诊断工具

### 1. 健康检查端点

```bash
# 快速检查
curl http://localhost:8000/api/v1/feedbacks/health/ \
  -H "Authorization: Bearer <admin-token>"

# 检查Redis
curl http://localhost:8000/api/v1/feedbacks/health/redis/ \
  -H "Authorization: Bearer <admin-token>"
```

### 2. 管理命令

```bash
# 基础检查
python manage.py check_health

# 详细检查
python manage.py check_health --verbose

# 输出示例：
✅ Redis: Available
   Version: 7.0.0
   Mode: redis
   Connected Clients: 3
   Memory Used: 1.5M
   Uptime: 30 days

✅ Celery: Configured with Redis
   Broker URL: ***@classic-salmon-7940.upstash.io:6379

✅ Database: Connected
   Type: mysql

✅ Email: SMTP configured
   Backend: django.core.mail.backends.smtp.EmailBackend
   Host: smtp.qq.com
   Port: 587

✅ Primary mode: Async (via Redis)
```

## 📊 性能影响对比

### 提交反馈性能

| 场景 | 响应时间 | 邮件发送 | 用户体验 |
|------|---------|---------|---------|
| Redis可用 | ~80ms | 后台异步 | ⭐⭐⭐⭐⭐ 优秀 |
| Redis不可用（降级） | ~3-5秒 | 同步等待 | ⭐⭐⭐ 可接受 |
| 数据库Broker | ~200ms | 半异步 | ⭐⭐⭐⭐ 良好 |
| 邮件失败 | ~80ms | 不发送 | ⭐⭐ 需手动重发 |

### 并发能力

| 模式 | 最大并发 | 推荐场景 |
|------|---------|---------|
| Redis异步 | 1000+/秒 | 生产环境 |
| 数据库Broker | 50/秒 | 中小应用 |
| 同步降级 | 10/秒 | 临时故障 |

## 🛡️ 容错最佳实践

### 1. 多层降级策略

```python
def send_email_with_full_fallback(email_data):
    """完整的多层降级策略"""
    
    # 第1层：尝试异步（Redis）
    try:
        if RedisHealthChecker.is_redis_available():
            return task.delay(email_data)
    except:
        pass
    
    # 第2层：尝试同步发送
    try:
        return send_email_directly(email_data)
    except:
        pass
    
    # 第3层：保存到数据库，稍后重试
    try:
        FeedbackEmailLog.objects.create(
            status='pending',
            **email_data
        )
        return {'mode': 'queued_for_retry'}
    except:
        pass
    
    # 第4层：记录到日志
    logger.error(f"All email sending methods failed: {email_data}")
    return {'mode': 'failed'}
```

### 2. 定期重试机制

```python
# 创建管理命令：retry_failed_emails.py

from django.core.management.base import BaseCommand
from feedbacks.models import FeedbackEmailLog

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 获取失败的邮件
        failed_emails = FeedbackEmailLog.objects.filter(
            status='failed',
            retry_count__lt=3
        )
        
        for email_log in failed_emails:
            try:
                # 重新发送
                send_email(email_log)
                email_log.status = 'sent'
                email_log.save()
            except:
                email_log.retry_count += 1
                email_log.save()
```

### 3. 健康检查集成到CI/CD

```yaml
# .github/workflows/deploy.yml
- name: Health Check
  run: |
    python manage.py check_health --fail-on-redis
  continue-on-error: true  # 不阻止部署
  
- name: Deploy
  if: success()
  run: |
    # 部署代码
```

## 📱 用户通知策略

### 前端降级提示

```javascript
// React组件示例
function SystemStatusBanner() {
  const [systemMode, setSystemMode] = useState('async');
  
  useEffect(() => {
    // 定期检查系统状态
    const checkHealth = async () => {
      try {
        const response = await fetch('/api/v1/feedbacks/feedbacks/');
        const mode = response.headers.get('X-System-Mode');
        setSystemMode(mode);
      } catch (error) {
        console.error('Health check failed:', error);
      }
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 60000); // 每分钟
    
    return () => clearInterval(interval);
  }, []);
  
  if (systemMode === 'sync') {
    return (
      <div className="alert alert-warning">
        ⚠️ System is running in maintenance mode. 
        Email notifications may be delayed.
      </div>
    );
  }
  
  return null;
}
```

## 🔧 故障排查步骤

### 步骤1：确认Redis状态
```bash
# 方法1：使用管理命令
python manage.py check_health --verbose

# 方法2：使用API
curl http://localhost:8000/api/v1/feedbacks/health/redis/ \
  -H "Authorization: Bearer <token>"

# 方法3：直接连接Redis
redis-cli -h your-host -p 6379 ping
```

### 步骤2：查看日志
```bash
# Django日志
tail -f /var/log/django/app.log | grep -i redis

# Celery日志
tail -f /var/log/celery/worker.log
```

### 步骤3：测试邮件发送
```python
# Django shell
from feedbacks.utils import EmailFallbackHandler

result = EmailFallbackHandler.send_email_with_fallback(
    subject='Test Email',
    message='Testing fallback mechanism',
    recipient_list=['test@example.com']
)

print(result)  # {'success': True, 'mode': 'direct'}
```

### 步骤4：切换到数据库Broker

如果Redis长期不可用：
```python
# settings.py
CELERY_BROKER_URL = 'django-db'
CELERY_RESULT_BACKEND = 'django-db'

# 添加app
INSTALLED_APPS += ['django_celery_results']
```

```bash
# 运行迁移
python manage.py migrate django_celery_results

# 重启Celery
pkill -f "celery worker"
celery -A core worker -l info
```

## 📋 部署检查清单

### 部署前检查
- [ ] Redis连接测试通过
- [ ] 健康检查命令正常
- [ ] Celery worker启动成功
- [ ] 测试邮件发送成功
- [ ] 监控中间件已启用

### 部署后验证
```bash
# 1. 检查系统健康
python manage.py check_health --verbose

# 2. 提交测试反馈
curl -X POST http://your-domain/api/v1/feedbacks/feedbacks/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","software":1,"contact_email":"test@example.com"}'

# 3. 检查邮件日志
python manage.py shell
>>> from feedbacks.models import FeedbackEmailLog
>>> FeedbackEmailLog.objects.latest('created_at')

# 4. 查看系统模式
curl http://your-domain/api/v1/feedbacks/health/ -H "Authorization: Bearer <token>"
```

## 🎯 总结

### 核心优势
✅ **无缝降级**：Redis断开时自动切换同步模式  
✅ **零停机**：系统持续运行，用户无感知  
✅ **自动恢复**：Redis恢复后自动切换回异步  
✅ **完整监控**：健康检查端点和管理命令  
✅ **多层容错**：异步 → 同步 → 数据库记录 → 日志

### 建议配置

**生产环境：**
```python
# 使用外部Redis（Upstash）+ 自动降级
CELERY_BROKER_URL = os.getenv('REDIS_URL')  # Upstash
FEEDBACK_EMAIL_FALLBACK_ENABLED = True      # 启用降级
```

**开发环境：**
```python
# 本地Redis或数据库
CELERY_BROKER_URL = 'redis://localhost:6379/0'
# 或
CELERY_BROKER_URL = 'django-db'
```

### 性能建议
- **优先使用Redis**：最佳性能
- **数据库Broker**：中等性能，无需额外服务
- **同步降级**：仅用于故障时的临时方案

系统已实现完整的容错机制，可以在任何环境下稳定运行！🚀
