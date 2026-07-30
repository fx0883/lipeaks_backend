# LiPeaks Backend — 工作区上下文

> 本文件由 WorkBuddy `/init` 生成，供后续会话快速加载项目上下文。最后更新：2026-06-29。

## 项目概览

**LiPeaks Backend** —— 企业级多租户 SaaS 平台后端系统。基于 Django 构建的现代化、高性能、可扩展的多租户架构，为不同组织/客户（租户）提供完全隔离的应用环境。

- **仓库**：`fx0883/lipeaks_backend`
- **类型**：Django 单体后端 + DRF API
- **领域**：多租户 SaaS（CMS、CRM、订单、许可证、打卡、积分、反馈、通知、微信小程序等）

## 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 语言 | Python | 3.13 (Dockerfile 用 3.13-slim) |
| 框架 | Django | 6.0.6 |
| API | Django REST Framework | 3.17.1 |
| API 文档 | drf-spectacular + drf-yasg | - |
| 数据库 | MySQL | 8.0 (PyMySQL 驱动) |
| 异步任务 | Celery + Redis | celery 5.6.3 / redis 8.0 |
| 缓存/消息 | Redis | - |
| 认证 | JWT (自研) + RBAC | - |
| 多语言 | django-parler | 2.4 (zh-hans/en/zh-hant/ja/ko/fr) |
| 部署 | Docker + Nginx + Gunicorn | - |
| 静态 | WhiteNoise | - |
| 测试 | pytest + pytest-django + factory_boy | - |

## 核心架构约定（CRITICAL — 改代码前必读）

### 1. 多租户隔离

所有需要租户隔离的模型 **必须** 继承 `common.models.BaseModel`：

```python
from common.models import BaseModel

class MyModel(BaseModel):
    name = models.CharField(max_length=100)
    # 自动获得：tenant FK + created_at + updated_at + is_deleted + 软删除
```

- **`objects`** = `TenantManager`（默认只返回当前租户的数据，已软删除的自动过滤）
- **`original_objects`** = 原始 Manager（管理员访问所有租户数据时用）
- 软删除：调用 `instance.soft_delete()`，**不要** 用 `.delete()`

### 2. 租户解析

- 中间件 `common.middleware.tenant_middleware.TenantMiddleware` 从请求解析当前租户
- 需要租户校验的路径配置在 `TENANT_ISOLATED_API_PATHS`（settings.py）
- 公开路径（免租户校验）配置在 `TENANT_PUBLIC_API_PATHS`
- Member 端 CMS 路径需携带 `X-Tenant-ID` 头（受 `FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER` 开关控制）

### 3. 认证体系

- 自定义认证：`common.authentication.api_auth.APIJWTAuthentication`（API 端）+ `WebSessionAuthentication`（Web 端）
- 自定义用户模型：`users.User`（`AUTH_USER_MODEL = 'users.User'`）
- JWT 配置在 `JWT_AUTH`（HS256，默认 7 天有效 + 28 天刷新）

### 4. API 规范

- URL 前缀：`/api/v1/<app>/`
- 响应格式：统一由 `common.renderers.StandardJSONRenderer` 包装
- 异常处理：`common.exceptions.custom_exception_handler`
- 分页：`common.pagination.StandardResultsSetPagination`（PAGE_SIZE=10）
- API 文档：Swagger UI → `/api/v1/docs/`，ReDoc → `/api/v1/redoc/`，Schema → `/api/v1/schema/`

### 5. 国际化

- 默认语言 `zh-hans`，时区 `UTC`（`USE_TZ=True`）
- 翻译文件在 `locale/`，使用 `django-parler` 做模型字段翻译
- `PARLER_DEFAULT_LANGUAGE_CODE = 'zh-hans'`，回退语言也是简体中文

## 应用清单（INSTALLED_APPS）

