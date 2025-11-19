# 评论系统 API 文档

## 概述
评论系统支持三种用户类型：
- **Member用户**：认证用户，评论自动批准
- **Admin用户**：管理员，可管理所有评论
- **游客**：匿名用户，评论需要审核

## 基础信息
- **Base URL**: `/api/v1/cms/comments/`
- **认证方式**: JWT Bearer Token（Member/Admin）或 无需认证（游客）
- **必需请求头**: `X-Tenant-ID: {tenant_id}`

## 重要特性
- **支持树形评论**：通过 `parent` 字段实现评论回复
- **灵活的查询**：支持 `parent` 和 `has_parent` 参数筛选顶级评论或回复
- **租户隔离**：所有评论严格按租户隔离
- **自动审核**：认证用户评论自动批准，游客评论需要审核

---

## 1. 获取评论列表

### 请求
```bash
GET /api/v1/cms/comments/
```

### 请求头
```
X-Tenant-ID: 1
```

### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| article | integer | 否 | 文章ID，筛选指定文章的评论 |
| status | string | 否 | 评论状态：approved/pending/spam/trash |
| parent | integer/null | 否 | 父评论ID，null表示只获取顶级评论 |
| has_parent | boolean | 否 | 是否有父评论：true=只获取回复，false=只获取顶级评论 |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认10 |

### cURL 示例
```bash
# 获取文章的所有已批准评论
curl -X GET "http://localhost:8000/api/v1/cms/comments/?article=10247" \
  -H "X-Tenant-ID: 1"

# 获取顶级评论（方式1：使用 parent=null）
curl -X GET "http://localhost:8000/api/v1/cms/comments/?article=10247&parent=null" \
  -H "X-Tenant-ID: 1"

# 获取顶级评论（方式2：使用 has_parent=false）
curl -X GET "http://localhost:8000/api/v1/cms/comments/?article=10247&has_parent=false" \
  -H "X-Tenant-ID: 1"

# 获取所有回复评论
curl -X GET "http://localhost:8000/api/v1/cms/comments/?article=10247&has_parent=true" \
  -H "X-Tenant-ID: 1"
```

### 响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 2,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 1,
        "article": 10247,
        "parent": null,
        "user": null,
        "member": 9,
        "author_info": {
          "id": 9,
          "username": "test_member_001",
          "nick_name": "测试会员001",
          "avatar": ""
        },
        "author_type": "member",
        "content": "这是Member用户的评论！",
        "status": "approved",
        "created_at": "2025-11-13T02:46:16.133006Z",
        "updated_at": "2025-11-13T02:46:45.995401Z",
        "likes_count": 0,
        "replies_count": 0
      }
    ]
  }
}
```

---

## 2. Member 创建评论

### 请求
```bash
POST /api/v1/cms/comments/
```

### 请求头
```
Authorization: Bearer {member_token}
X-Tenant-ID: 1
Content-Type: application/json
```

### 请求体
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| article | integer | 是 | 文章ID |
| content | string | 是 | 评论内容，最长1000字符 |
| parent | integer | 否 | 父评论ID（回复评论时使用） |

### cURL 示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 10247,
    "content": "这是Member用户的测试评论！"
  }'
```

### 响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "article": 10247,
    "parent": null,
    "user": null,
    "member": 9,
    "author_info": {
      "id": 9,
      "username": "test_member_001",
      "nick_name": "测试会员001"
    },
    "author_type": "member",
    "content": "这是Member用户的测试评论！",
    "status": "approved",
    "created_at": "2025-11-13T02:46:16.133006Z",
    "likes_count": 0,
    "replies_count": 0
  }
}
```

**说明**：
- Member用户的评论会自动批准（`status: "approved"`）
- `member` 字段会自动设置为当前登录的Member用户ID
- `user` 字段为 null

---

## 3. 游客创建评论

### 请求
```bash
POST /api/v1/cms/comments/
```

### 请求头
```
X-Tenant-ID: 1
Content-Type: application/json
```

**注意**：游客评论无需 Authorization 头

### 请求体
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| article | integer | 是 | 文章ID |
| content | string | 是 | 评论内容 |
| guest_name | string | 是 | 游客昵称 |
| guest_email | string | 否 | 游客邮箱 |
| guest_website | string | 否 | 游客网站 |

### cURL 示例
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 10247,
    "content": "这是游客的测试评论",
    "guest_name": "测试游客",
    "guest_email": "guest@example.com"
  }'
```

### 响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 3,
    "article": 10247,
    "user": null,
    "member": null,
    "author_info": {
      "name": "测试游客",
      "email": "guest@example.com",
      "type": "guest"
    },
    "author_type": "guest",
    "guest_name": "测试游客",
    "content": "这是游客的测试评论",
    "status": "pending",
    "created_at": "2025-11-13T02:48:39.207993Z"
  }
}
```

**说明**：
- 游客评论需要审核（`status: "pending"`）
- `user` 和 `member` 字段都为 null
- `guest_name` 字段必须提供

---

## 4. Member 更新自己的评论

### 请求
```bash
PATCH /api/v1/cms/comments/{id}/
```

### 请求头
```
Authorization: Bearer {member_token}
X-Tenant-ID: 1
Content-Type: application/json
```

### 请求体
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 新的评论内容 |

### cURL 示例
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/comments/1/" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这是更新后的评论内容！"
  }'
```

