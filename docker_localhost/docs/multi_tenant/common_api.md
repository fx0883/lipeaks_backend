# 通用 API

本文档描述系统中的通用API接口，如API日志查询等功能。

## 基础路径

所有通用API的基础路径为: `/api/v1/common/`

## 接口列表

### 1. 获取API日志列表

获取系统API调用日志列表，支持分页、排序和筛选。

- **URL**: `/api/v1/common/api-logs/`
- **方法**: `GET`
- **认证要求**: 需要认证（Bearer Token）
- **权限要求**: 超级管理员

#### 请求参数（Query String）

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| page | integer | 否 | 页码，默认为1 | 1 |
| page_size | integer | 否 | 每页记录数，默认为10 | 10 |
| search | string | 否 | 搜索关键词（用户名、IP、请求路径） | "login" |
| ordering | string | 否 | 排序字段，前缀'-'表示降序 | "-created_at" |
| user | integer | 否 | 筛选指定用户的日志 | 123 |
| method | string | 否 | 筛选指定HTTP方法的日志 | "POST" |
| status_code | integer | 否 | 筛选指定状态码的日志 | 200 |
| start_date | string | 否 | 起始日期，格式YYYY-MM-DD | "2025-04-01" |
| end_date | string | 否 | 结束日期，格式YYYY-MM-DD | "2025-04-22" |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 1000,
    "next": "http://example.com/api/v1/common/api-logs/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "user": {
          "id": 123,
          "username": "john_doe"
        },
        "ip_address": "192.168.1.1",
        "method": "POST",
        "path": "/api/v1/auth/login/",
        "query_params": {},
        "request_data": {
          "username": "john_doe",
          "password": "********"  // 密码会被脱敏
        },
        "status_code": 200,
        "response_data": {
          "success": true,
          "message": "登录成功",
          "data": {
            "token": "********",  // 敏感数据会被脱敏
            "user": {
              "id": 123,
              "username": "john_doe"
            }
          }
        },
        "execution_time": 235,  // 毫秒
        "created_at": "2025-04-22T10:05:23Z"
      },
      // 更多日志...
    ]
  }
}
```

### 2. 获取API日志详情

获取指定API日志的详细信息。

- **URL**: `/api/v1/common/api-logs/{id}/`
- **方法**: `GET`
- **认证要求**: 需要认证（Bearer Token）
- **权限要求**: 超级管理员

#### 路径参数

| 参数名 | 类型 | 描述 | 示例 |
|-------|------|------|------|
| id | integer | API日志ID | 1 |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 1,
    "user": {
      "id": 123,
      "username": "john_doe",
      "email": "john@example.com"
    },
    "ip_address": "192.168.1.1",
    "method": "POST",
    "path": "/api/v1/auth/login/",
    "query_params": {},
    "headers": {
      "User-Agent": "Mozilla/5.0...",
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    "request_data": {
      "username": "john_doe",
      "password": "********"  // 密码会被脱敏
    },
    "status_code": 200,
    "response_data": {
      "success": true,
      "code": 2000,
      "message": "登录成功",
      "data": {
        "token": "********",  // 敏感数据会被脱敏
        "refresh_token": "********",  // 敏感数据会被脱敏
        "user": {
          "id": 123,
          "username": "john_doe",
          "email": "john@example.com",
          "nick_name": "John",
          "is_admin": false,
          "is_super_admin": false,
          "avatar": "",
          "tenant_id": 1,
          "tenant_name": "Company A"
        }
      }
    },
    "execution_time": 235,  // 毫秒
    "created_at": "2025-04-22T10:05:23Z"
  }
}
```

#### 错误响应 (404 Not Found)

```json
{
  "success": false,
  "code": 4004,
  "message": "日志不存在",
  "data": null
}
```

## API日志说明

API日志记录了系统中所有API请求的详细信息，包括：

- 请求用户
- IP地址
- HTTP方法
- 请求路径
- 查询参数
- 请求头
- 请求数据
- 响应状态码
- 响应数据
- 执行时间
- 创建时间

API日志可用于：

- 系统监控和优化
- 安全审计
- 问题诊断和调试
- 用户行为分析

注意：出于安全考虑，敏感信息（如密码、令牌等）会在API日志中被脱敏处理，显示为"********"。 