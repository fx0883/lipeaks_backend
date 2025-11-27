# Feedback System API 文档

## 概览

Feedback System 提供用户反馈管理功能，包括反馈提交、查询、更新、回复、附件管理、投票和统计等功能。

## 认证方式

使用 JWT Token 认证，在请求头中添加：
```
Authorization: Bearer <token>
```

**重要说明**：
- 租户管理员通过 Token 自动获取 tenant_id，无需额外传递 `X-Tenant-ID` 请求头
- Token 中包含用户的租户信息，系统会自动关联

## API 测试总结

| API | 方法 | 端点 | 状态 |
|-----|------|------|------|
| 获取反馈列表 | GET | /api/v1/feedbacks/feedbacks/ | ✅ 正常 |
| 提交反馈 | POST | /api/v1/feedbacks/feedbacks/ | ✅ 正常 |
| 获取反馈详情 | GET | /api/v1/feedbacks/feedbacks/{id}/ | ✅ 正常 |
| 完整更新反馈 | PUT | /api/v1/feedbacks/feedbacks/{id}/ | ✅ 正常 |
| 部分更新反馈 | PATCH | /api/v1/feedbacks/feedbacks/{id}/ | ✅ 正常 |
| 删除反馈 | DELETE | /api/v1/feedbacks/feedbacks/{id}/ | ✅ 正常 |
| 更改反馈状态 | PATCH | /api/v1/feedbacks/feedbacks/{id}/status/ | ✅ 正常 |
| 切换通知设置 | PATCH | /api/v1/feedbacks/feedbacks/{id}/notifications/ | ✅ 正常 |
| 验证邮箱 | POST | /api/v1/feedbacks/feedbacks/{id}/verify-email/ | ✅ 正常 |
| 投票 | POST | /api/v1/feedbacks/feedbacks/{id}/vote/ | ✅ 正常 |
| 移除投票 | DELETE | /api/v1/feedbacks/feedbacks/{id}/vote/ | ✅ 正常 |
| 获取回复列表 | GET | /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/ | ✅ 正常 |
| 创建回复 | POST | /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/ | ✅ 正常 |
| 获取回复详情 | GET | /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/ | ✅ 正常 |
| 更新回复 | PUT/PATCH | /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/ | ✅ 正常 |
| 删除回复 | DELETE | /api/v1/feedbacks/feedbacks/{feedback_pk}/replies/{id}/ | ✅ 正常 |
| 获取附件列表 | GET | /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/ | ✅ 正常 |
| 上传附件 | POST | /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/ | ✅ 正常 |
| 获取附件详情 | GET | /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/{id}/ | ✅ 正常 |
| 删除附件 | DELETE | /api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/{id}/ | ✅ 正常 |
| 获取统计信息 | GET | /api/v1/feedbacks/statistics/ | ✅ 正常 |
| 系统健康检查 | GET | /api/v1/feedbacks/health/ | ✅ 正常 |
| Redis 状态检查 | GET | /api/v1/feedbacks/health/redis/ | ✅ 正常 |

## 修复记录

### 问题1: 租户ID未正确设置

**问题描述**: 使用租户管理员 Token 创建反馈时，tenant_id 为 NULL。

**原因分析**: `get_tenant_from_request` 函数只从 `request.tenant` 获取租户，但 feedbacks 路径不在租户中间件的验证范围内。

**解决方案**: 修改 `get_tenant_from_request` 函数，支持多来源获取租户：
1. `request.tenant` (中间件设置)
2. `get_current_tenant()` (线程本地存储)
3. `request.user.tenant` (用户关联的租户)

**修改文件**:
- `feedbacks/views/feedback_api_views.py`
- `feedbacks/views/feedback_reply_api_views.py`
- `feedbacks/views/feedback_attachment_api_views.py`

### 问题2: 投票 API 缺少租户设置

**问题描述**: 投票时未设置 tenant 字段。

**解决方案**: 在 `FeedbackVoteView.post` 方法中添加租户获取逻辑。

**修改文件**: `feedbacks/complete_system.py`

## Token 说明

### 租户管理员 Token (用于测试)
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDY0MjA5NCwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.A9fO2Mxdu19i4bua1WtJDRq4gP28DYT-qNLKMG_MBA4
```

解码后的 Payload:
```json
{
  "user_id": 3,
  "username": "admin_cms",
  "exp": 1764642094,
  "model_type": "user",
  "is_admin": true,
  "is_super_admin": false,
  "is_staff": true
}
```

该用户关联租户 ID = 3。

## 数据说明

- 测试租户 ID: 3
- 测试应用 ID: 6
