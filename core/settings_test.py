import os
import sys
from .settings import *  # noqa: F401,F403


class DisableMigrations(dict):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# 仅在执行测试（且非生成或执行迁移命令）时启用 DisableMigrations 以加速测试建表
# 保证在开发与 CI 环境中执行 makemigrations / migrate --settings=core.settings_test 时能正常生成和应用迁移
_is_test_run = 'test' in sys.argv or any('pytest' in arg for arg in sys.argv) or any('unittest' in arg for arg in sys.argv)
_is_migration_run = any(
    cmd in sys.argv for cmd in ('makemigrations', 'migrate', 'showmigrations', 'squashmigrations')
)
_force_migrations = os.getenv("ENABLE_MIGRATIONS", "").lower() in ("true", "1")
_force_disable = os.getenv("DISABLE_MIGRATIONS", "").lower() in ("true", "1")

if _force_disable:
    MIGRATION_MODULES = DisableMigrations()
elif not _force_migrations and _is_test_run and not _is_migration_run:
    MIGRATION_MODULES = DisableMigrations()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}

CELERY_ENABLED = True
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
WE_RSS_SYNC_INLINE = True

MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE
    if "api_logging" not in middleware.lower()
    and "browser_console_logging" not in middleware.lower()
    and "api_cache" not in middleware.lower()
] + [
    'common.middleware.response_standardization_middleware.ResponseStandardizationMiddleware',
]

# 严格隔离测试环境缓存：使用独立 LocMemCache，杜绝测试产生远程网络依赖
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'lipeaks-test-locmem',
        'TIMEOUT': 300,
        'KEY_PREFIX': 'lipeaks_test',
    }
}

# 确保在测试执行时，若调用 API 日志中间件采用同步执行以保证断言确定性
API_LOG_SYNC = True

# 单元测试环境下默认禁用全局 API 响应缓存，保证直接测试 Views/ORM 性能断言与逻辑确定性
API_CACHE_ENABLED = False

