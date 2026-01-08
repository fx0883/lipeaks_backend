# 通知系统 Admin API 文档

本文档详细说明了通知系统管理端的所有API接口，包括通知的创建、查询、发布、归档、接收者管理和统计等功能。

---

## 通用说明

### 基础URL
```
http://localhost:8000/api/v1/admin/notifications/
```

### 认证方式
大多数写操作需要JWT认证，请在Header中添加：
```
Authorization: Bearer {JWT_TOKEN}
```

### 租户ID
多租户环境下，需要在Header中指定租户ID：
```
X-Tenant-ID: {TENANT_ID}
```

**注意**: 
- GET请求允许匿名访问（需要租户ID，通过 X-Tenant-ID header）
- POST/PATCH/DELETE 需要认证 + 租户管理员权限

### 响应格式
所有响应遵循标准格式：
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": { ... }
}
```

### 错误码说明
- 2xxx: 成功
- 4000: 请求参数错误
- 4001: 未认证
- 4003: 权限不足
- 4004: 资源不存在
- 5000: 服务器内部错误

---

## 一、通知管理 API

### 1.1 获取通知列表

**接口**: `GET /api/v1/admin/notifications/`

**权限**: GET请求允许匿名访问（需要X-Tenant-ID header）

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| application | int | 否 | 关联应用ID |
| scope | string | 否 | 通知范围：tenant, application, members |
| status | string | 否 | 状态：draft, published, archived |
| type | string | 否 | 类型：info, warning, error, update, announcement |
| priority | string | 否 | 优先级：low, normal, high, urgent |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认10 |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/admin/notifications/?status=published&page=1&page_size=10" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 25,
    "next": "http://localhost:8000/api/v1/admin/notifications/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "title": "系统维护通知",
        "scope": "tenant",
        "scope_display": "面向租户",
        "application": null,
        "application_name": null,
        "notification_type": "info",
        "type_display": "信息通知",
        "priority": "normal",
        "priority_display": "普通",
        "status": "published",
        "status_display": "已发布",
        "send_email": false,
        "email_sent_at": null,
        "published_at": "2024-01-08T10:00:00Z",
        "created_by": 1,
        "created_by_name": "admin",
        "recipient_count": 150,
        "read_count": 80,
        "created_at": "2024-01-08T09:30:00Z",
        "updated_at": "2024-01-08T10:00:00Z"
      },
      {
        "id": 2,
        "title": "新功能发布",
        "scope": "application",
        "scope_display": "面向应用",
        "application": 5,
        "application_name": "博客系统",
        "notification_type": "update",
        "type_display": "更新通知",
        "priority": "high",
        "priority_display": "高",
        "status": "published",
        "status_display": "已发布",
        "send_email": true,
        "email_sent_at": "2024-01-08T11:30:00Z",
        "published_at": "2024-01-08T11:00:00Z",
        "created_by": 1,
        "created_by_name": "admin",
        "recipient_count": 45,
        "read_count": 30,
        "created_at": "2024-01-08T10:45:00Z",
        "updated_at": "2024-01-08T11:00:00Z"
      }
    ]
  }
}
```

---

### 1.2 创建通知

**接口**: `POST /api/v1/admin/notifications/`

**权限**: 需要租户管理员权限

**请求体**:
```json
{
  "title": "系统维护通知",
  "content": "我们将在今晚22:00-23:00进行系统维护，期间服务可能会暂时中断，请提前做好准备。感谢您的理解与支持！",
  "scope": "tenant",
  "application": null,
  "notification_type": "info",
  "priority": "normal",
  "send_email": false
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| title | string | 是 | 通知标题，最长200字符 |
| content | string | 是 | 通知内容，支持富文本/Markdown |
| scope | string | 是 | 通知范围：tenant(租户), application(应用), members(特定成员) |
| application | int | 条件 | 关联应用ID，当scope=application时必填 |
| notification_type | string | 否 | 类型：info, warning, error, update, announcement，默认info |
| priority | string | 否 | 优先级：low, normal, high, urgent，默认normal |
| send_email | bool | 否 | 是否发送邮件，默认false |

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "title": "系统维护通知",
    "content": "我们将在今晚22:00-23:00进行系统维护",
    "scope": "tenant",
    "notification_type": "info",
    "priority": "normal",
    "send_email": false
  }'
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "创建成功",
  "data": {
    "id": 10,
    "title": "系统维护通知",
    "content": "我们将在今晚22:00-23:00进行系统维护",
    "scope": "tenant",
    "scope_display": "面向租户",
    "application": null,
    "application_name": null,
    "notification_type": "info",
    "type_display": "信息通知",
    "priority": "normal",
    "priority_display": "普通",
    "status": "draft",
    "status_display": "草稿",
    "send_email": false,
    "email_sent_at": null,
    "published_at": null,
    "created_by": 1,
    "created_by_name": "admin",
    "recipient_count": 0,
    "read_count": 0,
    "unread_count": 0,
    "tenant": 3,
    "created_at": "2024-01-08T15:30:00Z",
    "updated_at": "2024-01-08T15:30:00Z"
  }
}
```

