# Member文章管理API文档

## 概述

Member文章API专为Member用户设计，Member用户只能管理自己创建的文章。

**基础路径**: `/api/v1/cms/member/articles/`

**重要**: Member用户的所有请求必须在Header中包含 `X-Tenant-ID: 3`

---

## 1. 获取我的文章列表

**请求方式**: `GET /api/v1/cms/member/articles/`

**权限**: Member

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 10 | 每页数量 |
| status | string | 否 | - | 文章状态：draft/pending/published/archived |
| search | string | 否 | - | 搜索关键词 |
| application | integer | 否 | - | 应用ID过滤（可选） |
| ordering | string | 否 | -created_at | 排序字段 |

**请求示例**:
```bash
# 获取所有已发布文章
curl -X GET "http://localhost:8000/api/v1/cms/member/articles/?status=published" \
  -H "Authorization: Bearer <MemberTOKEN>" \
  -H "X-Tenant-ID: 3"

# 按应用过滤文章
curl -X GET "http://localhost:8000/api/v1/cms/member/articles/?application=6" \
  -H "Authorization: Bearer <MemberTOKEN>" \
  -H "X-Tenant-ID: 3"
```

**响应参数**: 返回当前Member用户创建的文章列表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 请求是否成功 |
| data.pagination | object | 分页信息 |
| data.results | array | 我的文章列表 |

---

## 2. 创建文章

**请求方式**: `POST /api/v1/cms/member/articles/`

**权限**: Member

**请求体参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| title | string | 是 | - | 文章标题 |
| content | string | 是 | - | 文章内容 |
| content_type | string | 否 | markdown | 内容类型：markdown/html/text |
| excerpt | string | 否 | - | 摘要 |
| status | string | 否 | draft | 状态：draft/pending/published |
| **application** | **integer** | **是** | - | **关联的应用ID（必填）** |
| cover_image | string | 否 | - | 封面图片URL |
| category_ids | array | 否 | [] | 分类ID数组 |
| tag_ids | array | 否 | [] | 标签ID数组 |
| is_locked | boolean | 否 | false | 是否锁定（锁定后文章不可编辑） |
| allow_comment | boolean | 否 | true | 是否允许评论 |
| visibility | string | 否 | public | 可见性：public/private/password |
| password | string | 否 | - | 访问密码（visibility=password时必填） |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer <MemberTOKEN>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的第一篇文章",
    "content": "这是文章内容...",
    "content_type": "markdown",
    "excerpt": "文章摘要",
    "status": "draft",
    "application": 6,
    "category_ids": [1, 2],
    "tag_ids": [3, 4]
  }'
```

**响应参数**: 返回创建的文章对象

---

## 3. 获取我的单篇文章

**请求方式**: `GET /api/v1/cms/member/articles/{id}/`

**权限**: Member（只能查看自己的文章）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/member/articles/123/" \
  -H "Authorization: Bearer <MemberTOKEN>" \
  -H "X-Tenant-ID: 3"
```

**响应参数**: 返回完整的文章对象

---

## 4. 更新文章

**请求方式**: `PATCH /api/v1/cms/member/articles/{id}/`

**权限**: Member（只能更新自己的文章）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**请求体参数**: 

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| title | string | 否 | 文章标题 |
| content | string | 否 | 文章内容 |
| application | integer | 否 | 关联的应用ID（如提供则覆盖原有关联） |
| category_ids | array | 否 | 分类ID数组 |
| tag_ids | array | 否 | 标签ID数组 |
| ... | ... | 否 | 其他字段同创建 |

**请求示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/member/articles/123/" \
  -H "Authorization: Bearer <MemberTOKEN>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的标题",
    "content": "更新后的内容",
    "application_ids": [6]
  }'
```

---

## 5. 删除文章

**请求方式**: `DELETE /api/v1/cms/member/articles/{id}/`

**权限**: Member（只能删除自己的文章）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**说明**: Member用户删除文章只会将状态改为archived（软删除），不会物理删除

**请求示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/member/articles/123/" \
  -H "Authorization: Bearer <MemberTOKEN>" \
  -H "X-Tenant-ID: 3"
```

---

## 6. 发布文章

**请求方式**: `POST /api/v1/cms/member/articles/{id}/publish/`

