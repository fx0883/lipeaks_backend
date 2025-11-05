# 分类管理 API

Base: `/api/v1/cms/categories/`

## 通用要求
- **Headers（必须）**：
  - `X-Tenant-ID: <tenant_id>`
  - `Authorization: Bearer <token>`（GET匿名可不带；POST/PUT/PATCH/DELETE 需要）
  - `Content-Type: application/json`
  - `Accept-Language: zh-hans|en|zh-hant|ja|ko|fr`（可选）- 指定返回内容的语言，默认为简体中文(zh-hans)
- **权限模型（`CategoryPermission` 继承 `CMSBasePermission`）**：
  - 匿名：允许GET；仍需 `X-Tenant-ID`。仅返回激活分类（匿名场景）。
  - Member：创建/更新/删除需要认证，受租户限制。
  - Admin：管理本租户全部分类；Super Admin 需通过 `X-Tenant-ID` 指定租户。

## 1. 获取分类列表 GET /

### 请求参数
- `parent` - 父分类ID（过滤）
- `is_active` - 是否激活（过滤）
- `is_pinned` - 是否置顶（过滤）
- `search` - 关键词搜索（name/slug/description）
- `ordering` - 排序字段（可选：sort_order, name, created_at, is_pinned）

### 默认排序
置顶分类优先（`-is_pinned`），然后按 `sort_order` 和 `name` 排序。

### 权限
- 匿名：允许访问，仅返回 `is_active=true` 的分类
- 已登录：按租户过滤
- Headers：`X-Tenant-ID` 必须

### 示例
```bash
# 获取所有置顶分类
curl -X GET "http://your-domain.com/api/v1/cms/categories/?is_pinned=true" \
  -H "X-Tenant-ID: 1"

# 获取特定父分类下的激活子分类
curl -X GET "http://your-domain.com/api/v1/cms/categories/?parent=1&is_active=true" \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1"
```

### 响应示例
```json
[
  {
    "id": 1,
    "name": "技术",
    "slug": "tech",
    "description": "技术相关分类",
    "parent": null,
    "cover_image": "https://example.com/tech.jpg",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-20T10:30:00Z",
    "sort_order": 0,
    "is_active": true,
    "is_pinned": true,
    "seo_title": "SEO标题",
    "seo_description": "SEO描述"
  }
]
```

## 2. 获取分类详情 GET /{id}/

### 权限
- 匿名允许（需 `X-Tenant-ID`）
- 非本租户资源将被拒绝

### 示例
```bash
curl -X GET http://your-domain.com/api/v1/cms/categories/1/ \
  -H "X-Tenant-ID: 1"
```

### 响应示例
```json
{
  "id": 1,
  "name": "技术",
  "slug": "tech",
  "description": "技术相关分类",
  "parent": null,
  "cover_image": "https://example.com/images/tech-cover.jpg",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-20T10:30:00Z",
  "sort_order": 0,
  "tenant": 1,
  "is_active": true,
  "is_pinned": true,
  "seo_title": "技术分类 - 专业技术内容",
  "seo_description": "探索最新的技术资讯和教程"
}
```

## 3. 创建分类 POST /

### 字段说明

| 字段 | 类型 | 必填 | 说明/约束 |
|---|---|---|---|
| name | string | 是 | 分类名称 |
| slug | string | 否 | URL标识，未提供则根据name自动生成 |
| description | string | 否 | 分类描述 |
| parent | integer | 否 | 父分类ID，用于层级结构 |
| cover_image | string(URL) | 否 | 封面图URL，最大长度255字符；用于分类列表和详情页展示；支持常见图片格式（jpg/png/webp等） |
| sort_order | integer | 否 | 排序值，默认0；数值越大越靠前 |
| is_active | boolean | 否 | 是否激活，默认true；未激活的分类匿名用户无法访问 |
| is_pinned | boolean | 否 | 是否置顶，默认false；置顶分类将在列表中优先展示 |
| seo_title | string | 否 | SEO标题，最大长度255字符 |
| seo_description | string | 否 | SEO描述，用于搜索引擎优化 |

### 权限
- 需要认证
- Admin/Super Admin 可在其租户内创建
- Member 需有相应权限

### 示例
```bash
curl -X POST http://your-domain.com/api/v1/cms/categories/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{
    "name":"技术博客",
    "slug":"tech-blog",
    "description":"技术相关的文章分类",
    "cover_image":"https://example.com/images/tech-blog-cover.jpg",
    "sort_order":10,
    "is_active":true,
    "is_pinned":true,
    "seo_title":"技术博客 - 分享技术知识",
    "seo_description":"最新的技术文章和教程"
  }'
```