| App | 路由前缀 | 说明 |
|-----|---------|------|
| `common` | `/api/v1/common/` | 基础模型、中间件、认证、渲染器、权限、工具 |
| `tenants` | `/api/v1/tenants/` | 租户管理 |
| `users` | `/api/v1/` + `/api/v1/auth/` | 用户、认证、Member 密码重置/删号 |
| `rbac` | `/api/v1/rbac/` | RBAC 权限系统 |
| `cms` | `/api/v1/cms/` | 内容管理（文章、媒体、模板） |
| `customers` | `/api/v1/customers/` | 客户关系管理 |
| `orders` | `/api/v1/orders/` | 订单管理 |
| `licenses` | `/api/v1/licenses/` | 许可证管理（激活/心跳/解绑） |
| `applications` | `/api/v1/` | 应用管理（整合 licenses + feedbacks） |
| `feedbacks` | `/api/v1/feedbacks/` | 用户反馈系统（Celery 邮件任务） |
| `interactions` | `/api/v1/interactions/` | 收藏、点赞等互动 |
| `notifications` | `/api/v1/notifications/` + `/api/v1/admin/notifications/` | 通知系统（成员端 + 管理端） |
| `points` | `/api/v1/points/` | 多租户积分系统 |
| `check_system` | `/api/v1/check-system/` | 打卡系统 |
| `menus` | `/api/v1/menus/` | 动态菜单管理 |
| `charts` | `/api/v1/admin/charts/` | 图表/数据可视化 |
| `wechat` | `/api/v1/wechat/` | 微信小程序登录 |
| `we_rss` | `/api/v1/we-rss/` | RSS 订阅 |
| `docs_view` | `/docs/` | 文档查看应用 |

## 关键配置文件

| 文件 | 用途 |
|------|------|
| `core/settings.py` | 主配置（开发） |
| `core/settings_docker.py` | Docker 环境配置 |
| `core/settings_test.py` | 测试环境配置 |
| `core/urls.py` | 根 URL 路由 |
| `core/celery.py` | Celery 应用 |
| `.env` | 环境变量（不入库） |
| `.env.example` | 环境变量模板 |
| `docker-compose.yml` | 本地 Docker 编排（db + web + frontend + cms） |
| `Dockerfile` | 后端镜像构建 |
| `docker-entrypoint.sh` | 容器启动脚本（迁移/超级用户/快照导入） |
| `requirements.txt` | 生产依赖 |
| `requirements-dev.txt` | 开发依赖 |
| `requirements-prod.txt` | 生产额外依赖 |

## 环境变量（必需）

```
DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT   # MySQL
SECRET_KEY                                         # Django 密钥
DEBUG / LOG_TO_CONSOLE                             # 调试与日志
CELERY_ENABLED, CELERY_BROKER_URL, CELERY_RESULT_BACKEND  # 异步任务
WECHAT_APPID, WECHAT_SECRET                        # 微信小程序
```

## 常用命令

```bash
# 启动开发服务器
python manage.py runserver

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# Celery worker（开发）
celery -A core worker -l info

# Celery beat（定时任务）
celery -A core beat -l info

# 测试
pytest

# Docker 一键启动
docker-compose up -d
docker-compose exec web python manage.py migrate
```

## 部署拓扑

```
Nginx (80)
  ├── frontend (admin, :8848)       —— fx0883/lipeaks_admin
  ├── cms frontend (:80)            —— fx0883/lipeaks_espressox_cms
  └── web (:8000)                   —— fx0883/lipeaks_backend (Gunicorn)
        └── MySQL (:3306)
        └── Redis (Upstash)
```

## 注意事项

- `DEBUG` 在 settings.py 中实际读取的是 `INFO` 环境变量（历史遗留，注意区分）
- `ALLOWED_HOSTS = ['*']`（开发），生产需收紧
- CORS 当前 `CORS_ALLOW_ALL_ORIGINS = True`，生产建议改白名单
- 日志：`LOG_TO_CONSOLE=True` 时只输出控制台，否则写 `logs/` 下轮转文件（保留 15 天）
- `schema.yml` / `swagger.json` 是生成物，体积大，谨慎改动
- `media/` 目录有近 2 万张图片，注意别误提交
