# 附录 02：全系统 REST API 接口契约与端点目录（API Endpoint Catalog）

本目录收录了 LiPeaks Backend 系统中全部 **10 大业务群组、112 个 RESTful API 端点** 的完整协议规范，严格依据 `core/urls.py` 与各 App 子路由定义整理。

---

## 1. 认证与用户身份端点（Auth & Users）

| HTTP 方法 | 完整 URL 路径 | 视图类 (View Class) | 认证方案 | 权限类 (Permission) | 租户 Header 规则 | 接口核心用途 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login/` | `LoginView` | None | `AllowAny` | 免头 | 统一登录，根据账号密码自动识别管理员或成员身份并签发 JWT |
| `POST` | `/api/v1/auth/refresh/` | `TokenRefreshView` | None | `AllowAny` | 免头 | 使用 `refresh_token` 换发新 `access_token` |
| `GET` | `/api/v1/auth/profile/` | `UserProfileView` | JWT | `IsAuthenticated` | 自动匹配 | 获取当前登录用户的基本信息与权限列表 |
| `PUT` | `/api/v1/auth/profile/` | `UserProfileView` | JWT | `IsAuthenticated` | 自动匹配 | 更新当前登录用户的昵称、头像、手机号等资料 |
| `GET` | `/api/v1/admin/users/` | `AdminUserViewSet.list` | JWT | `IsSuperAdminUser` | 禁头 | 超级管理员分页获取全部租户管理员 |
| `POST` | `/api/v1/admin/users/` | `AdminUserViewSet.create`| JWT | `IsSuperAdminUser` | 禁头 | 超级管理员创建新租户管理员（触发租户管理员配额核验） |
| `GET` | `/api/v1/admin/users/<id>/` | `AdminUserViewSet.retrieve` | JWT | `IsSuperAdminUser` | 禁头 | 查看指定租户管理员的详细资料 |
| `PUT` | `/api/v1/admin/users/<id>/` | `AdminUserViewSet.update` | JWT | `IsSuperAdminUser` | 禁头 | 更新指定租户管理员的资料或重置状态 |
| `DELETE` | `/api/v1/admin/users/<id>/` | `AdminUserViewSet.destroy` | JWT | `IsSuperAdminUser` | 禁头 | 软删除租户管理员 |
| `GET` | `/api/v1/admin/members/` | `MemberAdminViewSet.list` | JWT | `IsTenantAdmin \| IsSuperAdmin` | 租户隔离 | 租户管理员查看本租户成员列表 |
| `POST` | `/api/v1/admin/members/` | `MemberAdminViewSet.create` | JWT | `IsTenantAdmin \| IsSuperAdmin` | 租户隔离 | 创建租户普通成员或子账号（触发普通成员配额校验） |
| `GET` | `/api/v1/members/me/profile/` | `MemberProfileView` | JWT | `IsMemberUser` | 强制匹配 | 终端 SaaS 成员查看个人基础画像 |
| `POST` | `/api/v1/members/me/change-password/` | `MemberChangePasswordView` | JWT | `IsMemberUser` | 强制匹配 | 成员修改个人登录密码 |
| `GET/POST`| `/api/v1/members/password-reset/` | `MemberPasswordResetView` | None | `AllowAny` | 免头 | 密码找回公开 Web 页面与 Token 验证 |
| `GET/POST`| `/api/v1/members/delete-account/` | `MemberDeleteAccountView` | None | `AllowAny` | 免头 | Google Play 数据安全要求的账号注销公开页面 |

---

## 2. 租户组织与配额管控端点（Tenants & Quotas）

| HTTP 方法 | 完整 URL 路径 | 视图类 (View Class) | 权限类 | 接口说明 |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/tenants/` | `TenantListCreateView` | `TenantApiPermission` | 超管获取全平台租户分页列表 |
| `POST` | `/api/v1/tenants/` | `TenantListCreateView` | `TenantApiPermission` | 新建租户组织，自动初始化 1GB 存储/10 成员默认配额 |
| `GET` | `/api/v1/tenants/<id>/` | `TenantRetrieveUpdateDeleteView` | `TenantApiPermission` | 查询租户基本联系信息与状态 |
| `PUT` | `/api/v1/tenants/<id>/` | `TenantRetrieveUpdateDeleteView` | `TenantApiPermission` | 更新租户基础资料 |
| `DELETE` | `/api/v1/tenants/<id>/` | `TenantRetrieveUpdateDeleteView` | `TenantApiPermission` | 软删除租户（连带冻结其下所有用户登录态） |
| `GET` | `/api/v1/tenants/<id>/comprehensive/` | `TenantComprehensiveView` | `TenantApiPermission` | 聚合返回租户基本信息、配额消耗百分比与管理员列表 |
| `PUT` | `/api/v1/tenants/<id>/quota/` | `TenantQuotaUpdateView` | `TenantApiPermission` | 调整租户配额（扩容存储空间或提升成员上限） |
| `GET` | `/api/v1/tenants/<id>/quota/usage/` | `TenantQuotaUsageView` | `TenantApiPermission` | 获取存储、成员数、产品数的资源使用率报表 |
| `POST` | `/api/v1/tenants/<id>/suspend/` | `TenantSuspendView` | `TenantApiPermission` | 立即暂停租户一切业务访问 |
| `POST` | `/api/v1/tenants/<id>/activate/` | `TenantActivateView` | `TenantApiPermission` | 恢复并激活已暂停的租户 |
| `GET` | `/api/v1/tenants/<id>/users/` | `TenantUserListView` | `TenantApiPermission` | 查看归属于该租户的全部账号清单 |

