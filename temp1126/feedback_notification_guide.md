# 反馈通知配置指南

## 概述

反馈通知功能允许租户管理员为每个应用配置邮件通知，当用户提交新反馈时，系统会自动向配置的接收者列表发送通知邮件。

## 功能特点

- **应用级别配置**：每个应用可以独立配置通知
- **多接收者支持**：每个应用可配置多个邮件接收者
- **灵活开关控制**：支持全局启用/禁用，也支持单个接收者的启用/禁用
- **异步发送**：使用线程池 + Celery 队列，不影响用户提交体验
- **邮件日志**：所有发送记录都会保存在 `FeedbackEmailLog` 中

## 配置方式

### 方式一：Admin 后台配置

1. 登录 Django Admin 后台
2. 进入 **Feedbacks > 反馈通知配置**
3. 点击 **添加反馈通知配置**
4. 选择应用并启用通知
5. 在内联表单中添加接收者邮箱

### 方式二：API 配置（推荐）

API 仅限租户管理员访问，需要携带有效的 JWT Token 和 X-Tenant-ID Header。

---

## API 接口文档

### 基础信息

- **Base URL**: `/api/v1/feedbacks/notification-configs/`
- **认证方式**: JWT Token (Bearer)
- **权限要求**: 仅限租户管理员
- **必需 Header**: 
  - `Authorization: Bearer <token>`
  - `X-Tenant-ID: <tenant_id>`

---

### 1. 获取通知配置列表

```http
GET /api/v1/feedbacks/notification-configs/
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "application": 6,
      "application_name": "CompressX",
      "application_code": "compressx",
      "is_enabled": true,
      "recipients": [
        {
          "id": 1,
          "email": "dev@example.com",
          "name": "开发团队",
          "is_active": true,
          "created_at": "2025-11-26T10:00:00Z"
        }
      ],
      "recipient_count": 1,
      "active_recipient_count": 1,
      "created_at": "2025-11-26T10:00:00Z",
      "updated_at": "2025-11-26T10:00:00Z"
    }
  ]
}
```

**curl 示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/notification-configs/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3"
```

---

### 2. 创建通知配置

```http
POST /api/v1/feedbacks/notification-configs/
```

**请求体**:
```json
{
  "application": 6,
  "is_enabled": true
}
```

**curl 示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/notification-configs/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"application": 6, "is_enabled": true}'
```

---

### 3. 获取配置详情

```http
GET /api/v1/feedbacks/notification-configs/{id}/
```

**curl 示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/notification-configs/1/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3"
```

---

### 4. 更新配置（启用/禁用通知）

```http
PATCH /api/v1/feedbacks/notification-configs/{id}/
```

**请求体**:
```json
{
  "is_enabled": false
}
```

**curl 示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/notification-configs/1/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": false}'
```

---

### 5. 删除配置

```http
DELETE /api/v1/feedbacks/notification-configs/{id}/
```

**curl 示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/notification-configs/1/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3"
```

---

### 6. 获取接收者列表

```http
GET /api/v1/feedbacks/notification-configs/{id}/recipients/
```

**curl 示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/notification-configs/1/recipients/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3"
```

---

### 7. 添加接收者

```http
POST /api/v1/feedbacks/notification-configs/{id}/recipients/add/
```

**请求体**:
```json
{
  "email": "notify@example.com",
  "name": "通知接收人",
  "is_active": true
}
```

**curl 示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/notification-configs/1/recipients/add/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"email": "notify@example.com", "name": "通知接收人", "is_active": true}'
```

---

### 8. 更新接收者

```http
PATCH /api/v1/feedbacks/notification-configs/{id}/recipients/{recipient_id}/update/
```

**请求体**:
```json
{
  "name": "新名称",
  "is_active": false
}
```

**curl 示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/notification-configs/1/recipients/1/update/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

---

### 9. 删除接收者

```http
DELETE /api/v1/feedbacks/notification-configs/{id}/recipients/{recipient_id}/
```

**curl 示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/notification-configs/1/recipients/1/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3"
```

---

### 10. 发送测试邮件

```http
POST /api/v1/feedbacks/notification-configs/{id}/test/
```

**请求体**:
```json
{
  "email": "test@example.com"
}
```

**curl 示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/notification-configs/1/test/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

---

### 11. 按应用查询配置

```http
GET /api/v1/feedbacks/notification-configs/by-application/{application_id}/
```

**curl 示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/notification-configs/by-application/6/" \
  -H "Authorization: Bearer <your_token>" \
  -H "X-Tenant-ID: 3"
