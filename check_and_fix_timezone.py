#!/usr/bin/env python
"""
检查MySQL时区设置并提供简单的修复方案
"""
import os
import sys
import django
import pymysql
import datetime

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

def check_mysql_timezone():
    """检查MySQL时区设置"""
    try:
        # 连接到MySQL数据库
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        
        print("成功连接到MySQL数据库")
        
        # 获取游标
        with conn.cursor() as cursor:
            # 检查时区设置
            cursor.execute("SELECT @@global.time_zone, @@session.time_zone;")
            result = cursor.fetchone()
            print(f"当前时区设置: 全局时区={result[0]}, 会话时区={result[1]}")
            
            # 检查当前时间
            cursor.execute("SELECT NOW();")
            now = cursor.fetchone()[0]
            print(f"当前MySQL服务器时间: {now}")
            print(f"当前Python时间: {datetime.datetime.now()}")
            
            # 检查时区表是否已安装
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE 'time_zone%' AND table_schema = 'mysql';")
            count = cursor.fetchone()[0]
            print(f"MySQL时区表数量: {count}")
            if count == 0:
                print("MySQL时区表未安装，这可能是问题的原因")
            
            # 尝试使用系统时区而非命名时区
            try:
                cursor.execute("SET GLOBAL time_zone = '+08:00';")  # 北京时间
                print("已设置全局时区为+08:00（北京时间）")
                
                cursor.execute("SET time_zone = '+08:00';")
                print("已设置会话时区为+08:00（北京时间）")
                
                # 再次检查时区设置
                cursor.execute("SELECT @@global.time_zone, @@session.time_zone;")
                result = cursor.fetchone()
                print(f"更新后的时区设置: 全局时区={result[0]}, 会话时区={result[1]}")
                
                # 测试查询
                cursor.execute("SELECT CURDATE(), CURTIME(), NOW();")
                date, time, now = cursor.fetchone()
                print(f"当前日期: {date}, 当前时间: {time}, 当前日期时间: {now}")
            except Exception as e:
                print(f"设置数字时区偏移失败: {str(e)}")
        
        # 关闭连接
        conn.close()
        print("数据库连接已关闭")
        
    except Exception as e:
        print(f"检查MySQL时区失败: {str(e)}")

def fix_django_timezone():
    """提供修复Django时区问题的建议"""
    print("\n解决Django时区问题的可能方法:")
    print("方法1: 安装MySQL时区表（推荐）")
    print("  - 在Linux/Unix: 执行 mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root mysql")
    print("  - 在Windows: 可能需要从MySQL安装目录导入时区SQL文件")
    print("  - 在my.cnf或my.ini中添加 default-time-zone='UTC'")
    
    print("\n方法2: 修改Django时区设置")
    print("  - 在settings.py中设置 USE_TZ = False")
    print("  - 确保MySQL的时区与系统本地时区一致")
    
    print("\n方法3: 使用时区偏移量而非命名时区")
    print("  - 在MySQL中使用 SET GLOBAL time_zone = '+08:00'; 而不是 'Asia/Shanghai'")
    print("  - 在settings.py中可以继续使用 TIME_ZONE = 'Asia/Shanghai'")
    
    print("\n方法4: 针对admin的date_hierarchy临时修复")
    print("  - 在CustomerAdmin类中移除 date_hierarchy = 'created_at'")
    
    print("\n根据您的环境和需求，选择最适合的方法。")
    print("如果希望保持Django最佳实践（USE_TZ = True），推荐方法1。")

if __name__ == "__main__":
    print(f"Django TIME_ZONE: {settings.TIME_ZONE}")
    print(f"Django USE_TZ: {settings.USE_TZ}")
    
    print("\n检查MySQL时区设置...")
    check_mysql_timezone()
    
    fix_django_timezone() 