# 第一阶段：项目整体架构与系统地图分析

本项目是一套基于 **Django 6.0 + Django REST Framework (DRF)** 构建的**企业级多租户 SaaS 核心底座与应用管理平台**。系统支持“管理员端（运营/租户管理）”与“成员端（终端 SaaS 客户/终端用户）”双重身份体系，并深度集成了软件授权许可（Licenses）、用户反馈（Feedbacks）、多语言内容发布（CMS）、微信生态整合（WeChat / We-RSS）以及积分等级权益（Points）等业务。

---

## 1. 系统模块全景拓扑图（System Architecture Map）

```mermaid
graph TB
    subgraph ClientLayer ["接入层 (Clients)"]
        WebAdmin["运营管理后台 (Vue/React Admin)"]
        MemberClient["SaaS 终端应用/用户前台 (Web/Client)"]
        DesktopApp["桌面分发客户端 (C++/Electron/Python)"]
        WxApp["微信小程序 / 微信公众号"]
    end

    subgraph GatewayLayer ["接入与基础设施网关"]
        Nginx["Nginx (反向代理 / SSL / 静态资源)"]
        WhiteNoise["WhiteNoise (静态资源Manifest服务)"]
    end

    subgraph MiddlewarePipeline ["Django 中间件链 (Pipeline)"]
        CorsMW["CorsMiddleware"]
        LocaleMW["LocaleMiddleware (多语言)"]
        AuthMW["AuthenticationMiddleware"]
        APIAuthMW["APIAuthMiddleware"]
        TenantMW["TenantMiddleware (租户上下文提取与校验)"]
        LogMW["EnhancedAPILoggingMiddleware (审计日志)"]
        RespMW["ResponseStandardizationMiddleware (标准响应封装)"]
    end

    subgraph CoreBase ["核心基石模块 (Infrastructure & Multi-Tenancy)"]
        common["common (BaseModel / TenantContext / 异常体系 / 标准渲染器)"]
        tenants["tenants (租户模型 / 配额 Quota / 资源限制)"]
        users["users (双身份: User 管理员 / Member 租户成员)"]
        rbac["rbac (多态角色 / 权限 / 菜单控制)"]
        menus["menus (动态菜单树 / 权限挂载)"]
    end

    subgraph CoreBusiness ["核心业务模块 (Business Domains)"]
        applications["applications (软件产品实体 / 版本管理 / RSA公私钥配置)"]
        licenses["licenses (软件授权 / 机器指纹绑定 / 在线心跳 / 激活验签)"]
        feedbacks["feedbacks (工单反馈 / 状态流转 / 邮件通知)"]
        cms["cms (多语言文章 / 分类树 / 标签 / 评论 / 统计)"]
        points["points (多租户积分引擎 / VIP 会员等级)"]
        customers["customers (客户企业与租户/成员关联)"]
        interactions["interactions (点赞 / 收藏 / 关注)"]
        notifications["notifications (站内信 / 广播通知 / 已读追踪)"]
        check_system["check_system (打卡任务 / 打卡周期 / 模板)"]
        wechat["wechat (微信小程序 code2session / 登录 / 资产)"]
        we_rss["we_rss (微信公众号抓取 / 凭证托管 / RSS订阅 / 图片防盗链代理)"]
    end

    subgraph AsyncAndExt ["异步任务、数据存储与外部集成"]
        MySQL[("MySQL 8.0 (utf8mb4, 连接池)")]
        Redis[("Redis (Celery Broker / Backend, Token缓存)")]
        CeleryWorker["Celery Worker (异步任务: 邮件发送 / RSS抓取 / 统计刷新)"]
        CeleryBeat["Celery Beat (定时任务: 邮件日志清理 / 定期同步)"]
        SMTP["SMTP 服务 (QQ/企业邮箱)"]
        WeChatAPI["微信官方 API / 搜狗微信搜索"]
    end

    %% 关联拓扑
    ClientLayer --> Nginx
    Nginx --> MiddlewarePipeline
    MiddlewarePipeline --> CoreBase
    CoreBase --> CoreBusiness
    CoreBusiness --> MySQL
    CoreBusiness --> Redis
    CoreBusiness -. 异步调度 .-> CeleryWorker
    CeleryBeat --> Redis
    CeleryWorker --> Redis
    CeleryWorker --> MySQL
    CeleryWorker -. 邮件投递 .-> SMTP
    we_rss -. 抓取/同步 .-> WeChatAPI
    wechat -. 认证/素材 .-> WeChatAPI
```

---

## 2. 模块组成与依赖拓扑关系

项目共划分为 **16 个 App**，分属于 4 个架构层级：

