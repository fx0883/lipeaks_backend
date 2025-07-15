#!/usr/bin/env python
"""
设置MySQL时区为UTC，解决Django时区转换问题
"""
import os
import sys
import django
import pymysql

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
DB_PORT = int(settings.DATABASES['default']['PORT'])

def set_mysql_timezone():
    """
    设置MySQL的全局时区为UTC和会话时区为系统时区
    这样可以确保数据库存储UTC时间，而应用程序处理本地时间转换
    """
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
            # 设置全局时区为UTC
            cursor.execute("SET GLOBAL time_zone = 'UTC';")
            print("已设置全局时区为UTC")
            
            # 设置会话时区为系统时区
            cursor.execute(f"SET time_zone = '{settings.TIME_ZONE}';")
            print(f"已设置会话时区为{settings.TIME_ZONE}")
            
            # 检查时区设置是否生效
            cursor.execute("SELECT @@global.time_zone, @@session.time_zone;")
            result = cursor.fetchone()
            print(f"确认设置: 全局时区={result[0]}, 会话时区={result[1]}")
            
            # 检查当前时间
            cursor.execute("SELECT NOW();")
            now = cursor.fetchone()[0]
            print(f"当前MySQL服务器时间: {now}")
            
            # 测试CONVERT_TZ函数是否正常工作
            try:
                cursor.execute("SELECT CONVERT_TZ('2025-07-03 10:00:00', 'UTC', 'Asia/Shanghai');")
                converted_time = cursor.fetchone()[0]
                print(f"时区转换测试: UTC 10:00 -> Asia/Shanghai = {converted_time}")
                print("时区转换功能正常")
            except Exception as e:
                print(f"时区转换测试失败: {str(e)}")
                print("您可能需要安装MySQL时区表")
        
        # 关闭连接
        conn.close()
        print("数据库连接已关闭")
        return True
        
    except Exception as e:
        print(f"设置MySQL时区失败: {str(e)}")
        return False

def main():
    """主函数"""
    print(f"Django TIME_ZONE: {settings.TIME_ZONE}")
    print(f"Django USE_TZ: {settings.USE_TZ}")
    
    print("\n设置MySQL时区...")
    set_mysql_timezone()
    
    print("\n处理完成。请重启Django应用以应用更改。")

if __name__ == "__main__":
    main() 