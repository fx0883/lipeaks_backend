# 文章管理 API

Base: `/api/v1/cms/articles/`

## 通用要求
- **Headers（必须）**：
  - `X-Tenant-ID: <tenant_id>`
  - `Authorization: Bearer <token>`（GET匿名可不带；POST/PUT/PATCH/DELETE 需要；特例见“记录阅读”）
  - `Content-Type: application/json`
- **权限模型**：
  - 匿名：仅可读取公开且已发布的文章（`status=published && visibility=public`）。
  - Member：可创建；仅可更新/删除自己文章。
  - Admin：可管理本租户下所有文章。
  - Super Admin：需通过 `X-Tenant-ID` 指定目标租户，方可管理该租户文章。

## 1. 获取文章列表 GET /
- 参数：
  - `page`, `page_size`
  - `status` (draft|pending|published|archived)
  - `category_id`, `tag_id`, `author_id`
  - `search`
  - `sort` (created_at|updated_at|published_at|title|views_count)
  - `sort_direction` (asc|desc)
  - `is_featured`, `is_pinned`, `visibility` (public|private|password)
  - `date_from`, `date_to` (YYYY-MM-DD)
- 权限：匿名允许；但若尝试获取非公开或非发布文章，需具备相应身份（作者/Admin/Super Admin）。
- Headers：必须包含 `X-Tenant-ID`。
- 示例：
```bash
curl -X GET "http://your-domain.com/api/v1/cms/articles/?status=published&search=demo" \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1"
```
- 响应（节选）：
```json
{
  "count": 42,
  "results": [{
    "id": 1, "title": "标题", "slug": "title", "excerpt": "摘要...",
    "author_info": {"id":1, "username":"admin"},
    "status": "published",
    "cover_image": "https://.../image.jpg",
    "categories": [{"id":3,"name":"技术","slug":"tech"}],
    "tags": [{"id":8,"name":"Python","slug":"python","color":"#3776AB"}],
    "comments_count": 15, "likes_count": 42, "views_count": 1250
  }]
}
```

## 2. 获取单篇文章 GET /{id}/
- 查询参数：`password`（当 `visibility=password` 时），`version`
- 权限：匿名可读公开发布文章；草稿/待审/私有文章仅作者、Admin、Super Admin 可读。
- Headers：必须包含 `X-Tenant-ID`。
- 示例：
```bash
curl -X GET http://your-domain.com/api/v1/cms/articles/1/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1"
```
- 响应要点：包含 `meta`、`stats`、`version_info`、`breadcrumb`、`children`

## 3. 创建文章 POST /
- 请求体主要字段：
  - 基本：`title`, `content`, `content_type(markdown|html)`, `excerpt`
  - 状态与显示：`status`, `is_featured`, `is_pinned`, `allow_comment`, `visibility`, `password`
  - 资源：`cover_image`, `cover_image_small`, `template`, `sort_order`, `parent`
  - 关联：`category_ids[]`, `tag_ids[]`, `meta{seo_title, seo_description, ...}`
  - 发布：`publish_now`, `scheduled_publish_time`
- 权限：需要认证。Member可创建（作者自动为当前用户），Admin/Super Admin 可创建。
- Headers：`Authorization`, `X-Tenant-ID` 必须。
- 示例：
```bash
curl -X POST http://your-domain.com/api/v1/cms/articles/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{
    "title":"我的文章","content":"内容...","content_type":"markdown",
    "category_ids":[2,5],"tag_ids":[3,8],
    "meta":{"seo_title":"SEO标题"},"publish_now":false
  }'
```

### 字段说明（创建/更新通用）

