# 用户反馈系统 - 详细使用手册

## 🎉 重要提示：代码已完成！

**✅ 所有必要的代码都已经写完并集成！**  
**✅ 无需修改任何 Python 代码文件！**  
**✅ 只需安装依赖和启动服务！**

## 📋 文档概述

**系统名称**：用户反馈系统（User Feedback System）  
**版本**：v1.0  
**更新时间**：2025-10-22  
**适用人员**：开发者、运维人员、系统管理员

**重要说明**：本手册中的"配置"指的是**环境变量配置**，不是修改代码！

---

## 🎯 系统简介

用户反馈系统是一个完整的反馈收集和管理平台，支持：

- ✅ **独立软件管理**：不依赖其他系统
- ✅ **多渠道反馈收集**：注册用户、匿名用户均可提交
- ✅ **异步邮件通知**：高性能邮件发送
- ✅ **完整的容错机制**：Redis断开时自动降级
- ✅ **多租户支持**：完整的数据隔离
- ✅ **管理后台**：Django Admin集成

---

## 🔧 Redis配置（已完成，仅需环境变量）

**✅ 重要提示：所有Celery和Redis配置代码都已写完！**

系统已自动包含完整的Redis配置，默认设置为：
- 默认Redis地址：`redis://localhost:6379/0`
- 支持环境变量覆盖：`CELERY_BROKER_URL`
- 自动降级机制：Redis不可用时切换同步模式
- 完整的任务路由和定时任务配置

### 方案A：使用Upstash（推荐⭐⭐⭐⭐⭐）

**只需要设置环境变量，无需修改代码！**

**步骤1：注册Upstash**
1. 访问：https://upstash.com
2. 使用GitHub或Google账号登录
3. 点击"Create Database"
4. 选择离您最近的区域
5. 点击"Create"

**步骤2：获取连接信息**
1. 进入创建的数据库
2. 复制"Redis Connect URL"
3. 格式类似：`rediss://:password@endpoint.upstash.io:6379`

**步骤3：配置环境变量（不是修改代码！）**

在项目根目录创建或编辑`.env`文件：
```bash
# .env文件（这不是代码文件，是环境变量配置）
CELERY_BROKER_URL=rediss://:password@endpoint.upstash.io:6379
CELERY_RESULT_BACKEND=rediss://:password@endpoint.upstash.io:6379
```

**就完成了！代码会自动读取这些环境变量。**

#### 方案B：使用数据库作为Broker（备选）

**代码已支持！只需设置环境变量：**

```bash
# .env文件
CELERY_BROKER_URL=django-db
CELERY_RESULT_BACKEND=django-db
```

**额外步骤**：
```bash
# 运行数据库Broker需要的迁移
python manage.py migrate django_celery_results
```

#### 方案C：本地Redis（开发环境）

**默认配置已支持！只需启动Redis：**

```bash
# Windows (using Docker)
docker run -d -p 6379:6379 redis:latest

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# 无需修改任何代码！系统会自动使用 redis://localhost:6379/0
```

### 2. 邮件配置（已完成，仅需环境变量）

**✅ 邮件配置代码已完成！** 

系统已配置QQ邮箱SMTP，您只需要提供邮箱账号信息：

**环境变量配置**（.env文件）：
```bash
# .env文件
EMAIL_HOST_USER=your-email@qq.com
EMAIL_HOST_PASSWORD=your-qq-app-password  # QQ邮箱应用专用密码
FRONTEND_URL=https://your-frontend-domain.com  # 可选，默认localhost:3000
```

**已内置的邮件配置**：
- ✅ QQ邮箱SMTP（smtp.qq.com:587）
- ✅ TLS加密连接
- ✅ 环境变量支持
- ✅ 默认发件人设置
- ✅ 前端链接构建

### 3. 中间件配置（完全可选）

**✅ 系统已可运行，此配置完全可选！**

如果您想要获得响应头中的系统状态信息，可以选择性添加监控中间件到 `core/settings.py`：

```python
# core/settings.py - MIDDLEWARE 中添加（完全可选）
MIDDLEWARE += [
    'feedbacks.middleware.RedisMonitoringMiddleware',      # Redis状态监控
    'feedbacks.middleware.EmailFallbackMiddleware',        # 邮件降级提示
]
```

**功能**：
- 在API响应头中添加系统状态信息
- 前端可以据此显示系统运行状态提示

**不配置的影响**：无，系统完全正常工作

---

## 🚀 系统启动（代码已完成）

### ⚡ 超简单启动（3步骤）

#### 步骤1：安装依赖（代码已包含所有必要依赖）
```bash
pip install -r requirements.txt
```

#### 步骤2：数据库迁移（表结构已完成）
```bash
python manage.py migrate
```

#### 步骤3：启动服务
```bash
python manage.py runserver
```

**完成！系统已可用！**
- 访问 API 文档：http://localhost:8000/api/v1/docs/
- 访问管理后台：http://localhost:8000/admin/

### 🔧 可选配置

#### 配置Redis（可选，提升性能）
```bash
# 方案1：使用本地Redis
docker run -d -p 6379:6379 redis:latest
celery -A core worker -l info &
python manage.py runserver

# 方案2：使用Upstash
# 创建 .env 文件：
echo "CELERY_BROKER_URL=rediss://:password@endpoint.upstash.io:6379" >> .env
celery -A core worker -l info &
python manage.py runserver
```

#### 初始化邮件模板（可选）
```bash
python manage.py init_feedback_templates
```

#### 验证系统状态（可选）
```bash
python manage.py check_health --verbose
```

**期望输出**：
```
============================================================
System Health Check
============================================================

[*] Checking Redis connection...
[OK] Redis: Available
   Version: 7.0.0
   Mode: redis

[*] Checking Celery configuration...
[OK] Celery: Configured with Redis

[*] Checking database connection...
[OK] Database: Connected
   Type: mysql

[*] Checking email configuration...
[OK] Email: SMTP configured

[*] Fallback mechanism status...
[OK] Primary mode: Async (via Redis)

============================================================
Summary
============================================================
[OK] System is running optimally
============================================================
```

---

## 🖥️ 管理界面使用

### Django Admin访问

**访问地址**：`http://localhost:8000/admin/`

**登录**：使用Django超级用户账号

### 反馈系统模块

进入Admin后，找到**"FEEDBACKS"**分组：

#### 1. 软件管理

**Software Categories（软件分类）**
- 管理软件类别（如：Web应用、移动APP等）
- 只有租户管理员可以创建和修改
- 支持图标和排序

**Software（软件产品）**
- 管理具体的软件产品
- 包含名称、描述、分类、版本等信息
- 统计反馈数量
- 支持Logo上传

**Software Versions（软件版本）**
- 管理软件的不同版本
- 包含版本号、发布日期、更新说明等
- 支持稳定版/测试版标记

#### 2. 反馈管理

**Feedbacks（反馈）**
- 查看所有反馈
- 按类型、状态、优先级筛选
- 批量操作：标记状态、分配等
- 查看附件和回复
- 状态变更历史

**Feedback Replies（反馈回复）**
- 查看所有回复
- 区分官方回复和内部备注
- 邮件发送状态追踪

**Feedback Votes（反馈投票）**
- 查看投票记录
- 统计最受关注的反馈

#### 3. 邮件管理

**Email Templates（邮件模板）**
- 自定义邮件模板
- 支持HTML和纯文本版本
- 变量替换功能
- 按租户分离

**Feedback Email Logs（邮件日志）**
- 查看所有邮件发送记录
- 追踪发送状态和错误信息
- 重试机制监控

