# 邮件系统 API 使用文档

## 📧 模块概述

邮件系统模块提供邮件模板管理和邮件发送日志查询功能。

**API 数量**: 8 个  
**权限要求**: 租户管理员  
**主要用途**: 自定义邮件模板、追踪邮件发送状态

## 📑 API 列表

### 邮件模板管理 (6个API)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/email-templates/` | 获取模板列表 | 管理员 |
| POST | `/email-templates/` | 创建模板 | 管理员 |
| GET | `/email-templates/{id}/` | 获取模板详情 | 管理员 |
| PUT | `/email-templates/{id}/` | 完整更新模板 | 管理员 |
| PATCH | `/email-templates/{id}/` | 部分更新模板 | 管理员 |
| DELETE | `/email-templates/{id}/` | 删除模板 | 管理员 |

### 邮件日志查询 (2个API)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/email-logs/` | 获取邮件日志列表 | 管理员 |
| GET | `/email-logs/{id}/` | 获取邮件详情 | 管理员 |

---

## 邮件模板管理

### 模板类型说明

| 模板类型 | 代码 | 触发时机 | 用途 |
|---------|------|---------|------|
| 反馈回复通知 | reply | 管理员回复反馈时 | 通知用户查看回复 |
| 状态变更通知 | status_change | 反馈状态改变时 | 通知用户处理进度 |
| 邮箱验证 | verification | 匿名用户提交反馈时 | 验证用户邮箱 |
| 每日摘要 | summary | 定时任务 | 汇总当天反馈 |

### 模板变量

**所有模板可用的变量**:

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `{{user_name}}` | 用户名 | 张三 |
| `{{contact_name}}` | 联系人姓名 | 李四 |
| `{{feedback_id}}` | 反馈ID | 123 |
| `{{feedback_title}}` | 反馈标题 | 登录问题 |
| `{{software_name}}` | 软件名称 | CRM系统 |
| `{{version}}` | 版本号 | v2.1.0 |

**回复通知专用变量**:

| 变量 | 说明 |
|------|------|
| `{{reply_content}}` | 回复内容 |
| `{{reply_user}}` | 回复者姓名 |

**状态变更专用变量**:

| 变量 | 说明 |
|------|------|
| `{{old_status}}` | 旧状态 |
| `{{new_status}}` | 新状态 |
| `{{change_reason}}` | 变更原因 |

**验证邮件专用变量**:

| 变量 | 说明 |
|------|------|
| `{{verification_link}}` | 验证链接 |
| `{{verification_token}}` | 验证令牌 |

### 1. 获取邮件模板列表

**接口**: `GET /email-templates/`

**返回字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 模板ID |
| template_type | string | 模板类型 |
| name | string | 模板名称 |
| subject | string | 邮件主题 |
| body_template | string | 邮件正文模板（HTML） |
| is_active | boolean | 是否启用 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

### 2. 创建邮件模板

**接口**: `POST /email-templates/`

**请求字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| template_type | string | ✅ | reply\|status_change\|verification\|summary |
| name | string | ✅ | 模板名称 |
| subject | string | ✅ | 邮件主题（可含变量） |
| body_template | string | ✅ | 邮件正文HTML（可含变量） |
| is_active | boolean | ❌ | 是否启用（默认true） |

**模板示例**:

**主题示例**:
```
【{{software_name}}】您的反馈收到新回复
```

**正文示例**:
```html
<html>
<body>
  <h2>Hi {{user_name}},</h2>
  <p>您的反馈 <strong>{{feedback_title}}</strong> 收到了新回复：</p>
  <blockquote>{{reply_content}}</blockquote>
  <p>回复者：{{reply_user}}</p>
  <p><a href="http://your-domain.com/feedbacks/{{feedback_id}}">查看详情</a></p>
</body>
</html>
```

**使用注意**:
- 变量使用 `{{变量名}}` 格式
- 主题和正文都支持变量替换
- 建议使用 HTML 格式以获得更好的显示效果
- 同一类型可以创建多个模板，系统使用最新激活的

---

### 3-6. 模板其他操作

**查看模板** (`GET /email-templates/{id}/`)
- 查看完整的模板内容
- 用于编辑前预览

**更新模板** (`PATCH /email-templates/{id}/`)
- 修改主题、正文
- 启用/禁用模板

**删除模板** (`DELETE /email-templates/{id}/`)
- 删除自定义模板
- 系统会回退使用默认模板

---

## 邮件日志查询

### 7. 获取邮件日志列表

**接口**: `GET /email-logs/`

