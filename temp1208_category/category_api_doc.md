# Category 分类 API 文档

## 概述

分类 API 提供文章分类的增删改查功能，**支持多语言（i18n）**。

### 多语言支持

- **支持的语言**: `zh-hans`(简体中文)、`en`(英语)、`zh-hant`(繁体中文)、`ja`(日语)、`ko`(韩语)、`fr`(法语)
- **可翻译字段**: `name`(分类名称)、`description`(描述)、`seo_title`、`seo_description`
- **非翻译字段**: `slug`、`parent`、`cover_image`、`sort_order`、`is_active`、`is_pinned`、`application`

### 请求头

| Header | 描述 | 必须 |
|--------|------|------|
| `X-Tenant-ID` | 租户ID | **是** |
| `Accept-Language` | 指定返回的语言（影响 `name`、`description` 等单语言字段） | 否（默认 `zh-hans`） |
| `Authorization` | Bearer Token（创建/更新/删除需要） | 写操作需要 |

### 基础URL

```
http://127.0.0.1:8000/api/v1/cms/categories/
```

---

## 1. 获取分类列表

获取所有分类，支持过滤和搜索。

### 请求

```
GET /api/v1/cms/categories/
```

### 查询参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `parent` | int | 父分类ID（过滤子分类） |
| `is_active` | bool | 是否激活 |
| `is_pinned` | bool | 是否置顶 |
| `application` | int | 关联应用ID |
| `search` | string | 搜索关键词（搜索 name、slug、description） |
| `ordering` | string | 排序字段：`sort_order`、`created_at`、`is_pinned` |

### curl 示例

```bash
# 获取租户1的所有分类
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/" \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: zh-hans"

# 只获取激活的分类
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/?is_active=true" \
  -H "X-Tenant-ID: 1"

# 搜索分类
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/?search=Tutorial" \
  -H "X-Tenant-ID: 1"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": [
        {
            "id": 5,
            "slug": "how-to-841",
            "parent": null,
            "cover_image": "",
            "created_at": "2025-10-09T10:14:15.921164Z",
            "updated_at": "2025-12-05T04:48:21.156017Z",
            "sort_order": 0,
            "tenant": 1,
            "application": null,
            "application_name": null,
            "is_active": true,
            "is_pinned": false,
            "translations": {
                "zh-hans": {
                    "name": "How To",
                    "description": "How To",
                    "seo_title": null,
                    "seo_description": null
                },
                "en": {
                    "name": "How To",
                    "description": "",
                    "seo_title": "",
                    "seo_description": ""
                },
                "zh-hant": {
                    "name": "How To",
                    "description": "",
                    "seo_title": "",
                    "seo_description": ""
                },
                "ja": {
                    "name": "How To",
                    "description": "",
                    "seo_title": "",
                    "seo_description": ""
                },
                "ko": {
                    "name": "How To",
                    "description": "",
                    "seo_title": "",
                    "seo_description": ""
                },
                "fr": {
                    "name": "How To",
                    "description": "",
                    "seo_title": "",
                    "seo_description": ""
                }
            },
            "name": "How To",
            "description": "How To",
            "seo_title": "",
            "seo_description": ""
        }
    ]
}
```

### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `id` | int | 分类ID |
| `slug` | string | URL别名（唯一） |
| `parent` | int/null | 父分类ID |
| `cover_image` | string | 封面图片URL |
| `sort_order` | int | 排序值 |
| `tenant` | int | 租户ID |
| `application` | int/null | 关联应用ID |
| `application_name` | string/null | 关联应用名称 |
| `is_active` | bool | 是否激活 |
| `is_pinned` | bool | 是否置顶 |
| `translations` | object | **多语言翻译对象**，包含所有语言的翻译 |
| `name` | string | **当前语言**的分类名称（根据 Accept-Language） |
| `description` | string | **当前语言**的描述 |
| `seo_title` | string | **当前语言**的SEO标题 |
| `seo_description` | string | **当前语言**的SEO描述 |

---

## 2. 获取分类详情

### 请求

```
GET /api/v1/cms/categories/{id}/
```

### curl 示例