---

## 📱 API使用指南

### 基础信息

**API基础URL**：`http://localhost:8000/api/v1/feedbacks/`

**认证方式**：JWT Bearer Token

**请求头**：
```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <jwt-token>  # 需要认证的接口
```

### 获取JWT Token

```http
POST /api/v1/auth/login/
```

**请求**：
```json
{
  "username": "admin@example.com",
  "password": "your-password"
}
```

**响应**：
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_tenant_admin": true
  }
}
```

### 常用API操作

#### 1. 软件管理（租户管理员）

##### 创建软件分类
```http
POST /api/v1/feedbacks/software-categories/
Authorization: Bearer <token>
```

**请求**：
```json
{
  "name": "Web应用",
  "code": "web",
  "description": "Web-based applications",
  "icon": "web",
  "sort_order": 1,
  "is_active": true
}
```

##### 创建软件产品
```http
POST /api/v1/feedbacks/software/
Authorization: Bearer <token>
```

**请求**：
```json
{
  "name": "客户管理系统",
  "code": "crm_system",
  "description": "客户关系管理系统，帮助企业管理客户信息",
  "category_id": 1,
  "website": "https://crm.example.com",
  "owner": "张三",
  "team": "CRM开发团队",
  "contact_email": "support@crm.example.com",
  "tags": ["企业级", "SaaS", "云端"],
  "status": "released",
  "is_active": true
}
```

**响应**：
```json
{
  "id": 1,
  "name": "客户管理系统",
  "code": "crm_system",
  "description": "客户关系管理系统，帮助企业管理客户信息",
  "category": {
    "id": 1,
    "name": "Web应用",
    "code": "web"
  },
  "logo": null,
  "website": "https://crm.example.com",
  "current_version": null,
  "owner": "张三",
  "team": "CRM开发团队",
  "contact_email": "support@crm.example.com",
  "tags": ["企业级", "SaaS", "云端"],
  "status": "released",
  "is_active": true,
  "total_feedbacks": 0,
  "open_feedbacks": 0,
  "versions": [],
  "created_at": "2025-01-15T10:00:00Z"
}
```

##### 添加软件版本
```http
POST /api/v1/feedbacks/software/{id}/versions/
Authorization: Bearer <token>
```

**请求**：
```json
{
  "version": "v2.1.0",
  "version_code": 210,
  "release_date": "2025-01-15",
  "release_notes": "## 新功能\n- 添加暗色模式\n- 性能优化\n\n## 修复问题\n- 修复登录问题\n- 修复数据导出错误",
  "is_stable": true,
  "is_active": true,
  "download_url": "https://releases.example.com/v2.1.0"
}
```

#### 2. 反馈提交（公开接口）

##### 注册用户提交反馈
```http
POST /api/v1/feedbacks/feedbacks/
Authorization: Bearer <token>
```

**请求**：
```json
{
  "title": "功能建议：支持批量导出",
  "description": "希望能够支持批量导出客户数据，目前只能一个一个导出，效率很低。建议增加选择多个客户后批量导出的功能。",
  "feedback_type": "feature",
  "priority": "medium",
  "software": 1,
  "software_version": 1,
  "environment_info": {
    "os": "Windows 11",
    "browser": "Chrome 120",
    "screen_resolution": "1920x1080",
    "user_agent": "Mozilla/5.0..."
  }
}
```

##### 匿名用户提交反馈
```http
POST /api/v1/feedbacks/feedbacks/
# 不需要Authorization头
```

**请求**：
```json
{
  "title": "Bug报告：登录后页面空白",
  "description": "使用Chrome浏览器登录后，页面显示空白，控制台有JavaScript错误。",
  "feedback_type": "bug",
  "priority": "high",
  "software": 1,
  "software_version": 1,
  "contact_email": "user@example.com",
  "contact_name": "用户甲",
  "environment_info": {
    "os": "macOS 13.0",
    "browser": "Chrome 120.0",
    "device": "MacBook Pro M1"
  }
}
```

**响应**：
```json
{
  "id": 1,
  "title": "Bug报告：登录后页面空白",
  "description": "使用Chrome浏览器登录后，页面显示空白...",
  "feedback_type": "bug",
  "priority": "high",
  "status": "submitted",
  "software": {
    "id": 1,
    "name": "客户管理系统"
  },
  "contact_email": "user@example.com",
  "contact_name": "用户甲",
  "email_verified": false,
  "email_notification_enabled": true,
  "vote_count": 0,
  "reply_count": 0,
  "created_at": "2025-01-15T14:30:00Z"
}
```

**注意**：匿名用户会收到邮件验证链接。

#### 3. 反馈查询

##### 获取反馈列表
```http
GET /api/v1/feedbacks/feedbacks/
Authorization: Bearer <token>
```

**查询参数**：
- `software=1` - 按软件筛选
- `feedback_type=bug` - 按类型筛选
- `status=submitted` - 按状态筛选
- `priority=high` - 按优先级筛选
- `search=登录` - 全文搜索
- `ordering=-created_at` - 排序方式

**示例请求**：
```http
GET /api/v1/feedbacks/feedbacks/?software=1&status=submitted&priority=high
Authorization: Bearer <token>
```

**响应**：
```json
{
  "count": 25,
  "next": "http://api.example.com/api/v1/feedbacks/feedbacks/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Bug报告：登录后页面空白",
      "feedback_type": "bug",
      "type_display": "Bug Report",
      "priority": "high",
      "priority_display": "High", 
      "status": "submitted",
      "status_display": "Submitted",
      "software_name": "客户管理系统",
      "version_number": "v2.1.0",
      "submitter": {
        "name": "用户甲",
        "email": "user@example.com"
      },
      "vote_count": 3,
      "reply_count": 1,
      "created_at": "2025-01-15T14:30:00Z"
    }
  ]
}
```

##### 获取反馈详情
```http
GET /api/v1/feedbacks/feedbacks/{id}/
Authorization: Bearer <token>
```

**响应**：包含完整的反馈信息、回复、附件、状态历史等。

#### 4. 反馈管理（管理员）

##### 更改反馈状态
```http
PATCH /api/v1/feedbacks/feedbacks/{id}/status/
Authorization: Bearer <token>
```

**请求**：
```json
{
  "status": "in_progress",
  "reason": "已分配给开发团队，正在调查中"
}
```

**状态流转规则**：
```
submitted → reviewing → confirmed → in_progress → resolved → closed
     ↓         ↓          ↓            ↓
  rejected  rejected   rejected    rejected
     ↓         ↓          ↓            ↓
  duplicate duplicate  duplicate  (可重新打开)
```

##### 回复反馈
```http
POST /api/v1/feedbacks/feedbacks/{feedback_id}/replies/
Authorization: Bearer <token>
```

**请求**：
```json
{
  "content": "感谢您的反馈！我们已经确认了这个问题，预计在v2.1.1版本中修复。",
  "is_internal_note": false
}
```

**注意**：
- `is_internal_note: false` - 会发送邮件给用户
- `is_internal_note: true` - 内部备注，不发邮件

#### 5. 投票和互动

##### 对反馈投票
```http
POST /api/v1/feedbacks/feedbacks/{id}/vote/
Authorization: Bearer <token>
```

**请求**：
```json
{
  "vote_type": 1  // 1表示赞成，-1表示反对
}
```

##### 取消投票
```http
DELETE /api/v1/feedbacks/feedbacks/{id}/vote/
Authorization: Bearer <token>
```

#### 6. 附件管理

##### 上传附件
```http
POST /api/v1/feedbacks/feedbacks/{feedback_id}/attachments/
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**请求**（表单数据）：
```
file: [选择文件]
```

