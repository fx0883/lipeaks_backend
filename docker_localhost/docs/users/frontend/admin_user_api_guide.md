# 管理员用户API使用指南

本文档详细介绍管理员用户相关API的使用方法，包括所有可用的端点、请求参数、响应格式以及权限要求。

## API基础信息

- **基础URL**: `/api/v1/admin-users/`
- **认证方式**: 所有请求需要在HTTP头部包含有效的JWT令牌：`Authorization: Bearer <token>`
- **响应格式**: 所有API返回标准JSON格式

## API端点概览

| 端点                          | 方法   | 描述                         | 权限要求               |
|-------------------------------|--------|------------------------------|------------------------|
| `/`                           | GET    | 获取管理员用户列表           | 需要管理员权限         |
| `/`                           | POST   | 创建新管理员                 | 需要管理员权限         |
| `/<id>/`                      | GET    | 获取单个管理员详情           | 需要管理员权限         |
| `/<id>/`                      | PUT    | 更新单个管理员信息           | 需要管理员权限         |
| `/<id>/`                      | DELETE | 删除单个管理员               | 需要管理员权限         |
| `/me/`                        | GET    | 获取当前登录管理员信息       | 需要管理员权限         |
| `/me/`                        | PUT    | 更新当前登录管理员信息       | 需要管理员权限         |
| `/me/password/`               | POST   | 修改当前登录管理员密码       | 需要管理员权限         |
| `/<id>/grant-super-admin/`    | POST   | 授予超级管理员权限           | 需要超级管理员权限     |
| `/<id>/revoke-super-admin/`   | POST   | 撤销超级管理员权限           | 需要超级管理员权限     |
| `/super-admin/create/`        | POST   | 创建超级管理员               | 需要超级管理员权限     |
| `/avatar/upload/`             | POST   | 上传当前管理员头像           | 需要管理员权限         |
| `/<id>/avatar/upload/`        | POST   | 为特定管理员上传头像         | 需要管理员权限         |

## 详细API说明

### 1. 获取管理员用户列表

获取系统中的管理员用户列表，支持分页和搜索。

- **URL**: `/`
- **方法**: `GET`
- **权限要求**: 需要管理员权限
- **查询参数**:
  - `search`: 搜索关键词，支持用户名、邮箱、昵称和手机号码
  - `status`: 用户状态筛选 (active/suspended/inactive)
  - `is_super_admin`: 是否为超级管理员 (true/false)
  - `tenant_id`: 租户ID，用于筛选特定租户下的管理员
  - `page`: 页码
  - `page_size`: 每页结果数

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "获取成功",
    "data": {
      "count": 5,
      "next": "http://example.com/api/v1/admin-users/?page=2",
      "previous": null,
      "results": [
        {
          "id": 1,
          "username": "admin",
          "email": "admin@example.com",
          "phone": "13800138000",
          "nick_name": "系统管理员",
          "tenant": null,
          "tenant_name": null,
          "is_admin": true,
          "is_member": false,
          "is_super_admin": true,
          "role": "超级管理员",
          "date_joined": "2023-01-01T12:00:00Z"
        }
      ]
    }
  }
  ```

### 2. 创建新管理员

创建新的管理员用户账号。

- **URL**: `/`
- **方法**: `POST`
- **权限要求**: 需要管理员权限
- **请求体**:
  ```json
  {
    "username": "newadmin",
    "email": "newadmin@example.com",
    "password": "securepassword",
    "password_confirm": "securepassword",
    "phone": "13900139000",
    "nick_name": "新管理员",
    "first_name": "张",
    "last_name": "三",
    "tenant_id": 1
  }
  ```

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2001,
    "message": "创建成功",
    "data": {
      "id": 10,
      "username": "newadmin",
      "email": "newadmin@example.com",
      "phone": "13900139000",
      "nick_name": "新管理员",
      "tenant": 1,
      "tenant_name": "测试租户",
      "is_admin": true,
      "is_member": false,
      "is_super_admin": false,
      "role": "租户管理员",
      "date_joined": "2023-01-05T12:00:00Z"
    }
  }
  ```

### 3. 获取单个管理员详情

获取单个管理员用户的详细信息。

