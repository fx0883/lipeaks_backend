# Feedback System API 使用文档

## 📚 文档概述

本文档集为前端开发者提供详细的 Feedback System API 使用指南。所有 API 都已集成到统一的 `Feedback System` 标签下。

## 🎯 文档结构

### 核心文档

1. **[00_API文档总览.md](00_API文档总览.md)** (本文档) - 文档导航和快速开始
2. **[01_软件管理API.md](01_软件管理API.md)** - 软件分类、产品、版本管理
3. **[02_反馈管理API.md](02_反馈管理API.md)** - 反馈的增删改查、状态管理
4. **[03_反馈互动API.md](03_反馈互动API.md)** - 回复、投票、附件
5. **[04_邮件系统API.md](04_邮件系统API.md)** - 邮件模板、日志管理
6. **[05_统计与监控API.md](05_统计与监控API.md)** - 统计数据、系统健康检查
7. **[06_前端对接指南.md](06_前端对接指南.md)** - Vue3 对接说明和最佳实践

## 🚀 快速开始

### API 基础信息

**基础 URL**: `http://your-domain.com/api/v1/feedbacks`

**认证方式**: JWT Bearer Token

**请求头配置**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

### 认证流程

1. **获取 Token**
   - 调用登录接口：`POST /api/v1/auth/login/`
   - 请求体：`{ username, password }`
   - 返回：`{ access, refresh }`

2. **使用 Token**
   - 在所有请求的 Header 中添加：`Authorization: Bearer {access}`

3. **刷新 Token**
   - Token 过期时调用：`POST /api/v1/auth/refresh/`
   - 请求体：`{ refresh }`
   - 返回新的：`{ access }`

### API 调用示例

**获取反馈列表**：
```
GET /api/v1/feedbacks/feedbacks/
Headers: Authorization: Bearer {token}
Params: { page: 1, page_size: 20 }
```

**提交反馈**：
```
POST /api/v1/feedbacks/feedbacks/
Headers: Authorization: Bearer {token}
Body: {
  title: "反馈标题",
  description: "详细描述",
  software: 1,
  feedback_type: "bug"
}
```

## 📊 API 分类统计

| 模块 | API 数量 | 主要功能 | 文档链接 |
|------|---------|---------|---------|
| 软件管理 | 18 | 分类、产品、版本管理 | [01_软件管理API.md](01_软件管理API.md) |
| 反馈管理 | 13 | 反馈CRUD、状态流转 | [02_反馈管理API.md](02_反馈管理API.md) |
| 反馈互动 | 10 | 回复、投票、附件 | [03_反馈互动API.md](03_反馈互动API.md) |
| 邮件系统 | 8 | 模板、日志查询 | [04_邮件系统API.md](04_邮件系统API.md) |
| 统计监控 | 3 | 统计、健康检查 | [05_统计与监控API.md](05_统计与监控API.md) |
| **总计** | **52** | - | - |

## 🔐 权限说明

### 用户角色

**超级管理员 (Superuser)**
- 访问所有租户的数据
- 管理所有系统配置
- 查看所有统计信息

**租户管理员 (Tenant Admin)**
- 管理本租户的软件和反馈
- 回复反馈、修改状态
- 管理邮件模板
- 查看租户统计数据

**普通成员 (Member)**
- 提交反馈
- 查看和修改自己的反馈
- 对反馈投票
- 查看公开回复

**匿名用户 (Anonymous)**
- 提交反馈（需邮箱验证）
- 无法查看其他反馈
- 无法投票或回复

### 权限矩阵

| 操作 | 超级管理员 | 租户管理员 | 普通成员 | 匿名用户 |
|------|-----------|-----------|---------|---------|
| 创建软件分类 | ✅ | ✅ | ❌ | ❌ |
| 创建软件产品 | ✅ | ✅ | ❌ | ❌ |
| 提交反馈 | ✅ | ✅ | ✅ | ✅ |
| 查看所有反馈 | ✅ | ✅ | ❌ | ❌ |
| 修改反馈状态 | ✅ | ✅ | ❌ | ❌ |
| 回复反馈 | ✅ | ✅ | ❌ | ❌ |
| 投票 | ✅ | ✅ | ✅ | ❌ |
| 上传附件 | ✅ | ✅ | ✅ | ✅ |
| 查看统计 | ✅ | ✅ | ❌ | ❌ |
| 管理邮件模板 | ✅ | ✅ | ❌ | ❌ |

## 📋 常见问题

### Q1: 如何处理分页？

**请求参数**：
- `page`: 页码（从1开始）
- `page_size`: 每页数量（默认20）
- `ordering`: 排序字段（加 `-` 表示降序）

**响应格式**：
```json
{
  "count": 100,           // 总记录数
  "next": "url",          // 下一页URL
  "previous": null,       // 上一页URL
  "results": [...]        // 当前页数据
}
```

### Q2: 如何搜索和筛选？

**搜索参数**：
- `search`: 全文搜索（标题、描述、邮箱）
- 字段筛选：`software`, `status`, `feedback_type`, `priority`
- 布尔筛选：`is_active`, `email_verified`

