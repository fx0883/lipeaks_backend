# CMS分类管理API文档

## API端点列表

**基础路径**: `/api/v1/cms/categories/`

---

## 1. 获取分类列表

**请求方式**: `GET /api/v1/cms/categories/`

**权限**: 所有用户（匿名用户只能看激活的分类）

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| parent | integer | 否 | - | 父分类ID（null表示顶级分类） |
| is_active | boolean | 否 | - | 是否激活 |
| is_pinned | boolean | 否 | - | 是否置顶 |
| application | integer | 否 | - | 应用ID |
| search | string | 否 | - | 搜索关键词（名称、slug、描述） |
| ordering | string | 否 | -is_pinned,sort_order,id | 排序字段 |

**排序字段**（ordering参数可选值）:
- `sort_order` / `-sort_order` - 排序值升序/降序
- `created_at` / `-created_at` - 创建时间升序/降序
- `is_pinned` / `-is_pinned` - 置顶状态升序/降序

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/categories/?is_active=true" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应参数**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 请求是否成功 |
| code | integer | 状态码 |
| message | string | 返回消息 |
| data | array | 分类列表（无分页） |

**分类对象字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 分类ID |
| slug | string | URL别名 |
| parent | integer | 父分类ID |
| cover_image | string | 封面图片URL |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| sort_order | integer | 排序值 |
| tenant | integer | 租户ID |
| application | integer | 应用ID |
| application_name | string | 应用名称 |
| is_active | boolean | 是否激活 |
| is_pinned | boolean | 是否置顶 |
| translations | object | 多语言翻译对象 |
| name | string | 当前语言的名称 |
| description | string | 当前语言的描述 |
| seo_title | string | 当前语言的SEO标题 |
| seo_description | string | 当前语言的SEO描述 |

**translations对象结构**:
```json
{
  "zh-hans": {
    "name": "技术文章",
    "description": "技术相关的文章",
    "seo_title": "技术文章 - SEO标题",
    "seo_description": "SEO描述"
  },
  "en": {
    "name": "Tech Articles",
    "description": "Technology related articles",
    "seo_title": "Tech Articles - SEO Title",
    "seo_description": "SEO Description"
  }
}
```

---

## 2. 创建分类

**请求方式**: `POST /api/v1/cms/categories/`

**权限**: 租户管理员

**请求体参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| translations | object | 是 | - | 多语言翻译对象（至少包含一种语言） |
| slug | string | 否 | 自动生成 | URL别名（不填则自动生成） |
| parent | integer | 否 | null | 父分类ID |
| cover_image | string | 否 | - | 封面图片URL |
| sort_order | integer | 否 | 0 | 排序值（数字越小越靠前） |
| application | integer | 否 | - | 关联的应用ID |
| is_active | boolean | 否 | true | 是否激活 |
| is_pinned | boolean | 否 | false | 是否置顶 |

**translations对象参数**:

每种语言包含以下字段：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 分类名称（最大100字符） |
| description | string | 否 | 分类描述 |
| seo_title | string | 否 | SEO标题 |
| seo_description | string | 否 | SEO描述 |

**支持的语言代码**:
- `zh-hans` - 简体中文
- `en` - 英文
- `zh-hant` - 繁体中文
- `ja` - 日文
- `ko` - 韩文
- `fr` - 法文

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "translations": {
      "zh-hans": {
        "name": "技术文章",
        "description": "技术相关的文章分类",
        "seo_title": "技术文章 - 专业技术内容分享",
        "seo_description": "汇集各类技术文章和教程"
      },
      "en": {
        "name": "Tech Articles",
        "description": "Technology related articles",
        "seo_title": "Tech Articles - Professional Content",
        "seo_description": "Collection of tech articles and tutorials"
      }
    },
    "is_active": true,
    "is_pinned": false,
    "sort_order": 10
  }'
```

**响应参数**: 返回创建的分类对象

---

## 3. 创建子分类

**请求方式**: `POST /api/v1/cms/categories/`

**权限**: 租户管理员

**说明**: 通过设置parent字段创建子分类

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/categories/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": 67,
    "translations": {
      "zh-hans": {
        "name": "Python教程",
        "description": "Python编程教程"
      }
    },
    "is_active": true
  }'
```

---

## 4. 获取分类详情

**请求方式**: `GET /api/v1/cms/categories/{id}/`

**权限**: 所有用户

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 分类ID |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/categories/67/" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应参数**: 返回完整的分类对象

---

## 5. 更新分类（完整更新）

