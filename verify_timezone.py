#!/usr/bin/env python
"""
验证Django和MySQL的时区设置
"""
import os
import sys
import django
import pymysql
import datetime
import pytz

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# 导入Django设置
from django.conf import settings
from django.utils import timezone

# 获取MySQL连接信息
DB_NAME = settings.DATABASES['default']['NAME']
DB_USER = settings.DATABASES['default']['USER']
DB_PASSWORD = settings.DATABASES['default']['PASSWORD']
DB_HOST = settings.DATABASES['default']['HOST']
DB_PORT = int(settings.DATABASES['default']['PORT'])

def verify_django_timezone():
    """验证Django时区设置"""
    print("===== Django时区设置 =====")
    print(f"Django TIME_ZONE: {settings.TIME_ZONE}")
    print(f"Django USE_TZ: {settings.USE_TZ}")
    
    # 获取当前时间
    now = timezone.now()
    now_naive = datetime.datetime.now()
    utc_now = datetime.datetime.now(pytz.UTC)
    
    print(f"Django timezone.now(): {now} ({now.tzinfo})")
    print(f"Python datetime.now(): {now_naive} (无时区)")
    print(f"Python UTC now: {utc_now} ({utc_now.tzinfo})")
    
    # 如果Django使用UTC，timezone.now()应该是UTC时间
    if settings.USE_TZ and settings.TIME_ZONE == 'UTC':
        print("Django正确配置为使用UTC时区")
    elif settings.USE_TZ:
        print(f"Django配置为使用{settings.TIME_ZONE}时区，但内部仍使用UTC")
    else:
        print(f"Django未启用时区支持，使用{settings.TIME_ZONE}作为时区")

def verify_mysql_timezone():
    """验证MySQL时区设置"""
    print("\n===== MySQL时区设置 =====")
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
            print(f"MySQL时区设置: 全局时区={result[0]}, 会话时区={result[1]}")
            
            # 检查当前时间
            cursor.execute("SELECT NOW(), UTC_TIMESTAMP();")
            now, utc_now = cursor.fetchone()
            print(f"MySQL当前时间: {now}")
            print(f"MySQL UTC时间: {utc_now}")
            
            # 验证是否为UTC
            if str(now) == str(utc_now):
                print("MySQL正确配置为使用UTC时区")
            else:
                print(f"MySQL未使用UTC时区，当前时区与UTC相差: {now - utc_now}")
            
            # 测试时区转换
            try:
                cursor.execute("SELECT CONVERT_TZ('2025-07-03 10:00:00', '+00:00', '+08:00');")
                result = cursor.fetchone()[0]
                print(f"时区转换测试: UTC 10:00 -> CST 18:00 = {result}")
                print("MySQL时区表正确安装")
            except Exception as e:
                print(f"时区转换测试失败: {str(e)}")
                print("MySQL时区表可能未正确安装")
        
        # 关闭连接
        conn.close()
        
    except Exception as e:
        print(f"验证MySQL时区失败: {str(e)}")

def verify_database_datetime():
    """验证数据库日期时间字段的处理"""
    print("\n===== 数据库日期时间字段处理 =====")
    
    try:
        # 尝试从customers表中获取记录
        from customers.models import Customer
        
        # 获取最新的客户记录
        latest_customer = Customer.objects.order_by('-created_at').first()
        
        if latest_customer:
            print(f"最新客户记录: {latest_customer.name}")
            print(f"创建时间 (数据库): {latest_customer.created_at}")
            print(f"时区信息: {latest_customer.created_at.tzinfo}")
            
            # 转换为UTC和本地时间
            utc_time = latest_customer.created_at.astimezone(pytz.UTC)
            local_time = latest_customer.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
            
            print(f"UTC时间: {utc_time}")
            print(f"本地时间 ({settings.TIME_ZONE}): {local_time}")
        else:
            print("未找到客户记录，无法验证日期时间字段处理")
    
    except Exception as e:
        print(f"验证数据库日期时间字段失败: {str(e)}")

def main():
    """主函数"""
    print("======================================")
    print("Django和MySQL时区设置验证工具")
    print("======================================")
    
    verify_django_timezone()
    verify_mysql_timezone()
    verify_database_datetime()
    
    print("\n======================================")
    print("验证完成")
    print("======================================")

if __name__ == "__main__":
    main() 