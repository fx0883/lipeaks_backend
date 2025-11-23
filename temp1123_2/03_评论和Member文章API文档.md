# CMS API 文档 - 评论管理 & Member文章管理

## 评论管理 API

### 1. 获取评论列表

```bash
# 匿名用户获取评论
curl -X GET "http://0.0.0.0:8000/api/v1/cms/comments/" \
  -H "X-Tenant-ID: 3"

# 按文章过滤
curl -X GET "http://0.0.0.0:8000/api/v1/cms/comments/?article=123" \
  -H "X-Tenant-ID: 3"

# 获取顶级评论（无父评论）
curl -X GET "http://0.0.0.0:8000/api/v1/cms/comments/?parent=null" \
  -H "X-Tenant-ID: 3"

# 获取某条评论的回复
curl -X GET "http://0.0.0.0:8000/api/v1/cms/comments/?parent=456" \
  -H "X-Tenant-ID: 3"
```

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| article | integer | 文章ID过滤 |
| parent | integer/null | 父评论ID（null获取顶级评论） |
| user | integer | 用户ID过滤 |
| status | string | 状态：pending, approved, rejected, spam |
| is_pinned | boolean | 是否置顶 |
| search | string | 搜索评论内容 |
| sort | string | 排序：created_at, likes_count |
| sort_direction | string | asc/desc |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "results": [
      {
        "id": 1,
        "article": 123,
        "parent": null,
        "content": "这是一条评论",
        "status": "approved",
        "is_pinned": false,
        "likes_count": 5,
        "user_info": {
          "id": 10,
          "username": "test@qq.com",
          "avatar": "..."
        },
        "created_at": "2025-11-23T12:00:00Z"
      }
    ]
  }
}
```

### 2. 创建评论 (Member/游客)

```bash
# Member创建评论
curl -X POST "http://0.0.0.0:8000/api/v1/cms/comments/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 123,
    "content": "这是我的评论",
    "parent": null
  }'

# 创建回复评论
curl -X POST "http://0.0.0.0:8000/api/v1/cms/comments/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 123,
    "content": "这是回复",
    "parent": 1
  }'

# 游客创建评论
curl -X POST "http://0.0.0.0:8000/api/v1/cms/comments/" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "article": 123,
    "content": "游客评论",
    "guest_name": "访客小明",
    "guest_email": "guest@example.com"
  }'
```

**请求字段**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| article | integer | 是 | 文章ID |
| content | string | 是 | 评论内容 |
| parent | integer | 否 | 父评论ID（回复时） |
| guest_name | string | 否* | 游客昵称（游客时必填） |
| guest_email | string | 否* | 游客邮箱（游客时必填） |

### 3. 更新评论 (作者/Admin)

```bash
# Member更新自己的评论
curl -X PATCH "http://0.0.0.0:8000/api/v1/cms/comments/1/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "更新后的评论内容"
  }'
```

### 4. 删除评论 (作者/Admin)

```bash
# Member删除自己的评论
curl -X DELETE "http://0.0.0.0:8000/api/v1/cms/comments/1/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"

# Admin删除任何评论
curl -X DELETE "http://0.0.0.0:8000/api/v1/cms/comments/1/" \
  -H "Authorization: Bearer {admin_token}"
```

### 5. 批准评论 (Admin)

```bash
curl -X POST "http://0.0.0.0:8000/api/v1/cms/comments/1/approve/" \
  -H "Authorization: Bearer {admin_token}"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "评论已批准",
  "data": {
    "id": 1,
    "status": "approved"
  }
}
```

### 6. 拒绝评论 (Admin)

```bash
curl -X POST "http://0.0.0.0:8000/api/v1/cms/comments/1/reject/" \
  -H "Authorization": Bearer {admin_token}"
```

### 7. 标记为垃圾评论 (Admin)

```bash
curl -X POST "http://0.0.0.0:8000/api/v1/cms/comments/1/mark-spam/" \
  -H "Authorization: Bearer {admin_token}"
```

### 8. 获取评论回复

```bash
curl -X GET "http://0.0.0.0:8000/api/v1/cms/comments/1/replies/" \
  -H "X-Tenant-ID: 3"
```

**响应**: 返回该评论下的所有回复列表

### 9. 批量处理评论 (Admin)

```bash
# 批量批准
curl -X POST "http://0.0.0.0:8000/api/v1/cms/comments/batch/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "comment_ids": [1, 2, 3],
    "action": "approve"
  }'

# 批量删除
curl -X POST "http://0.0.0.0:8000/api/v1/cms/comments/batch/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "comment_ids": [4, 5, 6],
    "action": "delete"
  }'
```

**请求字段**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| comment_ids | array | 是 | 评论ID数组 |
| action | string | 是 | 操作：approve, reject, spam, delete |

---

## Member文章管理 API

Member用户通过这组API管理自己的文章。**所有请求都必须携带`X-Tenant-ID`头**。

### 1. 获取我的文章列表

```bash
curl -X GET "http://0.0.0.0:8000/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"

