# Feedback 提交页面接入指南

## 概述

Feedback 提交页面是一个服务端渲染的 HTML 表单页面，允许用户（匿名或已认证的 Member）提交反馈信息。该页面支持多语言国际化，通过 `Accept-Language` HTTP Header 自动切换语言。

## 页面 URL

```
GET /api/v1/feedbacks/submit/
```

## URL 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `tenant_id` | integer | ✅ 是 | 租户 ID，必须是有效且激活状态的租户 |
| `application_id` | integer | ✅ 是 | 应用 ID，必须是该租户下有效且激活的应用 |
| `member_token` | string | ❌ 否 | Member 用户的 JWT Token，用于认证用户身份 |

## 完整 URL 示例

### 匿名用户访问

```
https://your-domain.com/api/v1/feedbacks/submit/?tenant_id=3&application_id=6
```

### 认证用户访问

```
https://your-domain.com/api/v1/feedbacks/submit/?tenant_id=3&application_id=6&member_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 多语言支持

页面通过 `Accept-Language` HTTP Header 自动检测用户语言偏好。

### 支持的语言

| 语言 | Accept-Language 值 | 示例 |
|------|---------------------|------|
| 简体中文 | `zh-hans`, `zh-Hans-CN`, `zh-CN` | 默认语言 |
| 繁體中文 | `zh-hant`, `zh-Hant-TW`, `zh-TW` | |
| English | `en`, `en-US`, `en-GB` | |
| 日本語 | `ja`, `ja-JP` | |
| 한국어 | `ko`, `ko-KR` | |
| Français | `fr`, `fr-FR` | |

### 语言切换示例

浏览器会自动发送 `Accept-Language` header。如果需要手动指定语言：

```bash
# 英文页面
curl -H "Accept-Language: en" \
  "http://localhost:8000/api/v1/feedbacks/submit/?tenant_id=3&application_id=6"

# 日文页面
curl -H "Accept-Language: ja" \
  "http://localhost:8000/api/v1/feedbacks/submit/?tenant_id=3&application_id=6"

# 韩文页面
curl -H "Accept-Language: ko" \
  "http://localhost:8000/api/v1/feedbacks/submit/?tenant_id=3&application_id=6"
```

## 表单字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | text | ✅ 是 | 反馈标题，最大200字符 |
| `description` | textarea | ✅ 是 | 反馈详细描述 |
| `feedback_type` | select | ✅ 是 | 反馈类型 |
| `priority` | select | ✅ 是 | 优先级 |
| `contact_email` | email | ❌ 否 | 联系邮箱（匿名用户可见） |
| `contact_name` | text | ❌ 否 | 联系人姓名（匿名用户可见） |

### 反馈类型 (feedback_type)

| 值 | 中文 | English | 日本語 |
|----|------|---------|--------|
| `bug` | Bug 报告 | Bug Report | バグ報告 |
| `feature` | 功能请求 | Feature Request | 機能リクエスト |
| `improvement` | 改进建议 | Improvement | 改善提案 |
| `question` | 问题咨询 | Question | 質問 |
| `other` | 其他 | Other | その他 |

### 优先级 (priority)

| 值 | 中文 | English | 日本語 |
|----|------|---------|--------|
| `critical` | 紧急 | Critical | 緊急 |
| `high` | 高 | High | 高 |
| `medium` | 中 | Medium | 中 |
| `low` | 低 | Low | 低 |

## 认证用户 vs 匿名用户

### 匿名用户

- 显示 `contact_email` 和 `contact_name` 输入框
- 用户可选择性填写联系方式

### 认证用户 (member_token)

- 自动填充 Member 的邮箱和姓名
- 隐藏联系信息输入框
- 页面显示当前登录用户信息

## 错误处理

### 参数缺失

```
缺少必需参数：tenant_id 和 application_id
```

显示条件：URL 未提供 `tenant_id` 或 `application_id` 参数

### 租户无效

```
租户不存在或已停用。
```

显示条件：
- `tenant_id` 对应的租户不存在
- 租户状态不是 `active`
- 租户已被软删除

### 应用无效

```
应用不存在或已停用。
```

显示条件：
- `application_id` 对应的应用不存在
- 应用不属于指定的租户
- 应用未激活 (`is_active=False`)
- 应用已被软删除

### Token 无效

如果 `member_token` 无效或过期，页面会静默降级为匿名模式，不会显示错误。

## 前端集成指南

### 方式一：直接链接

在应用中提供反馈入口链接：

```html
<a href="https://backend.example.com/api/v1/feedbacks/submit/?tenant_id=3&application_id=6" 
   target="_blank">
   提交反馈
