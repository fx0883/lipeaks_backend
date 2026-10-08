# 附录 01：全库数据模型与数据字典规范（Database Data Dictionary）

本规范系统梳理了 LiPeaks Backend 项目中全部 **16 个 App、64 张数据库物理表** 的模型设计、字段定义、主外键约束、索引与业务规则。

---

## 1. 数据库总体设计规范

1. **命名规范**：
   - 物理表名统一采用 `<app_name>_<model_name>` 小写下划线命名法（如 `licenses_license`, `cms_article`），部分历史核心表保持精简别名（如 `tenant`, `user`, `member`）。
   - 主键统一采用自增 64 位整型 `id BigAutoField PRIMARY KEY`。
2. **多租户基准字段（BaseModel）**：
   - 凡继承自 `common.models.BaseModel` 的表，均强制包含：
     - `tenant_id` (`BIGINT UNSIGNED FK -> tenant.id`, `ON DELETE CASCADE`, 带索引, 允许 NULL 表示平台级数据)
     - `created_at` (`DATETIME(6)`, `auto_now_add=True`, 带索引)
     - `updated_at` (`DATETIME(6)`, `auto_now=True`, 带索引)
     - `is_deleted` (`TINYINT(1)`, `default=0`, 带索引)
3. **字符集与排序规则**：
   - 数据库字符集：`utf8mb4`
   - 排序规则：`utf8mb4_unicode_ci`

---

## 2. 基础设施与租户组织表（common & tenants）

### 2.1 `tenant`（租户主表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 租户唯一主键 |
| `name` | Varchar(100) | Unique | - | 租户企业/组织名称 |
| `code` | Varchar(50) | Unique, Nullable | - | 租户唯一编码（小写识别代号） |
| `status` | Varchar(20) | Index | 'active' | 状态：`active`(活跃), `suspended`(暂停), `deleted`(已删除) |
| `contact_name`| Varchar(50) | Nullable | - | 联系人姓名 |
| `contact_email`| Varchar(254)| Nullable | - | 联系人电子邮箱 |
| `contact_phone`| Varchar(20) | Nullable | - | 联系人电话 |
| `created_at` | DateTime | Index | NOW | 创建时间 |
| `updated_at` | DateTime | Index | NOW | 更新时间 |
| `is_deleted` | Boolean | Index | 0 | 软删除标记 |

### 2.2 `tenant_quota`（租户资源配额表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `tenant_id` | BigInt | OneToOne FK -> `tenant.id` | - | 关联租户 |
| `max_users` | Int | - | 10 | 租户最大允许成员数 |
| `max_admins` | Int | - | 2 | 租户最大允许管理员数 |
| `max_storage_mb`| Int | - | 1024 | 最大文件存储容量 (MB) |
| `max_products`| Int | - | 100 | 最大允许创建软件产品数 |
| `current_storage_used_mb` | Int | - | 0 | 当前已使用存储容量 (MB) |
| `created_at` | DateTime | - | NOW | 配额初始化时间 |
| `updated_at` | DateTime | - | NOW | 最近配额变更时间 |

### 2.3 `common_api_log`（API 访问与性能审计表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 日志主键 |
| `tenant_id` | BigInt | FK -> `tenant.id`, Index | Nullable | 触发请求所属租户 |
| `user_id` | BigInt | FK -> `user.id`, Index | Nullable | 操作人（管理员） |
| `ip_address` | Varchar(50) | Index | - | 客户端公网 IP |
| `request_method`| Varchar(10) | Index | - | HTTP 请求方法 (GET/POST/PUT/DELETE) |
| `request_path` | Varchar(255)| Index | - | 请求路由 URL |
| `view_name` | Varchar(255)| Nullable | - | 处理该请求的 View 类名 |
| `query_params` | JSON | Nullable | - | GET 请求参数快照 |
| `request_body` | JSON | Nullable | - | POST/PUT 载荷快照 |
| `status_code` | Int | Index | - | 响应 HTTP 状态码 (200/400/401/500) |
| `response_time`| Int | - | - | 耗时时长 (ms) |
| `status_type` | Varchar(10) | - | - | `success` 或 `error` |
| `response_body`| JSON | Nullable | - | 返回数据内容快照 |
| `error_message`| LongText | Nullable | - | 异常堆栈信息 |
| `user_agent` | Varchar(500)| Nullable | - | 客户端 UA 串 |
| `created_at` | DateTime | Index | NOW | 访问发生时间 |

---

## 3. 双身份与 RBAC 权限表（users & rbac & menus）

### 3.1 `user`（管理端用户表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `username` | Varchar(150)| Unique | - | 登录账号 |
| `password` | Varchar(128)| - | - | PBKDF2/Argon2 密文散列 |
| `tenant_id` | BigInt | FK -> `tenant.id`, Index | Nullable | 所属租户（超管为 NULL） |
| `email` | Varchar(254)| - | - | 管理员邮箱 |
| `phone` | Varchar(11) | Nullable | - | 联系手机 |
| `nick_name` | Varchar(30) | Nullable | - | 昵称 |
| `avatar` | Varchar(200)| - | '' | 头像 URL |
| `status` | Varchar(20) | - | 'active' | `active`, `suspended`, `inactive` |
| `is_admin` | Boolean | - | 1 | 始终为 True |
| `is_super_admin`| Boolean | - | 0 | 1 为平台超管，0 为租户管理员 |
| `is_staff` | Boolean | - | 1 | 是否允许登入管理后台 |
| `is_superuser` | Boolean | - | 0 | Django 原生超级权限（超管为 1） |
| `is_deleted` | Boolean | Index | 0 | 软删除标记 |
| `date_joined` | DateTime | Index | NOW | 注册加入时间 |

