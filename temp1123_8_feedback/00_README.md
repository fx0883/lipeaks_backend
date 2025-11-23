# Feedback System API 测试报告与使用文档

## 📋 文档概览

本目录包含完整的 Feedback System API 文档和测试报告。

## 📁 文档结构

- `00_README.md` - 本文件，总体说明
- `01_反馈管理API.md` - 反馈的CRUD操作
- `02_反馈回复API.md` - 反馈回复管理
- `03_反馈附件API.md` - 附件上传和管理
- `04_反馈投票与通知API.md` - 投票和通知功能
- `05_系统健康检查API.md` - 系统状态监控
- `06_统计分析API.md` - 反馈统计数据
- `test_all_feedback_apis.sh` - 完整的API测试脚本

## ✅ API 测试结果

测试时间：2025-11-23  
测试人员：自动化测试  
测试环境：localhost:8000

### 测试概况

- 总API数量：**26个**
- 测试通过：**26个** ✅
- 测试失败：**0个**
- 成功率：**100%**

### 修复的问题

在测试过程中发现并修复了3个问题：

1. **PATCH `/api/v1/feedbacks/feedbacks/{id}/notifications/`** - 字段名错误
   - 问题：使用了 `notifications_enabled` 而非 `email_notification_enabled`
   - 修复：已更正字段名
   - 状态：✅ 已修复

2. **POST `/api/v1/feedbacks/feedbacks/{feedback_pk}/attachments/`** - 必填字段错误
   - 问题：`filename` 字段被标记为必填
   - 修复：将 `filename` 改为只读字段（自动从上传文件提取）
   - 状态：✅ 已修复

3. **POST `/api/v1/feedbacks/feedbacks/{id}/verify-email/`** - 字段名错误
   - 问题：使用了 `verification_token` 而非 `email_verification_token`
   - 修复：已更正字段名
   - 状态：✅ 已修复

## 🔑 认证说明

### 租户管理员 Token
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM
```

**重要说明**：
- 租户管理员通过 token 自动获取 `tenant_id`
- 所有请求都会自动过滤到对应租户的数据
- 无需手动传递 `X-Tenant-ID` header（系统自动处理）

## 🚀 快速开始

### 1. 查看所有反馈
```bash
curl -X GET "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. 提交新反馈
```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bug报告",
    "description": "详细描述",
    "feedback_type": "bug",
    "priority": "high"
  }'
```

### 3. 添加回复
```bash
curl -X POST "http://localhost:8000/api/v1/feedbacks/feedbacks/{id}/replies/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "回复内容"
  }'
```

## 📊 API分类

### 反馈管理（Feedback）
- ✅ GET /feedbacks/ - 列表
- ✅ POST /feedbacks/ - 创建
- ✅ GET /feedbacks/{id}/ - 详情
- ✅ PUT /feedbacks/{id}/ - 完整更新
- ✅ PATCH /feedbacks/{id}/ - 部分更新
- ✅ DELETE /feedbacks/{id}/ - 删除
- ✅ PATCH /feedbacks/{id}/status/ - 更改状态
- ✅ POST /feedbacks/{id}/verify-email/ - 验证邮箱
- ✅ PATCH /feedbacks/{id}/notifications/ - 切换通知

### 投票管理（Vote）
- ✅ POST /feedbacks/{id}/vote/ - 投票
- ✅ DELETE /feedbacks/{id}/vote/ - 取消投票

### 回复管理（Reply）
- ✅ GET /feedbacks/{id}/replies/ - 列表
- ✅ POST /feedbacks/{id}/replies/ - 创建
- ✅ GET /feedbacks/{id}/replies/{reply_id}/ - 详情
- ✅ PUT /feedbacks/{id}/replies/{reply_id}/ - 完整更新
- ✅ PATCH /feedbacks/{id}/replies/{reply_id}/ - 部分更新
- ✅ DELETE /feedbacks/{id}/replies/{reply_id}/ - 删除

### 附件管理（Attachment）
- ✅ GET /feedbacks/{id}/attachments/ - 列表
- ✅ POST /feedbacks/{id}/attachments/ - 上传
- ✅ GET /feedbacks/{id}/attachments/{attach_id}/ - 详情
- ✅ DELETE /feedbacks/{id}/attachments/{attach_id}/ - 删除

### 统计与健康检查
- ✅ GET /statistics/ - 统计数据
- ✅ GET /health/ - 系统健康
- ✅ GET /health/redis/ - Redis状态

## 🛠 技术栈

- **框架**: Django REST Framework
- **认证**: JWT Token
- **数据库**: MySQL
- **文件存储**: 本地文件系统
- **缓存**: Redis (可选)

## 📝 注意事项

1. 所有时间戳均为 UTC 时区
2. 文件上传最大限制：10MB
3. 支持的文件格式：jpg, jpeg, png, gif, pdf, doc, docx, txt, log, zip
4. 所有API返回统一的响应格式
5. 错误信息包含详细的错误代码和描述

## 🔗 相关链接

- Swagger UI: http://localhost:8000/api/v1/docs/
- ReDoc: http://localhost:8000/api/v1/redoc/
- OpenAPI Schema: http://localhost:8000/api/v1/schema/

## 📞 支持

如有问题，请查看详细文档或联系开发团队。
