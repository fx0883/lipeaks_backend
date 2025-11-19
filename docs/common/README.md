# Common模块API文档

本目录包含Common模块的所有API接口文档。

## 文档列表

### 文件上传相关

1. **[file_upload_api.md](file_upload_api.md)** - 通用文件上传API
   - 端点: `POST /api/v1/common/upload-file/`
   - 功能: 上传图片文件并返回URL
   - 适用场景: 通用图片上传

2. **[image_upload_with_thumbnail_api.md](image_upload_with_thumbnail_api.md)** - 图片上传并生成缩略图API
   - 端点: `POST /api/v1/common/upload-image-with-thumbnail/`
   - 功能: 上传图片文件，自动生成缩略图，返回原图和缩略图URL
   - 适用场景: 需要缩略图的图片上传（如商品图片、用户头像等）
   - 缩略图规格: 宽度200px，高度自适应，JPEG质量85

## 快速选择指南

### 何时使用通用文件上传API？

- 只需要上传原图，不需要缩略图
- 上传后只在少数场景下展示图片
- 对加载速度要求不高

### 何时使用图片上传并生成缩略图API？

- 需要在列表页、预览等场景展示图片
- 希望提高页面加载速度
- 需要优化用户体验
- 商品图片、用户头像、文章封面等场景

## 接口对比

| 特性 | 通用上传 | 带缩略图上传 |
|------|---------|------------|
| 端点 | `/upload-file/` | `/upload-image-with-thumbnail/` |
| 返回字段数 | 3个 | 6个 |
| 缩略图 | ❌ | ✅ |
| 处理时间 | 快 | 略慢 |
| 适用场景 | 通用 | 图片展示 |

## 更新日志

- **2024-11-16**: 新增图片上传并生成缩略图API
- **2024-10-XX**: 初始版本，通用文件上传API
