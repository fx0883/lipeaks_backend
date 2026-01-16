# 打卡系统 Admin API 文档

本文档详细说明了打卡系统(check_system)管理端的所有API接口，包括任务类型、任务、打卡记录、任务模板和21天打卡周期的管理功能。

---

## 通用说明

### 基础URL
```
http://localhost:8000/api/v1/check-system/
```

### 认证方式
所有API需要JWT认证，请在Header中添加：
```
Authorization: Bearer {JWT_TOKEN}
```

### 租户ID
多租户环境下，需要在Header中指定租户ID：
```
X-Tenant-ID: {TENANT_ID}
```

### 多语言支持
打卡系统支持多语言，在Header中添加语言标识获取对应翻译：
```
Accept-Language: zh-hans  # 简体中文
Accept-Language: en       # 英文
Accept-Language: zh-hant  # 繁体中文
```

**返回字段说明**：
- `name`, `description`, `goal`, `tip`, `quote`: 原始值（通常为英文）
- `translated_name`, `translated_description`, `translated_goal`, `translated_tip`, `translated_quote`: 根据 Accept-Language 返回的翻译值
- `translations`: 包含所有语言翻译的 JSON 对象

### 登录获取Token

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_jin",
    "password": "Admin123",
    "tenant_id": 1
  }'
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 2,
      "username": "admin_jin",
      "email": "admin_jin@qq.com",
      "is_admin": true,
      "is_super_admin": false,
      "is_member": false,
      "tenant_id": 1,
      "tenant_name": "金sir"
    }
  }
}
```

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

### 分页格式
列表接口返回标准分页格式：
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 21,
      "next": "http://localhost:8000/api/v1/check-system/task-categories/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 3
    },
    "results": [...]
  }
}
```

### 错误码说明
- 2xxx: 成功
- 4000: 请求参数错误
- 4001: 未认证
- 4003: 权限不足
- 4004: 资源不存在
- 4100: 租户操作失败
- 5000: 服务器内部错误

---

## 一、任务类型(TaskCategory) API

任务类型用于定义打卡任务的分类，如"早起"、"运动"等。系统预设类型(is_system=true)不可修改。

### 1.1 获取任务类型列表

**接口**: `GET /api/v1/check-system/task-categories/`

**权限**: 租户管理员

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| is_system | bool | 否 | 是否系统预设 |
| form_type | string | 否 | 表单类型: text, sleep等 |
| search | string | 否 | 搜索名称或描述 |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认10 |

**curl命令示例 (中文)**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/task-categories/?page=1&page_size=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: zh-hans"
```

**响应示例 (中文)**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 21,
      "next": "http://localhost:8000/api/v1/check-system/task-categories/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 3
    },
    "results": [
      {
        "id": 1,
        "name": "Awakening Self",
        "description": "Enhance self-awareness",
        "is_system": true,
        "icon": "🔮",
        "color": "#8B5CF6",
        "goal": "",
        "tip": "",
        "quote": "",
        "form_type": "text",
        "sort_order": 1,
        "translations": {
          "name": {"en": "Awakening Self", "zh-hans": "觉醒自我"},
          "description": {"en": "Enhance self-awareness", "zh-hans": "提升自我意识"}
        },
        "created_at": "2026-01-13T10:41:12.090845Z",
        "updated_at": "2026-01-14T15:36:00.000000Z",
        "translated_name": "觉醒自我",
        "translated_description": "提升自我意识",
        "translated_goal": "",
        "translated_tip": "",
        "translated_quote": ""
      },
      {
        "id": 2,
        "name": "Early Sleep",
        "description": "Regular sleep schedule",
        "is_system": true,
        "icon": "😴",
        "color": "#38BDF8",
        "goal": "",
        "tip": "",
        "quote": "",
        "form_type": "sleep",
        "sort_order": 2,
        "translations": {
          "name": {"en": "Early Sleep", "zh-hans": "早睡早起"},
          "description": {"en": "Regular sleep schedule", "zh-hans": "规律的睡眠作息"}
        },
        "created_at": "2026-01-13T10:41:12.093571Z",
        "updated_at": "2026-01-14T15:36:00.000000Z",
        "translated_name": "早睡早起",
        "translated_description": "规律的睡眠作息",
        "translated_goal": "",
        "translated_tip": "",
        "translated_quote": ""
      }
    ]
  }
}
```

---

### 1.2 获取任务类型详情

