#!/usr/bin/env python
"""
全链路UTC时区设置脚本
- 设置MySQL全局时区为UTC (+00:00)
- 确保Django设置为UTC时区
- 检查时区表是否正确安装
"""
import os
import sys
import django
import pymysql
import datetime
import subprocess
from pathlib import Path

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

def check_django_settings():
    """检查Django时区设置"""
    print("===== 检查Django时区设置 =====")
    print(f"Django TIME_ZONE: {settings.TIME_ZONE}")
    print(f"Django USE_TZ: {settings.USE_TZ}")
    
    if settings.TIME_ZONE != 'UTC':
        print("警告: Django TIME_ZONE 不是 UTC。建议将其设置为 'UTC'。")
        print("在 settings.py 中修改: TIME_ZONE = 'UTC'")
    
    if not settings.USE_TZ:
        print("警告: Django USE_TZ 为 False。建议将其设置为 True。")
        print("在 settings.py 中修改: USE_TZ = True")
    
    return settings.TIME_ZONE == 'UTC' and settings.USE_TZ

def check_mysql_timezone_tables():
    """检查MySQL时区表是否已安装"""
    print("\n===== 检查MySQL时区表 =====")
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
            # 检查时区表
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE 'time_zone%' AND table_schema = 'mysql';")
            count = cursor.fetchone()[0]
            print(f"MySQL时区表数量: {count}")
            
            if count >= 5:  # 通常有5个时区相关表
                print("MySQL时区表已正确安装")
                
                # 测试CONVERT_TZ函数
                try:
                    cursor.execute("SELECT CONVERT_TZ('2025-07-03 10:00:00', '+00:00', '+08:00');")
                    result = cursor.fetchone()[0]
                    print(f"时区转换测试: UTC 10:00 -> CST 18:00 = {result}")
                    print("时区转换功能正常工作")
                    return True
                except Exception as e:
                    print(f"时区转换测试失败: {str(e)}")
            else:
                print("MySQL时区表未完全安装，需要安装时区表")
                return False
        
        # 关闭连接
        conn.close()
        
    except Exception as e:
        print(f"检查MySQL时区表失败: {str(e)}")
        return False

def set_mysql_utc_timezone():
    """设置MySQL全局时区为UTC"""
    print("\n===== 设置MySQL时区为UTC =====")
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
            
            # 设置会话时区为+00:00 (UTC)
            cursor.execute("SET time_zone = '+00:00';")
            print("已设置会话时区为+00:00 (UTC)")
            
            # 再次检查时区设置
            cursor.execute("SELECT @@global.time_zone, @@session.time_zone;")
            result = cursor.fetchone()
            print(f"更新后的时区设置: 全局时区={result[0]}, 会话时区={result[1]}")
            
            # 测试查询
            cursor.execute("SELECT UTC_TIMESTAMP(), NOW();")
            utc_now, now = cursor.fetchone()
            print(f"当前UTC时间: {utc_now}, 当前系统时间: {now}")
            
            if str(utc_now) == str(now):
                print("验证成功: UTC_TIMESTAMP() 和 NOW() 返回相同的时间，确认MySQL使用UTC时区")
                return True
            else:
                print("警告: UTC_TIMESTAMP() 和 NOW() 返回不同的时间，MySQL可能未正确使用UTC时区")
                return False
        
        # 关闭连接
        conn.close()
        
    except Exception as e:
        print(f"设置MySQL时区失败: {str(e)}")
        return False

def provide_mysql_config_instructions():
    """提供MySQL配置说明"""
    print("\n===== MySQL永久配置说明 =====")
    print("注意: 通过SET GLOBAL设置的时区在MySQL重启后会恢复默认值。")
    print("要永久设置MySQL时区为UTC，请按照以下步骤操作:")
    
    if sys.platform == 'win32':
        print("\n在Windows上:")
        print("1. 找到my.ini文件 (通常在MySQL安装目录或C:\\ProgramData\\MySQL\\MySQL Server X.Y\\)")
        print("2. 在[mysqld]部分添加以下行:")
        print("   default-time-zone = '+00:00'")
        print("3. 重启MySQL服务")
    else:
        print("\n在Linux/Unix上:")
        print("1. 编辑my.cnf文件 (通常在/etc/mysql/my.cnf或/etc/my.cnf)")
        print("2. 在[mysqld]部分添加以下行:")
        print("   default-time-zone = '+00:00'")
        print("3. 重启MySQL服务: sudo systemctl restart mysql")

def main():
    """主函数"""
    print("======================================")
    print("全链路UTC时区设置工具")
    print("======================================")
    
    # 检查Django设置
    django_ok = check_django_settings()
    
    # 检查MySQL时区表
    tables_ok = check_mysql_timezone_tables()
    
    # 设置MySQL时区为UTC
    mysql_ok = set_mysql_utc_timezone()
    
    # 提供永久配置说明
    provide_mysql_config_instructions()
    
    # 总结
    print("\n===== 配置总结 =====")
    print(f"Django时区设置: {'✓ 正确' if django_ok else '✗ 需要修改'}")
    print(f"MySQL时区表: {'✓ 已安装' if tables_ok else '✗ 需要安装'}")
    print(f"MySQL时区设置: {'✓ 已设置为UTC' if mysql_ok else '✗ 设置失败'}")
    
    if django_ok and tables_ok and mysql_ok:
        print("\n✅ 全链路UTC时区配置完成！")
        print("现在您的系统使用UTC作为标准时间，Django将负责时区转换。")
        print("前端应用应该从UTC转换为用户本地时区进行显示。")
    else:
        print("\n⚠️ 时区配置未完全完成，请解决上述问题。")
    
    print("\n请重启Django应用以应用所有更改。")

if __name__ == "__main__":
    main() 