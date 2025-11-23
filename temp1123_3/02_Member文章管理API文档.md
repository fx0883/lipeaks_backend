# Member文章管理 API 文档

## 概述

Member文章管理API专门为Member用户设计，提供独立的文章CRUD功能。

### 权限说明
- **仅Member用户可访问**
- Member只能管理自己创建的文章
- 必须使用HTTP Header `X-Tenant-ID: 3` 传递租户ID

### Base URL
```
http://localhost:8000/api/v1/cms/member/articles
```

## API列表

### 1. 获取我的文章列表

**接口地址**
```
GET /api/v1/cms/member/articles/
```

**请求头**
```
Authorization: Bearer {MEMBER_TOKEN}
X-Tenant-ID: 3
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认1 |
| status | string | 否 | 文章状态过滤 |
| search | string | 否 | 搜索关键词 |
| sort | string | 否 | 排序字段：created_at, updated_at, published_at, title |
| sort_direction | string | 否 | 排序方向：asc, desc |

**curl示例**
```bash
curl -X GET "http://localhost:8000/api/v1/cms/member/articles/?page=1&status=published" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"
```

---

### 2. 创建文章

**接口地址**
```
POST /api/v1/cms/member/articles/
```

**请求头**
```
Authorization: Bearer {MEMBER_TOKEN}
X-Tenant-ID: 3
Content-Type: application/json
```

**请求体**
```json
{
  "title": "我的文章",
  "content": "文章内容",
  "content_type": "markdown",
  "status": "draft",
  "excerpt": "摘要",
  "visibility": "public",
  "allow_comment": true
}
```

**curl示例**
```bash
curl -X POST "http://localhost:8000/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Member的文章",
    "content": "内容",
    "content_type": "markdown",
    "status": "draft"
  }'
```

---

### 3. 获取我的单篇文章

**接口地址**
```
GET /api/v1/cms/member/articles/{id}/
```

**curl示例**
```bash
curl -X GET "http://localhost:8000/api/v1/cms/member/articles/10295/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"
```

---

### 4. 更新我的文章

**接口地址**
```
PUT /api/v1/cms/member/articles/{id}/
```

**请求体**
```json
{
  "title": "更新后的标题",
  "content": "更新后的内容",
  "content_type": "markdown"
}
```

**curl示例**
```bash
curl -X PUT "http://localhost:8000/api/v1/cms/member/articles/10295/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的标题",
    "content": "更新后的内容",
    "content_type": "markdown"
  }'
```

---

### 5. 部分更新我的文章

**接口地址**
```
PATCH /api/v1/cms/member/articles/{id}/
```

**curl示例**
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/member/articles/10295/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"status": "published"}'
```

---

### 6. 删除我的文章

删除操作为软删除，将状态改为archived。

**接口地址**
```
DELETE /api/v1/cms/member/articles/{id}/
```

**curl示例**
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/member/articles/10295/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"
```

---

### 7. 发布我的文章

将草稿或待审核状态的文章发布。

**接口地址**
```
POST /api/v1/cms/member/articles/{id}/publish/
```

**curl示例**
```bash
curl -X POST "http://localhost:8000/api/v1/cms/member/articles/10295/publish/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 10295,
    "title": "文章标题",
    "status": "published",
    "published_at": "2025-11-23T12:00:00Z"
  }
}
```

---

### 8. 获取我的文章统计

获取文章的统计信息（浏览量、点赞数等）。

**接口地址**
```
GET /api/v1/cms/member/articles/{id}/statistics/
```

**响应示例**
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "views_count": 100,
    "unique_views_count": 50,
    "likes_count": 20,
    "comments_count": 5,
    "shares_count": 10,
    "bookmarks_count": 8
  }
}
```

**curl示例**
```bash
curl -X GET "http://localhost:8000/api/v1/cms/member/articles/10295/statistics/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"
```

---

## 注意事项

1. **权限限制**：Member用户只能操作自己创建的文章
2. **租户ID**：必须在请求头中包含`X-Tenant-ID`
3. **软删除**：删除操作不会真正删除数据，只是将状态改为archived
4. **发布限制**：只有draft和pending状态的文章可以发布

## 错误响应

### 权限不足
```json
{
  "success": false,
  "code": 4003,
  "message": "您没有执行该操作的权限。",
  "data": null,
  "error_code": "AUTH_PERMISSION_DENIED"
}
```

### 文章不存在
```json
{
  "success": false,
  "code": 4004,
  "message": "No Article matches the given query.",
  "data": null,
  "error_code": "NOT_FOUND"
}
```
