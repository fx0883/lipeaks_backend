# 管理员用户API示例文档

本文档提供管理员用户API的实际请求和响应示例，帮助前端开发人员了解API的具体使用方式。这些示例基于实际的网络请求，展示了API的真实行为。

## 目录

1. [获取管理员列表](#获取管理员列表)
2. [创建新管理员](#创建新管理员)
3. [获取单个管理员](#获取单个管理员)
4. [更新管理员信息](#更新管理员信息)
5. [上传管理员头像](#上传管理员头像)
6. [授予超级管理员权限](#授予超级管理员权限)
7. [获取当前管理员信息](#获取当前管理员信息)
8. [更新当前管理员信息](#更新当前管理员信息)

## 获取管理员列表

### 请求

```
GET /api/v1/admin-users/?page=1&page_size=10
```

### 响应

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
      {
        "id": 1,
        "username": "admin",
        "email": "admin@qq.com",
        "phone": "13397651234",
        "nick_name": "Xuan",
        "first_name": "Feng",
        "last_name": "Xuan",
        "is_active": true,
        "avatar": "http://localhost:8000/media/avatars/a3fbfd97-e898-47b5-8725-5741f23597ad.jpg",
        "tenant": null,
        "tenant_name": null,
        "is_admin": true,
        "is_member": false,
        "is_super_admin": true,
        "role": "超级管理员",
        "date_joined": "2025-04-21T23:32:00+08:00"
      },
      {
        "id": 2,
        "username": "root",
        "email": "root@qq.com",
        "phone": null,
        "nick_name": null,
        "first_name": "",
        "last_name": "",
        "is_active": true,
        "avatar": "",
        "tenant": null,
        "tenant_name": null,
        "is_admin": true,
        "is_member": false,
        "is_super_admin": true,
        "role": "超级管理员",
        "date_joined": "2025-04-21T23:37:35.884364+08:00"
      },
      // ... 更多管理员记录 ...
    ]
  }
}
```

### 说明

- 请求参数包括`page`(页码)和`page_size`(每页数量)，用于分页
- 响应中包含管理员列表，以及分页信息（总数、下一页链接、上一页链接）
- 每个管理员记录包含完整的用户信息，包括ID、用户名、邮箱、电话、昵称、姓名、头像、租户信息、角色等

## 创建新管理员

### 请求

```
POST /api/v1/admin-users/
```

#### 请求体

```json
{
  "username": "rr6U111",
  "email": "user@example.com",
  "phone": "string",
  "nick_name": "string",
  "first_name": "string",
  "last_name": "string",
  "password": "string1234567",
  "password_confirm": "string1234567",
  "tenant_id": 1,
  "is_admin": true,
  "is_member": true,
  "avatar": "string"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 31,
    "username": "rr6U111",
    "email": "user@example.com",
    "phone": "string",
    "nick_name": "string",
    "first_name": "string",
    "last_name": "string",
    "avatar": "string"
  }
}
```

### 说明

- 创建管理员需要提供用户名、邮箱、密码和确认密码等必填字段
- 可以选择性地提供电话、昵称、姓名、租户ID和头像等信息
- `is_admin`字段应该设置为`true`以确保创建的是管理员用户
- 响应中返回新创建的管理员基本信息，包含分配的ID

## 获取单个管理员

### 请求

```
GET /api/v1/admin-users/31/
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 31,
    "username": "rr6U111",
    "email": "user@example.com",
    "phone": "string",
    "nick_name": "string",
    "first_name": "string",
    "last_name": "string",
    "is_active": true,
    "avatar": "http://localhost:8000/string",
    "tenant": 1,
    "tenant_name": "打卡系统1",
    "is_admin": true,
    "is_member": false,
    "is_super_admin": false,
    "role": "租户管理员",
    "date_joined": "2025-06-18T20:42:15.327560+08:00"
  }
}
```

### 说明

- 通过管理员ID获取单个管理员的详细信息
- 响应中包含管理员的完整信息，包括ID、用户名、邮箱、电话、姓名、头像、租户信息、角色、创建时间等
- `tenant_name`字段提供了租户的名称，方便前端显示

## 更新管理员信息

### 请求

```
PUT /api/v1/admin-users/31/
```

#### 请求体

```json
{
  "phone": "string",
  "nick_name": "string",
  "first_name": "string",
  "last_name": "string",
  "avatar": "string",
  "is_active": true,
  "status": "active",
  "username": "Ra@SvdLIxkoO0CoHlWc@z@896h@WMAaVYsfVR6.UrDF@Co7Nmn2OdIoUFzuIs",
  "email": "user@example.com"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 31,
    "username": "Ra@SvdLIxkoO0CoHlWc@z@896h@WMAaVYsfVR6.UrDF@Co7Nmn2OdIoUFzuIs",
    "email": "user@example.com",
    "phone": "string",
    "nick_name": "string",
    "first_name": "string",
    "last_name": "string",
    "is_active": true,
    "avatar": "http://localhost:8000/string",
    "tenant": 1,
    "tenant_name": "打卡系统1",
    "is_admin": true,
    "is_member": false,
    "is_super_admin": false,
    "role": "租户管理员",
    "date_joined": "2025-06-18T20:42:15.327560+08:00"
  }
}
```

### 说明

- 通过PUT请求更新管理员的信息
- 可以更新的字段包括电话、昵称、姓名、头像、状态等
- 用户名和邮箱通常也可以更新，但可能受到系统规则限制
- 响应中返回更新后的完整管理员信息

## 上传管理员头像

### 为特定管理员上传头像

#### 请求

```
POST /api/v1/admin-users/31/avatar/upload/
```

#### 请求体

```
------WebKitFormBoundaryGa8Jr7KKaBRSXhUQ
Content-Disposition: form-data; name="avatar"; filename="094b4ebd49fb68817563914a16c8f8c899e4fb9d03ad89fa8d3ad65be3527ad3.webp"
Content-Type: image/webp

[二进制图片数据]
------WebKitFormBoundaryGa8Jr7KKaBRSXhUQ--
```

#### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {
    "avatar": "http://localhost:8000/media/avatars/6006a926-9f24-4205-ae00-d166a2a1c27d.webp"
  }
}
```

### 为当前登录管理员上传头像

#### 请求

```
POST /api/v1/admin-users/avatar/upload/
```

#### 请求体

```
------WebKitFormBoundarya72iJs2eOjvySarF
Content-Disposition: form-data; name="avatar"; filename="094b4ebd49fb68817563914a16c8f8c899e4fb9d03ad89fa8d3ad65be3527ad3.webp"
Content-Type: image/webp

[二进制图片数据]
------WebKitFormBoundarya72iJs2eOjvySarF--
```

#### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {
    "avatar": "http://localhost:8000/media/avatars/b9e6d0a1-988a-45db-ae27-3d6d15703aad.webp"
  }
}
```

### 说明

- 头像上传使用`multipart/form-data`格式
- 表单字段名为`avatar`，值为图片文件
- 支持的图片格式包括webp、jpg、png等常见格式
- 响应中返回上传成功后的头像URL

## 授予超级管理员权限

### 请求

```
POST /api/v1/admin-users/31/grant-super-admin/
```

#### 请求体

```json
{
  "detail": "string"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "已成功将 Ra@SvdLIxkoO0CoHlWc@z@896h@WMAaVYsfVR6.UrDF@Co7Nmn2OdIoUFzuIs 设为超级管理员",
  "data": {}
}
```

### 说明

- 通过POST请求授予指定管理员超级管理员权限
- 请求体可以包含一个可选的`detail`字段，用于说明授权原因
- 此操作只能由现有超级管理员执行
- 响应中返回操作成功的消息，通常包含被授权用户的用户名

## 获取当前管理员信息

### 请求

```
GET /api/v1/admin-users/me/
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
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
  }
}
```

### 说明

- 获取当前登录管理员的详细信息
- 不需要提供ID参数，系统自动识别当前登录用户
- 响应包含完整的用户信息，包括ID、用户名、邮箱、电话、姓名、头像、租户信息、角色等

## 更新当前管理员信息

### 请求

```
PUT /api/v1/admin-users/me/
```

#### 请求体

```json
{
  "id": 1,
  "phone": "13397651234",
  "nick_name": "Xuan",
  "first_name": "Feng",
  "last_name": "Xuan",
  "avatar": "http://localhost:8000/media/avatars/b9e6d0a1-988a-45db-ae27-3d6d15703aad.webp",
  "role": "超级管理员",
  "date_joined": "2025-04-21T23:32:00+08:00"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
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
  }
}
```

### 说明

- 更新当前登录管理员的基本信息
- 可以更新的字段通常包括电话、昵称、姓名等个人信息
- 某些字段如`role`、`date_joined`、`is_super_admin`等通常是只读的
- 响应中返回更新后的完整用户信息 