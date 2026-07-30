# Member 更新 / 删除 / 发布文章 API（含管理员专属分类校验）

## API 端点

```
PATCH /api/v1/cms/member/articles/{id}/         # 部分更新
PUT   /api/v1/cms/member/articles/{id}/         # 全量更新
DELETE /api/v1/cms/member/articles/{id}/        # 删除（软删除，状态改为 archived）
POST  /api/v1/cms/member/articles/{id}/publish/ # 发布
```

## 描述

Member 用户对自己的文章进行更新、删除、发布操作。本次需求新增校验：若文章关联的分类中含 `is_admin_only=True` 的分类，所有这些操作都会被 403 拒绝。

**严格模式**：配置立即生效。即使文章是 Member 在分类标记为管理员专属**之前**创建的，标记之后 Member 也不能再编辑/删除/发布该文章。

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | `Bearer <token>`，Member token |
| Content-Type | string | 是 | `application/json`（PATCH/PUT/POST 需要，DELETE 不需要） |
| X-Tenant-ID | string | 是 | 租户 ID |

## 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer | 是 | 文章 ID |

---

## 1. 更新文章（PATCH / PUT）

### 请求体（PATCH 示例）

```json
{
  "title": "更新后的标题",
  "content": "更新后的内容",
  "category_ids": [26, 27]
}
```

### 参数说明

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| title | string | 否 | 文章标题 |
| content | string | 否 | 文章内容 |
| content_type | string | 否 | 内容类型 |
| excerpt | string | 否 | 文章摘要 |
| status | string | 否 | 文章状态 |
| application | integer | 否 | 关联应用 ID |
| **category_ids** | array | 否 | **分类 ID 列表。若含管理员专属分类，Member 会被 403 拒绝** |
| tag_ids | array | 否 | 标签 ID 列表 |
| visibility | string | 否 | 可见性 |
| allow_comment | boolean | 否 | 是否允许评论 |

### 成功响应（200 OK）

```json
{
  "id": 789,
  "title": "更新后的标题",
  "slug": "我的第一篇文章",
  "content": "更新后的内容",
  "content_type": "markdown",
  "excerpt": "文章摘要",
  "status": "draft",
  "user": null,
  "member": 456,
  "is_featured": false,
  "is_pinned": false,
  "allow_comment": true,
  "visibility": "public",
  "published_at": null,
  "cover_image": null,
  "sort_order": 0,
  "created_at": "2026-06-29T08:40:00.000000Z",
  "updated_at": "2026-06-29T08:45:00.000000Z",
  "tenant": "9f8c1b2a-1234-5678-9abc-def012345678"
}
```

### 失败响应

#### 文章关联管理员专属分类（403 Forbidden）— 本次需求新增

```json
{
  "detail": "分类 [公告] 是管理员专属分类，您无权编辑该分类下的文章"
}
```

> 注：即使请求体不含 `category_ids`，也会检查文章**当前关联的分类**是否含管理员专属。这是严格模式的体现。

#### 文章不属于当前 Member（400 Bad Request）

```json
{
  "你只能编辑自己的文章"
}
```

---

## 2. 删除文章（DELETE）

### 请求体

无需请求体。

### 成功响应（204 No Content）

空响应体。

### 失败响应

#### 文章关联管理员专属分类（403 Forbidden）— 本次需求新增

```json
{
  "detail": "分类 [公告] 是管理员专属分类，您无权删除该分类下的文章"
}
```

#### 文章不属于当前 Member（400 Bad Request）

```json
{
  "你只能删除自己的文章"
}
```

---

## 3. 发布文章（POST /publish/）

### 请求体

无需请求体。

### 成功响应（200 OK）

```json
{
  "id": 789,
  "title": "我的第一篇文章",
  "slug": "我的第一篇文章",
  "content": "这是文章内容...",
  "content_type": "markdown",
  "status": "published",
  "user": null,
  "member": 456,
  "is_featured": false,
  "is_pinned": false,
  "allow_comment": true,
  "visibility": "public",
  "published_at": "2026-06-29T08:50:00.000000Z",
  "cover_image": null,
  "sort_order": 0,
  "created_at": "2026-06-29T08:40:00.000000Z",
  "updated_at": "2026-06-29T08:50:00.000000Z",
  "tenant": "9f8c1b2a-1234-5678-9abc-def012345678"
}
```

