#!/usr/bin/env python
"""
为MySQL安装时区表，解决Django时区转换问题
"""
import os
import subprocess
import sys
import django
from pathlib import Path

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 初始化Django
try:
    django.setup()
except Exception as e:
    print(f"Django初始化错误: {str(e)}")
    sys.exit(1)

# 导入Django设置
from django.conf import settings

# 获取MySQL连接信息
DB_NAME = settings.DATABASES['default']['NAME']
DB_USER = settings.DATABASES['default']['USER']
DB_PASSWORD = settings.DATABASES['default']['PASSWORD']
DB_HOST = settings.DATABASES['default']['HOST']
DB_PORT = settings.DATABASES['default']['PORT']

# 检查zoneinfo路径
ZONEINFO_PATHS = [
    '/usr/share/zoneinfo',      # Linux
    '/usr/share/lib/zoneinfo',  # Solaris
    '/var/db/timezone/zoneinfo',  # FreeBSD
    'C:\\ProgramData\\MySQL\\MySQL Server 8.0\\data\\mysql\\time_zone_name.frm',  # Windows
    'C:\\Program Files\\MySQL\\MySQL Server 8.0\\share\\mysql\\timezone_posix.sql'  # Windows MySQL安装目录
]

def find_zoneinfo_path():
    """查找系统中可用的时区信息文件路径"""
    for path in ZONEINFO_PATHS:
        if os.path.exists(path):
            return path
    return None

def run_mysql_command(command):
    """运行MySQL命令"""
    full_cmd = f"mysql -u{DB_USER} -p{DB_PASSWORD} -h{DB_HOST} -P{DB_PORT} {DB_NAME} -e \"{command}\""
    print(f"执行命令: {full_cmd.replace(DB_PASSWORD, '********')}")
    
    try:
        result = subprocess.run(
            full_cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        print("命令执行成功!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def check_mysql_timezone_tables():
    """检查MySQL时区表是否已安装"""
    query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE 'time_zone%' AND table_schema = 'mysql';"
    result = run_mysql_command(query)
    return result

def install_mysql_timezone_tables():
    """安装MySQL时区表"""
    print("开始安装MySQL时区表...")
    
    # 查找zoneinfo路径
    zoneinfo_path = find_zoneinfo_path()
    if not zoneinfo_path:
        print("错误: 无法找到zoneinfo路径。请手动安装MySQL时区表。")
        return False
    
    # 对于Windows，我们需要使用MySQL提供的SQL文件
    if sys.platform == 'win32':
        # 检查是否为MySQL安装目录中的timezone_posix.sql
        if 'timezone_posix.sql' in zoneinfo_path:
            # 使用source命令导入时区SQL
            command = f"source {zoneinfo_path}"
            return run_mysql_command(command)
        else:
            print("警告: 在Windows上，我们可能无法自动安装时区表。")
            print("请手动运行以下命令安装MySQL时区表:")
            print(f"mysql_tzinfo_to_sql {zoneinfo_path} | mysql -u {DB_USER} -p mysql")
            return False
    
    # 对于类Unix系统，使用mysql_tzinfo_to_sql命令
    try:
        command = f"mysql_tzinfo_to_sql {zoneinfo_path} | mysql -u {DB_USER} -p mysql"
        print(f"请手动运行以下命令安装MySQL时区表:")
        print(command)
        return True
    except Exception as e:
        print(f"安装时区表失败: {str(e)}")
        return False

def set_mysql_timezone():
    """设置MySQL的时区"""
    timezone = settings.TIME_ZONE
    command = f"SET GLOBAL time_zone = '{timezone}'; SET time_zone = '{timezone}';"
    return run_mysql_command(command)

def main():
    """主函数"""
    print(f"Django TIME_ZONE: {settings.TIME_ZONE}")
    print(f"Django USE_TZ: {settings.USE_TZ}")
    
    # 检查并安装时区表
    print("\n检查MySQL时区表...")
    if check_mysql_timezone_tables():
        print("MySQL时区表已安装.")
    else:
        print("MySQL时区表未安装，尝试安装...")
        install_mysql_timezone_tables()
    
    # 设置MySQL时区
    print("\n设置MySQL时区...")
    set_mysql_timezone()
    
    print("\n处理完成。请重启Django应用以应用更改。")

if __name__ == "__main__":
    main() 