# Member Tenant Header — Test Plan

更新时间: 2025-08-26 20:15 (GMT+8)

## 1. 成员任意 API（/api/v1/members/* 及其他）
- 缺少头：400, code=4001
- 头与用户租户不一致：403, code=4003
- 正确头：200

## 2. 登录
- 管理员无头登录成功（200）
- 管理员带头：400, code=4001
- 成员无头：400, code=4001
- 成员仅头，无 body tenant_id：200
- 成员同时带 body tenant_id：400, code=4001

## 3. 成员注册
- 无头：400, code=4001
- 仅头：201
- body 携带 tenant_id：400, code=4001

## 4. 密码重置
- Request：
  - account_type=member + 无头：4001
  - account_type=member + 带头：200
  - account_type=user + 带头：4001
  - account_type=user + 无头：200
- Verify：
  - member token + 无头：4001
  - member token + 错头：4003
  - member token + 正确头：200
  - user token + 带头：4001
  - user token + 无头：200
- Confirm：同 Verify

## 5. CMS 访问（成员/匿名/管理员/超管）
- 成员：
  - 无头：400, code=4001（"缺少或非法的租户ID"）
  - 头与自身租户不一致：403, code=4003（"租户不匹配，或者没有权限"）
  - 正确头：200
  - query/body 出现 tenant_id：不影响结果，仅记录 Warning 日志
- 匿名：
  - 无头：400, code=4001（"缺少或非法的租户ID"）
  - 带头：200（响应建议携带 Vary: X-Tenant-ID）
- 管理员：
  - 携带头：400, code=4001
  - 无任何租户参数：使用绑定租户返回 200
  - ?tenant_id= 他租户：200（按参数指定）
- 超级管理员：
  - 携带头：400, code=4001
  - ?tenant_id= 指定租户：200
  - 无参数：返回全量 200

## 6. 管理员/超管调用其他 API（非 CMS）
- 任意 API 若带头：4001（全局规则）
- 无头：遵循各自权限规则（与本变更无直接关系）

## 7. 回归与边界
- query/body 中的 tenant_id 在成员请求下被忽略（记录 Warning），不触发 400。
- 非整数/不存在的 X-Tenant-ID：4001（"缺少或非法的租户ID"）
- 子账号（member.parent != None）照常强制头；其登录受限按现有业务规则验证。

## 8. 性能与安全
- 压测代表性接口，确保中间件开销可接受。
- 确保错误响应无敏感信息泄露。