| 字段 | 类型 | 必填 | 说明/约束 |
|---|---|---|---|
| title | string | 是 | 标题，建议唯一；若未提供 slug 将根据标题自动生成 |
| slug | string | 否 | 自定义URL标识，未提供则自动生成并去重 |
| content | string | 是 | 正文内容 |
| content_type | enum | 否 | `markdown` 或 `html`，默认 `markdown` |
| excerpt | string | 否 | 摘要，未提供时后端可能自动截取 |
| status | enum | 否 | `draft`/`pending`/`published`/`archived`，默认 `draft` |
| is_featured | boolean | 否 | 是否精选 |
| is_pinned | boolean | 否 | 是否置顶 |
| allow_comment | boolean | 否 | 是否允许评论，默认 true |
| visibility | enum | 否 | `public`/`private`/`password`，默认 `public` |
| password | string | 否 | 当 `visibility=password` 时必填，用于查看保护 |
| cover_image | string(URL) | 否 | 封面图 |
| cover_image_small | string(URL) | 否 | 封面小图 |
| template | string | 否 | 自定义渲染模板标识 |
| sort_order | integer | 否 | 排序值，越大越靠前 |
| parent | integer | 否 | 父文章ID，用于层级结构 |
| category_ids | int[] | 否 | 关联分类ID列表（需属于当前租户） |
| tag_ids | int[] | 否 | 关联标签ID列表（需属于当前租户） |
| meta | object | 否 | 文章元数据，如 `seo_title`、`seo_description` 等 |
| publish_now | boolean | 否 | 是否立即发布（创建/更新时可用） |
| scheduled_publish_time | datetime | 否 | 计划发布时间（与自动发布策略相关） |

> 更新专属字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
 | create_new_version | boolean | 否 | 默认 true；更新正文等内容时自动生成新版本 |
 | change_description | string | 否 | 本次修改说明，便于版本历史追踪 |

### 常见错误码与响应示例（创建/更新通用）

- 400 Bad Request（参数校验失败）
```json
{
  "detail": "无效的参数",
  "errors": {
    "category_ids": ["分类不存在或不属于当前租户"],
    "title": ["该字段是必填项"]
  }
}
```

- 401 Unauthorized（未登录/Token失效）
```json
{
  "detail": "Authentication credentials were not provided."
}
```

- 403 Forbidden（权限不足，例如Member修改他人文章）
```json
{
  "detail": "您没有权限执行此操作"
}
```

- 404 Not Found（资源不存在或不属于当前租户）
```json
{
  "detail": "未找到"
}
```

- 409 Conflict（slug 冲突或状态不允许的业务冲突）
```json
{
  "detail": "slug已存在，请更换或留空由系统自动生成"
}
```

## 4. 更新文章 PUT /{id}/
- 额外字段：`create_new_version`(默认true), `change_description`
- 权限：需要认证。
  - Member 仅可更新自己文章。
  - Admin 可更新本租户任何文章。
  - Super Admin 需带 `X-Tenant-ID`，可更新该租户文章。
- Headers：`Authorization`, `X-Tenant-ID` 必须。

## 5. 部分更新文章 PATCH /{id}/
- 示例：
```bash
curl -X PATCH http://your-domain.com/api/v1/cms/articles/15/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{"status":"published","is_featured":true,"publish_now":true}'
```
- 权限与Headers要求同“更新文章”。

## 6. 删除文章 DELETE /{id}/
- 查询：`?force=true`（强制删除），默认软删除（状态改为 `archived`）
- 权限：需要认证。
  - Member 仅可删除自己文章。
  - Admin 可删除本租户任何文章。
  - Super Admin 需带 `X-Tenant-ID`，可删除该租户文章。
- Headers：`Authorization`, `X-Tenant-ID` 必须。

## 7. 批量删除文章 POST /batch-delete/
```json
{"article_ids":[1,2,3], "force": false}
```
- 权限：需要认证（同单条删除的角色规则）。
- Headers：`Authorization`, `X-Tenant-ID` 必须。

## 8. 获取文章版本历史 GET /{id}/versions/
- 权限：匿名可读取公开发布文章的版本列表；非公开需作者/Admin/Super Admin。
- Headers：`X-Tenant-ID` 必须。

## 9. 获取特定版本 GET /{id}/versions/{version_number}/
- 权限与Headers：同“获取文章版本历史”。

## 10. 获取文章统计 GET /{id}/statistics/
- 参数：`period`(day|week|month|year|all), `start_date`, `end_date`
- 响应：`basic_stats`, `time_series.views`, `demographics(countries/devices/browsers)`, `referrers`
- 权限：匿名可读公开发布文章统计；非公开需作者/Admin/Super Admin。
- Headers：`X-Tenant-ID` 必须。

