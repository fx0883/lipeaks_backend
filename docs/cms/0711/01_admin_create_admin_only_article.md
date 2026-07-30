# 管理员在租户 20 下创建仅管理员可编辑的文章

> 功能日期：2026-07-11
> 模块：CMS
> 目标读者：Hermes（可直接按本文档调用 API）

## 目标

以租户 `20` 的管理员身份（用户名 `admin_com`，密码 `admin_main`）登录后，在分类 `70` 下创建一篇文章，使得该文章**仅管理员可编辑**（Member 无法编辑/删除/发布）。

## 核心逻辑

本系统通过**分类**的 `is_admin_only` 字段控制文章编辑权限：

- 当分类 `is_admin_only=true` 时，该分类下的文章仅管理员可创建/编辑/删除/发布。
- Member 即使自己是作者，也无权操作该分类下的文章。
- 因此，要让文章“仅管理员可编辑”，只需把文章关联到 `is_admin_only=true` 的分类（本例为分类 `70`）。

## 前提条件

| 项目 | 值 | 说明 |
|------|-----|------|
| 租户 ID | `20` | 整数形式，通过 `?tenant_id=20` 传递 |
| 用户名 | `admin_com` | 管理员账号（User 类型） |
| 密码 | `admin_main` | |
| 分类 ID | `70` | 需确保 `is_admin_only=true`（见步骤 2） |
| Base URL | `http://localhost:8000` | 生产环境请替换为实际域名 |

## 完整调用流程

### 步骤 1：管理员登录获取 JWT Token

#### API 端点

```
POST /api/v1/auth/login/
```

#### 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Content-Type | string | 是 | `application/json` |

#### 请求体

```json
{
  "username": "admin_com",
  "password": "admin_main"
}
```

#### 成功响应（200 OK）

```json
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin_com",
      "email": "admin@example.com",
      "nick_name": "管理员",
      "is_admin": true,
      "is_super_admin": false,
      "is_member": false,
      "tenant_id": 20,
      "tenant_name": "租户名称"
    }
  }
}
```

> 后续请求使用 `data.token` 作为 `Authorization: Bearer <token>`。

---

### 步骤 2：确认分类 70 为“管理员专属”

#### 2.1 查询分类 70 当前状态

```
GET /api/v1/cms/categories/70/?tenant_id=20
```

##### 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | `Bearer <token>`，步骤 1 获取的 token |
| Content-Type | string | 是 | `application/json` |

##### 成功响应（200 OK）

```json
{
  "id": 70,
  "slug": "admin-only-category",
  "parent": null,
  "is_active": true,
  "is_pinned": false,
  "is_admin_only": true,
  "translations": {
    "zh-hans": {
      "name": "管理员专属分类",
      "description": "仅管理员可操作"
    }
  },
  "name": "管理员专属分类",
  "tenant": "..."
}
```

- 若 `is_admin_only` 已为 `true`，直接跳到**步骤 3**。
- 若 `is_admin_only` 为 `false`，执行 2.2 更新分类。

#### 2.2 更新分类 70 为管理员专属

```
PATCH /api/v1/cms/categories/70/?tenant_id=20
```

##### 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | `Bearer <token>` |
| Content-Type | string | 是 | `application/json` |

##### 请求体

```json
{
  "is_admin_only": true
}
```

##### 成功响应（200 OK）

```json
{
  "id": 70,
  "is_admin_only": true,
  "...": "..."
}
```

> 只有管理员（User 类型）可以修改 `is_admin_only`。Member 调用会返回 403。

---

### 步骤 3：管理员创建文章

#### API 端点

```
POST /api/v1/cms/articles/?tenant_id=20
```

#### 描述

管理员专用文章创建端点。请求体中通过 `category_ids: [70]` 将文章关联到管理员专属分类，从而实现“仅管理员可编辑”。

#### 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | `Bearer <token>`，管理员 token |
| Content-Type | string | 是 | `application/json` |

> 注意：管理员写操作**不能**使用 `X-Tenant-ID` 请求头，必须通过 `?tenant_id=20` 查询参数指定租户。

#### 请求体

```json
{
  "title": "管理员专属文章示例",
  "content": "这是仅管理员可编辑的文章内容。",
  "content_type": "markdown",
  "excerpt": "这是一篇仅管理员可编辑的文章摘要",
  "status": "published",
  "visibility": "public",
  "allow_comment": true,
  "is_featured": false,
  "is_pinned": false,
  "category_ids": [70],
  "tag_ids": [],
  "applications": [],
  "publish_now": true
}
```

#### 参数说明

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| title | string | 是 | 文章标题 |
| content | string | 是 | 文章内容 |
| content_type | string | 否 | 内容类型，默认 `markdown`。可选：`markdown`、`html`、`image`、`video`、`audio`、`file`、`link`、`quote`、`code`、`table`、`list` |
| excerpt | string | 否 | 文章摘要，不传则自动从内容提取前 200 字符 |
| status | string | 否 | 文章状态，默认 `draft`。可选：`draft`、`pending`、`published`、`archived` |
| visibility | string | 否 | 可见性，默认 `public`。可选：`public`、`private`、`password` |
| allow_comment | boolean | 否 | 是否允许评论，默认 `true` |
| is_featured | boolean | 否 | 是否特色，默认 `false` |
| is_pinned | boolean | 否 | 是否置顶，默认 `false` |
| **category_ids** | array[int] | 否 | **分类 ID 列表。必须包含分类 70，以实现仅管理员可编辑** |
| tag_ids | array[int] | 否 | 标签 ID 列表 |
| applications | array[int] | 否 | 关联应用 ID 列表（管理员版本为数组，区别于 Member 版本的 `application` 单值） |
| publish_now | boolean | 否 | 是否立即发布，默认 `false` |
| scheduled_publish_time | string | 否 | 计划发布时间（ISO 8601 格式） |
| meta | object | 否 | 文章元数据（SEO 相关） |
| parent | integer | 否 | 父文章 ID |