| 架构层级 | App 列表 | 职责定位 |
| :--- | :--- | :--- |
| **框架与基础设施层** | `core`, `common` | 全局路由配置、WSGI/ASGI、环境变量、多租户上下文、全局日志、标准响应封装、统一分页与异常处理 |
| **租户与身份权限层** | `tenants`, `users`, `rbac`, `menus` | 租户注册与配额管理、双身份用户模型（User vs Member）、多态 RBAC 权限控制、前端动态菜单 |
| **核心商业化业务层** | `applications`, `licenses`, `feedbacks`, `customers`, `points` | 软件实体管理、机器指纹授权许可（支持在线/离线/租期/心跳）、工单反馈系统、客户CRM、积分与VIP等级系统 |
| **内容与扩展业务层** | `cms`, `interactions`, `notifications`, `check_system`, `charts`, `wechat`, `we_rss`, `docs_view` | 多语言内容管理、用户社交互动（点赞/收藏）、消息通知中心、打卡签到任务、可视化图表、微信生态集成 |

### 模块依赖关系拓扑图

```mermaid
graph TD
    classDef infra fill:#eceff1,stroke:#607d8b,stroke-width:2px;
    classDef identity fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef business fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef ext fill:#fff3e0,stroke:#f57c00,stroke-width:2px;

    common:::infra
    tenants:::identity
    users:::identity
    rbac:::identity
    menus:::identity
    applications:::business
    licenses:::business
    feedbacks:::business
    customers:::business
    points:::business
    cms:::business
    interactions:::business
    notifications:::business
    check_system:::business
    wechat:::ext
    we_rss:::ext
    charts:::ext

    common --> tenants
    common --> users
    tenants --> users
    users --> rbac
    tenants --> rbac
    rbac --> menus

    applications --> licenses
    applications --> feedbacks
    applications --> cms

    tenants --> applications
    tenants --> customers
    users --> customers
    users --> points
    tenants --> points
    users --> feedbacks
    users --> licenses

    users --> cms
    cms --> interactions
    users --> notifications
    users --> check_system
    users --> wechat
    users --> we_rss
    tenants --> we_rss

    charts --> tenants
    charts --> licenses
    charts --> cms
```

---

## 3. 多租户隔离机制与权限体系剖析

### 3.1 多租户（Multi-Tenancy）底层设计

本项目采用**共享数据库、共享数据表、共享架构，通过租户字段（Tenant ID）进行逻辑隔离**的模式，并在模型层、查询管理器层、中间件层以及 ViewSet 层构筑了四重安全防线：

```mermaid
flowchart TD
    Req[客户端 HTTP 请求] --> M1[TenantMiddleware 租户中间件]
    
    subgraph TenantMiddlewareFlow [TenantMiddleware 校验与解析]
        CheckPath{路径是否属于<br>TENANT_ISOLATED_API_PATHS ?}
        CheckPath -- 否 --> PassMW[跳过租户校验]
        CheckPath -- 是 --> IsPublic{是否在公开白名单<br>TENANT_PUBLIC_API_PATHS ?}
        IsPublic -- 是 --> PassMW
        IsPublic -- 否 --> Resolve[TenantIdResolver 解析租户ID]
        
        Resolve --> RuleMatch{请求身份解析}
        RuleMatch -- SuperAdmin --> SuperAdminCheck[允许无头或指定租户]
        RuleMatch -- TenantAdmin --> TenantAdminCheck[严格强制必须为其自身租户，禁止随意跨租户]
        RuleMatch -- Member --> MemberCheck[校验 Token 中的租户与 Header X-Tenant-ID 一致]
        RuleMatch -- Anonymous GET --> AnonCheck[必须携带合法且活跃的 X-Tenant-ID]
        
        SuperAdminCheck --> SetContext[set_current_tenant: 注入线程局部变量 threading.local]
        TenantAdminCheck --> SetContext
        MemberCheck --> SetContext
        AnonCheck --> SetContext
    end

    SetContext --> ViewSet[TenantModelViewSet 视图集]
    
    subgraph DataIsolationFlow [数据访问与操作隔离]
        ViewSet --> GetQueryset[get_queryset 过滤]
        GetQueryset --> TenantManager[TenantManager.get_queryset]
        TenantManager --> AutoFilter["自动注入: filter(is_deleted=False, tenant=current_tenant)"]
        
        ViewSet --> PerformCreate[perform_create / perform_update]
        PerformCreate --> AutoInjectTenant[自动注入/强制绑定 serializer.save(tenant=current_tenant)]
    end

    AutoFilter --> DB[(MySQL 查询执行)]
    AutoInjectTenant --> DB
    
    PassMW --> ViewSet
```

