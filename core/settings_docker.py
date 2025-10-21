"""
Docker-specific settings for the core project.
"""

from .settings import *

# 静态文件设置
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 添加白噪声中间件用于静态文件服务
MIDDLEWARE = ['whitenoise.middleware.WhiteNoiseMiddleware'] + MIDDLEWARE

# 启用白噪声的静态文件服务和压缩
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 确保所有静态文件都能被找到
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# 调试设置
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# 允许所有主机访问
ALLOWED_HOSTS = ['*']

# 数据库设置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'multi_tenant_db_dev'),
        'USER': os.environ.get('DB_USER', 'django'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'django_password'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
            'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'",
            'autocommit': True,
        },
    }
}

# Docker环境CORS配置 - 覆盖settings.py中的配置
CORS_ALLOW_ALL_ORIGINS = False  # 使用白名单模式
CORS_ALLOWED_ORIGINS = [
    # 本地开发环境
    "http://localhost",
    "http://localhost:80",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:8848",
    "http://127.0.0.1",
    "http://127.0.0.1:80",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8848",
    # 生产环境
    "http://espressox.online",
    "https://espressox.online",
    "http://backend.espressox.online",
    "https://backend.espressox.online",
    "http://admin.espressox.online",
    "https://admin.espressox.online",

    'http://43.142.76.105',
    'http://43.142.76.105:80',
    'http://43.142.76.105:8000',
    'http://43.142.76.105:8848',
]

# CSRF可信源 - Docker环境
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://localhost:80',
    'http://localhost:8000',
    'http://localhost:8848',
    'http://127.0.0.1',
    'http://127.0.0.1:80',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:8848',
    'http://espressox.online',
    'https://espressox.online',
    'http://backend.espressox.online',
    'https://backend.espressox.online',
    'http://admin.espressox.online',
    'https://admin.espressox.online',
    'http://43.142.76.105',
    'http://43.142.76.105:80',
    'http://43.142.76.105:8000',
    'http://43.142.76.105:8848',
]