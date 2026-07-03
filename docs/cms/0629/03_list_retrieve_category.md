# 分类列表 / 详情 API

## API 端点

```
GET /api/v1/cms/categories/                # 列表
GET /api/v1/cms/categories/{id}/           # 详情
GET /api/v1/cms/categories/tree/           # 树形结构
```

## 描述

获取分类列表、单条详情或树形结构。**本次需求仅影响响应字段，不影响请求参数和权限**。所有响应体现在都包含 `is_admin_only` 字段。

- 所有用户（含游客）可访问，前提是 `X-Tenant-ID` 正确
- 分页已禁用（`pagination_class = None`），一次性返回所有分类
- 响应中的 `is_admin_only` 字段对所有人可读

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 否 | 登录 token（不传也能查） |
| X-Tenant-ID | string | 是 | 租户 ID |

## 查询参数（列表）

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| parent | integer | 否 | 父分类 ID，用于查子分类 |
| is_active | boolean | 否 | 是否激活，true/false |
| is_pinned | boolean | 否 | 是否置顶 |
| application | integer | 否 | 关联应用 ID |
| search | string | 否 | 搜索关键词（匹配 name、slug、description） |
| ordering | string | 否 | 排序字段，如 `sort_order`、`-created_at`、`-is_pinned` |

## 路径参数（详情）

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer | 是 | 分类 ID |

## 响应

### 列表响应（200 OK）

```json
[
  {
    "id": 25,
    "slug": "announcement",
    "parent": null,
    "cover_image": "",
    "created_at": "2026-06-29T08:30:00.000000Z",
    "updated_at": "2026-06-29T08:30:00.000000Z",
    "sort_order": 0,
    "tenant": "9f8c1b2a-1234-5678-9abc-def012345678",
    "application": null,
    "application_name": null,
    "is_active": true,
    "is_pinned": false,
    "is_admin_only": true,
    "translations": {
      "zh-hans": {
        "name": "公告",
        "description": "官方公告分类",
        "seo_title": null,
        "seo_description": null,
        "master": null
      }
    },
    "name": "公告",
    "description": "官方公告分类",
    "seo_title": "",
    "seo_description": ""
  },
  {
    "id": 26,
    "slug": "user-share",
    "parent": null,
    "cover_image": "",
    "created_at": "2026-06-29T08:31:00.000000Z",
    "updated_at": "2026-06-29T08:31:00.000000Z",
    "sort_order": 1,
    "tenant": "9f8c1b2a-1234-5678-9abc-def012345678",
    "application": null,
    "application_name": null,
    "is_active": true,
    "is_pinned": false,
    "is_admin_only": false,
    "translations": {
      "zh-hans": {
        "name": "用户分享",
        "description": "所有用户都可发布",
        "seo_title": null,
        "seo_description": null,
        "master": null
      }
    },
    "name": "用户分享",
    "description": "所有用户都可发布",
    "seo_title": "",
    "seo_description": ""
  }
]
```

### 详情响应（200 OK）

```json
{
  "id": 25,
  "slug": "announcement",
  "parent": null,
  "cover_image": "",
  "created_at": "2026-06-29T08:30:00.000000Z",
  "updated_at": "2026-06-29T08:30:00.000000Z",
  "sort_order": 0,
  "tenant": "9f8c1b2a-1234-5678-9abc-def012345678",
  "application": null,
  "application_name": null,
  "is_active": true,
  "is_pinned": false,
  "is_admin_only": true,
  "translations": {
    "zh-hans": {
      "name": "公告",
      "description": "官方公告分类",
      "seo_title": null,
      "seo_description": null,
      "master": null
    }
  },
  "name": "公告",
  "description": "官方公告分类",
  "seo_title": "",
  "seo_description": ""
}
```

### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer | 分类 ID |
| slug | string | URL 别名 |
| parent | integer\|null | 父分类 ID |
| cover_image | string | 封面图片 URL |
| created_at | string | 创建时间（ISO 8601） |
| updated_at | string | 更新时间（ISO 8601） |
| sort_order | integer | 排序权重 |
| tenant | string | 租户 ID（UUID） |
| application | integer\|null | 关联应用 ID |
| application_name | string\|null | 关联应用名称 |
| is_active | boolean | 是否激活 |
| is_pinned | boolean | 是否置顶 |
| **is_admin_only** | boolean | **是否管理员专属**（本次新增）。true 表示该分类下文章仅管理员可增删改 |
| translations | object | 所有语言的翻译 |
| name | string | 当前语言名称（根据 Accept-Language 头） |
| description | string | 当前语言描述 |
| seo_title | string | 当前语言 SEO 标题 |
| seo_description | string | 当前语言 SEO 描述 |

### 失败响应

#### 缺少租户 ID（400 Bad Request）

```json
{
  "error_code": "TENANT_ID_REQUIRED",
  "detail": "未提供租户ID，无法访问CMS资源"
}
```

#### 分类不存在（404 Not Found）

```json
{
  "detail": "未找到。"
}
```

## 调用示例

### cURL — 获取分类列表（含管理员专属标记）

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -H 'Accept-Language: zh-hans'
```

**预期返回**：200 OK，数组中每个分类对象都包含 `is_admin_only` 字段

### cURL — 获取单个分类详情

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/categories/25/' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -H 'Accept-Language: zh-hans'
```

**预期返回**：200 OK，响应体含 `"is_admin_only": true`

### cURL — 获取分类树

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/categories/tree/' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
```

**预期返回**：200 OK，树结构中每个节点都包含 `is_admin_only` 字段

### cURL — 游客访问（无需 Authorization）

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/categories/?is_active=true' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
```

**预期返回**：200 OK，匿名用户只能看到 `is_active=true` 的分类，但响应仍包含 `is_admin_only` 字段

### cURL — 按 application 过滤

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/categories/?application=6' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
```

**预期返回**：200 OK，返回 application=6 下的所有分类

## 注意事项

1. **响应字段新增**：本次需求仅新增 `is_admin_only` 字段，原有字段不变
2. **观看权限不变**：所有人（含游客）都能看到 `is_admin_only=true` 的分类本身
3. **分页禁用**：分类列表不分页，一次性返回所有分类
4. **多语言**：`name`、`description` 等单语言字段根据 `Accept-Language` 请求头返回对应语言，默认 `zh-hans`
5. **树结构**：`/categories/tree/` 端点返回嵌套的树形结构，每个节点同样包含 `is_admin_only` 字段
