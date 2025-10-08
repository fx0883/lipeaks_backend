# 租户ID（X-Tenant-ID）全局使用指南

本文面向后端、前端与测试工程师，系统性说明在本项目中如何“正确、统一、可观测”地使用租户ID（X-Tenant-ID）。

- 适用代码位置：
  - 中间件：`common/middleware/member_header_enforce_middleware.py`、`common/middleware/tenant_middleware.py`
  - 工具：`common/utils/tenant_header.py`
  - 异常：`common/exceptions/__init__.py`
  - 响应规范：`common/middleware/response_standardization_middleware.py`

- 术语说明：
  - 成员（member）：普通业务用户
  - 租户管理员（tenant admin）：某租户的管理员
  - 超级管理员（super admin）：平台级管理员

---

## 1. 总体原则（必须遵守）

- X-Tenant-ID 是成员/匿名请求的单一可信来源。
- 对成员/匿名：
  - 必须提供合法的 `X-Tenant-ID` 请求头；
  - 若成员已登录，其 `X-Tenant-ID` 必须与成员自身的租户匹配，否则 4003。
- 对租户管理员与超级管理员：
  - 在 CMS 业务接口上禁止携带 `X-Tenant-ID`；
  - 管理员默认使用其绑定租户；超级管理员按场景由后续逻辑决定（支持跨租户操作）。
- Query/body 中的 `tenant_id` 一律忽略（但会记录 Warning 日志，便于排查滥用）。
- 文档与认证相关路径应排除强制校验（示例见“路径策略”）。

---

## 2. 路径策略（哪些需要/不需要租户头）

- 需要租户头（成员/匿名强制校验）：
  - 业务 API 前缀：`/api/v1/`（结合具体模块由中间件判断）。
- 不需要租户头（中间件明确跳过）：
  - 静态资源：`/static/`、`/media/`
  - 文档与Schema：`/api/v1/schema/`、`/api/v1/docs/`、`/api/v1/redoc/`
  - Django Admin：`/admin/`
  - 认证相关（建议排除）：`/api/v1/auth/`（登录、注册、重置密码等）

注意：当前仓库中 `MemberHeaderEnforceMiddleware` 已排除了 docs 路径；如需排除 auth，请在该文件中加入：

```python
# common/middleware/member_header_enforce_middleware.py
if path.startswith('/api/v1/auth/'):
    return None
```

---

## 3. 角色与校验规则

- 成员/匿名：
  - 必须提供 `X-Tenant-ID`；
  - 对成员：`X-Tenant-ID` 必须等于成员绑定的租户ID，否则 4003；
  - 对匿名：只要 `X-Tenant-ID` 合法即可通过；
- 租户管理员：
  - 禁止携带 `X-Tenant-ID`，由后续逻辑使用其绑定租户；
- 超级管理员：
  - 禁止携带 `X-Tenant-ID` 访问 CMS；
  - 跨租户能力由后续业务逻辑决定（如通过专用参数或后台操作）。

---

## 4. 中间件与工具如何协作

- `MemberHeaderEnforceMiddleware`（只做“策略校验”，不落地上下文）
  - 文件：`common/middleware/member_header_enforce_middleware.py`
  - 行为：
    - 早期拦截不合规请求（4001/4003），避免进入业务层；
    - 对成员/匿名强制要求 `X-Tenant-ID`；管理员/超管禁止携带；
    - 忽略 query/body 的 `tenant_id` 并记录 Warning；
  - 开关：`FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER`（settings）

- `TenantMiddleware`（负责“落地租户上下文”）
  - 文件：`common/middleware/tenant_middleware.py`
  - 行为：
    - 依据 `X-Tenant-ID`、用户绑定租户、以及用户类型，计算 `request.tenant_id`；
    - 设置线程级租户上下文 `set_current_tenant()` 供后续 ORM/业务使用；
    - 提供 `X-Debug-Log: true` 时，错误响应会携带 `debug_logs`，便于调试；

- `tenant_header.py`（工具方法）
  - `get_header_tenant_id(request)`：可靠解析并校验头部；
  - `require_member_header_match(request)`：实现“成员/匿名强制头+成员匹配”的复合规则。

---

## 5. 错误码与响应格式

- 统一响应由 `ResponseStandardizationMiddleware` 保证：