---

### 1.3 创建应用通知示例

**请求体**:
```json
{
  "title": "博客系统新功能上线",
  "content": "博客系统已支持Markdown编辑器和代码高亮功能，欢迎体验！",
  "scope": "application",
  "application": 5,
  "notification_type": "update",
  "priority": "high",
  "send_email": true
}
```

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "title": "博客系统新功能上线",
    "content": "博客系统已支持Markdown编辑器和代码高亮功能，欢迎体验！",
    "scope": "application",
    "application": 5,
    "notification_type": "update",
    "priority": "high",
    "send_email": true
  }'
```

---

### 1.4 获取通知详情

**接口**: `GET /api/v1/admin/notifications/{id}/`

**权限**: GET请求允许匿名访问（需要X-Tenant-ID header）

**路径参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | int | 通知ID |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/admin/notifications/1/" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 1,
    "title": "系统维护通知",
    "content": "我们将在今晚22:00-23:00进行系统维护，期间服务可能会暂时中断，请提前做好准备。感谢您的理解与支持！",
    "scope": "tenant",
    "scope_display": "面向租户",
    "application": null,
    "application_name": null,
    "notification_type": "info",
    "type_display": "信息通知",
    "priority": "normal",
    "priority_display": "普通",
    "status": "published",
    "status_display": "已发布",
    "send_email": false,
    "email_sent_at": null,
    "published_at": "2024-01-08T10:00:00Z",
    "created_by": 1,
    "created_by_name": "admin",
    "recipient_count": 150,
    "read_count": 80,
    "unread_count": 70,
    "tenant": 3,
    "created_at": "2024-01-08T09:30:00Z",
    "updated_at": "2024-01-08T10:00:00Z"
  }
}
```

---

### 1.5 更新通知

**接口**: `PATCH /api/v1/admin/notifications/{id}/` 或 `PUT /api/v1/admin/notifications/{id}/`

**权限**: 需要租户管理员权限

**注意**: 只有草稿状态(draft)的通知可以编辑

**请求体** (PATCH可以只传需要更新的字段):
```json
{
  "title": "系统维护通知（更新）",
  "content": "维护时间调整为今晚23:00-24:00",
  "priority": "high"
}
```

**curl命令示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/admin/notifications/10/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "title": "系统维护通知（更新）",
    "content": "维护时间调整为今晚23:00-24:00",
    "priority": "high"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "更新成功",
  "data": {
    "id": 10,
    "title": "系统维护通知（更新）",
    "content": "维护时间调整为今晚23:00-24:00",
    "scope": "tenant",
    "scope_display": "面向租户",
    "priority": "high",
    "priority_display": "高",
    "status": "draft",
    "updated_at": "2024-01-08T15:45:00Z"
  }
}
```

---

### 1.6 删除通知

**接口**: `DELETE /api/v1/admin/notifications/{id}/`

**权限**: 需要租户管理员权限

**注意**: 删除为软删除，数据仍保留在数据库中

**curl命令示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/notifications/10/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "删除成功"
}
```

---

## 二、通知发布与状态管理

### 2.1 发布通知

**接口**: `POST /api/v1/admin/notifications/{id}/publish/`

**权限**: 需要租户管理员权限

**功能说明**:
- 将通知状态从 draft 改为 published
- 根据 scope 自动创建接收者记录：
  - scope=tenant: 发送给租户下所有激活的Member
  - scope=application: 发送给租户下所有激活的Member
  - scope=members: 需要管理员手动添加接收者