### 响应示例
```json
{
  "id": 5,
  "name": "技术博客",
  "slug": "tech-blog",
  "description": "技术相关的文章分类",
  "parent": null,
  "cover_image": "https://example.com/images/tech-blog-cover.jpg",
  "created_at": "2024-01-20T12:00:00Z",
  "updated_at": "2024-01-20T12:00:00Z",
  "sort_order": 10,
  "tenant": 1,
  "is_active": true,
  "is_pinned": true,
  "seo_title": "技术博客 - 分享技术知识",
  "seo_description": "最新的技术文章和教程"
}
```

## 4. 更新分类 PUT /{id}/

### 权限
- 需要认证
- Admin/Super Admin 可更新本租户分类
- Member 限制更严格

### 示例
```bash
curl -X PUT http://your-domain.com/api/v1/cms/categories/1/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{
    "name":"技术教程",
    "slug":"tech-tutorial",
    "description":"更新后的描述",
    "cover_image":"https://example.com/images/new-cover.jpg",
    "is_active":true,
    "is_pinned":false
  }'
```

### 响应示例
```json
{
  "id": 1,
  "name": "技术教程",
  "slug": "tech-tutorial",
  "description": "更新后的描述",
  "parent": null,
  "cover_image": "https://example.com/images/new-cover.jpg",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-20T14:00:00Z",
  "sort_order": 0,
  "tenant": 1,
  "is_active": true,
  "is_pinned": false,
  "seo_title": null,
  "seo_description": null
}
```

## 5. 部分更新分类 PATCH /{id}/
- 权限与Headers同上。
- 示例：
```bash
# 将分类设为置顶
curl -X PATCH http://your-domain.com/api/v1/cms/categories/1/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{"is_pinned":true}'

# 更新封面图
curl -X PATCH http://your-domain.com/api/v1/cms/categories/1/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{"cover_image":"https://example.com/images/updated-cover.jpg"}'

# 取消激活状态
curl -X PATCH http://your-domain.com/api/v1/cms/categories/1/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{"is_active":false}'
```

## 6. 删除分类 DELETE /{id}/
- 约束：存在文章关联或有子分类时不可删除
- 权限：需要认证；Admin/Super Admin 可删除；删除前需确保无子分类且无文章关联。
- 示例：
```bash
curl -X DELETE http://your-domain.com/api/v1/cms/categories/1/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1"
```

## 7. 分类树 GET /tree/

### 权限
- 匿名允许（需 `X-Tenant-ID`）
- 匿名用户仅返回 `is_active=true` 节点

### 示例
```bash
curl -X GET http://your-domain.com/api/v1/cms/categories/tree/ \
  -H "X-Tenant-ID: 1"
```

### 响应示例
```json
[
  {
    "id": 1,
    "name": "技术",
    "slug": "tech",
    "description": "技术相关分类",
    "parent": null,
    "cover_image": "https://example.com/images/tech-cover.jpg",
    "sort_order": 0,
    "is_active": true,
    "is_pinned": true,
    "children": [
      {
        "id": 2,
        "name": "Python",
        "slug": "python",
        "description": "Python编程",
        "parent": 1,
        "cover_image": "https://example.com/images/python-cover.jpg",
        "sort_order": 0,
        "is_active": true,
        "is_pinned": false,
        "children": []
      }
    ]
  }
]
```

---

## 字段使用说明

### cover_image 封面图最佳实践

**字段特性**：
- 类型：`CharField`，最大长度 255 字符
- 可选字段，允许为 null 或空字符串
- 存储完整的图片 URL

**使用建议**：
1. **图片格式**：推荐使用 WebP、JPEG、PNG 等常见格式
2. **图片尺寸**：建议上传 1200x630 或 800x600 等标准尺寸
3. **CDN 加速**：建议将图片上传到 CDN 以提升加载速度
4. **响应式设计**：前端可根据不同设备加载不同尺寸的图片

**示例 URL 格式**：
```
https://cdn.example.com/images/categories/tech-cover.jpg
https://example.com/uploads/2024/01/category-5-cover.webp
```

**注意事项**：
- URL 必须是有效的 HTTP/HTTPS 链接
- 系统不会验证图片是否可访问，请确保 URL 有效
- 如需删除封面图，可传入空字符串 `""` 或 `null`

