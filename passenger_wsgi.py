import os
import sys
import pymysql

# 获取当前脚本目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加项目目录到路径
sys.path.insert(0, CURRENT_DIR)

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 设置pymysql选项
pymysql.connect_timeout = 30
pymysql.install_as_MySQLdb()

# 应用程序对象
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()