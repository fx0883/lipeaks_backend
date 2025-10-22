# 用户反馈系统 API 设计

## 文档信息
- **版本**: v1.0
- **创建日期**: 2025-10-22
- **API基础路径**: `/api/v1/feedbacks/`
- **认证方式**: JWT Token

## 1. API概览

### 1.1 端点列表

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| **软件管理** | | | |
| `/software-categories/` | GET | 软件分类列表 | 所有人 |
| `/software-categories/` | POST | 创建分类 | 租户管理员 |
| `/software-categories/{id}/` | GET | 分类详情 | 所有人 |
| `/software-categories/{id}/` | PATCH | 更新分类 | 租户管理员 |
| `/software-categories/{id}/` | DELETE | 删除分类 | 租户管理员 |
| `/software/` | GET | 软件列表 | 所有人 |
| `/software/` | POST | 创建软件 | 租户管理员 |
| `/software/{id}/` | GET | 软件详情 | 所有人 |
| `/software/{id}/` | PATCH | 更新软件 | 租户管理员 |
| `/software/{id}/` | DELETE | 删除软件 | 租户管理员 |
| `/software/{id}/versions/` | GET | 版本列表 | 所有人 |
| `/software/{id}/versions/` | POST | 添加版本 | 租户管理员 |
| `/software/{id}/versions/{vid}/` | GET | 版本详情 | 所有人 |
| `/software/{id}/versions/{vid}/` | PATCH | 更新版本 | 租户管理员 |
| `/software/{id}/versions/{vid}/` | DELETE | 删除版本 | 租户管理员 |
| **反馈管理** | | | |
| `/feedbacks/` | POST | 创建反馈 | 所有人 |
| `/feedbacks/` | GET | 反馈列表 | 注册用户 |
| `/feedbacks/{id}/` | GET | 反馈详情 | 提交人/管理员 |
| `/feedbacks/{id}/` | PATCH | 更新反馈 | 提交人/管理员 |
| `/feedbacks/{id}/` | DELETE | 删除反馈 | 提交人/管理员 |
| `/feedbacks/{id}/replies/` | POST | 添加回复 | 管理员 |
| `/feedbacks/{id}/replies/` | GET | 回复列表 | 提交人/管理员 |
| `/feedbacks/{id}/status/` | PATCH | 变更状态 | 管理员 |
| `/feedbacks/{id}/history/` | GET | 状态历史 | 提交人/管理员 |
| `/feedbacks/{id}/vote/` | POST | 投票 | 注册用户 |
| `/feedbacks/{id}/vote/` | DELETE | 取消投票 | 注册用户 |
| `/feedbacks/{id}/attachments/` | POST | 上传附件 | 提交人/管理员 |
| `/feedbacks/statistics/` | GET | 统计数据 | 管理员 |
| `/feedbacks/verify-email/` | POST | 验证邮箱 | 匿名 |

---

## 2. 软件管理API

### 2.1 软件分类列表

**端点**: `GET /api/v1/feedbacks/software-categories/`

