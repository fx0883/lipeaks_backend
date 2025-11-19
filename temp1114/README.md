# 评论审核 API 文档

欢迎使用评论审核 API 文档。本文档为前端开发者提供完整的 API 集成指南。

---

## 📚 文档目录

### 1. [概述与认证](./01_overview.md)
- API 基础信息
- 认证方式说明
- 权限规则详解
- 通用错误码

### 2. [批准评论接口](./02_approve_api.md)
- 接口说明
- 请求/响应参数
- 完整代码示例（JavaScript、Python、TypeScript）
- 错误处理

### 3. [拒绝评论接口](./03_reject_api.md)
- 接口说明
- 请求/响应参数
- 使用示例

### 4. [标记垃圾评论接口](./04_mark_spam_api.md)
- 接口说明
- 请求/响应参数
- 使用场景

### 5. [批量操作接口](./05_batch_api.md)
- 批量批准/拒绝/标记垃圾/删除
- 请求/响应参数
- 完整代码示例
- 权限说明

### 6. [查询评论接口](./06_query_api.md)
- 查询参数说明
- 分页处理
- 筛选条件
- 完整代码示例

### 7. [完整工作流示例](./07_workflow_examples.md)
- 管理员审核流程
- React 批量审核组件
- Vue 评论展示组件
- 自动监控垃圾评论
- Shell 脚本批处理
- 错误处理最佳实践

---

## 🚀 快速开始

### Step 1: 登录获取 Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

### Step 2: 查询待审核评论

```bash
curl -X GET "http://localhost:8000/api/v1/cms/comments/?status=pending" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 3: 批准评论

```bash
curl -X POST "http://localhost:8000/api/v1/cms/comments/3/approve/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 📋 API 概览

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 批准评论 | POST | `/cms/comments/{id}/approve/` | 批准单条评论 |
| 拒绝评论 | POST | `/cms/comments/{id}/reject/` | 拒绝单条评论 |
| 标记垃圾 | POST | `/cms/comments/{id}/mark-spam/` | 标记为垃圾评论 |
| 批量操作 | POST | `/cms/comments/batch/` | 批量处理评论 |
| 查询评论 | GET | `/cms/comments/` | 查询评论列表 |

---

## 🔐 权限说明

| 用户类型 | 权限 |
|---------|------|
| 超级管理员 | ✅ 所有租户的所有评论 |
| 租户管理员 | ✅ 本租户的所有评论 |
| 文章作者（管理员） | ✅ 自己文章下的评论 |
| 普通成员 | ❌ 无审核权限 |

**重要提示**：
- 租户管理员**无需**在请求中传递 `X-Tenant-ID` 或 `tenant_id` 参数
- 系统会自动从 JWT token 中推断租户信息
- 普通成员（Member）即使是文章作者也无法执行审核操作

---

## 📊 评论状态

| 状态 | 值 | 说明 |
|------|---|------|
| 待审核 | `pending` | 新创建的评论 |
| 已批准 | `approved` | 可在前端显示 |
| 已拒绝 | `rejected` | 不显示 |
| 垃圾评论 | `spam` | 标记为垃圾 |
| 已删除 | `trash` | 软删除 |

---

## ⚠️ 常见错误

| 错误码 | HTTP 状态 | 说明 | 解决方法 |
|-------|----------|------|---------|
| 4010 | 401 | 未认证 | 检查 token 是否有效 |
| 4030 | 403 | 无权限 | 检查用户类型和权限 |
| 4040 | 404 | 资源不存在 | 检查评论 ID 是否正确 |
| 4000 | 400 | 参数错误 | 检查请求参数格式 |

---

## 🔧 技术栈示例

### JavaScript/TypeScript
- [批准评论示例](./02_approve_api.md#使用示例)
- [批量操作示例](./05_batch_api.md#使用示例)

### Python
- [批准评论示例](./02_approve_api.md#python-requests)
- [查询评论示例](./06_query_api.md#python-requests)

### React
- [批量审核组件](./07_workflow_examples.md#工作流-2-批量审核评论)

### Vue
- [评论展示组件](./07_workflow_examples.md#工作流-3-文章详情页展示评论)

### Shell Script
- [批量处理脚本](./07_workflow_examples.md#工作流-5-shell-脚本批量审核)

---

## 📝 测试数据

文档中使用的测试数据：
- **基础 URL**: `http://localhost:8000/api/v1`
- **测试租户**: ID = 1 (租户名称: 金sir)
- **测试管理员**: `admin_jin` / `AdminPass123!`
- **测试文章**: ID = 10247
- **测试评论**: ID = 3, 35, 36, 37, 38, 39

---

## 🆘 技术支持

如有问题，请联系后端开发团队。

---

## 📅 更新日志

**v1.0.0** (2025-11-14)
- ✅ 完成评论审核 API 代码修改
- ✅ 修复 `AttributeError: 'Article' object has no attribute 'author_id'` 问题
- ✅ 使用 `comment.article.author` 属性替代 `author_id`
- ✅ 通过 cURL 验证所有接口
- ✅ 编写完整 API 文档

**修改内容**：
- 修改 `cms/views.py` 中 `approve`、`reject`、`mark_as_spam` 三个方法
- 将权限检查从 `can_moderate_comments(user, comment.article.author_id)` 改为 `can_moderate_comments(user, comment.article.author)`
- 无需修改数据库结构
- 保持对现有 API 的完全兼容

---

## ✅ API 验证状态

所有接口已通过 cURL 测试验证：

- ✅ **批准评论** - 测试通过 (评论 ID: 3)
- ✅ **拒绝评论** - 测试通过 (评论 ID: 35)
- ✅ **标记垃圾** - 测试通过 (评论 ID: 36)
- ✅ **批量批准** - 测试通过 (评论 ID: 37, 38)
- ✅ **批量标记垃圾** - 测试通过 (评论 ID: 39)

测试环境：
- 后端服务器：运行中
- 测试用户：租户管理员 `admin_jin`
- 测试时间：2025-11-14

---

**祝开发顺利！** 🎉
