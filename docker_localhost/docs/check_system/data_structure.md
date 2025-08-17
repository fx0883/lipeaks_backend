# 打卡系统数据结构分析文档

## 1. 用户（User）

- **模型位置**：users/models.py
- **父子关系**：通过 `parent` 字段（外键指向自身）实现主用户与子用户的父子关系。主用户 parent 为空，子用户 parent 指向主用户。
- **主要字段**：
  - id：用户唯一标识
  - username：用户名
  - tenant：所属租户
  - parent：父账号（主用户为 null，子用户为主用户 id）
  - is_admin / is_super_admin / is_member：角色标识
  - phone / email / nick_name / avatar：联系方式与展示信息
  - status：状态（active, suspended, inactive）
  - is_deleted：软删除标记
  - 其他：last_login_ip、date_joined 等

- **子用户特性**：
  - 不能为管理员或超级管理员
  - 不允许登录（is_active = False）

---

## 2. 打卡类型（TaskCategory）

- **模型位置**：check_system/models.py
- **主要字段**：
  - id：类型唯一标识
  - name：类型名称
  - description：类型描述
  - is_system：是否为系统预设类型
  - icon：图标
  - user：创建用户
  - tenant：所属租户
  - translations：多语言翻译
  - created_at / updated_at：创建/更新时间

---

## 3. 打卡任务（Task）

- **模型位置**：check_system/models.py
- **主要字段**：
  - id：任务唯一标识
  - name：任务名称
  - description：任务描述
  - category：所属打卡类型（TaskCategory 外键）
  - user：所属用户（主用户或子用户）
  - tenant：所属租户
  - start_date / end_date：任务起止日期
  - status：任务状态（active, completed, paused, archived）
  - reminder / reminder_time：是否提醒及提醒时间
  - frequency_type：打卡频率类型（daily, weekly, monthly, custom）
  - frequency_days：打卡频率天数（如每周几、每月几号、自定义日期等）
  - created_at / updated_at：创建/更新时间

---

## 4. 打卡记录（CheckRecord）

- **模型位置**：check_system/models.py
- **主要字段**：
  - id：记录唯一标识
  - task：所属任务（Task 外键）
  - user：所属用户
  - check_date / check_time：打卡日期/时间
  - remarks / comment：备注/评论
  - completion_time：完成时间
  - created_at：创建时间

- **唯一性约束**：同一用户同一任务同一天只能有一条打卡记录

---

## 5. 任务模板（TaskTemplate）

- **模型位置**：check_system/models.py
- **主要字段**：
  - id：模板唯一标识
  - name：模板名称
  - description：模板描述
  - category：所属类型
  - is_system：是否为系统预设模板
  - user：创建用户
  - tenant：所属租户
  - reminder / reminder_time：是否提醒及提醒时间
  - translations：多语言翻译
  - created_at / updated_at：创建/更新时间

---

## 6. 典型数据结构示例

### 用户（主用户+子用户）

```json
[
  {
    "id": 1,
    "username": "liming",
    "nick_name": "李明",
    "parent": null,
    "is_admin": true,
    "is_super_admin": false,
    "is_member": false,
    "avatar": "/static/avatar/liming.png",
    "status": "active",
    "sub_accounts": [
      {
        "id": 2,
        "username": "xiaoming",
        "nick_name": "小明",
        "parent": 1,
        "is_admin": false,
        "is_super_admin": false,
        "is_member": true,
        "avatar": "/static/avatar/xiaoming.png",
        "status": "active"
      },
      {
        "id": 3,
        "username": "xiaohong",
        "nick_name": "小红",
        "parent": 1,
        "is_admin": false,
        "is_super_admin": false,
        "is_member": true,
        "avatar": "/static/avatar/xiaohong.png",
        "status": "active"
      }
    ]
  }
]
```

### 打卡类型

```json
{
  "id": 1,
  "name": "运动",
  "description": "每日锻炼身体",
  "icon": "medal",
  "user": 1,
  "is_system": false,
  "created_at": "2024-06-01T10:00:00Z"
}
```

### 打卡任务

```json
{
  "id": 1,
  "name": "晨跑",
  "description": "每天早上6点跑步3公里",
  "category": 1,
  "user": 1,
  "start_date": "2024-06-01",
  "end_date": "2024-06-30",
  "status": "active",
  "reminder": true,
  "reminder_time": "06:00:00",
  "frequency_type": "daily",
  "frequency_days": [],
  "created_at": "2024-06-01T10:00:00Z"
}
```

### 打卡记录

```json
{
  "id": 1,
  "task": 1,
  "user": 1,
  "check_date": "2024-06-01",
  "check_time": "06:10:00",
  "remarks": "状态良好",
  "comment": "",
  "completion_time": "06:30:00",
  "created_at": "2024-06-01T06:30:00Z"
}
```

---

## 7. 关系说明

- 一个主用户可有多个子用户（parent 字段）。
- 每个用户（主/子）可有多个打卡类型、任务、打卡记录。
- 任务与打卡类型、用户、租户关联。
- 打卡记录与任务、用户关联，且同一用户同一任务同一天只能有一条记录。

---

## 8. 前端页面数据填充建议

- 首页、个人中心等页面可展示主用户及其子用户信息。
- 任务列表、打卡类型、数据统计等页面可根据 user 字段区分主用户/子用户数据。
- 创建任务、打卡等页面需支持选择打卡类型、设置频率、提醒等。

---

如需更详细的字段说明或有其他疑问，请随时告知。
如需调整数据结构或补充特殊字段，也请及时说明。 