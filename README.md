# LiPeaks Backend

> **基于 Django 6.1.2 的企业级多租户 SaaS 数字化平台后端系统**

---

## 📌 项目简介

`lipeaks_backend` 是一个面向企业级多租户数字化场景的高性能后端服务系统。系统依托 Django 6.1.2 与 Django REST Framework 构建，提供从多租户隔离、双身份认证、RBAC 细粒度权限控制、商业许可证授权与设备绑定，到内容管理（CMS）、微信生态内容聚合（We-RSS）、积分体系及考勤打卡等端到端的数字化能力。

本项目已历经严密的多阶段深度代码审计与稳定性工程治理（涵盖 P0 致命缺陷修复、P1 性能瓶颈与数据一致性治理、P2 架构解耦与安全加固），全量通过 638 项测试用例，达成 100% 绿色通过，获得 **A+ 生产级就绪评级**。

---

## 🏆 项目工程状态（代码审计与治理结项）

当前系统已全面完成 Phase 0 至 Phase 4 的深度治理，测试指标与架构健康度如下：

| 评估维度 | 指标与验收标准 | 实测状态 | 结论 |
|:---|:---|:---|:---:|
| **Django 版本** | 适配并升级至最新版本 | `Django==6.1.2` (Python 3.13) | **✅ 生产就绪** |
| **系统架构健康** | `python manage.py check --settings=core.settings_test` | **`0 issues (0 silenced)`** | **✅ 完全达标** |
| **数据库迁移一致性** | `python manage.py makemigrations --check --dry-run` | **`No changes detected` (零残留无漂移)** | **✅ 完全达标** |
| **Django 原生测试套件** | `python manage.py test --settings=core.settings_test` | **`638 tests, OK (failures=0, errors=0, skipped=7)`** | **✅ 100% 通过** |
| **Pytest 测试工具链** | `pytest --collect-only` | **`666 tests collected, 0 errors`** | **✅ 零阻断收集** |
| **多租户安全边界** | 租户上下文彻底采用 `contextvars.ContextVar` 隔离 | 杜绝 ASGI/协程跨请求串染与提权 | **✅ 深度加固** |
| **数据并发一致性** | 积分扣减与设备激活全面落地 `select_for_update` + `F()` | 杜绝并发超兑、负积分与更新丢失 | **✅ 行锁受控** |
| **自动化测试覆盖** | 补齐 tenants, check_system, applications, customers, notifications | 新增 77 项深度测试，彻底清零盲区 | **✅ 全量覆盖** |

