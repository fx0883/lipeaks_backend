# 反馈附件 API 文档

## 概述

反馈附件API提供文件上传、下载和管理功能，支持截图、日志文件等多种格式。

---

## 1. 获取附件列表

### 基本信息
- **接口**: `GET /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/`
- **权限**: 需要认证
- **说明**: 获取指定反馈的所有附件

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| feedback_pk | int | 反馈ID |

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": [
        {
            "id": 1,
            "file": "http://localhost:8000/media/feedbacks/attachments/2025/11/screenshot.png",
            "file_url": "http://localhost:8000/media/feedbacks/attachments/2025/11/screenshot.png",
            "filename": "screenshot.png",
            "file_size": 245678,
            "mime_type": "image/png",
            "uploaded_by": 3,
            "created_at": "2025-11-23T13:47:44Z"
        },
        {
            "id": 2,
            "file": "http://localhost:8000/media/feedbacks/attachments/2025/11/error.log",
            "file_url": "http://localhost:8000/media/feedbacks/attachments/2025/11/error.log",
            "filename": "error.log",
            "file_size": 12345,
            "mime_type": "text/plain",
            "uploaded_by": 3,
            "created_at": "2025-11-23T13:48:00Z"
        }
    ]
}
```

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/27/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 2. 上传附件

### 基本信息
- **接口**: `POST /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/`
- **权限**: 需要认证
- **说明**: 
  - 支持多种文件格式
  - 文件大小限制：10MB
  - 自动提取文件元数据（名称、大小、MIME类型）

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| feedback_pk | int | 反馈ID |

### 请求参数（FormData）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 要上传的文件 |

### 支持的文件格式

| 类别 | 扩展名 | 说明 |
|------|--------|------|
| 图片 | jpg, jpeg, png, gif | 截图、示意图 |
| 文档 | pdf, doc, docx, txt | 文档资料 |
| 日志 | log | 错误日志 |
| 压缩包 | zip | 批量文件 |

### 文件大小限制

- 单个文件最大：**10MB**
- 建议图片压缩后上传以提高速度

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 1,
        "file": "http://localhost:8000/media/feedbacks/attachments/2025/11/test_attachment.txt",
        "file_url": "http://localhost:8000/media/feedbacks/attachments/2025/11/test_attachment.txt",
        "filename": "test_attachment.txt",
        "file_size": 18,
        "mime_type": "text/plain",
        "uploaded_by": 3,
        "created_at": "2025-11-23T13:47:44Z"
    }
}
```

### curl 示例

```bash
# 上传图片
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/screenshot.png"

# 上传日志文件
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/error.log"

# 上传PDF文档
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

---

## 3. 获取附件详情

### 基本信息
- **接口**: `GET /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/{id}/`
- **权限**: 需要认证
- **说明**: 获取指定附件的详细信息

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| feedback_pk | int | 反馈ID |
| id | int | 附件ID |

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 1,
        "file": "http://localhost:8000/media/feedbacks/attachments/2025/11/test_attachment.txt",
        "file_url": "http://localhost:8000/media/feedbacks/attachments/2025/11/test_attachment.txt",
        "filename": "test_attachment.txt",
        "file_size": 18,
        "mime_type": "text/plain",
        "uploaded_by": 3,
        "created_at": "2025-11-23T13:47:44Z"
    }
}
```

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/27/attachments/1/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 4. 删除附件

### 基本信息
- **接口**: `DELETE /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/{id}/`
- **权限**: 需要认证，仅附件上传者或管理员
- **说明**: 软删除附件（标记为已删除，不真正删除文件）

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| feedback_pk | int | 反馈ID |
| id | int | 附件ID |

### 响应

成功返回 HTTP 204 No Content

### curl 示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/feedbacks/27/attachments/1/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 使用场景示例

### 场景1：提交Bug时上传截图

```bash
# 1. 创建反馈
FEEDBACK_ID=$(curl -s -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "登录按钮显示异常",
    "description": "登录按钮在Chrome浏览器中显示不正常",
    "feedback_type": "bug",
    "priority": "medium"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])")

# 2. 上传截图
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/login_button_bug.png"

# 3. 上传浏览器控制台日志
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/console.log"
```

### 场景2：批量上传多个文件

```bash
FEEDBACK_ID=27

# 上传多个截图
for file in screenshot1.png screenshot2.png screenshot3.png; do
  curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/attachments/" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -F "file=@${file}"
done
```

### 场景3：下载附件