### 3.2 `member`（SaaS 终端成员表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `username` | Varchar(150)| Unique | - | 登录账号 |
| `password` | Varchar(128)| - | - | 密码密文散列 |
| `tenant_id` | BigInt | FK -> `tenant.id`, Index | Nullable | 归属的租户组织 |
| `parent_id` | BigInt | FK -> `member.id`, Nullable| - | 父账号 ID（非空代表此实例为子账号） |
| `email` | Varchar(254)| - | - | 成员邮箱 |
| `phone` | Varchar(11) | Nullable | - | 成员手机 |
| `nick_name` | Varchar(30) | Nullable | - | 成员昵称 |
| `is_staff` | Boolean | - | 0 | 始终为 False（杜绝越权访问后台） |
| `is_active` | Boolean | - | 1 | 是否允许登录（子账号被强制置 0） |
| `status` | Varchar(20) | - | 'active' | 账号生命周期状态 |
| `is_deleted` | Boolean | Index | 0 | 软删除 |

### 3.3 `rbac_permission`（原子权限定义表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `code` | Varchar(100)| Unique | - | 权限识别码（如 `license:generate`） |
| `name` | Varchar(100)| - | - | 权限中文说明 |
| `category` | Varchar(50) | Index | - | 模块归类（如“授权管理”） |
| `is_system` | Boolean | - | 0 | 系统基础权限，禁止删除 |

### 3.4 `rbac_role`（角色表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `name` | Varchar(100)| - | - | 角色名称（如“审计员”、“技术支持”） |
| `code` | Varchar(50) | - | - | 角色编码 |
| `tenant_id` | BigInt | FK -> `tenant.id`, Nullable| - | 所属租户（NULL 代表全平台系统角色） |
| `is_system` | Boolean | - | 0 | 是否为系统内置角色 |
| *联合唯一约束* | - | Unique(`name`, `tenant_id`)| - | 同一租户下角色名称唯一 |

### 3.5 `rbac_user_role`（多态用户角色指派表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `user_type` | Varchar(10) | Index | - | 目标身份：`user`(管理员) 或 `member`(成员) |
| `user_id` | Int | Index | - | 关联的主体主键 ID |
| `role_id` | BigInt | FK -> `rbac_role.id` | - | 赋予的角色 |
| `is_active` | Boolean | - | 1 | 启用/冻结状态 |
| `start_date` | Date | Nullable | - | 角色生效起始日 |
| `end_date` | Date | Nullable | - | 角色到期截止日 |
| *联合唯一约束* | - | Unique(`user_type`, `user_id`, `role_id`)| - | 防止重复赋权 |

---

## 4. 商业授权与软件管理表（applications & licenses）

### 4.1 `applications_application`（软件产品主表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `tenant_id` | BigInt | FK -> `tenant.id`, Index | - | 所属租户 |
| `name` | Varchar(100)| - | - | 软件全名（如 "CompressX"） |
| `code` | Varchar(50) | Index | - | 软件代码（租户内唯一） |
| `current_version`| Varchar(50)| - | '1.0.0' | 当前公开发布版本号 |
| `status` | Varchar(20) | Index | 'active' | `development/testing/active/archived` |
| `is_active` | Boolean | - | 1 | 是否上架分发 |
| `metadata` | JSON | - | {} | 关键扩展元数据（包含 RSA 公私钥） |

### 4.2 `licenses_license_plan`（许可方案模板表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `application_id`| BigInt | FK -> `applications_application.id` | - | 绑定的软件产品 |
| `name` | Varchar(100)| - | - | 方案套餐名 |
| `code` | Varchar(50) | - | - | 方案代号（如 `ENTERPRISE_YEARLY`） |
| `plan_type` | Varchar(20) | Index | - | `trial`, `basic`, `professional`, `enterprise` |
| `default_max_activations` | Int | - | 1 | 默认最大激活设备台数 |
| `default_validity_days` | Int | - | 365 | 默认有效天数 |
| `features` | JSON | - | {} | 该方案开启的高级功能 JSON 开关 |
| `price` | Decimal(10,2)| - | 0.00 | 售价 |
| `currency` | Varchar(3) | - | 'CNY' | 结算币种 |

