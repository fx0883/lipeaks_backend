# CMS文章管理API文档

## API端点列表

**基础路径**: `/api/v1/cms/articles/`

---

## 1. 获取文章列表

**请求方式**: `GET /api/v1/cms/articles/`

**权限**: 租户管理员、Member

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 10 | 每页数量 |
| status | string | 否 | - | 文章状态：draft/pending/published/archived |
| category_id | integer | 否 | - | 分类ID过滤 |
| tag_id | integer | 否 | - | 标签ID过滤 |
| author_id | integer | 否 | - | 作者ID过滤 |
| author_type | string | 否 | - | 作者类型：member/admin |
| search | string | 否 | - | 搜索关键词 |
| application | integer | 否 | - | 应用ID过滤（可选） |
| ordering | string | 否 | -created_at | 排序字段，可选值见下方说明 |
| is_featured | boolean | 否 | - | 是否特色文章 |
| is_pinned | boolean | 否 | - | 是否置顶文章 |
| visibility | string | 否 | - | 可见性：public/private/password |

**排序字段**（ordering参数可选值）:
- `created_at` / `-created_at` - 创建时间升序/降序
- `updated_at` / `-updated_at` - 更新时间升序/降序
- `published_at` / `-published_at` - 发布时间升序/降序
- `title` / `-title` - 标题升序/降序
- `views_count` / `-views_count` - 浏览量升序/降序

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/?page=1&status=published&ordering=-published_at" \
  -H "Authorization: Bearer <TOKEN>"

# 获取特定应用的文章
curl -X GET "http://localhost:8000/api/v1/cms/admin/articles/?application=6" \
  -H "Authorization: Bearer <TenantAdminTOKEN>" \
  -H "X-Tenant-ID: 3"
```

**响应参数**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 请求是否成功 |
| code | integer | 状态码（2000表示成功） |
| message | string | 返回消息 |
| data | object | 数据对象 |
| data.pagination | object | 分页信息 |
| data.pagination.count | integer | 总记录数 |
| data.pagination.page_size | integer | 每页数量 |
| data.pagination.current_page | integer | 当前页码 |
| data.pagination.total_pages | integer | 总页数 |
| data.pagination.next | string | 下一页URL |
| data.pagination.previous | string | 上一页URL |
| data.results | array | 文章列表 |

**文章对象字段**（results中每个元素）:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 文章ID |
| title | string | 文章标题 |
| slug | string | URL别名 |
| excerpt | string | 摘要 |
| author_info | object | 作者信息对象 |
| author_info.id | integer | 作者ID |
| author_info.username | string | 作者用户名 |
| author_info.email | string | 作者邮箱 |
| author_info.nick_name | string | 作者昵称 |
| author_type | string | 作者类型：member/admin |
| status | string | 文章状态 |
| is_featured | boolean | 是否特色文章 |
| is_pinned | boolean | 是否置顶 |
| is_locked | boolean | 是否锁定（锁定后不可编辑） |
| cover_image | string | 封面图片URL |
| published_at | string | 发布时间（ISO 8601格式） |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| categories | array | 分类列表 |
| tags | array | 标签列表 |
| comments_count | integer | 评论数 |
| likes_count | integer | 点赞数 |
| views_count | integer | 浏览数 |

---

## 2. 创建文章

**请求方式**: `POST /api/v1/cms/articles/`

**权限**: 租户管理员、Member

**请求体参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| title | string | 是 | - | 文章标题（最大200字符） |
| content | string | 是 | - | 文章内容 |
| content_type | string | 否 | markdown | 内容类型：markdown/html/text |
| excerpt | string | 否 | - | 摘要（最大500字符） |
| status | string | 否 | draft | 状态：draft/pending/published/archived |
| is_featured | boolean | 否 | false | 是否特色文章 |
| is_pinned | boolean | 否 | false | 是否置顶 |
| is_locked | boolean | 否 | false | 是否锁定（锁定后文章不可编辑） |
| allow_comment | boolean | 否 | true | 是否允许评论 |
| visibility | string | 否 | public | 可见性：public/private/password |
| password | string | 否 | - | 访问密码（visibility=password时必填） |
| cover_image | string | 否 | - | 封面图片URL |
| cover_image_small | string | 否 | - | 封面小图URL |
| template | string | 否 | - | 使用的模板名称 |
| sort_order | integer | 否 | 0 | 排序顺序 |
| parent | integer | 否 | - | 父文章ID（用于子文章） |
| category_ids | array | 否 | [] | 分类ID数组 |
| tag_ids | array | 否 | [] | 标签ID数组 |
| meta | object | 否 | - | SEO元数据对象 |

**meta对象字段**:

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| seo_title | string | 否 | SEO标题 |
| seo_description | string | 否 | SEO描述 |
| seo_keywords | string | 否 | SEO关键词 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python最佳实践指南",
    "content": "# Python最佳实践\n\n详细内容...",
    "content_type": "markdown",
    "excerpt": "学习Python编程的最佳实践",
    "status": "draft",
    "category_ids": [1, 2],
    "tag_ids": [5, 8],
    "meta": {
      "seo_title": "Python最佳实践完整指南",
      "seo_description": "详细介绍Python编程的最佳实践"
    }
  }'
```

**响应参数**: 返回创建的文章对象，包含所有字段

---

## 3. 获取单篇文章

**请求方式**: `GET /api/v1/cms/articles/{id}/`

