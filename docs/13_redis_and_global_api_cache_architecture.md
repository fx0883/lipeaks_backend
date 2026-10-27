# 模块详细分析 13：Redis 基础设施与全局 API 缓存架构

本文档针对系统的 Redis 集中式缓存、Celery 异步队列中介及全局 API 缓存中间件体系进行全生命周期设计与落地记录。

---

## 1. 任务 1 完成记录：依赖配置与 Python 驱动升级

### 1.1 背景与现状
原工程 `requirements.txt` 中仅声明了 `redis==8.0.0` 与 `celery==5.6.3`，缺少 Django 生态中最主流、功能最完备的 Redis 适配库 `django-redis`。这导致 `core/settings.py` 的缓存后端只能回退到 Django 原生驱动或内存 `LocMemCache`，缺失连接池微调、集群容灾（`IGNORE_EXCEPTIONS`）及底层 Redis 原生客户端操作（`get_redis_connection`）等高级特性。

### 1.2 改造实施
1. **依赖升级**：
   - 在 [`requirements.txt`](../requirements.txt) 追加 `django-redis==7.0.0`。
   - 适配环境：Python 3.13 / Django 6.1.2 / redis-py。
2. **环境安装与验证**：
   - 执行安装：`py -3.13 -m pip install django-redis==7.0.0`
   - 验证结果：`django_redis 7.0.0` 成功安装并可通过 Python 解释器无警告导入。

---

## 2. 任务 2 完成记录：本地 Docker Compose 编排与双模基础设施

### 2.1 编排设计
为满足本地开发环境的快速启动与跨平台交付，在项目根目录新建了规范轻量的 [`docker-compose.yml`](../docker-compose.yml)：
- **基础镜像**：`redis:7-alpine`
- **容器命名**：`lipeaks_redis`
- **端口映射**：`6379:6379`
- **持久化挂载**：`redis_data:/data`（命名卷，保证数据重启不丢失）
- **健康检查**：`CMD redis-cli ping`（每 5 秒探测一次，重试 5 次）

### 2.2 运行与维护指引
- **Docker 模式（推荐生产/日常开发）**：
  在启动 Docker Desktop 之后，在项目根目录下执行：
  ```bash
  # 后台启动 Redis 容器
  docker compose up -d

  # 查看容器运行与健康状态
  docker compose ps

  # 查看实时日志
  docker compose logs -f redis

  # 停止并保留数据
  docker compose down
  ```
- **Windows 本地独立运行双模兜底（Dev Fallback）**：
  若在纯 Windows 开发宿主机上未开启 Docker Desktop，系统已自动兼容并接入本地 `D:\Software\Redis-x64-5.0.14.1\redis-server.exe`，保证随时随地保持 6379 端口畅通无阻，开发与测试零障碍。

---

## 3. 任务 3 完成记录：环境变量分库隔离与缓存初始化治理

### 3.1 环境变量拓扑与多库物理隔离
为杜绝业务清空缓存（`cache.clear()`）导致后台排队的 Celery 异步任务被误删清空，系统严格实施了 Redis 分库隔离规范：
- **Redis DB 0（异步任务总线）**：
  - `CELERY_BROKER_URL=redis://127.0.0.1:6379/0`
  - `CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0`
  - 承载 `we_rss` 文章抓取同步、`feedbacks` 邮件发送与系统 Beat 定时调度。
- **Redis DB 1（业务与全局 API 缓存）**：
  - `REDIS_URL=redis://127.0.0.1:6379/1`
  - 承载全局 API 缓存、微信 Access Token、租户验证器 `TenantValidator` 对象缓存、密码找回防刷与 RBAC 权限缓存。
- **全局 API 缓存开关**：
  - `API_CACHE_ENABLED=True`（全局总开关，可快速热切）
  - `API_CACHE_DEFAULT_TIMEOUT=120`（默认 2 分钟安全 TTL）

