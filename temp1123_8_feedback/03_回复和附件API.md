# 回复和附件 API 详细文档

## 回复管理 API

### 1. 获取回复列表

#### 基本信息
- **端点**: `GET /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/`
- **权限**: 允许匿名访问，非管理员用户不显示内部备注

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| feedback_pk | integer | 是 | 反馈 ID |

#### 响应格式

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": [
        {
            "id": 32,
            "feedback": 31,
            "user": 3,
            "user_name": "admin_cms",
            "user_email": "jackfeng8123@gmail.com",
            "content": "感谢您的反馈，我们正在处理中。",
            "is_internal_note": false,
            "email_sent": false,
            "email_sent_at": null,
            "created_at": "2025-11-25T05:26:26.522835Z",
            "updated_at": "2025-11-25T05:26:26.522875Z"
        }
    ]
}
```

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/31/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 2. 创建回复

#### 基本信息
- **端点**: `POST /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/`
- **权限**: 需要认证

#### 请求参数 (JSON Body)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 回复内容，不能为空 |
| is_internal_note | boolean | 否 | 是否为内部备注（默认 false） |

#### 响应格式

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 32,
        "feedback": 31,
        "user": 3,
        "user_name": "admin_cms",
        "user_email": "jackfeng8123@gmail.com",
        "content": "感谢您的反馈，我们正在处理中。",
        "is_internal_note": false,
        "email_sent": false,
        "email_sent_at": null,
        "created_at": "2025-11-25T05:26:26.522835Z",
        "updated_at": "2025-11-25T05:26:26.522875Z"
    }
}
```

#### curl 示例

```bash
# 创建公开回复
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/31/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "感谢您的反馈，我们正在处理中。", "is_internal_note": false}'

# 创建内部备注
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/31/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "这是内部备注，用户看不到", "is_internal_note": true}'
```

---

### 3. 获取回复详情

#### 基本信息
- **端点**: `GET /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/`
- **权限**: 允许匿名访问，非管理员用户不能访问内部备注

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| feedback_pk | integer | 是 | 反馈 ID |
| id | integer | 是 | 回复 ID |

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/31/replies/32/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 4. 更新回复

#### 基本信息
- **端点 (完整更新)**: `PUT /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/`
- **端点 (部分更新)**: `PATCH /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/`
- **权限**: 需要认证

#### 请求参数 (JSON Body)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | PUT必填 | 回复内容 |
| is_internal_note | boolean | 否 | 是否为内部备注 |

#### curl 示例

```bash
# 部分更新
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/31/replies/32/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "感谢您的反馈，问题已经修复。"}'
```

---

### 5. 删除回复

#### 基本信息
- **端点**: `DELETE /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/`
- **权限**: 需要认证
- **说明**: 软删除

#### 响应

成功时返回 HTTP 204 No Content。

#### curl 示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/feedbacks/31/replies/32/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 附件管理 API

### 1. 获取附件列表

#### 基本信息
- **端点**: `GET /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/`
- **权限**: 允许匿名访问

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| feedback_pk | integer | 是 | 反馈 ID |

#### 响应格式

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": [
        {
            "id": 3,
            "file": "http://localhost:8000/media/feedbacks/attachments/2025/11/test_attachment_NB8aU2V.txt",
            "file_url": "http://localhost:8000/media/feedbacks/attachments/2025/11/test_attachment_NB8aU2V.txt",
            "filename": "test_attachment.txt",
            "file_size": 18,
            "mime_type": "text/plain",
            "uploaded_by": 3,
            "created_at": "2025-11-25T05:26:52.415744Z"
        }
    ]
}
```

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/31/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 2. 上传附件

#### 基本信息
- **端点**: `POST /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/`
- **权限**: 允许匿名上传
- **Content-Type**: `multipart/form-data`

#### 请求参数 (Form Data)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 上传的文件 |

#### 支持的文件类型

- 图片: jpg, jpeg, png, gif
- 文档: pdf, doc, docx, txt
- 日志: log
- 压缩包: zip

#### 文件大小限制

最大 10MB

#### 响应格式

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 3,
        "file": "http://localhost:8000/media/feedbacks/attachments/2025/11/test_attachment_NB8aU2V.txt",
        "file_url": "http://localhost:8000/media/feedbacks/attachments/2025/11/test_attachment_NB8aU2V.txt",
        "filename": "test_attachment.txt",
        "file_size": 18,
        "mime_type": "text/plain",
        "uploaded_by": 3,
        "created_at": "2025-11-25T05:26:52.415744Z"
    }
}
```

#### curl 示例

```bash
# 上传文本文件
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/31/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/your/file.txt"

# 上传截图
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/31/attachments/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/screenshot.png"
```

---

### 3. 获取附件详情

#### 基本信息
- **端点**: `GET /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/{id}/`
- **权限**: 允许匿名访问

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| feedback_pk | integer | 是 | 反馈 ID |
| id | integer | 是 | 附件 ID |

#### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/31/attachments/3/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 4. 删除附件

#### 基本信息
- **端点**: `DELETE /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/{id}/`
- **权限**: 需要认证
- **说明**: 软删除

#### 响应

成功时返回 HTTP 204 No Content。

#### curl 示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/feedbacks/31/attachments/3/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 字段说明

### 回复字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 回复 ID |
| feedback | integer | 关联的反馈 ID |
| user | integer | 回复者的用户 ID |
| user_name | string | 回复者用户名 |
| user_email | string | 回复者邮箱 |
| content | string | 回复内容 |
| is_internal_note | boolean | 是否为内部备注 |
| email_sent | boolean | 是否已发送邮件通知 |
| email_sent_at | datetime | 邮件发送时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 附件字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 附件 ID |
| file | string | 文件 URL |
| file_url | string | 完整的文件访问 URL |
| filename | string | 原始文件名 |
| file_size | integer | 文件大小（字节） |
| mime_type | string | MIME 类型 |
| uploaded_by | integer | 上传者的用户 ID |
| created_at | datetime | 创建时间 |
