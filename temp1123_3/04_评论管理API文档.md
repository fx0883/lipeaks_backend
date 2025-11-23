# 评论管理 API 文档

## 概述

评论管理API用于处理文章评论的创建、审核和管理。

### 权限说明
- **Admin用户**：可以管理所有评论，审核、批准、拒绝等，使用查询参数`?tenant_id=3`
- **Member用户**：可以创建评论，使用Header `X-Tenant-ID: 3`
- **游客**：可以留言但需要提供guest_name和guest_email

## Base URL
```
http://localhost:8000/api/v1/cms/comments
```

---

## API列表

### 1. 获取评论列表

**接口地址**
```
GET /api/v1/cms/comments/
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tenant_id | integer | Admin必填 | 租户ID |
| article | integer | 否 | 按文章ID过滤 |
| status | string | 否 | 评论状态：pending, approved, spam, trash |
| parent | integer | 否 | 父评论ID（获取回复） |
| search | string | 否 | 搜索关键词 |

**curl示例**

Admin查看所有评论：
```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

查看特定文章的评论：
```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/?tenant_id=3&article=10298" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "count": 50,
    "next": "http://localhost:8000/api/v1/cms/comments/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "article": 10298,
        "article_title": "示例文章",
        "content": "这是一条评论",
        "status": "approved",
        "author_type": "member",
        "author_username": "test02@qq.com",
        "author_display_name": "Nihao",
        "parent": null,
        "is_pinned": false,
        "likes_count": 5,
        "created_at": "2025-11-23T12:00:00Z"
      }
    ]
  }
}
```

---

### 2. 创建评论

**接口地址**
```
POST /api/v1/cms/comments/
```

**请求体**

Member用户评论：
```json
{
  "article": 10298,
  "content": "这是我的评论内容",
  "parent": null
}
```

游客评论：
```json
{
  "article": 10298,
  "content": "游客的评论",
  "guest_name": "张三",
  "guest_email": "zhangsan@example.com",
  "guest_website": "https://example.com"
}
```

**curl示例**

Member用户评论：
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 10298,
    "content": "这是一条很好的文章！"
  }'
```

游客评论：
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 10298,
    "content": "游客留言",
    "guest_name": "游客",
    "guest_email": "guest@example.com"
  }'
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 123,
    "article": 10298,
    "content": "这是一条很好的文章！",
    "status": "pending",
    "created_at": "2025-11-23T12:00:00Z"
  }
}
```

---

### 3. 获取评论详情

**接口地址**
```
GET /api/v1/cms/comments/{id}/
```

**curl示例**
```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/1/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 4. 更新评论

**接口地址**
```
PUT /api/v1/cms/comments/{id}/
PATCH /api/v1/cms/comments/{id}/
```

**curl示例**
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/comments/1/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "更新后的评论内容",
    "status": "approved"
  }'
```

---

### 5. 删除评论

**接口地址**
```
DELETE /api/v1/cms/comments/{id}/
```

**curl示例**
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/comments/1/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 6. 批准评论

将待审核的评论状态改为已批准。

**接口地址**
```
POST /api/v1/cms/comments/{id}/approve/
```

**curl示例**
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/1/approve/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "status": "approved",
    "message": "评论已批准"
  }
}
```

---

### 7. 拒绝评论

将评论状态改为已拒绝（trash）。

**接口地址**
```
POST /api/v1/cms/comments/{id}/reject/
```

**curl示例**
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/1/reject/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 8. 标记为垃圾评论

将评论标记为垃圾评论。

**接口地址**
```
POST /api/v1/cms/comments/{id}/mark-spam/
```

**curl示例**
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/1/mark-spam/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

---

### 9. 获取评论回复

获取某条评论的所有回复。

**接口地址**
```
GET /api/v1/cms/comments/{id}/replies/
```

**curl示例**
```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/1/replies/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 2,
      "content": "这是对评论1的回复",
      "parent": 1,
      "author_username": "admin_cms",
      "created_at": "2025-11-23T12:10:00Z"
    },
    {
      "id": 3,
      "content": "这是另一条回复",
      "parent": 1,
      "author_username": "test02@qq.com",
      "created_at": "2025-11-23T12:15:00Z"
    }
  ]
}
```

---

### 10. 批量处理评论

批量批准、拒绝或删除多条评论。

**接口地址**
```
POST /api/v1/cms/comments/batch/
```

**请求体**
```json
{
  "comment_ids": [1, 2, 3],
  "action": "approve"
}
```

**支持的操作**
- `approve`: 批准评论
- `reject`: 拒绝评论
- `spam`: 标记为垃圾评论
- `delete`: 删除评论

**curl示例**

批量批准评论：
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/batch/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "comment_ids": [1, 2, 3],
    "action": "approve"
  }'
```

批量删除评论：
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/batch/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "comment_ids": [4, 5, 6],
    "action": "delete"
  }'
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "message": "批量操作成功",
    "processed_count": 3,
    "action": "approve"
  }
}
```

---

## 评论状态说明

| 状态 | 说明 |
|------|------|
| pending | 待审核（新评论的默认状态） |
| approved | 已批准（显示在文章下方） |
| spam | 垃圾评论（被标记为垃圾） |
| trash | 已删除（已拒绝或删除） |

---

## 评论者类型

### 1. Admin用户评论
```json
{
  "user": 3,
  "member": null,
  "guest_name": null
}
```

### 2. Member用户评论
```json
{
  "user": null,
  "member": 10,
  "guest_name": null
}
```

### 3. 游客评论
```json
{
  "user": null,
  "member": null,
  "guest_name": "张三",
  "guest_email": "zhangsan@example.com",
  "guest_website": "https://example.com"
}
```

---

## 回复评论

创建回复时，需要指定parent字段为父评论的ID：

```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 10298,
    "content": "这是对评论1的回复",
    "parent": 1
  }'
```

---

## 注意事项

1. **审核机制**：新评论默认状态为pending，需要Admin审核后才会显示
2. **权限控制**：
   - Admin可以管理所有评论
   - Member只能评论，不能审核
   - 游客需要提供邮箱才能评论
3. **垃圾过滤**：建议配合spam检测机制使用
4. **回复层级**：支持无限层级回复
5. **IP记录**：系统会自动记录评论者的IP地址和User-Agent

---

## 前端集成建议

### 评论列表展示
```javascript
// 获取文章评论
fetch(`/api/v1/cms/comments/?article=10298&status=approved`, {
  headers: {
    'X-Tenant-ID': '3'
  }
})
.then(res => res.json())
.then(data => {
  // 渲染评论列表
  renderComments(data.data.results);
});
```

### 提交评论
```javascript
// Member用户提交评论
fetch('/api/v1/cms/comments/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${memberToken}`,
    'X-Tenant-ID': '3'
  },
  body: JSON.stringify({
    article: 10298,
    content: '评论内容'
  })
})
.then(res => res.json())
.then(data => {
  if (data.success) {
    alert('评论提交成功，等待审核');
  }
});
```

### 游客评论
```javascript
// 游客提交评论
fetch('/api/v1/cms/comments/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-ID': '3'
  },
  body: JSON.stringify({
    article: 10298,
    content: '游客评论内容',
    guest_name: '游客昵称',
    guest_email: 'guest@example.com'
  })
})
.then(res => res.json())
.then(data => {
  if (data.success) {
    alert('评论提交成功');
  }
});
```