### 响应示例
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "content": "这是更新后的评论内容！",
    "updated_at": "2025-11-13T02:46:45.995401Z"
  }
}
```

**权限说明**：
- Member只能更新自己的评论
- Admin可以更新所有评论

---

## 5. Member 删除自己的评论

### 请求
```bash
DELETE /api/v1/cms/comments/{id}/
```

### 请求头
```
Authorization: Bearer {member_token}
X-Tenant-ID: 1
```

### cURL 示例
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/comments/1/" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "X-Tenant-ID: 1"
```

### 响应
```
HTTP/1.1 204 No Content
```

**权限说明**：
- Member只能删除自己的评论
- Admin可以删除所有评论
- 文章作者可以删除其文章下的所有评论

---

## 数据模型说明

### Comment 对象
| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 评论ID |
| article | integer | 文章ID |
| parent | integer/null | 父评论ID，null表示顶级评论 |
| user | integer/null | Admin用户ID |
| member | integer/null | Member用户ID |
| author_info | object | 评论者信息 |
| author_type | string | 评论者类型：admin/member/guest |
| content | string | 评论内容 |
| status | string | 状态：approved/pending/spam/trash |
| guest_name | string/null | 游客昵称 |
| guest_email | string/null | 游客邮箱 |
| likes_count | integer | 点赞数 |
| replies_count | integer | 回复数 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### author_info 对象

**Member/Admin 用户**:
```json
{
  "id": 9,
  "username": "test_member_001",
  "nick_name": "测试会员001",
  "avatar": ""
}
```

**游客**:
```json
{
  "name": "测试游客",
  "email": "guest@example.com",
  "type": "guest"
}
```

---

## 错误代码

| 错误码 | 说明 |
|--------|------|
| 4000 | 数据验证失败 |
| 4001 | 未认证 |
| 4003 | 无权限 |
| 4004 | 资源不存在 |
| 5000 | 服务器内部错误 |

---

## 前端集成示例

### JavaScript/TypeScript
```javascript
// API 配置
const API_BASE = 'http://localhost:8000/api/v1';
const TENANT_ID = '1';

// 获取评论列表
async function getComments(articleId) {
  const response = await fetch(
    `${API_BASE}/cms/comments/?article=${articleId}`,
    {
      headers: {
        'X-Tenant-ID': TENANT_ID
      }
    }
  );
  return response.json();
}

// Member 发表评论
async function postComment(articleId, content, token) {
  const response = await fetch(`${API_BASE}/cms/comments/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Tenant-ID': TENANT_ID,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      article: articleId,
      content: content
    })
  });
  return response.json();
}

// 游客发表评论
async function postGuestComment(articleId, content, guestName, guestEmail) {
  const response = await fetch(`${API_BASE}/cms/comments/`, {
    method: 'POST',
    headers: {
      'X-Tenant-ID': TENANT_ID,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      article: articleId,
      content: content,
      guest_name: guestName,
      guest_email: guestEmail
    })
  });
  return response.json();
}

// 更新评论
async function updateComment(commentId, content, token) {
  const response = await fetch(`${API_BASE}/cms/comments/${commentId}/`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Tenant-ID': TENANT_ID,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ content })
  });
  return response.json();
}

// 删除评论
async function deleteComment(commentId, token) {
  const response = await fetch(`${API_BASE}/cms/comments/${commentId}/`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Tenant-ID': TENANT_ID
    }
  });
  return response.status === 204;
}
```

---

## 测试验证结果

✅ **已验证功能**：
1. Member 用户注册和登录
2. Member 创建评论（自动批准）
3. Member 查看评论列表  
4. Member 更新自己的评论
5. Member 删除自己的评论
6. 游客创建评论（需要审核）
7. 匿名获取评论列表

✅ **数据库验证**：
- `cms_comment` 表的 `member_id` 字段正确填充
- `user_id` 和 `member_id` 约束正确工作
- 游客评论时两个字段都为 NULL
- `operation_log` 表正确记录 Member 操作

---

## 注意事项

1. **认证**：
   - Member/Admin 评论需要提供 JWT Token
   - 游客评论无需认证，但需提供 `guest_name`

2. **权限**：
   - Member 只能编辑/删除自己的评论
   - Admin 可以管理所有评论
   - 文章作者可以管理其文章下的所有评论

3. **审核**：
   - Member/Admin 评论自动批准
   - 游客评论需要审核（status: pending）

4. **租户隔离**：
   - 所有请求必须包含 `X-Tenant-ID` 头
   - 用户只能访问其租户下的评论
