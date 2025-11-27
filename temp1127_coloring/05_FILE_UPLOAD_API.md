# Lipeaks Coloring - 文件上传 API 文档

> 通用文件和图片上传接口
> 基础URL: `http://localhost:8000`
> 通用Headers:
> - `Authorization: Bearer {token}` (必须)
> - `X-Tenant-ID: {租户ID}` (必须)

---

## 1. 上传文件

**接口**: `POST /api/v1/common/upload-file/`

**描述**: 上传通用文件

### 请求Headers
| Header | 必填 | 说明 |
|--------|------|------|
| Authorization | 是 | Bearer {token} |
| X-Tenant-ID | 是 | 租户ID |
| Content-Type | 是 | multipart/form-data |

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 要上传的文件 |
| application | integer | 否 | 应用ID (Query参数) |

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/common/upload-file/?application=6" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3" \
  -F "file=@/path/to/file.pdf"
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "文件上传成功",
  "data": {
    "url": "http://localhost:8000/media/uploads/3/files/xxx.pdf",
    "filename": "xxx.pdf",
    "size": 1024000,
    "content_type": "application/pdf"
  }
}
```

### 错误响应
| code | message | 说明 |
|------|---------|------|
| 4000 | 文件不能为空 | 未提供文件 |
| 4000 | 文件类型不支持 | 不允许的文件类型 |
| 4000 | 文件大小超过限制 | 文件太大 |

---

## 2. 上传图片（自动生成缩略图）

**接口**: `POST /api/v1/common/upload-image-with-thumbnail/`

**描述**: 上传图片并自动生成缩略图

### 请求Headers
| Header | 必填 | 说明 |
|--------|------|------|
| Authorization | 是 | Bearer {token} |
| X-Tenant-ID | 是 | 租户ID |
| Content-Type | 是 | multipart/form-data |

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 要上传的图片文件 |
| application | integer | 否 | 应用ID (Query参数) |

### curl 示例
```bash
curl -X POST "http://localhost:8000/api/v1/common/upload-image-with-thumbnail/?application=6" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 3" \
  -F "file=@/path/to/image.jpg"
```

### 成功响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "图片上传成功",
  "data": {
    "url": "http://localhost:8000/media/uploads/3/images/xxx.jpg",
    "thumbnail_url": "http://localhost:8000/media/uploads/3/images/xxx_thumb.jpg",
    "thumbnail_small_url": "http://localhost:8000/media/uploads/3/images/xxx_thumb_small.jpg",
    "filename": "xxx.jpg",
    "size": 512000,
    "width": 1920,
    "height": 1080,
    "content_type": "image/jpeg"
  }
}
```

### 响应参数说明
| 参数 | 类型 | 说明 |
|------|------|------|
| url | string | 原图URL |
| thumbnail_url | string | 中等缩略图URL |
| thumbnail_small_url | string | 小缩略图URL |
| filename | string | 文件名 |
| size | integer | 文件大小（字节） |
| width | integer | 图片宽度 |
| height | integer | 图片高度 |
| content_type | string | MIME类型 |

### 支持的图片格式
- JPEG/JPG
- PNG
- GIF
- WebP
- BMP

### 错误响应
| code | message | 说明 |
|------|---------|------|
| 4000 | 文件不能为空 | 未提供文件 |
| 4000 | 请上传有效的图片文件 | 非图片文件 |
| 4000 | 图片大小超过限制 | 图片太大 |

---

## 文件存储说明

### 存储路径规则
文件会按照以下规则存储:
```
/media/uploads/{tenant_id}/{type}/{filename}
```

- `tenant_id`: 租户ID
- `type`: 文件类型目录 (files/images/avatars等)
- `filename`: UUID生成的唯一文件名

### 缩略图尺寸
- `_thumb`: 中等缩略图，最大宽度 400px
- `_thumb_small`: 小缩略图，最大宽度 200px

### 文件大小限制
- 普通文件: 最大 50MB
- 图片文件: 最大 20MB

---

## 错误响应通用说明

| code | 说明 |
|------|------|
| 2000 | 成功 |
| 4000 | 请求参数错误 |
| 4001 | 认证失败 |
| 4003 | 权限不足 |
| 5000 | 服务器内部错误 |
