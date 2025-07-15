# 自律打卡App 数据库设计文档

## 数据库概述

自律打卡App的数据库设计旨在支持用户创建和管理各种打卡任务、记录打卡进度、分享打卡成果以及查看统计数据等功能。数据库结构需要满足以下核心需求：

1. 用户账户管理
2. 打卡类型和任务管理
3. 打卡记录和历史跟踪
4. 社交分享和互动
5. 数据统计和分析
6. 系统配置和用户设置

## 实体关系模型

```
┌────────────┐      ┌────────────┐      ┌────────────┐
│    User    │      │ TaskType   │      │    Task    │
├────────────┤      ├────────────┤      ├────────────┤
│ id         │      │ id         │      │ id         │
│ username   │      │ name       │──1┐  │ title      │
│ password   │      │ description│    │  │ description│
│ email      │      │ icon       │    └─◇ type_id    │
│ avatar     │      │ color      │      │ user_id    │──┐
│ created_at │      │ created_by │──────┘│ duration   │  │
│ updated_at │◇────┐│ created_at │      │ remind_time│  │
└────────────┘     ││ updated_at │      │ is_active  │  │
                   │└────────────┘      │ created_at │  │
                   │                    │ updated_at │  │
                   │                    └────────────┘  │
                   │                                    │
                   │                                    │
                   │                    ┌────────────┐  │
                   │                    │ CheckIn    │  │
                   │                    ├────────────┤  │
                   │                    │ id         │  │
                   └────────────────────┤ user_id    │◇─┘
                                        │ task_id    │
                                        │ check_date │
                                        │ duration   │
                                        │ comment    │
                                        │ created_at │
                                        └────────────┘

┌────────────┐      ┌────────────┐      ┌────────────┐
│ Friendship │      │ Comment    │      │ Statistics │
├────────────┤      ├────────────┤      ├────────────┤
│ id         │      │ id         │      │ id         │
│ user_id    │◇────┐│ user_id    │◇────┐│ user_id    │◇────┐
│ friend_id  │◇───┐││ checkin_id │◇─┐  │││ date       │     │
│ status     │    │││ created_at │  │  │││ completed  │     │
│ created_at │    │││ updated_at │  │  │││ total      │     │
└────────────┘    ││││ created_at │  │  │││ streak     │     │
                  │└└└└──────────┘  │  │└└└──────────┘     │
                  │                 │  │                   │
┌────────────┐    │                 │  │                   │
│ Notification│    │  ┌────────────┐│  │ ┌────────────┐    │
├────────────┤    │  │  Settings  │└──┘ │  User      │    │
│ id         │    │  ├────────────┤     ├────────────┤    │
│ user_id    │◇───┘  │ id         │     │ (continued)│    │
│ content    │       │ user_id    │◇────┘            │    │
│ is_read    │       │ reminder   │                  │    │
│ created_at │       │ theme      │                  │    │
└────────────┘       │ privacy    │                  │    │
                     └────────────┘                  └────┘
```

## 数据库表结构

### 1. User (用户表)

存储用户基本信息和身份验证数据。

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| id | Integer | 用户唯一标识 | 主键, 自增 |
| username | String | 用户名 | 唯一, 非空 |
| password | String | 加密后的密码 | 非空 |
| email | String | 电子邮箱 | 唯一, 非空 |
| phone | String | 手机号码 | 唯一 |
| avatar | String | 头像URL | 可空 |
| bio | Text | 个人简介 | 可空 |
| created_at | DateTime | 创建时间 | 非空, 默认当前时间 |
| updated_at | DateTime | 更新时间 | 非空, 默认当前时间 |

### 2. TaskType (打卡类型表)

存储不同类型的打卡活动类别，如运动、学习、冥想等。

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| id | Integer | 类型唯一标识 | 主键, 自增 |
| name | String | 类型名称 | 非空 |
| description | Text | 类型描述 | 可空 |
| icon | String | 图标标识 | 非空 |
| color | String | 颜色代码 | 非空 |
| created_by | Integer | 创建者ID | 外键(User.id) |
| created_at | DateTime | 创建时间 | 非空, 默认当前时间 |
| updated_at | DateTime | 更新时间 | 非空, 默认当前时间 |

### 3. Task (任务表)

存储用户创建的具体打卡任务。

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| id | Integer | 任务唯一标识 | 主键, 自增 |
| title | String | 任务标题 | 非空 |
| description | Text | 任务描述 | 可空 |
| type_id | Integer | 所属类型ID | 外键(TaskType.id) |
| user_id | Integer | 所属用户ID | 外键(User.id) |
| duration | Integer | 预计时长(分钟) | 非空 |
| remind_time | Time | 提醒时间 | 可空 |
| is_active | Boolean | 是否激活 | 非空, 默认true |
| frequency | String | 重复频率(daily, weekly, monthly) | 非空, 默认daily |
| repeat_days | String | 每周重复日(1-7,逗号分隔) | 可空 |
| created_at | DateTime | 创建时间 | 非空, 默认当前时间 |
| updated_at | DateTime | 更新时间 | 非空, 默认当前时间 |

