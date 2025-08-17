# API 日志系统文档

## 概述

本文档详细介绍多租户系统的API日志功能，包括日志记录的内容、存储方式、查询方法以及如何利用日志进行系统监控和排错。该功能通过中间件自动记录所有API请求和响应，无需开发人员额外编写代码。

## 功能特点

- **全面的请求和响应记录**：自动记录HTTP请求和响应的完整信息
- **用户和租户关联**：将API调用与用户和租户关联，便于审计和分析
- **性能监控**：记录API响应时间，识别性能瓶颈
- **错误追踪**：详细记录异常信息，便于快速定位问题
- **搜索和过滤**：支持按多种条件搜索和过滤日志
- **数据可视化**：提供日志数据的可视化展示

## 实现方式

API日志功能通过以下组件实现：

1. **增强型API日志中间件**：`EnhancedAPILoggingMiddleware`
2. **API日志模型**：`APILog`存储日志数据
3. **日志查询API**：提供日志检索功能
4. **响应标准化中间件**：确保所有API响应格式一致

### 日志记录流程

```
HTTP请求 → TenantMiddleware → EnhancedAPILoggingMiddleware(开始记录)
        → 业务视图处理 → ResponseStandardizationMiddleware
        → EnhancedAPILoggingMiddleware(完成记录) → HTTP响应
```

## 日志内容

每条API日志包含以下信息：

| 字段 | 描述 | 示例 |
| ---- | ---- | ---- |
| id | 日志记录唯一标识 | 1 |
| timestamp | 请求时间戳 | 2025-04-24T12:30:45.123Z |
| user_id | 关联的用户ID | 5 |
| tenant_id | 关联的租户ID | 2 |
| request_method | HTTP请求方法 | GET |
| request_path | 请求路径 | /api/v1/users/ |
| view_name | 处理请求的视图名称 | users:user-list |
| status_code | HTTP状态码 | 200 |
| response_time | 响应时间(毫秒) | 125 |
| ip_address | 客户端IP地址 | 192.168.1.100 |
| user_agent | 用户代理信息 | Mozilla/5.0... |
| request_body | 请求体内容 | {"username": "test"} |
| query_params | 查询参数 | {"page": "1"} |
| response_body | 响应体内容 | {"success": true, ...} |
| error_message | 错误信息(如有) | null |

## 日志查询

### 管理员界面

管理员可以通过Django admin界面查看和搜索API日志：

1. 访问 `/admin/common/apilog/`
2. 使用过滤器按日期、用户、租户等条件筛选
3. 点击日志记录查看详情

### API接口

系统提供API接口用于编程方式查询日志：

#### 获取日志列表

```
GET /api/v1/logs/
```

支持的查询参数：

- `start_date`: 开始日期(YYYY-MM-DD)
- `end_date`: 结束日期(YYYY-MM-DD)
- `user_id`: 用户ID
- `tenant_id`: 租户ID
- `status_code`: HTTP状态码
- `min_response_time`: 最小响应时间(毫秒)
- `path`: 请求路径(支持模糊匹配)
- `method`: HTTP方法

响应示例：

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 253,
    "next": "http://example.com/api/v1/logs/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1001,
        "timestamp": "2025-04-24T12:30:45.123Z",
        "user": {
          "id": 5,
          "username": "admin"
        },
        "tenant": {
          "id": 2,
          "name": "测试租户"
        },
        "request_method": "GET",
        "request_path": "/api/v1/users/",
        "status_code": 200,
        "response_time": 125
      },
      // 更多日志记录...
    ]
  }
}
```

#### 获取日志详情

```
GET /api/v1/logs/{id}/
```

响应示例：

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 1001,
    "timestamp": "2025-04-24T12:30:45.123Z",
    "user": {
      "id": 5,
      "username": "admin"
    },
    "tenant": {
      "id": 2,
      "name": "测试租户"
    },
    "request_method": "GET",
    "request_path": "/api/v1/users/",
    "view_name": "users:user-list",
    "status_code": 200,
    "response_time": 125,
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "request_body": {"username": "test"},
    "query_params": {"page": "1"},
    "response_body": {"success": true, ...},
    "error_message": null
  }
}
```

## 日志统计分析

系统提供日志统计分析功能，帮助管理员监控API使用情况：

```
GET /api/v1/logs/stats/
```

支持的查询参数：

- `start_date`: 开始日期(YYYY-MM-DD)
- `end_date`: 结束日期(YYYY-MM-DD)
- `tenant_id`: 租户ID(可选)
- `interval`: 统计间隔(hour/day/week/month)

响应示例：

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "total_requests": 2845,
    "average_response_time": 187,
    "error_rate": 0.032,
    "top_endpoints": [
      {
        "path": "/api/v1/users/",
        "count": 532,
        "average_time": 143
      }
    ],
    "status_distribution": {
      "200": 2541,
      "401": 165,
      "404": 89,
      "500": 50
    },
    "time_series": [
      {
        "timestamp": "2025-04-23",
        "count": 1245,
        "average_time": 178
      },
      {
        "timestamp": "2025-04-24",
        "count": 1600,
        "average_time": 195
      }
    ]
  }
}
```

## 最佳实践

### 性能考虑

1. **日志轮换**：定期归档和清理旧日志，防止数据库过大
2. **选择性记录**：配置哪些路径需要详细记录，哪些可以简化
3. **异步处理**：使用异步任务处理日志写入，避免影响API响应时间

### 隐私和安全

1. **敏感信息过滤**：自动屏蔽密码、令牌等敏感字段
2. **数据访问控制**：严格控制日志查询API的访问权限
3. **合规性考虑**：确保日志记录符合相关数据保护法规

### 排错指南

1. **常见错误模式**：关注状态码4xx和5xx的请求
2. **慢请求分析**：定期检查响应时间超过1秒的请求
3. **异常堆栈**：查看日志中的异常堆栈信息快速定位问题

## 配置选项

API日志系统可通过Django设置进行配置：

```python
# settings.py

# API日志配置
API_LOGGING = {
    # 是否记录请求体
    'LOG_REQUEST_BODY': True,
    
    # 是否记录响应体
    'LOG_RESPONSE_BODY': True,
    
    # 慢请求阈值(毫秒)
    'SLOW_REQUEST_THRESHOLD': 1000,
    
    # 日志保留天数
    'LOG_RETENTION_DAYS': 30,
    
    # 排除的路径
    'EXCLUDE_PATHS': [
        '/api/v1/health/',
        '/api/v1/docs/'
    ],
    
    # 敏感字段(将被屏蔽)
    'SENSITIVE_FIELDS': [
        'password',
        'token',
        'secret'
    ]
}
```

## 未来计划

API日志系统的未来发展计划：

1. 添加实时告警功能，当出现异常时自动通知管理员
2. 集成机器学习技术，实现异常检测和自动分类
3. 增强数据可视化，提供更直观的日志分析工具
4. 支持导出日志数据为常见格式(CSV, JSON)

## 常见问题

### Q: API日志会影响系统性能吗？

A: 日志记录会略微增加系统负载，但我们通过异步处理和选择性记录等优化手段将影响降到最低。对于高流量系统，可以配置仅记录关键路径或错误请求。

### Q: 如何防止日志数据过度增长？

A: 系统默认配置了日志轮换策略，定期清理30天前的日志数据。管理员可以根据系统需求调整保留时间。

### Q: 如何确保敏感信息不被记录？

A: 中间件内置了敏感字段过滤功能，会自动屏蔽密码、令牌等敏感信息。管理员可以配置额外的敏感字段列表。
