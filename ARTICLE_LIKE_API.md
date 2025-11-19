# 文章点赞功能 API 文档

## 功能概述

文章点赞功能已成功实现，支持 Member 用户对文章进行点赞操作。

## 实现内容

### 1. 数据模型 (`interactions/models.py`)
- **ArticleLike 模型**
  - 字段：from_member, article, tenant, created_at, ip_address, user_agent
  - 唯一约束：同一用户不能重复点赞同一文章
  - 索引优化：支持高效查询

### 2. 序列化器 (`interactions/serializers.py`)
- **ArticleLikeSerializer**: 详情序列化器（包含文章详情和用户信息）
- **ArticleLikeCreateSerializer**: 创建序列化器（验证逻辑）

### 3. 权限控制 (`interactions/permissions.py`)
- **ArticleLikePermission**: 仅 Member 用户可访问

### 4. 视图集 (`interactions/views.py`)
- **ArticleLikeViewSet**: 提供完整的点赞 CRUD 操作

### 5. 后台管理 (`interactions/admin.py`)
- **ArticleLikeAdmin**: 支持在 Django Admin 中管理点赞记录

## API 端点

### 基础 URL
```
/api/v1/interactions/article-likes/
```

### 可用接口

#### 1. 获取我点赞的文章列表
```bash
GET /api/v1/interactions/article-likes/
Headers:
  Authorization: Bearer {token}
  X-Tenant-ID: {tenant_id}
```

#### 2. 点赞文章
```bash
POST /api/v1/interactions/article-likes/
Headers:
  Authorization: Bearer {token}
  X-Tenant-ID: {tenant_id}
  Content-Type: application/json
Body:
{
  "article": 10251
}
```

#### 3. 取消点赞（通过记录ID）
```bash
DELETE /api/v1/interactions/article-likes/{id}/
Headers:
  Authorization: Bearer {token}
  X-Tenant-ID: {tenant_id}
```

#### 4. 取消点赞（通过文章ID）
```bash
DELETE /api/v1/interactions/article-likes/by-article/{article_id}/
Headers:
  Authorization: Bearer {token}
  X-Tenant-ID: {tenant_id}
```

#### 5. 检查文章点赞状态
```bash
GET /api/v1/interactions/article-likes/check/{article_id}/
Headers:
  Authorization: Bearer {token}
  X-Tenant-ID: {tenant_id}
```

**响应示例：**
```json
{
  "is_liked": true,
  "like_id": 1,
  "created_at": "2025-11-19T03:50:05.254719Z"
}
```

#### 6. 获取文章的点赞用户列表
```bash
GET /api/v1/interactions/article-likes/by-article/{article_id}/likers/
Headers:
  Authorization: Bearer {token}
  X-Tenant-ID: {tenant_id}
```

## 核心功能特性

### ✅ 已实现功能
1. **点赞/取消点赞**: 支持对文章进行点赞和取消点赞
2. **防重复点赞**: 同一用户不能重复点赞同一文章
3. **状态检查**: 快速查询文章的点赞状态
4. **列表查询**: 
   - 获取用户点赞的文章列表
   - 获取文章的点赞用户列表
5. **统计同步**: 实时更新 `ArticleStatistics.likes_count`
6. **IP 和 User-Agent 记录**: 记录点赞来源信息
7. **租户隔离**: 严格的租户权限控制
8. **完整权限控制**: 仅 Member 用户可以点赞

### 🔒 权限验证
- 需要 JWT 认证
- 仅 Member 用户可访问
- 租户隔离验证
- 防止跨租户操作

### 📊 统计功能
- 点赞时自动更新文章统计的 `likes_count`
- 取消点赞时自动减少计数
- 保证统计数据准确性

## 测试结果

所有测试用例通过：
- ✅ 检查未点赞状态
- ✅ 点赞文章
- ✅ 检查已点赞状态
- ✅ 获取我点赞的文章列表
- ✅ 获取文章的点赞用户列表
- ✅ 取消点赞
- ✅ 重复点赞验证（正确拒绝）
- ✅ 统计同步验证

## 已删除内容

- ❌ 删除了 `cms.Interaction` 模型
- ❌ 删除了 `cms_interaction` 数据库表
- ❌ 删除了相关的序列化器、权限类、Admin 配置

## 数据库变更

- 新表：`interactions_article_like`
- 删除表：`cms_interaction`

## 注意事项

1. **用户类型限制**: 只有 Member 用户可以点赞文章（不支持 Admin 用户）
2. **租户隔离**: 严格的租户权限控制，无法跨租户操作
3. **统计实时性**: 点赞/取消点赞后统计数据实时更新
4. **防重复**: 数据库层面的唯一约束防止重复点赞

## 使用示例

参考 Django Swagger 文档获取详细的 API 使用示例：
```
http://localhost:8000/api/v1/docs/
```

标签：`用户互动-文章点赞`
