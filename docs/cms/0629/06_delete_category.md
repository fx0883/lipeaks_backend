# 删除分类 API

## API 端点

```
DELETE /api/v1/cms/categories/{id}/
```

## 描述

删除一个分类。**物理删除**（Category 继承 TranslatableModel，不走软删除机制）。

删除前会做两项前置检查：
1. 该分类下是否有关联文章 → 有则拒绝
2. 该分类下是否有子分类 → 有则拒绝

只有两项检查都通过才会执行删除。

- 管理员（租户管理员 + 超级管理员）可删除
- Member / 游客不可删除

> 注：`is_admin_only` 标记不影响删除分类本身的能力 —— 无论分类是否标记为管理员专属，删除权限都仅限管理员。

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | `Bearer <token>`，管理员 token |
| X-Tenant-ID | string | 是 | 租户 ID |

## 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer | 是 | 要删除的分类 ID |

## 请求体

无需请求体。

## 响应

### 成功响应（204 No Content）

空响应体。

### 失败响应

#### 分类下有关联文章（400 Bad Request）

```json
{
  "Cannot delete category with associated articles, please remove associated articles first"
}
```

> 注：需先解除文章与该分类的关联（编辑文章移除 `category_ids` 中的该分类，或删除相关文章），再重试删除。

#### 分类下有子分类（400 Bad Request）

```json
{
  "Cannot delete category with sub-categories, please delete all sub-categories first"
}
```

> 注：需先删除所有子分类（递归删除，从最深层开始），再重试删除父分类。

#### 分类不存在（404 Not Found）

```json
{
  "detail": "未找到。"
}
```

#### Member / 游客尝试删除（403 Forbidden）

```json
{
  "detail": "您没有执行该操作的权限。"
}
```

#### 未认证（401 Unauthorized）

```json
{
  "detail": "身份认证信息未提供。"
}
```

## 调用示例

### cURL — 管理员删除空分类（成功）

**前提**：ID=26 的分类下无文章、无子分类。

```bash
curl -X DELETE 'http://localhost:8000/api/v1/cms/categories/26/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin_token' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
```

**预期返回**：204 No Content（空响应体）

### cURL — 删除有关联文章的分类（被拒绝）

```bash
curl -X DELETE 'http://localhost:8000/api/v1/cms/categories/25/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin_token' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
```

**预期返回**：400 Bad Request
```json
{
  "Cannot delete category with associated articles, please remove associated articles first"
}
```

### cURL — 删除有子分类的父分类（被拒绝）

```bash
curl -X DELETE 'http://localhost:8000/api/v1/cms/categories/10/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin_token' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
```

**预期返回**：400 Bad Request
```json
{
  "Cannot delete category with sub-categories, please delete all sub-categories first"
}
```

### cURL — Member 尝试删除（被拒绝）

```bash
curl -X DELETE 'http://localhost:8000/api/v1/cms/categories/26/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.member_token' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
```

**预期返回**：403 Forbidden
```json
{
  "detail": "您没有执行该操作的权限。"
}
```

### cURL — 递归删除带子分类的分类树（完整流程）

**场景**：分类 10 下有子分类 11、12，需先删子分类再删父分类。

```bash
# Step 1: 先删叶子分类 11（前提：11 下无文章无子分类）
curl -X DELETE 'http://localhost:8000/api/v1/cms/categories/11/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin_token' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
# 预期：204 No Content

# Step 2: 删叶子分类 12
curl -X DELETE 'http://localhost:8000/api/v1/cms/categories/12/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin_token' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
# 预期：204 No Content

# Step 3: 现在父分类 10 下无子分类了，可以删
curl -X DELETE 'http://localhost:8000/api/v1/cms/categories/10/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin_token' \
  -H 'X-Tenant-ID: 9f8c1b2a-1234-5678-9abc-def012345678'
# 预期：204 No Content
```

## 注意事项

1. **物理删除**：分类被删除后不可恢复（Category 继承 TranslatableModel 而非 BaseModel，不走软删除）。如需保留数据，建议通过 `PATCH` 将 `is_active` 设为 `false` 来"禁用"分类，而非删除。
2. **删除顺序**：若分类有子分类，必须**先删子分类再删父分类**（递归删除，从最深层叶子节点开始）。
3. **关联文章**：若分类下有文章关联，必须先解除关联（编辑文章移除该分类，或删除文章），才能删除分类。
4. **操作日志**：删除操作会记录到 `cms_operation_log` 表（action=delete, entity_type=category）。
5. **多语言数据**：删除分类时会同时删除 `cms_category_translation` 表中该分类的所有语言翻译记录（CASCADE）。
6. **`is_admin_only` 不影响删除**：无论分类是否标记为管理员专属，删除分类本身的权限规则不变（仅管理员可删）。
7. **超级管理员**：需通过 `X-Tenant-ID` 请求头指定租户 ID。
