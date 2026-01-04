# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

LiPeaks Backend is a multi-tenant SaaS platform backend built with Django 5.2 and Django REST Framework. It provides tenant-isolated business modules including user management, CMS, customer management, orders, licenses, and more.

**Language preference:** Use Chinese (中文) for all responses and communication.

## Development Commands

```bash
# Virtual environment setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Database migrations
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
python manage.py test
python manage.py test tests.test_tenant_isolation  # Run specific test

# Code formatting
black .
isort .

# Docker deployment
docker-compose up -d
docker-compose exec web python manage.py migrate
```

## Architecture

### Multi-Tenant Architecture

The system uses a shared-database, shared-schema multi-tenant approach with automatic tenant isolation:

1. **BaseModel** (`common/models.py`): Base class for all tenant-isolated models
   - Provides `tenant` ForeignKey, `created_at`, `updated_at`, `is_deleted`
   - Uses `TenantManager` as default manager for automatic tenant filtering
   - Use `original_objects` manager to bypass tenant filtering (for admin operations)

2. **TenantManager** (`common/utils/tenant_manager.py`): 
   - Automatically filters querysets by current tenant context
   - Excludes soft-deleted records by default

3. **TenantModelViewSet** (`common/viewsets.py`): Base ViewSet for tenant-isolated APIs
   - Auto-filters querysets by tenant
   - Auto-sets tenant on create
   - Validates tenant ownership on update/delete
   - Paths requiring isolation defined in `settings.TENANT_ISOLATED_API_PATHS`

4. **Tenant Context**: 
   - Set via `set_current_tenant()`, get via `get_current_tenant()` from `common/utils/tenant_context.py`
   - Managed by `TenantMiddleware` using X-Tenant-ID header or user's tenant

### User Model Hierarchy

```
BaseUserModel (abstract)
├── User (管理员) - is_admin=True always
│   ├── is_super_admin=True → Super admin (no tenant)
│   └── is_super_admin=False → Tenant admin (has tenant)
└── Member (普通成员) - Regular users with optional parent for sub-accounts
```

### Authentication

- **APIJWTAuthentication**: JWT auth for `/api/` paths only
- **WebSessionAuthentication**: Session auth for admin panel
- Tokens include user_id, tenant_id (if applicable), and auth_type

### API Response Format

All responses follow standardized format (enforced by `ResponseStandardizationMiddleware`):
```json
{
  "success": true/false,
  "code": 2000,  // 2xxx=success, 4xxx=client error, 5xxx=server error
  "message": "操作描述",
  "data": { ... }
}
```

### Key Directories

- `core/` - Django settings, URLs, WSGI
- `common/` - Shared utilities, middleware, base classes, authentication
- `tenants/` - Tenant and quota management
- `users/` - User and Member models, authentication APIs
- `rbac/` - Role-based access control (Permission, Role, UserRole)
- `cms/` - Multi-language content management with django-parler
- Other modules: `customers/`, `orders/`, `licenses/`, `feedbacks/`, `applications/`, `menus/`, `charts/`, `points/`, `interactions/`

### Middleware Chain (order matters)

1. WhiteNoiseMiddleware - Static files
2. SecurityMiddleware
3. CorsMiddleware
4. SessionMiddleware
5. LocaleMiddleware
6. CommonMiddleware
7. CsrfViewMiddleware
8. AuthenticationMiddleware
9. MessageMiddleware
10. XFrameOptionsMiddleware
11. **APIAuthMiddleware** - Custom JWT processing
12. **TenantMiddleware** - Tenant context setup
13. **EnhancedAPILoggingMiddleware** - Request/response logging
14. **BrowserConsoleLoggingMiddleware**
15. **ResponseStandardizationMiddleware** - Format standardization

## Creating New Tenant-Isolated Models

```python
from common.models import BaseModel

class MyModel(BaseModel):
    name = models.CharField(max_length=100)
    # tenant, created_at, updated_at, is_deleted inherited
    
    class Meta:
        # Don't forget abstract = False (inherited from BaseModel)
        verbose_name = 'My Model'
```

## Creating New Tenant-Isolated ViewSets

```python
from common.viewsets import TenantModelViewSet

class MyModelViewSet(TenantModelViewSet):
    queryset = MyModel.objects.all()  # TenantManager auto-filters
    serializer_class = MyModelSerializer
    # perform_create, perform_update, perform_destroy auto-handle tenant
```

## Environment Variables

Key settings in `.env`:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - MySQL connection
- `CELERY_ENABLED` - Enable async tasks (default: true)
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` - Redis URLs
- `LOG_TO_CONSOLE` - Log to console instead of files

## RIPER-5 Development Protocol

This project follows the RIPER-5 workflow protocol (from `.cursorrules`):

1. **RESEARCH** - Information gathering, read files, understand structure. No suggestions.
2. **INNOVATE** - Brainstorm solutions, evaluate approaches. No implementation.
3. **PLAN** - Create detailed technical specs with file paths, function signatures. No code.
4. **EXECUTE** - Implement exactly as planned. Track progress in task files under `.tasks/`.
5. **REVIEW** - Verify implementation matches plan, check for deviations.

Mode transitions require explicit commands: "ENTER RESEARCH MODE", "ENTER PLAN MODE", etc.

**Key rules:**
- Declare mode at start of each response: `[MODE: RESEARCH]`
- Default mode is RESEARCH for new conversations
- Never implement without explicit approval
- Use Chinese for responses (except mode declarations)
- Create task files in `.tasks/` directory for tracking
