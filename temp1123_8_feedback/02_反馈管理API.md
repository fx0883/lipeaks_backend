# 反馈管理 API 详细文档

## 1. 获取反馈列表

### 基本信息
- **端点**: `GET /api/v1/feedbacks/feedbacks/`
- **权限**: 需要认证，租户管理员可查看所有反馈，普通用户只能查看自己的反馈

### 请求参数 (Query Parameters)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| application | integer | 否 | 按应用 ID 过滤 |
| feedback_type | string | 否 | 按反馈类型过滤：bug, feature, improvement, question, other |
| status | string | 否 | 按状态过滤：submitted, reviewing, confirmed, in_progress, resolved, closed, rejected, duplicate |
| priority | string | 否 | 按优先级过滤：critical, high, medium, low |
| email_verified | boolean | 否 | 按邮箱验证状态过滤 |
| search | string | 否 | 搜索标题、描述、邮箱 |
| ordering | string | 否 | 排序字段，如：-created_at, vote_count |

### 响应格式

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": [
        {
            "id": 31,
            "title": "测试反馈001",
            "description": "这是一个测试反馈的描述内容",
            "feedback_type": "bug",
            "type_display": "Bug Report",
            "priority": "high",
            "priority_display": "High",
            "status": "submitted",
            "status_display": "Submitted",
            "application": 6,
            "application_name": "填色花园",
            "submitter": {
                "id": 3,
                "username": "admin_cms",
                "email": "jackfeng8123@gmail.com"
            },
            "contact_email": "test@example.com",
            "vote_count": 0,
            "reply_count": 0,
            "created_at": "2025-11-25T05:25:29.394670Z",
            "updated_at": "2025-11-25T05:25:29.394686Z"
        }
    ]
}
```

### curl 示例

```bash
# 获取所有反馈
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 按应用过滤
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/?application=6" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 按类型和状态过滤
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/?feedback_type=bug&status=submitted" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 搜索反馈
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/?search=测试" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 分页和排序
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/?page=1&page_size=20&ordering=-created_at" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 2. 提交反馈

### 基本信息
- **端点**: `POST /api/v1/feedbacks/feedbacks/`
- **权限**: 允许匿名提交，但匿名用户必须提供邮箱

### 请求参数 (JSON Body)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 反馈标题，最大 200 字符 |
| description | string | 是 | 反馈详细描述 |
| feedback_type | string | 否 | 反馈类型：bug(默认), feature, improvement, question, other |
| priority | string | 否 | 优先级：critical, high, medium(默认), low |
| application | integer | 否 | 关联的应用 ID |
| contact_email | string | 否 | 联系邮箱（匿名用户必填） |
| contact_name | string | 否 | 联系人姓名 |
| environment_info | object | 否 | 环境信息（JSON 格式） |

### 响应格式

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 31,
        "title": "测试反馈001",
        "description": "这是一个测试反馈的描述内容",
        "feedback_type": "bug",
        "priority": "high",
        "status": "submitted",
        "application": {
            "id": 6,
            "name": "填色花园",
            "code": "test-create-app",
            "description": "填色花园",
            "logo": null,
            "current_version": "1.0.0",
            "status": "development",
            "is_active": true,
            "created_at": "2025-11-23T13:20:58.551182Z",
            "updated_at": "2025-11-24T11:34:18.587693Z"
        },
        "user": 3,
        "user_info": {
            "id": 3,
            "username": "admin_cms",
            "email": "jackfeng8123@gmail.com",
            "is_registered": true
        },
        "contact_email": "test@example.com",
        "contact_name": "测试用户",
        "email_verified": false,
        "email_notification_enabled": true,
        "environment_info": {},
        "ip_address": "127.0.0.1",
        "user_agent": "curl/8.7.1",
        "assigned_to": null,
        "resolved_at": null,
        "resolution_notes": null,
        "view_count": 0,
        "vote_count": 0,
        "reply_count": 0,
        "attachments": [],
        "replies": [],
        "status_history": [],
        "user_vote": null,
        "created_at": "2025-11-25T05:25:29.394670Z",
        "updated_at": "2025-11-25T05:25:29.394686Z"
    }
}
```

### curl 示例

```bash
# 提交 Bug 反馈
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试反馈001",
    "description": "这是一个测试反馈的描述内容",
    "feedback_type": "bug",
    "priority": "high",
    "application": 6,
    "contact_email": "test@example.com",
    "contact_name": "测试用户"
  }'

