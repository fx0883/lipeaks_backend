# 打卡系统 Member API 文档

本文档详细说明了打卡系统(check_system)成员端的所有API接口，提供给Member用户使用的打卡功能。

---

## 通用说明

### 基础URL
```
http://localhost:8000/api/v1/check-system/member/
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

### Member登录获取Token

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "username": "fx0883",
    "password": "Member123"
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
      "id": 3,
      "username": "fx0883",
      "nickname": "Felix",
      "email": "fx0883@example.com",
      "avatar": "http://localhost:8000/media/avatars/xxx.webp",
      "is_admin": false,
      "is_super_admin": false,
      "is_member": true,
      "is_sub_account": false,
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
      "next": "http://localhost:8000/api/v1/check-system/member/themes/?page=2",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 3
    },
    "results": [...]
  }
}
```

---

## 一、主题(Theme) API - 只读

主题是系统预设的打卡类型，Member用户只能查看，不能修改。

### 1.1 获取主题列表

**接口**: `GET /api/v1/check-system/member/themes/`

**权限**: Member用户

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| is_system | bool | 否 | 是否系统预设 |
| form_type | string | 否 | 表单类型过滤 |
| search | string | 否 | 搜索名称或描述 |
| page | int | 否 | 页码，默认1 |

**curl命令示例 (中文)**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/member/themes/" \
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
      "next": "http://localhost:8000/api/v1/check-system/member/themes/?page=2",
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

### 1.2 获取主题详情

**接口**: `GET /api/v1/check-system/member/themes/{id}/`

**权限**: Member用户

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/member/themes/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

---

## 二、任务(Task) API

Member用户可以创建、修改、删除自己的任务。

### 2.1 获取我的任务列表

**接口**: `GET /api/v1/check-system/member/tasks/`

**权限**: Member用户(只能看到自己的任务)

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| category | int | 否 | 类型ID过滤 |
| status | string | 否 | 状态过滤 |
| search | string | 否 | 搜索名称或描述 |
| ordering | string | 否 | 排序字段: created_at, start_date |
| page | int | 否 | 页码 |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/member/tasks/" \
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

### 2.2 创建任务

**接口**: `POST /api/v1/check-system/member/tasks/`

**权限**: Member用户

**请求体**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 任务名称 |
| description | string | 否 | 任务描述 |
| category | int | 是 | 关联类型ID |
| start_date | date | 否 | 开始日期 |
| end_date | date | 否 | 结束日期 |
| reminder | bool | 否 | 是否提醒 |
| reminder_time | time | 否 | 提醒时间 |
| frequency_type | string | 否 | 频率类型: daily, weekly, custom |
| frequency_days | array | 否 | 频率天数(用于custom类型) |

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/check-system/member/tasks/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "name": "每日阅读",
    "description": "阅读30分钟技术书籍",
    "category": 1,
    "start_date": "2026-01-14",
    "reminder": true,
    "reminder_time": "21:00:00",
    "frequency_type": "daily"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "每日阅读",
    "description": "阅读30分钟技术书籍",
    "category": 1,
    "category_name": "Awakening Self",
    "member": 3,
    "member_name": "fx0883",
    "start_date": "2026-01-14",
    "end_date": null,
    "status": "active",
    "reminder": true,
    "reminder_time": "21:00:00",
    "frequency_type": "daily",
    "frequency_days": null,
    "created_at": "2026-01-14T10:00:00.000000Z",
    "updated_at": "2026-01-14T10:00:00.000000Z"
  }
}
```

### 2.3 更新任务

**接口**: `PATCH /api/v1/check-system/member/tasks/{id}/`

**权限**: Member用户(只能修改自己的任务)

**curl命令示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/check-system/member/tasks/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "name": "每日阅读1小时",
    "reminder_time": "20:30:00"
  }'
```

### 2.4 删除任务

**接口**: `DELETE /api/v1/check-system/member/tasks/{id}/`

**权限**: Member用户(只能删除自己的任务)

**注意**: 删除为软删除

**curl命令示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/check-system/member/tasks/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

---

## 三、打卡(Checkin) API

Member用户可以创建、查看和管理自己的打卡记录。

### 3.1 获取我的打卡记录

**接口**: `GET /api/v1/check-system/member/checkins/`

**权限**: Member用户(只能看到自己的记录)

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| task | int | 否 | 任务ID过滤 |
| theme | int | 否 | 主题ID过滤 |
| check_date | date | 否 | 打卡日期过滤 |
| delayed | bool | 否 | 是否延迟打卡 |
| ordering | string | 否 | 排序: -check_date, -check_time |
| page | int | 否 | 页码 |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/member/checkins/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

