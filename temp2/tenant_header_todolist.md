# Tenant Header Enforcement — TODO List

更新时间: 2025-08-27 10:28 (GMT+8)

## 概览
- 目标：在 member 与 CMS API 全面落地 X-Tenant-ID 强制规则、统一错误码、角色分流逻辑与缓存策略。
- 关键规则回顾：
  - 成员/匿名：CMS 必须携带 `X-Tenant-ID`；缺失/非法=4001；成员错租户=4003；成员请求中 query/body 的 `tenant_id` 一律忽略并记录 Warning。
  - 管理员/超管：禁止带头；管理员默认绑定租户，可用 `?tenant_id=` 指定；超管可用 `?tenant_id=` 指定，未指定时全量（沿用现有逻辑）。
  - CMS 成员/匿名 GET 响应需设置 `Vary: X-Tenant-ID`。
  - 错误码中文固定文案：4001 “缺少或非法的租户ID”；4003 “租户不匹配，或者没有权限”。

---

## 阶段一：实现准备
- [x] 文档完成并一致化（execution_plan / integration / tests）
- [ ] 明确开关变量：`FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER` 的默认值与环境覆盖策略
- [ ] 列出受影响模块清单与变更范围（代码清单与文件路径）

受影响模块（初版）：
- `common/viewsets.py` 中 `TenantModelViewSet`
- `common/utils/tenant_header.py`（新增）
- 中间件：`MemberHeaderEnforceMiddleware`（新增）
- 权限类：`RequireTenantHeaderForMember`（新增）
- `cms/views.py`（必要时对响应头添加 `Vary`）

验收：准备阶段完成的 MR/变更说明文档。

---

## 阶段二：公共工具与错误映射
- [x] 新建 `common/utils/tenant_header.py`
  - [x] `get_header_tenant_id(request) -> Optional[int]`
  - [x] `require_member_header_match(request)`：成员缺头/非法=4001；不匹配=4003
  - [x] 成员请求里 query/body 的租户参数记录 Warning 日志
- [x] 统一异常映射：新增 `TenantHeaderInvalidOrMissing` 与 `TenantMismatchOrNoPermission`，在 `custom_exception_handler` 固定中文文案与业务 code（4001/4003）
- [x] 日志格式与等级规范：已采用 Warning（忽略的 tenant_id）、Info（角色路由）

验收：单元测试覆盖工具函数与异常映射；日志断言。

---

## 阶段三：中间件与权限
- [ ] 中间件 `MemberHeaderEnforceMiddleware`
  - [ ] 成员/匿名在 CMS 路径下强制 `X-Tenant-ID`，缺失/非法=4001
  - [ ] 管理员/超管携带头=4001
  - [ ] 受 Feature Flag 控制
- [ ] 权限 `RequireTenantHeaderForMember`
  - [ ] 供成员端点在非 CMS 路径复用（如需要）

验收：中间件/权限的行为测试；Flag on/off 切换测试。

---

## 阶段四：`TenantModelViewSet` 改造（核心）
- [ ] `get_queryset()`：
  - [ ] CMS 路径：
    - [ ] 成员/匿名：必须头；缺头/非法=4001；成员错租户=4003；忽略 query/body 租户并 Warning
    - [ ] 管理员：禁止头；无参数默认绑定租户；`?tenant_id=` 指定
    - [ ] 超管：禁止头；`?tenant_id=` 指定；无参数=全量
  - [ ] 非 CMS 路径：保持现有行为，若与成员强制策略相关则统一错误码
- [ ] 写操作（create/update/destroy/_verify_tenant_ownership）同上分流与错误码
- [ ] 统一返回结构/异常处理

验收：视图集行为单测全绿；角色矩阵覆盖。

---

## 阶段五：CMS 响应头
- [ ] 成员/匿名下的 CMS GET 统一添加 `Vary: X-Tenant-ID`
- [ ] 回归检查 CDN/缓存配置，避免跨租户污染

验收：响应头断言与缓存策略验证。

---

## 阶段六：登录/注册/密码重置链路
- [ ] 登录：
  - [ ] 成员仅从 Header 获取租户；无头=4001；错头=4003
  - [ ] 管理员/超管禁止携带头；携带=4001
- [ ] 自注册与找回密码：
  - [ ] 成员请求忽略 body/query 租户，警告日志
  - [ ] Reset Verify/Confirm：member token 需校验与头一致

验收：三条链路端到端测试。

---

## 阶段七：测试与质量
- [ ] 覆盖三角色 + 匿名的全矩阵测试（参照 `temp2/member_tenant_header_tests.md`）
- [ ] 性能基线与回归压测
- [ ] 安全检查：错误信息不泄露敏感数据

验收：CI 全绿，性能回归达标。

---

## 阶段八：发布与监控
- [ ] Feature Flag 在测试环境开启，观察 24-48 小时
- [ ] 日志与告警监控（头缺失、错租户、被忽略的参数、管理员携头）
- [ ] 分阶段灰度至生产；问题回滚预案

验收：变更复盘与监控看板截图。

---

## 附：参考文档
- `temp2/member_tenant_header_execution_plan.md`
- `temp2/member_api_integration.md`
- `temp2/member_tenant_header_tests.md`
