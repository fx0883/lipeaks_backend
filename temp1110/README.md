# Member CMS API 集成指南

## 📋 文档概述

本系列文档专门为前端开发人员编写，提供完整的Member（会员用户）CMS系统API集成指南。所有文档都包含详细的输入参数说明、输出格式、使用示例，让前端开发者能够快速集成API。

**📢 更新说明**: 本文档已通过实际API调用验证，所有返回示例均基于真实的服务器响应数据，确保与实际API行为完全一致。

## 📚 文档目录

### 📖 [API 完整参考手册](API_REFERENCE.md)
- 所有API接口的完整索引
- 快速导航和查找
- 集成指南和最佳实践

### 1. 🔐 [认证系统](01_authentication.md) - 5个接口
- 用户注册 (`POST /auth/member/register/`)
- 用户登录 (`POST /auth/login/`)
- Token刷新 (`POST /auth/refresh/`)
- Token验证 (`GET /auth/verify/`)
- 密码重置请求 (`POST /auth/password-reset/request/`)

### 2. 👤 [用户管理](02_user_management.md) - 5个接口
- 获取用户信息 (`GET /members/me/`)
- 更新用户信息 (`PUT/PATCH /members/me/`)
- 修改密码 (`POST /members/me/password/`)
- 上传头像 (`POST /members/avatar/upload/`)
- 为指定用户上传头像 (`POST /members/{id}/avatar/upload/`)

### 3. 📝 [文章管理](03_article_management.md) - 7个接口
- 获取文章列表 (`GET /cms/member/articles/`)
- 获取单篇文章 (`GET /cms/member/articles/{id}/`)
- 创建文章 (`POST /cms/member/articles/`)
- 更新文章 (`PUT/PATCH /cms/member/articles/{id}/`)
- 删除文章 (`DELETE /cms/member/articles/{id}/`)
- 发布文章 (`POST /cms/member/articles/{id}/publish/`)
- 获取文章统计 (`GET /cms/member/articles/{id}/statistics/`)

### 4. 💝 [互动功能](04_interactions.md) - 6个接口
- 获取收藏列表 (`GET /interactions/favorites/`)
- 收藏文章 (`POST /interactions/favorites/`)
- 取消收藏 (`DELETE /interactions/favorites/{id}/`)
- 检查收藏状态 (`GET /interactions/favorites/check/{id}/`)
- 获取点赞列表 (`GET /interactions/likes/`)
- 点赞用户 (`POST /interactions/likes/`)

### 5. 🏷️ [分类标签](05_categories_tags.md) - 6个接口
- 获取分类列表 (`GET /cms/categories/`)
- 获取分类树 (`GET /cms/categories/tree/`)
- 创建分类 (`POST /cms/categories/`)
- 获取标签列表 (`GET /cms/tags/`)
- 创建标签 (`POST /cms/tags/`)
- 获取标签分组列表 (`GET /cms/tag-groups/`)

### 6. 💬 [评论系统](06_comments.md) - 13个接口
        - 获取文章评论列表 (`GET /cms/comments/`)
        - 获取单条评论详情 (`GET /cms/comments/{id}/`)
        - 发表评论 (`POST /cms/comments/`)
        - 回复评论 (`POST /cms/comments/{id}/replies/`)
        - 更新评论 (`PUT/PATCH /cms/comments/{id}/`)
        - 删除评论 (`DELETE /cms/comments/{id}/`)
        - 获取评论回复 (`GET /cms/comments/{id}/replies/`)
        - 点赞评论 (`POST /cms/comments/{id}/like/`)
        - 取消点赞评论 (`DELETE /cms/comments/{id}/like/`)
        - 举报评论 (`POST /cms/comments/{id}/report/`)
        - 审核评论 (`POST /cms/comments/{id}/moderate/`)

## 🔑 通用规范

### 请求头要求
```bash
Authorization: Bearer {access_token}    # 除注册登录外都需要
X-Tenant-ID: {tenant_id}                # Member用户必填
Content-Type: application/json          # POST/PUT请求
```

### 响应格式
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": { ... },           // 主要数据
  "error_code": null         // 错误时返回错误码
}
```

### 分页响应
```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 150,            // 总条数
    "next": "...",           // 下一页URL
    "previous": "...",       // 上一页URL
    "results": [...]         // 数据列表
  }
}
```

## 🛠️ 开发环境配置

### Base URL
```
https://your-domain.com/api/v1/
```

### 测试Token获取
```bash
# 1. 注册/登录获取token
curl -X POST https://your-domain.com/api/v1/auth/member/register/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "password_confirm": "password123"
  }'
```

## 📝 注意事项

1. **租户隔离**: 所有Member相关操作都需要指定 `X-Tenant-ID`
2. **权限控制**: 只能操作自己的数据（文章、收藏等）
3. **Token管理**: Access Token有效期通常为15分钟，需要及时刷新
4. **错误处理**: 统一响应格式，优先检查 `success` 字段
5. **分页处理**: 大数据量接口都支持分页，默认每页20条

## 🎯 快速开始

1. 阅读 [认证系统文档](01_authentication.md) 了解登录注册
2. 查看 [用户管理文档](02_user_management.md) 了解用户信息操作
3. 学习 [文章管理文档](03_article_management.md) 实现文章功能
4. 集成 [互动功能文档](04_interactions.md) 增加用户粘性

---

**文档版本**: v2.0 (双外键架构优化版)  
**更新时间**: 2025-11-10  
**适用对象**: 前端开发人员
