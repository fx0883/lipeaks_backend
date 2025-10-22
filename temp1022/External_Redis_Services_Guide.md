# 外部Redis服务配置指南（cPanel环境）

## 🌟 推荐方案：使用外部Redis服务

由于cPanel共享主机通常无法安装Redis，使用外部托管的Redis服务是最佳选择。

## 🆓 免费Redis服务提供商

### 1. Upstash（强烈推荐）

**优势：**
- ✅ 永久免费计划：10,000命令/天
- ✅ 全球边缘网络，低延迟
- ✅ REST API支持（无需TCP连接）
- ✅ 自动备份
- ✅ TLS加密
- ✅ 中国可访问

**注册步骤：**

1. 访问：https://upstash.com/
2. 使用GitHub/Google登录
3. 创建Redis数据库
4. 选择区域（建议选择离您最近的）
5. 获取连接信息

**配置示例：**
```python
# settings.py
CELERY_BROKER_URL = 'rediss://:your-password@your-endpoint.upstash.io:6379'
CELERY_RESULT_BACKEND = 'rediss://:your-password@your-endpoint.upstash.io:6379'


# UPSTASH_REDIS_REST_URL="https://classic-salmon-7940.upstash.io"
# UPSTASH_REDIS_REST_TOKEN="AR8EAAImcDIyNDM5Y2MwOWY0OWU0ZDFmYTdkOWNhOWJjMDAxNTA2OXAyNzk0MA"

# 使用REST API（如果TCP端口被阻止）
CELERY_BROKER_URL = 'https://your-endpoint.upstash.io'
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'headers': {
        'Authorization': 'Bearer your-token'
    }
}
```

### 2. Redis Labs (Redis Cloud)

**优势：**
- ✅ 免费30MB
- ✅ 官方服务，稳定可靠
- ✅ 全球多个数据中心
- ✅ 专业支持

**注册步骤：**

1. 访问：https://redis.com/try-free/
2. 注册账号
3. 创建免费订阅
4. 创建数据库
5. 获取endpoint和密码

**配置示例：**
```python
# settings.py
CELERY_BROKER_URL = 'redis://default:your-password@redis-12345.c1.us-east-1.cloud.redislabs.com:12345'
CELERY_RESULT_BACKEND = 'redis://default:your-password@redis-12345.c1.us-east-1.cloud.redislabs.com:12345'
```


<!-- REDIS_URL="rediss://default:AR8EAAImcDIyNDM5Y2MwOWY0OWU0ZDFmYTdkOWNhOWJjMDAxNTA2OXAyNzk0MA@classic-salmon-7940.upstash.io:6379" -->



### 3. Render (Redis)

**优势：**
- ✅ 免费25MB
- ✅ 自动备份
- ✅ 易于使用

**配置：**
```python
CELERY_BROKER_URL = os.getenv('REDIS_URL')  # Render自动设置环境变量
```

### 4. Railway

**优势：**
- ✅ 免费$5信用/月
- ✅ 自动扩展

**配置：**
```python
CELERY_BROKER_URL = os.getenv('REDIS_PRIVATE_URL')
```

## 🔒 安全配置

### 使用环境变量

**不要**在代码中硬编码密码！

#### 方法1：使用 .env 文件

```bash
# .env
REDIS_URL=rediss://:password@endpoint.upstash.io:6379
```

```python
# settings.py
from dotenv import load_dotenv
import os

load_dotenv()

CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')
```

#### 方法2：cPanel 环境变量

在cPanel中设置环境变量：
1. Setup Python App
2. Environment Variables
3. 添加 `REDIS_URL`

### TLS/SSL 配置

```python
# settings.py
CELERY_BROKER_URL = 'rediss://...'  # 注意是 rediss:// (两个s)
CELERY_BROKER_USE_SSL = {
    'ssl_cert_reqs': 'CERT_REQUIRED',
    'ssl_ca_certs': '/etc/ssl/certs/ca-certificates.crt'  # Linux
    # 'ssl_ca_certs': certifi.where()  # 或使用certifi
}
```

## 📊 性能优化

### 连接池配置

```python
# settings.py
CELERY_BROKER_POOL_LIMIT = 10  # 连接池大小
CELERY_BROKER_CONNECTION_TIMEOUT = 30  # 连接超时
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
```

### 网络优化

对于高延迟网络（国际连接）：

```python
# settings.py
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,  # 1小时
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
}

# 减少心跳频率
BROKER_HEARTBEAT = 60  # 60秒
```

### 数据压缩

```python
# 对于慢速网络，启用压缩
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'
```

## 🧪 测试连接

### Python 测试脚本