### 4. CheckIn (打卡记录表)

存储用户每次打卡的具体记录。

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| id | Integer | 记录唯一标识 | 主键, 自增 |
| user_id | Integer | 用户ID | 外键(User.id), 非空 |
| task_id | Integer | 任务ID | 外键(Task.id), 非空 |
| check_date | Date | 打卡日期 | 非空 |
| check_time | Time | 打卡时间 | 非空 |
| duration | Integer | 实际花费时间(分钟) | 非空 |
| comment | Text | 打卡感想 | 可空 |
| status | String | 状态(completed, failed) | 非空 |
| created_at | DateTime | 创建时间 | 非空, 默认当前时间 |

### 5. Friendship (社交关系表)

存储用户之间的社交关系。

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| id | Integer | 关系唯一标识 | 主键, 自增 |
| user_id | Integer | 用户ID | 外键(User.id), 非空 |
| friend_id | Integer | 好友ID | 外键(User.id), 非空 |
| status | String | 状态(pending, accepted, rejected) | 非空 |
| created_at | DateTime | 创建时间 | 非空, 默认当前时间 |

### 6. Comment (评论表)

存储用户对打卡记录的评论。

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| id | Integer | 评论唯一标识 | 主键, 自增 |
| user_id | Integer | 评论者ID | 外键(User.id), 非空 |
| checkin_id | Integer | 打卡记录ID | 外键(CheckIn.id), 非空 |
| content | Text | 评论内容 | 非空 |
| created_at | DateTime | 创建时间 | 非空, 默认当前时间 |
| updated_at | DateTime | 更新时间 | 非空, 默认当前时间 |

### 7. Statistics (统计数据表)

存储用户的打卡统计数据，按日/周/月汇总。

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| id | Integer | 统计唯一标识 | 主键, 自增 |
| user_id | Integer | 用户ID | 外键(User.id), 非空 |
| date | Date | 统计日期 | 非空 |
| period_type | String | 统计周期(daily, weekly, monthly) | 非空 |
| completed_count | Integer | 完成任务数 | 非空, 默认0 |
| total_count | Integer | 总任务数 | 非空, 默认0 |
| streak | Integer | 连续打卡天数 | 非空, 默认0 |
| total_duration | Integer | 总时长(分钟) | 非空, 默认0 |
| created_at | DateTime | 创建时间 | 非空, 默认当前时间 |
| updated_at | DateTime | 更新时间 | 非空, 默认当前时间 |

### 8. Notification (通知表)

存储系统对用户的提醒和通知。

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| id | Integer | 通知唯一标识 | 主键, 自增 |
| user_id | Integer | 接收用户ID | 外键(User.id), 非空 |
| type | String | 通知类型(reminder, social, system) | 非空 |
| title | String | 通知标题 | 非空 |
| content | Text | 通知内容 | 非空 |
| related_id | Integer | 相关记录ID | 可空 |
| is_read | Boolean | 是否已读 | 非空, 默认false |
| created_at | DateTime | 创建时间 | 非空, 默认当前时间 |

### 9. Settings (用户设置表)

存储用户的个性化设置。

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| id | Integer | 设置唯一标识 | 主键, 自增 |
| user_id | Integer | 用户ID | 外键(User.id), 非空, 唯一 |
| reminder_enabled | Boolean | 是否启用提醒 | 非空, 默认true |
| reminder_time_before | Integer | 提前提醒时间(分钟) | 非空, 默认15 |
| theme | String | 主题设置(light, dark, system) | 非空, 默认system |
| privacy_level | String | 隐私级别(public, friends, private) | 非空, 默认friends |
| notification_enabled | Boolean | 是否启用通知 | 非空, 默认true |
| sound_enabled | Boolean | 是否启用声音 | 非空, 默认true |
| created_at | DateTime | 创建时间 | 非空, 默认当前时间 |
| updated_at | DateTime | 更新时间 | 非空, 默认当前时间 |

## API接口设计

### 用户管理API

1. **用户注册**
   - 请求方式: POST
   - 路径: `/api/users/register/`
   - 参数: username, password, email, phone(可选)
   - 返回: 用户信息和认证令牌

2. **用户登录**
   - 请求方式: POST
   - 路径: `/api/users/login/`
   - 参数: username/email, password
   - 返回: 用户信息和认证令牌

3. **获取用户信息**
   - 请求方式: GET
   - 路径: `/api/users/{user_id}/`
   - 参数: 无
   - 返回: 用户详细信息

4. **更新用户信息**
   - 请求方式: PUT
   - 路径: `/api/users/{user_id}/`
   - 参数: avatar, bio等
   - 返回: 更新后的用户信息

5. **修改密码**
   - 请求方式: POST
   - 路径: `/api/users/change-password/`
   - 参数: old_password, new_password
   - 返回: 成功/失败信息

### 任务管理API

1. **获取任务类型列表**
   - 请求方式: GET
   - 路径: `/api/task-types/`
   - 参数: 无
   - 返回: 任务类型列表