```bash
# 获取分类ID=5的详情（中文）
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/5/" \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: zh-hans"

# 获取分类ID=5的详情（英文）
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/5/" \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: en"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 5,
        "slug": "how-to-841",
        "parent": null,
        "cover_image": "",
        "created_at": "2025-10-09T10:14:15.921164Z",
        "updated_at": "2025-12-05T04:48:21.156017Z",
        "sort_order": 0,
        "tenant": 1,
        "application": null,
        "application_name": null,
        "is_active": true,
        "is_pinned": false,
        "translations": {
            "zh-hans": {
                "name": "How To",
                "description": "How To",
                "seo_title": null,
                "seo_description": null
            },
            "en": {
                "name": "How To EN",
                "description": "How To Articles",
                "seo_title": "",
                "seo_description": ""
            }
        },
        "name": "How To",
        "description": "How To",
        "seo_title": "",
        "seo_description": ""
    }
}
```

---

## 3. 获取分类树

以树形结构返回所有分类（包含子分类）。

### 请求

```
GET /api/v1/cms/categories/tree/
```

### curl 示例

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/tree/" \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: zh-hans"
```

### 响应示例

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": [
        {
            "id": 5,
            "name": "How To",
            "slug": "how-to-841",
            "description": "How To",
            "is_active": true,
            "sort_order": 0,
            "children": []
        },
        {
            "id": 6,
            "name": "Review",
            "slug": "review-064",
            "description": "Review 064分类",
            "is_active": true,
            "sort_order": 0,
            "children": []
        },
        {
            "id": 7,
            "name": "Tutorial",
            "slug": "tutorial-565",
            "description": "Tutorial",
            "is_active": true,
            "sort_order": 0,
            "children": []
        }
    ]
}
```

### 树节点字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `id` | int | 分类ID |
| `name` | string | 分类名称（当前语言） |
| `slug` | string | URL别名 |
| `description` | string | 描述 |
| `is_active` | bool | 是否激活 |
| `sort_order` | int | 排序值 |
| `children` | array | 子分类列表（递归结构） |

---

## 4. 创建分类

创建新分类，**需要认证**。

### 请求

```
POST /api/v1/cms/categories/
Content-Type: application/json
```

### 请求体

```json
{
    "slug": "tech-blog",
    "parent": null,
    "cover_image": "https://example.com/images/tech.jpg",
    "is_active": true,
    "is_pinned": false,
    "sort_order": 0,
    "application": null,
    "translations": {
        "zh-hans": {
            "name": "技术博客",
            "description": "技术相关的文章分类",
            "seo_title": "技术博客 - 分享技术知识",
            "seo_description": "分享最新的技术知识和教程"
        },
        "en": {
            "name": "Tech Blog",
            "description": "Technology related articles",
            "seo_title": "Tech Blog - Share Tech Knowledge",
            "seo_description": "Share latest tech knowledge and tutorials"
        }
    }
}
```

### 请求字段说明

| 字段 | 类型 | 必须 | 描述 |
|------|------|------|------|
| `slug` | string | 否 | URL别名（不填则自动生成） |
| `parent` | int/null | 否 | 父分类ID |
| `cover_image` | string | 否 | 封面图片URL |
| `is_active` | bool | 否 | 是否激活（默认true） |
| `is_pinned` | bool | 否 | 是否置顶（默认false） |
| `sort_order` | int | 否 | 排序值（默认0） |
| `application` | int/null | 否 | 关联应用ID |
| `translations` | object | **是** | 多语言翻译对象 |
| `translations.{lang}.name` | string | **是** | 分类名称 |
| `translations.{lang}.description` | string | 否 | 分类描述 |
| `translations.{lang}.seo_title` | string | 否 | SEO标题 |
| `translations.{lang}.seo_description` | string | 否 | SEO描述 |

### curl 示例

```bash
# 需要先获取认证Token
TOKEN="your_jwt_token_here"

curl -X POST "http://127.0.0.1:8000/api/v1/cms/categories/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "tech-blog",
    "is_active": true,
    "is_pinned": false,
    "sort_order": 0,
    "translations": {
        "zh-hans": {
            "name": "技术博客",
            "description": "技术相关的文章分类"
        },
        "en": {
            "name": "Tech Blog",
            "description": "Technology related articles"
        }
    }
}'
```

