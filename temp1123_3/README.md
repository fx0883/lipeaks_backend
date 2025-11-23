# CMS API 完整测试与文档

## 租户ID传递规则

**重要说明：不同用户类型传递租户ID的方式不同**

### 1. Admin用户（租户管理员）
- **使用查询参数**: `?tenant_id=3`
- **不使用header**: 不能使用`X-Tenant-ID` header，否则会被拒绝
- 示例：`GET /api/v1/cms/categories/?tenant_id=3`

### 2. Member用户
- **使用HTTP Header**: `X-Tenant-ID: 3`
- **不使用查询参数**: Member用户使用header传递租户ID
- 示例：`GET /api/v1/cms/member/articles/` 配合 `X-Tenant-ID: 3` header

### 3. Super Admin用户
- 可以使用查询参数 `?tenant_id=3` 指定要操作的租户
- 如果不指定租户ID，可以查看所有租户的数据

## Token信息

### Admin Token（租户管理员）
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM
```

### Member Token
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc
```

### 租户ID
```
Tenant ID: 3
```

## API分类

### 1. 文章管理 API (CMS-文章管理)
- 支持Admin和Member用户访问
- Member用户只能操作自己的文章
- Admin用户可以操作本租户所有文章

### 2. Member文章管理 API (CMS-Member文章管理)
- 仅Member用户访问
- Member用户管理自己的文章

### 3. 分类管理 API (CMS-分类管理)
- 仅Admin用户可以管理
- Member用户只能查看

### 4. 标签管理 API (CMS-标签管理)
- 仅Admin用户可以管理
- Member用户只能查看

### 5. 评论管理 API (CMS-评论管理)
- Admin可以管理所有评论
- Member可以创建评论

## 测试说明

### Admin用户调用示例
```bash
# 获取分类列表（使用查询参数）
curl -X GET "http://localhost:8000/api/v1/cms/categories/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"

# 创建分类（使用查询参数）
curl -X POST "http://localhost:8000/api/v1/cms/categories/?tenant_id=3" \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Category","slug":"test-category"}'
```

### Member用户调用示例
```bash
# 获取我的文章列表（使用header）
curl -X GET "http://localhost:8000/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3"

# 创建文章（使用header）
curl -X POST "http://localhost:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer {MEMBER_TOKEN}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Article","content":"Content","content_type":"markdown","status":"draft"}'
```

## 测试脚本说明

- `test_all_cms_apis_fixed.sh`: 修复后的完整测试脚本
- 脚本会自动测试所有API并输出测试结果
- 测试结果会保存到 `test_results_fixed.txt`

## 常见错误

### 错误1: "Tenant operation failed"
- **原因**: Admin用户使用了X-Tenant-ID header
- **解决**: 改用查询参数 `?tenant_id=3`

### 错误2: "身份认证信息未提供"
- **原因**: 未提供或Token过期
- **解决**: 确保请求头中包含有效的Authorization token

### 错误3: "You do not have permission to create articles"
- **原因**: 权限不足或用户类型错误
- **解决**: 检查用户是否是Member类型，确保已修复权限代码

## 文件列表

1. `README.md` - 本文件
2. `test_all_cms_apis_fixed.sh` - 修复后的测试脚本
3. `01_文章管理API文档.md` - 文章管理API详细文档
4. `02_分类标签API文档.md` - 分类和标签API详细文档
5. `03_评论管理API文档.md` - 评论管理API详细文档
6. `04_Member文章API文档.md` - Member文章管理API详细文档
