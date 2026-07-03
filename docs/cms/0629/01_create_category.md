# 创建分类 API

## API 端点

```
POST /api/v1/cms/categories/
```

## 描述

创建一个新的分类。支持多语言（通过 `translations` 字段）。本次需求新增 `is_admin_only` 字段，用于标记"管理员专属分类"。

- 管理员（User 类型）可创建任意分类，包括 `is_admin_only=True`
- Member 不能创建 `is_admin_only=True` 的分类，会返回 403

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | `Bearer <token>`，管理员 token |
| Content-Type | string | 是 | `application/json` |
| X-Tenant-ID | string | 是 | 租户 ID（UUID） |

## 请求体

```json
{
  "translations": {
    "zh-hans": {
      "name": "公告",
      "description": "官方公告分类，仅管理员可发布"
    },
    "en": {
      "name": "Announcement",
      "description": "Official announcements, admin only"
    }
  },
  "slug": "announcement",
  "parent": null,
  "cover_image": "",
  "sort_order": 0,
  "application": null,
  "is_active": true,
  "is_pinned": false,
  "is_admin_only": true
}
```

### 参数说明

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| translations | object | 是 | 多语言翻译对象，key 为语言代码（如 `zh-hans`、`en`） |
| translations.\<lang\>.name | string | 是 | 分类名称 |
| translations.\<lang\>.description | string | 否 | 分类描述 |
| translations.\<lang\>.seo_title | string | 否 | SEO 标题 |
| translations.\<lang\>.seo_description | string | 否 | SEO 描述 |
| slug | string | 否 | URL 别名，不传则根据 name 自动生成 |
| parent | integer | 否 | 父分类 ID，null 表示根分类 |
| cover_image | string | 否 | 封面图片 URL |
| sort_order | integer | 否 | 排序权重，默认 0，数字越小越靠前 |
| application | integer | 否 | 关联应用 ID，null 表示全局分类 |
| is_active | boolean | 否 | 是否激活，默认 true |
| is_pinned | boolean | 否 | 是否置顶，默认 false |
| **is_admin_only** | boolean | 否 | **是否管理员专属**，默认 false。true 时该分类下文章仅管理员可增删改，Member 不可操作。**仅管理员可设置为 true** |

## 响应

### 成功响应（201 Created）

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
      "description": "官方公告分类，仅管理员可发布",
      "seo_title": null,
      "seo_description": null,
      "master": null
    },
    "en": {
      "name": "Announcement",
      "description": "Official announcements, admin only",
      "seo_title": null,
      "seo_description": null,
      "master": null
    }
  },
  "name": "公告",
  "description": "官方公告分类，仅管理员可发布",
  "seo_title": "",
  "seo_description": ""
}
```

### 失败响应

#### Member 创建管理员专属分类（403 Forbidden）

```json
{
  "detail": "只有管理员可以创建管理员专属分类"
}
```

#### 未认证（401 Unauthorized）

```json
{
  "detail": "身份认证信息未提供。"
}
```

#### 缺少租户 ID（400 Bad Request）

```json
{
  "error_code": "TENANT_ID_REQUIRED",
  "detail": "未提供租户ID，无法访问CMS资源"
}
```

## 调用示例

### cURL — 管理员创建管理员专属分类

```bash
curl -X POST 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsInVzZXJuYW1lIjoiYWRtaW4ifQ.xxx.yyy' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "translations": {
      "zh-hans": {
        "name": "公告",
        "description": "官方公告分类，仅管理员可发布"
      }
    },
    "is_admin_only": true,
    "is_active": true,
    "sort_order": 0
  }'
```

**预期返回**：201 Created，响应体含 `"is_admin_only": true`

### cURL — Member 尝试创建管理员专属分类（应被拒绝）

```bash
curl -X POST 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtZW1iZXJfaWQiOjQ1NiwidXNlcm5hbWUiOiJtZW1iZXIxIn0.xxx.yyy' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "translations": {
      "zh-hans": {
        "name": "被拒绝的分类"
      }
    },
    "is_admin_only": true
  }'
```

**预期返回**：403 Forbidden
```json
{
  "detail": "只有管理员可以创建管理员专属分类"
}
```

### cURL — 管理员创建普通分类（is_admin_only=false）

```bash
curl -X POST 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "translations": {
      "zh-hans": {
        "name": "用户分享",
        "description": "所有用户都可发布"
      }
    },
    "is_admin_only": false,
    "is_active": true
  }'
```

**预期返回**：201 Created，响应体含 `"is_admin_only": false`

## 注意事项

1. **多语言必填**：`translations` 至少要提供一种语言的 `name`
2. **slug 自动生成**：若不传 `slug`，系统根据 `zh-hans` 的 `name` 自动生成；若名称为空则用时间戳
3. **`is_admin_only` 不影响观看**：所有用户（含游客）都能看到管理员专属分类本身和其下的公开文章
4. **配置立即生效**：标记为 `is_admin_only=True` 后，该分类下已有的 Member 文章，Member 也不能再编辑/删除
5. **不继承**：父分类标记为管理员专属，子分类不会自动继承，需单独标记