# 提交功能请求
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "功能请求：添加深色模式",
    "description": "希望应用能够支持深色模式以保护眼睛",
    "feedback_type": "feature",
    "priority": "medium",
    "application": 6
  }'
```

---

## 3. 获取反馈详情

### 基本信息
- **端点**: `GET /api/v1/feedbacks/feedbacks/{id}/`
- **权限**: 允许匿名访问

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 反馈 ID |

### 响应格式

同"提交反馈"的响应格式，包含完整的反馈详情、附件、回复和状态历史。

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/31/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 4. 更新反馈

### 基本信息
- **端点 (完整更新)**: `PUT /api/v1/feedbacks/feedbacks/{id}/`
- **端点 (部分更新)**: `PATCH /api/v1/feedbacks/feedbacks/{id}/`
- **权限**: 需要认证

### 请求参数 (JSON Body)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | PUT必填 | 反馈标题 |
| description | string | PUT必填 | 反馈详细描述 |
| priority | string | 否 | 优先级 |
| status | string | 否 | 状态（有状态转换限制） |
| assigned_to | integer | 否 | 分配给的用户 ID |
| resolution_notes | string | 否 | 解决备注 |
| email_notification_enabled | boolean | 否 | 是否启用邮件通知 |

### curl 示例

```bash
# 完整更新
curl -X PUT "http://localhost:8000/api/v1/feedbacks/feedbacks/31/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试反馈001-已更新",
    "description": "更新后的描述内容",
    "priority": "critical"
  }'

# 部分更新
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/31/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"priority": "high"}'
```

---

## 5. 删除反馈

### 基本信息
- **端点**: `DELETE /api/v1/feedbacks/feedbacks/{id}/`
- **权限**: 需要认证
- **说明**: 软删除，数据不会真正删除

### 响应

成功时返回 HTTP 204 No Content。

### curl 示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/feedbacks/31/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 6. 更改反馈状态

### 基本信息
- **端点**: `PATCH /api/v1/feedbacks/feedbacks/{id}/status/`
- **权限**: 需要管理员权限

### 请求参数 (JSON Body)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 新状态 |
| reason | string | 否 | 状态变更原因 |

### 状态转换规则

| 当前状态 | 可转换为 |
|----------|----------|
| submitted | reviewing, rejected, duplicate |
| reviewing | confirmed, rejected, duplicate |
| confirmed | in_progress, rejected, duplicate |
| in_progress | resolved, rejected |
| resolved | closed, in_progress |
| closed | submitted |
| rejected | submitted |
| duplicate | submitted |

### curl 示例

```bash
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/31/status/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "reviewing", "reason": "开始审核此反馈"}'
```

---

## 7. 切换通知设置

### 基本信息
- **端点**: `PATCH /api/v1/feedbacks/feedbacks/{id}/notifications/`
- **权限**: 需要认证，只有反馈创建者可以操作

### 说明
每次调用会切换 `email_notification_enabled` 的状态（true ↔ false）。

### curl 示例

```bash
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/31/notifications/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 8. 验证邮箱

### 基本信息
- **端点**: `POST /api/v1/feedbacks/feedbacks/{id}/verify-email/`
- **权限**: 允许匿名访问

### 请求参数 (JSON Body)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 是 | 邮箱验证令牌 |

### curl 示例

```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/31/verify-email/" \
  -H "Content-Type: application/json" \
  -d '{"token": "your_verification_token"}'
```

---

## 9. 投票

### 基本信息
- **端点 (投票)**: `POST /api/v1/feedbacks/feedbacks/{id}/vote/`
- **端点 (移除投票)**: `DELETE /api/v1/feedbacks/feedbacks/{id}/vote/`
- **权限**: 需要认证

### 请求参数 (POST - JSON Body)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| vote_type | integer | 是 | 投票类型：1 (赞成) 或 -1 (反对) |

### 响应格式 (POST)

```json
{
    "success": true,
    "code": 2000,
    "message": "Vote recorded",
    "data": {
        "message": "Vote recorded",
        "vote_type": 1,
        "total_votes": 1
    }
}
```

### curl 示例

```bash
# 投赞成票
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/31/vote/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": 1}'

# 投反对票
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/31/vote/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": -1}'

# 移除投票
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/feedbacks/31/vote/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
