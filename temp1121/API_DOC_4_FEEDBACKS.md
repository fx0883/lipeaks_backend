# Feedbacks API 文档

## 基础信息

**Base URL**: `http://localhost:8000/api/v1/feedbacks`  
**认证**: 大部分端点支持匿名访问  
**必需请求头**: `Tenant-ID: {tenant_id}`

---

## API端点

### 1. 创建反馈（匿名）

**POST** `/feedbacks/`

```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "发现一个Bug",
    "description": "详细描述问题...",
    "feedback_type": "bug",
    "priority": "high",
    "application": 1,
    "contact_email": "user@example.com",
    "contact_name": "张三"
  }'
```

**请求体字段**:
- `title` - 标题（必填）
- `description` - 详细描述（必填）
- `feedback_type` - 类型（必填）: `bug`, `feature`, `improvement`, `question`
- `priority` - 优先级（必填）: `low`, `medium`, `high`, `urgent`
- `application` - 应用ID（可选）
- `contact_email` - 联系邮箱（必填）
- `contact_name` - 联系人（可选）
- `attachments` - 附件列表（可选）

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "反馈提交成功",
  "data": {
    "id": 1,
    "title": "发现一个Bug",
    "feedback_type": "bug",
    "priority": "high",
    "status": "pending",
    "tracking_number": "FB202411210001",
    "created_at": "2024-11-21T10:00:00Z"
  }
}
```

---

### 2. 获取反馈列表

**GET** `/feedbacks/` （需要认证）

```bash
curl "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

**查询参数**:
- `application` - 应用ID
- `status` - 状态: `pending`, `in_progress`, `resolved`, `closed`, `rejected`
- `priority` - 优先级
- `feedback_type` - 类型
- `search` - 搜索关键词
- `page` - 页码
- `page_size` - 每页数量

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "count": 50,
    "next": "http://...?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "tracking_number": "FB202411210001",
        "title": "发现一个Bug",
        "feedback_type": "bug",
        "priority": "high",
        "status": "pending",
        "application": {
          "id": 1,
          "name": "LiPeaks CMS"
        },
        "contact_email": "user@example.com",
        "created_at": "2024-11-21T10:00:00Z"
      }
    ]
  }
}
```

---

### 3. 获取反馈详情

**GET** `/feedbacks/{id}/`

```bash
curl "http://localhost:8000/api/v1/feedbacks/feedbacks/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "tracking_number": "FB202411210001",
    "title": "发现一个Bug",
    "description": "详细描述...",
    "feedback_type": "bug",
    "priority": "high",
    "status": "pending",
    "application": {
      "id": 1,
      "name": "LiPeaks CMS",
      "current_version": "1.0.0"
    },
    "submitter": null,
    "assignee": null,
    "contact_name": "张三",
    "contact_email": "user@example.com",
    "contact_phone": null,
    "attachments": [],
    "tags": [],
    "created_at": "2024-11-21T10:00:00Z",
    "updated_at": "2024-11-21T10:00:00Z"
  }
}
```

---

### 4. 更新反馈状态（管理员）

**PATCH** `/feedbacks/{id}/`

```bash
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "assignee": 2
  }'
```

**可更新字段**:
- `status` - 状态
- `priority` - 优先级
- `assignee` - 指派给的用户ID
- `internal_notes` - 内部备注

---

### 5. 添加回复

**POST** `/feedbacks/{id}/reply/`

```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/1/reply/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "我们已经收到您的反馈，正在处理中。",
    "is_internal": false
  }'
```

**请求体字段**:
- `content` - 回复内容（必填）
- `is_internal` - 是否内部可见（默认false）

---

### 6. 上传附件

**POST** `/feedbacks/{id}/upload-attachment/`

```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/1/upload-attachment/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -F "file=@/path/to/screenshot.png" \
  -F "description=错误截图"
```

---

### 7. 按追踪号查询

**GET** `/feedbacks/by-tracking-number/{tracking_number}/`

```bash
curl "http://localhost:8000/api/v1/feedbacks/feedbacks/by-tracking-number/FB202411210001/" \
  -H "Tenant-ID: 1"
```

**注意**: 此端点支持匿名访问，用户可通过追踪号查询自己的反馈进度

---

## 完整测试示例

```bash
# 1. 匿名提交反馈
FEEDBACK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "页面加载缓慢",
    "description": "首页加载时间超过5秒",
    "feedback_type": "bug",
    "priority": "medium",
    "application": 1,
    "contact_email": "test@example.com",
    "contact_name": "测试用户"
  }')

TRACKING_NUMBER=$(echo "$FEEDBACK_RESPONSE" | jq -r '.data.tracking_number')
echo "追踪号: $TRACKING_NUMBER"

# 2. 通过追踪号查询
curl "http://localhost:8000/api/v1/feedbacks/feedbacks/by-tracking-number/$TRACKING_NUMBER/" \
  -H "Tenant-ID: 1" | jq

# 3. 管理员获取列表（需要登录）
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' \
  | jq -r '.data.token')

curl "http://localhost:8000/api/v1/feedbacks/feedbacks/?status=pending" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" | jq

# 4. 更新状态
FEEDBACK_ID=$(echo "$FEEDBACK_RESPONSE" | jq -r '.data.id')
curl -X PATCH "http://localhost:8000/api/v1/feedbacks/feedbacks/$FEEDBACK_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}' | jq

# 5. 添加回复
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/$FEEDBACK_ID/reply/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"content": "我们正在调查此问题"}' | jq
```

---

## 状态流转

```
pending → in_progress → resolved → closed
   ↓            ↓
rejected     rejected
```

**状态说明**:
- `pending` - 待处理
- `in_progress` - 处理中
- `resolved` - 已解决
- `closed` - 已关闭
- `rejected` - 已拒绝

---

## 注意事项

1. **application_version字段已删除** - 反馈不再关联具体版本
2. **匿名提交** - 创建反馈和查询追踪号不需要认证
3. **追踪号** - 系统自动生成，格式：FB+日期+序号
4. **权限** - 更新状态、指派、查看全部需要管理员权限
