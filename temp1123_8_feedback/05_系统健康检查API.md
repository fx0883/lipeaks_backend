# 系统健康检查 API 文档

## 概述

系统健康检查API提供了系统各组件的健康状态监控，包括数据库、Redis、Celery和邮件服务等。

---

## 1. 系统健康检查

### 基本信息
- **接口**: `GET /api/v1/feedbacks/health/`
- **权限**: 仅管理员
- **说明**: 
  - 检查所有关键系统组件的健康状态
  - 提供优化建议
  - 用于监控和故障排查

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 系统整体状态：healthy(健康), degraded(降级), unhealthy(不健康) |
| components | object | 各组件的详细状态 |
| recommendations | array | 系统优化建议 |

### 组件状态

#### Redis
| 字段 | 说明 |
|------|------|
| available | Redis是否可用 |
| mode | 连接模式：redis, upstash, fallback |
| version | Redis版本（如果可用） |
| error | 错误信息（如果不可用） |

#### Database
| 字段 | 说明 |
|------|------|
| available | 数据库是否可用 |
| type | 数据库类型：mysql, postgresql, sqlite |

#### Celery
| 字段 | 说明 |
|------|------|
| available | Celery是否可用 |
| mode | 运行模式：async(异步), sync(同步), database(数据库broker) |
| fallback_enabled | 是否启用降级模式 |
| broker | Broker URL |

#### Email
| 字段 | 说明 |
|------|------|
| available | 邮件服务是否可用 |
| mode | 邮件模式：smtp, console |
| backend | 邮件后端 |

### 响应示例

#### 健康状态

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "status": "healthy",
        "components": {
            "redis": {
                "available": true,
                "mode": "redis",
                "version": "7.0.0"
            },
            "database": {
                "available": true,
                "type": "mysql"
            },
            "celery": {
                "available": true,
                "mode": "async",
                "fallback_enabled": true,
                "broker": "redis://localhost:6379/0"
            },
            "email": {
                "available": true,
                "mode": "smtp",
                "backend": "django.core.mail.backends.smtp.EmailBackend"
            }
        },
        "recommendations": []
    }
}
```

#### 降级状态（Redis不可用）

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "status": "degraded",
        "components": {
            "redis": {
                "available": false,
                "mode": "redis",
                "error": "Error 61 connecting to localhost:6379. Connection refused.",
                "message": "Redis connection failed"
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
                "mode": "smtp",
                "backend": "django.core.mail.backends.smtp.EmailBackend"
            }
        },
        "recommendations": [
            "Redis is not available. Email tasks will run synchronously.",
            "Consider setting up Redis or using external Redis service (Upstash)."
        ]
    }
}
```

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/health/" \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -m json.tool
```

---

## 2. Redis状态检查

### 基本信息
- **接口**: `GET /api/v1/feedbacks/health/redis/`
- **权限**: 仅管理员
- **说明**: 
  - 专门检查Redis连接状态
  - 提供详细的配置建议
  - 用于Redis故障排查

### 响应示例

#### Redis正常

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "available": true,
        "mode": "redis",
        "version": "7.0.0",
        "host": "localhost",
        "port": 6379
    }
}
```

#### Redis不可用

