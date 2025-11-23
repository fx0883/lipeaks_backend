# 反馈管理 API 文档

## 概述

反馈管理API提供了反馈的完整生命周期管理功能，包括创建、查询、更新、删除以及状态管理。

---

## 1. 获取反馈列表

### 基本信息
- **接口**: `GET /api/v1/feedbacks/feedbacks/`
- **权限**: 需要认证
- **说明**: 
  - 租户管理员可查看本租户所有反馈
  - 普通用户只能查看自己提交的反馈
  - 超级管理员可查看所有反馈

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| software | int | 否 | 按应用ID过滤 | 1 |
| feedback_type | string | 否 | 反馈类型 | bug, feature, improvement, question, other |
| status | string | 否 | 状态 | submitted, reviewing, confirmed, in_progress, resolved, closed, rejected, duplicate |
| priority | string | 否 | 优先级 | critical, high, medium, low |
| email_verified | boolean | 否 | 邮箱验证状态 | true, false |
| search | string | 否 | 搜索标题、描述、邮箱 | 关键词 |
| ordering | string | 否 | 排序字段 | -created_at, vote_count, -vote_count |

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": [
        {
            "id": 1,
            "title": "登录页面无法访问",
            "description": "点击登录按钮后页面无响应",
            "feedback_type": "bug",
            "type_display": "Bug Report",
            "priority": "high",
            "priority_display": "High",
            "status": "reviewing",
            "status_display": "Reviewing",
            "application": 1,
            "submitter": {
                "id": 3,
                "username": "admin_cms",
                "email": "admin@example.com"
            },
            "contact_email": "admin@example.com",
            "vote_count": 5,
            "reply_count": 3,
            "created_at": "2025-11-23T10:00:00Z",
            "updated_at": "2025-11-23T12:00:00Z"
        }
    ]
}
```

### curl 示例

```bash
# 获取所有反馈
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 按类型过滤
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/?feedback_type=bug&priority=high" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 搜索反馈
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/?search=登录" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 排序
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/?ordering=-vote_count" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 2. 创建反馈

### 基本信息
- **接口**: `POST /api/v1/feedbacks/feedbacks/`
- **权限**: 需要认证（任何登录用户都可提交）
- **说明**: 提交新的反馈，系统会自动关联到当前用户和租户

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| title | string | 是 | 反馈标题（最多200字符） | "登录问题" |
| description | string | 是 | 详细描述 | "无法登录系统" |
| feedback_type | string | 是 | 反馈类型 | bug, feature, improvement, question, other |
| priority | string | 否 | 优先级（默认medium） | critical, high, medium, low |
| application | int | 否 | 关联的应用ID | 1 |
| contact_email | string | 否 | 联系邮箱（默认使用用户邮箱） | user@example.com |
| contact_name | string | 否 | 联系人姓名 | "张三" |
| environment_info | object | 否 | 环境信息 | {"os": "Windows 10", "browser": "Chrome"} |

### 请求示例

```json
{
    "title": "页面加载缓慢",
    "description": "首页加载时间超过10秒，影响用户体验",
    "feedback_type": "bug",
    "priority": "high",
    "application": 1,
    "environment_info": {
        "os": "Windows 10",
        "browser": "Chrome 119",
        "screen": "1920x1080"
    }
}
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 27,
        "title": "页面加载缓慢",
        "description": "首页加载时间超过10秒，影响用户体验",
        "feedback_type": "bug",
        "priority": "high",
        "status": "submitted",
        "application": 1,
        "user": 3,
        "user_info": {
            "id": 3,
            "username": "admin_cms",
            "email": "admin@example.com",
            "is_registered": true
        },
        "contact_email": "admin@example.com",
        "contact_name": "admin_cms",
        "email_verified": false,
        "email_notification_enabled": true,
        "environment_info": {
            "os": "Windows 10",
            "browser": "Chrome 119",
            "screen": "1920x1080"
        },
        "ip_address": "127.0.0.1",
        "user_agent": "curl/8.7.1",
        "vote_count": 0,
        "reply_count": 0,
        "attachments": [],
        "replies": [],
        "status_history": [],
        "user_vote": null,
        "created_at": "2025-11-23T13:43:59Z",
        "updated_at": "2025-11-23T13:43:59Z"
    }
}
```

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "页面加载缓慢",
    "description": "首页加载时间超过10秒",
    "feedback_type": "bug",
    "priority": "high"
  }'
