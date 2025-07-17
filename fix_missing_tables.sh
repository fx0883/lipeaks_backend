#!/bin/bash

# 此脚本用于修复Docker环境中缺失的数据库表

echo "开始修复缺失的数据库表..."

# 确保使用正确的设置模块
export DJANGO_SETTINGS_MODULE=core.settings_docker

# 执行所有迁移
echo "执行所有应用的迁移..."
python manage.py migrate

# 单独执行各个应用的迁移
echo "执行用户相关迁移..."
python manage.py migrate users

echo "执行RBAC相关迁移..."
python manage.py migrate rbac

echo "执行菜单相关迁移..."
python manage.py migrate menus

echo "执行租户相关迁移..."
python manage.py migrate tenants

echo "执行公共模块迁移..."
python manage.py migrate common

echo "执行CMS相关迁移..."
python manage.py migrate cms

echo "执行客户相关迁移..."
python manage.py migrate customers

echo "执行订单相关迁移..."
python manage.py migrate orders

echo "执行检查系统相关迁移..."
python manage.py migrate check_system

echo "执行图表相关迁移..."
python manage.py migrate charts

echo "检查数据库表..."
python -c "
import os
import django
import pymysql
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_docker')
django.setup()
from django.conf import settings

# 连接数据库
conn = pymysql.connect(
    host=settings.DATABASES['default']['HOST'],
    user=settings.DATABASES['default']['USER'],
    password=settings.DATABASES['default']['PASSWORD'],
    db=settings.DATABASES['default']['NAME']
)

try:
    with conn.cursor() as cursor:
        # 获取所有表
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        print(f'数据库中共有 {len(tables)} 个表:')
        for table in tables:
            print(f'- {table[0]}')
        
        # 检查特定表是否存在
        critical_tables = [
            'django_migrations', 'django_session', 'auth_user', 
            'user', 'user_menu', 'menu', 'common_config'
        ]
        
        for table in critical_tables:
            cursor.execute(f\"\"\"
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{settings.DATABASES['default']['NAME']}' 
                AND table_name = '{table}'
            \"\"\")
            if cursor.fetchone()[0] == 0:
                print(f'警告: {table} 表不存在!')
            else:
                print(f'√ {table} 表存在')
finally:
    conn.close()
"

echo "修复完成!" 