### 3.2 Django 6 与 PyMySQL 驱动兼容
针对 Django 6.x 底层 `mysqlclient` 版本检查机制，在 `core/settings.py` 中对 `pymysql.version_info` 注入标准兼容垫片，彻底消除连接数据库时的启动异常。

### 3.3 实测验证
- **Django 缓存读写测试**：成功写入键 `test_key` 并准确读取出 `hello_redis`，底层自动追加标准键前缀 `lipeaks:1:test_key`。
- **Celery Broker 握手测试**：Celery 成功连通 `127.0.0.1:6379/0`，返回 `conn.connected == True`。

---

## 4. 任务 4 完成记录：全局 API 缓存中间件设计与落地

### 4.1 架构实现
在 [`common/middleware/api_cache_middleware.py`](../common/middleware/api_cache_middleware.py) 中实现了全站统一的 `APICacheMiddleware`：
- **装配位置**：位于 `APIAuthMiddleware`、`TenantMiddleware` 之后，在 `EnhancedAPILoggingMiddleware` 之前。确保在执行缓存检索前，用户身份与租户上下文已可靠解析。
- **四重安全隔离 Key 算法**：
  $$\text{Key} = \text{api\_cache}:\{\text{tenant\_id}\}:\{\text{user\_scope}\}:\{\text{normalized\_path}\}:\{\text{query\_params\_hash}\}$$
  - `tenant_id`：基于 ContextVar 与请求头解析租户 ID（公共访问则归为 `public`）；
  - `user_scope`：登录用户按 `user_{id}` 单独隔离，未登录公用 `anon`；
  - `normalized_path`：标准化去除结尾斜杠的 URL 路径；
  - `query_params_hash`：对 Query 参数按 Key 升序排序后计算 SHA256 哈希（截取前 16 位），消除 URL 参数无序抖动导致的假未命中。

### 4.2 缓存黑名单与安全边界
严格排除非幂等、认证敏感、实时验签与流式资源：
- 认证与账号安全：`/api/v1/auth/`、`/api/v1/members/password-reset/`、`/api/v1/members/delete-account/`
- API 文档与元数据：`/api/v1/schema/`、`/api/v1/docs/`、`/api/v1/redoc/`
- 实时健康探针与心跳：`/api/v1/health/`、`/api/v1/licenses/heartbeat/`、`/api/v1/licenses/verify/`、`/api/v1/licenses/activate/`、`/api/v1/licenses/status/`
- 流式反代：`/api/v1/we-rss/images/proxy/`

### 4.3 读写联动失效与主动穿透机制
1. **写操作自动联动失效**：
   当收到 `POST`、`PUT`、`PATCH`、`DELETE` 请求且状态码为成功（2xx）时，中间件自动剥离资源 ID，提取业务前缀（如 `/api/v1/cms/articles/123/` 提取为 `/api/v1/cms/articles`），并通过 Redis 模式匹配 `*api_cache:{tenant_id}:*:{resource_prefix}*` 批量失效当前租户下对应资源的全部 API 缓存。
2. **主动刷新机制**：
   客户端请求头携带 `Cache-Control: no-cache`、`Pragma: no-cache` 或 URL 携带 `?nocache=1` 时，服务端自动穿透缓存查库，并在响应时刷新 Redis 缓存。
3. **可观测响应头**：
   - `X-Cache: HIT`（命中 Redis 缓存并直接返回）
   - `X-Cache: MISS`（未命中并回写 Redis 缓存）
   - `X-Cache-Key: <key>`（便于快速定位排查）

---

3. **可观测响应头**：
   - `X-Cache: HIT`（命中 Redis 缓存并直接返回）
   - `X-Cache: MISS`（未命中并回写 Redis 缓存）
   - `X-Cache-Key: <key>`（便于快速定位排查）

---

## 5. 任务 5 完成记录：端到端连通性与完整回归测试报告

