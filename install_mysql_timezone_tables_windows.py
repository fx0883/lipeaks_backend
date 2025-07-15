#!/usr/bin/env python
"""
为Windows环境安装MySQL时区表
此脚本将下载MySQL官方时区SQL文件并导入到MySQL数据库
"""
import os
import sys
import django
import pymysql
import tempfile
import urllib.request
import subprocess

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 初始化Django
django.setup()

# 导入Django设置
from django.conf import settings

# 获取MySQL连接信息
DB_NAME = settings.DATABASES['default']['NAME']
DB_USER = settings.DATABASES['default']['USER']
DB_PASSWORD = settings.DATABASES['default']['PASSWORD']
DB_HOST = settings.DATABASES['default']['HOST']
DB_PORT = int(settings.DATABASES['default']['PORT'])

# MySQL时区SQL文件URL
TIMEZONE_SQL_URL = "https://raw.githubusercontent.com/mysql/mysql-server/8.0/mysql-test/std_data/timezone_posix.sql"

def download_timezone_sql():
    """下载MySQL时区SQL文件"""
    print("下载MySQL时区SQL文件...")
    temp_file = os.path.join(tempfile.gettempdir(), "timezone_posix.sql")
    
    try:
        urllib.request.urlretrieve(TIMEZONE_SQL_URL, temp_file)
        print(f"成功下载时区SQL文件到: {temp_file}")
        return temp_file
    except Exception as e:
        print(f"下载时区SQL文件失败: {str(e)}")
        return None

def import_timezone_sql(sql_file):
    """导入时区SQL文件到MySQL"""
    print("\n导入时区SQL文件到MySQL...")
    
    try:
        # 构建mysql命令
        mysql_cmd = f"mysql -u{DB_USER} -p{DB_PASSWORD} -h{DB_HOST} -P{DB_PORT} mysql < {sql_file}"
        
        # 提示用户手动执行命令
        print("请在命令行中执行以下命令导入时区表:")
        print(f"mysql -u{DB_USER} -p -h{DB_HOST} -P{DB_PORT} mysql < {sql_file}")
        
        # 尝试自动执行
        try:
            print("\n尝试自动导入时区表...")
            result = subprocess.run(
                mysql_cmd, 
                shell=True, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            print("时区表导入成功!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"自动导入失败: {e}")
            print(f"错误输出: {e.stderr}")
            print("\n请手动执行上述命令导入时区表。")
            return False
            
    except Exception as e:
        print(f"导入时区SQL文件失败: {str(e)}")
        return False

def check_timezone_tables():
    """检查时区表是否已安装"""
    print("\n检查时区表是否已安装...")
    
    try:
        # 连接到MySQL数据库
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database="mysql"  # 连接到mysql系统数据库
        )
        
        # 获取游标
        with conn.cursor() as cursor:
            # 检查时区表
            cursor.execute("SHOW TABLES LIKE 'time_zone%';")
            tables = cursor.fetchall()
            
            if tables:
                print(f"找到以下时区表:")
                for table in tables:
                    print(f"- {table[0]}")
                
                # 检查时区名称表中的数据
                cursor.execute("SELECT COUNT(*) FROM time_zone_name;")
                count = cursor.fetchone()[0]
                print(f"time_zone_name表中有{count}条记录")
                
                if count > 0:
                    print("时区表已正确安装")
                    return True
                else:
                    print("时区表存在但可能为空，需要导入数据")
                    return False
            else:
                print("未找到时区表，需要安装")
                return False
        
    except Exception as e:
        print(f"检查时区表失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("======================================")
    print("MySQL时区表安装工具 (Windows版)")
    print("======================================")
    
    # 检查是否为Windows
    if sys.platform != 'win32':
        print("此脚本专为Windows环境设计。在Linux/Unix系统上，请使用mysql_tzinfo_to_sql命令。")
        sys.exit(1)
    
    # 检查时区表是否已安装
    if check_timezone_tables():
        print("\n✅ MySQL时区表已安装，无需进一步操作。")
        sys.exit(0)
    
    # 下载时区SQL文件
    sql_file = download_timezone_sql()
    if not sql_file:
        print("\n❌ 无法下载时区SQL文件，安装失败。")
        sys.exit(1)
    
    # 导入时区SQL文件
    if import_timezone_sql(sql_file):
        print("\n✅ MySQL时区表安装完成!")
    else:
        print("\n⚠️ MySQL时区表安装可能未完成，请手动检查。")
    
    # 再次检查时区表
    if check_timezone_tables():
        print("\n✅ 确认MySQL时区表已成功安装。")
    else:
        print("\n⚠️ MySQL时区表可能未正确安装，请手动检查。")

if __name__ == "__main__":
    main() 