---

## 3. RBAC 权限与动态前端菜单（RBAC & Menus）

| HTTP 方法 | 完整 URL 路径 | 视图类 | 权限要求 | 接口说明 |
| :--- | :--- | :--- | :--- | :--- |
| `GET/POST`| `/api/v1/rbac/permissions/` | `PermissionViewSet` | `IsSuperAdminUser` | 原子操作权限定义列表与录入 |
| `GET/POST`| `/api/v1/rbac/roles/` | `RoleViewSet` | `IsTenantAdmin \| IsSuperAdmin` | 查询本租户角色或新建自定义角色 |
| `GET` | `/api/v1/rbac/users/<type>/<id>/roles/` | `UserRolesViewSet.list` | `IsAdminUser` | 查询管理员(`user`)或成员(`member`)已绑定的角色 |
| `POST` | `/api/v1/rbac/users/<type>/<id>/roles/` | `UserRolesViewSet.create` | `IsAdminUser` | 为指定用户赋予角色（支持生效开始与截止日期） |
| `DELETE` | `/api/v1/rbac/users/<type>/<id>/roles/<rid>/` | `UserRoleDetailViewSet` | `IsAdminUser` | 移除某用户的指定角色关联 |
| `GET` | `/api/v1/rbac/users/<type>/<id>/permissions/` | `UserPermissionsViewSet` | `IsAuthenticated` | 聚合计算用户拥有的全部去重权限编码列表 |
| `POST` | `/api/v1/rbac/cache/refresh/` | `CacheRefreshViewSet` | `IsSuperAdminUser` | 刷新 Redis 全局权限缓存字典 |
| `GET` | `/api/v1/menus/` | `MenuViewSet` | `IsAuthenticated` | 获取当前用户权限裁剪后的树形侧边栏菜单 |
| `GET` | `/api/v1/menus/admin/routes/` | `AdminRoutesView` | `IsAdminUser` | 获取管理后台动态工作台路由树 |

---

## 4. 软件实体与商业授权许可（Applications & Licenses）

| HTTP 方法 | 完整 URL 路径 | 权限要求 | 接口分类 | 接口说明 |
| :--- | :--- | :--- | :--- | :--- |
| `GET/POST`| `/api/v1/applications/` | `IsTenantAdmin \| IsSuperAdmin` | 管理端 | 软件产品注册管理（生成并托管 RSA 2048 密钥对） |
| `GET/PUT` | `/api/v1/applications/<id>/` | `IsTenantAdmin \| IsSuperAdmin` | 管理端 | 软件版本号更新、发布状态更迭 |
| `GET/POST`| `/api/v1/licenses/admin/plans/` | `IsTenantAdmin \| IsSuperAdmin` | 管理端 | 配置试用版/专业版/企业版许可模板及默认激活台数 |
| `GET/POST`| `/api/v1/licenses/admin/licenses/` | `IsTenantAdmin \| IsSuperAdmin` | 管理端 | 批量签发 License 序列号、延长有效期或撤销授权 |
| `GET` | `/api/v1/licenses/admin/machine-bindings/` | `IsTenantAdmin \| IsSuperAdmin` | 管理端 | 查看所有已绑定的硬件指纹与网络 IP |
| `POST` | `/api/v1/licenses/activate/` | `AllowAny` (公开客户端) | 客户端直连 | 桌面软件首次安装，上报机器指纹在线换发数字凭证 |
| `POST` | `/api/v1/licenses/verify/` | `AllowAny` (公开客户端) | 客户端直连 | 软件冷启动校验 License 状态与防篡改签名 |
| `POST` | `/api/v1/licenses/heartbeat/` | `AllowAny` (公开客户端) | 客户端直连 | 客户端每隔 15 分钟定期上报保活包与系统资源占用 |
| `POST` | `/api/v1/licenses/unbind/` | `AllowAny` (公开客户端) | 客户端直连 | 客户端主动释放硬件绑定，腾挪设备名额 |
| `GET` | `/api/v1/licenses/info/<key>/` | `AllowAny` (公开客户端) | 客户端直连 | 凭序列号明文查询剩余可用设备额度与截止日期 |
| `GET` | `/api/v1/licenses/member/my-licenses/` | `IsMemberUser` | 成员自助 | 租户成员查看自己获配的许可证与设备状态 |
| `POST` | `/api/v1/licenses/member/apply/` | `CanApplyTrialLicense` | 成员自助 | 成员一键申请个人免费试用版 License |
| `POST` | `/api/v1/licenses/member/unbind-device/` | `IsMemberUser` | 成员自助 | 成员在网页控制台远程剔除旧电脑绑定 |

---

