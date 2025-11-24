# CMS标签管理API文档

## 标签API

**基础路径**: `/api/v1/cms/tags/`

---

### 1. 获取标签列表

**请求方式**: `GET /api/v1/cms/tags/`

**权限**: 所有用户

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 10 | 每页数量 |
| group | integer | 否 | - | 标签组ID过滤 |
| is_active | boolean | 否 | - | 是否激活 |
| search | string | 否 | - | 搜索关键词（名称、slug、描述） |
| ordering | string | 否 | name | 排序字段 |

**排序字段**（ordering参数可选值）:
- `name` / `-name` - 名称升序/降序
- `created_at` / `-created_at` - 创建时间升序/降序

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tags/?page=1&is_active=true" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 请求是否成功 |
| data.pagination | object | 分页信息 |
| data.results | array | 标签列表 |

**标签对象字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 标签ID |
| name | string | 标签名称 |
| slug | string | URL别名 |
| description | string | 描述 |
| group | integer | 所属标签组ID |
| group_name | string | 标签组名称 |
| color | string | 颜色值（十六进制，如#FF0000） |
| is_active | boolean | 是否激活 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| tenant | integer | 租户ID |

---

### 2. 创建标签

**请求方式**: `POST /api/v1/cms/tags/`

**权限**: 租户管理员

**请求体参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| name | string | 是 | - | 标签名称（最大50字符） |
| slug | string | 否 | 自动生成 | URL别名 |
| description | string | 否 | - | 描述 |
| group | integer | 否 | - | 所属标签组ID |
| color | string | 否 | #000000 | 颜色值（十六进制格式） |
| is_active | boolean | 否 | true | 是否激活 |

**请求示例**:
```bash
# 创建独立标签
curl -X POST "http://localhost:8000/api/v1/cms/tags/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python",
    "description": "Python编程语言",
    "color": "#3776AB"
  }'

# 创建属于标签组的标签
curl -X POST "http://localhost:8000/api/v1/cms/tags/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "JavaScript",
    "description": "JS编程语言",
    "group": 9,
    "color": "#F7DF1E"
  }'
```

**响应参数**: 返回创建的标签对象

---

### 3. 获取标签详情

**请求方式**: `GET /api/v1/cms/tags/{id}/`

**权限**: 所有用户

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 标签ID |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tags/15/" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应参数**: 返回完整的标签对象

---

### 4. 更新标签

**请求方式**: `PATCH /api/v1/cms/tags/{id}/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 标签ID |

**请求体参数**: 只需提供要更新的字段

**请求示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/tags/15/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python3",
    "color": "#306998"
  }'
```

---

### 5. 删除标签

**请求方式**: `DELETE /api/v1/cms/tags/{id}/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 标签ID |

**请求示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/tags/15/" \
  -H "Authorization: Bearer <租户管理员TOKEN>"
```

**注意**: 删除前需确保没有文章使用该标签

---

## 标签组API

**基础路径**: `/api/v1/cms/tag-groups/`

---

### 1. 获取标签组列表

**请求方式**: `GET /api/v1/cms/tag-groups/`

**权限**: 所有用户

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| is_active | boolean | 否 | - | 是否激活 |
| search | string | 否 | - | 搜索关键词 |
| ordering | string | 否 | name | 排序字段 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer <TOKEN>"
```

**响应字段**:

**标签组对象字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 标签组ID |
| name | string | 标签组名称 |
| slug | string | URL别名 |
| description | string | 描述 |
| is_active | boolean | 是否激活 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| tenant | integer | 租户ID |

---

### 2. 创建标签组

**请求方式**: `POST /api/v1/cms/tag-groups/`

**权限**: 租户管理员

**请求体参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| name | string | 是 | - | 标签组名称（最大50字符） |
| slug | string | 否 | 自动生成 | URL别名 |
| description | string | 否 | - | 描述 |
| is_active | boolean | 否 | true | 是否激活 |

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/cms/tag-groups/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "编程语言",
    "description": "编程语言相关的标签"
  }'
```

**响应参数**: 返回创建的标签组对象

---

### 3. 获取标签组详情

**请求方式**: `GET /api/v1/cms/tag-groups/{id}/`

**权限**: 所有用户

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 标签组ID |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/cms/tag-groups/9/" \
  -H "Authorization: Bearer <TOKEN>"
```

---

### 4. 更新标签组

**请求方式**: `PATCH /api/v1/cms/tag-groups/{id}/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 标签组ID |

**请求体参数**: 只需提供要更新的字段

**请求示例**:
```bash
curl -X PATCH "http://localhost:8000/api/v1/cms/tag-groups/9/" \
  -H "Authorization: Bearer <租户管理员TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "编程技术",
    "description": "更新后的描述"
  }'
```

---

### 5. 删除标签组

**请求方式**: `DELETE /api/v1/cms/tag-groups/{id}/`

**权限**: 租户管理员

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 标签组ID |

**请求示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/cms/tag-groups/9/" \
  -H "Authorization: Bearer <租户管理员TOKEN>"
```

**注意**: 删除标签组不会删除该组下的标签，标签会变为无分组状态

---

## 注意事项

### 1. slug自动生成
- 创建标签和标签组时，slug字段可选
- 系统会自动从name字段生成slug
- 使用slugify函数处理中文（如："Python教程" -> "python-jiao-cheng"）
- 无法生成时使用时间戳确保唯一性

### 2. 颜色格式
- color字段使用十六进制颜色代码
- 格式：#RRGGBB（如#FF0000表示红色）
- 必须包含#号
- 推荐使用品牌色或语义化的颜色

### 3. 标签组关系
- 标签可以属于一个标签组（通过group字段）
- 一个标签只能属于一个标签组
- 标签组被删除后，标签不会被删除，只是group字段变为null
- 标签可以独立存在，不必属于任何标签组

### 4. 删除限制
- 删除标签前需确保没有文章使用该标签
- 删除标签组不会影响其下的标签
- 建议先移除文章关联再删除标签

### 5. 推荐用法
- 使用标签组进行分类管理（如：技术栈、主题类型等）
- 每个标签组下包含相关的标签（如：技术栈组包含Python、Java、Go等标签）
- 使用颜色区分不同类型的标签（如：技术标签用蓝色，主题标签用绿色）

### 6. 常见颜色值参考
| 颜色 | 十六进制值 | 说明 |
|------|-----------|------|
| 红色 | #FF0000 | 重要标签 |
| 蓝色 | #0000FF | 技术标签 |
| 绿色 | #00FF00 | 教程标签 |
| 黄色 | #FFFF00 | 热门标签 |
| 灰色 | #808080 | 普通标签 |
| Python蓝 | #3776AB | Python相关 |
| JS黄 | #F7DF1E | JavaScript相关 |
