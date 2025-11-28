"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# ============================================================================
# 修复 cPanel 环境的 Unicode 编码问题
# 必须在导入任何其他模块之前执行
# ============================================================================

# 强制设置 UTF-8 编码环境
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['LC_CTYPE'] = 'en_US.UTF-8'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# 修复 Python 在 cPanel 环境下的编码问题
# 问题：cPanel 的 Passenger 以 C/POSIX locale 启动 Python，导致 os.environ 使用 ASCII 编码
# 当环境变量中存在非 ASCII 字符（如中文）时，访问 os.environ 会崩溃
def _fix_cpanel_encoding():
    """
    通过修改 os.environ 的编码方式来修复 cPanel 环境的编码问题。
    必须在访问任何可能包含非ASCII字符的环境变量之前调用。
    """
    import sys
    
    # 方法1：尝试重新初始化 os 模块的编码
    if hasattr(sys, 'getfilesystemencoding'):
        # 设置文件系统编码提示
        if hasattr(sys, '_enablelegacywindowsfsencoding'):
            pass  # Windows 专用，跳过
    
    # 方法2：直接操作底层 environ 数据
    # 使用 os.environb（bytes 版本）来避免编码问题
    try:
        import os as _os
        # 获取我们需要的环境变量的原始 bytes
        needed_vars = {}
        for key_bytes, val_bytes in _os.environb.items():
            try:
                key = key_bytes.decode('utf-8', errors='replace')
                val = val_bytes.decode('utf-8', errors='replace')
                needed_vars[key] = val
            except:
                continue
        
        # 清空当前环境并重新设置（使用已解码的值）
        # 注意：只清理和重建我们能安全处理的变量
        _os.environ.clear()
        for k, v in needed_vars.items():
            try:
                _os.environ[k] = v
            except:
                pass
                
    except Exception as e:
        # 如果方法2失败，记录错误但继续
        pass

_fix_cpanel_encoding()

import pymysql

# 必须在导入 Django 之前设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 设置pymysql的连接超时和尝试次数
pymysql.connect_timeout = 30
pymysql.reconnect_attempt = 3

# 使用pymysql代替mysqlclient
pymysql.install_as_MySQLdb()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