**支持的文件类型**：jpg, jpeg, png, gif, pdf, doc, docx, txt, log, zip
**文件大小限制**：10MB

**响应**：
```json
{
  "id": 1,
  "file": "http://localhost:8000/media/feedbacks/attachments/2025/01/screenshot.png",
  "file_url": "http://localhost:8000/media/feedbacks/attachments/2025/01/screenshot.png",
  "filename": "screenshot.png",
  "file_size": 245760,
  "mime_type": "image/png",
  "uploaded_by": 1,
  "created_at": "2025-01-15T15:00:00Z"
}
```

---

## 📊 统计和监控

### 获取统计数据（管理员）

```http
GET /api/v1/feedbacks/statistics/
Authorization: Bearer <token>
```

**查询参数**：
- `software=1` - 按软件筛选
- `date_from=2025-01-01` - 开始日期
- `date_to=2025-01-31` - 结束日期

**响应**：
```json
{
  "total_feedbacks": 156,
  "open_feedbacks": 23,
  "resolved_feedbacks": 108,
  "avg_resolution_time": "2 days, 14:30:00",
  "feedbacks_by_type": {
    "bug": 62,
    "feature": 45,
    "improvement": 28,
    "question": 18,
    "other": 3
  },
  "feedbacks_by_status": {
    "submitted": 8,
    "reviewing": 5,
    "confirmed": 10,
    "in_progress": 15,
    "resolved": 108,
    "closed": 7,
    "rejected": 2,
    "duplicate": 1
  },
  "feedbacks_by_priority": {
    "critical": 12,
    "high": 34,
    "medium": 85,
    "low": 25
  },
  "top_voted_feedbacks": [
    {
      "id": 15,
      "title": "功能建议：支持暗色模式",
      "vote_count": 28,
      "feedback_type": "feature",
      "status": "confirmed"
    }
  ],
  "daily_trend": [
    {"date": "2025-01-15", "count": 8},
    {"date": "2025-01-14", "count": 5},
    {"date": "2025-01-13", "count": 12}
  ]
}
```

### 系统健康检查（管理员）

```http
GET /api/v1/feedbacks/health/
Authorization: Bearer <token>
```

**响应**（系统正常时）：
```json
{
  "status": "healthy",
  "components": {
    "redis": {
      "available": true,
      "mode": "redis",
      "version": "7.0.0",
      "uptime_days": 30
    },
    "database": {
      "available": true,
      "type": "mysql"
    },
    "celery": {
      "available": true,
      "mode": "async",
      "fallback_enabled": true
    },
    "email": {
      "available": true,
      "mode": "smtp"
    }
  },
  "recommendations": []
}
```

**响应**（Redis不可用时）：
```json
{
  "status": "degraded",
  "components": {
    "redis": {
      "available": false,
      "mode": "redis",
      "error": "Connection refused"
    },
    "celery": {
      "mode": "sync",
      "fallback_enabled": true
    }
  },
  "recommendations": [
    "Redis is not available. Email tasks will run synchronously.",
    "Consider setting up Redis or using external Redis service (Upstash)."
  ]
}
```

---

## 🔍 系统监控

### 1. 命令行监控

#### 基础健康检查
```bash
python manage.py check_health
```

**输出示例**（Redis不可用）：
```
============================================================
System Health Check
============================================================

[*] Checking Redis connection...
[FAIL] Redis: Unavailable
   Error: Connection refused
   Impact: Email tasks will run synchronously

[*] Checking Celery configuration...
[WARN] Celery: Redis configured but unavailable
   Status: Will fallback to synchronous execution

[*] Checking database connection...
[OK] Database: Connected

[*] Checking email configuration...
[OK] Email: SMTP configured

[*] Fallback mechanism status...
[WARN] Fallback mode: Synchronous
   All email tasks will execute synchronously
   API responses may be slower

============================================================
Summary
============================================================
[WARN] System is running in degraded mode

[i] Recommendations:
   1. Check Redis connection
   2. Setup external Redis service (Upstash - Free)
   3. See: temp1022/Redis_FAQ_ZH.md for solutions
============================================================
```

#### 详细健康检查
```bash
python manage.py check_health --verbose
```

额外显示：
- Redis版本、内存使用、连接数
- 邮件配置详情
- Celery broker URL（隐藏密码）

### 2. API监控

每个反馈系统的API响应都包含系统状态头：

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-System-Mode: async                    # 系统模式：async或sync
X-Redis-Status: available               # Redis状态：available或unavailable
X-System-Warning: ...                   # 警告信息（如有）
```

**前端可以据此显示提示**：
```javascript
fetch('/api/v1/feedbacks/feedbacks/')
  .then(response => {
    const systemMode = response.headers.get('X-System-Mode');
    const redisStatus = response.headers.get('X-Redis-Status');
    
    if (systemMode === 'sync') {
      showNotification('系统当前运行较慢，请耐心等待', 'warning');
    }
    
    if (redisStatus === 'unavailable') {
      console.warn('Redis unavailable, system running in degraded mode');
    }
    
    return response.json();
  });