**用途**: 查看邮件发送历史，追踪邮件状态。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| feedback | integer | 按反馈ID筛选 |
| status | string | pending\|sending\|sent\|failed\|bounced |
| email_type | string | reply\|status_change\|verification\|summary |
| page | integer | 页码 |
| page_size | integer | 每页数量 |

**邮件状态说明**:

| 状态 | 说明 | 处理建议 |
|------|------|---------|
| pending | 待发送 | 等待 Celery 处理 |
| sending | 发送中 | 正在发送 |
| sent | 已发送 | 发送成功 |
| failed | 发送失败 | 检查错误信息，考虑重发 |
| bounced | 退信 | 邮箱地址无效 |

**返回字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 日志ID |
| feedback | integer | 关联反馈ID |
| feedback_title | string | 反馈标题 |
| recipient_email | string | 收件人邮箱 |
| recipient_name | string | 收件人姓名 |
| email_type | string | 邮件类型 |
| status | string | 发送状态 |
| subject | string | 邮件主题 |
| sent_at | datetime | 发送时间 |
| error_message | string/null | 错误信息（如有） |
| retry_count | integer | 重试次数 |
| created_at | datetime | 创建时间 |

---

### 8. 获取邮件日志详情

**接口**: `GET /email-logs/{id}/`

**返回额外字段**:
- `body`: 完整的邮件正文HTML
- `feedback_detail`: 关联反馈的详细信息

**用途**:
- 查看实际发送的邮件内容
- 排查邮件发送问题
- 确认变量替换是否正确

---

## 邮件系统工作流程

### 邮件发送流程

```
触发事件（回复/状态变更）
    ↓
获取对应类型的激活模板
    ↓
替换模板中的变量
    ↓
创建邮件日志记录（status: pending）
    ↓
Celery 异步任务发送邮件
    ↓
更新日志状态（sending → sent）
    ↓
发送成功：status = sent
    ↓
发送失败：status = failed（自动重试）
```

### 邮件自动发送触发条件

| 事件 | 邮件类型 | 收件人 | 条件 |
|------|---------|--------|------|
| 匿名提交反馈 | verification | 提交者邮箱 | 总是发送 |
| 管理员添加公开回复 | reply | 反馈提交者 | email_notification_enabled=true |
| 反馈状态变更 | status_change | 反馈提交者 | email_notification_enabled=true |
| 每日摘要（定时） | summary | 管理员 | 配置启用时 |

---

## 管理后台功能

### 邮件模板管理页面

**功能列表**:
- 查看所有邮件模板
- 创建新模板
- 编辑现有模板
- 启用/禁用模板
- 预览模板效果
- 删除自定义模板

**建议功能**:
1. **模板编辑器**: 富文本或代码编辑器
2. **变量帮助**: 显示可用变量列表
3. **预览功能**: 实时预览邮件效果
4. **测试发送**: 向指定邮箱发送测试邮件

### 邮件日志查询页面

**功能列表**:
- 查看所有发送日志
- 按状态筛选（成功/失败）
- 按反馈筛选
- 按时间范围筛选
- 查看邮件详情
- 查看失败原因

**统计面板**:
- 今日发送总数
- 发送成功率
- 失败邮件数量
- 最近错误列表

---

## 故障排查

### 邮件发送失败常见原因

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| SMTP连接失败 | SMTP配置错误 | 检查 EMAIL_HOST 等配置 |
| 邮箱地址无效 | 用户邮箱格式错误 | 验证邮箱格式 |
| 被拒绝 | 邮件内容被判定为垃圾邮件 | 优化邮件内容 |
| 超时 | 网络问题 | 检查网络连接 |
| 退信 | 邮箱不存在 | 更新收件人邮箱 |

### 邮件日志监控建议

**每日检查**:
- 查看发送失败的邮件
- 分析失败原因
- 手动重发重要邮件

**指标监控**:
- 邮件发送成功率（目标 >98%）
- 平均发送时间
- 失败邮件占比

---

## 注意事项

### 邮件模板
1. **变量语法**: 必须使用 `{{变量名}}` 格式
2. **HTML格式**: 建议使用标准HTML，避免复杂CSS
3. **响应式**: 考虑移动端邮件客户端显示
4. **测试**: 修改后务必测试

### 邮件日志
1. **只读**: 邮件日志无法修改或删除
2. **保留期**: 默认保留90天
3. **隐私**: 注意保护用户邮箱隐私
4. **性能**: 日志量大时使用分页

### 邮件发送
1. **异步**: 邮件通过 Celery 异步发送
2. **重试**: 失败自动重试最多3次
3. **降级**: Redis不可用时同步发送
4. **限流**: 避免短时间发送大量邮件

---

**下一步**: [05_统计与监控API.md](05_统计与监控API.md)
