# 成员头像上传 API

本文档详细描述了与成员(Member)头像上传相关的API端点。

## 1. 上传当前成员头像

上传并更新当前登录成员的头像图片。

- **URL**: `/api/v1/members/avatar/upload/`
- **Method**: `POST`
- **权限要求**: 需要成员身份验证，子账号不允许更改头像
- **Content-Type**: `multipart/form-data`

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| avatar | file | 是 | 要上传的头像文件，支持JPG、PNG、GIF、WEBP或BMP格式，大小不超过2MB |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {
    "avatar": "http://localhost:8000/media/avatars/d0070ec2-78ce-45aa-b00f-47d91c84dd61.webp"
  }
}
```

### 错误响应

#### 400 请求参数错误

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "detail": "未提供头像文件"
  }
}
```

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "detail": "不支持的文件类型，请上传JPG、PNG、GIF、WEBP或BMP格式的图片"
  }
}
```

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "detail": "文件太大，头像大小不能超过2MB"
  }
}
```

#### 403 权限不足

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": {
    "detail": "该接口仅适用于普通用户"
  }
}
```

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": {
    "detail": "子账号不允许更改头像"
  }
}
```

#### 500 服务器内部错误

```json
{
  "success": false,
  "code": 5000,
  "message": "服务器内部错误",
  "data": {
    "detail": "头像上传失败: [错误详情]"
  }
}
```

## 2. 为特定成员上传头像

允许管理员和普通用户为特定成员上传头像。租户管理员只能为其所属租户的成员上传头像，超级管理员可以为任何成员上传头像，普通用户只能为自己的子账号上传头像。

- **URL**: `/api/v1/members/{id}/avatar/upload/`
- **Method**: `POST`
- **权限要求**: 超级管理员可为任何成员上传头像；租户管理员只能为自己租户的成员上传头像；普通用户只能为自己的子账号上传头像
- **Content-Type**: `multipart/form-data`

### 路径参数

| 参数名 | 类型 | 描述 |
|-------|------|------|
| id | integer | 成员ID |

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| avatar | file | 是 | 要上传的头像文件，支持JPG、PNG、GIF、WEBP或BMP格式，大小不超过2MB |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {
    "avatar": "http://localhost:8000/media/avatars/d0070ec2-78ce-45aa-b00f-47d91c84dd61.webp"
  }
}
```

### 错误响应

#### 400 请求参数错误

与上传当前成员头像API的错误响应相同。

#### 403 权限不足

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": {
    "detail": "您只能为自己的子账号上传头像"
  }
}
```

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": {
    "detail": "您没有权限为该普通用户上传头像"
  }
}
```

#### 404 资源不存在

```json
{
  "success": false,
  "code": 4004,
  "message": "资源不存在",
  "data": {
    "detail": "普通用户不存在"
  }
}
```

#### 500 服务器内部错误

```json
{
  "success": false,
  "code": 5000,
  "message": "服务器内部错误",
  "data": {
    "detail": "头像上传失败: [错误详情]"
  }
}
```

## 技术实现说明

1. 头像文件会保存在服务器的`media/avatars/`目录下
2. 文件名会使用UUID生成，以避免文件名冲突
3. 上传新头像时，会自动删除旧的头像文件（如果存在）
4. 返回的头像URL会包含完整的域名和协议 