*详细审计报告与逐项缺陷修复溯源请参阅 [CODE_REVIEW_REPORT.md](file:///D:/Github/lipeaks_backend/CODE_REVIEW_REPORT.md)。*

---

## 🌟 核心特性与架构设计

### 1. 多租户四重防护机制 (Multi-Tenancy)
- **路由层识别**：通过请求头 `X-Tenant-ID` 或子域名由中间件解析；
- **上下文隔离**：采用 Python 原生 `contextvars.ContextVar` 存储线程与协程安全的租户上下文，杜绝 ASGI 跨请求数据泄漏；
- **ORM 层自动过滤**：模型继承 `BaseModel` 并由 `TenantManager` 自动下推 `tenant_id` 过滤条件；
- **配额层硬性拦截**：`TenantQuota` 针对用户数、应用数与存储空间实施生命周期资源配额管控。

### 2. 双身份认证与多态 RBAC
- **用户隔离体系**：运营管理端用户（`User`）与 SaaS 客户端租户成员（`Member`）物理分表存储；
- **租户级唯一约束**：`Member.username` 采用租户内联合条件唯一约束（`condition=Q(is_deleted=False)`），支持软删除记录平滑重建；
- **JWT 统一定制**：Payload 注入 `model_type` 与 `tenant_id`，中间件单次解析并实施 `type(user_id) is int and user_id > 0` 严格防御。

### 3. 商业软件许可证体系 (Licenses)
- **RSA 2048 非对称防伪**：基于公私钥对生成防伪数字签名；
- **硬件指纹绑定**：采集 CPU、MAC、BIOS 序列号混淆计算唯一机器指纹（`MachineBinding`）；
- **防超卖悲观行锁**：激活与绑定逻辑执行行级排他锁（`select_for_update`），保证高并发配额判定的绝对强一致。

### 4. 社交互动与高频业务防刷
- **事务内长网络隔离**：邮件通知与异步调用通过 `transaction.on_commit()` 钩子延迟触发，杜绝数据库事务阻塞；
- **原子增减与计数防刷**：点赞、投票、文章阅读量全面采用数据库 `F()` 表达式维护，杜绝无限刷票与负计数量；
- **打卡记录条件唯一防重**：数据库底层建立 `(member, task, check_date)` 唯一约束，彻底杜绝并发重复签到。

---

## 🏗️ 系统核心模块拓扑

```text
lipeaks_backend/
├── core/             # 系统总配置、路由分发与测试配置 (settings_test.py)
├── common/           # 通用基类 (BaseModel)、租户上下文、中间件与通用工具
├── tenants/          # 多租户管理与租户资源配额 (TenantQuota)
├── users/            # 双身份用户模型 (User, Member)、认证与密码重置
├── rbac/             # 基于角色的权限控制 (Role, Permission, UserRole)
├── menus/            # 动态层级菜单与权限路由分发
├── applications/     # 统一软件资产与发布管理
├── licenses/         # 商业许可证计划、RSA 授权验签与机器绑定
├── feedbacks/        # 工单反馈、工单回复、投票与邮件模板通知
├── customers/        # CRM 客户管理与租户联系人映射
├── cms/              # 内容管理系统、富文本、无限极分类与版本审计
├── interactions/     # 文章点赞、收藏与成员关注社交互动
├── points/           # 积分引擎 (select_for_update)、VIP 会员成长梯队
├── check_system/     # 考勤打卡系统、打卡周期与任务模板
├── charts/           # 数据大屏与统计分析 (ORM TruncDate 分组聚合)
├── notifications/    # 消息通知中心、公告广播与已读回执
├── wechat/           # 微信小程序登录与公众平台接入
└── we_rss/           # 微信文章采集抓取、图片防盗链流式反代与标准 RSS 订阅
```

---

## 🛠️ 环境准备与快速上手

### 环境要求
- **Python**: `>= 3.13`
- **Django**: `6.1.2`
- **数据库**: MySQL 8.0+（生产环境）/ SQLite（开发与测试环境）
- **缓存与异步**: Redis 6.0+（生产环境），Celery 5.x

### 本地开发环境部署

1. **克隆项目并创建虚拟环境**：
   ```bash
   git clone https://github.com/fx0883/lipeaks_backend.git
   cd lipeaks_backend
   python -m venv venv
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   # Linux/macOS
   source venv/bin/activate
   ```

2. **安装项目依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**：
   复制并根据环境调整配置文件：
   ```bash
   cp .env.example .env
   ```
   > **注意**：生产环境下切勿将包含真实密钥的 `.env` 提交至版本库，系统 `.gitignore` 已实施严格保护。

4. **数据库迁移**：
   ```bash
   python manage.py migrate
   ```

5. **启动本地开发服务器**：
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

---

## 🧪 自动化测试运行指引

系统配置了完备的原生与 Pytest 自动化测试体系，测试环境使用独立的 `core/settings_test.py` 隔离配置。

### 1. 运行 Django 官方全量测试套件
> [!IMPORTANT]
> 执行测试时必须显式指定 `--settings=core.settings_test` 配置：

```powershell
python manage.py test --settings=core.settings_test
```
执行单应用或指定测试模块：
```powershell
# 运行 applications 应用测试
python manage.py test applications.tests --settings=core.settings_test

# 运行 P0 专项并发与安全回归测试
python manage.py test licenses.tests.test_p0_regressions --settings=core.settings_test
```

### 2. 使用 Pytest 运行测试
项目根目录下提供了标准化 `pytest.ini`，已预置测试设置与命令脚本隔离选项，可直接执行：
```powershell
# 收集所有测试用例（共 666 项）
pytest --collect-only

# 执行全量测试并输出简报
pytest -v
```

---

## 🔒 安全与生产配置注意事项

1. **生产环境 DEBUG 开关**：
   - 生产环境中必须设置 `DEBUG=False`。
   - `core/settings.py` 已加固为严格解析布尔值环境变量（默认 `False`）。
2. **密钥配置规范**：
   - 生产启动时必须通过环境变量提供强随机 `SECRET_KEY`，否则系统在启动前置检查中将阻断运行。
3. **敏感日志自动脱敏**：
   - 系统内置递归脱敏处理器（`common.utils.sensitive.mask_sensitive_data`），在请求日志落盘时自动隐藏密码、Token 及私钥信息。
4. **反代真实 IP 与限流**：
   - 系统集成防伪造 IP 提取器（`common.utils.network.get_client_ip`），密码重置等高危接口默认开启 10 分钟 3 次速率限制。

---

## 📄 变更日志与许可

- **项目变更日志**：详见 [CHANGELOG.md](file:///D:/Github/lipeaks_backend/CHANGELOG.md)
- **开源许可证**：本项目遵循 MIT License
