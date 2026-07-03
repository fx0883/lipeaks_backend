# 更新分类 API

## API 端点

```
PATCH /api/v1/cms/categories/{id}/
PUT /api/v1/cms/categories/{id}/
```

## 描述

更新分类信息。支持部分更新（PATCH）和全量更新（PUT）。本次需求支持修改 `is_admin_only` 字段，用于动态开启/关闭"管理员专属"标记。

- 管理员可修改 `is_admin_only` 字段
- Member 不能修改 `is_admin_only` 字段（任何值都不行，包括 false→true）
- 取消 `is_admin_only` 标记后，Member 立即恢复对相关文章的操作权限

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | `Bearer <token>`，管理员 token |
| Content-Type | string | 是 | `application/json` |
| X-Tenant-ID | string | 是 | 租户 ID |

## 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer | 是 | 分类 ID |

## 请求体

### 部分更新（PATCH）— 仅修改 `is_admin_only`

```json
{
  "is_admin_only": true
}
```

### 全量更新（PUT）

```json
{
  "translations": {
    "zh-hans": {
      "name": "公告",
      "description": "更新后的描述"
    }
  },
  "slug": "announcement",
  "parent": null,
  "sort_order": 0,
  "is_active": true,
  "is_pinned": false,
  "is_admin_only": true
}
```

### 参数说明

| 参数名 | 类型 | 必填(PUT) | 必填(PATCH) | 描述 |
|--------|------|----------|------------|------|
| translations | object | 是 | 否 | 多语言翻译对象 |
| slug | string | 是 | 否 | URL 别名 |
| parent | integer | 是 | 否 | 父分类 ID |
| cover_image | string | 否 | 否 | 封面图片 URL |
| sort_order | integer | 是 | 否 | 排序权重 |
| application | integer | 否 | 否 | 关联应用 ID |
| is_active | boolean | 是 | 否 | 是否激活 |
| is_pinned | boolean | 是 | 否 | 是否置顶 |
| **is_admin_only** | boolean | 是 | 否 | **是否管理员专属**。仅管理员可修改此字段 |

## 响应

### 成功响应（200 OK）

```json
{
  "id": 25,
  "slug": "announcement",
  "parent": null,
  "cover_image": "",
  "created_at": "2026-06-29T08:30:00.000000Z",
  "updated_at": "2026-06-29T08:35:00.000000Z",
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
      "description": "更新后的描述",
      "seo_title": null,
      "seo_description": null,
      "master": null
    }
  },
  "name": "公告",
  "description": "更新后的描述",
  "seo_title": "",
  "seo_description": ""
}
```

### 失败响应

#### Member 修改分类（含 `is_admin_only` 字段）（403 Forbidden）

```json
{
  "detail": "只有管理员可以创建管理员专属分类"
}
```

> 注：校验逻辑同时拦截 Member 创建和修改两种场景，错误消息统一为"创建管理员专属分类"。

#### 分类不存在（404 Not Found）

```json
{
  "detail": "未找到。"
}
```

## 调用示例

### cURL — 管理员开启管理员专属标记

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/categories/25/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "is_admin_only": true
  }'
```

**预期返回**：200 OK，响应体含 `"is_admin_only": true`

### cURL — 管理员关闭管理员专属标记（恢复 Member 权限）

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/categories/25/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "is_admin_only": false
  }'
```

**预期返回**：200 OK，响应体含 `"is_admin_only": false`

**效果**：该分类下已有的 Member 文章，Member 立即恢复编辑/删除/发布权限

### cURL — Member 尝试修改 is_admin_only（应被拒绝）

```bash
curl -X PATCH 'http://localhost:8000/api/v1/cms/categories/25/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678' \
  -d '{
    "is_admin_only": false
  }'
```

**预期返回**：403 Forbidden
```json
{
  "detail": "只有管理员可以创建管理员专属分类"
}
```

## 注意事项

1. **配置即时生效**：修改 `is_admin_only` 后，相关文章的权限立即变化，无需重启服务
2. **取消标记的影响**：从 true 改为 false 后，该分类下原本被锁定的 Member 文章，Member 立即可以编辑/删除
3. **Member 限制范围**：Member 不能修改 `is_admin_only` 的值（无论 true→false 还是 false→true）
4. **超级管理员**：需通过 `X-Tenant-ID` 请求头指定租户 ID
