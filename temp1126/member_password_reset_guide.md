# Member 密码重置功能接入指南

## 概述

Member 密码重置功能是一个独立的服务端渲染页面，支持多语言、多租户。前端应用只需通过链接跳转即可使用，无需自行实现密码重置流程。

## 基本信息

| 项目 | 说明 |
|------|------|
| **基础 URL** | `/api/v1/members/password-reset/` |
| **请求方式** | GET（显示页面）/ POST（提交表单） |
| **认证要求** | 无需认证（公开页面） |
| **多语言支持** | 通过 `Accept-Language` Header 自动切换 |

## 环境配置

### SITE_URL 配置（重要）

邮件中的重置链接需要包含完整的域名。系统通过以下逻辑生成链接：

1. **优先使用 `SITE_URL` 环境变量**（推荐）
2. 如未配置，则从 HTTP 请求的 `Host` 头获取

**配置方法**（在 `.env` 文件或环境变量中）：

```bash
# 生产环境（必须配置）
SITE_URL=https://api.yourdomain.com

# 开发/测试环境（可选，如需固定域名）
SITE_URL=http://192.168.1.100:8000
```

**示例**：

| SITE_URL 配置 | 生成的邮件链接 |
|--------------|---------------|
| `https://api.example.com` | `https://api.example.com/api/v1/members/password-reset/{token}/?tenant_id=3` |
| 未配置 | 根据用户访问的域名自动生成，如 `http://localhost:8000/...` |

> ⚠️ **生产环境必须配置 `SITE_URL`**，否则邮件链接可能使用 `localhost` 导致用户无法访问。

## URL 端点

### 1. 密码重置请求页面

**URL**: `GET /api/v1/members/password-reset/?tenant_id={tenant_id}`

用户输入邮箱地址，系统发送重置链接到邮箱。

**必需参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `tenant_id` | integer | ✅ | 租户ID，用于识别用户所属租户 |

**示例**:
```
https://your-domain.com/api/v1/members/password-reset/?tenant_id=3
```

---

### 2. 邮件发送成功页面

**URL**: `GET /api/v1/members/password-reset/sent/?tenant_id={tenant_id}`

显示邮件已发送的确认信息。

**必需参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `tenant_id` | integer | ✅ | 租户ID |

---

### 3. 设置新密码页面

**URL**: `GET /api/v1/members/password-reset/{token}/?tenant_id={tenant_id}`

用户通过邮件中的链接访问，设置新密码。

**必需参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `token` | string | ✅ | 密码重置令牌（64位随机字符串，在URL路径中） |
| `tenant_id` | integer | ✅ | 租户ID |

**示例**:
```
https://your-domain.com/api/v1/members/password-reset/abc123xyz.../?tenant_id=3
```

---

### 4. 重置完成页面

**URL**: `GET /api/v1/members/password-reset/complete/?tenant_id={tenant_id}`

密码重置成功后的确认页面。

**必需参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `tenant_id` | integer | ✅ | 租户ID |

---

## 多语言支持

### 支持的语言

| 语言代码 | 语言 |
|----------|------|
| `zh-hans` | 简体中文（默认） |
| `zh-hant` | 繁体中文 |
| `en` | English |
| `ja` | 日本語 |
| `ko` | 한국어 |
| `fr` | Français |

### 切换语言

通过 HTTP 请求头 `Accept-Language` 控制页面语言：

```bash
# 英文页面
curl -H "Accept-Language: en" \
  "https://your-domain.com/api/v1/members/password-reset/?tenant_id=3"

# 日文页面
curl -H "Accept-Language: ja" \
  "https://your-domain.com/api/v1/members/password-reset/?tenant_id=3"

# 繁体中文页面
curl -H "Accept-Language: zh-Hant" \
  "https://your-domain.com/api/v1/members/password-reset/?tenant_id=3"
```

浏览器会自动根据用户语言偏好发送 `Accept-Language` 头。

---

## 完整流程

```
┌─────────────────────────────────────────────────────────────────┐
│                         密码重置流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 用户访问请求页面                                              │
│     GET /api/v1/members/password-reset/?tenant_id=3             │
│                    ↓                                            │
│  2. 用户输入邮箱地址，提交表单                                     │
│     POST /api/v1/members/password-reset/?tenant_id=3            │
│                    ↓                                            │
│  3. 系统发送重置邮件，跳转到成功页面                                │
│     → /api/v1/members/password-reset/sent/?tenant_id=3          │
│                    ↓                                            │
│  4. 用户查收邮件，点击重置链接                                     │
│     GET /api/v1/members/password-reset/{token}/?tenant_id=3     │
│                    ↓                                            │
│  5. 用户输入新密码，提交表单                                       │
│     POST /api/v1/members/password-reset/{token}/?tenant_id=3    │
│                    ↓                                            │
│  6. 密码重置成功，跳转到完成页面                                    │
│     → /api/v1/members/password-reset/complete/?tenant_id=3      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 错误处理

### 缺少 tenant_id 参数

如果访问时未提供 `tenant_id` 参数，系统会显示错误页面：

```
无效请求
无法处理您的请求

