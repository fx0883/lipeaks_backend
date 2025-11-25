# 统计和健康检查 API 详细文档

## 统计 API

### 获取反馈统计信息

#### 基本信息
- **端点**: `GET /api/v1/feedbacks/statistics/`
- **权限**: 需要管理员权限

#### 请求参数 (Query Parameters)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| software | integer | 否 | 按软件 ID 过滤 |
| date_from | date | 否 | 开始日期 (YYYY-MM-DD) |
| date_to | date | 否 | 结束日期 (YYYY-MM-DD) |

#### 响应格式

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "total_feedbacks": 2,
        "open_feedbacks": 2,
        "resolved_feedbacks": 0,
        "avg_resolution_time": null,
        "feedbacks_by_type": {
            "bug": 1,
            "feature": 1
        },
        "feedbacks_by_status": {
            "reviewing": 1,
            "submitted": 1
        },
        "feedbacks_by_priority": {
            "high": 1,
            "medium": 1
        },
        "top_voted_feedbacks": [
            {
                "id": 31,
                "title": "测试反馈001-已更新",
                "description": "更新后的描述内容",
                "feedback_type": "bug",
                "type_display": "Bug Report",
                "priority": "high",
                "priority_display": "High",
                "status": "reviewing",
                "status_display": "Reviewing",
                "application": 6,
                "application_name": "填色花园",
                "submitter": {
                    "id": 3,
                    "username": "admin_cms",
                    "email": "jackfeng8123@gmail.com"
                },
                "contact_email": "test@example.com",
                "vote_count": 0,
                "reply_count": 1,
                "created_at": "2025-11-25T05:25:29.394670Z",
                "updated_at": "2025-11-25T05:26:12.634417Z"
            }
        ],
        "recent_feedbacks": [
            {
                "id": 32,
                "title": "功能请求：添加深色模式",
                "description": "希望应用能够支持深色模式以保护眼睛",
                "feedback_type": "feature",
                "type_display": "Feature Request",
                "priority": "medium",
                "priority_display": "Medium",
                "status": "submitted",
                "status_display": "Submitted",
                "application": 6,
                "application_name": "填色花园",
                "submitter": {
                    "id": 3,
                    "username": "admin_cms",
                    "email": "jackfeng8123@gmail.com"
                },
                "contact_email": "jackfeng8123@gmail.com",
                "vote_count": 0,
                "reply_count": 0,
                "created_at": "2025-11-25T05:25:52.394016Z",
                "updated_at": "2025-11-25T05:25:52.394056Z"
            }
        ],
        "daily_trend": [
            {
                "date": "2025-11-25",
                "count": 2
            }
        ]
    }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| total_feedbacks | integer | 反馈总数 |
| open_feedbacks | integer | 未解决的反馈数（状态为 submitted, reviewing, confirmed, in_progress） |
| resolved_feedbacks | integer | 已解决的反馈数 |
| avg_resolution_time | string | 平均解决时间 |
| feedbacks_by_type | object | 按类型统计 |
| feedbacks_by_status | object | 按状态统计 |
| feedbacks_by_priority | object | 按优先级统计 |
| top_voted_feedbacks | array | 投票数最多的反馈（前10条） |
| recent_feedbacks | array | 最近的反馈（前10条） |
| daily_trend | array | 每日反馈趋势（过去30天） |

#### curl 示例

```bash
# 获取所有统计信息
curl -X GET "http://localhost:8000/api/v1/feedbacks/statistics/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 按日期范围过滤
curl -X GET "http://localhost:8000/api/v1/feedbacks/statistics/?date_from=2025-11-01&date_to=2025-11-30" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 按软件过滤
curl -X GET "http://localhost:8000/api/v1/feedbacks/statistics/?software=6" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 健康检查 API

### 1. 系统健康检查

#### 基本信息
- **端点**: `GET /api/v1/feedbacks/health/`
- **权限**: 需要管理员权限

#### 响应格式

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

#### 状态说明

| 状态 | 说明 |
|------|------|
| healthy | 所有组件正常 |
| degraded | 部分组件异常，但系统仍可运行 |
| unhealthy | 关键组件异常 |

#### 组件说明

| 组件 | 说明 |
|------|------|
| redis | Redis 连接状态 |
| database | 数据库连接状态 |
| celery | Celery 任务队列状态 |
| email | 邮件服务状态 |

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/health/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 2. Redis 状态检查

#### 基本信息
- **端点**: `GET /api/v1/feedbacks/health/redis/`
- **权限**: 需要管理员权限

#### 响应格式

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

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/health/redis/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 枚举值参考

### 反馈类型 (feedback_type)

| 值 | 显示名称 |
|----|----------|
| bug | Bug Report |
| feature | Feature Request |
| improvement | Improvement |
| question | Question |
| other | Other |

### 反馈状态 (status)

| 值 | 显示名称 | 说明 |
|----|----------|------|
| submitted | Submitted | 已提交 |
| reviewing | Reviewing | 审核中 |
| confirmed | Confirmed | 已确认 |
| in_progress | In Progress | 处理中 |
| resolved | Resolved | 已解决 |
| closed | Closed | 已关闭 |
| rejected | Rejected | 已拒绝 |
| duplicate | Duplicate | 重复 |

### 优先级 (priority)

| 值 | 显示名称 |
|----|----------|
| critical | Critical |
| high | High |
| medium | Medium |
| low | Low |

### 投票类型 (vote_type)

| 值 | 说明 |
|----|------|
| 1 | 赞成 (Upvote) |
| -1 | 反对 (Downvote) |

---

## 错误响应格式

### 通用错误格式

```json
{
    "success": false,
    "code": 4000,
    "message": "错误信息",
    "data": {}
}
```

### 常见错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| 4000 | 400 | 请求参数错误 |
| 4001 | 401 | 未授权/未认证 |
| 4003 | 403 | 权限不足 |
| 4004 | 404 | 资源不存在 |
| 5000 | 500 | 服务器内部错误 |
