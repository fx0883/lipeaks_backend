# Member文章管理API - 快速参考手册

**版本**: v2.0（架构升级）  
**更新**: 2025-11-10  
**性能提升**: 10-50倍 🚀

---

## 认证

### 登录
```
POST /api/v1/auth/login/
Headers: X-Tenant-ID: {tenant_id}
Body: {"username": "xxx", "password": "xxx"}
Response: {"success": true, "data": {"token": "...", "user": {...}}}
```

---

## 文章管理

### 创建文章
```
POST /api/v1/cms/member/articles/
Headers: Authorization: Bearer {token}, X-Tenant-ID: {tenant_id}
Body: {"title": "...", "content": "...", "status": "draft"}
Response: 201 Created
```

### 获取文章列表
```
GET /api/v1/cms/member/articles/?page=1&page_size=20
Headers: Authorization: Bearer {token}, X-Tenant-ID: {tenant_id}
Response: {"success": true, "data": {"count": N, "results": [...]}}
```

#### 🚀 v2.0 高性能查询参数
```
# 推荐：精确查询（最佳性能）
GET /api/v1/cms/member/articles/?member_id=123&status=published
GET /api/v1/cms/member/articles/?user_id=456&status=published

# 兼容：通用查询
GET /api/v1/cms/member/articles/?author_id=123&status=published
```

### 获取文章详情
```
GET /api/v1/cms/member/articles/{id}/
Headers: Authorization: Bearer {token}, X-Tenant-ID: {tenant_id}
Response: {"success": true, "data": {...}}
```

### 更新文章
```
PATCH /api/v1/cms/member/articles/{id}/
Headers: Authorization: Bearer {token}, X-Tenant-ID: {tenant_id}
Body: {"title": "新标题"}
Response: 200 OK
```

### 删除文章
```
DELETE /api/v1/cms/member/articles/{id}/
Headers: Authorization: Bearer {token}, X-Tenant-ID: {tenant_id}
Response: 204 No Content
```

### 发布文章
```
POST /api/v1/cms/member/articles/{id}/publish/
Headers: Authorization: Bearer {token}, X-Tenant-ID: {tenant_id}
Response: {"success": true, "data": {...}}
```

### 获取文章统计
```
GET /api/v1/cms/member/articles/{id}/statistics/
Headers: Authorization: Bearer {token}, X-Tenant-ID: {tenant_id}
Response: {"success": true, "data": {"views_count": N, ...}}
```

---

## 状态码

| Code | 说明 |
|------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功 |
| 400 | 参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 不存在 |
| 500 | 服务器错误 |

---

## 文章状态

| 值 | 说明 |
|----|------|
| draft | 草稿 |
| pending | 待审核 |
| published | 已发布 |
| archived | 已归档 |

---

## 常见错误

| Error Code | 说明 | 处理 |
|------------|------|------|
| AUTH_TOKEN_EXPIRED | Token过期 | 刷新或重登录 |
| AUTH_PERMISSION_DENIED | 权限不足 | 提示用户 |
| TENANT_ID_INVALID | 租户ID错误 | 使用数字格式 |
| VALIDATION_ERROR | 参数验证失败 | 检查参数 |

---

## 重要提示

1. **所有请求必须携带**: `Authorization`和`X-Tenant-ID`头
2. **租户ID格式**: 必须是数字字符串，如`"1"`而不是`"tenant_1"`
3. **Token有效期**: 30天，过期需重新登录
4. **权限限制**: 只能操作自己创建的文章

---

**详细文档**: 
- 文档1: 认证与概述
- 文档2: 文章CRUD接口
- 文档3: 文章操作接口
- 文档4: 完整集成示例