可能的原因：
• 缺少必需参数 (tenant_id)
• 无效或未激活的租户
...
```

### 无效的租户

如果提供的 `tenant_id` 不存在或租户未激活，同样显示错误页面。

### 无效的重置链接

以下情况会显示链接无效错误：
- 链接已过期（超过1小时）
- 链接已被使用
- 链接格式不正确

---

## 安全特性

1. **令牌安全**: 64位随机字符串，难以猜测
2. **有效期限制**: 重置链接1小时后过期
3. **一次性使用**: 每个链接只能使用一次
4. **频率限制**: 同一IP每10分钟最多3次请求
5. **账号枚举保护**: 无论邮箱是否存在，都显示相同的成功消息
6. **密码强度要求**:
   - 至少8个字符
   - 不能是常用密码
   - 不能全为数字

---

## 前端集成示例

### HTML 链接

```html
<!-- 密码重置入口链接 -->
<a href="https://your-domain.com/api/v1/members/password-reset/?tenant_id=3">
  忘记密码？
</a>
```

### JavaScript (React)

```jsx
const ForgotPasswordLink = ({ tenantId }) => {
  const baseUrl = process.env.REACT_APP_API_URL;
  const resetUrl = `${baseUrl}/api/v1/members/password-reset/?tenant_id=${tenantId}`;
  
  return (
    <a href={resetUrl} target="_blank" rel="noopener noreferrer">
      忘记密码？
    </a>
  );
};
```

### JavaScript (Vue)

```vue
<template>
  <a :href="resetUrl" target="_blank" rel="noopener noreferrer">
    忘记密码？
  </a>
</template>

<script>
export default {
  props: ['tenantId'],
  computed: {
    resetUrl() {
      return `${process.env.VUE_APP_API_URL}/api/v1/members/password-reset/?tenant_id=${this.tenantId}`;
    }
  }
};
</script>
```

### iOS (Swift)

```swift
func openPasswordReset(tenantId: Int) {
    let baseURL = "https://your-domain.com"
    guard let url = URL(string: "\(baseURL)/api/v1/members/password-reset/?tenant_id=\(tenantId)") else {
        return
    }
    UIApplication.shared.open(url)
}
```

### Android (Kotlin)

```kotlin
fun openPasswordReset(tenantId: Int) {
    val baseUrl = "https://your-domain.com"
    val url = "$baseUrl/api/v1/members/password-reset/?tenant_id=$tenantId"
    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
    startActivity(intent)
}
```

### Flutter (Dart)

```dart
import 'package:url_launcher/url_launcher.dart';

void openPasswordReset(int tenantId) async {
  final baseUrl = 'https://your-domain.com';
  final url = '$baseUrl/api/v1/members/password-reset/?tenant_id=$tenantId';
  
  if (await canLaunch(url)) {
    await launch(url);
  }
}
```

---

## 邮件模板

重置邮件包含以下内容：

**邮件主题**: `密码重置 - {租户名称}`

**邮件正文**:
- 用户姓名问候
- 重置原因说明
- 重置按钮/链接
- 链接过期时间
- 安全提示（如果未请求重置，请忽略）
- 发件方信息

邮件内容也支持多语言，根据用户请求时的语言设置发送对应语言的邮件。

---

## 技术细节

### 表单字段

**请求页面表单**:
| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `email` | email | ✅ | 用户注册邮箱 |
| `tenant_id` | hidden | ✅ | 从URL参数自动填充 |

**设置密码表单**:
| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `new_password` | password | ✅ | 新密码 |
| `new_password_confirm` | password | ✅ | 确认新密码 |

### HTTP 方法

- `GET`: 显示页面
- `POST`: 提交表单（自动处理 CSRF 保护）

### 响应类型

- 成功: HTTP 302 重定向到下一步
- 表单错误: HTTP 200 + 错误提示
- 参数错误: HTTP 200 + 错误页面

---

## 测试命令

```bash
# 测试请求页面（中文）
curl -s "http://localhost:8000/api/v1/members/password-reset/?tenant_id=3" | head -20

# 测试请求页面（英文）
curl -s -H "Accept-Language: en" \
  "http://localhost:8000/api/v1/members/password-reset/?tenant_id=3" | head -20

# 测试缺少 tenant_id 的错误处理
curl -s "http://localhost:8000/api/v1/members/password-reset/" | head -20

# 测试无效租户
curl -s "http://localhost:8000/api/v1/members/password-reset/?tenant_id=99999" | head -20
```

---

## 常见问题

### Q: 用户没有收到重置邮件怎么办？
A: 
1. 检查垃圾邮件文件夹
2. 确认邮箱地址正确
3. 确认用户属于指定的租户
4. 检查服务器邮件配置

### Q: 重置链接打不开怎么办？
A:
1. 链接可能已过期（1小时有效期）
2. 链接可能已被使用
3. 确保完整复制链接，没有截断

### Q: 如何自定义页面样式？
A: 当前使用 Bootstrap 5 样式。如需自定义，可以：
1. 修改 `templates/members/password_reset_*.html` 模板
2. 修改 `templates/base.html` 基础模板
3. 添加自定义 CSS

### Q: 如何修改重置链接有效期？
A: 在 `users/views/member_password_reset_views.py` 中修改：
```python
expires_at = timezone.now() + timezone.timedelta(hours=1)  # 修改此处
```

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2024-11-26 | 初始版本，支持6种语言、租户必填 |