```

### 3. 邮件监控

#### 查看邮件发送日志
```http
GET /api/v1/feedbacks/email-logs/
Authorization: Bearer <token>
```

**查询参数**：
- `feedback=1` - 按反馈筛选
- `status=failed` - 按状态筛选（pending/sending/sent/failed/bounced）
- `email_type=reply` - 按类型筛选（reply/status_change/verification/summary）

#### Django Admin查看
访问：`Admin → FEEDBACKS → Feedback email logs`

可以查看：
- 邮件发送状态
- 错误信息
- 重试次数
- 发送时间

---

## ⚙️ 邮件模板管理

### 1. 默认模板类型

系统包含4种邮件模板：

| 类型 | 代码 | 说明 | 触发时机 |
|------|------|------|---------|
| 回复通知 | reply | 管理员回复反馈时 | 添加非内部回复 |
| 状态变更 | status_change | 反馈状态变更时 | 状态改变 |
| 邮件验证 | verification | 匿名用户提交时 | 匿名提交 |
| 欢迎邮件 | welcome | 自定义使用 | 手动触发 |

### 2. 模板管理

#### 通过API管理
```http
GET /api/v1/feedbacks/email-templates/
POST /api/v1/feedbacks/email-templates/
PUT /api/v1/feedbacks/email-templates/{id}/
DELETE /api/v1/feedbacks/email-templates/{id}/
Authorization: Bearer <token>  # 需要租户管理员权限
```

#### 创建自定义模板
```http
POST /api/v1/feedbacks/email-templates/
Authorization: Bearer <token>
```

**请求**：
```json
{
  "name": "自定义回复模板",
  "template_type": "reply",
  "subject": "您的反馈已回复：{feedback_title}",
  "body_html": "<!DOCTYPE html><html><body><h1>反馈回复</h1><p>您好{contact_name}，</p><p>您的反馈：<strong>{feedback_title}</strong></p><p>我们的回复：</p><blockquote>{reply_content}</blockquote><p>感谢您的反馈！</p><p><a href=\"{view_url}\">查看详情</a></p></body></html>",
  "body_text": "您好{contact_name}，\n\n您的反馈：{feedback_title}\n\n我们的回复：\n{reply_content}\n\n感谢您的反馈！\n\n查看详情：{view_url}",
  "is_active": true,
  "variables": {
    "feedback_title": "反馈标题",
    "contact_name": "联系人姓名",
    "reply_content": "回复内容",
    "view_url": "查看链接"
  }
}
```

#### 通过Django Admin管理

访问：`Admin → FEEDBACKS → Email templates`

可以直接编辑：
- 模板名称
- 邮件主题
- HTML内容
- 纯文本内容
- 可用变量

### 3. 模板变量

#### 通用变量
```
{feedback_title}     - 反馈标题
{feedback_id}        - 反馈ID
{software_name}      - 软件名称
{software_version}   - 软件版本
{contact_name}       - 联系人姓名
{contact_email}      - 联系人邮箱
{view_url}          - 查看反馈的链接
{unsubscribe_url}   - 取消订阅链接
```

#### 回复模板专用
```
{reply_content}     - 回复内容
{reply_user}        - 回复者用户名
```

#### 状态变更模板专用
```
{old_status}        - 旧状态
{new_status}        - 新状态
{changed_by}        - 更改者
{change_reason}     - 更改原因
```

#### 验证模板专用
```
{verification_url}  - 验证链接
{verification_token} - 验证令牌
```

---

## 🔐 权限说明

### 用户角色权限

#### 超级管理员（Superuser）
- ✅ 查看本租户的所有反馈
- ✅ 回复任何反馈
- ✅ 更改任何反馈状态
- ❌ **不能管理软件**（重要限制）
- ❌ 不能查看其他租户的反馈

#### 租户管理员（Tenant Admin）
- ✅ 查看本租户的所有反馈
- ✅ 回复任何反馈
- ✅ 更改任何反馈状态
- ✅ **管理软件**（创建、修改、删除）
- ✅ 管理邮件模板
- ❌ 不能查看其他租户的反馈

#### 普通用户（Member）
- ✅ 提交反馈
- ✅ 查看自己提交的反馈
- ✅ 对反馈投票
- ✅ 修改自己的反馈（未被回复时）
- ❌ 不能回复反馈
- ❌ 不能管理软件
- ❌ 不能查看他人反馈

#### 匿名用户
- ✅ 提交反馈（需提供邮箱）
- ✅ 邮件验证
- ❌ 不能查看反馈
- ❌ 不能投票

### 数据隔离

每个租户的数据完全隔离：
- 软件产品按租户分离
- 反馈按租户分离
- 邮件模板按租户分离
- 统计数据按租户分离

---

## 🛠️ 故障排查

### 常见问题及解决方案

#### 问题1：Redis连接失败

**症状**：
```bash
python manage.py check_health
[FAIL] Redis: Unavailable
Error: Connection refused
```

**解决方案**：

1. **检查Redis服务**：
```bash
# Docker方式
docker ps | grep redis
docker start redis  # 如果已停止

# 系统服务方式
sudo systemctl status redis
sudo systemctl start redis
```

2. **检查配置**：
```python
# 确认 core/settings.py 中的配置
print(settings.CELERY_BROKER_URL)
# 输出应该是正确的Redis URL
```

3. **测试连接**：
```bash
# 安装redis-cli
sudo apt install redis-tools

# 测试连接
redis-cli -u "redis://localhost:6379" ping
# 应该返回：PONG
```

4. **使用Upstash替代**：
- 注册 https://upstash.com
- 创建数据库
- 更新 REDIS_URL

5. **临时使用数据库broker**：
```python
# core/settings.py
CELERY_BROKER_URL = 'django-db'
CELERY_RESULT_BACKEND = 'django-db'
```

#### 问题2：邮件发送失败

**症状**：
- Django Admin中看到邮件状态为"Failed"
- 用户报告未收到邮件

**排查步骤**：

1. **检查SMTP配置**：
```python
# Django shell
python manage.py shell

>>> from django.core.mail import send_mail
>>> send_mail(
...     'Test Email',
...     'This is a test',
...     'your-email@qq.com',
...     ['recipient@example.com'],
...     fail_silently=False
... )
```

2. **检查邮件日志**：
```http
GET /api/v1/feedbacks/email-logs/?status=failed
Authorization: Bearer <token>
```

查看错误信息，常见错误：
- 认证失败：检查邮箱密码（使用应用专用密码）
- SMTP服务器拒绝：检查邮箱设置
- 收件人地址无效：检查邮箱格式

3. **检查邮件模板**：
```http
GET /api/v1/feedbacks/email-templates/
Authorization: Bearer <token>
```

确保有active的模板。

#### 问题3：Celery任务不执行

**症状**：
- 反馈提交后没有收到邮件
- Celery日志无任务执行记录

**解决步骤**：

1. **检查Celery Worker状态**：
```bash
# 查看正在运行的worker
celery -A core inspect active

# 查看worker统计
celery -A core inspect stats
```

2. **检查任务队列**：
```bash
# 查看队列中的任务
celery -A core inspect reserved
```

3. **重启Worker**：
```bash
# 停止所有worker
pkill -f "celery worker"

# 重新启动
celery -A core worker -l info --queue=feedbacks,celery
```

4. **检查任务路由**：
```python
# core/settings.py
CELERY_TASK_ROUTES = {
    'feedbacks.tasks.*': {'queue': 'feedbacks'},
}
```

#### 问题4：权限错误

**症状**：
- 403 Forbidden错误
- "You don't have permission"提示

**解决步骤**：

1. **检查用户角色**：
```python
# Django shell
>>> from users.models import User
>>> user = User.objects.get(email='user@example.com')
>>> print(f"Is superuser: {user.is_superuser}")
>>> print(f"Is tenant admin: {getattr(user, 'is_tenant_admin', False)}")
```

2. **检查租户关联**：
```python
# 确认用户属于正确的租户
>>> print(f"User tenant: {user.tenant}")
>>> print(f"User tenant ID: {user.tenant_id}")
```

3. **测试权限**：
```bash
# 使用正确的用户token测试API
curl -H "Authorization: Bearer <correct-token>" \
     http://localhost:8000/api/v1/feedbacks/software/
```

#### 问题5：附件上传失败

**症状**：
- 文件上传返回413或415错误
- 附件无法显示

**解决方案**：

1. **检查文件大小**（限制10MB）：
```bash
ls -lh /path/to/file.jpg
# 确保小于10MB
```

2. **检查文件类型**：
支持的格式：jpg, jpeg, png, gif, pdf, doc, docx, txt, log, zip

3. **检查媒体文件配置**：
```python
# core/settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 确保媒体目录存在且可写
```

4. **检查Nginx配置**（生产环境）：
```nginx
client_max_body_size 10M;  # 允许10MB文件上传
```

---

## 📈 性能优化

### 1. Redis性能优化

#### 连接池配置
```python
# core/settings.py

# 连接池设置
CELERY_BROKER_POOL_LIMIT = 10
CELERY_BROKER_CONNECTION_TIMEOUT = 30

# 对于高延迟网络
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
}

# 启用压缩（慢速网络）
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'
```

#### 任务优化
```python
# 限制worker并发
celery -A core worker -l info --concurrency=4

# 限制每个worker处理的任务数
celery -A core worker -l info --max-tasks-per-child=1000

# 设置任务超时
CELERY_TASK_TIME_LIMIT = 300  # 5分钟
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4分钟警告
```

### 2. 数据库优化

#### 索引优化
系统已自动创建必要的索引：
```sql
-- 主要索引
CREATE INDEX feedback_fe_tenant__d5e0dd_idx ON feedback_feedback (tenant_id, status);
CREATE INDEX feedback_fe_softwar_c6e970_idx ON feedback_feedback (software_id, status);
CREATE INDEX feedback_fe_created_84c297_idx ON feedback_feedback (created_at);
```

#### 查询优化
```python
# 使用select_related减少查询
feedback = Feedback.objects.select_related(
    'software', 'software_version', 'user'
).get(pk=1)

