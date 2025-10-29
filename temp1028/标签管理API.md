# 标签管理 API

## 标签组 TagGroup
Base: `/api/v1/cms/tag-groups/`

### 通用要求
- **Headers（必须）**：
  - `X-Tenant-ID: <tenant_id>`
  - `Authorization: Bearer <token>`（GET匿名可不带；POST/PUT/PATCH/DELETE 需要）
  - `Content-Type: application/json`
- **权限模型（`TagPermission` 继承 `CMSBasePermission`，`TagGroupViewSet` 也用该权限）**：
  - 匿名：允许GET；仍需 `X-Tenant-ID`。
  - Member：写操作需认证且受租户限制。
  - Admin：管理本租户全部标签/标签组；Super Admin 需通过 `X-Tenant-ID` 指定租户。

### 1. 获取列表 GET /
- 参数：`is_active`, `search`
- 权限：匿名允许（需 `X-Tenant-ID`）。
- 示例：
```bash
curl -X GET http://your-domain.com/api/v1/cms/tag-groups/ \
  -H "X-Tenant-ID: 1"
```

### 2. 获取详情 GET /{id}/
- 权限：匿名允许（需 `X-Tenant-ID`）。
```bash
curl -X GET http://your-domain.com/api/v1/cms/tag-groups/1/ \
  -H "X-Tenant-ID: 1"
```

### 3. 创建 POST /
```json
{"name":"技术栈","slug":"tech-stack","description":"描述","is_active":true}
```
- 权限：需要认证；Admin/Super Admin 可创建；Member 受限。
- 示例：
```bash
curl -X POST http://your-domain.com/api/v1/cms/tag-groups/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{"name":"技术栈","slug":"tech-stack","is_active":true}'
```

### 4. 更新 PUT /{id}/
- 权限：需要认证；Admin/Super Admin 可更新。
```bash
curl -X PUT http://your-domain.com/api/v1/cms/tag-groups/1/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{"name":"技术主题","is_active":true}'
```

### 5. 部分更新 PATCH /{id}/
- 权限与Headers同上。

### 6. 删除 DELETE /{id}/
- 约束：存在关联标签时不可删除
- 权限：需要认证；Admin/Super Admin 可删除。
```bash
curl -X DELETE http://your-domain.com/api/v1/cms/tag-groups/1/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1"
```

---

## 标签 Tag
Base: `/api/v1/cms/tags/`

### 通用要求
- **Headers（必须）**：同上
- **额外校验**：创建/更新时若指定 `group`，该 `group` 必须属于当前 `X-Tenant-ID` 对应租户，否则会被拒绝（见 `views.TagViewSet.perform_create/perform_update`）。

### 1. 获取列表 GET /
- 参数：`group`, `is_active`, `search`
- 权限：匿名允许（需 `X-Tenant-ID`）。
```bash
curl -X GET http://your-domain.com/api/v1/cms/tags/?group=1 \
  -H "X-Tenant-ID: 1"
```

### 2. 获取详情 GET /{id}/
```bash
curl -X GET http://your-domain.com/api/v1/cms/tags/8/ \
  -H "X-Tenant-ID: 1"
```

### 3. 创建 POST /
```json
{"name":"Python","slug":"python","group":1,"color":"#3776AB","is_active":true}
```
- 权限：需要认证；Admin/Super Admin 可创建；Member 受限。
```bash
curl -X POST http://your-domain.com/api/v1/cms/tags/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{"name":"Python","slug":"python","group":1,"color":"#3776AB","is_active":true}'
```

### 4. 更新 PUT /{id}/
```bash
curl -X PUT http://your-domain.com/api/v1/cms/tags/8/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1" -H "Content-Type: application/json" \
  -d '{"name":"Python3","color":"#3776AB"}'
```

### 5. 部分更新 PATCH /{id}/
- 权限与Headers同上。

### 6. 删除 DELETE /{id}/
- 约束：存在关联文章时不可删除
- 权限：需要认证；Admin/Super Admin 可删除。
```bash
curl -X DELETE http://your-domain.com/api/v1/cms/tags/8/ \
  -H "Authorization: Bearer <token>" -H "X-Tenant-ID: 1"
```

### 7. 使用统计 GET /usage-stats/
- 响应：`[{"id":1,"name":"Python","slug":"python","color":"#3776AB","articles_count":25}]`
- 权限：匿名允许（需 `X-Tenant-ID`）。
