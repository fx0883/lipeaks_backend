# 管理员用户API示例文档（补充）

本文档是管理员用户API示例文档的补充部分，提供其他常用API端点的请求和响应示例。

## 目录

1. [修改管理员密码](#修改管理员密码)
2. [撤销超级管理员权限](#撤销超级管理员权限)
3. [创建超级管理员](#创建超级管理员)
4. [删除管理员](#删除管理员)
5. [管理员搜索和筛选](#管理员搜索和筛选)

## 修改管理员密码

### 请求

```
POST /api/v1/admin-users/me/password/
```

#### 请求体

```json
{
  "old_password": "oldpassword123",
  "new_password": "newpassword456",
  "new_password_confirm": "newpassword456"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "密码修改成功",
  "data": {
    "detail": "密码修改成功"
  }
}
```

### 说明

- 此API用于修改当前登录管理员的密码
- 需要提供旧密码、新密码和确认新密码
- 新密码必须符合系统的密码强度要求
- 密码修改成功后，通常不会自动退出登录，但某些系统可能要求重新登录

## 撤销超级管理员权限

### 请求

```
POST /api/v1/admin-users/31/revoke-super-admin/
```

#### 请求体

```json
{
  "tenant_id": 1
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "已成功撤销超级管理员权限",
  "data": {
    "detail": "已成功撤销 Ra@SvdLIxkoO0CoHlWc@z@896h@WMAaVYsfVR6.UrDF@Co7Nmn2OdIoUFzuIs 的超级管理员权限，并设置为租户管理员"
  }
}
```

### 说明

- 此API用于撤销指定管理员的超级管理员权限
- 必须提供一个租户ID，因为超级管理员被降级后需要分配到某个租户
- 此操作只能由现有超级管理员执行
- 响应中返回操作成功的消息，通常包含被撤销权限用户的用户名
- 不能撤销自己的超级管理员权限

## 创建超级管理员

### 请求

```
POST /api/v1/admin-users/super-admin/create/
```

#### 请求体

```json
{
  "username": "newsuperadmin",
  "email": "newsuperadmin@example.com",
  "password": "securepassword123",
  "password_confirm": "securepassword123",
  "phone": "13900139002",
  "nick_name": "新超级管理员",
  "first_name": "超级",
  "last_name": "管理员"
}
```

### 响应

```json
{
  "success": true,
  "code": 2001,
  "message": "创建成功",
  "data": {
    "id": 32,
    "username": "newsuperadmin",
    "email": "newsuperadmin@example.com",
    "phone": "13900139002",
    "nick_name": "新超级管理员",
    "first_name": "超级",
    "last_name": "管理员",
    "is_active": true,
    "avatar": "",
    "tenant": null,
    "tenant_name": null,
    "is_admin": true,
    "is_member": false,
    "is_super_admin": true,
    "role": "超级管理员",
    "date_joined": "2025-06-18T21:15:30.123456+08:00"
  }
}
```

### 说明

- 此API用于创建新的超级管理员
- 与创建普通管理员类似，但不需要提供租户ID
- 只有现有超级管理员可以创建新的超级管理员
- 响应中返回新创建的超级管理员信息，`is_super_admin`字段为`true`

## 删除管理员

### 请求

```
DELETE /api/v1/admin-users/31/
```

### 响应

```
状态码: 204 No Content
```

### 说明

- 此API用于删除指定的管理员
- 实际执行的是软删除，即将用户标记为已删除，但不会从数据库中物理删除
- 删除成功后返回204状态码，没有响应体
- 不能删除当前登录的管理员账号
- 租户管理员只能删除自己租户内的管理员

## 管理员搜索和筛选

### 基本搜索

#### 请求

```
GET /api/v1/admin-users/?search=admin
```

#### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@qq.com",
        "phone": "13397651234",
        "nick_name": "Xuan",
        "first_name": "Feng",
        "last_name": "Xuan",
        "is_active": true,
        "avatar": "http://localhost:8000/media/avatars/b9e6d0a1-988a-45db-ae27-3d6d15703aad.webp",
        "tenant": null,
        "tenant_name": null,
        "is_admin": true,
        "is_member": false,
        "is_super_admin": true,
        "role": "超级管理员",
        "date_joined": "2025-04-21T23:32:00+08:00"
      },
      // ... 其他匹配结果 ...
    ]
  }
}
```

### 按状态筛选

#### 请求

```
GET /api/v1/admin-users/?status=active
```

#### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "count": 8,
    "next": null,
    "previous": null,
    "results": [
      // ... 状态为active的管理员列表 ...
    ]
  }
}
```

### 按超级管理员身份筛选

#### 请求

```
GET /api/v1/admin-users/?is_super_admin=true
```

#### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "count": 4,
    "next": null,
    "previous": null,
    "results": [
      // ... 超级管理员列表 ...
    ]
  }
}
```

### 按租户筛选

#### 请求

```
GET /api/v1/admin-users/?tenant_id=1
```

#### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
      // ... 属于租户ID为1的管理员列表 ...
    ]
  }
}
```

### 组合筛选

#### 请求

```
GET /api/v1/admin-users/?search=admin&status=active&is_super_admin=true&page=1&page_size=10
```

#### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
      // ... 符合所有条件的管理员列表 ...
    ]
  }
}
```

### 说明

- 搜索参数`search`支持按用户名、邮箱、昵称和手机号进行模糊搜索
- 状态筛选参数`status`可以是`active`、`inactive`或`suspended`
- 超级管理员筛选参数`is_super_admin`可以是`true`或`false`
- 租户筛选参数`tenant_id`用于筛选特定租户下的管理员
- 可以组合多个筛选条件进行精确筛选
- 所有筛选都支持分页，使用`page`和`page_size`参数 