</a>
```

### 方式二：带认证的链接

```javascript
const feedbackUrl = new URL('https://backend.example.com/api/v1/feedbacks/submit/');
feedbackUrl.searchParams.set('tenant_id', tenantId);
feedbackUrl.searchParams.set('application_id', applicationId);

// 如果用户已登录，附加 token
if (memberToken) {
  feedbackUrl.searchParams.set('member_token', memberToken);
}

window.open(feedbackUrl.toString(), '_blank');
```

### 方式三：iOS/macOS 应用

```swift
import Foundation

func openFeedbackPage(tenantId: Int, applicationId: Int, memberToken: String? = nil) {
    var components = URLComponents(string: "https://backend.example.com/api/v1/feedbacks/submit/")!
    
    var queryItems = [
        URLQueryItem(name: "tenant_id", value: String(tenantId)),
        URLQueryItem(name: "application_id", value: String(applicationId))
    ]
    
    if let token = memberToken {
        queryItems.append(URLQueryItem(name: "member_token", value: token))
    }
    
    components.queryItems = queryItems
    
    if let url = components.url {
        // iOS
        UIApplication.shared.open(url)
        // macOS
        // NSWorkspace.shared.open(url)
    }
}
```

### 方式四：Android 应用

```kotlin
fun openFeedbackPage(tenantId: Int, applicationId: Int, memberToken: String? = null) {
    val uri = Uri.parse("https://backend.example.com/api/v1/feedbacks/submit/")
        .buildUpon()
        .appendQueryParameter("tenant_id", tenantId.toString())
        .appendQueryParameter("application_id", applicationId.toString())
        .apply {
            memberToken?.let { appendQueryParameter("member_token", it) }
        }
        .build()
    
    val intent = Intent(Intent.ACTION_VIEW, uri)
    startActivity(intent)
}
```

## 提交成功

表单提交成功后，用户会被重定向到成功页面：

```
/api/v1/feedbacks/submit/success/
```

该页面显示：
- 成功确认信息
- 后续处理说明
- 预计响应时间

## 技术细节

### HTTP 方法

- `GET` - 显示表单页面
- `POST` - 提交表单数据

### CSRF 保护

页面使用 Django CSRF Token 保护，表单中自动包含隐藏的 `csrfmiddlewaretoken` 字段。

### 响应类型

- Content-Type: `text/html; charset=utf-8`

### 数据存储

提交的反馈会创建 `Feedback` 记录，包含：
- 租户关联
- 应用关联
- 反馈内容
- 用户 IP 地址
- User-Agent 信息
- 初始状态：`submitted`

## 常见问题

### Q: 如何获取有效的 tenant_id 和 application_id？

A: 这些 ID 应由后台管理员提供，或通过相关 API 查询获取。

### Q: member_token 从哪里获取？

A: Member 用户登录后会获得 JWT Token，该 Token 可用作 `member_token` 参数。

### Q: 页面语言不正确怎么办？

A: 检查浏览器的语言设置，或在请求中明确设置 `Accept-Language` header。

### Q: 可以在 iframe 中嵌入吗？

A: 默认情况下可能受 X-Frame-Options 限制，如需嵌入请联系后台配置。