**常见错误**：
```json
{
  "cover_image": ["Ensure this field has no more than 255 characters."]
}
```

---

## 多语言支持

分类系统支持多语言内容，可以为每个分类维护多种语言版本。

### 支持的语言

- `zh-hans`: 简体中文（默认）
- `en`: 英文
- `zh-hant`: 繁体中文
- `ja`: 日语
- `ko`: 韩语
- `fr`: 法语

### 可翻译字段

以下字段支持多语言：
- `name` - 分类名称
- `description` - 分类描述
- `seo_title` - SEO标题
- `seo_description` - SEO描述

### 响应格式

API响应包含两种格式的翻译数据：

1. **translations对象** - 包含所有语言的完整翻译
2. **单语言字段** - 根据`Accept-Language`头返回对应语言的内容

**完整响应示例**：
```json
{
  "id": 1,
  "slug": "tech",
  "parent": null,
  "cover_image": "https://example.com/tech.jpg",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-20T10:30:00Z",
  "sort_order": 0,
  "tenant": 1,
  "is_active": true,
  "is_pinned": true,
  
  "translations": {
    "zh-hans": {
      "name": "技术",
      "description": "技术相关分类",
      "seo_title": "技术分类",
      "seo_description": "探索最新的技术资讯"
    },
    "en": {
      "name": "Technology",
      "description": "Technology related category",
      "seo_title": "Technology Category",
      "seo_description": "Explore the latest tech news"
    },
    "zh-hant": {
      "name": "技術",
      "description": "技術相關分類",
      "seo_title": "技術分類",
      "seo_description": "探索最新的技術資訊"
    },
    "ja": {
      "name": "テクノロジー",
      "description": "テクノロジー関連のカテゴリー",
      "seo_title": "テクノロジーカテゴリー",
      "seo_description": "最新のテクノロジー情報を探す"
    }
  },
  
  "name": "Technology",
  "description": "Technology related category",
  "seo_title": "Technology Category",
  "seo_description": "Explore the latest tech news"
}
```

### 使用场景

#### 场景1：获取英文内容

```bash
curl -X GET "http://your-domain.com/api/v1/cms/categories/1/" \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: en"
```

响应中的`name`、`description`等字段将返回英文内容，`translations`对象包含所有语言。

#### 场景2：创建多语言分类

```bash
curl -X POST http://your-domain.com/api/v1/cms/categories/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "tech-news",
    "translations": {
      "zh-hans": {
        "name": "技术新闻",
        "description": "最新的技术新闻和资讯",
        "seo_title": "技术新闻 - 最新科技资讯",
        "seo_description": "获取最新的技术新闻和行业动态"
      },
      "en": {
        "name": "Tech News",
        "description": "Latest technology news and updates",
        "seo_title": "Tech News - Latest Technology Updates",
        "seo_description": "Get the latest tech news and industry trends"
      },
      "zh-hant": {
        "name": "技術新聞",
        "description": "最新的技術新聞和資訊",
        "seo_title": "技術新聞 - 最新科技資訊",
        "seo_description": "獲取最新的技術新聞和行業動態"
      },
      "ja": {
        "name": "テクノロジーニュース",
        "description": "最新のテクノロジーニュースと情報",
        "seo_title": "テクノロジーニュース - 最新技術情報",
        "seo_description": "最新のテクノロジーニュースと業界動向を入手"
      }
    },
    "is_active": true
  }'
```

#### 场景3：更新特定语言的翻译

```bash
curl -X PATCH http://your-domain.com/api/v1/cms/categories/1/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "translations": {
      "en": {
        "name": "Updated Tech News",
        "description": "Updated description in English"
      }
    }
  }'
```

### 语言回退机制

如果请求的语言没有翻译内容，系统会自动回退到默认语言（简体中文）：

```bash
# 请求法语内容（不存在）
curl -X GET "http://your-domain.com/api/v1/cms/categories/1/" \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: fr"

# 响应会返回简体中文内容（回退语言）
{
  "name": "技术",
  "description": "技术相关分类",
  ...
}
```

### 最佳实践

1. **创建分类时至少提供默认语言（简体中文）的翻译**
2. **使用`Accept-Language`头请求特定语言的内容**
3. **`translations`对象用于管理后台显示所有语言**
4. **单语言字段用于前端展示特定语言内容**
5. **slug字段不参与翻译，保持全局唯一**