1. **底层线程上下文**：`common/utils/tenant_context.py` 基于 `threading.local` 存储 `_thread_local.tenant`，提供了 `get_current_tenant()`、`set_current_tenant()` 与 `clear_current_tenant()`。
2. **模型与管理器**：
   - 绝大多数业务模型继承自 `common.models.BaseModel`，自带 `tenant` 外键、`created_at`、`updated_at`、`is_deleted`（软删除标志）。
   - 默认管理器为 `common.utils.tenant_manager.TenantManager`，其 `get_queryset()` 会自动拦截并追加 `filter(is_deleted=False, tenant=current_tenant)`。如需无租户过滤查询，必须显式调用 `original_objects`。
3. **租户配额控制（Quota）**：
   - `TenantQuota`（`tenants/models.py`）针对每个租户约束 `max_users`（最大成员数）、`max_admins`（最大管理员数）、`max_storage_mb`（最大存储空间）与 `max_products`。在创建 `User` 与 `Member` 时通过 `save()` 钩子强制校验。

---

### 3.2 双身份认证体系（Dual Authentication）与 RBAC

系统将用户区分为两大隔离实体，均继承自 `BaseUserModel`：

```mermaid
classDiagram
    class AbstractUser {
        <<Django Auth>>
    }
    class BaseUserModel {
        +tenant: ForeignKey(Tenant)
        +phone: CharField
        +email: EmailField
        +nick_name: CharField
        +avatar: CharField
        +status: CharField (active/suspended/inactive)
        +is_deleted: BooleanField
        +soft_delete()
    }
    class User {
        +is_admin: Boolean (True)
        +is_super_admin: Boolean
        +is_staff: Boolean (True)
        +is_superuser: Boolean (SuperAdmin only)
        +display_role: "超级管理员" | "租户管理员"
    }
    class Member {
        +parent: ForeignKey(Member, self)
        +is_staff: Boolean (False)
        +is_sub_account: Boolean
        +display_role: "普通成员" | "子账号"
    }

    AbstractUser <|-- BaseUserModel
    BaseUserModel <|-- User
    BaseUserModel <|-- Member
```

- **认证模式（JWT Authentication）**：
  - 核心类：`common/authentication/jwt_auth.py`。
  - 生成 Payload 时带有 `model_type: 'user' | 'member'`。
  - 解密 Token 时，若 `model_type == 'member'` 则查询 `Member` 表；否则查询 `User` 表。
  - 安全门禁：拦截子账号（`parent` 非空禁止直接登录）、校验用户激活状态（`status == 'active'`）、校验租户活跃状态（`tenant.status == 'active'` 且未软删除）。

- **多态 RBAC 权限设计**：
  - 模型：`rbac/models.py` 中的 `Permission`, `Role`, `RolePermission`, `UserRole`。
  - `UserRole` 采用多态设计：`user_type`（`'user'` 或 `'member'`）配合 `user_id`，打破单表关联，一套 RBAC 引擎同时管理管理员和终端客户角色的权限与有效期（`start_date`, `end_date`, `is_active`）。

---

## 4. 核心数据模型关系图（ER Diagram）

```mermaid
erDiagram
    Tenant ||--o{ TenantQuota : "1:1 配额约束"
    Tenant ||--o{ User : "1:N 拥有管理员"
    Tenant ||--o{ Member : "1:N 拥有租户成员"
    Tenant ||--o{ Application : "1:N 拥有软件应用"
    Tenant ||--o{ License : "1:N 拥有许可证"
    Tenant ||--o{ Article : "1:N 拥有文章"
    Tenant ||--o{ Feedback : "1:N 接收用户反馈"

    Member ||--o{ Member : "父子账号层级"
    
    Application ||--o{ LicensePlan : "1:N 许可定价方案"
    Application ||--o{ License : "1:N 签发许可证"
    Application ||--o{ Feedback : "1:N 关联产品反馈"
    Application ||--o{ ArticleApplication : "1:N 内容关联软件"

    LicensePlan ||--o{ License : "作为模板生成"
    License ||--o{ MachineBinding : "1:N 绑定机器硬件指纹"
    License ||--o{ LicenseActivation : "1:N 激活记录"
    License ||--o{ LicenseUsageLog : "1:N 心跳与使用日志"
    License ||--o{ LicenseAssignment : "1:N 分配给租户成员"
    Member ||--o{ LicenseAssignment : "持有许可证"

    Feedback ||--o{ FeedbackReply : "1:N 沟通回复"
    Feedback ||--o{ FeedbackStatusHistory : "1:N 状态轨迹"
    Feedback ||--o{ FeedbackAttachment : "1:N 附件材料"
    Feedback ||--o{ FeedbackVote : "1:N 用户投票点赞"

    Article ||--o| User : "作者为管理员"
    Article ||--o| Member : "作者为租户成员"
    Article ||--o{ Article : "系列/父子文章树"
    Article ||--o{ ArticleCategory : "多对多分类"
    Category ||--o{ ArticleCategory : "多对多文章"
    Article ||--o{ Comment : "1:N 文章评论"
    Article ||--o| ArticleStatistics : "1:1 阅读点赞统计"
```