### 5.1 自动化测试覆盖
新建了专属测试套件 [`common/tests/test_api_cache_middleware.py`](../common/tests/test_api_cache_middleware.py)，全方位覆盖：
1. **首次未命中与回写（MISS）、二次请求命中返回（HIT）**：验证响应头 `X-Cache` 与 JSON 数据一致性；
2. **多租户严格隔离性**：验证 Tenant Alpha 无法命中 Tenant Beta 的缓存；
3. **用户与匿名身份隔离**：不同 UID 用户与匿名访问生成独立隔离 Key；
4. **Query 参数敏感与乱序一致性**：不同分页参数独立缓存，同参数不同顺序正确哈希归一；
5. **客户端主动穿透控制**：验证 `Cache-Control: no-cache` 与 `?nocache=1` 绕过缓存；
6. **黑名单敏感接口豁免**：验证 `/auth/`、`/licenses/heartbeat/` 等接口绝不参与缓存；
7. **写操作联动失效**：验证执行 `POST/PUT/DELETE` 成功后，自动模糊清除相关资源的全部 GET 缓存；
8. **错误码与非 JSON 响应防缓存保护**：验证 400 异常及 HTML 响应不被写入缓存。

### 5.2 真实 Redis（DB 1）端到端集成实测
在宿主机运行中的 Redis 实例上，模拟全链路请求：
- **第 1 次 GET 请求**：缓存未命中，响应返回 `X-Cache: MISS`，在 Redis DB 1 成功生成并存储键 `api_cache:tenant_99:anon:/api/v1/cms/articles:ffbbffbee53fa0b2`；
- **第 2 次 GET 请求**：瞬时命中，响应直接返回 `X-Cache: HIT`，零数据库查询开销；
- **写操作执行**：模拟 `POST /api/v1/cms/articles/` 创建文章，触发中间件模糊匹配并成功删除 `*api_cache:tenant_99:*:/api/v1/cms/articles*`；
- **第 3 次 GET 请求**：由于相关缓存已精准失效，请求再次返回 `X-Cache: MISS` 并刷新回写新数据，实现近乎零延迟的数据强一致性！

### 5.3 全库回归测试成绩单
- **测试框架**：`pytest 8.3.5` / `pytest-django 4.11.1`
- **执行命令**：`py -3.13 -m pytest -q`
- **总耗时**：262.71s
- **测试结果**：**666 passed, 7 skipped, 0 failed（100% 通过）**

---

## 6. 真实业务 GET API 缓存加速与实测记录

### 6.1 实测接口选型与覆盖场景
通过包含真实数据库与本地运行中的 Redis 实例对 4 个具有代表性的典型业务 GET 接口进行了实测检验：
1. **系统全局公共接口**：`GET /api/v1/menus/`（导航菜单树）
2. **多租户业务接口**：`GET /api/v1/cms/categories/`（CMS 分类）
3. **复杂参数分页接口**：`GET /api/v1/cms/articles/?status=published&page=1&page_size=10`（文章列表）
4. **安全敏感豁免接口**：`GET /api/v1/feedbacks/health/`（健康探针，黑名单）

### 6.2 实测响应指标对照表

| 接口名称 | URL 路径 | 第 1 次请求（查库写缓存） | 第 2 次请求（Redis 缓存直出） | 加速比（提速倍数） | 客户端主动穿透（`no-cache`） |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **菜单列表** | `/api/v1/menus/` | 322.05 ms (`MISS`) | **0.35 ms (`HIT`)** | **931.0 倍** | 成功穿透 (`MISS`) |
| **文章分类** | `/api/v1/cms/categories/` | 8.94 ms (`MISS`) | **1.47 ms (`HIT`)** | **6.1 倍** | 成功穿透 (`MISS`) |
| **分页文章** | `/api/v1/cms/articles/?...` | 17.57 ms (`MISS`) | **2.14 ms (`HIT`)** | **8.2 倍** | 成功穿透 (`MISS`) |
| **健康探针** | `/api/v1/feedbacks/health/` | 42.98 ms (`NONE`) | 实时透传 (`NONE`) | 实时探针不缓存 | 保持实时 |

---