```json
{
  "success": false,
  "code": 4001,
  "message": "缺少或非法的租户ID",
  "data": null
}
```

- 常见错误：
  - 4001 `TenantHeaderInvalidOrMissing`：缺少或非法的租户ID；
  - 4003 `TenantMismatchOrNoPermission`：成员的租户与头不匹配，或没有权限；
  - 其他业务错误会映射为统一结构。

---

## 6. 前后端集成示例

### 6.1 前端（Axios拦截器）

```ts
// axios.ts
import axios from 'axios'

const instance = axios.create({ baseURL: '/api/v1' })

instance.interceptors.request.use((config) => {
  const tid = sessionStorage.getItem('tenant_id') // 或从用户上下文/选择器获取
  const isAuthPath = (config.url || '').startsWith('/auth/')
  // 对非认证路径附带 X-Tenant-ID
  if (!isAuthPath && tid) {
    config.headers['X-Tenant-ID'] = String(tid)
  }
  return config
})

export default instance
```

### 6.2 后端（cURL 示例）

- 业务接口（必须带 X-Tenant-ID）：

```bash
curl -X GET 'http://localhost:8000/api/v1/cms/articles/' \
  -H 'X-Tenant-ID: 1' -H 'Accept: application/json'
```

- 认证接口（建议排除校验，不需要带 X-Tenant-ID）：

```bash
curl -X POST 'http://localhost:8000/api/v1/auth/login/' \
  -H 'Content-Type: application/json' \
  --data '{"username":"u","password":"p"}'
```

---

## 7. 测试编写建议（pytest/DRF）

- DRF APIClient：

```python
from rest_framework.test import APIClient

client = APIClient()
client.credentials(HTTP_X_TENANT_ID='1')  # 非认证路径可省略
resp = client.get('/api/v1/cms/articles/')
```

- 认证视图测试：

```python
resp = client.post('/api/v1/auth/login/', {"username":"u","password":"p"}, format='json')
```

- 成员匹配断言：

```python
client.force_authenticate(user=member_user)
client.credentials(HTTP_X_TENANT_ID=str(member_user.tenant_id))
```

---

## 8. 调试与排错指南

- 打开调试日志：
  - 查看中间件入口日志：所有中间件在 `process_request/response` 已记录：`[进入中间件] ... - 处理请求: {path}`
- 返回 debug_logs：
  - 在调用时添加请求头 `X-Debug-Log: true`，部分中间件在错误响应中会附带详细 `debug_logs` 字段；
- 常见问题：
  - 登录接口 4001：请确认 `MemberHeaderEnforceMiddleware` 已对 `/api/v1/auth/` 排除；
  - 成员跨租户访问 4003：检查 `X-Tenant-ID` 是否与成员绑定租户一致；
  - 前端误把 `tenant_id` 放 query/body：会被忽略并产生 Warning 日志；

---

## 9. 最佳实践清单（Checklist）

- 前端：
  - 仅在业务接口为请求设置 `X-Tenant-ID`；
  - 认证/文档/静态路径不加；
  - 租户切换时更新会话存储中的 `tenant_id`；
- 后端：
  - `MemberHeaderEnforceMiddleware` 放在 `TenantMiddleware` 之前；
  - 为 `/api/v1/auth/`、文档、静态、Admin 路径加“跳过”条件；
  - 不在视图里手动读取 query/body 的 `tenant_id`；
- 运维：
  - 正确设置 `FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER`；
  - 观察日志与 `debug_logs`，配合 4001/4003 迅速定位问题；

---

## 10. 版本与迁移建议

- 新老前端并存期：后端保留 Warning 日志，便于识别仍从 query/body 传 `tenant_id` 的旧客户端；
- 渐进式灰度：
  1) 先在测试环境启用强制策略；
  2) 收集日志并修正客户端；
  3) 最后在生产开启开关并加监控。

---

## 11. 附录：相关代码入口

- `MemberHeaderEnforceMiddleware.process_request()`
- `TenantMiddleware.process_request()` / `process_response()`
- `tenant_header.get_header_tenant_id()` / `require_member_header_match()`
- `common/exceptions/__init__.py` 中的 `TenantHeaderInvalidOrMissing` 与 `TenantMismatchOrNoPermission`
- `ResponseStandardizationMiddleware.process_response()`

如需扩展请在本文件追加章节，并同步更新上述中间件的路径排除列表（如新增开放接口）。