---

## 5. 核心业务模块概览

| 核心业务模块 | 业务领域与核心功能 | 核心数据模型 | 关键端点 (API Prefix) |
| :--- | :--- | :--- | :--- |
| **`applications`** | 统一管理对外发布的软件实体、版本号发布、运行状态、RSA公私钥元数据（为许可证验签提供基准密钥）。 | `Application` | `/api/v1/applications/` |
| **`licenses`** | 商业软件授权体系，支持试用版/企业版方案，基于 SHA256 许可证密钥与硬件指纹（CPU/MAC/BIOS）哈希绑定，支持机器解绑、在线心跳、离线激活码签发、租户成员授权分配。 | `LicensePlan`, `License`, `MachineBinding`, `LicenseActivation`, `LicenseUsageLog`, `LicenseAssignment` | `/api/v1/licenses/` |
| **`feedbacks`** | 统一工单与用户建议反馈中心，支持公网匿名提交、附件上传、工单状态推进（待处理→处理中→已解决）、内部私密备注与公开回复，自动触发 Celery 邮件通知客户。 | `Feedback`, `FeedbackReply`, `FeedbackAttachment`, `FeedbackEmailLog`, `EmailTemplate` | `/api/v1/feedbacks/` |
| **`cms`** | 多租户内容发布系统，支持 Markdown/HTML 混合编排、无限层级父子文章树、多语言分类（Parler i18n）、标签分组、版本修订快照（Version）、防刷阅读统计与操作日志审计。 | `Article`, `Category`, `TagGroup`, `Tag`, `Comment`, `ArticleVersion`, `ArticleStatistics` | `/api/v1/cms/` |
| **`points`** | 租户用户忠诚度与积分等级引擎，支持经验值增长、VIP等级梯度（白银/黄金/钻石）、积分扣除与增发规则引擎、会员权益标签。 | `TenantUserProfile`, `UserLevel`, `TenantUserPoints`, `UserTypeTag` | `/api/v1/points/` |
| **`we_rss`** | 微信公众号内容订阅与知识聚合系统，支持微信登录凭证托管（扫码轮询登录）、自动化文章拉取、微信防盗链图片反代（Image Proxy）、Markdown 导出与 ZIP 打包。 | `WechatCredential`, `WechatFeed`, `WechatArticle`, `MemberFeedSubscription`, `WechatSyncTask` | `/api/v1/we-rss/` |

---

## 6. 一次典型请求在系统中的全链路调用时序图

以一个“**租户成员发起创建 CMS 文章请求（POST /api/v1/cms/articles/）**”为例：