**权限**: 租户管理员、Member

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| password | string | 否 | 访问密码（文章visibility=password时需要） |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/123/" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应字段**（完整文章对象）:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 文章ID |
| title | string | 标题 |
| slug | string | URL别名 |
| content | string | 完整内容 |
| content_type | string | 内容类型 |
| excerpt | string | 摘要 |
| author_info | object | 作者信息 |
| author_type | string | 作者类型 |
| status | string | 状态 |
| is_featured | boolean | 是否特色 |
| is_pinned | boolean | 是否置顶 |
| is_locked | boolean | 是否锁定 |
| allow_comment | boolean | 是否允许评论 |
| visibility | string | 可见性 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| published_at | string | 发布时间 |
| cover_image | string | 封面图片 |
| template | string | 模板 |
| tenant | integer | 租户ID |
| categories | array | 分类列表 |
| tags | array | 标签列表 |
| meta | object | SEO元数据 |
| stats | object | 统计信息 |
| version_info | object | 版本信息 |
| parent | integer | 父文章ID |
| children | array | 子文章列表 |
| breadcrumb | array | 面包屑导航 |

---

## 4. 更新文章

**请求方式**: `PATCH /api/v1/cms/articles/{id}/`

**权限**: 租户管理员（所有文章）、Member（自己的文章）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**请求体参数**: 与创建文章相同，但所有字段都是可选的

**请求示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/articles/123/" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的标题",
    "status": "published"
  }'
```

---

## 5. 删除文章

**请求方式**: `DELETE /api/v1/cms/articles/{id}/`

**权限**: 租户管理员（所有文章）、Member（自己的文章）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| force | boolean | 否 | false | 是否强制删除（true=物理删除，false=软删除） |

**请求示例**:
```bash
# 软删除（改为archived状态）
curl -X DELETE "http://localhost:8000/api/v1/cms/articles/123/" \
  -H "Authorization: Bearer <TOKEN>"

# 强制删除（物理删除）
curl -X DELETE "http://localhost:8000/api/v1/cms/articles/123/?force=true" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 6. 发布文章

**请求方式**: `POST /api/v1/cms/articles/{id}/publish/`

**权限**: 租户管理员、Member（自己的文章）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**说明**: 将文章状态从draft/pending改为published，并设置published_at为当前时间

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/123/publish/" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 是否成功 |
| message | string | 提示信息 |
| data.message | string | 操作结果消息 |
| data.id | integer | 文章ID |
| data.status | string | 新状态（published） |
| data.published_at | string | 发布时间 |

---

## 7. 取消发布文章

**请求方式**: `POST /api/v1/cms/articles/{id}/unpublish/`

**权限**: 租户管理员、Member（自己的文章）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**说明**: 将文章状态从published改为draft

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/123/unpublish/" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 8. 归档文章

**请求方式**: `POST /api/v1/cms/articles/{id}/archive/`

**权限**: 租户管理员、Member（自己的文章）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**说明**: 将文章状态改为archived，归档的文章不会在前台展示

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/123/archive/" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 9. 记录文章阅读

**请求方式**: `POST /api/v1/cms/articles/{id}/view/`

**权限**: 公开（无需认证）

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**说明**: 记录文章的阅读行为，更新浏览量统计

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/123/view/"
```

---

## 10. 获取文章统计

**请求方式**: `GET /api/v1/cms/articles/{id}/statistics/`

**权限**: 租户管理员、Member

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| period | string | 否 | all | 统计周期：day/week/month/year/all |
| start_date | string | 否 | - | 起始日期（YYYY-MM-DD） |
| end_date | string | 否 | - | 结束日期（YYYY-MM-DD） |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/123/statistics/?period=week" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| basic_stats | object | 基本统计 |
| basic_stats.views_count | integer | 浏览量 |
| basic_stats.unique_views_count | integer | 独立访客数 |
| basic_stats.likes_count | integer | 点赞数 |
| basic_stats.comments_count | integer | 评论数 |
| basic_stats.shares_count | integer | 分享数 |
| basic_stats.bookmarks_count | integer | 收藏数 |
| basic_stats.avg_reading_time | integer | 平均阅读时长（秒） |
| time_series | object | 时间序列数据 |
| demographics | object | 用户画像数据 |

---

## 11. 获取文章版本历史

**请求方式**: `GET /api/v1/cms/articles/{id}/versions/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/articles/123/versions/" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应字段**: 返回版本列表数组

| 字段名 | 类型 | 说明 |
|--------|------|------|
| version | integer | 版本号 |
| created_at | string | 创建时间 |
| created_by | object | 创建者信息 |
| change_summary | string | 修改摘要 |

---

## 12. 批量删除文章

**请求方式**: `POST /api/v1/cms/articles/batch-delete/`

**权限**: 租户管理员

**请求体参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| article_ids | array | 是 | 文章ID数组 |
| force | boolean | 否 | 是否强制删除（默认false） |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/articles/batch-delete/" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [123, 124, 125],
    "force": false
  }'
```

---

## 文章状态说明

| 状态 | 值 | 说明 |
|------|-----|------|
| 草稿 | draft | 未发布的草稿 |
| 待审核 | pending | 等待审核 |
| 已发布 | published | 已发布并公开可见 |
| 已归档 | archived | 已归档，不在前台显示 |

## 内容类型说明

| 类型 | 值 | 说明 |
|------|-----|------|
| Markdown | markdown | Markdown格式 |
| HTML | html | HTML格式 |
| 纯文本 | text | 纯文本格式 |

## 可见性说明

| 类型 | 值 | 说明 |
|------|-----|------|
| 公开 | public | 所有人可见 |
| 私有 | private | 仅作者和管理员可见 |
| 密码保护 | password | 需要密码访问 |
