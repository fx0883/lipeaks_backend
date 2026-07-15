# 获取管理员专属分类（is_admin_only=true）API

> 模块：CMS
> 创建日期：2026-07-09
> 关联：[分类级管理员专属控制](../category_admin_only_requirement.md)

## 功能概述

获取指定租户下标记为"管理员专属"（`is_admin_only=true`）的分类列表。

- **无需登录 token**，任何客户端（含游客）可调用
- 必须通过 `X-Tenant-ID` 请求头指定租户
- 支持 `?is_admin_only=true` **服务端过滤**，直接返回管理员专属分类

## API 端点

```
GET /api/v1/cms/categories/?is_admin_only=true
```

## 请求头

| 名称 | 必填 | 说明 |
|------|------|------|
| X-Tenant-ID | 是 | 租户 ID（数字，如 `3`） |
| Authorization | 否 | 登录 token；不传即以游客身份访问 |
| Accept-Language | 否 | 语言，默认 `zh-hans` |

## 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| is_admin_only | bool | 是否管理员专属；传 `true` 只返回管理员专属分类，`false` 只返回普通分类，不传则返回全部 |
| is_active | bool | 是否激活；游客访问建议传 `true`（游客仅能看到 `is_active=true` 的分类） |
| parent | int | 父分类 ID，用于查子分类 |
| is_pinned | bool | 是否置顶 |
| application | int | 关联应用 ID |
| search | string | 搜索关键词（匹配 name / slug / description） |
| ordering | string | 排序字段，如 `-is_pinned`、`sort_order` |

## 响应

### 200 OK

返回标准响应包裹，`data` 为分类数组（分页已禁用，一次性返回全部）：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 25,
      "slug": "announcement",
      "parent": null,
      "cover_image": "",
      "created_at": "2026-06-29T08:30:00.000000Z",
      "updated_at": "2026-06-29T08:30:00.000000Z",
      "sort_order": 0,
      "tenant": 3,
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
          "seo_description": null
        }
      },
      "name": "公告",
      "description": "官方公告分类",
      "seo_title": "",
      "seo_description": ""
    }
  ]
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 分类 ID |
| slug | string | URL 别名 |
| parent | int\|null | 父分类 ID |
| cover_image | string | 封面图 URL |
| created_at | string | 创建时间（ISO 8601） |
| updated_at | string | 更新时间（ISO 8601） |
| sort_order | int | 排序权重 |
| tenant | int | 租户 ID |
| application | int\|null | 关联应用 ID |
| application_name | string\|null | 关联应用名称 |
| is_active | bool | 是否激活 |
| is_pinned | bool | 是否置顶 |
| **is_admin_only** | bool | **是否管理员专属**；`true` 表示该分类下文章仅管理员可增删改，Member 不可操作 |
| translations | object | 全语言翻译 |
| name | string | 当前语言名称（随 `Accept-Language`） |
| description | string | 当前语言描述 |
| seo_title | string | SEO 标题 |
| seo_description | string | SEO 描述 |

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

> 以下示例假设后端服务运行在 `http://localhost:8000`，租户 ID 为 `3`，请替换为实际值。

### cURL - 服务端过滤 is_admin_only=true（推荐）

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/categories/?is_admin_only=true&is_active=true' \
  -H 'X-Tenant-ID: 3' \
  -H 'Accept-Language: zh-hans'
```

直接返回该租户下所有管理员专属分类（`data` 中每项的 `is_admin_only` 均为 `true`）。

### cURL - 获取全部分类（不过滤）

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/categories/?is_active=true' \
  -H 'X-Tenant-ID: 3'
```

### cURL + jq - 仅取 ID 和名称

```bash
curl -s -X GET 'http://localhost:8000/api/v1/cms/categories/?is_admin_only=true' \
  -H 'X-Tenant-ID: 3' \
  -H 'Accept-Language: zh-hans' \
| jq '.data[] | {id, name}'
```

### JavaScript（前端）示例

```js
const res = await fetch('/api/v1/cms/categories/?is_admin_only=true&is_active=true', {
  headers: { 'X-Tenant-ID': '3' }
});
const { data } = await res.json();
// data 即为管理员专属分类数组
```

## 注意事项

1. **无需 token**：不传 `Authorization` 即以游客身份访问。
2. **必须带 X-Tenant-ID**：否则返回 400（`code: 4001`）。
3. **服务端过滤**：支持 `?is_admin_only=true` 直接过滤，无需客户端筛选。
4. **游客可见性**：游客只能看到 `is_active=true` 的分类；管理员专属分类本身对游客可见（仅该分类下文章的写操作对 Member 受限）。
5. **分页禁用**：分类列表不分页，一次返回全部。
6. **多语言**：`name`/`description` 等字段随 `Accept-Language` 请求头返回对应语言，默认 `zh-hans`。