```bash
# 1. 获取附件列表
ATTACHMENTS=$(curl -s -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/27/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN")

# 2. 提取文件URL并下载
FILE_URL=$(echo $ATTACHMENTS | python3 -c "import sys, json; print(json.load(sys.stdin)['data'][0]['file_url'])")

# 3. 下载文件
curl -O "$FILE_URL"
```

---

## 最佳实践

### 1. 文件命名

推荐使用描述性文件名：
- ✅ `login_error_screenshot_chrome.png`
- ✅ `backend_error_20231123.log`
- ❌ `IMG_1234.png`
- ❌ `untitled.txt`

### 2. 图片优化

上传前压缩图片可以：
- 加快上传速度
- 节省存储空间
- 提高页面加载速度

```bash
# 使用ImageMagick压缩图片
convert screenshot.png -quality 85 -resize 1920x1080\> screenshot_compressed.png

# 上传压缩后的图片
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@screenshot_compressed.png"
```

### 3. 日志文件处理

对于大型日志文件：
```bash
# 提取关键错误信息
grep "ERROR" app.log > errors_only.log

# 压缩日志
zip error_logs.zip errors_only.log

# 上传压缩包
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@error_logs.zip"
```

### 4. 多文件上传脚本

创建一个便捷的上传脚本：

```bash
#!/bin/bash
# upload_attachments.sh

FEEDBACK_ID=$1
TOKEN=$2
shift 2

for file in "$@"; do
  echo "Uploading $file..."
  curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/${FEEDBACK_ID}/attachments/" \
    -H "Authorization: Bearer ${TOKEN}" \
    -F "file=@${file}"
  echo ""
done

echo "All files uploaded!"
```

使用方法：
```bash
chmod +x upload_attachments.sh
./upload_attachments.sh 27 "YOUR_TOKEN" file1.png file2.log file3.pdf
```

---

## 错误处理

### 常见错误

| 错误码 | 错误信息 | 原因 | 解决方案 |
|--------|----------|------|----------|
| 400 | File size cannot exceed 10MB | 文件过大 | 压缩文件或分割上传 |
| 400 | Invalid file type | 文件格式不支持 | 使用支持的格式 |
| 404 | Feedback not found | 反馈不存在 | 检查反馈ID |
| 413 | Request Entity Too Large | 请求体过大 | 减小文件大小 |
| 415 | Unsupported Media Type | 不支持的文件类型 | 转换为支持的格式 |

### 错误响应示例

#### 文件过大
```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "file": [
            "File size cannot exceed 10MB."
        ]
    }
}
```

#### 文件格式不支持
```json
{
    "success": false,
    "code": 4150,
    "message": "不支持的文件类型",
    "data": {
        "file": [
            "File extension 'exe' is not allowed. Supported extensions: jpg, jpeg, png, gif, pdf, doc, docx, txt, log, zip"
        ]
    }
}
```

---

## 技术说明

### 文件存储路径

文件存储在服务器的以下路径：
```
media/feedbacks/attachments/YYYY/MM/filename
```

示例：
```
media/feedbacks/attachments/2025/11/screenshot.png
```

### MIME类型自动检测

系统会自动检测文件的MIME类型：

| 扩展名 | MIME类型 |
|--------|----------|
| .jpg, .jpeg | image/jpeg |
| .png | image/png |
| .gif | image/gif |
| .pdf | application/pdf |
| .txt | text/plain |
| .log | text/plain |
| .zip | application/zip |
| .doc | application/msword |
| .docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document |

### 文件元数据

上传时自动提取的元数据：
- `filename`: 原始文件名
- `file_size`: 文件大小（字节）
- `mime_type`: MIME类型
- `uploaded_by`: 上传用户ID
- `created_at`: 上传时间

---

## 安全注意事项

1. **文件验证**：
   - 仅允许特定扩展名
   - 检查文件大小
   - 验证MIME类型

2. **路径安全**：
   - 文件名会被清理
   - 使用UUID避免冲突
   - 防止路径遍历攻击

3. **访问控制**：
   - 需要认证才能上传
   - 租户隔离
   - 权限验证

4. **病毒扫描**（推荐）：
   - 建议在生产环境集成病毒扫描
   - 可使用ClamAV等开源方案

---

## 性能优化建议

1. **CDN集成**：
   - 将附件托管到CDN
   - 加快全球访问速度

2. **懒加载**：
   - 前端实现图片懒加载
   - 只在需要时下载附件

3. **缩略图**：
   - 为图片生成缩略图
   - 列表页显示缩略图，详情页显示原图

4. **异步处理**：
   - 大文件异步上传
   - 后台处理图片压缩