**接口**: `GET /api/v1/check-system/task-categories/{id}/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | int | 任务类型ID |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/task-categories/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "Awakening Self",
    "description": "Enhance self-awareness",
    "is_system": true,
    "icon": "🔮",
    "color": "#8B5CF6",
    "goal": "",
    "tip": "",
    "quote": "",
    "form_type": "text",
    "sort_order": 1,
    "translations": {},
    "created_at": "2026-01-13T10:41:12.090845Z",
    "updated_at": "2026-01-13T10:41:12.090862Z",
    "translated_name": "Awakening Self",
    "translated_description": "Enhance self-awareness"
  }
}
```

---

### 1.3 创建任务类型

**接口**: `POST /api/v1/check-system/task-categories/`

**权限**: 租户管理员

**请求体**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 类型名称 |
| description | string | 否 | 类型描述 |
| icon | string | 否 | 图标(emoji) |
| color | string | 否 | 颜色代码 |
| goal | string | 否 | 目标说明 |
| tip | string | 否 | 提示信息 |
| quote | string | 否 | 引用语 |
| form_type | string | 否 | 表单类型: text, sleep等 |
| sort_order | int | 否 | 排序顺序 |
| translations | object | 否 | 多语言翻译 |

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/check-system/task-categories/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "name": "冥想打卡",
    "description": "每日冥想练习",
    "icon": "🧘",
    "color": "#10B981",
    "form_type": "text",
    "sort_order": 100
  }'
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 22,
    "name": "冥想打卡",
    "description": "每日冥想练习",
    "is_system": false,
    "icon": "🧘",
    "color": "#10B981",
    "goal": "",
    "tip": "",
    "quote": "",
    "form_type": "text",
    "sort_order": 100,
    "translations": {},
    "created_at": "2026-01-14T10:00:00.000000Z",
    "updated_at": "2026-01-14T10:00:00.000000Z",
    "translated_name": "冥想打卡",
    "translated_description": "每日冥想练习"
  }
}
```

---

### 1.4 更新任务类型

**接口**: `PATCH /api/v1/check-system/task-categories/{id}/`

**权限**: 租户管理员

**注意**: 系统预设类型(is_system=true)不可修改

**curl命令示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/check-system/task-categories/22/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "name": "冥想练习",
    "description": "每日15分钟冥想"
  }'
```

---

### 1.5 删除任务类型

**接口**: `DELETE /api/v1/check-system/task-categories/{id}/`

**权限**: 租户管理员

**注意**: 系统预设类型(is_system=true)不可删除，删除为软删除

**curl命令示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/check-system/task-categories/22/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

---

## 二、任务(Task) API

任务是用户创建的具体打卡项目，关联到Member用户。

### 2.1 获取任务列表

**接口**: `GET /api/v1/check-system/tasks/`

**权限**: 租户管理员(查看租户内所有任务)

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| category | int | 否 | 类型ID过滤 |
| status | string | 否 | 状态过滤 |
| search | string | 否 | 搜索名称或描述 |
| page | int | 否 | 页码 |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/tasks/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 0,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": []
  }
}
```

**字段说明**:

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | int | 任务ID |
| name | string | 任务名称 |
| description | string | 任务描述 |
| category | int | 关联类型ID |
| category_name | string | 类型名称 |
| member | int | 关联成员ID |
| member_name | string | 成员名称 |
| start_date | date | 开始日期 |
| end_date | date | 结束日期 |
| status | string | 状态 |
| reminder | bool | 是否提醒 |
| reminder_time | time | 提醒时间 |
| frequency_type | string | 频率类型 |
| frequency_days | array | 频率天数 |

---

## 三、打卡记录(CheckRecord) API

打卡记录用于记录用户的打卡行为。

### 3.1 获取打卡记录列表

**接口**: `GET /api/v1/check-system/check-records/`

**权限**: 租户管理员(查看租户内所有记录)

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| task | int | 否 | 任务ID过滤 |
| theme | int | 否 | 主题ID过滤 |
| check_date | date | 否 | 打卡日期过滤 |
| delayed | bool | 否 | 是否延迟打卡 |
| page | int | 否 | 页码 |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/check-records/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 0,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": []
  }
}
```

**字段说明**:

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | int | 记录ID |
| task | int | 关联任务ID |
| task_name | string | 任务名称 |
| theme | int | 关联主题ID |
| theme_name | string | 主题名称 |
| member | int | 成员ID |
| member_name | string | 成员名称 |
| check_date | date | 打卡日期 |
| check_time | time | 打卡时间 |
| remarks | string | 备注 |
| comment | string | 评论 |
| completion_time | int | 完成时长(分钟) |
| extra_data | object | 额外数据 |
| delayed | bool | 是否延迟打卡 |

---

## 四、任务模板(TaskTemplate) API

任务模板用于预定义常用任务，方便用户快速创建任务。