```json
{
    "success": true,
    "code": 2000,
    "message": "Redis connection failed",
    "data": {
        "available": false,
        "mode": "redis",
        "error": "Error 61 connecting to localhost:6379. Connection refused.",
        "message": "Redis connection failed",
        "suggestions": [
            {
                "priority": "high",
                "title": "Setup External Redis",
                "description": "Use Upstash for free Redis hosting",
                "link": "/api/v1/feedbacks/docs/#section/External-Redis-Services"
            },
            {
                "priority": "medium",
                "title": "Use Database Broker",
                "description": "Temporary solution with lower performance",
                "config": "CELERY_BROKER_URL = \"django-db\""
            }
        ]
    }
}
```

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/health/redis/" \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -m json.tool
```

---

## 状态说明

### 系统状态级别

| 状态 | 说明 | 示例场景 |
|------|------|----------|
| healthy | 所有组件正常运行 | 所有服务可用 |
| degraded | 部分组件异常但系统可用 | Redis不可用，使用同步模式 |
| unhealthy | 关键组件异常 | 数据库连接失败 |

### Redis模式说明

| 模式 | 说明 | 性能 |
|------|------|------|
| redis | 本地Redis | 最佳 |
| upstash | 外部Redis服务 | 良好 |
| fallback | 降级到同步模式 | 一般 |

### Celery模式说明

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| async | 异步执行（推荐） | 生产环境 |
| sync | 同步执行 | 开发环境或Redis不可用时 |
| database | 使用数据库作为broker | 临时方案 |

---

## 使用场景

### 场景1：系统监控

定期检查系统健康状态：

```bash
#!/bin/bash
# health_monitor.sh - 系统健康监控脚本

TOKEN="YOUR_TOKEN"
LOG_FILE="/var/log/feedback_health.log"

while true; do
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  
  # 获取健康状态
  HEALTH=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/health/" \
    -H "Authorization: Bearer $TOKEN")
  
  STATUS=$(echo $HEALTH | jq -r '.data.status')
  
  # 记录日志
  echo "[$TIMESTAMP] System Status: $STATUS" >> $LOG_FILE
  
  # 如果状态异常，发送告警
  if [ "$STATUS" != "healthy" ]; then
    echo "[$TIMESTAMP] WARNING: System is $STATUS" >> $LOG_FILE
    echo "$HEALTH" | jq '.data.recommendations[]' >> $LOG_FILE
    
    # 可选：发送邮件或Slack通知
    # send_alert "$HEALTH"
  fi
  
  # 每5分钟检查一次
  sleep 300
done
```

### 场景2：部署前检查

部署新版本前验证系统状态：

```bash
#!/bin/bash
# pre_deploy_check.sh

TOKEN="YOUR_TOKEN"

echo "开始部署前检查..."

# 1. 检查系统健康
HEALTH=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/health/" \
  -H "Authorization: Bearer $TOKEN")

STATUS=$(echo $HEALTH | jq -r '.data.status')

if [ "$STATUS" != "healthy" ]; then
  echo "❌ 系统状态异常: $STATUS"
  echo "建议:"
  echo "$HEALTH" | jq -r '.data.recommendations[]'
  exit 1
fi

# 2. 检查Redis
REDIS=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/health/redis/" \
  -H "Authorization: Bearer $TOKEN")

REDIS_AVAILABLE=$(echo $REDIS | jq -r '.data.available')

if [ "$REDIS_AVAILABLE" != "true" ]; then
  echo "⚠️  Redis不可用，系统将使用降级模式"
fi

# 3. 检查数据库连接
DB_AVAILABLE=$(echo $HEALTH | jq -r '.data.components.database.available')

if [ "$DB_AVAILABLE" != "true" ]; then
  echo "❌ 数据库连接失败"
  exit 1
fi

echo "✅ 所有检查通过，可以部署"
exit 0
```

### 场景3：故障排查

Redis连接问题排查：

```bash
#!/bin/bash
# redis_troubleshoot.sh

TOKEN="YOUR_TOKEN"

echo "Redis故障排查..."
echo "===================="

# 1. 检查Redis状态
REDIS_STATUS=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/health/redis/" \
  -H "Authorization: Bearer $TOKEN")

echo "Redis状态:"
echo "$REDIS_STATUS" | jq '.'

AVAILABLE=$(echo $REDIS_STATUS | jq -r '.data.available')

if [ "$AVAILABLE" != "true" ]; then
  echo ""
  echo "Redis不可用，建议的解决方案:"
  echo "$REDIS_STATUS" | jq -r '.data.suggestions[] | "[\(.priority)] \(.title): \(.description)"'
  
  echo ""
  echo "快速修复步骤:"
  echo "1. 检查Redis服务是否运行: redis-cli ping"
  echo "2. 检查连接配置: cat .env | grep REDIS"
  echo "3. 尝试启动Redis: redis-server"
  echo "4. 或使用数据库broker: CELERY_BROKER_URL='django-db'"