### 3.2 创建打卡

**接口**: `POST /api/v1/check-system/member/checkins/`

**权限**: Member用户

**请求体**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| task | int | 条件 | 关联任务ID(与theme二选一) |
| theme | int | 条件 | 关联主题ID(与task二选一) |
| check_date | date | 是 | 打卡日期 |
| check_time | time | 否 | 打卡时间 |
| remarks | string | 否 | 备注 |
| comment | string | 否 | 评论 |
| completion_time | int | 否 | 完成时长(分钟) |
| extra_data | object | 否 | 额外数据 |
| delayed | bool | 否 | 是否延迟打卡 |

**curl命令示例 - 任务型打卡**:
```bash
curl -X POST "http://localhost:8000/api/v1/check-system/member/checkins/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "task": 1,
    "check_date": "2026-01-14",
    "check_time": "21:30:00",
    "remarks": "今天阅读了《代码整洁之道》第三章",
    "completion_time": 35
  }'
```

**curl命令示例 - 主题型打卡(21天挑战)**:
```bash
curl -X POST "http://localhost:8000/api/v1/check-system/member/checkins/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "theme": 2,
    "check_date": "2026-01-14",
    "check_time": "22:30:00",
    "remarks": "今天22:30准时入睡",
    "extra_data": {"sleep_time": "22:30"}
  }'
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "task": 1,
    "task_name": "每日阅读",
    "theme": null,
    "theme_name": null,
    "member": 3,
    "member_name": "fx0883",
    "check_date": "2026-01-14",
    "check_time": "21:30:00",
    "remarks": "今天阅读了《代码整洁之道》第三章",
    "comment": null,
    "completion_time": 35,
    "extra_data": null,
    "delayed": false,
    "created_at": "2026-01-14T21:30:00.000000Z",
    "updated_at": "2026-01-14T21:30:00.000000Z"
  }
}
```

**错误响应示例 - 重复打卡**:
```json
{
  "success": false,
  "code": 4000,
  "message": "您今天已经为该任务打过卡了",
  "data": null
}
```

### 3.3 获取今日打卡状态

**接口**: `GET /api/v1/check-system/member/checkins/today/`

**权限**: Member用户

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/member/checkins/today/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

**响应示例**:
```json
{
  "date": "2026-01-14",
  "total": 2,
  "records": [
    {
      "id": 1,
      "task": 1,
      "task_name": "每日阅读",
      "check_date": "2026-01-14",
      "check_time": "21:30:00"
    },
    {
      "id": 2,
      "theme": 2,
      "theme_name": "Early Sleep",
      "check_date": "2026-01-14",
      "check_time": "22:30:00"
    }
  ]
}
```

### 3.4 更新打卡记录

**接口**: `PATCH /api/v1/check-system/member/checkins/{id}/`

**权限**: Member用户(只能修改自己的记录)

**curl命令示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/check-system/member/checkins/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "remarks": "更新备注：阅读了第三章和第四章",
    "completion_time": 60
  }'
```

### 3.5 删除打卡记录

**接口**: `DELETE /api/v1/check-system/member/checkins/{id}/`

**权限**: Member用户(只能删除自己的记录)

**curl命令示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/check-system/member/checkins/1/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

---

## 四、21天周期(Cycle) API

Member用户可以创建和管理自己的21天打卡挑战周期。

### 4.1 获取我的周期列表

**接口**: `GET /api/v1/check-system/member/cycles/`

**权限**: Member用户(只能看到自己的周期)

**请求参数** (Query):

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| is_active | bool | 否 | 是否活跃 |
| ordering | string | 否 | 排序: -created_at, start_date |
| page | int | 否 | 页码 |

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/member/cycles/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

### 4.2 创建21天周期

**接口**: `POST /api/v1/check-system/member/cycles/`

**权限**: Member用户

**请求体**:

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| start_date | date | 否 | 开始日期(默认今天) |
| selected_themes | array | 是 | 选中的主题ID列表(最多选5个) |

**curl命令示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/check-system/member/cycles/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "start_date": "2026-01-14",
    "selected_themes": [1, 2, 3, 4, 5]
  }'
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "member": 3,
    "member_name": "fx0883",
    "start_date": "2026-01-14",
    "end_date": "2026-02-03",
    "selected_themes": [1, 2, 3, 4, 5],
    "is_active": true,
    "current_day": 1,
    "progress": 4,
    "themes": [
      {
        "id": 1,
        "name": "Awakening Self",
        "icon": "🔮",
        "color": "#8B5CF6"
      },
      {
        "id": 2,
        "name": "Early Sleep",
        "icon": "😴",
        "color": "#38BDF8"
      }
    ],
    "created_at": "2026-01-14T10:00:00.000000Z",
    "updated_at": "2026-01-14T10:00:00.000000Z"
  }
}
```