- **URL**: `/<id>/`
- **方法**: `GET`
- **权限要求**: 需要管理员权限
- **URL参数**:
  - `id`: 管理员用户ID

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "获取成功",
    "data": {
      "id": 10,
      "username": "newadmin",
      "email": "newadmin@example.com",
      "phone": "13900139000",
      "nick_name": "新管理员",
      "first_name": "张",
      "last_name": "三",
      "is_active": true,
      "avatar": "/media/avatars/newadmin.png",
      "tenant": 1,
      "tenant_name": "测试租户",
      "is_admin": true,
      "is_member": false,
      "is_super_admin": false,
      "role": "租户管理员",
      "date_joined": "2023-01-05T12:00:00Z"
    }
  }
  ```

### 4. 更新单个管理员信息

更新指定管理员用户的信息。

- **URL**: `/<id>/`
- **方法**: `PUT`
- **权限要求**: 需要管理员权限
- **URL参数**:
  - `id`: 管理员用户ID
- **请求体**:
  ```json
  {
    "phone": "13900139001",
    "nick_name": "更新后的昵称",
    "first_name": "李",
    "last_name": "四",
    "is_active": true,
    "status": "active"
  }
  ```

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "更新成功",
    "data": {
      "id": 10,
      "username": "newadmin",
      "email": "newadmin@example.com",
      "phone": "13900139001",
      "nick_name": "更新后的昵称",
      "first_name": "李",
      "last_name": "四",
      "is_active": true,
      "avatar": "/media/avatars/newadmin.png",
      "tenant": 1,
      "tenant_name": "测试租户",
      "is_admin": true,
      "is_member": false,
      "is_super_admin": false,
      "role": "租户管理员",
      "date_joined": "2023-01-05T12:00:00Z"
    }
  }
  ```

### 5. 删除单个管理员

删除指定的管理员用户(软删除)。

- **URL**: `/<id>/`
- **方法**: `DELETE`
- **权限要求**: 需要管理员权限
- **URL参数**:
  - `id`: 管理员用户ID

- **成功响应**:
  - 状态码: `204 No Content`

### 6. 获取当前登录管理员信息

获取当前登录的管理员用户详细信息。

- **URL**: `/me/`
- **方法**: `GET`
- **权限要求**: 需要管理员权限

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "获取成功",
    "data": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "phone": "13800138000",
      "nick_name": "系统管理员",
      "first_name": "",
      "last_name": "",
      "is_active": true,
      "avatar": "/media/avatars/admin.png",
      "tenant": null,
      "tenant_name": null,
      "is_admin": true,
      "is_member": false,
      "is_super_admin": true,
      "role": "超级管理员",
      "date_joined": "2023-01-01T12:00:00Z"
    }
  }
  ```

### 7. 更新当前登录管理员信息

更新当前登录的管理员用户基本信息。

- **URL**: `/me/`
- **方法**: `PUT`
- **权限要求**: 需要管理员权限
- **请求体**:
  ```json
  {
    "phone": "13800138001",
    "nick_name": "新昵称",
    "first_name": "管理",
    "last_name": "员"
  }
  ```

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "更新成功",
    "data": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "phone": "13800138001",
      "nick_name": "新昵称",
      "first_name": "管理",
      "last_name": "员",
      "is_active": true,
      "avatar": "/media/avatars/admin.png",
      "tenant": null,
      "tenant_name": null,
      "is_admin": true,
      "is_member": false,
      "is_super_admin": true,
      "role": "超级管理员",
      "date_joined": "2023-01-01T12:00:00Z"
    }
  }
  ```

### 8. 修改当前登录管理员密码

修改当前登录的管理员用户密码。

- **URL**: `/me/password/`
- **方法**: `POST`
- **权限要求**: 需要管理员权限
- **请求体**:
  ```json
  {
    "old_password": "oldpassword",
    "new_password": "newpassword",
    "new_password_confirm": "newpassword"
  }
  ```

- **成功响应**:
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

### 9. 授予超级管理员权限

将指定管理员提升为超级管理员。

- **URL**: `/<id>/grant-super-admin/`
- **方法**: `POST`
- **权限要求**: 需要超级管理员权限
- **URL参数**:
  - `id`: 管理员用户ID

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "授权成功",
    "data": {
      "detail": "已成功授予超级管理员权限"
    }
  }
  ```

### 10. 撤销超级管理员权限

撤销指定管理员的超级管理员权限。

- **URL**: `/<id>/revoke-super-admin/`
- **方法**: `POST`
- **权限要求**: 需要超级管理员权限
- **URL参数**:
  - `id`: 管理员用户ID
- **请求体**:
  ```json
  {
    "tenant_id": 1
  }
  ```

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "撤销成功",
    "data": {
      "detail": "已成功撤销超级管理员权限，并设置为租户管理员"
    }
  }
  ```

### 11. 创建超级管理员

创建新的超级管理员账号。