#### 成功响应（201 Created）

```json
{
  "id": 1001,
  "title": "管理员专属文章示例",
  "slug": "admin-only-category-example",
  "content": "这是仅管理员可编辑的文章内容。",
  "content_type": "markdown",
  "excerpt": "这是一篇仅管理员可编辑的文章摘要",
  "status": "published",
  "user": 1,
  "member": null,
  "is_featured": false,
  "is_pinned": false,
  "allow_comment": true,
  "visibility": "public",
  "published_at": "2026-07-11T08:00:00.000000Z",
  "cover_image": null,
  "cover_image_small": null,
  "template": null,
  "sort_order": 0,
  "created_at": "2026-07-11T08:00:00.000000Z",
  "updated_at": "2026-07-11T08:00:00.000000Z",
  "tenant": "..."
}
```

> 响应中的 `user` 字段为管理员 ID，`member` 为 `null`，表示这是一篇管理员 authored 的文章。

---

## 失败响应

### 未认证（401 Unauthorized）

```json
{
  "detail": "身份认证信息未提供。"
}
```

### 管理员携带 X-Tenant-ID 头（400 Bad Request）

```json
{
  "code": 4000,
  "message": "管理员/超级管理员不能通过X-Tenant-ID请求头指定租户，请使用tenant_id查询参数",
  "data": null
}
```

### 分类 70 不存在或无权限（400 Bad Request）

```json
{
  "分类ID 70 不存在或无权限访问"
}
```

### Member 尝试在管理员专属分类下创建文章（403 Forbidden）

> 注意：本端点为管理员端点，Member 本无权限访问。若用 Member token 调用 `/api/v1/cms/member/articles/` 并传 `category_ids: [70]`，会返回：

```json
{
  "detail": "分类 [管理员专属分类] 是管理员专属分类，您无权编辑该分类下的文章"
}
```

---

## 完整 cURL 示例

### 示例 1：登录

```bash
curl -X POST 'http://localhost:8000/api/v1/auth/login/' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "admin_com",
    "password": "admin_main"
  }'
```

**预期返回**：200 OK，从 `data.token` 提取 JWT。

### 示例 2：查询分类 70 状态

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/categories/70/?tenant_id=20' \
  -H 'Authorization: Bearer <ADMIN_TOKEN>' \
  -H 'Content-Type: application/json'
```

**预期返回**：200 OK，检查 `is_admin_only` 是否为 `true`。

### 示例 3：将分类 70 设为管理员专属（如需要）

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/categories/70/?tenant_id=20' \
  -H 'Authorization: Bearer <ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "is_admin_only": true
  }'
```

**预期返回**：200 OK，`is_admin_only` 变为 `true`。

### 示例 4：管理员创建仅管理员可编辑的文章

```bash
curl -X POST 'http://localhost:8000/api/v1/cms/articles/?tenant_id=20' \
  -H 'Authorization: Bearer <ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "管理员专属文章示例",
    "content": "这是仅管理员可编辑的文章内容。",
    "content_type": "markdown",
    "excerpt": "这是一篇仅管理员可编辑的文章摘要",
    "status": "published",
    "visibility": "public",
    "allow_comment": true,
    "is_featured": false,
    "is_pinned": false,
    "category_ids": [70],
    "tag_ids": [],
    "applications": [],
    "publish_now": true
  }'
```

**预期返回**：201 Created，响应体包含文章详情，`user` 为管理员 ID，`member` 为 `null`。

---

## 验证“仅管理员可编辑”

创建完成后，可通过以下方式验证权限：

1. **用 Member 账号调用 Member 更新端点**：

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/member/articles/<article_id>/' \
  -H 'Authorization: Bearer <MEMBER_TOKEN>' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 20' \
  -d '{
    "title": "Member 尝试修改"
  }'
```

**预期返回**：403 Forbidden

```json
{
  "detail": "分类 [管理员专属分类] 是管理员专属分类，您无权编辑该分类下的文章"
}
```

2. **用管理员账号调用管理员更新端点**（应成功）：

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/articles/<article_id>/?tenant_id=20' \
  -H 'Authorization: Bearer <ADMIN_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "管理员修改后的标题"
  }'
```

**预期返回**：200 OK

---

## 注意事项

1. **租户传递方式**：管理员写操作必须通过 `?tenant_id=20` 查询参数指定租户，**不能**使用 `X-Tenant-ID` 请求头。
2. **权限控制粒度**：“仅管理员可编辑”是通过分类 `is_admin_only=true` 实现的，不是文章本身的字段。
3. **观看权限不受影响**：管理员专属分类下的公开文章，所有人（含游客）仍可正常观看。
4. **子分类不继承**：如果分类 70 有子分类，子分类默认 `is_admin_only=false`，需要单独设置。
5. **Member 端点不同**：管理员创建文章使用 `/api/v1/cms/articles/`，Member 创建文章使用 `/api/v1/cms/member/articles/`。
6. **applications 字段**：管理员版本使用 `applications`（数组），Member 版本使用 `application`（单值）。