### 4.3 获取当前活跃周期

**接口**: `GET /api/v1/check-system/member/cycles/current/`

**权限**: Member用户

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/member/cycles/current/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "X-Tenant-ID: 1"
```

**响应示例 - 有活跃周期**:
```json
{
  "id": 1,
  "member": 3,
  "member_name": "fx0883",
  "start_date": "2026-01-14",
  "end_date": "2026-02-03",
  "selected_themes": [1, 2, 3, 4, 5],
  "is_active": true,
  "current_day": 5,
  "progress": 23,
  "themes": [...]
}
```

**响应示例 - 无活跃周期**:
```json
{
  "detail": "没有活跃的周期"
}
```

### 4.4 获取周期统计

**接口**: `GET /api/v1/check-system/member/cycles/{id}/stats/`

**权限**: Member用户(只能查看自己的周期)

**curl命令示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/check-system/member/cycles/1/stats/" \
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

**字段说明**:

| 字段名 | 类型 | 说明 |
|-------|------|------|
| cycle_id | int | 周期ID |
| current_day | int | 当前是第几天 |
| progress | int | 进度百分比 |
| total_checkins | int | 总打卡次数 |
| unique_days | int | 打卡天数 |
| themes_completed | int | 完成的主题数 |
| selected_themes_count | int | 选择的主题数 |

---

## 五、数据字典

### 5.1 表单类型 (form_type)

| 值 | 说明 |
|---|------|
| text | 文本表单(通用) |
| sleep | 睡眠表单 |
| exercise | 运动表单 |
| diet | 饮食表单 |

### 5.2 任务状态 (status)

| 值 | 说明 |
|---|------|
| active | 进行中 |
| completed | 已完成 |
| paused | 已暂停 |
| cancelled | 已取消 |

### 5.3 频率类型 (frequency_type)

| 值 | 说明 |
|---|------|
| daily | 每天 |
| weekly | 每周 |
| custom | 自定义 |

---

## 六、API路由总览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /member/themes/ | 获取主题列表(只读) |
| GET | /member/themes/{id}/ | 获取主题详情(只读) |
| GET | /member/tasks/ | 获取我的任务列表 |
| POST | /member/tasks/ | 创建任务 |
| GET | /member/tasks/{id}/ | 获取任务详情 |
| PATCH | /member/tasks/{id}/ | 更新任务 |
| DELETE | /member/tasks/{id}/ | 删除任务 |
| GET | /member/checkins/ | 获取我的打卡记录 |
| POST | /member/checkins/ | 创建打卡 |
| GET | /member/checkins/{id}/ | 获取打卡详情 |
| PATCH | /member/checkins/{id}/ | 更新打卡记录 |
| DELETE | /member/checkins/{id}/ | 删除打卡记录 |
| GET | /member/checkins/today/ | 获取今日打卡状态 |
| GET | /member/cycles/ | 获取我的周期列表 |
| POST | /member/cycles/ | 创建21天周期 |
| GET | /member/cycles/{id}/ | 获取周期详情 |
| GET | /member/cycles/current/ | 获取当前活跃周期 |
| GET | /member/cycles/{id}/stats/ | 获取周期统计 |

---

## 七、使用场景示例

### 7.1 开始21天打卡挑战

```bash
# 1. 查看可选主题
curl -X GET "http://localhost:8000/api/v1/check-system/member/themes/?is_system=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 1"

# 2. 创建21天周期，选择5个主题
curl -X POST "http://localhost:8000/api/v1/check-system/member/cycles/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "start_date": "2026-01-14",
    "selected_themes": [1, 2, 3, 4, 5]
  }'
```

### 7.2 每日打卡流程

```bash
# 1. 获取当前周期
curl -X GET "http://localhost:8000/api/v1/check-system/member/cycles/current/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 1"

# 2. 为选中的主题打卡
curl -X POST "http://localhost:8000/api/v1/check-system/member/checkins/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "theme": 2,
    "check_date": "2026-01-14",
    "remarks": "今天22:00准时入睡"
  }'

# 3. 查看今日打卡状态
curl -X GET "http://localhost:8000/api/v1/check-system/member/checkins/today/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 1"
```

### 7.3 查看打卡进度

```bash
# 获取周期统计
curl -X GET "http://localhost:8000/api/v1/check-system/member/cycles/1/stats/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 1"

# 响应: {"current_day": 5, "progress": 23, "total_checkins": 15, ...}
```
