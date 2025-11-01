# 子账号管理 API 文档

> **适用对象**: 前端开发人员（iOS/Web/Android）  
> **Base URL**: `/api/v1/members/sub-accounts/`  
> **文档版本**: 2.0  
> **最后更新**: 2025-10-31

---

## 📋 目录

1. [功能概述](#功能概述)
2. [获取子账号列表](#1-获取子账号列表)
3. [创建子账号](#2-创建子账号)
4. [获取子账号详情](#3-获取子账号详情)
5. [更新子账号信息](#4-更新子账号信息)
6. [删除子账号](#5-删除子账号)
7. [集成流程](#集成流程)
8. [常见问题](#常见问题)

---

## 功能概述

### 什么是子账号？

子账号是与主账号（Member）关联的附属账号，具有以下特点：

- ✅ 与主账号共享租户
- ✅ 可用于数据关联和权限控制
- ❌ **不能登录系统**（默认is_active=False）
- ❌ 不能创建自己的子账号
- ❌ 不能修改头像

### 使用场景

1. **多设备管理**: 为不同设备创建不同的子账号
2. **家庭账户**: 家庭成员共用主账号，各有子账号
3. **数据隔离**: 不同业务场景使用不同子账号进行数据关联

### 权限说明

| 用户类型 | 可以做什么 |
|---------|-----------|
| Member主账号 | 创建、查看、编辑、删除自己的子账号 |
| 超级管理员 | 查看、编辑、删除所有子账号 |
| 租户管理员 | 查看、编辑、删除本租户内的所有子账号 |
| 子账号 | ❌ 无法查看或管理子账号 |

---

## 1. 获取子账号列表

### 接口信息
- **URL**: `/api/v1/members/sub-accounts/`
- **方法**: `GET`
- **权限**: 需要认证，Member主账号可用

### 请求参数

| 参数名 | 类型 | 位置 | 必填 | 说明 | 默认值 |
|--------|------|------|------|------|--------|
| page | integer | query | 否 | 页码 | 1 |
| page_size | integer | query | 否 | 每页数量 | 10 |

### 请求示例

```http
GET /api/v1/members/sub-accounts/?page=1&page_size=10 HTTP/1.1
Host: your-domain.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
X-Tenant-ID: 1
```

### 响应格式

**成功响应 (200)**:
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 20,
      "username": "john_sub1",
      "email": "john.sub1@example.com",
      "phone": "13900001111",
      "nick_name": "John的设备1",
      "tenant": 1,
      "tenant_name": "示例公司",
      "is_sub_account": true,
      "parent": 10,
      "parent_username": "john_doe",
      "status": "active",
      "date_joined": "2025-10-20T10:00:00Z"
    }
  ]
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| count | integer | 子账号总数 |
| next | string/null | 下一页URL |
| previous | string/null | 上一页URL |
| results | array | 子账号列表 |

**results数组元素**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 子账号ID |
| username | string | 用户名 |
| email | string | 邮箱 |
| phone | string | 手机号 |
| nick_name | string | 昵称 |
| tenant | integer | 租户ID |
| tenant_name | string | 租户名称 |
| is_sub_account | boolean | 是否为子账号（始终为true） |
| parent | integer | 父账号ID |
| parent_username | string | 父账号用户名 |
| status | string | 状态 |
| date_joined | string | 创建时间 |

---

## 2. 创建子账号

### 接口信息
- **URL**: `/api/v1/members/sub-accounts/`
- **方法**: `POST`
- **权限**: 需要认证，Member主账号可用
- **Content-Type**: `application/json`

### 请求参数

| 字段名 | 类型 | 必填 | 说明 | 验证规则 |
|--------|------|------|------|----------|
| username | string | 是 | 用户名 | 唯一，3-150字符，字母数字下划线 |
| email | string | 是 | 邮箱 | 唯一，有效的邮箱格式 |
| password | string | 是 | 密码 | 至少8个字符 |
| nick_name | string | 否 | 昵称 | 最大30字符 |
| phone | string | 否 | 手机号 | 11位数字 |
| wechat_id | string | 否 | 微信号 | 最大32字符 |

### 自动设置的字段

- `parent`: 自动设置为当前登录用户
- `tenant`: 自动设置为父账号的租户
- `is_active`: 默认为False（不能登录）

### 请求示例

```http
POST /api/v1/members/sub-accounts/ HTTP/1.1
Host: your-domain.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
X-Tenant-ID: 1
Content-Type: application/json

{
  "username": "john_device_mobile",
  "email": "john.mobile@example.com",
  "password": "SecurePass123",
  "nick_name": "John的手机",
  "phone": "13900003333"
}
```

### 响应格式

**成功响应 (201)**:
```json
{
  "id": 22,
  "username": "john_device_mobile",
  "email": "john.mobile@example.com",
  "phone": "13900003333",
  "nick_name": "John的手机",
  "tenant": 1,
  "tenant_name": "示例公司",
  "is_sub_account": true,
  "parent": 10,
  "parent_username": "john_doe",
  "status": "active",
  "date_joined": "2025-10-31T12:00:00Z"
}
```

**错误响应 (400) - 用户名已存在**:
```json
{
  "username": ["该用户名已被使用"]
}
```

**错误响应 (400) - 邮箱已存在**:
```json
{
  "email": ["该邮箱已被注册"]
}
```

---

## 3. 获取子账号详情

### 接口信息
- **URL**: `/api/v1/members/sub-accounts/{id}/`
- **方法**: `GET`
- **权限**: 需要认证，只能查看自己的子账号

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 子账号ID |

### 请求示例

```http
GET /api/v1/members/sub-accounts/22/ HTTP/1.1
Host: your-domain.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
X-Tenant-ID: 1
```

### 响应格式

**成功响应 (200)**: 返回子账号详细信息（格式同列表中的单个元素）

**错误响应 (403)**:
```json
{
  "detail": "您没有权限访问此子账号"
}
```

---

## 4. 更新子账号信息

### 接口信息
- **URL**: `/api/v1/members/sub-accounts/{id}/`
- **方法**: `PATCH` 或 `PUT`
- **权限**: 需要认证，只能更新自己的子账号
- **Content-Type**: `application/json`

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 子账号ID |

### 请求参数

| 字段名 | 类型 | 必填 | 可修改 | 说明 |
|--------|------|------|--------|------|
| nick_name | string | 否 | ✅ | 昵称，最大30字符 |
| phone | string | 否 | ✅ | 手机号，11位数字 |
| wechat_id | string | 否 | ✅ | 微信号，最大32字符 |
| username | string | - | ❌ | 用户名（不可修改） |
| email | string | - | ❌ | 邮箱（不可修改） |

### 请求示例

```http
PATCH /api/v1/members/sub-accounts/22/ HTTP/1.1
Host: your-domain.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
X-Tenant-ID: 1
Content-Type: application/json

{
  "nick_name": "John的手机（已更新）",
  "phone": "13900004444"
}
```

### 响应格式

**成功响应 (200)**: 返回更新后的子账号信息

---

## 5. 删除子账号

### 接口信息
- **URL**: `/api/v1/members/sub-accounts/{id}/`
- **方法**: `DELETE`
- **权限**: 需要认证，只能删除自己的子账号

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 子账号ID |

### 请求示例

```http
DELETE /api/v1/members/sub-accounts/22/ HTTP/1.1
Host: your-domain.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
X-Tenant-ID: 1
```

### 响应格式

**成功响应 (204)**: 无响应体

### 注意事项

- ⚠️ 删除是软删除，数据保留在数据库
- ⚠️ 与子账号关联的数据不会被删除
- ⚠️ 删除操作不可通过API恢复

---

## 集成流程

### 子账号管理页面集成流程

```
┌──────────────────┐
│  页面加载         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  调用获取列表API │
│  GET /          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  显示子账号列表   │
│  - 用户名        │
│  - 昵称          │
│  - 创建时间      │
└────────┬─────────┘
         │
    ┌────┴────┐
    │  用户操作│
    └────┬────┘
         │
    ┌────┴────┐
    │         │         │
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│ 创建   │ │ 编辑   │ │ 删除   │
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ POST / │ │PATCH   │ │DELETE  │
│        │ │/{id}/  │ │/{id}/  │
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    └──────┬───┴──────────┘
           │
           ▼
    ┌──────────────┐
    │  刷新列表     │
    └──────────────┘
```

### 创建子账号详细流程

```
┌──────────────────┐
│  用户填写表单     │
│  - 用户名        │
│  - 邮箱          │
│  - 密码          │
│  - 昵称（可选）  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  前端验证         │
│  - 必填字段      │
│  - 格式检查      │
│  - 长度限制      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  调用创建API     │
│  POST /         │
└────────┬─────────┘
         │
         ▼
    ┌────┴────┐
    │ 是否成功│
    └────┬────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ 成功   │ │ 失败   │
│ 添加到 │ │ 显示   │
│ 列表   │ │ 错误   │
└────────┘ └────────┘
```

---

## 数据类型定义

### 子账号信息对象

```
SubAccount {
  id: Integer
  username: String
  email: String
  phone: String
  nick_name: String
  tenant: Integer
  tenant_name: String
  is_sub_account: Boolean (始终为true)
  parent: Integer
  parent_username: String
  status: String
  date_joined: String (ISO 8601 DateTime)
}
```

### 创建子账号请求对象

```
CreateSubAccountRequest {
  username: String (必填，3-150字符)
  email: String (必填，邮箱格式)
  password: String (必填，至少8字符)
  nick_name: String (可选，最大30字符)
  phone: String (可选，11位数字)
  wechat_id: String (可选，最大32字符)
}
```

### 更新子账号请求对象

```
UpdateSubAccountRequest {
  nick_name: String (可选)
  phone: String (可选)
  wechat_id: String (可选)
}
```

---

## 集成要点

### 1. 权限控制
- 只有Member主账号可以管理子账号
- 子账号不能查看或创建子账号
- 只能管理自己创建的子账号

### 2. 唯一性约束
- `username`必须在全系统唯一
- `email`必须在全系统唯一
- 创建前可以先验证

### 3. 自动字段
- `parent`字段会自动设置为当前用户
- `tenant`字段会自动设置为父账号的租户
- `is_active`默认为False（不能登录）

### 4. 数据验证
- 用户名只能包含字母、数字和下划线
- 邮箱必须是有效格式
- 密码至少8个字符

---

## 使用场景示例

### 场景1: 设备管理

**目标**: 为不同设备创建子账号

**流程**:
1. 调用`GET /sub-accounts/`获取现有子账号
2. 显示设备列表（每个子账号代表一个设备）
3. 用户添加新设备 → 调用`POST /sub-accounts/`
4. 设置子账号昵称为设备名（如"iPhone"、"iPad"）

### 场景2: 家庭账户

**目标**: 为家庭成员创建子账号

**流程**:
1. 主账号为家庭成员创建子账号
2. 每个成员使用各自的子账号ID进行数据关联
3. 主账号可以查看和管理所有成员的子账号

---

## 常见问题

### Q1: 子账号能否登录系统？
**A**: 不能。子账号的`is_active`默认为False，无法登录。如需登录功能，请创建正常的Member账号。

### Q2: 子账号数量有限制吗？
**A**: 后端没有硬性限制，但可能受租户配额限制。建议不要创建过多子账号。

### Q3: 删除子账号后能恢复吗？
**A**: 通过API无法恢复。删除是软删除，数据在数据库中保留，需要管理员手动操作才能恢复。

### Q4: 为什么要设置子账号密码？
**A**: 虽然子账号不能登录，但password字段是数据模型的必填字段。建议设置一个安全的随机密码。

### Q5: 子账号能否创建自己的子账号？
**A**: 不能。子账号无法创建或管理任何子账号。

### Q6: 如何修改子账号的用户名或邮箱？
**A**: 不能通过API修改。如需修改，请联系管理员或创建新的子账号后删除旧的。

---

## 错误码说明

| 状态码 | 场景 | 错误信息示例 |
|--------|------|-------------|
| 400 | 用户名重复 | `{"username": ["该用户名已被使用"]}` |
| 400 | 邮箱重复 | `{"email": ["该邮箱已被注册"]}` |
| 400 | 验证失败 | `{"password": ["密码至少需要8个字符"]}` |
| 403 | 子账号尝试操作 | `{"detail": "权限不足"}` |
| 403 | 操作他人子账号 | `{"detail": "您没有权限访问此子账号"}` |
| 404 | 子账号不存在 | `{"detail": "未找到"}` |

---

## 测试检查清单

- [ ] 成功获取子账号列表
- [ ] 空列表时正确显示
- [ ] 分页功能正常
- [ ] 成功创建子账号
- [ ] 用户名重复时正确报错
- [ ] 邮箱重复时正确报错
- [ ] 必填字段验证正常
- [ ] 成功更新子账号信息
- [ ] 成功删除子账号
- [ ] 子账号尝试访问时被拒绝

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.0 | 2025-10-31 | 移除前端代码，改为通用集成说明 |
| 1.0 | 2025-10-31 | 初始版本 |

---

**技术支持**: 如有问题，请联系后端团队。