# 使用prefetch_related优化多对多查询
feedbacks = Feedback.objects.prefetch_related(
    'replies', 'attachments', 'votes'
).filter(software=1)
```

### 3. 缓存策略

#### 软件列表缓存（推荐）
```python
# 缓存软件列表（不常变动）
from django.core.cache import cache

def get_software_list():
    cache_key = f'software_list_tenant_{tenant_id}'
    software_list = cache.get(cache_key)
    
    if software_list is None:
        software_list = Software.objects.filter(
            tenant=tenant,
            is_active=True
        ).select_related('category')
        cache.set(cache_key, software_list, 300)  # 缓存5分钟
    
    return software_list
```

---

## 🔄 备份和恢复

### 1. 数据备份

#### 备份数据库表
```bash
# MySQL备份反馈相关表
mysqldump -u username -p database_name \
  feedback_software_category \
  feedback_software \
  feedback_software_version \
  feedback_feedback \
  feedback_reply \
  feedback_attachment \
  feedback_vote \
  feedback_email_log \
  feedback_email_template \
  feedback_status_history \
  > feedback_system_backup.sql
```

#### 备份媒体文件
```bash
# 备份上传的文件
tar -czf media_backup.tar.gz media/feedbacks/
```

### 2. 数据恢复

#### 恢复数据库
```bash
# 恢复表结构和数据
mysql -u username -p database_name < feedback_system_backup.sql
```

#### 恢复媒体文件
```bash
# 恢复媒体文件
tar -xzf media_backup.tar.gz
```

### 3. Redis备份（如果使用）

#### 备份Redis数据
```bash
# 备份Redis
redis-cli --rdb feedback_redis_backup.rdb

# 或者保存当前状态
redis-cli BGSAVE
```

---

## 📊 使用统计分析

### 1. 通过Django Admin查看

访问：`Admin → FEEDBACKS`

**各模块统计**：
- **Feedbacks**：总反馈数、按状态分布、按类型分布
- **Software**：软件数量、反馈统计
- **Feedback replies**：回复数量、邮件发送统计
- **Feedback votes**：投票统计

### 2. 通过API获取

```bash
# 获取完整统计
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8000/api/v1/feedbacks/statistics/"

# 按软件统计
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8000/api/v1/feedbacks/statistics/?software=1"

# 按时间范围统计
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8000/api/v1/feedbacks/statistics/?date_from=2025-01-01&date_to=2025-01-31"
```

### 3. 自定义报表

#### Python脚本示例
```python
#!/usr/bin/env python
# generate_report.py

import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from feedbacks.models import Feedback, Software
from django.db.models import Count, Q

def generate_monthly_report(tenant_id, year, month):
    """生成月度反馈报告"""
    
    # 查询条件
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    feedbacks = Feedback.objects.filter(
        tenant_id=tenant_id,
        created_at__gte=start_date,
        created_at__lt=end_date
    )
    
    # 统计数据
    stats = {
        'total': feedbacks.count(),
        'by_type': dict(feedbacks.values('feedback_type').annotate(count=Count('id'))),
        'by_status': dict(feedbacks.values('status').annotate(count=Count('id'))),
        'by_priority': dict(feedbacks.values('priority').annotate(count=Count('id'))),
        'resolved': feedbacks.filter(status='resolved').count(),
    }
    
    # 按软件统计
    software_stats = feedbacks.values('software__name').annotate(count=Count('id'))
    stats['by_software'] = {item['software__name']: item['count'] for item in software_stats}
    
    print(f"=== {year}-{month:02d} 月度反馈报告 ===")
    print(f"总反馈数：{stats['total']}")
    print(f"已解决：{stats['resolved']}")
    print(f"解决率：{stats['resolved'] / stats['total'] * 100:.1f}%" if stats['total'] > 0 else "N/A")
    print("\n按类型分布：")
    for type_name, count in stats['by_type'].items():
        print(f"  {type_name}: {count}")
    
    return stats

# 使用示例
if __name__ == '__main__':
    report = generate_monthly_report(tenant_id=1, year=2025, month=1)
```

---

## 🎯 最佳实践

### 1. 系统部署最佳实践

#### 推荐配置组合

**生产环境**：
```python
# core/settings.py

# 使用Upstash Redis（免费且稳定）
CELERY_BROKER_URL = os.getenv('REDIS_URL')  # Upstash连接

# 启用容错机制
FEEDBACK_EMAIL_FALLBACK_ENABLED = True

# 启用监控中间件
MIDDLEWARE += [
    'feedbacks.middleware.RedisMonitoringMiddleware',
]

# 设置合理的超时
CELERY_TASK_TIME_LIMIT = 300
CELERY_BROKER_CONNECTION_TIMEOUT = 30

# 配置任务队列
CELERY_TASK_ROUTES = {
    'feedbacks.tasks.*': {'queue': 'feedbacks'},
}
```

**开发环境**：
```python
# 简化配置，使用数据库broker
CELERY_BROKER_URL = 'django-db'
CELERY_RESULT_BACKEND = 'django-db'
```

### 2. 邮件配置最佳实践

#### QQ邮箱配置
```python
# core/settings.py

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')      # 你的QQ邮箱
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')  # QQ邮箱应用专用密码
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# 前端链接配置
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://your-domain.com')
```

#### Gmail配置
```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# 使用应用专用密码
```

#### 企业邮箱配置
```python
EMAIL_HOST = 'smtp.exmail.qq.com'  # 腾讯企业邮
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

### 3. 安全最佳实践

#### 环境变量管理
```bash
# .env文件
REDIS_URL=rediss://:password@endpoint.upstash.io:6379
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-specific-password
FRONTEND_URL=https://your-domain.com
SECRET_KEY=your-django-secret-key

# 设置文件权限
chmod 600 .env

# 添加到.gitignore
echo ".env" >> .gitignore
```

#### 生产环境安全
```python
# core/settings.py

# 生产环境配置
if not DEBUG:
    # 强制HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    
    # 安全cookie
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Redis安全连接
    CELERY_BROKER_USE_SSL = {
        'ssl_cert_reqs': 'CERT_REQUIRED',
    }
```

### 4. 监控最佳实践

#### 定期健康检查
```bash
# 添加到crontab
*/10 * * * * cd /path/to/project && python manage.py check_health > /var/log/feedback_health.log 2>&1

# 每天生成报告
0 9 * * * cd /path/to/project && python generate_report.py
```

#### 日志监控
```bash
# 监控容错事件
tail -f /var/log/django/app.log | grep -i "降级\|fallback\|redis"

# 监控邮件发送
tail -f /var/log/celery/worker.log | grep -i "email\|mail"
```

#### 系统监控脚本
```python
#!/usr/bin/env python
# monitor.py

import requests
import time
import smtplib
from email.message import EmailMessage

def check_system_health():
    try:
        response = requests.get(
            'http://localhost:8000/api/v1/feedbacks/health/',
            headers={'Authorization': 'Bearer <admin-token>'},
            timeout=10
        )
        
        if response.status_code == 200:
            health = response.json()
            
            if health['status'] != 'healthy':
                send_alert(f"系统状态异常: {health['status']}")
                
            if not health['components']['redis']['available']:
                send_alert("Redis不可用，系统运行在降级模式")
                
        else:
            send_alert(f"健康检查API返回错误: {response.status_code}")
            
    except Exception as e:
        send_alert(f"健康检查失败: {str(e)}")

def send_alert(message):
    # 发送告警邮件的逻辑
    pass

if __name__ == '__main__':
    while True:
        check_system_health()
        time.sleep(300)  # 每5分钟检查
```

