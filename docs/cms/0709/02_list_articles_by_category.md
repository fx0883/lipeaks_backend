# 获取分类下所有文章 API

> 模块：CMS
> 创建日期：2026-07-09

## 功能概述

获取指定分类下的文章列表，支持分页、排序和过滤。

- **无需登录 token**，游客可调用
- 必须通过 `X-Tenant-ID` 请求头指定租户
- 通过 `?category_id=` 指定分类

## API 端点

```
GET /api/v1/cms/articles/?category_id=<分类ID>
```

## 请求头

| 名称 | 必填 | 说明 |
|------|------|------|
| X-Tenant-ID | 是 | 租户 ID（数字，如 `3`） |
| Authorization | 否 | 登录 token；不传即以游客身份访问 |
| Accept-Language | 否 | 语言，默认 `zh-hans` |

## 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category_id | int | 是 | 分类 ID，按该分类过滤文章 |
| page | int | 否 | 页码，默认 `1` |
| page_size | int | 否 | 每页条数，默认 `10` |
| status | string | 否 | 文章状态：`draft`/`pending`/`published`/`archived`；前台推荐传 `published` |
| search | string | 否 | 搜索关键词（匹配标题、内容、摘要） |
| sort | string | 否 | 排序字段：`created_at`/`updated_at`/`published_at`/`title`/`views_count` |
| sort_direction | string | 否 | 排序方向：`asc`/`desc`（默认 `desc`） |
| date_from | string | 否 | 发布日期起始，格式 `YYYY-MM-DD` |
| date_to | string | 否 | 发布日期截止，格式 `YYYY-MM-DD` |
| is_featured | bool | 否 | 是否特色文章 |
| is_pinned | bool | 否 | 是否置顶 |
| visibility | string | 否 | 可见性：`public`/`private`/`password` |
| author_type | string | 否 | 作者类型：`member`/`admin` |

> 空字符串参数（如 `search=`、`date_from=`）会被当作未传处理，不会报错。

## 响应

### 200 OK

返回标准响应包裹，`data` 含分页信息与 `results` 数组：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 128,
      "next": "http://localhost:8000/api/v1/cms/articles/?category_id=25&page=2&page_size=10",
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 13
    },
    "results": [
      {
        "id": 10340,
        "title": "test1",
        "slug": "test1-952",
        "excerpt": "excerpt123",
        "author_info": { "id": 6, "username": "admin_com" },
        "author_type": "admin",
        "status": "draft",
        "is_featured": false,
        "is_pinned": false,
        "is_locked": false,
        "cover_image": "http://localhost:8000/media/uploads/20/article_covers/example.png",
        "cover_image_small": "http://localhost:8000/media/uploads/20/article_covers/example_thumb_small.jpg",
        "published_at": null,
        "created_at": "2026-07-04T13:51:00.000000Z",
        "updated_at": "2026-07-04T13:51:00.000000Z",
        "categories": [
          { "id": 25, "name": "公告", "slug": "announcement" }
        ],
        "tags": [],
        "comments_count": 0,
        "likes_count": 0,
        "views_count": 0,
        "parent": null,
        "parent_info": null,
        "children_count": 0
      }
    ]
  }
}
```

### 分页字段说明（data.pagination）

| 字段 | 类型 | 说明 |
|------|------|------|
| count | int | 总条数 |
| next | string\|null | 下一页 URL |
| previous | string\|null | 上一页 URL |
| page_size | int | 每页条数 |
| current_page | int | 当前页码 |
| total_pages | int | 总页数 |

### 文章字段说明（data.results[]）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 文章 ID |
| title | string | 标题 |
| slug | string | URL 别名 |
| excerpt | string | 摘要 |
| author_info | object\|null | 作者信息（User 或 Member） |
| author_type | string\|null | 作者类型：`member`/`admin` |
| status | string | 状态：`draft`/`pending`/`published`/`archived` |
| is_featured | bool | 是否特色 |
| is_pinned | bool | 是否置顶 |
| is_locked | bool | 是否锁定 |
| cover_image | string | 封面图完整 URL |
| cover_image_small | string | 封面小图完整 URL |
| published_at | string\|null | 发布时间 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| categories | array | 关联分类，`[{id, name, slug}]` |
| tags | array | 关联标签，`[{id, name, slug, color}]` |
| comments_count | int | 评论数 |
| likes_count | int | 点赞数 |
| views_count | int | 浏览数 |
| parent | int\|null | 父文章 ID |
| parent_info | object\|null | 父文章信息 `{id, title, slug}` |
| children_count | int | 子文章数量 |

### 400 Bad Request（缺少 X-Tenant-ID）

```json
{
  "success": false,
  "code": 4001,
  "message": "未提供租户ID，无法访问CMS资源",
  "data": null
}
```

## 调用示例

> 以下示例假设后端服务运行在 `http://localhost:8000`，租户 ID 为 `3`，分类 ID 为 `25`，请替换为实际值。

### cURL - 获取分类 25 下的已发布文章（游客）

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/articles/?category_id=25&status=published&page=1&page_size=10' \
  -H 'X-Tenant-ID: 3' \
  -H 'Accept-Language: zh-hans'
```

### cURL - 按浏览量降序获取前 20 篇

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/articles/?category_id=25&sort=views_count&sort_direction=desc&page_size=20' \
  -H 'X-Tenant-ID: 3'
```

### cURL + jq - 只取标题和 ID

```bash
curl -s -X GET 'http://localhost:8000/api/v1/cms/articles/?category_id=25&status=published&page_size=10' \
  -H 'X-Tenant-ID: 3' \
| jq '.data.results[] | {id, title}'
```

## 注意事项

1. **无需 token**：不传 `Authorization` 即以游客身份访问。
2. **必须带 X-Tenant-ID**：否则返回 400（`code: 4001`）。
3. **前台推荐 `status=published`**：列表接口本身不过滤状态，不传 `status` 时该分类下所有状态的文章都会返回；前台展示建议显式传 `status=published`。访问单篇详情时，非 `published`/非 `public` 的文章对游客会返回 403。
4. **分页**：默认 `page=1`、`page_size=10`。
5. **分类下无文章**：返回 `count: 0`、`results: []`，仍为 200。
6. **空字符串参数**：`search=`、`date_from=` 等空值会被忽略，不触发报错。