## 11. 记录阅读 POST /{id}/view/
- 无需认证；记录访问日志并自增 `views_count`
- 权限：该动作在代码中对该动作使用 `permission_classes=[]` 放宽，但需能定位到同租户文章对象。
- Headers：建议携带 `X-Tenant-ID` 以确保能正确匹配文章归属。
  
## 12. 发布文章 POST /{id}/publish/

将文章状态改为已发布。

### 权限要求
- **需要认证**（登录）
- **Member**: 只能发布自己创建的文章
- **Admin**: 可以发布本租户所有文章
- **Super Admin**: 需通过 `X-Tenant-ID` 指定租户

### Headers（必须）
```http
Authorization: Bearer <token>
X-Tenant-ID: 1
```

### 业务规则
- 文章当前状态必须不是 `published`
- 发布成功后自动设置 `published_at` 为当前时间
- 会记录操作日志

### 请求示例
```bash
# Member发布自己的文章
curl -X POST http://your-domain.com/api/v1/cms/articles/15/publish/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1"
```

### 响应示例

**成功响应 (200)**
```json
{
  "message": "文章已成功发布",
  "id": 15,
  "status": "published",
  "published_at": "2024-01-20T10:30:00Z"
}
```

**错误响应 (403) - Member尝试发布别人的文章**
```json
{
  "detail": "您只能发布自己创建的文章"
}
```

**错误响应 (400) - 文章已经是发布状态**
```json
{
  "detail": "文章已经是发布状态"
}
```

---

## 13. 取消发布文章 POST /{id}/unpublish/

将文章状态从已发布改为草稿。

### 权限要求
- **需要认证**（登录）
- **Member**: 只能取消发布自己创建的文章
- **Admin**: 可以取消发布本租户所有文章
- **Super Admin**: 需通过 `X-Tenant-ID` 指定租户

### Headers（必须）
```http
Authorization: Bearer <token>
X-Tenant-ID: 1
```

### 业务规则
- 文章当前状态必须是 `published`
- 取消发布后状态变为 `draft`（草稿）
- `published_at` 时间戳保持不变
- 会记录操作日志

### 使用场景
Member发现已发布的文章有问题需要下线修改，可调用此接口将文章改为草稿状态。

### 请求示例
```bash
# Member取消发布自己的文章
curl -X POST http://your-domain.com/api/v1/cms/articles/15/unpublish/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1"
```

### 响应示例

**成功响应 (200)**
```json
{
  "message": "文章已取消发布",
  "id": 15,
  "status": "draft"
}
```

**错误响应 (403)**
```json
{
  "detail": "您只能取消发布自己创建的文章"
}
```

**错误响应 (400)**
```json
{
  "detail": "文章不是发布状态，无法取消发布"
}
```

---

## 14. 归档文章 POST /{id}/archive/

将文章状态改为归档。归档的文章不会在前台展示，但保留在数据库中。

### 权限要求
- **需要认证**（登录）
- **Member**: 只能归档自己创建的文章
- **Admin**: 可以归档本租户所有文章
- **Super Admin**: 需通过 `X-Tenant-ID` 指定租户

### Headers（必须）
```http
Authorization: Bearer <token>
X-Tenant-ID: 1
```

### 业务规则
- 任何状态的文章都可以归档
- 归档后状态变为 `archived`
- 归档的文章匿名用户无法访问
- 会记录操作日志

### 使用场景
Member想要隐藏过时或不再需要的文章，但又不想完全删除。

### 请求示例
```bash
# Member归档自己的文章
curl -X POST http://your-domain.com/api/v1/cms/articles/15/archive/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1"
```

### 响应示例

**成功响应 (200)**
```json
{
  "message": "文章已归档",
  "id": 15,
  "status": "archived"
}
```

**错误响应 (403)**
```json
{
  "detail": "您只能归档自己创建的文章"
}
```

**错误响应 (400)**
```json
{
  "detail": "文章已经是归档状态"
}
```