**示例**：
```
GET /feedbacks/?software=1&status=submitted&search=崩溃
```

### Q3: 如何上传文件？

**要求**：
- 使用 `multipart/form-data` 格式
- 文件字段名：`file`
- 最大大小：10MB
- 支持格式：图片、PDF、Word、TXT、ZIP

**请求示例**：
```
POST /feedbacks/{id}/attachments/
Content-Type: multipart/form-data
Body: FormData { file: File, description: "说明" }
```

### Q4: 如何处理错误？

**HTTP 状态码**：

| 状态码 | 说明 | 处理建议 |
|--------|------|---------|
| 200 | 成功 | 正常处理数据 |
| 201 | 创建成功 | 获取新资源ID |
| 204 | 删除成功 | 无响应体 |
| 400 | 参数错误 | 检查请求参数 |
| 401 | 未授权 | 重新登录或刷新Token |
| 403 | 权限不足 | 提示用户权限不足 |
| 404 | 资源不存在 | 检查资源ID |
| 413 | 文件过大 | 压缩文件或分片上传 |
| 500 | 服务器错误 | 稍后重试 |

**错误响应格式**：
```json
{
  "error": "错误信息",
  "detail": "详细描述",
  "field_errors": {
    "title": ["此字段不能为空"],
    "email": ["请输入有效的邮箱"]
  }
}
```

## 🎨 响应格式说明

### 成功响应示例

```json
{
  "id": 1,
  "title": "反馈标题",
  "status": "submitted",
  "created_at": "2025-10-22T10:00:00Z"
}
```

### 列表响应示例

```json
{
  "count": 100,
  "next": "http://api.example.com/feedbacks/?page=2",
  "previous": null,
  "results": [
    { "id": 1, "title": "..." },
    { "id": 2, "title": "..." }
  ]
}
```

### 时间格式

所有时间字段使用 **ISO 8601** 格式（UTC 时区）：
- 格式：`YYYY-MM-DDTHH:mm:ss.sssZ`
- 示例：`2025-10-22T10:30:45.123Z`

前端需要转换为本地时间显示。

## 🌐 API 访问地址

- **开发环境**: `http://localhost:8000/api/v1/feedbacks/`
- **测试环境**: `http://test.your-domain.com/api/v1/feedbacks/`
- **生产环境**: `https://api.your-domain.com/api/v1/feedbacks/`

## 📱 在线文档

- **Swagger UI**: `/api/v1/docs/` - 交互式 API 测试
- **ReDoc**: `/api/v1/redoc/` - 美观的文档界面
- **OpenAPI Schema**: `/api/v1/schema/` - JSON 格式的 API 规范

## 🎯 数据流程图

### 反馈提交流程

```
用户填写表单
    ↓
调用 POST /feedbacks/
    ↓
系统创建反馈 (status: submitted)
    ↓
发送验证邮件（匿名用户）
    ↓
返回反馈ID
```

### 反馈处理流程

```
管理员查看反馈列表
    ↓
选择反馈查看详情
    ↓
添加回复 → 用户收到邮件通知
    ↓
修改状态 → 用户收到邮件通知
    ↓
反馈解决 (status: resolved)
    ↓
关闭反馈 (status: closed)
```

### 状态流转图

```
submitted (已提交)
    ↓
reviewing (审核中)
    ↓
confirmed (已确认) / rejected (已拒绝)
    ↓
in_progress (处理中)
    ↓
resolved (已解决)
    ↓
closed (已关闭)
```

## 💡 最佳实践

### 1. Token 管理
- 将 access_token 存储在 localStorage 或 Vuex
- 在请求拦截器中自动添加 Authorization 头
- Token 过期时自动使用 refresh_token 刷新

### 2. 错误处理
- 在响应拦截器中统一处理错误
- 401 错误：跳转登录页
- 403 错误：提示权限不足
- 500 错误：提示稍后重试

### 3. 性能优化
- 使用分页加载，避免一次加载大量数据
- 对搜索功能使用防抖（debounce）
- 图片使用懒加载
- 缓存常用数据（如软件列表）

### 4. 用户体验
- 显示加载状态
- 操作后给予明确反馈
- 表单验证提前在前端进行
- 使用乐观更新提升响应速度

## 📖 下一步

根据您的需求选择对应的文档：

- 📦 **管理软件** → [01_软件管理API.md](01_软件管理API.md)
- 💬 **处理反馈** → [02_反馈管理API.md](02_反馈管理API.md)
- 🔄 **互动功能** → [03_反馈互动API.md](03_反馈互动API.md)
- 📧 **邮件系统** → [04_邮件系统API.md](04_邮件系统API.md)
- 📊 **统计数据** → [05_统计与监控API.md](05_统计与监控API.md)
- 🚀 **对接指南** → [06_前端对接指南.md](06_前端对接指南.md)

## 💡 提示

- 所有 ID 字段都是整数类型
- 文件大小限制：10MB
- API 限流：每分钟 60 次请求
- 支持 CORS 跨域请求
- 建议使用 HTTPS 协议

---

**文档版本**: 1.0.0  
**最后更新**: 2025-10-22  
**适用项目**: Vue 3 前端应用