### 4.1 获取任务模板列表

**接口**: `GET /api/v1/check-system/task-templates/`

**权限**: 租户管理员

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/task-templates/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 0,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": []
  }
}
```

**字段说明**:

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | int | 模板ID |
| name | string | 模板名称 |
| description | string | 模板描述 |
| category | int | 关联类型ID |
| category_name | string | 类型名称 |
| is_system | bool | 是否系统预设 |
| translations | object | 多语言翻译 |
| reminder | bool | 是否提醒 |
| reminder_time | time | 提醒时间 |
| translated_name | string | 当前语言名称 |
| translated_description | string | 当前语言描述 |

### 4.2 创建任务模板

**接口**: `POST /api/v1/check-system/task-templates/`

**权限**: 租户管理员

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/check-system/task-templates/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "name": "每日阅读30分钟",
    "description": "培养阅读习惯",
    "category": 1,
    "reminder": true,
    "reminder_time": "21:00:00"
  }'
```

---

## 五、21天打卡周期(CheckinCycle) API

21天周期用于管理用户的打卡挑战。

### 5.1 获取周期列表

**接口**: `GET /api/v1/check-system/cycles/`

**权限**: 租户管理员(查看租户内所有周期)

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| is_active | bool | 否 | 是否活跃 |
| page | int | 否 | 页码 |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/cycles/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 0,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": []
  }
}
```

**字段说明**:

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | int | 周期ID |
| member | int | 成员ID |
| member_name | string | 成员名称 |
| start_date | date | 开始日期 |
| end_date | date | 结束日期(自动计算为start_date+21天) |
| selected_themes | array | 选中的主题ID列表 |
| is_active | bool | 是否活跃 |
| current_day | int | 当前是第几天 |
| progress | int | 进度百分比 |
| themes | array | 选中主题的详细信息 |

### 5.2 获取当前活跃周期

**接口**: `GET /api/v1/check-system/cycles/current/`

**权限**: 租户管理员

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/cycles/current/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

### 5.3 获取周期统计

**接口**: `GET /api/v1/check-system/cycles/{id}/stats/`

**权限**: 租户管理员

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/cycles/1/stats/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

**响应示例**:
```json
{
  "cycle_id": 1,
  "current_day": 5,
  "progress": 23,
  "total_checkins": 15,
  "unique_days": 5,
  "themes_completed": 3,
  "selected_themes_count": 5
}
```

---

## 六、数据字典

### 6.1 表单类型 (form_type)

| 值 | 说明 |
|---|------|
| text | 文本表单 |
| sleep | 睡眠表单 |
| exercise | 运动表单 |
| diet | 饮食表单 |

### 6.2 任务状态 (status)

| 值 | 说明 |
|---|------|
| active | 进行中 |
| completed | 已完成 |
| paused | 已暂停 |
| cancelled | 已取消 |

### 6.3 频率类型 (frequency_type)

| 值 | 说明 |
|---|------|
| daily | 每天 |
| weekly | 每周 |
| custom | 自定义 |

---

## 七、API路由总览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /task-categories/ | 获取任务类型列表 |
| POST | /task-categories/ | 创建任务类型 |
| GET | /task-categories/{id}/ | 获取任务类型详情 |
| PATCH | /task-categories/{id}/ | 更新任务类型 |
| DELETE | /task-categories/{id}/ | 删除任务类型 |
| GET | /tasks/ | 获取任务列表 |
| POST | /tasks/ | 创建任务 |
| GET | /tasks/{id}/ | 获取任务详情 |
| PATCH | /tasks/{id}/ | 更新任务 |
| DELETE | /tasks/{id}/ | 删除任务 |
| GET | /check-records/ | 获取打卡记录列表 |
| POST | /check-records/ | 创建打卡记录 |
| GET | /check-records/{id}/ | 获取打卡记录详情 |
| PATCH | /check-records/{id}/ | 更新打卡记录 |
| DELETE | /check-records/{id}/ | 删除打卡记录 |
| GET | /task-templates/ | 获取任务模板列表 |
| POST | /task-templates/ | 创建任务模板 |
| GET | /task-templates/{id}/ | 获取任务模板详情 |
| PATCH | /task-templates/{id}/ | 更新任务模板 |
| DELETE | /task-templates/{id}/ | 删除任务模板 |
| GET | /cycles/ | 获取周期列表 |
| POST | /cycles/ | 创建周期 |
| GET | /cycles/{id}/ | 获取周期详情 |
| GET | /cycles/current/ | 获取当前活跃周期 |
| GET | /cycles/{id}/stats/ | 获取周期统计 |