- 如果 send_email=true，异步发送邮件通知

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications/10/publish/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "发布成功",
  "data": {
    "id": 10,
    "title": "系统维护通知（更新）",
    "content": "维护时间调整为今晚23:00-24:00",
    "scope": "tenant",
    "scope_display": "面向租户",
    "status": "published",
    "status_display": "已发布",
    "published_at": "2024-01-08T15:50:00Z",
    "recipient_count": 150,
    "read_count": 0,
    "unread_count": 150,
    "created_at": "2024-01-08T15:30:00Z",
    "updated_at": "2024-01-08T15:50:00Z"
  }
}
```

---

### 2.2 归档通知

**接口**: `POST /api/v1/admin/notifications/{id}/archive/`

**权限**: 需要租户管理员权限

**功能说明**: 将通知状态改为 archived（已归档），归档后的通知不会在成员端显示

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications/1/archive/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "归档成功",
  "data": {
    "id": 1,
    "title": "系统维护通知",
    "status": "archived",
    "status_display": "已归档",
    "updated_at": "2024-01-08T16:00:00Z"
  }
}
```

---

## 三、接收者管理 API

### 3.1 获取通知接收者列表

**接口**: `GET /api/v1/admin/notifications/{id}/recipients/`

**权限**: GET请求允许匿名访问（需要X-Tenant-ID header）

**路径参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | int | 通知ID |

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认10 |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/admin/notifications/1/recipients/?page=1&page_size=20" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 150,
    "next": "http://localhost:8000/api/v1/admin/notifications/1/recipients/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1001,
        "member": 20,
        "member_username": "zhang_san",
        "member_email": "zhangsan@example.com",
        "is_read": true,
        "read_at": "2024-01-08T10:30:00Z",
        "created_at": "2024-01-08T10:00:00Z"
      },
      {
        "id": 1002,
        "member": 21,
        "member_username": "li_si",
        "member_email": "lisi@example.com",
        "is_read": false,
        "read_at": null,
        "created_at": "2024-01-08T10:00:00Z"
      }
    ]
  }
}
```

---

### 3.2 添加接收者

**接口**: `POST /api/v1/admin/notifications/{id}/add-recipients/`

**权限**: 需要租户管理员权限

**注意**: 只有 scope=members 的通知可以手动添加接收者

**请求体**:
```json
{
  "member_ids": [20, 21, 22, 23]
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| member_ids | array | 是 | 成员ID列表，至少包含1个 |

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications/15/add-recipients/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "member_ids": [20, 21, 22, 23]
  }'
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "成功添加 4 个接收者",
  "data": {
    "detail": "成功添加 4 个接收者",
    "added_count": 4
  }
}
```

**错误响应示例** (非members通知):
```json
{
  "success": false,
  "code": 4000,
  "message": "只有\"面向特定成员\"的通知可以手动添加接收者"
}
```

---

### 3.3 移除接收者

**接口**: `POST /api/v1/admin/notifications/{id}/remove-recipients/`

**权限**: 需要租户管理员权限

**功能说明**: 软删除接收者记录，移除后成员将看不到该通知

**请求体**:
```json
{
  "member_ids": [20, 21]
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| member_ids | array | 是 | 成员ID列表，至少包含1个 |

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications/15/remove-recipients/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "member_ids": [20, 21]
  }'
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "成功移除 2 个接收者",
  "data": {
    "detail": "成功移除 2 个接收者",
    "removed_count": 2
  }
}
```

---

## 四、统计信息 API

### 4.1 获取通知统计

**接口**: `GET /api/v1/admin/notifications/{id}/statistics/`

**权限**: GET请求允许匿名访问（需要X-Tenant-ID header）

**功能说明**: 获取通知的接收者统计信息，包括总数、已读数、未读数和阅读率

**路径参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | int | 通知ID |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/admin/notifications/1/statistics/" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "total_recipients": 150,
    "read_count": 120,
    "unread_count": 30,
    "read_rate": 80.0
  }
}
```

**字段说明**:

| 字段名 | 类型 | 说明 |
|-------|------|------|
| total_recipients | int | 总接收者数量 |
| read_count | int | 已读数量 |
| unread_count | int | 未读数量 |
| read_rate | float | 阅读率（百分比） |

---

## 五、数据字典

### 5.1 通知范围 (scope)

| 值 | 说明 | 发布行为 |
|---|------|---------|
| tenant | 面向租户 | 自动发送给租户下所有激活的Member |
| application | 面向应用 | 自动发送给租户下所有激活的Member |
| members | 面向特定成员 | 需要管理员手动添加接收者 |