```

---

## 3. 获取反馈详情

### 基本信息
- **接口**: `GET /api/v1/feedbacks/feedbacks/{id}/`
- **权限**: 需要认证
- **说明**: 获取指定反馈的详细信息，会自动增加浏览次数

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 反馈ID |

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 27,
        "title": "页面加载缓慢",
        "description": "首页加载时间超过10秒",
        "feedback_type": "bug",
        "priority": "high",
        "status": "submitted",
        "application": 1,
        "user": 3,
        "user_info": {
            "id": 3,
            "username": "admin_cms",
            "email": "admin@example.com",
            "is_registered": true
        },
        "contact_email": "admin@example.com",
        "email_verified": false,
        "email_notification_enabled": true,
        "view_count": 1,
        "vote_count": 0,
        "reply_count": 0,
        "attachments": [],
        "replies": [],
        "status_history": [],
        "user_vote": null,
        "created_at": "2025-11-23T13:43:59Z",
        "updated_at": "2025-11-23T13:43:59Z"
    }
}
```

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/27/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 4. 更新反馈（完整更新）

### 基本信息
- **接口**: `PUT /api/v1/feedbacks/feedbacks/{id}/`
- **权限**: 需要认证，只能更新自己提交的反馈
- **说明**: 完整更新反馈信息，需要提供所有字段

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 反馈ID |

### 请求参数

与创建反馈相同，但所有字段都需要提供。

### curl 示例

```bash
curl -X PUT "http://localhost:8000/api/v1/feedbacks/feedbacks/27/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "页面加载缓慢（已更新）",
    "description": "首页加载时间超过10秒，影响用户体验",
    "feedback_type": "bug",
    "priority": "critical"
  }'
```

---

## 5. 更新反馈（部分更新）

### 基本信息
- **接口**: `PATCH /api/v1/feedbacks/feedbacks/{id}/`
- **权限**: 需要认证，只能更新自己提交的反馈
- **说明**: 部分更新反馈信息，只需提供要更新的字段

### curl 示例

```bash
# 只更新标题
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "新标题"
  }'

# 只更新优先级
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "priority": "critical"
  }'
```

---

## 6. 删除反馈

### 基本信息
- **接口**: `DELETE /api/v1/feedbacks/feedbacks/{id}/`
- **权限**: 需要认证，管理员或反馈创建者
- **说明**: 软删除反馈（标记为已删除，不真正删除数据）

### 响应

成功返回 HTTP 204 No Content

### curl 示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/feedbacks/27/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 7. 更改反馈状态

### 基本信息
- **接口**: `PATCH /api/v1/feedbacks/feedbacks/{id}/status/`
- **权限**: 仅管理员
- **说明**: 更改反馈状态，会自动创建状态历史记录

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 可选值 |
|------|------|------|------|--------|
| status | string | 是 | 新状态 | submitted, reviewing, confirmed, in_progress, resolved, closed, rejected, duplicate |
| reason | string | 否 | 状态变更原因 | 任意文本 |

### 请求示例

```json
{
    "status": "reviewing",
    "reason": "已分配给开发团队处理"
}
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 27,
        "title": "页面加载缓慢",
        "status": "reviewing",
        "status_history": [
            {
                "id": 2,
                "feedback": 27,
                "from_status": "submitted",
                "to_status": "reviewing",
                "from_status_display": "Submitted",
                "to_status_display": "Reviewing",
                "changed_by": 3,
                "changed_by_name": "admin_cms",
                "reason": "已分配给开发团队处理",
                "created_at": "2025-11-23T13:44:29Z"
            }
        ]
    }
}
```

### curl 示例

```bash
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/status/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "reviewing",
    "reason": "已分配给开发团队处理"
  }'
```

---

## 8. 验证反馈邮箱

### 基本信息
- **接口**: `POST /api/v1/feedbacks/feedbacks/{id}/verify-email/`
- **权限**: 不需要认证（用于匿名用户验证邮箱）
- **说明**: 验证反馈提交者的邮箱地址

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 是 | 邮箱验证令牌 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/verify-email/" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "abc123def456"
  }'
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "detail": "Email verified successfully."
    }
}
```

---

## 9. 切换通知设置

### 基本信息
- **接口**: `PATCH /api/v1/feedbacks/feedbacks/{id}/notifications/`
- **权限**: 需要认证，仅反馈创建者
- **说明**: 切换反馈的邮件通知开关

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 27,
        "email_notification_enabled": false
    }
}
```

### curl 示例

```bash
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/notifications/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 状态说明

### 反馈类型 (feedback_type)
- `bug` - Bug报告
- `feature` - 功能请求
- `improvement` - 改进建议
- `question` - 问题咨询
- `other` - 其他

### 优先级 (priority)
- `critical` - 严重
- `high` - 高
- `medium` - 中
- `low` - 低

### 状态 (status)
- `submitted` - 已提交
- `reviewing` - 审核中
- `confirmed` - 已确认
- `in_progress` - 处理中
- `resolved` - 已解决
- `closed` - 已关闭
- `rejected` - 已拒绝
- `duplicate` - 重复

---

## 错误码

| 错误码 | 说明 |
|--------|------|
| 4000 | 请求参数错误 |
| 4010 | 未认证 |
| 4030 | 权限不足 |
| 4040 | 资源不存在 |
| 5000 | 服务器内部错误 |