### 失败响应

#### 文章关联管理员专属分类（403 Forbidden）— 本次需求新增

```json
{
  "detail": "分类 [公告] 是管理员专属分类，您无权发布该分类下的文章"
}
```

#### 文章不属于当前 Member（403 Forbidden）

```json
{
  "detail": "你只能发布自己的文章"
}
```

#### 文章状态不允许发布（400 Bad Request）

```json
{
  "detail": "只有草稿或待审核状态的文章可以发布"
}
```

---

## 调用示例

### cURL — Member 更新开放分类下的文章（成功）

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/member/articles/789/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "title": "更新后的标题",
    "content": "更新后的内容"
  }'
```

**预期返回**：200 OK

**前提**：文章 789 关联的分类都是 `is_admin_only=false`

### cURL — Member 更新管理员专属分类下的文章（被拒绝）

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/member/articles/790/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "title": "尝试更新"
  }'
```

**预期返回**：403 Forbidden
```json
{
  "detail": "分类 [公告] 是管理员专属分类，您无权编辑该分类下的文章"
}
```

**前提**：文章 790 关联了 `is_admin_only=true` 的分类（ID=25，名称"公告"）

> 注：即使请求体不含 `category_ids`，也会被拒绝（严格模式，检查文章当前关联分类）

### cURL — Member 把文章移到管理员专属分类（被拒绝）

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/member/articles/789/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "category_ids": [25]
  }'
```

**预期返回**：400 Bad Request（在 serializer.validate 阶段拦截）
```json
{
  "分类 [公告] 是管理员专属分类，您无法在此分类下创建文章"
}
```

> 注：更新时传入新的 `category_ids` 含管理员专属分类，会在序列化器校验阶段被 400 拦截（与创建一致）；如果不传 `category_ids` 但文章当前关联管理员专属分类，会在 `perform_update` 阶段被 403 拦截。

### cURL — Member 删除管理员专属分类下的文章（被拒绝）

```bash
curl -X DELETE 'http://localhost:8000/api/v1/cms/member/articles/790/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
```

**预期返回**：403 Forbidden
```json
{
  "detail": "分类 [公告] 是管理员专属分类，您无权删除该分类下的文章"
}
```

### cURL — Member 发布管理员专属分类下的草稿（被拒绝）

```bash
curl -X POST 'http://localhost:8000/api/v1/cms/member/articles/790/publish/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
```

**预期返回**：403 Forbidden
```json
{
  "detail": "分类 [公告] 是管理员专属分类，您无权发布该分类下的文章"
}
```

### cURL — 管理员取消标记后 Member 恢复操作权限

**Step 1：管理员取消标记**

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/categories/25/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin_token' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "is_admin_only": false
  }'
```

**Step 2：Member 现在可以更新/删除/发布该分类下的文章**

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/member/articles/790/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "title": "取消标记后可以更新了"
  }'
```

**预期返回**：200 OK（权限立即恢复）

## 错误消息动作映射

| 操作 | action 参数 | 错误消息中的动词 |
|------|------------|-----------------|
| 更新（PATCH/PUT） | update | 编辑 |
| 删除（DELETE） | delete | 删除 |
| 发布（POST /publish/） | publish | 发布 |

## 注意事项

1. **严格模式**：即使请求体不含 `category_ids`，也会检查文章**当前关联的分类**是否含管理员专属。这是为了防止 Member 通过"不传 category_ids"绕过校验
2. **配置即时生效**：管理员取消 `is_admin_only` 标记后，Member 立即恢复操作权限，无需重启服务
3. **两种拦截点**：
   - 传入新的 `category_ids` 含管理员专属 → 400（序列化器校验阶段）
   - 文章当前关联管理员专属分类 → 403（视图 perform 阶段）
4. **软删除**：DELETE 不是物理删除，而是把 status 改为 `archived`
5. **发布条件**：只有 `draft` 或 `pending` 状态的文章可以发布
6. **作者校验优先**：所有操作都先校验"是否是文章作者"，再校验"是否关联管理员专属分类"