```mermaid
sequenceDiagram
    autonumber
    actor Client as 客户端 (前端/App)
    participant Nginx as Nginx 网关
    participant MW_CORS as Cors / Locale 中间件
    participant MW_Auth as APIAuthMiddleware
    participant MW_Tenant as TenantMiddleware
    participant DRF_Auth as APIJWTAuthentication
    participant DRF_Perm as Permission Classes (IsMemberUser)
    participant ViewSet as ArticleViewSet (TenantModelViewSet)
    participant Serializer as ArticleSerializer
    participant Model as Article (BaseModel)
    participant Manager as TenantManager
    participant DB as MySQL 数据库
    participant MW_Resp as ResponseStandardizationMiddleware

    Client->>Nginx: HTTP POST /api/v1/cms/articles/ <br/>Header: Authorization: Bearer <Token>, X-Tenant-ID: 10
    Nginx->>MW_CORS: 转发请求
    MW_CORS->>MW_Auth: CORS 跨域校验 & 语言上下文设置
    MW_Auth->>MW_Tenant: 调用认证前置校验
    
    rect rgb(240, 248, 255)
        Note over MW_Tenant: 租户安全门禁
        MW_Tenant->>MW_Tenant: 清理旧上下文 (clear_current_tenant)
        MW_Tenant->>MW_Tenant: 判定路径在 TENANT_ISOLATED_API_PATHS 内
        MW_Tenant->>MW_Tenant: 解析有效 Tenant ID (Token 租户与 Header 租户比对)
        MW_Tenant->>MW_Tenant: 注入 threading.local: set_current_tenant(tenant_10)
    end
    
    MW_Tenant->>ViewSet: 进入 DRF 路由分发
    
    rect rgb(255, 245, 238)
        Note over DRF_Auth,DRF_Perm: 认证与权限评估
        ViewSet->>DRF_Auth: authenticate(request)
        DRF_Auth->>DB: 根据 Token 中 model_type='member' 读取 Member 实例
        DB-->>DRF_Auth: 返回 Member(id=5, tenant=10)
        DRF_Auth-->>ViewSet: request.user = Member 实例
        ViewSet->>DRF_Perm: has_permission(request, view)
        DRF_Perm-->>ViewSet: 校验活跃状态与租户状态 -> 鉴权通过
    end

    rect rgb(240, 255, 240)
        Note over ViewSet,Model: 业务处理与数据持久化
        ViewSet->>Serializer: is_valid(raise_exception=True)
        Serializer-->>ViewSet: 数据校验通过
        ViewSet->>ViewSet: perform_create(serializer)
        ViewSet->>Model: 强制注入 tenant=get_current_tenant(), member=request.user
        Model->>Model: clean() 校验: 确保 user/member 单一作者约束
        Model->>DB: INSERT INTO cms_article (..., tenant_id=10, member_id=5)
        DB-->>Model: 返回插入结果
        Model->>DB: 触发自动创建关联 ArticleStatistics 记录
    end

    ViewSet-->>MW_Tenant: 返回 Response(data, status=201)
    MW_Tenant->>MW_Tenant: process_response: 执行 clear_current_tenant()
    MW_Tenant->>MW_Resp: 交付响应标准化中间件
    
    rect rgb(245, 245, 245)
        Note over MW_Resp: 标准化封装
        MW_Resp->>MW_Resp: 格式化为 { code: 200, message: "success", data: {...} }
    end

    MW_Resp-->>Nginx: HTTP 201 Created
    Nginx-->>Client: 返回标准 JSON 响应
```

---

## 7. 外部依赖、缓存与异步任务拓扑

```mermaid
graph LR
    subgraph AppServer ["Django Application Server"]
        WebProcess["Gunicorn / WSGI (Web 进程)"]
        CeleryTaskPublisher["Task Dispatcher (delay / apply_async)"]
    end

    subgraph CacheAndBroker ["Redis 缓存与消息队列"]
        RedisBroker["Redis DB 0: Celery Broker"]
        RedisResult["Redis DB 0: Celery Backend"]
        RedisTokenCache["Redis: WeChat AccessToken 缓存"]
    end

    subgraph BackgroundWorkers ["后台工作进程"]
        FeedbackWorker["Celery Worker: feedbacks 队列"]
        RSSWorker["Celery Worker: we_rss 队列"]
        BeatScheduler["Celery Beat 定时调度器"]
    end

    subgraph ExternalThirdParty ["外部第三方服务"]
        QQ_SMTP["QQ / 企业邮箱 SMTP 服务器"]
        WxServer["微信开放平台 (小程序 Code2Session / AccessToken)"]
        WxCDN["微信图片 CDN (mmbiz.qpic.cn / mmbiz.qlogo.cn)"]
        SogouSearch["搜狗微信公众号检索接口"]
    end

    WebProcess -->|读写缓存| RedisTokenCache
    WebProcess -->|投递工单邮件/抓取任务| CeleryTaskPublisher
    CeleryTaskPublisher --> RedisBroker

    RedisBroker --> FeedbackWorker
    RedisBroker --> RSSWorker
    BeatScheduler -->|每天凌晨 2:00 投递清理邮件日志任务| RedisBroker

    FeedbackWorker -->|调用发送模板邮件| QQ_SMTP
    RSSWorker -->|抓取公众号历史文章与图片| WxCDN
    RSSWorker -->|查询公众号元数据| SogouSearch
    WebProcess -->|微信小程序快捷登录换取 OpenID| WxServer
    WebProcess -->|Image Proxy 流式代理解析微信防盗链图片| WxCDN
```

- **异步任务容灾策略**：系统在 `core/settings.py` 中定义了 `CELERY_ENABLED = os.getenv('CELERY_ENABLED', 'true')`。若部署环境为虚拟主机或无 Redis 守护进程的环境，系统支持 `CELERY_TASK_ALWAYS_EAGER = True`，此时邮件发送等任务自动退化为同步调用，确保系统具备极致的环境适应性。
