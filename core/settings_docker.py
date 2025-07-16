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