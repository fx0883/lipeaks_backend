"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
import pymysql

from django.core.wsgi import get_wsgi_application

# 设置pymysql的连接超时和尝试次数
pymysql.connect_timeout = 30
pymysql.reconnect_attempt = 3

# 使用pymysql代替mysqlclient
pymysql.install_as_MySQLdb()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()