### 4.3 `licenses_license`（许可证实例表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `tenant_id` | BigInt | FK -> `tenant.id`, Index | - | 签发租户 |
| `application_id`| BigInt | FK -> `applications_application.id` | - | 授权软件 |
| `plan_id` | BigInt | FK -> `licenses_license_plan.id` | - | 对应的资费套餐 |
| `license_key` | Varchar(200)| Unique | - | 25 位易读明文 Key |
| `license_hash`| Varchar(64) | Unique, Index | - | SHA-256 摘要（用于极速验签查询） |
| `customer_name`| Varchar(100)| - | '' | 购买客户姓名 |
| `customer_email`| Varchar(254)| - | '' | 接收通知邮箱 |
| `max_activations` | Int | - | 1 | 最终核定设备上限 |
| `current_activations` | Int | - | 0 | 当前已激活机器数 |
| `issued_at` | DateTime | - | NOW | 签发时间 |
| `expires_at` | DateTime | Index | - | 授权截止时间戳 |
| `last_verified_at` | DateTime | Nullable | - | 上次客户端心跳核验时间 |
| `status` | Varchar(20) | Index | 'generated' | `generated/activated/suspended/revoked/expired` |

### 4.4 `licenses_machine_binding`（机器指纹绑定表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `license_id` | BigInt | FK -> `licenses_license.id`, Index | - | 所属许可证 |
| `machine_id` | Varchar(100)| Index | - | 客户端设备物理 ID |
| `machine_fingerprint` | Varchar(64)| Index | - | CPU/MAC/BIOS 联合计算的 64 位指纹 |
| `encrypted_hardware_info`| LongText | - | - | AES 密文存储的硬件详细序列号 |
| `os_info` | JSON | - | {} | 操作系统、内核版本 |
| `last_ip_address` | GenericIP | Nullable | - | 最近联网 IP |
| `status` | Varchar(20) | Index | 'active' | `active`, `inactive`, `blocked` |
| *联合唯一约束* | - | Unique(`license_id`, `machine_fingerprint`)| - | 单卡单机唯一对应 |

---

## 5. 内容与多语言国际化表（cms & interactions）

### 5.1 `cms_article`（文章主表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `tenant_id` | BigInt | FK -> `tenant.id`, Index | - | 所属租户 |
| `title` | Varchar(255)| Index | - | 文章标题 |
| `slug` | Varchar(255)| Unique, Index | - | 网页 SEO URL 别名 |
| `content` | LongText | - | - | 正文内容 |
| `content_type` | Varchar(20) | - | 'markdown' | `markdown`, `html`, `image`, `code` 等 |
| `parent_id` | BigInt | FK -> `cms_article.id`, Index | Nullable | 父级文章 ID（自关联目录树） |
| `user_id` | BigInt | FK -> `user.id`, Index | Nullable | 管理员作者 |
| `member_id` | BigInt | FK -> `member.id`, Index | Nullable | 租户成员作者 |
| `status` | Varchar(20) | Index | 'draft' | `draft`, `pending`, `published`, `archived` |
| `visibility` | Varchar(20) | - | 'public' | `public`, `private`, `password` |
| `password` | Varchar(128)| Nullable | - | 密码访问保护 |
| `published_at`| DateTime | Index, Nullable | - | 正式发布时间戳 |
| `sort_order` | Int | - | 0 | 排序权重 |
| *数据库检查约束* | CheckConstraint | `article_one_author_required` | - | `user` 与 `member` 有且仅有一个非空 |

### 5.2 `cms_category` 与 `cms_category_translation`（多语言分类表）
- `cms_category`：存储共享字段 `id`, `slug (Unique)`, `parent_id (自关联分类树)`, `sort_order`, `is_active`。
- `cms_category_translation`：由 `django-parler` 自动管理：
  - `master_id` (`FK -> cms_category.id`)
  - `language_code` (`Varchar(15)`, 索引，如 `zh-hans`, `en`, `ja`)
  - `name` (`Varchar(100)`)
  - `description` (`TextField`)
  - `seo_title`, `seo_description`
  - 联合唯一约束：`Unique('master_id', 'language_code')`

---

## 6. 微信生态与 RSS 聚合表（wechat & we_rss）

### 6.1 `we_rss_credential`（公众号凭证表）
| 字段名 | 物理类型 | 约束 / 索引 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigInt | PK, Auto Increment | - | 主键 |
| `tenant_id` | BigInt | FK -> `tenant.id` | - | 归属租户 |
| `name` | Varchar(100)| - | - | 凭证标签说明 |
| `token` | Varchar(255)| - | - | 微信公众平台交互 Token |
| `cookies` | LongText | - | - | 微信公众平台加密会话 Cookie |
| `status` | Varchar(20) | - | 'active' | `active`, `expired`, `invalid` |
| `is_default` | Boolean | - | 0 | 是否为默认抓取凭据 |

### 6.2 `we_rss_feed` 与 `we_rss_article`（公众号与文章库）
- `we_rss_feed`：记录公众号基本信息：`fakeid (Unique)`, `name`, `avatar`, `last_sync_at`。
- `we_rss_article`：存储收录的微信图文：
  - `feed_id` (`FK -> we_rss_feed.id`)
  - `title` (`Varchar(255)`)
  - `link` (`Varchar(1024)`, 微信原文外链)
  - `content_html` (`LongText`)
  - `publish_time` (`DateTime`, 带索引)
  - `read_count`, `like_count` (`Int`, 阅读点赞量指标)
