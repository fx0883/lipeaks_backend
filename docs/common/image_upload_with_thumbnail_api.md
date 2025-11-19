# 图片上传并生成缩略图API使用指南

## 概述

图片上传并生成缩略图API提供了一个专用接口，允许已登录用户上传图片文件到系统中，系统会自动生成缩略图，并返回原图和缩略图的可访问URL。该API支持多种图片格式，并根据用户类型（普通租户用户或超级管理员）自动确定文件存储路径。

## API端点

```
POST /api/v1/common/upload-image-with-thumbnail/
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

## 缩略图规格

- **宽度**：固定200px（无论原图大小，都会调整到200px宽）
- **高度**：自适应（保持原图宽高比）
- **格式**：JPEG
- **质量**：85
- **命名规则**：原图文件名UUID + `_thumb_small.jpg`
- **缩放行为**：
  - 原图宽度 > 200px：缩小到200px
  - 原图宽度 < 200px：放大到200px
  - 原图宽度 = 200px：保持200px

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
  "message": "图片上传成功",
  "data": {
    "url": "http://example.com/media/uploads/17/hello/c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "filename": "c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "size": 235065,
    "thumbnail_url": "http://example.com/media/uploads/17/hello/c96f4957-af76-456b-80cc-5a343f927cd3_thumb_small.jpg",
    "thumbnail_filename": "c96f4957-af76-456b-80cc-5a343f927cd3_thumb_small.jpg",
    "thumbnail_size": 15234
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| url | 字符串 | 原图的完整URL路径，可直接访问 |
| filename | 字符串 | 原图在服务器上的文件名（UUID格式，保证唯一性） |
| size | 整数 | 原图文件大小（字节） |
| thumbnail_url | 字符串 | 缩略图的完整URL路径，可直接访问 |
| thumbnail_filename | 字符串 | 缩略图在服务器上的文件名 |
| thumbnail_size | 整数 | 缩略图文件大小（字节） |

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

#### 文件为空 (HTTP 400)

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "detail": "文件为空，请上传有效的图片文件"
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

#### 缩略图生成失败 (HTTP 500)

```json
{
  "success": false,
  "code": 5000,
  "message": "服务器内部错误",
  "data": {
    "detail": "生成缩略图失败: [错误详情]"
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
    "detail": "图片上传失败: [错误详情]"
  }
}
```

## 使用示例

### cURL

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/common/upload-image-with-thumbnail/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@image.png;type=image/png' \
  -F 'folder=product_images'
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/common/upload-image-with-thumbnail/"
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}
files = {
    "file": open("image.png", "rb")
}
data = {
    "folder": "product_images"
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### JavaScript (Fetch API)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('folder', 'product_images');

fetch('http://localhost:8000/api/v1/common/upload-image-with-thumbnail/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
  },
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('原图URL:', data.data.url);
  console.log('缩略图URL:', data.data.thumbnail_url);
})
.catch(error => console.error('Error:', error));
```

## 最佳实践

1. **文件类型验证**：虽然服务器会验证文件类型，但前端也应该进行初步验证，提高用户体验。

2. **文件大小限制**：在前端限制文件大小，避免用户上传过大的文件导致请求失败。

3. **文件夹命名**：使用有意义的文件夹名称，如 `avatars`、`product_images`、`blog_posts` 等，以便于管理和组织文件。

4. **错误处理**：妥善处理上传过程中可能出现的各种错误，并向用户提供清晰的错误提示。

5. **并发控制**：避免同时上传大量文件，可能导致服务器压力过大。

6. **缩略图使用**：对于列表页、预览等场景，优先使用缩略图以提高加载速度和用户体验。

7. **原图使用**：仅在需要查看完整图片时才加载原图。

## 与普通上传接口的区别

| 特性 | 普通上传接口 | 图片上传带缩略图接口 |
|------|------------|-------------------|
| 端点 | `/api/v1/common/upload-file/` | `/api/v1/common/upload-image-with-thumbnail/` |
| 返回内容 | 仅原图信息 | 原图 + 缩略图信息 |
| 缩略图生成 | 否 | 是（200px宽，保持宽高比） |
| 适用场景 | 通用文件上传 | 需要缩略图的图片上传 |
| 性能影响 | 较小 | 略大（需生成缩略图） |

## 常见问题

### Q: 上传失败，返回401错误

A: 检查您的JWT令牌是否有效，可能已经过期或无效。需要重新登录获取新的令牌。

### Q: 上传失败，返回"文件太大"错误

A: 确保上传的文件不超过5MB。如果需要上传更大的文件，请联系系统管理员调整限制。

### Q: 如何获取上传后的原图和缩略图URL？

A: 成功上传后，响应的`data.url`字段包含原图URL，`data.thumbnail_url`字段包含缩略图URL，可以直接用于访问或显示。

### Q: 上传的文件会自动重命名吗？

A: 是的，为了避免文件名冲突，系统会使用UUID格式自动生成唯一的文件名。原始文件名不会保留。

### Q: 缩略图的尺寸是固定的吗？

A: 缩略图宽度固定为200px，高度会根据原图的宽高比自动计算，以保持图片不变形。无论原图是大于还是小于200px，都会调整到200px宽度。

### Q: 如果缩略图生成失败会怎样？

A: 如果缩略图生成失败，系统会自动删除已上传的原图，并返回500错误，确保数据一致性。

### Q: 支持哪些图片格式？

A: 支持JPG、JPEG、PNG、GIF、WEBP和BMP格式。PNG透明背景会自动转换为白色背景。

### Q: 缩略图的质量如何？

A: 缩略图使用JPEG格式，质量设置为85，在保证清晰度的同时有效控制文件大小。

## 技术细节

### 缩略图生成算法

1. 使用Pillow库的`resize()`方法生成缩略图
2. 采用LANCZOS重采样算法，保证缩略图质量
3. 自动处理RGBA、LA、P等颜色模式，转换为RGB
4. PNG透明背景自动转换为白色背景
5. 无论原图大小，都会调整到200px宽度（支持放大和缩小）
6. 保持原图宽高比，高度自动计算

### 文件命名规则

- 原图：`{UUID}{原扩展名}`，例如：`c96f4957-af76-456b-80cc-5a343f927cd3.png`
- 缩略图：`{UUID}_thumb_small.jpg`，例如：`c96f4957-af76-456b-80cc-5a343f927cd3_thumb_small.jpg`

### 错误处理机制

- 如果缩略图生成失败，系统会自动删除已上传的原图
- 确保原图和缩略图要么同时存在，要么都不存在
- 所有错误都会记录到日志系统，便于排查问题
