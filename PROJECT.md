# Project: Lipeaks Backend P1 High-Priority Remediation & Performance Engineering

> **项目名称**：Lipeaks 后端 14 项 P1 级高优先级优化与系统级缺陷修复  
> **需求源文档**：`CODE_REVIEW_REPORT.md` 第 4.2 节 & `ORIGINAL_REQUEST.md`  
> **技术栈**：Python 3.13 / Django 6.1.2 / Django REST Framework 3.16.0 / SQLite (Test) / MySQL 8.0 (Prod) / Redis  
> **目标**：全量消灭 14 项 P1 缺陷，彻底解决 N+1、无界 OOM、数据一致性、防刷漏洞、ASGI 上下文串染与测试阻断，达成 100% 测试通过率。

---

## Architecture (系统架构与分层设计)

系统基于 Django + DRF 分层多租户架构，整改范围横跨核心基础设施层、数据模型层、业务服务层与表现层：

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              API / 表现层 (Views)                            │
│  - 收敛 StandardJSONRenderer 统一响应格式 (移除 ResponseStandardizationMiddleware)│
│  - 接入 StandardResultsSetPagination (治理 feedbacks 裸 APIView 无界全量查询)     │
│  - ViewSet 补充 select_related / prefetch_related / annotate 预取下推         │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                              业务服务层 (Services)                            │
│  - 强制事务回滚保证：@transaction.atomic 内部显式事务回滚 (set_rollback=True)   │
│  - 外部 I/O 隔离：通过 transaction.on_commit() 钩子将 SMTP 邮件发信解耦       │
│  - 数据库行级原子并发：采用 F('vote_count') 消除丢失更新与取消投票恶意刷票      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                           数据模型与迁移层 (Models & DB)                     │
│  - 复合索引：WechatArticle, CheckRecord, User, Member, SecurityAuditLog      │
│  - 条件唯一约束：升级 unique_together 为 UniqueConstraint(condition=Q(...))   │
│  - 统一生成 Django 规范迁移文件 (保证 makemigrations --check 零残留)          │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                           基础设施与上下文 (Core & Common)                    │
│  - 根目录规范 pytest.ini 配置与测试收集阻断隔离                               │
│  - contextvars.ContextVar 租户上下文隔离 (彻底消除 ASGI 跨租户数据串染风险)    │
│  - Redis 集中式缓存配置与本地环境优雅降级                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Feature Inventory (14 项 P1 需求完整清单)

| # | Feature 代号 | 需求与整改简述 | 归属里程碑 | 来源依据 |
|---|-------------|---------------|:---------:|---------|
| 1 | **PERF-01** | CMS 文章列表与序列化器 N+1 查询风暴治理 (预取+注解) | **M4** | CODE_REVIEW §4.2.1 |
| 2 | **PERF-02** | 许可证管理模块全套 ViewSet 缺失关联预加载治理 | **M4** | CODE_REVIEW §4.2.2 |
| 3 | **PERF-03** | 反馈列表/回复/邮件模板裸 APIView 无界全量查询 OOM 治理 | **M4** | CODE_REVIEW §4.2.3 |
| 4 | **PERF-04** | 仪表盘图表 API 数据库 TruncDate 分组聚合与消除循环 365 次 COUNT 查库 | **M4** | CODE_REVIEW §4.2.4 |
| 5 | **PERF-05/07** | 引入 Redis 集中式缓存配置与 API 日志非阻塞写入 | **M4** | CODE_REVIEW §4.2.5 |
| 6 | **PERF-06** | 微信文章、打卡记录与核心表补充数据库高频复合索引并生成迁移 | **M2** | CODE_REVIEW §4.2.6 |
| 7 | **BUG-03** | 治理 `@transaction.atomic` 内部捕获异常破坏事务原子性 | **M3** | CODE_REVIEW §4.2.7 |
| 8 | **BUG-05** | 修复软删除与底层无条件唯一约束冲突导致的永久失效与 500 | **M2, M3** | CODE_REVIEW §4.2.8 |
| 9 | **BUG-06** | 修复反馈取消投票不联动扣减与防刷漏洞 (原子 F 表达式) | **M3** | CODE_REVIEW §4.2.9 |
| 10 | **BUG-07** | 消除数据库事务块内执行耗时外部网络发信 (transaction.on_commit) | **M3** | CODE_REVIEW §4.2.10 |
| 11 | **BUG-08** | 打卡记录数据库联合唯一防重与并发竞态消除 (约束+400校验) | **M2, M3** | CODE_REVIEW §4.2.11 |
| 12 | **ARCH-02** | 改造租户上下文为 `contextvars.ContextVar` 消除 ASGI 跨租户泄漏风险 | **M1** | CODE_REVIEW §4.2.12 |
| 13 | **ARCH-04** | 收敛双重响应包装，移除 `ResponseStandardizationMiddleware` | **M1** | CODE_REVIEW §4.2.13 |
| 14 | **ARCH-05** | 规范化根目录 `pytest.ini` 配置并恢复测试套件一键运行 | **M1** | CODE_REVIEW §4.2.14 |