- **URL**: `/super-admin/create/`
- **方法**: `POST`
- **权限要求**: 需要超级管理员权限
- **请求体**:
  ```json
  {
    "username": "newsuperadmin",
    "email": "newsuperadmin@example.com",
    "password": "securepassword",
    "password_confirm": "securepassword",
    "phone": "13900139002",
    "nick_name": "新超级管理员"
  }
  ```

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2001,
    "message": "创建成功",
    "data": {
      "id": 11,
      "username": "newsuperadmin",
      "email": "newsuperadmin@example.com",
      "phone": "13900139002",
      "nick_name": "新超级管理员",
      "tenant": null,
      "tenant_name": null,
      "is_admin": true,
      "is_member": false,
      "is_super_admin": true,
      "role": "超级管理员",
      "date_joined": "2023-01-10T12:00:00Z"
    }
  }
  ```

### 12. 上传当前管理员头像

上传并更新当前登录管理员的头像图片。

- **URL**: `/avatar/upload/`
- **方法**: `POST`
- **权限要求**: 需要管理员权限
- **内容类型**: `multipart/form-data`
- **表单字段**:
  - `avatar`: 图片文件 (JPG, PNG, GIF, WEBP 或 BMP)

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "头像上传成功",
    "data": {
      "detail": "头像上传成功",
      "avatar": "/media/avatars/admin-123456.jpg"
    }
  }
  ```

### 13. 为特定管理员上传头像

管理员为指定管理员上传头像。

- **URL**: `/<id>/avatar/upload/`
- **方法**: `POST`
- **权限要求**: 需要管理员权限
- **URL参数**:
  - `id`: 管理员用户ID
- **内容类型**: `multipart/form-data`
- **表单字段**:
  - `avatar`: 图片文件 (JPG, PNG, GIF, WEBP 或 BMP)

- **成功响应**:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "头像上传成功",
    "data": {
      "detail": "头像上传成功",
      "avatar": "/media/avatars/newadmin-123456.jpg"
    }
  }
  ```

## 错误响应

### 1. 未认证错误

- 状态码: `401 Unauthorized`
- 响应体:
  ```json
  {
    "success": false,
    "code": 4001,
    "message": "未认证或认证已过期",
    "data": {
      "detail": "身份认证信息未提供。"
    }
  }
  ```

### 2. 权限错误

- 状态码: `403 Forbidden`
- 响应体:
  ```json
  {
    "success": false,
    "code": 4003,
    "message": "权限不足",
    "data": {
      "detail": "您没有执行该操作的权限。"
    }
  }
  ```

### 3. 资源不存在

- 状态码: `404 Not Found`
- 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "资源不存在",
    "data": {
      "detail": "未找到。"
    }
  }
  ```

### 4. 请求验证错误

- 状态码: `400 Bad Request`
- 响应体:
  ```json
  {
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
      "username": ["该字段不能为空。"],
      "email": ["请输入一个有效的电子邮件地址。"]
    }
  }
  ```

## 状态码说明

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `204 No Content`: 删除成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或认证已过期
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

## 前端API封装示例

以下是一个使用Axios封装管理员用户API的示例代码：

```javascript
// admin-users.js

import axios from 'axios';

const BASE_URL = '/api/v1/admin-users';

export default {
  // 获取管理员列表
  getAdminUsers(params = {}) {
    return axios.get(BASE_URL, { params });
  },

  // 获取单个管理员详情
  getAdminUser(id) {
    return axios.get(`${BASE_URL}/${id}/`);
  },

  // 创建新管理员
  createAdminUser(data) {
    return axios.post(BASE_URL, data);
  },

  // 更新管理员信息
  updateAdminUser(id, data) {
    return axios.put(`${BASE_URL}/${id}/`, data);
  },

  // 删除管理员
  deleteAdminUser(id) {
    return axios.delete(`${BASE_URL}/${id}/`);
  },

  // 获取当前管理员信息
  getCurrentAdmin() {
    return axios.get(`${BASE_URL}/me/`);
  },

  // 更新当前管理员信息
  updateCurrentAdmin(data) {
    return axios.put(`${BASE_URL}/me/`, data);
  },

  // 修改当前管理员密码
  changePassword(data) {
    return axios.post(`${BASE_URL}/me/password/`, data);
  },

  // 授予超级管理员权限
  grantSuperAdmin(id) {
    return axios.post(`${BASE_URL}/${id}/grant-super-admin/`);
  },

  // 撤销超级管理员权限
  revokeSuperAdmin(id, data) {
    return axios.post(`${BASE_URL}/${id}/revoke-super-admin/`, data);
  },

  // 创建超级管理员
  createSuperAdmin(data) {
    return axios.post(`${BASE_URL}/super-admin/create/`, data);
  },

  // 上传当前管理员头像
  uploadAvatar(file) {
    const formData = new FormData();
    formData.append('avatar', file);
    return axios.post(`${BASE_URL}/avatar/upload/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  // 为特定管理员上传头像
  uploadUserAvatar(id, file) {
    const formData = new FormData();
    formData.append('avatar', file);
    return axios.post(`${BASE_URL}/${id}/avatar/upload/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};
``` 