---

## 📋 日常维护

### 1. 定期维护任务

#### 清理旧数据
```bash
# 手动清理90天前的邮件日志
python manage.py shell
```

```python
from feedbacks.models import FeedbackEmailLog
from datetime import timedelta
from django.utils import timezone

# 删除90天前的日志
cutoff_date = timezone.now() - timedelta(days=90)
deleted_count = FeedbackEmailLog.objects.filter(
    created_at__lt=cutoff_date
).delete()[0]

print(f"已删除 {deleted_count} 条旧邮件日志")
```

#### 更新软件统计
```bash
# Django shell
from feedbacks.models import Software

for software in Software.objects.all():
    software.update_statistics()
    print(f"已更新 {software.name} 的统计数据")
```

#### 重试失败的邮件
```bash
# Django shell
from feedbacks.models import FeedbackEmailLog
from feedbacks.tasks import send_feedback_reply_email

# 获取失败的回复邮件
failed_logs = FeedbackEmailLog.objects.filter(
    email_type='reply',
    status='failed',
    retry_count__lt=3
)

for log in failed_logs:
    if log.feedback:
        # 重新发送
        task = send_feedback_reply_email.delay(log.feedback.replies.first().id)
        print(f"重新发送邮件任务: {task.id}")
```

### 2. 系统升级

#### 代码更新后的步骤
```bash
# 1. 停止Celery worker
pkill -f "celery worker"
pkill -f "celery beat"

# 2. 更新代码
git pull origin main

# 3. 安装新依赖
pip install -r requirements.txt

# 4. 运行迁移
python manage.py migrate

# 5. 收集静态文件
python manage.py collectstatic --noinput

# 6. 重启服务
celery -A core worker -l info --queue=feedbacks,celery --detach
celery -A core beat -l info --detach
sudo systemctl restart gunicorn  # 或其他WSGI服务器

# 7. 检查健康状态
python manage.py check_health --verbose
```

---

## 📱 前端集成示例

### React集成

#### 安装依赖
```bash
npm install axios
```

#### API服务封装
```javascript
// services/feedbackAPI.js
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1/feedbacks';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 自动添加认证头
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 监控系统状态
api.interceptors.response.use(
  (response) => {
    // 检查系统模式
    const systemMode = response.headers['x-system-mode'];
    const redisStatus = response.headers['x-redis-status'];
    
    if (systemMode === 'sync') {
      console.warn('System is running in sync mode');
      // 可以显示全局提示
      window.dispatchEvent(new CustomEvent('systemSlowMode', {
        detail: { mode: systemMode, redis: redisStatus }
      }));
    }
    
    return response;
  },
  (error) => {
    // 错误处理
    return Promise.reject(error);
  }
);

export const feedbackAPI = {
  // 软件管理
  getSoftwareList: () => api.get('/software/'),
  createSoftware: (data) => api.post('/software/', data),
  
  // 反馈管理
  getFeedbackList: (params = {}) => api.get('/feedbacks/', { params }),
  getFeedback: (id) => api.get(`/feedbacks/${id}/`),
  createFeedback: (data) => api.post('/feedbacks/', data),
  updateFeedback: (id, data) => api.patch(`/feedbacks/${id}/`, data),
  
  // 反馈操作
  changeStatus: (id, status, reason) => 
    api.patch(`/feedbacks/${id}/status/`, { status, reason }),
  addReply: (feedbackId, content, isInternal = false) =>
    api.post(`/feedbacks/${feedbackId}/replies/`, { 
      content, 
      is_internal_note: isInternal 
    }),
  vote: (feedbackId, voteType) => 
    api.post(`/feedbacks/${feedbackId}/vote/`, { vote_type: voteType }),
  
  // 文件上传
  uploadAttachment: (feedbackId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/feedbacks/${feedbackId}/attachments/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  // 统计数据
  getStatistics: (params = {}) => api.get('/statistics/', { params }),
  
  // 系统健康
  getSystemHealth: () => api.get('/health/'),
};
```

#### React组件示例

**反馈提交组件**：
```jsx
// components/FeedbackForm.jsx
import React, { useState, useEffect } from 'react';
import { feedbackAPI } from '../services/feedbackAPI';

function FeedbackForm() {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    feedback_type: 'bug',
    priority: 'medium',
    software: '',
    software_version: '',
    contact_email: '',
    contact_name: ''
  });
  const [softwareList, setSoftwareList] = useState([]);
  const [versions, setVersions] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [systemMode, setSystemMode] = useState('async');

  useEffect(() => {
    loadSoftwareList();
    
    // 监听系统模式变化
    const handleSystemMode = (event) => {
      setSystemMode(event.detail.mode);
    };
    
    window.addEventListener('systemSlowMode', handleSystemMode);
    return () => window.removeEventListener('systemSlowMode', handleSystemMode);
  }, []);

  const loadSoftwareList = async () => {
    try {
      const response = await feedbackAPI.getSoftwareList();
      setSoftwareList(response.data.results);
    } catch (error) {
      console.error('Failed to load software list:', error);
    }
  };

  const handleSoftwareChange = async (softwareId) => {
    setFormData({ ...formData, software: softwareId, software_version: '' });
    
    if (softwareId) {
      try {
        const response = await feedbackAPI.getSoftware(softwareId);
        setVersions(response.data.versions);
      } catch (error) {
        console.error('Failed to load versions:', error);
      }
    } else {
      setVersions([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const response = await feedbackAPI.createFeedback({
        ...formData,
        environment_info: {
          os: navigator.platform,
          user_agent: navigator.userAgent,
          screen_resolution: `${screen.width}x${screen.height}`,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        }
      });

      alert('反馈提交成功！');
      if (!response.data.user && !response.data.email_verified) {
        alert('请检查您的邮箱，点击验证链接以接收后续通知。');
      }
      
      // 重置表单
      setFormData({
        title: '',
        description: '',
        feedback_type: 'bug',
        priority: 'medium',
        software: '',
        software_version: '',
        contact_email: '',
        contact_name: ''
      });
      
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('提交失败：' + (error.response?.data?.error || error.message));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="feedback-form">
      {systemMode === 'sync' && (
        <div className="alert alert-warning">
          ⚠️ 系统当前运行在同步模式，提交可能需要稍长时间，请耐心等待。
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>软件产品 *</label>
          <select 
            value={formData.software} 
            onChange={(e) => handleSoftwareChange(e.target.value)}
            required
          >
            <option value="">请选择软件</option>
            {softwareList.map(software => (
              <option key={software.id} value={software.id}>
                {software.name} ({software.current_version || 'N/A'})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>软件版本</label>
          <select 
            value={formData.software_version} 
            onChange={(e) => setFormData({...formData, software_version: e.target.value})}
          >
            <option value="">选择版本（可选）</option>
            {versions.map(version => (
              <option key={version.id} value={version.id}>
                {version.version} ({version.release_date})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>反馈类型 *</label>
          <select 
            value={formData.feedback_type} 
            onChange={(e) => setFormData({...formData, feedback_type: e.target.value})}
          >
            <option value="bug">Bug报告</option>
            <option value="feature">功能建议</option>
            <option value="improvement">改进建议</option>
            <option value="question">使用问题</option>
            <option value="other">其他</option>
          </select>
        </div>

        <div className="form-group">
          <label>优先级 *</label>
          <select 
            value={formData.priority} 
            onChange={(e) => setFormData({...formData, priority: e.target.value})}
          >
            <option value="low">低</option>
            <option value="medium">中</option>
            <option value="high">高</option>
            <option value="critical">紧急</option>
          </select>
        </div>

        <div className="form-group">
          <label>标题 *</label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({...formData, title: e.target.value})}
            placeholder="简要描述问题或建议"
            required
          />
        </div>

        <div className="form-group">
          <label>详细描述 *</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            placeholder="详细描述问题的具体情况、重现步骤、期望结果等"
            rows={6}
            required
          />
        </div>

        <div className="form-group">
          <label>联系邮箱 *</label>
          <input
            type="email"
            value={formData.contact_email}
            onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
            placeholder="用于接收回复和通知"
            required
          />
        </div>

        <div className="form-group">
          <label>姓名</label>
          <input
            type="text"
            value={formData.contact_name}
            onChange={(e) => setFormData({...formData, contact_name: e.target.value})}
            placeholder="您的姓名（可选）"
          />
        </div>

        <button 
          type="submit" 
          disabled={submitting}
          className="btn btn-primary"
        >
          {submitting ? '提交中...' : '提交反馈'}
        </button>
        
        {submitting && systemMode === 'sync' && (
          <p className="text-warning">
            ⏱️ 系统正在同步发送邮件，请稍候...
          </p>
        )}
      </form>
    </div>
  );
}

export default FeedbackForm;
```