**权限**: 所有人

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": [
    {
      "id": 1,
      "name": "Web应用",
      "code": "web",
      "description": "基于浏览器的应用程序",
      "icon": "web",
      "sort_order": 1,
      "software_count": 12
    },
    {
      "id": 2,
      "name": "移动APP",
      "code": "mobile",
      "description": "iOS和Android移动应用",
      "icon": "smartphone",
      "sort_order": 2,
      "software_count": 8
    }
  ]
}
```

---

### 2.2 创建软件

**端点**: `POST /api/v1/feedbacks/software/`

**权限**: 租户管理员（超级管理员不可创建）

**请求体**:
```json
{
  "name": "CRM系统",
  "code": "crm_system",
  "description": "客户关系管理系统，用于管理客户信息和销售流程",
  "category_id": 1,
  "current_version": "v1.0.0",
  "owner": "张三",
  "team": "产品研发部",
  "contact_email": "crm-support@example.com",
  "website": "https://crm.example.com",
  "tags": ["企业级", "SaaS", "B2B"],
  "status": "released",
  "is_active": true
}
```

**响应** (201 Created):
```json
{
  "success": true,
  "code": 2000,
  "message": "软件创建成功",
  "data": {
    "id": 1,
    "name": "CRM系统",
    "code": "crm_system",
    "description": "客户关系管理系统...",
    "category": {
      "id": 1,
      "name": "Web应用"
    },
    "current_version": "v1.0.0",
    "owner": "张三",
    "team": "产品研发部",
    "contact_email": "crm-support@example.com",
    "website": "https://crm.example.com",
    "logo": null,
    "tags": ["企业级", "SaaS", "B2B"],
    "status": "released",
    "is_active": true,
    "total_feedbacks": 0,
    "open_feedbacks": 0,
    "created_at": "2025-10-22T10:00:00Z"
  }
}
```

**业务规则**:
1. 软件代码（code）在租户内必须唯一
2. 只有租户管理员可以创建软件
3. 超级管理员不能管理软件
4. 创建时自动关联当前租户

---

### 2.3 软件列表

**端点**: `GET /api/v1/feedbacks/software/`

**权限**: 所有人

**请求参数**:
```
?page=1
&page_size=20
&category_id=1
&status=released
&is_active=true
&search=CRM  // 搜索名称和描述
&sort=-created_at
```

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 25,
    "results": [
      {
        "id": 1,
        "name": "CRM系统",
        "code": "crm_system",
        "description": "客户关系管理系统...",
        "category": {
          "id": 1,
          "name": "Web应用",
          "code": "web"
        },
        "current_version": "v1.2.3",
        "status": "released",
        "logo": "https://example.com/media/logos/crm.png",
        "total_feedbacks": 45,
        "open_feedbacks": 12,
        "is_active": true
      }
    ]
  }
}
```

---

### 2.4 添加软件版本

**端点**: `POST /api/v1/feedbacks/software/{id}/versions/`

**权限**: 租户管理员

**请求体**:
```json
{
  "version": "v1.2.4",
  "version_code": 124,
  "release_date": "2025-10-22",
  "release_notes": "新增功能：\n1. 夜间模式\n2. 数据导出\n\n修复问题：\n1. 启动速度优化",
  "is_stable": true,
  "download_url": "https://download.example.com/crm/v1.2.4/"
}
```

**响应** (201 Created):
```json
{
  "success": true,
  "code": 2000,
  "message": "版本添加成功",
  "data": {
    "id": 10,
    "software_id": 1,
    "software_name": "CRM系统",
    "version": "v1.2.4",
    "version_code": 124,
    "release_date": "2025-10-22",
    "release_notes": "新增功能...",
    "is_stable": true,
    "download_url": "https://download.example.com/crm/v1.2.4/",
    "created_at": "2025-10-22T10:30:00Z"
  }
}
```

**业务规则**:
1. 版本号在同一软件下必须唯一
2. 如果是稳定版且版本代码最新，自动更新软件的current_version
3. 只有租户管理员可以添加版本

---

## 3. 反馈管理API

### 3.1 创建反馈

**端点**: `POST /api/v1/feedbacks/`

**权限**: 所有人（包括匿名用户）

**请求头**:
```http
Content-Type: application/json
Authorization: Bearer {token}  # 注册用户必填
X-Tenant-ID: {tenant_id}  # 可选
```

**请求体** (注册用户):
```json
{
  "title": "软件启动时出现错误",
  "description": "详细描述问题...",
  "feedback_type": "bug",
  "priority": "high",
  "software_id": 1,
  "software_version_id": 10,  // 可选，关联具体版本
  "environment_info": {
    "os": "Windows 10",
    "browser": "Chrome",
    "app_version": "1.2.3"
  },
  "attachments": [
    {"file": "base64..."},
    {"file": "base64..."}
  ]
}
```

**请求体** (匿名用户):
```json
{
  "title": "希望增加夜间模式",
  "description": "详细描述...",
  "feedback_type": "feature",
  "priority": "medium",
  "software_id": 1,
  "anonymous_name": "张三",  // 可选
  "contact_email": "zhangsan@example.com",  // 必填
  "environment_info": {...}
}
```

