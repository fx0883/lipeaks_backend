# 评论审核 API 文档 - 概述

## 目录
- [概述](#概述)
- [认证说明](#认证说明)
- [权限说明](#权限说明)
- [通用错误码](#通用错误码)
- [相关文档](#相关文档)

---

## 概述

评论审核 API 提供了完整的评论管理功能，包括批准、拒绝、标记垃圾以及批量操作等。这些接口用于帮助租户管理员和文章作者管理用户评论内容。

**基础 URL**: `http://localhost:8000/api/v1`

**版本**: v1

---

## 认证说明

所有评论审核接口都需要 JWT 认证。请在请求头中包含有效的 token：

```http
Authorization: Bearer {your_jwt_token}
```

### 获取 Token

**接口地址**: `POST /api/v1/auth/login/`

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 2,
      "username": "admin_jin",
      "email": "admin_jin@qq.com",
      "is_admin": true,
      "tenant_id": 1,
      "tenant_name": "金sir"
    }
  }
}
```

---

## 权限说明

评论审核操作的权限规则如下：

| 用户类型 | 权限范围 |
|---------|---------|
| **超级管理员** | 可以审核所有租户的所有评论 |
| **租户管理员** | 可以审核本租户内的所有评论 |
| **文章作者（管理员）** | 可以审核自己文章下的评论（仅限管理员类型用户） |
| **普通成员 (Member)** | ❌ 无权限进行审核操作 |
| **游客** | ❌ 无权限进行审核操作 |

### 重要说明

1. **租户管理员**：
   - 无需在请求中传递 `X-Tenant-ID` 头或 `tenant_id` 参数
   - 系统会自动从 JWT token 中推断租户信息
   - 只能审核本租户内的评论

2. **普通成员限制**：
   - 即使是文章作者，如果用户类型是 Member，也无法执行审核操作
   - 审核权限仅限于管理员类型用户（User 模型）

3. **文章作者权限**：
   - 文章作者（管理员用户）可以审核自己文章下的评论
   - 系统会自动识别文章作者身份

---

## 通用错误码

| HTTP 状态码 | 业务码 | 说明 |
|-----------|-------|------|
| 200 | 2000 | 操作成功 |
| 400 | 4000 | 请求参数错误 |
| 401 | 4010 | 未认证或 token 无效 |
| 403 | 4030 | 无权限执行该操作 |
| 404 | 4040 | 资源不存在 |
| 500 | 5000 | 服务器内部错误 |

### 成功响应格式
```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    // 具体数据
  }
}
```

### 错误响应格式
```json
{
  "success": false,
  "code": 4030,
  "message": "您没有权限批准此评论",
  "data": null
}
```

---

## 相关文档

- [02_approve_api.md](./02_approve_api.md) - 批准评论接口
- [03_reject_api.md](./03_reject_api.md) - 拒绝评论接口
- [04_mark_spam_api.md](./04_mark_spam_api.md) - 标记垃圾评论接口
- [05_batch_api.md](./05_batch_api.md) - 批量操作接口
- [06_query_api.md](./06_query_api.md) - 查询评论接口
- [07_workflow_examples.md](./07_workflow_examples.md) - 完整工作流示例

---

## 评论状态说明

评论有以下几种状态：

| 状态 | 值 | 说明 |
|------|---|------|
| 待审核 | `pending` | 评论刚创建，等待管理员审核 |
| 已批准 | `approved` | 评论已通过审核，可以在前端显示 |
| 已拒绝 | `rejected` | 评论被拒绝，不会在前端显示 |
| 垃圾评论 | `spam` | 评论被标记为垃圾内容 |
| 已删除 | `trash` | 评论已被删除（软删除） |

---

## 技术支持

如有问题，请联系开发团队。
