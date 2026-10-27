# Changelog

All notable changes to the `lipeaks_backend` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2026.10.15] - 代码审计治理结项 (Code Audit & Remediation Milestone)

本版本为系统性全维度代码审计（Phase 0）及深度稳定性工程治理（Phase 1 ~ Phase 4）的最终结项版本。全量修复 42 项核心缺陷，自动化测试用例从 302 项扩充至 638 项（Pytest 收集 666 项），测试通过率达成 100%，系统整体健康度跃升至 A+ 生产级就绪标准。

### Security

- **[SEC-01] 消除公开注册强制提权漏洞**：
  - 移除 `User.save()` 中无条件的 `is_admin=True` 赋值；
  - 封堵公开注册接口允许传入 `is_admin`、`is_staff`、`is_superuser` 及 `tenant_id` 的越权漏洞；
  - 补充 `users/tests/test_sec01_adversarial.py` 严格防御对抗测试。
- **[SEC-02] 加固反馈工单与附件操作访问控制**：
  - 废除 `feedbacks/views/` 各视图的 `AllowAny` 类级别全量放行，拆分为公共只读与写操作隔离；
  - 反馈工单回复（`FeedbackReplyViewSet`）与附件上传（`FeedbackAttachmentViewSet`）强制要求 `IsAuthenticated` 认证守卫。
- **[SEC-04] 防护通知系统 IDOR 水平越权**：
  - 在 `notifications/member_views.py` 中重构通知详情、标为已读与批量已读逻辑；
  - 废除无限定的全局主键直接检索，强制限定仅当前已认证登录 `member` 的通知记录可查可写。
- **[SEC-05] 补齐多租户白名单路径并收敛跨租户权限**：
  - 在 `core/settings.py` 的 `TENANT_ISOLATED_API_PATHS` 中追加 `points`、`check-system`、`interactions` 等高危端点；
  - 强化 `TenantMiddleware` 鉴权，仅系统顶级超级管理员（`is_super_admin`）可跨租户访问，普通 staff 成员强制受限于各自租户。
- **[SEC-06 & SEC-08 & ARCH-03] 敏感凭据版本库脱离与 DEBUG/SECRET_KEY 安全加固**：
  - 补全 `.gitignore`，严防 `.env`、`.env.prod`、微信私钥及证书泄漏；
  - 修正 `core/settings.py` 中 `DEBUG` 环境变量读取，转为严格布尔值解析（默认 `False`）；
  - 增加生产环境强随机 `SECRET_KEY` 存在性断言，防止硬编码或默认弱密钥投产。
- **[SEC-07] 审计日志递归深度脱敏**：
  - 在 `common/utils/sensitive.py` 中实现 `mask_sensitive_data` 递归脱敏处理器；
  - 对密码、API Key、Token、私钥等核心敏感字段进行自动哈希或星号遮蔽，杜绝日志明文落盘。
- **[SEC-09 & SEC-10] 防伪造真实 IP 提取、频控与 CSRF 恢复**：
  - 在 `common/utils/network.py` 中实现安全的反代真实客户端 IP 提取器 `get_client_ip`，免疫 `X-Forwarded-For` 伪造欺骗；
  - 密码重置接口接入 10 分钟 3 次速率限制，防爆破与短信/邮件轰炸；
  - 恢复 Cookie/Session 模式管理端接口的 CSRF 防护。

### Fixed

- **Phase 1: 10 项失败/错误测试用例与环境阻断修复**：
  - 修复 `feedbacks.test_tenant_fix` 遗留过时模型引用引发的 `ImportError`（清理该脚本并将其有效断言迁移至测试包）；
  - 修复 `we_rss/tests/test_articles_api.py` 中缺失导入 `datetime` 导致的 2 项 `NameError`；
  - 修复 `we_rss` 流式同步在 SQLite 环境下并发写入凭据引发的 `IntegrityError` / 数据库表锁冲突；
  - 修复 `we_rss` 路由 `@extend_schema` OpenAPI 契约中缺失租户 Header `X-Tenant-ID`、规范 Tag 及参数描述的 4 项断言错误。