### 响应示例（201 Created）

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "id": 100,
        "slug": "tech-blog",
        "parent": null,
        "cover_image": "",
        "created_at": "2025-12-08T10:00:00.000000Z",
        "updated_at": "2025-12-08T10:00:00.000000Z",
        "sort_order": 0,
        "tenant": 1,
        "application": null,
        "application_name": null,
        "is_active": true,
        "is_pinned": false,
        "translations": {
            "zh-hans": {
                "name": "技术博客",
                "description": "技术相关的文章分类",
                "seo_title": null,
                "seo_description": null
            },
            "en": {
                "name": "Tech Blog",
                "description": "Technology related articles",
                "seo_title": null,
                "seo_description": null
            }
        },
        "name": "技术博客",
        "description": "技术相关的文章分类",
        "seo_title": "",
        "seo_description": ""
    }
}
```

---

## 5. 更新分类

更新现有分类，**需要认证**。

### 请求

```
PUT /api/v1/cms/categories/{id}/
Content-Type: application/json
```

### curl 示例

```bash
TOKEN="your_jwt_token_here"

# 完整更新
curl -X PUT "http://127.0.0.1:8000/api/v1/cms/categories/5/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "how-to-updated",
    "is_active": true,
    "is_pinned": true,
    "sort_order": 1,
    "translations": {
        "zh-hans": {
            "name": "使用指南",
            "description": "如何使用的教程"
        },
        "en": {
            "name": "How To Guide",
            "description": "How to use tutorials"
        }
    }
}'
```

---

## 6. 部分更新分类

部分更新分类字段，**需要认证**。

### 请求

```
PATCH /api/v1/cms/categories/{id}/
Content-Type: application/json
```

### curl 示例

```bash
TOKEN="your_jwt_token_here"

# 只更新部分翻译
curl -X PATCH "http://127.0.0.1:8000/api/v1/cms/categories/5/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "translations": {
        "ja": {
            "name": "ハウツー",
            "description": "使い方ガイド"
        }
    }
}'

# 只更新置顶状态
curl -X PATCH "http://127.0.0.1:8000/api/v1/cms/categories/5/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_pinned": true
}'
```

---

## 7. 删除分类

删除分类，**需要认证**。

### 注意事项

- 如果分类有关联文章，无法删除（需先移除关联）
- 如果分类有子分类，无法删除（需先删除子分类）

### 请求

```
DELETE /api/v1/cms/categories/{id}/
```

### curl 示例

```bash
TOKEN="your_jwt_token_here"

curl -X DELETE "http://127.0.0.1:8000/api/v1/cms/categories/100/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN"
```

### 响应

- **204 No Content**: 删除成功
- **400 Bad Request**: 有关联文章或子分类，无法删除

```json
{
    "success": false,
    "code": 4000,
    "message": "Cannot delete category with associated articles, please remove associated articles first",
    "data": null
}
```

---

## 权限说明

| 操作 | 匿名用户 | 普通用户 | 租户管理员 | 超级管理员 |
|------|---------|----------|-----------|-----------|
| 列表/详情/树 | ✅（只读激活分类） | ✅（只读） | ✅ | ✅ |
| 创建 | ❌ | ❌ | ✅ | ✅ |
| 更新 | ❌ | ❌ | ✅ | ✅ |
| 删除 | ❌ | ❌ | ✅ | ✅ |

---

## 错误码

| HTTP状态码 | 错误描述 |
|-----------|---------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 分类不存在 |

---

## 多语言使用示例

### 前端读取多语言数据

```javascript
// 获取分类列表
const response = await fetch('/api/v1/cms/categories/', {
    headers: {
        'X-Tenant-ID': '1',
        'Accept-Language': 'zh-hans'  // 指定语言
    }
});
const data = await response.json();

// 使用 translations 对象获取所有语言
const category = data.data[0];
console.log(category.translations['zh-hans'].name);  // 中文名
console.log(category.translations['en'].name);       // 英文名

// 使用顶层字段获取当前语言（由 Accept-Language 决定）
console.log(category.name);  // 当前语言的名称
```

### 创建多语言分类

```javascript
const newCategory = {
    slug: 'my-category',
    is_active: true,
    translations: {
        'zh-hans': {
            name: '我的分类',
            description: '这是中文描述'
        },
        'en': {
            name: 'My Category',
            description: 'This is English description'
        },
        'ja': {
            name: 'マイカテゴリ',
            description: 'これは日本語の説明です'
        }
    }
};

const response = await fetch('/api/v1/cms/categories/', {
    method: 'POST',
    headers: {
        'X-Tenant-ID': '1',
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(newCategory)
});
```