### 5.2 通知类型 (notification_type)

| 值 | 说明 |
|---|------|
| info | 信息通知 |
| warning | 警告通知 |
| error | 错误通知 |
| update | 更新通知 |
| announcement | 公告 |

### 5.3 优先级 (priority)

| 值 | 说明 |
|---|------|
| low | 低 |
| normal | 普通 |
| high | 高 |
| urgent | 紧急 |

### 5.4 状态 (status)

| 值 | 说明 | 可操作 |
|---|------|--------|
| draft | 草稿 | 可编辑、可发布、可删除 |
| published | 已发布 | 可归档、不可编辑 |
| archived | 已归档 | 不可编辑、不在成员端显示 |

---

## 六、使用场景示例

### 6.1 创建并发布租户通知

```bash
# 1. 创建草稿
curl -X POST "http://localhost:8000/api/v1/admin/notifications/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "title": "系统升级通知",
    "content": "系统将于本周六凌晨进行升级",
    "scope": "tenant",
    "notification_type": "announcement",
    "priority": "high",
    "send_email": true
  }'

# 响应: { "data": { "id": 20, "status": "draft", ... } }

# 2. 发布通知
curl -X POST "http://localhost:8000/api/v1/admin/notifications/20/publish/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"

# 响应: { "data": { "id": 20, "status": "published", "recipient_count": 150, ... } }
```

### 6.2 创建应用通知

```bash
# 创建并发布应用通知
curl -X POST "http://localhost:8000/api/v1/admin/notifications/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "title": "博客系统更新",
    "content": "新增了评论功能",
    "scope": "application",
    "application": 5,
    "notification_type": "update",
    "priority": "normal",
    "send_email": false
  }'
```

### 6.3 创建定向通知

```bash
# 1. 创建面向特定成员的通知
curl -X POST "http://localhost:8000/api/v1/admin/notifications/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "title": "VIP用户专属通知",
    "content": "您已获得VIP特权",
    "scope": "members",
    "notification_type": "info",
    "priority": "normal"
  }'

# 响应: { "data": { "id": 25, "status": "draft", ... } }

# 2. 添加接收者
curl -X POST "http://localhost:8000/api/v1/admin/notifications/25/add-recipients/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 3" \
  -d '{
    "member_ids": [20, 25, 30]
  }'

# 3. 发布通知
curl -X POST "http://localhost:8000/api/v1/admin/notifications/25/publish/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"
```

---

## 七、注意事项

1. **权限控制**:
   - GET请求允许匿名访问，但需要提供X-Tenant-ID
   - POST/PATCH/DELETE需要租户管理员权限

2. **通知范围**:
   - scope=application时，application字段必填
   - scope不是application时，application字段必须为空或null

3. **编辑限制**:
   - 只有draft状态的通知可以编辑
   - published和archived状态的通知不可编辑

4. **发布行为**:
   - tenant和application范围的通知发布时自动创建接收者
   - members范围的通知需要手动添加接收者后再发布

5. **删除**:
   - 所有删除操作都是软删除
   - 软删除的数据不会在查询中显示，但保留在数据库中

6. **邮件发送**:
   - send_email=true时，发布通知会异步发送邮件
   - 邮件发送状态记录在email_sent_at字段

---

## 八、常见问题

**Q: 如何查询某个应用的所有通知？**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/notifications/?application=5" \
  -H "X-Tenant-ID: 3"
```

**Q: 如何查询所有已发布的通知？**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/notifications/?status=published" \
  -H "X-Tenant-ID: 3"
```

**Q: 如何查看通知的阅读情况？**
```bash
# 查看统计信息
curl -X GET "http://localhost:8000/api/v1/admin/notifications/1/statistics/" \
  -H "X-Tenant-ID: 3"

# 查看具体接收者列表
curl -X GET "http://localhost:8000/api/v1/admin/notifications/1/recipients/" \
  -H "X-Tenant-ID: 3"
```

**Q: 发布后的通知能否再编辑？**

不能。只有draft状态的通知可以编辑。如需修改已发布的通知，建议归档旧通知，创建新通知。

**Q: 如何撤回已发布的通知？**

可以通过归档API将通知状态改为archived，归档后成员端将看不到该通知。
```bash
curl -X POST "http://localhost:8000/api/v1/admin/notifications/1/archive/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 3"
```