**响应** (成功 - 201 Created):
```json
{
  "success": true,
  "code": 2000,
  "message": "反馈提交成功",
  "data": {
    "id": 123,
    "tracking_number": "FB-20251022-001",
    "title": "软件启动时出现错误",
    "description": "详细描述问题...",
    "feedback_type": "bug",
    "feedback_type_display": "Bug报告",
    "status": "submitted",
    "status_display": "已提交",
    "priority": "high",
    "priority_display": "高",
    "software": {
      "id": 1,
      "name": "示例软件",
      "code": "DEMO_001"
    },
    "software_version": "v1.2.3",
    "submitter": {
      "type": "member",  // user/member/anonymous
      "name": "用户名",
      "email": "user@example.com"
    },
    "email_verified": false,
    "email_verification_required": true,
    "can_reply_by_email": true,
    "created_at": "2025-10-22T10:30:00Z",
    "updated_at": "2025-10-22T10:30:00Z"
  }
}
```

**响应** (失败 - 400 Bad Request):
```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "errors": {
    "title": ["标题不能为空"],
    "contact_email": ["匿名用户必须提供邮箱"]
  }
}
```

**业务规则**:
1. 匿名用户必须提供contact_email
2. 标题最多200字符，描述最多5000字符
3. 附件最多5个，每个最大10MB
4. 匿名用户提交后发送邮箱验证邮件
5. 自动收集IP地址和User Agent

---

### 3.2 反馈列表

**端点**: `GET /api/v1/feedbacks/`

**权限**: 注册用户

**请求参数**:
```
?page=1
&page_size=20
&software_id=1
&feedback_type=bug
&status=submitted
&priority=high
&submitter_id=10  // 管理员可用
&date_from=2025-10-01
&date_to=2025-10-31
&search=关键词  // 搜索标题和描述
&sort=-created_at  // 排序: created_at, -created_at, votes_count, -votes_count
```

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 100,
    "next": "http://api.example.com/api/v1/feedbacks/?page=2",
    "previous": null,
    "results": [
      {
        "id": 123,
        "tracking_number": "FB-20251022-001",
        "title": "软件启动时出现错误",
        "feedback_type": "bug",
        "feedback_type_display": "Bug报告",
        "status": "submitted",
        "status_display": "已提交",
        "priority": "high",
        "priority_display": "高",
        "software": {
          "id": 1,
          "name": "示例软件"
        },
        "submitter": {
          "name": "用户名"
        },
        "votes_count": 5,
        "replies_count": 2,
        "created_at": "2025-10-22T10:30:00Z",
        "last_replied_at": "2025-10-22T15:20:00Z"
      }
    ]
  }
}
```

**权限规则**:
- 普通用户：只能看到自己提交的反馈
- 管理员：可以看到本租户所有反馈

---

### 3.3 反馈详情

**端点**: `GET /api/v1/feedbacks/{id}/`

**权限**: 提交人或管理员

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "id": 123,
    "tracking_number": "FB-20251022-001",
    "title": "软件启动时出现错误",
    "description": "详细描述...",
    "feedback_type": "bug",
    "feedback_type_display": "Bug报告",
    "status": "in_progress",
    "status_display": "处理中",
    "priority": "high",
    "priority_display": "高",
    "software": {
      "id": 1,
      "name": "示例软件",
      "code": "DEMO_001",
      "version": "v1.0.0"
    },
    "software_version": {
      "id": 10,
      "version": "v1.2.3",
      "release_date": "2025-10-15"
    },
    "submitter": {
      "type": "member",
      "id": 50,
      "name": "用户名",
      "email": "user@example.com"
    },
    "environment_info": {
      "os": "Windows 10",
      "browser": "Chrome 120.0",
      "screen_resolution": "1920x1080"
    },
    "email_verified": true,
    "can_reply_by_email": true,
    "email_notification_enabled": true,
    "views_count": 15,
    "votes_count": 5,
    "replies_count": 3,
    "attachments": [
      {
        "id": 1,
        "filename": "error_screenshot.png",
        "file_type": "image",
        "file_size": 102400,
        "url": "https://example.com/media/feedbacks/...",
        "uploaded_at": "2025-10-22T10:30:00Z"
      }
    ],
    "created_at": "2025-10-22T10:30:00Z",
    "updated_at": "2025-10-22T15:20:00Z",
    "first_replied_at": "2025-10-22T12:00:00Z",
    "last_replied_at": "2025-10-22T15:20:00Z",
    "resolved_at": null,
    "closed_at": null
  }
}
```

