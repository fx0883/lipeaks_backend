import os
import sys

# 修复 cPanel 环境的 Unicode 编码问题
# 必须在导入其他模块之前设置，否则 load_dotenv() 会因环境变量中的非 ASCII 字符报错
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['PYTHONIOENCODING'] = 'utf-8'

import pymysql

# 限制 OpenBLAS 线程数，避免在 cPanel 共享主机环境中耗尽资源
# 必须在导入 numpy/pandas 之前设置
# 
# 线程数建议：
# - 1: 最安全，资源占用最小（推荐用于共享主机）
# - 2-4: 平衡性能和资源占用（如果主机资源较充足可尝试）
# - 不设置: 默认32线程，在共享主机会导致资源耗尽
#
# cPanel 共享主机进程限制通常为 1400-1500，建议从2开始测试，如仍报错则改为1
os.environ['OPENBLAS_NUM_THREADS'] = '2'
os.environ['MKL_NUM_THREADS'] = '2'
os.environ['NUMEXPR_NUM_THREADS'] = '2'
os.environ['OMP_NUM_THREADS'] = '2'

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