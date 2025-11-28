import os
import sys
import traceback
from datetime import datetime

# 修复 cPanel 环境的 Unicode 编码问题
# 必须在导入其他模块之前设置，否则 load_dotenv() 会因环境变量中的非 ASCII 字符报错
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 获取当前脚本目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 确保日志目录存在
LOGS_DIR = os.path.join(CURRENT_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)


def log_startup_error(error_msg):
    """将启动错误写入日志文件（在 Django 日志系统初始化之前使用）"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(LOGS_DIR, f'startup_error.{date_str}.log')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{timestamp}] STARTUP ERROR\n")
        f.write(f"{'='*60}\n")
        f.write(error_msg)
        f.write('\n')


try:
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

except Exception as e:
    # 捕获所有启动错误并写入日志
    error_detail = f"Exception: {type(e).__name__}: {e}\n\nTraceback:\n{traceback.format_exc()}"
    log_startup_error(error_detail)
    # 重新抛出异常，让 Passenger 知道启动失败
    raise