*核验结果：全部 14 项需求已 100% 映射至对应里程碑，无遗漏未分配项。*

---

## Milestones (里程碑划分与执行计划)

| # | 里程碑名称 (Milestone) | 覆盖核心任务 | 模块与文件范围 | 前置依赖 | 状态 |
|---|----------------------|-------------|---------------|:-------:|:----:|
| **M1** | **测试基建与底层架构解耦** | P1-14 (ARCH-05)<br>P1-13 (ARCH-04)<br>P1-12 (ARCH-02) | `pytest.ini`<br>`core/settings.py`<br>`core/settings_test.py`<br>`common/utils/tenant_context.py`<br>`common/middleware/tenant_middleware.py` | 无 | **DONE** |
| **M2** | **数据模型、复合索引与条件唯一约束** | P1-06 (PERF-06)<br>P1-08 (BUG-05)<br>P1-11 (BUG-08) [模型部分] | `we_rss/models.py`<br>`check_system/models.py`<br>`users/models.py`<br>`licenses/models.py`<br>`interactions/models.py`<br>`points/models.py`<br>`tenants/models.py`<br>各应用迁移文件 | M1 | **DONE** |
| **M3** | **业务事务一致性与防刷治理** | P1-07 (BUG-03)<br>P1-09 (BUG-06)<br>P1-10 (BUG-07)<br>P1-11 (BUG-08) [接口防重]<br>P1-08 (BUG-05) [软删除恢复] | `licenses/services/*.py`<br>`points/services/*.py`<br>`feedbacks/models.py`<br>`feedbacks/services.py`<br>`feedbacks/complete_system.py`<br>`check_system/views.py`<br>`interactions/serializers.py` | M2 | **DONE** |
| **M4** | **ORM 查询性能、无界分页与缓存** | P1-01 (PERF-01)<br>P1-02 (PERF-02)<br>P1-03 (PERF-03)<br>P1-04 (PERF-04)<br>P1-05 (PERF-05/07) | `cms/views/base_views.py`<br>`cms/serializers.py`<br>`licenses/views/admin_views.py`<br>`feedbacks/views/*.py`<br>`charts/views.py`, `charts/utils.py`<br>`core/settings.py`<br>`common/middleware/enhanced_api_logging_middleware.py` | M1, M2 | **IN_PROGRESS** |
| **M5** | **全量回归验证与 E2E 交付** | 全量 14 项功能综合验证 | 全量测试用例套件 (`manage.py test` 与 `pytest`)，专项回归用例 | M1~M4 | **PLANNED** |

---

## Interface Contracts (跨模块接口契约)

### 1. 租户上下文接口契约 (`common.utils.tenant_context`)
- **调用方**：中间件 `TenantMiddleware`、ORM 查询拦截器、业务服务层。
- **签名**：
  ```python
  def get_current_tenant() -> Optional[Tenant]: ...
  def set_current_tenant(tenant: Optional[Tenant]) -> None: ...
  def clear_current_tenant() -> None: ...
  ```