# 带过滤和搜索
curl -X GET "http://0.0.0.0:8000/api/v1/cms/member/articles/?status=draft&search=关键词" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

**查询参数**: 与文章列表API相同，但只返回当前Member的文章

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "pagination": {...},
    "results": [
      {
        "id": 10295,
        "title": "我的文章",
        "status": "draft",
        "created_at": "2025-11-23T12:00:00Z",
        ...
      }
    ]
  }
}
```

### 2. 创建文章 (Member)

```bash
curl -X POST "http://0.0.0.0:8000/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的第一篇文章",
    "content": "文章内容...",
    "excerpt": "摘要",
    "status": "draft",
    "category_ids": [1, 2],
    "tag_ids": [3, 4]
  }'
```

**请求字段**: 与Admin创建文章相同

**响应**: 创建成功返回201状态码和文章详情

### 3. 获取我的单篇文章

```bash
curl -X GET "http://0.0.0.0:8000/api/v1/cms/member/articles/10295/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

### 4. 更新我的文章

```bash
# 完整更新 (PUT)
curl -X PUT "http://0.0.0.0:8000/api/v1/cms/member/articles/10295/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新标题",
    "content": "更新内容",
    "excerpt": "更新摘要",
    "status": "draft"
  }'

# 部分更新 (PATCH)
curl -X PATCH "http://0.0.0.0:8000/api/v1/cms/member/articles/10295/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "只更新标题"
  }'
```

### 5. 删除我的文章

```bash
curl -X DELETE "http://0.0.0.0:8000/api/v1/cms/member/articles/10295/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

### 6. 发布我的文章

```bash
curl -X POST "http://0.0.0.0:8000/api/v1/cms/member/articles/10295/publish/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "文章已发布",
  "data": {
    "id": 10295,
    "status": "published",
    "published_at": "2025-11-23T12:20:00Z"
  }
}
```

### 7. 获取我的文章统计

```bash
curl -X GET "http://0.0.0.0:8000/api/v1/cms/member/articles/10295/statistics/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "data": {
    "views_count": 50,
    "likes_count": 5,
    "favorites_count": 2,
    "comments_count": 3,
    "shares_count": 1
  }
}
```

---

## 完整工作流示例

### Member发布文章完整流程

```bash
# Step 1: Member创建草稿
RESPONSE=$(curl -s -X POST "http://0.0.0.0:8000/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的技术分享",
    "content": "# 标题\n\n内容...",
    "excerpt": "这是一篇技术分享文章",
    "status": "draft",
    "content_type": "markdown",
    "category_ids": [1],
    "tag_ids": [3, 5]
  }')
  
ARTICLE_ID=$(echo $RESPONSE | jq -r '.data.id')
echo "文章ID: $ARTICLE_ID"

# Step 2: 编辑和更新
curl -X PATCH "http://0.0.0.0:8000/api/v1/cms/member/articles/$ARTICLE_ID/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# 更新后的标题\n\n更新内容..."
  }'

# Step 3: 发布文章
curl -X POST "http://0.0.0.0:8000/api/v1/cms/member/articles/$ARTICLE_ID/publish/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"

# Step 4: 查看统计
curl -X GET "http://0.0.0.0:8000/api/v1/cms/member/articles/$ARTICLE_ID/statistics/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"
```

### Admin审核评论流程

```bash
# Step 1: 查看待审核评论
curl -X GET "http://0.0.0.0:8000/api/v1/cms/comments/?status=pending" \
  -H "Authorization: Bearer {admin_token}"

# Step 2: 批量批准评论
curl -X POST "http://0.0.0.0:8000/api/v1/cms/comments/batch/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "comment_ids": [1, 2, 3],
    "action": "approve"
  }'

# Step 3: 标记垃圾评论
curl -X POST "http://0.0.0.0:8000/api/v1/cms/comments/5/mark-spam/" \
  -H "Authorization: Bearer {admin_token}"
```

---

## 权限说明

### 评论权限
- **查看**: 所有用户可查看已批准的评论
- **创建**: Member/游客可创建评论
- **编辑**: 只能编辑自己的评论
- **删除**: 只能删除自己的评论或Admin删除任何评论
- **审核**: 仅Admin可批准/拒绝/标记垃圾评论

### Member文章权限
- **查看**: 只能查看自己的文章
- **创建**: 可创建文章
- **编辑**: 只能编辑自己的文章
- **删除**: 只能删除自己的文章
- **发布**: 可发布自己的文章

---

## 注意事项

1. **租户头要求**:
   - Member用户所有请求必须携带`X-Tenant-ID`头
   - Admin用户不需要租户头
   
2. **评论状态流转**:
   ```
   pending -> approved (批准)
   pending -> rejected (拒绝)
   any -> spam (标记垃圾)
   ```

3. **Member文章限制**:
   - 只能操作自己创建的文章
   - 无法查看或编辑其他Member的文章
   - 无法访问Admin创建的文章

4. **API路径差异**:
   - Admin文章: `/api/v1/cms/articles/`
   - Member文章: `/api/v1/cms/member/articles/`
