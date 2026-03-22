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

MIGRATION_MODULES = DisableMigrations()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE
    if "api_logging" not in middleware.lower()
    and "browser_console_logging" not in middleware.lower()
]
