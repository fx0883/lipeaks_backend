# 图片上传API文档

本项目提供两个图片上传API，用于不同场景的图片上传需求。

---

## API 1: 通用文件上传

### 基本信息

| 项目 | 说明 |
|------|------|
| 端点 | `POST /api/v1/common/upload-file/` |
| 功能 | 上传图片文件并返回访问URL |
| 权限 | 需要JWT认证（已登录用户） |

### 请求格式

**请求头：**
- `Authorization`: Bearer {JWT_TOKEN}
- `Content-Type`: multipart/form-data

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| file | 文件 | 是 | 图片文件，支持JPG/JPEG/PNG/GIF/WEBP/BMP |
| folder | 字符串 | 否 | 可选的存储子文件夹名称 |

**文件限制：**
- 支持格式：JPG、JPEG、PNG、GIF、WEBP、BMP
- 最大大小：20MB

### 文件存储路径规则

| 用户类型 | 默认路径 | 带folder参数 |
|---------|---------|--------------|
| 租户用户 | `uploads/{租户ID}/` | `uploads/{租户ID}/{folder}/` |
| 超级管理员 | `uploads/super_admin/` | `uploads/super_admin/{folder}/` |

### cURL示例

```bash
# 基本上传（不指定folder）
curl -X POST 'http://localhost:8000/api/v1/common/upload-file/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/path/to/image.png'

# 指定folder上传
curl -X POST 'http://localhost:8000/api/v1/common/upload-file/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/path/to/image.png' \
  -F 'folder=avatars'
```

### 响应示例

**成功响应 (HTTP 200):**
```json
{
  "success": true,
  "code": 2000,
  "message": "文件上传成功",
  "data": {
    "url": "media/uploads/17/avatars/c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "filename": "c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "size": 235065
  }
}
```

**错误响应：**

未提供文件 (HTTP 400):
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

不支持的文件类型 (HTTP 400):
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

文件太大 (HTTP 400):
```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "detail": "文件太大，图片大小不能超过20MB"
  }
}
```

未认证 (HTTP 401):
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

---

## API 2: 图片上传并生成缩略图

### 基本信息

| 项目 | 说明 |
|------|------|
| 端点 | `POST /api/v1/common/upload-image-with-thumbnail/` |
| 功能 | 上传图片文件，自动生成缩略图，返回原图和缩略图URL |
| 权限 | 需要JWT认证（已登录用户） |

### 请求格式

**请求头：**
- `Authorization`: Bearer {JWT_TOKEN}
- `Content-Type`: multipart/form-data

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| file | 文件 | 是 | 图片文件，支持JPG/JPEG/PNG/GIF/WEBP/BMP |
| folder | 字符串 | 否 | 可选的存储子文件夹名称 |

**文件限制：**
- 支持格式：JPG、JPEG、PNG、GIF、WEBP、BMP
- 最大大小：20MB

### 缩略图规格

| 属性 | 值 |
|------|-----|
| 宽度 | 200px（固定） |
| 高度 | 自适应（保持宽高比） |
| 格式 | JPEG |
| 质量 | 85 |
| 命名规则 | `{原图UUID}_thumb_small.jpg` |

### 文件存储路径规则

与API 1相同。

### cURL示例

```bash
# 基本上传（不指定folder）
curl -X POST 'http://localhost:8000/api/v1/common/upload-image-with-thumbnail/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/path/to/image.png'

# 指定folder上传
curl -X POST 'http://localhost:8000/api/v1/common/upload-image-with-thumbnail/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/path/to/image.png' \
  -F 'folder=product_images'
```

### 响应示例

**成功响应 (HTTP 200):**
```json
{
  "success": true,
  "code": 2000,
  "message": "图片上传成功",
  "data": {
    "url": "media/uploads/17/product_images/c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "filename": "c96f4957-af76-456b-80cc-5a343f927cd3.png",
    "size": 235065,
    "thumbnail_url": "media/uploads/17/product_images/c96f4957-af76-456b-80cc-5a343f927cd3_thumb_small.jpg",
    "thumbnail_filename": "c96f4957-af76-456b-80cc-5a343f927cd3_thumb_small.jpg",
    "thumbnail_size": 15234
  }
}
```

**错误响应：**

文件为空 (HTTP 400):
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

缩略图生成失败 (HTTP 500):
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

其他错误响应与API 1相同。

---

## 两个API的对比

| 特性 | upload-file | upload-image-with-thumbnail |
|------|-------------|----------------------------|
| 端点 | `/api/v1/common/upload-file/` | `/api/v1/common/upload-image-with-thumbnail/` |
| 返回内容 | 仅原图信息 | 原图 + 缩略图信息 |
| 缩略图生成 | 否 | 是（200px宽，保持宽高比） |
| 适用场景 | 通用文件上传 | 需要缩略图的图片上传 |
| 性能影响 | 较小 | 略大（需生成缩略图） |

---

## 使用建议

1. **选择合适的API**：
   - 如果只需要原图，使用 `upload-file`
   - 如果需要列表展示/预览场景，使用 `upload-image-with-thumbnail`

2. **folder参数用途**：
   - `avatars` - 用户头像
   - `product_images` - 产品图片
   - `blog_posts` - 博客图片
   - `attachments` - 通用附件

3. **前端最佳实践**：
   - 上传前在前端验证文件类型和大小
   - 列表页使用缩略图URL，详情页使用原图URL
   - 妥善处理上传失败的情况