**响应** (403 Forbidden):
```json
{
  "success": false,
  "code": 4003,
  "message": "无权访问此反馈"
}
```

---

### 3.4 更新反馈

**端点**: `PATCH /api/v1/feedbacks/{id}/`

**权限**: 提交人（仅未处理状态）或管理员

**请求体**:
```json
{
  "title": "更新后的标题",
  "description": "更新后的描述",
  "priority": "urgent"
}
```

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "更新成功",
  "data": {
    // 完整反馈信息
  }
}
```

**业务规则**:
1. 普通用户只能在status为"submitted"时更新
2. 管理员可以随时更新
3. 不能直接更新status，需使用状态变更API

---

### 3.5 删除反馈

**端点**: `DELETE /api/v1/feedbacks/{id}/`

**权限**: 提交人（仅未回复）或管理员

**响应** (204 No Content):
```json
{
  "success": true,
  "code": 2000,
  "message": "删除成功"
}
```

**业务规则**:
1. 软删除，设置is_deleted=True
2. 普通用户只能删除无回复的反馈
3. 管理员可以随时删除

---

## 4. 回复管理API

### 4.1 添加回复

**端点**: `POST /api/v1/feedbacks/{id}/replies/`

**权限**: 管理员

**请求体**:
```json
{
  "content": "感谢您的反馈，我们已经定位到问题...",
  "reply_type": "official",  // official/internal
  "is_internal": false,
  "change_status": "in_progress",  // 可选，同时变更状态
  "attachments": [  // 可选
    {"file": "base64..."}
  ]
}
```

**响应** (201 Created):
```json
{
  "success": true,
  "code": 2000,
  "message": "回复成功",
  "data": {
    "id": 50,
    "feedback_id": 123,
    "content": "感谢您的反馈...",
    "reply_type": "official",
    "is_internal": false,
    "replier": {
      "id": 1,
      "name": "管理员"
    },
    "email_sent": false,
    "email_sent_at": null,
    "created_at": "2025-10-22T16:00:00Z"
  }
}
```

**业务规则**:
1. 只有官方回复(is_internal=false)才发送邮件
2. 邮件异步发送，返回时email_sent可能为false
3. 如果无法获取收件人邮箱，标记"无法发送"
4. 回复后自动更新反馈的last_replied_at

---

### 4.2 回复列表

**端点**: `GET /api/v1/feedbacks/{id}/replies/`

**权限**: 提交人或管理员

**请求参数**:
```
?include_internal=false  // 管理员可设为true查看内部备注
```

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": [
    {
      "id": 50,
      "content": "感谢您的反馈...",
      "reply_type": "official",
      "is_internal": false,
      "replier": {
        "id": 1,
        "name": "管理员"
      },
      "email_sent": true,
      "email_sent_at": "2025-10-22T16:01:00Z",
      "created_at": "2025-10-22T16:00:00Z"
    },
    {
      "id": 51,
      "content": "内部讨论记录...",
      "reply_type": "internal",
      "is_internal": true,
      "replier": {
        "id": 2,
        "name": "技术主管"
      },
      "created_at": "2025-10-22T16:30:00Z"
    }
  ]
}
```

**权限规则**:
- 普通用户：只能看到官方回复(is_internal=false)
- 管理员：可以看到所有回复

---

## 5. 状态管理API

### 5.1 变更状态

**端点**: `PATCH /api/v1/feedbacks/{id}/status/`

**权限**: 管理员