- **契约保证**：内部由 `_tenant_context = contextvars.ContextVar('current_tenant', default=None)` 驱动，多线程与协程间严格隔离。接口签名与返回值完全向后兼容。

### 2. 事务回滚与防刷契约 (`services` ↔ `transaction`)
- **调用方**：`licenses.services.license_service`, `points.services.vip_service`, `feedbacks.services`
- **契约规则**：
  1. 凡带有 `@transaction.atomic` 的业务方法，若捕获异常并返回失败字典，**必须在 except 块中调用 `transaction.set_rollback(True)`**。
  2. 凡涉及外部 SMTP/网络调用或异步 Worker 触发，**必须挂载于 `transaction.on_commit(callback)`**。

### 3. 数据分页契约 (`views` ↔ `pagination`)
- **调用方**：前端客户端、E2E 测试用例。
- **统一响应结构**：
  ```json
  {
    "count": 100,
    "next": "http://.../?page=2",
    "previous": null,
    "results": [ ... ]
  }
  ```
- **契约规则**：`FeedbackListView`、`FeedbackReplyListView`、`EmailTemplateListView` 接入 `StandardResultsSetPagination`，默认单页上限 10~20 条，最大不超过 100 条。

### 4. 条件软删除复用契约 (`interactions` / `points` / `tenants`)
- **契约规则**：当记录被软删除（`is_deleted=True` 或 `is_active=False`）后，用户重新执行点赞、关注或续签 VIP 时，系统必须支持平滑恢复或重新创建，不得抛出 `IntegrityError`。

---

## Code Layout (代码文件专属权与边界)

为避免并发子代理冲突，严格划分文件修改归属权：

| 模块边界 | 独占文件清单 | 负责代理角色 |
|---------|-------------|:-----------:|
| **基建与设置** | `pytest.ini`<br>`core/settings.py`<br>`core/settings_test.py`<br>`common/utils/tenant_context.py`<br>`common/middleware/tenant_middleware.py` | M1 负责 Worker |
| **模型与迁移** | `we_rss/models.py`<br>`check_system/models.py`<br>`users/models.py`<br>`licenses/models.py`<br>`interactions/models.py`<br>`points/models.py`<br>`tenants/models.py`<br>`*/migrations/*` | M2 负责 Worker |
| **服务与事务** | `licenses/services/*.py`<br>`points/services/*.py`<br>`feedbacks/models.py`<br>`feedbacks/services.py`<br>`feedbacks/complete_system.py`<br>`check_system/views.py`<br>`interactions/serializers.py` | M3 负责 Worker |
| **查询与分页** | `cms/views/base_views.py`, `cms/serializers.py`<br>`licenses/views/admin_views.py`, `licenses/serializers.py`<br>`feedbacks/views/*.py`<br>`charts/views.py`, `charts/utils.py`<br>`common/middleware/enhanced_api_logging_middleware.py` | M4 负责 Worker |
| **测试与验证** | `tests/`, 各 App 下 `tests/` 目录中新增回归用例 | M5 / Reviewer / Challenger |

---

## Acceptance Criteria (系统级验收基线)

1. **环境与模型健康**：
   - `python manage.py check --settings=core.settings_test` 输出 0 issues。
2. **迁移完整性无漂移**：
   - `python manage.py makemigrations --check --dry-run --settings=core.settings_test` 输出 `No changes detected`。
3. **全量测试通过率 100%**：
   - `python manage.py test --settings=core.settings_test` 输出 `OK` (通过数 $\ge 408$ 用例)。
   - `pytest --ds=core.settings_test` 无收集崩溃，全量执行通过率 100%。
4. **关键文件不可侵犯**：
   - 保护文件 `.env`, `.env.prod`, `wechat/wechat_config.json`, `CODE_REVIEW_REPORT.md` 绝对完好无损。