**权限**: Member（只能发布自己的文章）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**说明**: 
- 将文章状态从draft/pending改为published
- 自动设置published_at为当前时间
- 文章必须是draft或pending状态才能发布

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/member/articles/123/publish/" \
  -H "Authorization: Bearer <MemberTOKEN>" \
  -H "X-Tenant-ID: 3"
```

**响应字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 是否成功 |
| message | string | 提示信息 |
| data.status | string | 新状态（published） |
| data.published_at | string | 发布时间 |

---

## 7. 获取文章统计

**请求方式**: `GET /api/v1/cms/member/articles/{id}/statistics/`

**权限**: Member（只能查看自己文章的统计）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| period | string | 否 | all | 统计周期：day/week/month/year/all |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/member/articles/123/statistics/?period=week" \
  -H "Authorization: Bearer <MemberTOKEN>" \
  -H "X-Tenant-ID: 3"
```

**响应字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| basic_stats | object | 基本统计 |
| basic_stats.views_count | integer | 浏览量 |
| basic_stats.likes_count | integer | 点赞数 |
| basic_stats.comments_count | integer | 评论数 |
| basic_stats.shares_count | integer | 分享数 |

---

## Member Token

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NTkwMzUwLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.1Cu5_gyY5n_rV9MTNf6wNQaov7BBUZQJizE4J0OmpNw
```

---

## 与租户管理员文章API的区别

| 特性 | Member文章API | 租户管理员文章API |
|------|---------------|-------------------|
| 基础路径 | `/member/articles/` | `/articles/` |
| 租户ID | 必须通过X-Tenant-ID传递 | 从Token自动获取 |
| 可见文章 | 只能看到自己的文章 | 可以看到所有文章 |
| 编辑权限 | 只能编辑自己的文章 | 可以编辑所有文章 |
| 删除方式 | 只有软删除（archived） | 支持软删除和强制删除 |
| 版本历史 | 不支持查看版本历史 | 支持查看版本历史 |
| 批量操作 | 不支持批量操作 | 支持批量删除等操作 |
| 取消发布 | 不支持 | 支持unpublish |
| 归档 | 不支持主动归档 | 支持archive操作 |

---

## 注意事项

### 1. 必须传递X-Tenant-ID
- **所有请求**都必须在Header中包含`X-Tenant-ID: 3`
- 这是Member用户识别所属租户的唯一方式
- 缺少此header会导致请求失败

### 2. 只能操作自己的文章
- Member用户只能查看、编辑、删除自己创建的文章
- 尝试访问其他人的文章会返回404错误
- 系统会自动验证作者身份

### 3. 软删除机制
- Member删除文章只会将状态改为archived
- 文章数据不会被物理删除
- 如需彻底删除，需要联系租户管理员

### 4. 发布限制
- 只能发布draft或pending状态的文章
- published状态的文章不能重复发布
- archived状态的文章需要先恢复才能发布

### 5. 不支持的功能
以下功能仅租户管理员可用，Member不支持：
- 取消发布（unpublish）
- 主动归档（archive）
- 查看版本历史（versions）
- 批量删除（batch-delete）
- 强制删除（force=true）

### 6. 文章状态流转

```
draft（草稿）
    ↓
    → publish → published（已发布）
    ↓
    → delete → archived（已归档）

pending（待审核）
    ↓
    → publish → published（已发布）
```

### 7. 推荐工作流程

**创作流程**：
1. 创建草稿（status=draft）
2. 编辑完善内容
3. 发布文章（调用publish接口）
4. 查看统计数据

**修改流程**：
1. 获取文章详情
2. 更新内容（PATCH）
3. 重新发布（如需要）

### 8. 错误处理

**常见错误**：

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 401 | 未认证 | 检查Token是否正确 |
| 403 | 权限不足 | 检查X-Tenant-ID是否正确 |
| 404 | 文章不存在 | 检查文章ID或确认是否是自己的文章 |
| 400 | 参数错误 | 检查请求参数格式 |

### 9. 性能建议
- 列表查询建议使用分页
- 避免频繁调用统计接口
- 图片建议先上传后再关联到文章
- 大量文章建议使用搜索和过滤功能

### 10. 安全建议
- 妥善保管Member Token
- 不要在前端代码中硬编码Token
- 使用HTTPS协议传输
- 设置合理的Token过期时间
