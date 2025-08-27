# Django Middleware 调用顺序（线框图）

更新时间: 2025-08-27 11:55 (GMT+8)
来源: `core/settings.py` -> `MIDDLEWARE`

- 请求方向（Inbound）按列表自上而下依次调用。
- 响应方向（Outbound）按列表自下而上反向返回。

---

## 顺序清单（请求方向）
1. `whitenoise.middleware.WhiteNoiseMiddleware`
2. `django.middleware.security.SecurityMiddleware`
3. `django.contrib.sessions.middleware.SessionMiddleware`
4. `corsheaders.middleware.CorsMiddleware`
5. `django.middleware.common.CommonMiddleware`
6. `django.middleware.csrf.CsrfViewMiddleware`
7. `django.contrib.auth.middleware.AuthenticationMiddleware`
8. `common.middleware.api_auth_middleware.APIAuthMiddleware`
9. `common.middleware.member_header_enforce_middleware.MemberHeaderEnforceMiddleware`
10. `django.contrib.messages.middleware.MessageMiddleware`
11. `django.middleware.clickjacking.XFrameOptionsMiddleware`
12. `common.middleware.tenant_middleware.TenantMiddleware`
13. `common.middleware.enhanced_api_logging_middleware.EnhancedAPILoggingMiddleware`
14. `common.middleware.browser_console_logging_middleware.BrowserConsoleLoggingMiddleware`
15. `common.middleware.response_standardization_middleware.ResponseStandardizationMiddleware`

---

## 线框图（请求 -> 视图）
```
[WhiteNoise]
   ↓
[Security]
   ↓
[Session]
   ↓
[CORS]
   ↓
[Common]
   ↓
[CSRF]
   ↓
[Auth]
   ↓
[APIAuth]
   ↓
[MemberHeaderEnforce]
   ↓
[Messages]
   ↓
[XFrameOptions]
   ↓
[Tenant]
   ↓
[EnhancedAPILogging]
   ↓
[BrowserConsoleLogging]
   ↓
[ResponseStandardization]
   ↓
      [View / DRF ViewSet]
```

## 线框图（视图 -> 响应）
```
      [View / DRF ViewSet]
   ↑
[ResponseStandardization]
   ↑
[BrowserConsoleLogging]
   ↑
[EnhancedAPILogging]
   ↑
[Tenant]
   ↑
[XFrameOptions]
   ↑
[Messages]
   ↑
[MemberHeaderEnforce]
   ↑
[APIAuth]
   ↑
[Auth]
   ↑
[CSRF]
   ↑
[Common]
   ↑
[CORS]
   ↑
[Session]
   ↑
[Security]
   ↑
[WhiteNoise]
```

---

## 关键职责与位置约束
- 【WhiteNoise】静态文件优化，最靠前处理静态资源。
- 【Security】安全相关 headers 与安全策略。
- 【Session】启用会话支持，为后续认证提供依赖。
- 【CORS】跨域处理，需在较前位置。
- 【Common】通用请求处理（如 APPEND_SLASH）。
- 【CSRF】CSRF 校验（对 Cookie/Session 场景有效）。
- 【Auth】Django 认证，将用户注入 `request.user`。
- 【APIAuth】自定义 API 认证（如 JWT），依赖 `Auth` 之后。
- 【MemberHeaderEnforce】成员/匿名 Header 策略校验；必须位于 `TenantMiddleware` 之前：
  - 成员/匿名：要求 `X-Tenant-ID` 且成员需匹配
  - 管理员/超管：禁止携带 `X-Tenant-ID`
  - 相关源码：`common/middleware/member_header_enforce_middleware.py`
- 【Messages】消息框架。
- 【XFrameOptions】点击劫持防护。
- 【Tenant】解析并设置租户上下文；依赖于前置 Header 校验已完成。
- 【EnhancedAPILogging】增强型 API 日志记录。
- 【BrowserConsoleLogging】浏览器控制台辅助日志（调试）。
- 【ResponseStandardization】统一响应格式，需最末尾以包裹所有响应。

---

## 相关设置文件
- 中间件顺序：`core/settings.py` -> `MIDDLEWARE`
- 成员 Header 强制开关：`FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER`（同文件）

---

## 备注
- 请求方向：上 → 下；响应方向：下 → 上（反向）。
- `MemberHeaderEnforceMiddleware` 建议提供“多前缀/豁免路径”能力，以避免对公开文档/探活等路径造成影响。
