#!/usr/bin/env python
"""
为Django设置MySQL时区，遵循最佳实践
- 设置MySQL全局时区为UTC
- 让Django在应用程序层处理时区转换
"""
import os
import sys
import django
import pymysql

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

def set_mysql_utc_timezone():
    """设置MySQL全局时区为UTC"""
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
            # 检查当前时区设置
            cursor.execute("SELECT @@global.time_zone, @@session.time_zone;")
            result = cursor.fetchone()
            print(f"当前时区设置: 全局时区={result[0]}, 会话时区={result[1]}")
            
            # 设置全局时区为+00:00 (UTC)
            cursor.execute("SET GLOBAL time_zone = '+00:00';")
            print("已设置全局时区为+00:00 (UTC)")
            
            # 再次检查时区设置
            cursor.execute("SELECT @@global.time_zone, @@session.time_zone;")
            result = cursor.fetchone()
            print(f"更新后的时区设置: 全局时区={result[0]}, 会话时区={result[1]}")
            
            # 测试查询
            cursor.execute("SELECT UTC_TIMESTAMP(), NOW();")
            utc_now, now = cursor.fetchone()
            print(f"当前UTC时间: {utc_now}, 当前系统时间: {now}")
            
            print("\n时区设置完成。MySQL现在使用UTC时区，Django会在应用层处理时区转换。")
        
        # 关闭连接
        conn.close()
        print("数据库连接已关闭")
        
    except Exception as e:
        print(f"设置MySQL时区失败: {str(e)}")

def check_admin_date_hierarchy():
    """检查admin模型中的date_hierarchy设置"""
    try:
        from customers.admin import CustomerAdmin
        
        if hasattr(CustomerAdmin, 'date_hierarchy'):
            print(f"\nCustomerAdmin.date_hierarchy = '{CustomerAdmin.date_hierarchy}'")
            print("注意: 如果时区问题仍然存在，可以考虑移除这个设置")
    except ImportError:
        print("\n无法导入CustomerAdmin类进行检查")

if __name__ == "__main__":
    print(f"Django TIME_ZONE: {settings.TIME_ZONE}")
    print(f"Django USE_TZ: {settings.USE_TZ}")
    
    print("\n设置MySQL时区为UTC...")
    set_mysql_utc_timezone()
    
    check_admin_date_hierarchy()
    
    print("\n请重启Django服务器以应用更改。") 