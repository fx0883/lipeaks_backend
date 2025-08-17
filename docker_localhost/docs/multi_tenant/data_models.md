# 数据模型

本文档描述系统中的主要数据模型和字段，帮助前端开发人员理解API返回的数据结构。

## 用户模型 (User)

用户模型存储系统用户信息，包括认证信息、个人资料和角色权限。

| 字段名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| id | integer | 自动生成 | 用户ID，唯一标识 | 123 |
| username | string | 是 | 用户名，同一租户内唯一 | "john_doe" |
| email | string | 是 | 电子邮箱，同一租户内唯一 | "john@example.com" |
| phone | string | 否 | 手机号，同一租户内唯一 | "13812345678" |
| nick_name | string | 否 | 用户昵称 | "John" |
| first_name | string | 否 | 名字 | "John" |
| last_name | string | 否 | 姓氏 | "Doe" |
| is_active | boolean | 自动 | 用户是否激活 | true |
| avatar | string | 否 | 头像URL | "" |
| tenant | integer | 否 | 关联租户ID | 1 |
| tenant_name | string | 自动 | 关联租户名称（只读） | "Company A" |
| is_admin | boolean | 否 | 是否为管理员 | false |
| is_member | boolean | 否 | 是否为普通成员 | true |
| is_super_admin | boolean | 否 | 是否为超级管理员 | false |
| role | string | 自动 | 角色显示名称（只读） | "普通用户" |
| date_joined | datetime | 自动 | 注册时间 | "2025-04-22T10:00:00Z" |
| last_login | datetime | 自动 | 最后登录时间 | "2025-04-22T10:05:00Z" |
| last_login_ip | string | 自动 | 最后登录IP | "192.168.1.1" |
| is_deleted | boolean | 自动 | 是否已删除（软删除标记） | false |
| status | string | 自动 | 用户状态，可选值: active/suspended/inactive | "active" |

### 用户角色说明

用户可以同时具有多个角色标记，系统根据这些标记确定用户的实际角色：

- **超级管理员**：`is_super_admin=true`，此时`is_admin`也必定为`true`，不属于任何租户（`tenant=null`）
- **租户管理员**：`is_admin=true`且`is_super_admin=false`，必须关联到租户
- **普通用户**：`is_member=true`且`is_admin=false`，通常关联到租户

### 用户状态说明

- **active**：活跃状态，用户可以正常登录和使用系统
- **suspended**：暂停状态，用户无法登录，但数据保留
- **inactive**：未激活状态，通常用于新注册但未确认的用户或被软删除的用户

## 租户模型 (Tenant)

租户模型存储多租户系统中的租户信息。

| 字段名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| id | integer | 自动生成 | 租户ID，唯一标识 | 1 |
| name | string | 是 | 租户名称，全局唯一 | "Company A" |
| code | string | 否 | 租户代码，如不提供将自动生成，全局唯一 | "COMP-A" |
| description | string | 否 | 租户描述 | "公司A的描述" |
| status | string | 自动 | 租户状态，可选值: active/suspended/inactive | "active" |
| is_deleted | boolean | 自动 | 是否已删除（软删除标记） | false |
| created_at | datetime | 自动 | 创建时间 | "2025-04-01T10:00:00Z" |
| updated_at | datetime | 自动 | 更新时间 | "2025-04-22T10:00:00Z" |

### 租户状态说明

- **active**：活跃状态，租户正常运行，用户可以登录和使用系统
- **suspended**：暂停状态，租户被暂停，租户内的用户无法登录，但数据保留
- **inactive**：未激活或已删除状态，通常表示租户已被软删除

## 租户配额模型 (TenantQuota)

租户配额模型存储租户的资源使用限制。

| 字段名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| id | integer | 自动生成 | 配额ID，唯一标识 | 1 |
| tenant | integer | 自动 | 关联租户ID | 1 |
| max_users | integer | 否 | 最大用户数，默认50 | 100 |
| max_admins | integer | 否 | 最大管理员数，默认5 | 10 |
| current_users | integer | 自动计算 | 当前用户数（只读） | 45 |
| current_admins | integer | 自动计算 | 当前管理员数（只读） | 2 |

## API日志模型 (APILog)

API日志模型记录系统中所有API请求的详细信息。

| 字段名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| id | integer | 自动生成 | 日志ID，唯一标识 | 1 |
| user | integer | 自动 | 关联用户ID | 123 |
| ip_address | string | 自动 | 请求IP地址 | "192.168.1.1" |
| method | string | 自动 | HTTP方法 | "POST" |
| path | string | 自动 | 请求路径 | "/api/v1/auth/login/" |
| query_params | object | 自动 | 查询参数 | {} |
| headers | object | 自动 | 请求头 | {"User-Agent": "Mozilla/5.0..."} |
| request_data | object | 自动 | 请求数据 | {"username": "john_doe"} |
| status_code | integer | 自动 | 响应状态码 | 200 |
| response_data | object | 自动 | 响应数据 | {"success": true} |
| execution_time | integer | 自动 | 执行时间（毫秒） | 235 |
| created_at | datetime | 自动 | 创建时间 | "2025-04-22T10:05:23Z" |

## 数据模型关系

1. **用户与租户**：多对一关系，多个用户可以属于一个租户，超级管理员不属于任何租户

2. **租户与配额**：一对一关系，每个租户有一个对应的配额设置

3. **API日志与用户**：多对一关系，一个用户可以有多条API日志记录

## 数据验证规则

1. **用户名**：
   - 在同一租户内唯一
   - 长度限制：3-150个字符
   - 只允许使用字母、数字、下划线等字符

2. **电子邮箱**：
   - 在同一租户内唯一
   - 必须符合标准邮箱格式

3. **手机号**：
   - 在同一租户内唯一
   - 长度限制：11个字符
   - 必须符合手机号格式规则

4. **密码**：
   - 长度至少8个字符
   - 必须同时包含字母和数字
   - 建议同时包含大小写字母、数字和特殊字符

5. **租户名称**：
   - 全局唯一
   - 长度限制：2-50个字符

6. **租户代码**：
   - 全局唯一
   - 长度限制：2-20个字符
   - 只允许使用大写字母、数字和连字符

7. **配额限制**：
   - `max_users` 必须大于或等于 `current_users`
   - `max_admins` 必须大于或等于 `current_admins`
   - `max_admins` 必须小于或等于 `max_users` 