**请求体**:
```json
{
  "new_status": "resolved",
  "reason": "问题已在v1.2.4版本修复",
  "send_email": true  // 是否发送邮件通知
}
```

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "状态变更成功",
  "data": {
    "feedback_id": 123,
    "old_status": "in_progress",
    "old_status_display": "处理中",
    "new_status": "resolved",
    "new_status_display": "已解决",
    "reason": "问题已在v1.2.4版本修复",
    "changed_by": {
      "id": 1,
      "name": "管理员"
    },
    "email_sent": true,
    "changed_at": "2025-10-22T17:00:00Z"
  }
}
```

**业务规则**:
1. 验证状态流转合法性
2. 记录到FeedbackStatusHistory
3. 如果send_email=true且用户开启通知，发送邮件
4. 状态变更为"resolved"时记录resolved_at
5. 状态变更为"closed"时记录closed_at

---

### 5.2 状态历史

**端点**: `GET /api/v1/feedbacks/{id}/history/`

**权限**: 提交人或管理员

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": [
    {
      "id": 1,
      "old_status": "submitted",
      "old_status_display": "已提交",
      "new_status": "reviewing",
      "new_status_display": "审阅中",
      "reason": null,
      "changed_by": {
        "id": 1,
        "name": "管理员"
      },
      "email_sent": false,
      "created_at": "2025-10-22T11:00:00Z"
    },
    {
      "id": 2,
      "old_status": "reviewing",
      "new_status": "confirmed",
      "reason": "问题确认存在",
      "changed_by": {
        "id": 1,
        "name": "管理员"
      },
      "email_sent": true,
      "created_at": "2025-10-22T12:00:00Z"
    }
  ]
}
```

---

## 6. 投票功能API

### 6.1 投票

**端点**: `POST /api/v1/feedbacks/{id}/vote/`

**权限**: 注册用户（User/Member）

**请求体**: 无

**响应** (201 Created):
```json
{
  "success": true,
  "code": 2000,
  "message": "投票成功",
  "data": {
    "feedback_id": 123,
    "votes_count": 6,
    "has_voted": true
  }
}
```

**响应** (400 Bad Request - 已投票):
```json
{
  "success": false,
  "code": 4000,
  "message": "您已经投过票了"
}
```

---

### 6.2 取消投票

**端点**: `DELETE /api/v1/feedbacks/{id}/vote/`

**权限**: 注册用户（User/Member）

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "取消投票成功",
  "data": {
    "feedback_id": 123,
    "votes_count": 5,
    "has_voted": false
  }
}
```

---

## 7. 附件管理API

### 7.1 上传附件

**端点**: `POST /api/v1/feedbacks/{id}/attachments/`

**权限**: 提交人或管理员

**请求体** (multipart/form-data):
```
file: <binary>
file_type: image  // 可选，自动检测
```

**响应** (201 Created):
```json
{
  "success": true,
  "code": 2000,
  "message": "上传成功",
  "data": {
    "id": 10,
    "feedback_id": 123,
    "filename": "error_log.txt",
    "original_filename": "日志.txt",
    "file_type": "log",
    "file_size": 10240,
    "mime_type": "text/plain",
    "url": "https://example.com/media/feedbacks/attachments/...",
    "uploaded_at": "2025-10-22T10:35:00Z"
  }
}
```

**业务规则**:
1. 文件大小限制：10MB
2. 允许类型：jpg, png, gif, txt, log, zip
3. 每个反馈最多5个附件
4. 自动重命名防止冲突
5. 按日期分目录存储

---

## 8. 统计分析API

### 8.1 反馈统计

**端点**: `GET /api/v1/feedbacks/statistics/`

**权限**: 管理员

**请求参数**:
```
?software_id=1
&date_from=2025-10-01
&date_to=2025-10-31
&group_by=type  // type/status/date
```

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "summary": {
      "total_feedbacks": 150,
      "by_type": {
        "bug": 80,
        "feature": 40,
        "experience": 20,
        "other": 10
      },
      "by_status": {
        "submitted": 30,
        "reviewing": 20,
        "confirmed": 15,
        "in_progress": 25,
        "resolved": 50,
        "closed": 10
      },
      "by_priority": {
        "low": 20,
        "medium": 80,
        "high": 40,
        "urgent": 10
      }
    },
    "response_time": {
      "average_first_response_hours": 4.5,
      "average_resolution_hours": 48.2
    },
    "hot_feedbacks": [
      {
        "id": 123,
        "tracking_number": "FB-20251022-001",
        "title": "希望增加夜间模式",
        "votes_count": 25,
        "status": "confirmed"
      }
    ],
    "trend": [
      {
        "date": "2025-10-01",
        "count": 5
      },
      {
        "date": "2025-10-02",
        "count": 8
      }
    ]
  }
}
```