fi
```

---

## 监控集成

### Prometheus集成

导出健康检查指标：

```python
# metrics_exporter.py
import requests
from prometheus_client import Gauge, start_http_server

# 定义指标
system_health = Gauge('feedback_system_health', 'System health status', ['component'])

def collect_metrics():
    response = requests.get(
        'http://localhost:8000/api/v1/feedbacks/health/',
        headers={'Authorization': 'Bearer YOUR_TOKEN'}
    )
    data = response.json()['data']
    
    # 导出各组件状态
    for component, status in data['components'].items():
        value = 1 if status.get('available') else 0
        system_health.labels(component=component).set(value)

if __name__ == '__main__':
    start_http_server(8001)
    while True:
        collect_metrics()
        time.sleep(60)
```

### Grafana Dashboard

创建监控面板的查询示例：

```promql
# Redis可用性
feedback_system_health{component="redis"}

# 数据库可用性
feedback_system_health{component="database"}

# 总体健康度
avg(feedback_system_health)
```

---

## 告警规则

### 配置告警

```yaml
# alertmanager.yml
groups:
  - name: feedback_system
    interval: 60s
    rules:
      - alert: RedisDown
        expr: feedback_system_health{component="redis"} == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis is unavailable"
          description: "Redis has been unavailable for 5 minutes"
      
      - alert: DatabaseDown
        expr: feedback_system_health{component="database"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is unavailable"
          description: "Database connection failed"
```

---

## 最佳实践

### 1. 定期检查

- 生产环境：每1-5分钟检查一次
- 测试环境：每15-30分钟检查一次
- 开发环境：手动检查或部署前检查

### 2. 告警阈值

| 组件 | 告警级别 | 触发条件 |
|------|----------|----------|
| 数据库 | Critical | 不可用 > 1分钟 |
| Redis | Warning | 不可用 > 5分钟 |
| Email | Info | 不可用 > 30分钟 |

### 3. 日志记录

记录所有健康检查结果，便于：
- 故障分析
- 性能趋势分析
- SLA报告

### 4. 自动恢复

```bash
# auto_recovery.sh
# 自动恢复脚本示例

if ! redis-cli ping > /dev/null 2>&1; then
  echo "Redis down, attempting recovery..."
  sudo systemctl restart redis
  sleep 5
  
  if redis-cli ping > /dev/null 2>&1; then
    echo "Redis recovered successfully"
  else
    echo "Redis recovery failed, sending alert..."
    send_alert "Redis auto-recovery failed"
  fi
fi
```

---

## 故障处理流程

### Redis故障

1. **检测**：健康检查发现Redis不可用
2. **降级**：系统自动切换到同步模式
3. **告警**：通知运维人员
4. **修复**：
   - 检查Redis服务状态
   - 检查网络连接
   - 查看Redis日志
   - 重启Redis服务
5. **恢复**：系统自动恢复到异步模式

### 数据库故障

1. **检测**：健康检查发现数据库不可用
2. **告警**：立即通知（Critical级别）
3. **检查**：
   - 数据库服务状态
   - 连接配置
   - 网络连接
   - 数据库日志
4. **修复**：根据具体问题修复
5. **验证**：再次运行健康检查

---

## API响应时间

| 端点 | 预期响应时间 | 超时设置 |
|------|--------------|----------|
| /health/ | < 500ms | 5s |
| /health/redis/ | < 200ms | 2s |

如果响应时间超过预期，可能表明：
- 网络问题
- 系统负载过高
- 某个组件响应慢

---

## 安全注意事项

1. **权限控制**：
   - 仅管理员可访问
   - 不暴露敏感配置信息

2. **速率限制**：
   - 防止频繁调用
   - 建议间隔至少10秒

3. **日志审计**：
   - 记录所有健康检查请求
   - 监控异常访问模式
