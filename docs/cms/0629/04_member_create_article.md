# Member 创建文章 API（含管理员专属分类校验）

## API 端点

```
POST /api/v1/cms/member/articles/
```

## 描述

Member 用户创建新文章。本次需求新增校验：若 `category_ids` 中包含 `is_admin_only=True` 的分类，返回 400 拒绝。

- Member 在管理员专属分类下创建文章 → 400
- Member 在开放分类下创建文章 → 201（正常）
- Member 同时关联管理员专属 + 开放分类 → 400（任一受限即拒绝）
- 管理员通过 `/api/v1/cms/articles/` 创建文章，不受此限制

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | `Bearer <token>`，Member token |
| Content-Type | string | 是 | `application/json` |
| X-Tenant-ID | string | 是 | 租户 ID |

## 请求体

```json
{
  "title": "我的第一篇文章",
  "content": "这是文章内容...",
  "content_type": "markdown",
  "excerpt": "文章摘要",
  "status": "draft",
  "application": 6,
  "category_ids": [25, 26],
  "tag_ids": [3, 8],
  "visibility": "public",
  "allow_comment": true
}
```

### 参数说明

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| title | string | 是 | 文章标题 |
| content | string | 是 | 文章内容 |
| content_type | string | 否 | 内容类型，可选值：markdown, html, image, video 等，默认 markdown |
| excerpt | string | 否 | 文章摘要，不传则自动从内容提取前 200 字符 |
| status | string | 否 | 文章状态，可选值：draft, pending, published, archived，默认 draft |
| application | integer | 是 | 关联应用 ID（Member 版本为单值，区别于管理员的 applications 数组） |
| **category_ids** | array | 否 | **分类 ID 列表。若含 `is_admin_only=True` 的分类，Member 会被拒绝** |
| tag_ids | array | 否 | 标签 ID 列表 |
| visibility | string | 否 | 可见性，可选值：public, private, password，默认 public |
| allow_comment | boolean | 否 | 是否允许评论，默认 true |
| cover_image | string | 否 | 封面图片 URL |
| is_featured | boolean | 否 | 是否特色，默认 false |
| is_pinned | boolean | 否 | 是否置顶，默认 false |
| parent | integer | 否 | 父文章 ID（用于系列文章） |
| meta | object | 否 | 文章元数据（SEO 相关） |
| publish_now | boolean | 否 | 是否立即发布，默认 false |
| scheduled_publish_time | string | 否 | 计划发布时间（ISO 8601） |

## 响应

### 成功响应（201 Created）

```json
{
  "id": 789,
  "title": "我的第一篇文章",
  "slug": "我的第一篇文章",
  "content": "这是文章内容...",
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
  "updated_at": "2026-06-29T08:40:00.000000Z",
  "tenant": "9f8c1b2a-1234-5678-9abc-def012345678"
}
```

### 失败响应

#### 在管理员专属分类下创建（400 Bad Request）— 本次需求新增

```json
{
  "分类 [公告] 是管理员专属分类，您无法在此分类下创建文章"
}
```

> 注：错误消息为 DRF ValidationError 格式，直接作为响应体返回。若关联了多个管理员专属分类，会用逗号连接名称，如 `"分类 [公告, 官方资讯] 是管理员专属分类，您无法在此分类下创建文章"`

#### 应用 ID 不存在（400 Bad Request）

```json
{
  "应用ID 999 不存在或无权限访问"
}
```

#### 分类 ID 不存在（400 Bad Request）

```json
{
  "分类ID 999 不存在或无权限访问"
}
```

#### 未认证（401 Unauthorized）

```json
{
  "detail": "身份认证信息未提供。"
}
```

## 调用示例

### cURL — Member 在开放分类下创建文章（成功）

```bash
curl -X POST 'http://localhost:8000/api/v1/cms/member/articles/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "title": "我的分享",
    "content": "今天学到了...",
    "content_type": "markdown",
    "status": "draft",
    "application": 6,
    "category_ids": [26],
    "tag_ids": [3],
    "visibility": "public",
    "allow_comment": true
  }'
```

**预期返回**：201 Created，响应体含文章详情

**前提**：ID=26 的分类 `is_admin_only=false`

### cURL — Member 在管理员专属分类下创建文章（被拒绝）

```bash
curl -X POST 'http://localhost:8000/api/v1/cms/member/articles/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "title": "尝试在公告分类发文",
    "content": "应该被拒绝",
    "content_type": "markdown",
    "status": "draft",
    "application": 6,
    "category_ids": [25]
  }'
```

**预期返回**：400 Bad Request
```json
{
  "分类 [公告] 是管理员专属分类，您无法在此分类下创建文章"
}
```

**前提**：ID=25 的分类 `is_admin_only=true`，名称为"公告"

### cURL — Member 关联混合分类（1 专属 + 1 开放，被拒绝）

```bash
curl -X POST 'http://localhost:8000/api/v1/cms/member/articles/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "title": "混合分类测试",
    "content": "应被拒绝（任一受限即拒绝）",
    "content_type": "markdown",
    "status": "draft",
    "application": 6,
    "category_ids": [25, 26]
  }'
```

**预期返回**：400 Bad Request
```json
{
  "分类 [公告] 是管理员专属分类，您无法在此分类下创建文章"
}
```

### cURL — Member 创建不关联分类的文章（成功）

```bash
curl -X POST 'http://localhost:8000/api/v1/cms/member/articles/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "title": "无分类文章",
    "content": "不关联任何分类",
    "content_type": "markdown",
    "status": "draft",
    "application": 6
  }'
```

**预期返回**：201 Created（不传 `category_ids` 不受 `is_admin_only` 影响）

## 注意事项

1. **任一受限即拒绝**：`category_ids` 中只要有一个分类 `is_admin_only=true`，整个请求被拒绝
2. **不传 category_ids 不受影响**：文章可以不关联任何分类，正常创建
3. **Member 专属端点**：此端点仅 Member 可用，管理员走 `/api/v1/cms/articles/`
4. **application 单值**：Member 版本用 `application`（单值），管理员版本用 `applications`（数组）
5. **子分类不继承**：父分类是管理员专属，子分类未标记时，Member 可以在子分类下创建文章