**请求方式**: `PUT /api/v1/cms/categories/{id}/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 分类ID |

**请求体参数**: 与创建分类相同，所有字段都需要提供

**请求示例**:
```bash
curl -X PUT "http://localhost:8000/api/v1/cms/categories/67/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "translations": {
      "zh-hans": {
        "name": "完整更新后的名称",
        "description": "完整更新后的描述"
      }
    },
    "is_active": true,
    "is_pinned": false,
    "sort_order": 20
  }'
```

---

## 6. 更新分类（部分更新）

**请求方式**: `PATCH /api/v1/cms/categories/{id}/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 分类ID |

**请求体参数**: 只需提供要更新的字段

**请求示例**:
```bash
# 只更新中文名称和置顶状态
curl -X PATCH "http://localhost:8000/api/v1/cms/categories/67/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "translations": {
      "zh-hans": {
        "name": "更新后的分类名"
      }
    },
    "is_pinned": true
  }'

# 只更新排序值
curl -X PATCH "http://localhost:8000/api/v1/cms/categories/67/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "sort_order": 5
  }'
```

---

## 7. 删除分类

**请求方式**: `DELETE /api/v1/cms/categories/{id}/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 分类ID |

**删除限制**:
1. 有关联文章的分类不能删除
2. 有子分类的分类不能删除

**请求示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/categories/67/" \
  -H "Authorization: Bearer <租户管理员TOKEN>"
```

**响应参数**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 是否成功 |
| code | integer | 状态码（2000表示成功） |
| message | string | 返回消息 |

**错误响应**（有关联数据时）:
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": "Cannot delete category with associated articles, please remove associated articles first"
}
```

---

## 8. 获取分类树

**请求方式**: `GET /api/v1/cms/categories/tree/`

**权限**: 所有用户

**说明**: 以树形结构获取当前租户的所有分类，自动构建父子关系

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/categories/tree/" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应参数**: 返回树形结构的分类数组

**树节点字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 分类ID |
| name | string | 分类名称（当前语言） |
| slug | string | URL别名 |
| description | string | 描述（当前语言） |
| is_active | boolean | 是否激活 |
| sort_order | integer | 排序值 |
| children | array | 子分类数组（递归结构） |

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "name": "技术博客",
      "slug": "tech-blog",
      "description": "技术相关文章",
      "is_active": true,
      "sort_order": 0,
      "children": [
        {
          "id": 2,
          "name": "Python教程",
          "slug": "python-tutorial",
          "description": "Python编程教程",
          "is_active": true,
          "sort_order": 0,
          "children": [
            {
              "id": 3,
              "name": "基础教程",
              "slug": "python-basic",
              "description": "Python基础知识",
              "is_active": true,
              "sort_order": 0,
              "children": []
            }
          ]
        },
        {
          "id": 4,
          "name": "JavaScript教程",
          "slug": "javascript-tutorial",
          "description": "JavaScript编程教程",
          "is_active": true,
          "sort_order": 1,
          "children": []
        }
      ]
    },
    {
      "id": 5,
      "name": "生活分享",
      "slug": "life-sharing",
      "description": "生活相关内容",
      "is_active": true,
      "sort_order": 1,
      "children": []
    }
  ]
}
```

---

## 注意事项

### 1. slug自动生成规则
- 创建时如果不提供slug，系统会自动从translations中的中文名称（zh-hans）生成
- 使用slugify函数处理中文（如："技术文章" -> "ji-shu-wen-zhang"）
- 如果无法从中文生成，使用时间戳确保唯一性（如："category-1732448641"）
- 可以手动指定slug，但必须确保在租户内唯一

### 2. 多语言支持
- translations对象至少需要包含一种语言
- 建议至少提供zh-hans（简体中文）
- API响应会同时返回translations对象和当前语言的单独字段
- 当前语言通过Accept-Language header确定（默认zh-hans）

### 3. 删除限制
- 删除前会检查是否有文章关联到该分类
- 删除前会检查是否有子分类
- 必须先删除所有子分类和关联文章才能删除父分类

### 4. 树形结构
- 支持无限级嵌套
- 通过parent字段建立父子关系
- tree接口会自动构建完整的层级结构
- 推荐最多使用3-4层，避免过深的嵌套

### 5. 排序规则
- 默认排序：置顶分类在前 -> 按sort_order升序 -> 按ID升序
- sort_order值越小越靠前（0在最前面）
- 置顶分类（is_pinned=true）始终显示在前面

### 6. 权限说明
- 匿名用户：只能查看is_active=true的分类
- Member用户：可以查看所有分类，但不能创建/修改/删除
- 租户管理员：可以管理本租户下的所有分类
- 超级管理员：可以管理所有租户的分类

### 7. 响应格式
API同时返回两种格式的数据：
- `translations`: 包含所有语言的翻译
- `name`、`description`等单字段：当前语言的值（方便前端使用）