**系统状态监控组件**：
```jsx
// components/SystemStatusBanner.jsx
import React, { useState, useEffect } from 'react';
import { feedbackAPI } from '../services/feedbackAPI';

function SystemStatusBanner() {
  const [systemHealth, setSystemHealth] = useState(null);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    checkSystemHealth();
    
    // 每5分钟检查一次
    const interval = setInterval(checkSystemHealth, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const checkSystemHealth = async () => {
    try {
      const response = await feedbackAPI.getSystemHealth();
      setSystemHealth(response.data);
      setShowBanner(response.data.status !== 'healthy');
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };

  if (!showBanner || !systemHealth) {
    return null;
  }

  return (
    <div className={`alert ${systemHealth.status === 'degraded' ? 'alert-warning' : 'alert-danger'}`}>
      <div className="d-flex justify-content-between align-items-center">
        <div>
          <strong>系统状态提醒</strong>
          {systemHealth.status === 'degraded' ? (
            <span> - 系统运行在降级模式，响应可能较慢</span>
          ) : (
            <span> - 系统状态异常</span>
          )}
        </div>
        <button 
          className="btn btn-sm btn-outline-secondary"
          onClick={() => setShowBanner(false)}
        >
          关闭
        </button>
      </div>
      
      {systemHealth.recommendations && systemHealth.recommendations.length > 0 && (
        <div className="mt-2">
          <small>建议：{systemHealth.recommendations.join('，')}</small>
        </div>
      )}
    </div>
  );
}

export default SystemStatusBanner;
```

---

## 🛠️ 开发和调试

### 1. 本地开发环境

#### 快速启动脚本
创建`start_dev.sh`：
```bash
#!/bin/bash
# start_dev.sh

echo "启动开发环境..."

# 检查依赖
echo "检查依赖..."
pip install -r requirements.txt

# 数据库迁移
echo "数据库迁移..."
python manage.py migrate

# 初始化模板
echo "初始化邮件模板..."
python manage.py init_feedback_templates

# 检查健康状态
echo "系统健康检查..."
python manage.py check_health

# 启动Redis（如果需要）
if ! redis-cli ping > /dev/null 2>&1; then
    echo "启动Redis..."
    if command -v docker &> /dev/null; then
        docker run -d -p 6379:6379 redis:latest
    else
        echo "请手动启动Redis或配置为数据库broker模式"
    fi
fi

# 启动Celery Worker
echo "启动Celery Worker..."
celery -A core worker -l info --detach

# 启动Django
echo "启动Django服务器..."
python manage.py runserver 0.0.0.0:8000

echo "开发环境启动完成！"
echo "API文档：http://localhost:8000/api/v1/docs/"
echo "管理后台：http://localhost:8000/admin/"
```

#### 调试模式
```python
# core/settings.py

# 开发环境配置
if DEBUG:
    # 邮件输出到控制台
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    
    # Celery调试
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_TASK_ALWAYS_EAGER = True  # 同步执行任务，便于调试
    
    # 详细日志
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'feedbacks': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
        },
    }
```

### 2. 测试工具

#### 使用cURL测试

**提交反馈**：
```bash
curl -X POST http://localhost:8000/api/v1/feedbacks/feedbacks/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试反馈",
    "description": "这是一个测试",
    "feedback_type": "bug",
    "priority": "medium",
    "software": 1,
    "contact_email": "test@example.com"
  }'
```

**获取反馈列表**：
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/feedbacks/feedbacks/
```

#### 使用Python测试

```python
#!/usr/bin/env python
# test_api.py

import requests
import json

BASE_URL = 'http://localhost:8000/api/v1/feedbacks'

def test_anonymous_feedback():
    """测试匿名反馈提交"""
    data = {
        "title": "测试匿名反馈",
        "description": "这是一个测试",
        "feedback_type": "bug",
        "priority": "medium",
        "software": 1,
        "contact_email": "test@example.com"
    }
    
    response = requests.post(f'{BASE_URL}/feedbacks/', json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 检查响应头
    print(f"System Mode: {response.headers.get('X-System-Mode', 'unknown')}")
    print(f"Redis Status: {response.headers.get('X-Redis-Status', 'unknown')}")

def test_health_check():
    """测试健康检查（需要管理员token）"""
    headers = {'Authorization': 'Bearer <admin-token>'}
    response = requests.get(f'{BASE_URL}/health/', headers=headers)
    
    if response.status_code == 200:
        health = response.json()
        print("系统健康状态：", health['status'])
        print("Redis状态：", health['components']['redis']['available'])
    else:
        print("健康检查失败：", response.status_code)

if __name__ == '__main__':
    print("=== API测试 ===")
    test_anonymous_feedback()
    print("\n=== 健康检查 ===")
    test_health_check()
```

---

## 🚨 故障处理手册

### 紧急故障处理流程

#### 1. 系统无响应

**症状**：API请求超时或返回500错误

**处理步骤**：
```bash
# 1. 检查系统状态
python manage.py check_health

# 2. 检查Django进程
ps aux | grep "manage.py runserver"

# 3. 检查数据库连接
python manage.py dbshell
mysql> SELECT 1;

# 4. 检查日志
tail -f /var/log/django/error.log

# 5. 重启服务
sudo systemctl restart gunicorn
# 或
pkill -f "manage.py runserver"
python manage.py runserver &
```

#### 2. 邮件发送故障

**症状**：用户报告未收到邮件

**处理步骤**：
```bash
# 1. 检查邮件配置
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])

# 2. 检查Celery worker
celery -A core inspect active

# 3. 查看失败邮件
python manage.py shell
>>> from feedbacks.models import FeedbackEmailLog
>>> failed = FeedbackEmailLog.objects.filter(status='failed')
>>> for log in failed:
...     print(f"Error: {log.error_message}")

