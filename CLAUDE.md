# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

LiPeaks Backend — a multi-tenant SaaS platform backend. Django 6.0 + DRF monolith with ~22 apps (CMS, CRM, orders, licenses, check-in, points, feedback, notifications, WeChat mini-program, RSS, LLM gateway, image prompt). MySQL 8 (via PyMySQL), Celery + Redis for async, `django-parler` for model-field translations, custom JWT + RBAC auth.

`WORKBUDDY.md` at the repo root holds an extended app-by-app breakdown and deployment topology; read it when you need the full map.

## Commands

```bash
# Dev server (uses core.settings by default)
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Tests — MUST use the test settings (SQLite, migrations disabled, MD5 hasher)
pytest --ds=core.settings_test                          # pytest-based tests
python manage.py test --settings=core.settings_test -v 2  # Django-runner tests
# Single test:
pytest cms/tests/test_category_admin_only.py --ds=core.settings_test
python manage.py test cms.tests.test_category_admin_only --settings=core.settings_test -v 2

# Celery (dev)
celery -A core worker -l info
celery -A core beat -l info

# Code quality (dev deps)
black .
isort .
flake8

# Docker: db + web + admin frontend + cms frontend
docker-compose up -d
docker-compose exec web python manage.py migrate
```

There is **no** `pytest.ini`/`pyproject.toml` pytest config — the Django settings module must be passed explicitly (`--ds=core.settings_test` for pytest, `--settings=core.settings_test` for `manage.py test`). Tests mix both runners; new pytest tests use `@pytest.mark.django_db` and DRF `APIClient` with an `X-Tenant-ID` header to simulate tenants.

Settings modules: `core.settings` (dev, default), `core.settings_docker` (containers), `core.settings_test` (tests).

## Architecture — read before changing code

### Multi-tenant isolation (central concept)
Tenant-scoped models inherit `common.models.BaseModel`, which adds `tenant` FK, `created_at`/`updated_at`, `is_deleted`, and two managers:
- `objects` = `TenantManager` — filters to the current thread-local tenant and excludes soft-deleted rows.
- `original_objects` = plain `Manager` — unfiltered, for cross-tenant/admin access.

Never call `.delete()`; call `instance.soft_delete()`. Models needing both translation and tenant filtering use `common.managers.TranslatableTenantManager` (fuses parler's `TranslatableManager` with tenant filtering) — e.g. `Category`.

The "current tenant" is thread-local, set by middleware and read via `common.utils.tenant_context.get_current_tenant()` / `set_current_tenant()`.

### Tenant resolution flow
1. `common.middleware.tenant_middleware.TenantMiddleware` resolves the tenant per request.
2. Paths requiring isolation are listed in `TENANT_ISOLATED_API_PATHS`; public exceptions in `TENANT_PUBLIC_API_PATHS` (both in `core/settings.py`).
3. `common.viewsets.TenantModelViewSet` enforces per-role tenant rules in `get_queryset`/`perform_create`/`perform_update`/`perform_destroy`. The role logic is gated by the `FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER` flag:
   - **Super admin** (JWT + `is_super_admin`): must pass `?tenant_id=` (writes require it; reads without it see all).
   - **Tenant admin** (`is_admin`): uses `?tenant_id=` or falls back to their own tenant. Admins/super-admins passing `X-Tenant-ID` are **rejected**.
   - **Member/anonymous**: must send `X-Tenant-ID` header, validated against their membership.

   When extending tenant-scoped viewsets, subclass `TenantModelViewSet` rather than DRF's `ModelViewSet` so this logic applies.

### Auth
Custom (not `djangorestframework-simplejwt`). Auth classes in `common.authentication/`: `APIJWTAuthentication` (API), `WebSessionAuthentication` (web). Custom user model `users.User` (`AUTH_USER_MODEL`). JWT tuning in the `JWT_AUTH` setting (HS256). Members are a separate concept (`users.Member`) from admin `User`s.

### Standard response envelope
`common.renderers.StandardJSONRenderer` wraps every API response as `{success, code, message, data}` with a business `code` (2000 success, 4001/4003/4004/4000/5000). It deliberately skips OpenAPI schema endpoints and already-wrapped payloads. Errors go through `common.exceptions.custom_exception_handler`; pagination through `common.pagination.StandardResultsSetPagination` (PAGE_SIZE 10). When returning data, don't hand-build this envelope — return plain serializer data and let the renderer wrap it.

### URLs & docs
All APIs under `/api/v1/<app>/` (see `core/urls.py`). Swagger UI `/api/v1/docs/`, ReDoc `/api/v1/redoc/`, schema `/api/v1/schema/` via drf-spectacular. `schema.yml` / `swagger.json` are generated artifacts — do not hand-edit.

### i18n
Default language `zh-hans`, `TIME_ZONE='UTC'`, `USE_TZ=True`. Model-field translations via django-parler (`PARLER_LANGUAGES`, fallback `zh-hans`). Codebase comments/messages are largely Chinese — match the surrounding language when editing.

## Gotchas
- In `core/settings.py`, `DEBUG` is read from the **`INFO`** env var, not `DEBUG` (historical). The `FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER` flag genuinely changes tenant-access behavior — check it when debugging permission issues.
- `CELERY_ENABLED=false` forces synchronous task execution (`CELERY_TASK_ALWAYS_EAGER`) for environments without a worker (e.g. cPanel).
- `media/` contains ~20k images — never stage it. `logs/` rotates daily (15-day retention); when `LOG_TO_CONSOLE=true` logs go to console only.
- Dev config has `ALLOWED_HOSTS=['*']` and `CORS_ALLOW_ALL_ORIGINS=True` — tighten for production.