## 5. 工单反馈与客户管理（Feedbacks & Customers）

| HTTP 方法 | 完整 URL 路径 | 视图类 | 权限要求 | 接口说明 |
| :--- | :--- | :--- | :--- | :--- |
| `GET/POST`| `/api/v1/feedbacks/` | `FeedbackListView` | `AllowAny / IsAuthenticated` | 检索工单列表；提交新问题反馈（支持匿名） |
| `GET` | `/api/v1/feedbacks/<id>/` | `FeedbackDetailView` | `AllowAny` | 查看指定工单详情与公开讨论记录 |
| `POST` | `/api/v1/feedbacks/<id>/change-status/` | `FeedbackChangeStatusView`| `IsAdminUser` | 管理员更新工单状态并异步发送结果告知邮件 |
| `POST` | `/api/v1/feedbacks/<id>/replies/` | `FeedbackReplyListView` | `IsAuthenticated` | 针对工单进行答复；管理员可发表内部备注 |
| `POST` | `/api/v1/feedbacks/<id>/attachments/` | `FeedbackAttachmentListView` | `AllowAny` | 上传报错日志、界面截图等辅助附件 |
| `POST` | `/api/v1/feedbacks/<id>/vote/` | `FeedbackVoteView` | `IsAuthenticated` | 为心仪的功能需求投票点赞 |
| `GET/POST`| `/api/v1/customers/` | `CustomerViewSet` | `IsTenantAdmin \| IsSuperAdmin` | 多租户 CRM 客户企业档案维护 |
| `GET/POST`| `/api/v1/customers/tenants/relations/` | `CustomerTenantRelationViewSet` | `IsTenantAdmin` | 绑定客户企业与租户的合同期与关系类型 |

---

## 6. 内容管理与社交互动（CMS & Interactions）

| HTTP 方法 | 完整 URL 路径 | 视图类 | 权限要求 | 接口说明 |
| :--- | :--- | :--- | :--- | :--- |
| `GET/POST`| `/api/v1/cms/articles/` | `ArticleViewSet` | `IsAdminUser` (写) / `AllowAny` (读) | 文章增删改查（支持无限极父子系列树） |
| `GET` | `/api/v1/cms/articles/<id>/` | `ArticleViewSet.retrieve` | 依可见性规则检查 | 阅读文章（自动校验公开/密码/仅登录规则并累计 PV） |
| `GET` | `/api/v1/cms/categories/tree/` | `CategoryViewSet` | `AllowAny` | 获取包含当前语言翻译的分类多级树 |
| `GET/POST`| `/api/v1/cms/member/articles/` | `MemberArticleViewSet` | `IsMemberUser` | 租户普通成员前台创作列表与草稿提交 |
| `POST` | `/api/v1/interactions/favorites/` | `ArticleFavoriteViewSet` | `IsMemberUser` | 收藏指定文章 |
| `DELETE` | `/api/v1/interactions/favorites/<id>/`| `ArticleFavoriteViewSet` | `IsMemberUser` | 取消文章收藏 |
| `POST` | `/api/v1/interactions/article-likes/` | `ArticleLikeViewSet` | `AllowAny` | 对文章点赞（支持游客基于 IP 去重） |
| `POST` | `/api/v1/interactions/follows/` | `MemberFollowViewSet` | `IsMemberUser` | 关注某位作者成员 |

---

## 7. 微信集成与 We-RSS 订阅抓取（WeChat & We-RSS）

| HTTP 方法 | 完整 URL 路径 | 权限要求 | 接口分类 | 接口说明 |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/wechat/login/` | `AllowAny` | 小程序端 | 凭 `js_code` 完成微信一键登录并签发 JWT |
| `POST` | `/api/v1/wechat/draft/add/` | `IsAdminUser` | 平台运营 | 将平台文章打包推送到微信公众号草稿箱 |
| `GET` | `/api/v1/we-rss/image-proxy/` | `AllowAny` | 资源网关 | 微信防盗链图片流式反代（解决图片 403 跨域） |
| `POST` | `/api/v1/we-rss/credentials/login-sessions/` | `IsAdminUser` | 抓取中控 | 获取公众号后台扫码登录二维码 UUID |
| `GET` | `/api/v1/we-rss/credentials/login-sessions/<sid>/` | `IsAdminUser` | 抓取中控 | 轮询扫码确认状态并捕获 Token/Cookie 快照 |
| `POST` | `/api/v1/we-rss/feeds/<id>/sync_by_history/` | `IsAdminUser` | 抓取中控 | 投递 Celery 任务全量抓取公众号历史图文 |
| `GET` | `/api/v1/we-rss/articles/<id>/markdown-with-images/` | `IsAuthenticated` | 知识沉淀 | 将微信排版文章转换为标准 Markdown |
| `POST` | `/api/v1/we-rss/articles/export-markdown-images/` | `IsAuthenticated` | 知识沉淀 | 批量打包下载包含本地图片的 ZIP 离线知识包 |
| `GET` | `/api/v1/we-rss/rss/<feed_id>/` | `AllowAny` | 订阅源 | 输出符合 RSS 2.0 标准规范的 XML 订阅数据源 |
