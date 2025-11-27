"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# 修复 cPanel 环境的 Unicode 编码问题
# 必须在导入 Django 之前设置
os.environ.setdefault('LANG', 'en_US.UTF-8')
os.environ.setdefault('LC_ALL', 'en_US.UTF-8')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

import pymysql

from django.core.wsgi import get_wsgi_application

# 设置pymysql的连接超时和尝试次数
pymysql.connect_timeout = 30
pymysql.reconnect_attempt = 3

# 使用pymysql代替mysqlclient
pymysql.install_as_MySQLdb()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()