```python
# test_redis.py
import redis
import os

# 从环境变量读取
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

try:
    # 连接Redis
    r = redis.from_url(redis_url)
    
    # 测试ping
    print("测试连接...")
    result = r.ping()
    print(f"✅ Ping成功: {result}")
    
    # 测试写入
    print("\n测试写入...")
    r.set('test_key', 'Hello from Python!')
    print("✅ 写入成功")
    
    # 测试读取
    print("\n测试读取...")
    value = r.get('test_key')
    print(f"✅ 读取成功: {value.decode('utf-8')}")
    
    # 清理
    r.delete('test_key')
    print("\n✅ 所有测试通过！")
    
except Exception as e:
    print(f"❌ 错误: {str(e)}")
```

运行测试：
```bash
python test_redis.py
```

### Celery 测试

```python
# Django shell
python manage.py shell

>>> from feedbacks.tasks import send_verification_email
>>> result = send_verification_email.delay(1)
>>> print(result.id)  # 任务ID
>>> print(result.state)  # 任务状态
>>> print(result.get(timeout=10))  # 等待结果
```

## 📝 cPanel 完整配置示例

### 1. 项目结构
```
/home/username/
├── lipeaks_backend/
│   ├── core/
│   ├── feedbacks/
│   └── .env  # 环境变量文件
└── virtualenv/  # Python虚拟环境
```

### 2. .env 文件
```bash
# .env
REDIS_URL=rediss://:abc123@redis-12345.upstash.io:6379
DJANGO_SETTINGS_MODULE=core.settings
DEBUG=False
```

### 3. settings.py 配置
```python
# core/settings.py
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Redis配置
REDIS_URL = os.getenv('REDIS_URL')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Celery配置
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'  # 你的时区
CELERY_ENABLE_UTC = True

# 连接配置
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
```

### 4. Celery 启动脚本

创建 `start_celery.sh`：
```bash
#!/bin/bash
cd /home/username/lipeaks_backend
source /home/username/virtualenv/bin/activate
celery -A core worker -l info --logfile=/home/username/logs/celery.log --detach
```

### 5. Cron Job 配置

在cPanel的Cron Jobs中添加：

```bash
# 确保Celery worker运行（每5分钟检查）
*/5 * * * * /home/username/lipeaks_backend/start_celery.sh

# 或者使用supervisor（如果可用）
* * * * * supervisorctl start celery
```

## 🐛 故障排查

### 问题1：连接超时

```python
# 增加超时时间
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'socket_timeout': 60,
    'socket_connect_timeout': 60,
}
```

### 问题2：SSL证书错误

```python
# 临时禁用SSL验证（不推荐生产环境）
CELERY_BROKER_USE_SSL = {
    'ssl_cert_reqs': 'CERT_NONE'
}
```

### 问题3：防火墙阻止

尝试使用REST API：
```python
# Upstash支持REST API
pip install upstash-redis

from upstash_redis import Redis
redis = Redis(url='https://...', token='...')
```

### 问题4：任务丢失

```python
# 启用任务确认
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
```

## 💰 成本估算

### 免费方案对比

| 服务商 | 免费额度 | 适用场景 |
|--------|---------|---------|
| Upstash | 10k命令/天 | 小型应用 |
| Redis Labs | 30MB存储 | 中型应用 |
| Render | 25MB | 小型应用 |
| Railway | $5/月 | 测试环境 |

### 升级建议

- **<1000用户**：免费方案足够
- **1000-10000用户**：升级到付费基础版（$5-10/月）
- **>10000用户**：专用Redis实例

## ✅ 最佳实践

1. **使用TLS加密连接**
2. **设置强密码**
3. **定期备份**（大多数服务自动提供）
4. **监控使用量**
5. **设置连接池**
6. **使用环境变量**
7. **启用压缩**（慢速网络）
8. **配置重试机制**

## 🎯 推荐配置（生产环境）

```python
# settings.py
import os
import certifi

# Redis连接
REDIS_URL = os.getenv('REDIS_URL')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# 安全配置
CELERY_BROKER_USE_SSL = {
    'ssl_cert_reqs': 'CERT_REQUIRED',
    'ssl_ca_certs': certifi.where(),
}

# 性能配置
CELERY_BROKER_POOL_LIMIT = 10
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10

# 网络配置
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
}

# 任务配置
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'
CELERY_RESULT_EXPIRES = 3600  # 结果保留1小时

# 序列化配置
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
```

## 📞 获取帮助

如果遇到问题：

1. 查看服务商文档
2. 检查Redis日志
3. 测试网络连接
4. 联系服务商支持

**Upstash支持：** support@upstash.com  
**Redis Labs支持：** https://redis.com/company/support/