```

---

## 邮件模板配置

### 默认模板

系统内置了默认的新反馈通知邮件模板，包含以下信息：
- 应用名称
- 反馈标题
- 反馈类型和优先级
- 提交者信息
- 提交时间
- 反馈内容摘要
- 查看详情链接

### 自定义模板

可以通过 Admin 后台或 API 创建自定义邮件模板：

1. 进入 **Feedbacks > Email Templates**
2. 创建新模板，选择类型为 **New Feedback Notification**
3. 使用以下变量自定义内容：

| 变量名 | 说明 |
|--------|------|
| `{application_name}` | 应用名称 |
| `{feedback_title}` | 反馈标题 |
| `{feedback_description}` | 反馈描述（最多500字符） |
| `{feedback_type}` | 反馈类型（如 Bug 报告、功能请求） |
| `{priority}` | 优先级（如 紧急、高、中、低） |
| `{contact_name}` | 提交者姓名 |
| `{contact_email}` | 提交者邮箱 |
| `{submitted_at}` | 提交时间 |
| `{feedback_id}` | 反馈 ID |
| `{view_url}` | 查看详情链接 |

### 模板示例

**邮件标题**:
```
[{application_name}] 新反馈: {feedback_title}
```

**邮件正文 (HTML)**:
```html
<h2>新反馈通知</h2>
<p><strong>{application_name}</strong> 收到了一条新的用户反馈：</p>
<ul>
  <li><strong>标题：</strong>{feedback_title}</li>
  <li><strong>类型：</strong>{feedback_type}</li>
  <li><strong>优先级：</strong>{priority}</li>
  <li><strong>提交者：</strong>{contact_name} ({contact_email})</li>
</ul>
<p><strong>内容：</strong></p>
<p>{feedback_description}</p>
<p><a href="{view_url}">点击查看详情</a></p>
```

---

## 前端集成指南

### 配置页面集成

前端可以提供一个通知配置管理页面，包含：

1. **配置列表**：显示所有应用的通知配置状态
2. **启用/禁用开关**：快速切换通知状态
3. **接收者管理**：添加、编辑、删除接收者
4. **测试功能**：发送测试邮件验证配置

### React 示例代码

```jsx
import { useState, useEffect } from 'react';

function NotificationConfigPage({ applicationId }) {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConfig();
  }, [applicationId]);

  const fetchConfig = async () => {
    try {
      const response = await fetch(
        `/api/v1/feedbacks/notification-configs/by-application/${applicationId}/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': tenantId
          }
        }
      );
      if (response.ok) {
        const data = await response.json();
        setConfig(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch config:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleEnabled = async () => {
    await fetch(`/api/v1/feedbacks/notification-configs/${config.id}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': tenantId,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ is_enabled: !config.is_enabled })
    });
    fetchConfig();
  };

  const addRecipient = async (email, name) => {
    await fetch(`/api/v1/feedbacks/notification-configs/${config.id}/recipients/add/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': tenantId,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, name, is_active: true })
    });
    fetchConfig();
  };

  // ... 渲染逻辑
}
```

---

## 技术架构

### 执行流程

```
用户提交反馈
     │
     ▼
FeedbackSubmitPageView.form_valid()
     │
     ├─ 创建 Feedback 记录
     │
     └─ EmailService.send_new_feedback_notification(feedback)
          │
          ├─ 检查 Application 是否有 NotificationConfig
          │
          └─ 提交到 EmailThreadPoolManager
               │
               ▼
          _process_new_feedback_notification() [后台线程]
               │
               ▼
          TaskExecutor.execute_task(send_new_feedback_notification)
               │
               ├─ Celery 可用 → 异步任务
               │
               └─ Celery 不可用 → 同步执行
                    │
                    ▼
               遍历接收者发送邮件
               记录 FeedbackEmailLog
```

### 相关文件

| 文件 | 说明 |
|------|------|
| `feedbacks/models.py` | 模型定义 |
| `feedbacks/serializers.py` | 序列化器 |
| `feedbacks/views/notification_config_views.py` | API ViewSet |
| `feedbacks/tasks.py` | Celery 任务 |
| `feedbacks/services.py` | 服务层逻辑 |
| `feedbacks/admin.py` | Admin 配置 |

---

## 常见问题

### Q: 为什么配置了通知但没有收到邮件？

A: 请检查以下几点：
1. 通知配置的 `is_enabled` 是否为 `true`
2. 接收者的 `is_active` 是否为 `true`
3. 邮件地址是否正确
4. SMTP 邮件服务是否正常（检查 `EMAIL_*` 环境变量配置）
5. 查看 `FeedbackEmailLog` 表中的发送记录和错误信息

### Q: 如何查看邮件发送日志？

A: 
1. Admin 后台：**Feedbacks > Feedback Email Logs**
2. 数据库：查询 `feedback_email_log` 表
3. 日志文件：查看应用日志中的 `feedbacks.tasks` 相关记录

### Q: 支持哪些邮箱服务？

A: 支持任何标准 SMTP 服务，项目默认配置了 QQ 邮箱。可通过以下环境变量配置：
- `EMAIL_HOST_USER`: SMTP 账号
- `EMAIL_HOST_PASSWORD`: SMTP 密码/授权码
- `DEFAULT_FROM_EMAIL`: 发件人地址

### Q: 可以按反馈类型或优先级过滤通知吗？

A: 当前版本暂不支持，所有新反馈都会触发通知。如需此功能，可在后续版本中扩展 `FeedbackNotificationConfig` 模型，添加过滤条件字段。