2. **创建任务类型**
   - 请求方式: POST
   - 路径: `/api/task-types/`
   - 参数: name, description, icon, color
   - 返回: 创建的任务类型信息

3. **获取用户任务列表**
   - 请求方式: GET
   - 路径: `/api/tasks/`
   - 参数: status(可选), date(可选), type_id(可选)
   - 返回: 任务列表

4. **创建任务**
   - 请求方式: POST
   - 路径: `/api/tasks/`
   - 参数: title, description, type_id, duration, remind_time等
   - 返回: 创建的任务信息

5. **更新任务**
   - 请求方式: PUT
   - 路径: `/api/tasks/{task_id}/`
   - 参数: 任务相关字段
   - 返回: 更新后的任务信息

6. **删除任务**
   - 请求方式: DELETE
   - 路径: `/api/tasks/{task_id}/`
   - 参数: 无
   - 返回: 成功/失败信息

### 打卡记录API

1. **打卡**
   - 请求方式: POST
   - 路径: `/api/checkins/`
   - 参数: task_id, duration, comment(可选)
   - 返回: 打卡记录信息

2. **获取打卡记录**
   - 请求方式: GET
   - 路径: `/api/checkins/`
   - 参数: task_id(可选), date(可选), period(day/week/month, 可选)
   - 返回: 打卡记录列表

3. **获取打卡详情**
   - 请求方式: GET
   - 路径: `/api/checkins/{checkin_id}/`
   - 参数: 无
   - 返回: 打卡详细信息

4. **添加打卡评论**
   - 请求方式: POST
   - 路径: `/api/checkins/{checkin_id}/comments/`
   - 参数: content
   - 返回: 创建的评论信息

### 社交API

1. **获取好友列表**
   - 请求方式: GET
   - 路径: `/api/friends/`
   - 参数: 无
   - 返回: 好友列表

2. **发送好友请求**
   - 请求方式: POST
   - 路径: `/api/friends/requests/`
   - 参数: friend_id
   - 返回: 请求信息

3. **处理好友请求**
   - 请求方式: PUT
   - 路径: `/api/friends/requests/{request_id}/`
   - 参数: status(accepted/rejected)
   - 返回: 更新后的请求信息

4. **获取社交动态**
   - 请求方式: GET
   - 路径: `/api/feed/`
   - 参数: page, limit
   - 返回: 好友打卡动态列表

### 统计API

1. **获取用户统计数据**
   - 请求方式: GET
   - 路径: `/api/statistics/`
   - 参数: period(day/week/month), date(可选)
   - 返回: 统计数据

2. **获取任务完成率**
   - 请求方式: GET
   - 路径: `/api/statistics/completion-rate/`
   - 参数: task_id(可选), period(day/week/month)
   - 返回: 完成率数据

3. **获取连续打卡数据**
   - 请求方式: GET
   - 路径: `/api/statistics/streaks/`
   - 参数: task_id(可选)
   - 返回: 连续打卡数据

### 设置API

1. **获取用户设置**
   - 请求方式: GET
   - 路径: `/api/settings/`
   - 参数: 无
   - 返回: 用户设置信息

2. **更新用户设置**
   - 请求方式: PUT
   - 路径: `/api/settings/`
   - 参数: 设置相关字段
   - 返回: 更新后的设置信息

### 通知API

1. **获取通知列表**
   - 请求方式: GET
   - 路径: `/api/notifications/`
   - 参数: is_read(可选), type(可选)
   - 返回: 通知列表

2. **标记通知为已读**
   - 请求方式: PUT
   - 路径: `/api/notifications/{notification_id}/read/`
   - 参数: 无
   - 返回: 更新后的通知信息

## 数据关系与联合使用

1. **用户与任务的关系**：
   - 一个用户可以创建多个任务
   - 用户通过User.id与Task.user_id关联

2. **任务与打卡记录的关系**：
   - A一个任务可以有多条打卡记录
   - 通过Task.id与CheckIn.task_id关联

3. **打卡记录与评论的关系**：
   - 一条打卡记录可以有多条评论
   - 通过CheckIn.id与Comment.checkin_id关联

4. **用户与统计数据的关系**：
   - 一个用户有多条统计数据（按日/周/月）
   - 通过User.id与Statistics.user_id关联

5. **用户与设置的关系**：
   - 一个用户有一条设置记录
   - 通过User.id与Settings.user_id一对一关联

## 数据库优化建议

1. **索引设计**：
   - 为频繁查询的字段创建索引，如task_id, user_id, check_date等
   - 为经常联合查询的字段创建复合索引

2. **数据分区**：
   - 对于CheckIn表，可以考虑按时间分区，提高查询效率

3. **缓存策略**：
   - 使用Redis缓存热点数据，如用户统计信息、当日任务等

4. **数据库事务**：
   - 打卡操作需要更新多个表，应使用事务确保数据一致性

5. **安全性考虑**：
   - 敏感字段（如密码）应加密存储
   - 实现行级权限控制，确保用户只能访问自己的数据 