---

## 9. 邮箱验证API

### 9.1 验证邮箱

**端点**: `POST /api/v1/feedbacks/verify-email/`

**权限**: 无（匿名可访问）

**请求体**:
```json
{
  "token": "verification_token_string"
}
```

**响应** (200 OK):
```json
{
  "success": true,
  "code": 2000,
  "message": "邮箱验证成功",
  "data": {
    "feedback_id": 123,
    "tracking_number": "FB-20251022-001",
    "email_verified": true
  }
}
```

**响应** (400 Bad Request - token无效):
```json
{
  "success": false,
  "code": 4000,
  "message": "验证令牌无效或已过期"
}
```

---

## 10. 错误码定义

### 10.1 标准错误码

| 错误码 | 说明 |
|-------|------|
| 2000 | 成功 |
| 4000 | 请求参数错误 |
| 4001 | 认证失败 |
| 4003 | 权限不足 |
| 4004 | 资源不存在 |
| 4009 | 请求冲突（如重复投票） |
| 4029 | 请求过于频繁 |
| 5000 | 服务器内部错误 |
| 5003 | 服务暂时不可用 |

### 10.2 业务错误码

| 错误码 | 说明 |
|-------|------|
| 10001 | 反馈不存在 |
| 10002 | 无权访问此反馈 |
| 10003 | 邮箱未验证 |
| 10004 | 反馈已关闭，无法操作 |
| 10005 | 附件数量超限 |
| 10006 | 附件大小超限 |
| 10007 | 不支持的文件类型 |
| 10008 | 已投票，无法重复投票 |
| 10009 | 未投票，无法取消 |
| 10010 | 状态流转不合法 |

---

## 11. 频率限制

### 11.1 提交反馈限制

```
匿名用户：
- 同一邮箱：每小时3个
- 同一IP：每小时5个

注册用户：
- 每小时10个
- 每天50个
```

### 11.2 投票限制

```
注册用户：
- 每分钟10个
```

### 11.3 API调用限制

```
注册用户：
- 每分钟60次
- 每小时1000次

管理员：
- 每分钟120次
- 每小时3000次
```

---

## 12. 测试用例

### 12.1 创建反馈测试

```bash
# 注册用户提交
curl -X POST https://api.example.com/api/v1/feedbacks/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试反馈",
    "description": "这是一个测试",
    "feedback_type": "bug",
    "software_id": 1
  }'

# 匿名用户提交
curl -X POST https://api.example.com/api/v1/feedbacks/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "匿名反馈",
    "description": "这是匿名提交",
    "feedback_type": "feature",
    "software_id": 1,
    "contact_email": "test@example.com"
  }'
```

### 12.2 添加回复测试

```bash
curl -X POST https://api.example.com/api/v1/feedbacks/123/replies/ \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "感谢反馈，我们会尽快处理",
    "reply_type": "official"
  }'
```

### 12.3 投票测试

```bash
# 投票
curl -X POST https://api.example.com/api/v1/feedbacks/123/vote/ \
  -H "Authorization: Bearer {token}"

# 取消投票
curl -X DELETE https://api.example.com/api/v1/feedbacks/123/vote/ \
  -H "Authorization: Bearer {token}"
```

---

## 13. 性能指标

### 13.1 响应时间要求

| 接口 | P50 | P95 | P99 |
|------|-----|-----|-----|
| 创建反馈 | <200ms | <500ms | <1s |
| 反馈列表 | <150ms | <300ms | <500ms |
| 反馈详情 | <100ms | <200ms | <400ms |
| 添加回复 | <200ms | <500ms | <1s |
| 统计数据 | <500ms | <1s | <2s |

### 13.2 并发能力

- 支持100并发用户
- 支持1000 QPS（查询）
- 支持200 TPS（写入）

---

## 14. 相关文档

- [02_数据模型设计.md](./02_数据模型设计.md) - 数据模型详细设计
- [04_邮件系统设计.md](./04_邮件系统设计.md) - 邮件系统详细设计
- [05_权限设计.md](./05_权限设计.md) - 权限控制方案

