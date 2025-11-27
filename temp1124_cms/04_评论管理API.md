# CMS评论管理API文档

## API端点列表

**基础路径**: `/api/v1/cms/comments/`

---

## 1. 获取评论列表

**请求方式**: `GET /api/v1/cms/comments/`

**权限**: 租户管理员

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 10 | 每页数量 |
| article_id | integer | 否 | - | 文章ID过滤 |
| status | string | 否 | - | 状态：pending/approved/rejected/spam |
| search | string | 否 | - | 搜索关键词（内容） |
| ordering | string | 否 | -created_at | 排序字段 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/?article_id=123&status=pending" \
  -H "Authorization: Bearer <租户管理员TOKEN>"
```

**响应字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 请求是否成功 |
| data.pagination | object | 分页信息 |
| data.results | array | 评论列表 |

**评论对象字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 评论ID |
| article | integer | 文章ID |
| article_title | string | 文章标题 |
| content | string | 评论内容 |
| parent | integer | 父评论ID（回复） |
| status | string | 状态 |
| commenter_type | string | 评论者类型：user/member/guest |
| commenter_info | object | 评论者信息 |
| guest_name | string | 游客名称 |
| guest_email | string | 游客邮箱 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| ip_address | string | IP地址 |
| user_agent | string | User Agent |

---

## 2. 创建评论

**请求方式**: `POST /api/v1/cms/comments/`

**权限**: 所有用户（包括游客）

**请求体参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| article | integer | 是 | 文章ID |
| content | string | 是 | 评论内容（最大1000字符） |
| parent | integer | 否 | 父评论ID（用于回复评论） |
| guest_name | string | 否 | 游客名称（游客必填） |
| guest_email | string | 否 | 游客邮箱（游客必填） |

**请求示例**:

```bash
# Member用户创建评论
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "Authorization: Bearer <MemberTOKEN>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 123,
    "content": "这是一条测试评论"
  }'

# 游客创建评论
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 123,
    "guest_name": "张三",
    "guest_email": "zhangsan@example.com",
    "content": "这是游客的评论"
  }'

# 创建回复评论
curl -X POST "http://localhost:8000/api/v1/cms/comments/" \
  -H "Authorization: Bearer <MemberTOKEN>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 123,
    "parent": 456,
    "content": "这是对评论的回复"
  }'
```

**响应参数**: 返回创建的评论对象

---

## 3. 获取评论详情

**请求方式**: `GET /api/v1/cms/comments/{id}/`

**权限**: 所有用户

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 评论ID |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/456/" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 4. 更新评论

**请求方式**: `PATCH /api/v1/cms/comments/{id}/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 评论ID |

**请求体参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| content | string | 否 | 评论内容 |
| status | string | 否 | 状态 |

**请求示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/comments/456/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "修改后的内容",
    "status": "approved"
  }'
```

---

## 5. 删除评论

**请求方式**: `DELETE /api/v1/cms/comments/{id}/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 评论ID |

**请求示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/comments/456/" \
  -H "Authorization: Bearer <租户管理员TOKEN>"
```

---

## 6. 批准评论

**请求方式**: `POST /api/v1/cms/comments/{id}/approve/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 评论ID |

**说明**: 将评论状态从pending改为approved

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/456/approve/" \
  -H "Authorization: Bearer <租户管理员TOKEN>"
```

**响应字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 是否成功 |
| message | string | 提示信息 |
| data.id | integer | 评论ID |
| data.status | string | 新状态（approved） |

---

## 7. 拒绝评论

**请求方式**: `POST /api/v1/cms/comments/{id}/reject/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 评论ID |

**说明**: 将评论状态改为rejected

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/456/reject/" \
  -H "Authorization: Bearer <租户管理员TOKEN>"
```

---

## 8. 标记为垃圾评论

**请求方式**: `POST /api/v1/cms/comments/{id}/mark-spam/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 评论ID |

**说明**: 将评论标记为垃圾评论（spam状态）

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/456/mark-spam/" \
  -H "Authorization: Bearer <租户管理员TOKEN>"
```

---

## 9. 获取评论的回复

**请求方式**: `GET /api/v1/cms/comments/{id}/replies/`

**权限**: 所有用户

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 父评论ID |

**说明**: 获取指定评论的所有回复

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/456/replies/" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应参数**: 返回回复评论列表数组

---

## 10. 批量处理评论

**请求方式**: `POST /api/v1/cms/comments/batch/`

**权限**: 租户管理员

**请求体参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| comment_ids | array | 是 | 评论ID数组 |
| action | string | 是 | 操作类型：approve/reject/spam/delete |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/batch/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "comment_ids": [123, 124, 125],
    "action": "approve"
  }'
```

**响应字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 是否成功 |
| data.processed | integer | 成功处理的数量 |
| data.failed | integer | 失败的数量 |
| data.action | string | 执行的操作 |

---

## 评论者类型说明

### 1. 管理员用户（user）
- 租户管理员发表的评论
- 无需审核，自动approved状态
- commenter_info包含管理员用户信息

### 2. Member用户（member）
- 普通会员发表的评论
- 需要审核（pending状态）
- commenter_info包含Member用户信息
- **重要**: Member用户必须在header中添加`X-Tenant-ID`

### 3. 游客（guest）
- 未登录用户发表的评论
- 必须提供guest_name和guest_email
- 需要审核（pending状态）
- commenter_info为null，使用guest_name和guest_email字段

---

## 评论状态说明

| 状态 | 值 | 说明 |
|------|-----|------|
| 待审核 | pending | 新创建的评论，等待管理员审核 |
| 已批准 | approved | 管理员批准，公开可见 |
| 已拒绝 | rejected | 管理员拒绝，不公开显示 |
| 垃圾评论 | spam | 被标记为垃圾评论 |

---

## 注意事项

### 1. 游客评论要求
- 必须提供guest_name（最大50字符）
- 必须提供guest_email（有效的邮箱格式）
- 游客评论默认为pending状态，需要管理员审核

### 2. 评论审核流程
- 新评论创建时默认状态为pending
- 管理员可以批准（approve）、拒绝（reject）或标记为垃圾评论（spam）
- 只有approved状态的评论会在前台显示

### 3. 嵌套回复
- 支持多级评论回复
- 通过parent字段指定父评论ID
- 回复评论与父评论属于同一篇文章
- 可以对评论和回复进行回复，形成评论树

### 4. Member用户评论
- Member用户必须在header中添加`X-Tenant-ID: 3`
- Member用户只能在所属租户下发表评论
- Member的评论需要审核

### 5. 权限控制
- 所有用户（包括游客）可以创建评论
- 只有租户管理员可以审核、修改、删除评论
- Member用户不能修改或删除自己的评论（需要联系管理员）

### 6. IP地址和User Agent
- 系统自动记录评论者的IP地址和User Agent
- 用于反垃圾评论和追溯
- 前端不需要提供这些信息

### 7. 评论通知
- 评论被回复时可以通知原评论者
- 评论状态变更时可以通知评论者
- 需要配置邮件或站内通知功能

### 8. 反垃圾评论建议
- 启用评论审核（所有评论默认pending）
- 限制游客评论频率
- 使用验证码（前端实现）
- 定期清理spam状态的评论
