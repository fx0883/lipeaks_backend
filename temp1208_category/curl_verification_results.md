# Category API Curl 验证结果

验证时间: 2025-12-08
租户ID: 1
服务器: http://127.0.0.1:8000

---

## 1. 获取分类列表 ✅

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/" \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: zh-hans"
```

**结果**: 成功返回分类列表，包含 `translations` 多语言对象和当前语言的 `name`、`description` 字段。

---

## 2. 获取分类树 ✅

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/tree/" \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: zh-hans"
```

**响应片段**:
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
        }
    ]
}
```

---

## 3. 获取分类详情 ✅

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/5/" \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: zh-hans"
```

**结果**: 成功返回分类详情，包含所有语言的翻译。

---

## 4. 语言切换验证 ✅

```bash
# 请求日语版本
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/5/" \
  -H "X-Tenant-ID: 1" \
  -H "Accept-Language: ja"
```

**结果**: 
- `name` 字段返回日语翻译（如果存在）或回退到其他语言
- `translations` 对象包含所有语言的翻译

---

## 5. 搜索功能验证 ✅

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/cms/categories/?search=Review" \
  -H "X-Tenant-ID: 1"
```

**结果**: 返回 1 个匹配的分类 (id=6, name=Review)

---

## 6. 创建分类（需认证）✅

```bash
# 未认证请求
curl -X POST "http://127.0.0.1:8000/api/v1/cms/categories/" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"translations": {"zh-hans": {"name": "测试"}}}'
```

**响应**:
```json
{
    "success": false,
    "code": 4001,
    "message": "身份认证信息未提供。",
    "data": null,
    "error_code": "AUTH_NOT_AUTHENTICATED"
}
```

**结论**: 创建分类需要认证，符合预期。

---

## 多语言字段结构

每个分类返回的数据包含：

1. **`translations` 对象**: 包含所有已设置的语言翻译
   ```json
   "translations": {
       "zh-hans": {"name": "...", "description": "..."},
       "en": {"name": "...", "description": "..."},
       "ja": {"name": "...", "description": "..."}
   }
   ```

2. **当前语言字段**: 根据 `Accept-Language` 返回对应语言的值
   - `name`: 当前语言的分类名称
   - `description`: 当前语言的描述
   - `seo_title`: 当前语言的SEO标题
   - `seo_description`: 当前语言的SEO描述

---

## 支持的语言代码

| 语言代码 | 语言 |
|---------|------|
| `zh-hans` | 简体中文（默认） |
| `en` | 英语 |
| `zh-hant` | 繁体中文 |
| `ja` | 日语 |
| `ko` | 韩语 |
| `fr` | 法语 |