# 4. 重试失败邮件
>>> from feedbacks.tasks import send_feedback_reply_email
>>> task = send_feedback_reply_email.delay(reply_id)
>>> print(task.get())
```

#### 3. Redis连接故障

**症状**：
- 健康检查显示Redis不可用
- 系统运行在同步模式

**处理步骤**：

1. **检查Redis状态**：
```bash
# 检查系统健康
python manage.py check_health --verbose

# 如果使用Upstash
redis-cli -u $REDIS_URL ping
```

2. **临时解决方案**：
```bash
# 系统已自动降级，可继续使用
# 用户可能感觉稍慢，但功能正常
```

3. **恢复Redis**：
```bash
# 本地Redis
sudo systemctl start redis

# Upstash检查
# 登录dashboard检查服务状态
```

4. **验证恢复**：
```bash
# 等待60秒后检查
python manage.py check_health
# 应该显示：[OK] Primary mode: Async (via Redis)
```

---

## 📋 维护检查清单

### 日常检查（每日）

- [ ] 运行健康检查：`python manage.py check_health`
- [ ] 检查邮件发送状态：查看Django Admin中的Email Logs
- [ ] 检查Celery worker状态：`celery -A core inspect active`
- [ ] 检查错误日志：`tail -f /var/log/django/error.log`

### 周检查

- [ ] 检查反馈处理情况：统计待处理反馈数量
- [ ] 检查存储使用：`du -sh media/feedbacks/`
- [ ] 检查数据库大小：查看反馈相关表的记录数
- [ ] 更新软件版本信息：添加新版本到系统

### 月检查

- [ ] 清理旧邮件日志：手动运行清理任务
- [ ] 备份重要数据：导出数据库和媒体文件
- [ ] 检查系统性能：分析响应时间和并发能力
- [ ] 更新文档：根据使用情况更新配置文档

---

## 📞 技术支持

### 获取帮助的步骤

1. **查看相关文档**：
   - 配置问题 → `Redis_FAQ_ZH.md`
   - 容错问题 → `完整的Redis容错方案_ZH.md`
   - API使用 → `Frontend_Integration_Guide.md`
   - 部署问题 → `Celery_Deployment_Guide.md`

2. **运行诊断命令**：
```bash
python manage.py check_health --verbose > system_status.log
```

3. **收集错误信息**：
```bash
# 收集最近的错误日志
tail -n 100 /var/log/django/error.log > error.log
tail -n 100 /var/log/celery/worker.log > celery.log
```

4. **测试系统功能**：
```bash
# 测试基本功能
curl -X POST http://localhost:8000/api/v1/feedbacks/feedbacks/ \
  -H "Content-Type: application/json" \
  -d '{"title":"测试","software":1,"contact_email":"test@example.com"}'
```

### 常用诊断命令

```bash
# 系统整体状态
python manage.py check_health --verbose

# 检查数据库连接
python manage.py dbshell

# 检查Celery状态
celery -A core inspect ping
celery -A core inspect active
celery -A core inspect stats

# 测试Redis连接
python -c "from feedbacks.utils import RedisHealthChecker; print('Redis:', RedisHealthChecker.is_redis_available())"

# 测试邮件发送
python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test', 'Test', 'from@example.com', ['to@example.com'])"
```

---

## 📝 配置文件总览

### 主要配置文件

#### 1. core/settings.py（主配置文件）

**必需配置**：
```python
# 应用配置
INSTALLED_APPS = [
    # ... 其他apps
    'feedbacks',  # 反馈系统
]

# URL配置
# 在 core/urls.py 中已自动包含

# Redis/Celery配置（三选一）
# 方案1：Upstash Redis（推荐）
CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')

# 方案2：本地Redis
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# 方案3：数据库Broker
# CELERY_BROKER_URL = 'django-db'
# CELERY_RESULT_BACKEND = 'django-db'
# INSTALLED_APPS += ['django_celery_results']

# 邮件配置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# 前端URL
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
```

#### 2. .env文件（敏感配置）

```bash
# .env文件内容

# Redis配置（Upstash示例）
REDIS_URL=rediss://:AR8EAAImcDIyNDM5Y2MwOWY0OWU0ZDFmYTdkOWNhOWJjMDAxNTA2OXAyNzk0MA@classic-salmon-7940.upstash.io:6379

# 邮件配置
EMAIL_HOST_USER=your-email@qq.com
EMAIL_HOST_PASSWORD=your-qq-app-password

# 前端地址
FRONTEND_URL=https://your-frontend-domain.com

# Django密钥
SECRET_KEY=your-secret-key

# 数据库配置（如需要）
DATABASE_URL=mysql://user:password@host:port/dbname
```

#### 3. requirements.txt（依赖配置）

已添加的反馈系统依赖：
```text
# Async Task Processing (Celery)
celery==5.3.4
redis==5.0.1
django-celery-beat==2.5.0
django-celery-results==2.5.1
django-ratelimit==4.1.0
```

---

## ✅ 完整配置检查清单

### 安装检查

- [ ] **依赖安装**：`pip install -r requirements.txt`
- [ ] **数据库迁移**：`python manage.py migrate`
- [ ] **模板初始化**：`python manage.py init_feedback_templates`

### 配置检查

- [ ] **INSTALLED_APPS**：包含'feedbacks'
- [ ] **URLs配置**：core/urls.py已包含反馈路由
- [ ] **Redis配置**：CELERY_BROKER_URL已设置
- [ ] **邮件配置**：EMAIL_HOST等已配置
- [ ] **环境变量**：.env文件已创建

### 运行检查

- [ ] **健康检查**：`python manage.py check_health`显示正常
- [ ] **API访问**：http://localhost:8000/api/v1/docs/ 可访问
- [ ] **管理后台**：http://localhost:8000/admin/ 可访问
- [ ] **Redis状态**：显示available或降级模式正常

### 功能检查

- [ ] **提交反馈**：匿名提交成功
- [ ] **邮件接收**：验证邮件能收到
- [ ] **管理员回复**：回复邮件能收到
- [ ] **文件上传**：附件上传成功
- [ ] **投票功能**：投票计数正确

---

## 🎉 使用手册总结

### 🎯 核心要点

1. **Redis配置是关键**：
   - 推荐Upstash（免费、简单）
   - 本地Redis适用于开发
   - 数据库broker作为备选

2. **系统具备完整容错**：
   - Redis断开自动降级
   - 邮件一定会发送
   - 系统持续可用

3. **三种运行模式**：
   - 异步模式（Redis）- 最佳性能
   - 半异步模式（数据库broker）- 良好性能
   - 同步模式（降级）- 容错保障

### 🚀 快速开始

```bash
# 最简单的启动（无需Redis）
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 推荐配置（5分钟设置Upstash）
# 1. 注册 https://upstash.com
# 2. 创建Redis数据库
# 3. 复制连接URL到.env
# 4. 启动：celery -A core worker -l info &
```

### 📚 文档导航

- **快速入门**：`Quick_Start_Guide.md`
- **Redis配置**：`Redis_FAQ_ZH.md`
- **容错机制**：`完整的Redis容错方案_ZH.md`
- **API文档**：`Frontend_Integration_Guide.md`
- **部署指南**：`Celery_Deployment_Guide.md`

### ⚡ 关键命令

```bash
# 系统健康检查
python manage.py check_health --verbose

# 初始化邮件模板
python manage.py init_feedback_templates

# 启动Celery
celery -A core worker -l info
```

**系统已可用，立即开始体验！** 🚀

---

**文档最后更新**：2025-10-22  
**版本**：v1.0  
**状态**：生产就绪
