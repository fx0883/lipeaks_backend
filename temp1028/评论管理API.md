# 评论管理 API

Base: `/api/v1/cms/comments/`

## 通用要求
- **Headers（必须）**：
  - `X-Tenant-ID: <tenant_id>`
  - `Authorization: Bearer <token>`（GET匿名可不带；POST/PUT/PATCH/DELETE 需要）
  - `Content-Type: application/json`
- **权限模型（`CommentPermission` 继承 `CMSBasePermission`）**：
  - 匿名：仅可GET查看 `status=approved` 的评论；仍需 `X-Tenant-ID`。
  - 登录用户：可查看已批准评论与“自己的评论”。
  - 文章作者：可管理其文章下所有评论（approve/reject/spam/delete）。
  - Admin：可管理本租户评论；Super Admin 需通过 `X-Tenant-ID` 指定租户。
  - 创建评论：文章需允许评论（由后端校验 `article.allow_comment`）。

## 1. 获取评论列表 GET /
- 参数：`article`, `parent`, `user`, `status(pending|approved|rejected|spam)`, `is_pinned`, `search`, `sort(created_at|likes_count)`, `sort_direction`
- 匿名仅可见 `approved`；登录用户可见 `approved` 和自己的；管理员可见全部
- Headers：必须 `X-Tenant-ID`。
- 示例：
```bash
curl -X GET 'http://your-domain.com/api/v1/cms/comments/?article=15&parent=' \
  -H 'X-Tenant-ID: 1'
```

## 2. 获取评论详情 GET /{id}/
- 权限：匿名可见 `approved`；登录用户可见自己的；作者/Admin/Super Admin 可见全部。
- 示例：
```bash
curl -X GET http://your-domain.com/api/v1/cms/comments/1001/ \
  -H 'X-Tenant-ID: 1'
```

## 3. 创建评论 POST /
- 规则：若未提供 `user` 且无 `guest_name`，则自动设置为当前用户；记录 `ip_address`、`user_agent`
- 非管理员/作者创建的评论默认 `pending`
```json
{"article":1,"parent":null,"content":"这是一条评论","guest_name":"游客A","guest_email":"guest@example.com"}
```
- 权限：需要认证或提供 `guest_name` 作为游客；文章必须允许评论。
- 示例：
```bash
curl -X POST http://your-domain.com/api/v1/cms/comments/ \
  -H 'Authorization: Bearer <token>' -H 'X-Tenant-ID: 1' -H 'Content-Type: application/json' \
  -d '{"article":15,"content":"写得很好！"}'
```

## 4. 更新评论 PUT /{id}/、PATCH /{id}/
- 状态变更将同步更新对应文章的 `comments_count`
- 权限：需要认证；评论作者、文章作者、Admin、Super Admin 可根据角色规则更新。
- 示例：
```bash
curl -X PATCH http://your-domain.com/api/v1/cms/comments/1001/ \
  -H 'Authorization: Bearer <token>' -H 'X-Tenant-ID: 1' -H 'Content-Type: application/json' \
  -d '{"content":"修改后的内容"}'
```

## 5. 删除评论 DELETE /{id}/
- 同步更新 `comments_count`
- 权限：需要认证；评论作者、文章作者、Admin、Super Admin 允许。
- 示例：
```bash
curl -X DELETE http://your-domain.com/api/v1/cms/comments/1001/ \
  -H 'Authorization: Bearer <token>' -H 'X-Tenant-ID: 1'
```

## 6. 获取回复 GET /{id}/replies/
- 匿名仅返回 `approved`；非管理员仅返回 `approved` 或自己的
- Headers：`X-Tenant-ID` 必须。
- 示例：
```bash
curl -X GET http://your-domain.com/api/v1/cms/comments/1000/replies/ \
  -H 'X-Tenant-ID: 1'
```

## 7. 批准评论 POST /{id}/approve/
- 权限：需要认证；Member 不允许；文章作者/Admin/Super Admin 可操作。
```bash
curl -X POST http://your-domain.com/api/v1/cms/comments/1001/approve/ \
  -H 'Authorization: Bearer <token>' -H 'X-Tenant-ID: 1'
```

## 8. 拒绝评论 POST /{id}/reject/
```bash
curl -X POST http://your-domain.com/api/v1/cms/comments/1001/reject/ \
  -H 'Authorization: Bearer <token>' -H 'X-Tenant-ID: 1'
```

## 9. 标记垃圾评论 POST /{id}/mark-spam/
```bash
curl -X POST http://your-domain.com/api/v1/cms/comments/1001/mark-spam/ \
  -H 'Authorization: Bearer <token>' -H 'X-Tenant-ID: 1'
```

## 10. 批量处理评论 POST /batch/
```json
{"comment_ids":[1,2,3],"action":"approve"}
```
- `action`: approve | reject | spam | delete
- 权限：需要认证；普通用户仅可批量处理自己的评论与自己文章下的评论；Admin 可处理本租户全部；Super Admin 需指定租户。
- 示例：
```bash
curl -X POST http://your-domain.com/api/v1/cms/comments/batch/ \
  -H 'Authorization: Bearer <token>' -H 'X-Tenant-ID: 1' -H 'Content-Type: application/json' \
  -d '{"comment_ids":[1001,1002],"action":"approve"}'
```