- **[BUG-LOGIC-01] 积分消费与充值并发数据竞态修复**：
  - 在 `points/services/points_engine.py` 的 `consume_points` 及积分模型层全面引入 `select_for_update()` 悲观行锁；
  - 采用 Django `F()` 原子更新表达式维护积分账户余额，杜绝并发超兑与负积分更新丢失。
- **[BUG-LOGIC-02] 商业许可证激活配额并发穿透修复**：
  - 在 `licenses/services/license_service.py` 的设备激活绑定流程中对许可证行加悲观锁（`select_for_update`），保证单机或限额授权在并发击穿下绝对安全。
- **[BUG-LOGIC-04 & BUG-LOGIC-10] 试用许可证配额字段与积分引擎变量修复**：
  - 修复试用许可证配额查询中错误的 `product` 属性引用，修正为规范外键 `application`；
  - 修复积分服务引擎中偶发的未定义变量名 `NameError`。
- **[BUG-LOGIC-03] `@transaction.atomic` 内部异常吞没破坏事务原子性修复**：
  - 修复服务层 `try...except` 捕获异常返回失败字典时导致的静默提交破损数据缺陷，在异常捕获块显式调用 `transaction.set_rollback(True)` 确保事务回滚。
- **[BUG-LOGIC-05] 软删除与底层无条件唯一约束冲突导致 500 修复**：
  - 将 `interactions`（点赞/收藏/关注）、`points` 及 `tenants` 中的旧式 `unique_together` 重构为带条件约束 `UniqueConstraint(..., condition=Q(is_deleted=False))`；
  - 使得软删除记录平滑允许重新创建与复用，生成对应数据库迁移。
- **[BUG-LOGIC-06] 反馈投票不联动扣减与防刷漏洞修复**：
  - 修复取消点赞/取消投票时不扣减计数量缺陷；
  - 采用 `F('vote_count') - 1` 结合正负值校验，杜绝无限刷票与负投票数。
- **[BUG-LOGIC-07] 消除数据库事务块内长网络发信阻塞**：
  - 采用 `transaction.on_commit(callback)` 钩子，将 SMTP 邮件模板投递与外部长耗时 HTTP 请求解耦至事务成功提交后触发，杜绝数据库连接池耗尽。
- **[BUG-LOGIC-08] 打卡记录并发重复打卡缺陷修复**：
  - 在 `check_system/models.py` 中引入 `(member, task, check_date)` 数据库级联合唯一约束与复合索引；
  - 视图层补充 400 校验提示，生成对应迁移文件。
- **[BUG-LOGIC-09~12] 业务边界与健壮性修复**：
  - 修复账号注销逻辑中的字段名映射不匹配缺陷；
  - 修复运营大屏图表除零异常（ZeroDivisionError）并提供安全兜底；
  - CMS 文章浏览量改为 `F('views') + 1` 原子自增，消除多端同时阅读时的更新丢失。
- **[ARCH-09] 修复核心设置中拼写错误**：
  - 修正 `core/settings.py` 中 WhiteNoise 缓存配置 `WHITENOISE_AUTOREFRESH` 的拼写错误。

### Changed

- **核心框架版本升级**：
  - 成功将核心 Web 框架从 `Django 5.2` 升级至 **`Django 6.1.2`**，同步适配更新 `requirements.txt`。
- **[DEFECT-ARCH-01] Member 用户名全局唯一重构**：
  - 将 `users.Member.username` 全局唯一物理约束重构为 `unique=False`，配置租户内联合条件唯一约束 `UniqueConstraint(fields=['tenant', 'username'], condition=Q(is_deleted=False))`，支持不同租户拥有同名成员。
- **[DEFECT-ARCH-02] 租户上下文彻底迁移至 ContextVar**：
  - 废弃 `threading.local`，全面迁移至 Python 原生 `contextvars.ContextVar`，消除 ASGI 与协程并发下的跨租户数据穿透与脏读风险。
