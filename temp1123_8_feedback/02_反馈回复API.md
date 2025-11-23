# 反馈回复 API 文档

## 概述

反馈回复API提供了对反馈进行回复、查看回复、编辑和删除回复的功能。支持公开回复和内部备注两种类型。

---

## 1. 获取反馈回复列表

### 基本信息
- **接口**: `GET /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/`
- **权限**: 需要认证
- **说明**: 
  - 普通用户只能看到非内部备注的回复
  - 管理员可以看到所有回复（包括内部备注）

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
            "feedback": 27,
            "user": 3,
            "user_name": "admin_cms",
            "user_email": "admin@example.com",
            "content": "我们已经收到您的反馈，正在处理中",
            "is_internal_note": false,
            "email_sent": true,
            "email_sent_at": "2025-11-23T14:00:00Z",
            "created_at": "2025-11-23T13:45:07Z",
            "updated_at": "2025-11-23T13:45:07Z"
        },
        {
            "id": 2,
            "feedback": 27,
            "user": 3,
            "user_name": "admin_cms",
            "user_email": "admin@example.com",
            "content": "问题已解决，请查收",
            "is_internal_note": false,
            "email_sent": true,
            "email_sent_at": "2025-11-23T15:00:00Z",
            "created_at": "2025-11-23T14:50:00Z",
            "updated_at": "2025-11-23T14:50:00Z"
        }
    ]
}
```

### curl 示例

```bash
# 获取反馈的所有回复
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 2. 创建反馈回复

### 基本信息
- **接口**: `POST /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/`
- **权限**: 需要认证（通常是管理员或客服人员）
- **说明**: 
  - 添加回复到指定反馈
  - 如果不是内部备注，会自动发送邮件通知反馈提交者
  - 系统会自动更新反馈的回复计数

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| feedback_pk | int | 反馈ID |

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| content | string | 是 | 回复内容 | - |
| is_internal_note | boolean | 否 | 是否为内部备注 | false |

**内部备注说明**：
- 内部备注（`is_internal_note: true`）只有管理员可见
- 内部备注不会发送邮件通知
- 内部备注不计入回复数量统计

### 请求示例

```json
{
    "content": "您好，我们已经收到您的反馈，正在安排技术人员处理。预计在24小时内给您回复。",
    "is_internal_note": false
}
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 30,
        "feedback": 27,
        "user": 3,
        "user_name": "admin_cms",
        "user_email": "admin@example.com",
        "content": "您好，我们已经收到您的反馈，正在安排技术人员处理。预计在24小时内给您回复。",
        "is_internal_note": false,
        "email_sent": false,
        "email_sent_at": null,
        "created_at": "2025-11-23T13:45:07Z",
        "updated_at": "2025-11-23T13:45:07Z"
    }
}
```

### curl 示例

```bash
# 添加公开回复
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "感谢您的反馈，我们正在处理"
  }'

# 添加内部备注（仅管理员可见）
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "此问题需要后端团队介入",
    "is_internal_note": true
  }'
```

---

## 3. 获取回复详情

### 基本信息
- **接口**: `GET /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/`
- **权限**: 需要认证
- **说明**: 获取指定回复的详细信息

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| feedback_pk | int | 反馈ID |
| id | int | 回复ID |

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 30,
        "feedback": 27,
        "user": 3,
        "user_name": "admin_cms",
        "user_email": "admin@example.com",
        "content": "感谢您的反馈，我们正在处理",
        "is_internal_note": false,
        "email_sent": true,
        "email_sent_at": "2025-11-23T13:46:00Z",
        "created_at": "2025-11-23T13:45:07Z",
        "updated_at": "2025-11-23T13:45:07Z"
    }
}
```

### curl 示例

```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/30/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 4. 更新回复（完整更新）

### 基本信息
- **接口**: `PUT /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/`
- **权限**: 需要认证，仅回复创建者或管理员
- **说明**: 完整更新回复内容

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| feedback_pk | int | 反馈ID |
| id | int | 回复ID |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 回复内容 |
| is_internal_note | boolean | 否 | 是否为内部备注 |

### curl 示例

```bash
curl -X PUT "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/30/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "更新后的回复内容",
    "is_internal_note": false
  }'
```

---

## 5. 更新回复（部分更新）

### 基本信息
- **接口**: `PATCH /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/`
- **权限**: 需要认证，仅回复创建者或管理员
- **说明**: 部分更新回复，只需提供要更新的字段

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 30,
        "feedback": 27,
        "user": 3,
        "user_name": "admin_cms",
        "user_email": "admin@example.com",
        "content": "更新后的回复内容",
        "is_internal_note": false,
        "email_sent": true,
        "email_sent_at": "2025-11-23T13:46:00Z",
        "created_at": "2025-11-23T13:45:07Z",
        "updated_at": "2025-11-23T13:45:22Z"
    }
}
```

### curl 示例

```bash
# 只更新内容
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/30/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "修正后的回复"
  }'

# 将公开回复改为内部备注
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/30/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_internal_note": true
  }'
```

---

## 6. 删除回复

### 基本信息
- **接口**: `DELETE /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/`
- **权限**: 需要认证，仅回复创建者或管理员
- **说明**: 软删除回复（标记为已删除，不真正删除数据）

### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| feedback_pk | int | 反馈ID |
| id | int | 回复ID |

### 响应

成功返回 HTTP 204 No Content

### curl 示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/30/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 使用场景示例

### 场景1：客服回复用户反馈

```bash
# 1. 查看用户反馈详情
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/27/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 添加回复
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "您好，我们已经定位到问题，将在下个版本修复。"
  }'

# 3. 更新反馈状态
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/status/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "reason": "已安排开发团队修复"
  }'
```

### 场景2：团队内部协作

```bash
# 1. 管理员添加内部备注
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "此问题涉及数据库性能优化，需要DBA协助",
    "is_internal_note": true
  }'

# 2. 另一个管理员查看所有回复（包括内部备注）
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 场景3：修改已发送的回复

```bash
# 发现回复有误，修改内容
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/27/replies/30/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "抱歉，刚才的回复有误。正确的解决方案是..."
  }'
```

---

## 注意事项

1. **邮件通知**：
   - 公开回复会自动发送邮件通知给反馈提交者
   - 内部备注不会触发邮件通知
   - 邮件发送是异步执行的，可能有延迟

2. **权限控制**：
   - 普通用户看不到内部备注
   - 只有管理员可以创建内部备注
   - 回复创建者可以编辑和删除自己的回复

3. **数据统计**：
   - 内部备注不计入 `reply_count`
   - 删除回复会减少 `reply_count`

4. **最佳实践**：
   - 回复应该专业、友好、及时
   - 使用内部备注进行团队协作
   - 重要决策应该记录在回复中
   - 定期清理过时的内部备注

---

## 错误处理

### 常见错误

| 错误码 | 错误信息 | 说明 |
|--------|----------|------|
| 404 | Feedback not found | 反馈不存在或已删除 |
| 404 | Reply not found | 回复不存在或已删除 |
| 403 | Permission denied | 没有权限访问此回复 |
| 400 | Content is required | 回复内容不能为空 |
| 400 | Content cannot be empty | 回复内容不能只有空格 |

### 错误响应示例

```json
{
    "success": false,
    "code": 4040,
    "message": "资源不存在",
    "data": {
        "detail": "Reply not found."
    }
}
```
