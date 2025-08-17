# 文件上传API使用指南

## 概述

文件上传API提供了一个通用的接口，允许已登录用户上传图片文件到系统中，并返回可访问的URL。该API支持多种图片格式，并根据用户类型（普通租户用户或超级管理员）自动确定文件存储路径。

## API端点

```
POST /api/v1/common/upload-file/
```

## 权限要求

- 用户必须已登录（需要有效的JWT令牌）
- 支持所有类型的已认证用户（超级管理员、租户管理员和普通成员）

## 请求格式

### 请求头

| 头部名称 | 必填 | 说明 |
|---------|------|------|
| Authorization | 是 | Bearer token格式的JWT令牌 |
| Content-Type | 是 | 必须为 `multipart/form-data` |

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| file | 文件 | 是 | 要上传的图片文件，支持JPG、JPEG、PNG、GIF、WEBP或BMP格式 |
| folder | 字符串 | 否 | 可选的存储子文件夹名称，用于组织文件 |

### 文件限制

- 支持的文件格式：JPG、JPEG、PNG、GIF、WEBP、BMP
- 最大文件大小：5MB

## 文件存储路径规则

上传的文件路径取决于用户类型和是否提供了folder参数：

### 普通租户用户

- 默认情况下，文件存储在 `uploads/租户ID/` 目录
- 如果提供了folder参数，则文件存储在 `uploads/租户ID/{folder}/` 目录
- 如果用户没有关联租户，则使用 `uploads/user_{user.id}/` 目录

### 超级管理员

- 默认情况下，文件存储在 `uploads/super_admin/` 目录
- 如果提供了folder参数，则文件存储在 `uploads/super_admin/{folder}/` 目录

## 响应格式

### 成功响应 (HTTP 200)

```json
{
  "success": true,
  "code": 2000,
  "message": "文件上传成功",
  "data": {
    "url": "http://example.com/media/uploads/17/hello/c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "filename": "c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "size": 235065
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| url | 字符串 | 上传文件的完整URL路径，可直接访问 |
| filename | 字符串 | 服务器上的文件名（UUID格式，保证唯一性） |
| size | 整数 | 文件大小（字节） |

### 错误响应

#### 未提供文件 (HTTP 400)

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "detail": "未提供文件"
  }
}
```

#### 不支持的文件类型 (HTTP 400)

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

#### 文件太大 (HTTP 400)

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "detail": "文件太大，图片大小不能超过5MB"
  }
}
```

#### 未认证 (HTTP 401)

```json
{
  "success": false,
  "code": 4001,
  "message": "认证失败",
  "data": {
    "detail": "身份验证凭据未提供或已过期"
  }
}
```

#### 服务器错误 (HTTP 500)

```json
{
  "success": false,
  "code": 5000,
  "message": "服务器内部错误",
  "data": {
    "detail": "文件上传失败: [错误详情]"
  }
}
```

## 使用示例

### cURL

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/common/upload-file/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@image.png;type=image/png' \
  -F 'folder=project_images'
```

## 最佳实践

1. **文件类型验证**：虽然服务器会验证文件类型，但前端也应该进行初步验证，提高用户体验。

2. **文件大小限制**：在前端限制文件大小，避免用户上传过大的文件导致请求失败。

3. **文件夹命名**：使用有意义的文件夹名称，如 `avatars`、`product_images`、`blog_posts` 等，以便于管理和组织文件。

4. **错误处理**：妥善处理上传过程中可能出现的各种错误，并向用户提供清晰的错误提示。

5. **并发控制**：避免同时上传大量文件，可能导致服务器压力过大。

## 常见问题

### Q: 上传失败，返回401错误

A: 检查您的JWT令牌是否有效，可能已经过期或无效。需要重新登录获取新的令牌。

### Q: 上传失败，返回"文件太大"错误

A: 确保上传的文件不超过5MB。如果需要上传更大的文件，请联系系统管理员调整限制。

### Q: 如何获取上传后的文件URL？

A: 成功上传后，响应的`data.url`字段包含完整的文件URL，可以直接用于访问或显示该文件。

### Q: 上传的文件会自动重命名吗？

A: 是的，为了避免文件名冲突，系统会使用UUID格式自动生成唯一的文件名。原始文件名不会保留。 