- **[DEFECT-ARCH-04] 收敛双重响应包装**：
  - 移除冗余的 `ResponseStandardizationMiddleware`，统一由表现层 `StandardJSONRenderer` 执行标准化封装，降低请求链路开销。
- **[DEFECT-ARCH-05] 根目录规范化配置 pytest.ini**：
  - 新建标准化 `pytest.ini`，排除 `management/commands` 非测试脚本，统一测试收集规则，恢复测试工具链一键收集与运行。
- **[PERF-01~06] ORM 查询性能优化与索引覆盖**：
  - CMS 文章列表、收藏列表全面引入 `select_related`、`prefetch_related` 与 `annotate(children_count=Count('children'))`，彻底消灭 N+1 查询风暴；
  - 许可证 ViewSet 全面预加载关联模型；
  - 反馈列表等裸 `APIView` 统一接入 `StandardResultsSetPagination` 并限定切片，杜绝无界全量查询 OOM；
  - 大屏图表计算由 Python 循环 365 次数据库 COUNT 查询重构为数据库级 `TruncDate` / `TruncMonth` 分组聚合；
  - 为微信文章、打卡记录、用户表高频查询条件建立高频复合索引并生成迁移文件。
- **[ARCH-07] API 认证链路优化与中间件重构**：
  - 重构 `APIAuthMiddleware`，消除双重 JWT 解码与重复查库；
  - 引入 `type(user_id) is int and user_id > 0` 严格防御守卫，防止 `bool` 子类绕过伪造。
- **[ARCH-08] 代码库清理与冗余消除**：
  - 安全删除 4 个遮蔽 `views/` 模块的同名空 `views.py` 文件（`customers`, `feedbacks`, `licenses`, `users`）；
  - 彻底清理废弃僵尸应用目录 `orders/`。
- **[ARCH-10] 领域异常依赖倒置解耦**：
  - 重构 `common/exceptions/`，各业务应用建立自闭环的领域异常体系，解除基础设施层反向依赖业务领域的坏味道。
- **[PERF-09 & PERF-10] 外部网关分页与超时保护**：
  - We-RSS 恢复标准分页类，增强 `PaginatedDict` 切片兼容性；
  - ComfyUI 客户端全部 6 处 HTTP 调用注入超时配置 `timeout=(5, 30)` 与流式下载处理，杜绝网络阻塞卡死 Worker。

### Added

- **[ARCH-06] 补齐 5 大核心业务模块自动化测试用例（共 77 项用例）**：
  - `tenants/tests/`（19 项）：租户自动 code 生成、配额初始化、软删除与条件唯一、状态机流转与跨租户配额隔离测试；
  - `check_system/tests/`（15 项）：多语言任务分类、打卡频次核验、周期排他进度与重复打卡拦截测试；
  - `applications/tests/`（7 项）：模型默认值与租户内唯一、关联统计方法、读写权限分级与跨租户隔离测试；
  - `customers/tests/`（17 项）：软删除、联系人与租户关系排他性、CRUD 权限与批量操作测试；
  - `notifications/tests/`（新增 19 项 + 原有 9 项 = 28 项）：模型约束、已读状态机追踪、定向私信与广播公告隔离测试。
- **专项对抗性与并发回归测试套件**：
  - `users/tests/test_sec01_adversarial.py`：注册提权与非法字段注入对抗测试；
  - `licenses/tests/test_p0_regressions.py`：许可证悲观行锁防并发击穿回归测试；
  - `points/tests_concurrency_challenge.py`：积分高并发扣减零更新丢失回归测试；
  - `cms/tests/test_adversarial_m4_article_perf.py`：CMS 文章列表 N+1 消除断言测试；
  - `common/tests/test_m1_architecture_regressions.py`：架构清理、异常解耦与类型守卫回归测试。

---

## [0.1.0] - 2025.12.25

### Added
- 初始化企业级多租户 SaaS 数字化平台后端架构；
- 支持用户管理、RBAC 权限控制、CMS 内容管理、商业许可证管理等基础模块。
