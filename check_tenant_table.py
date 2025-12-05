#!/usr/bin/env python
"""
检查租户表名
"""
import os
import sys
import django
from pathlib import Path

# 设置Django环境
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenants.models import Tenant

print("租户表名:", Tenant._meta.db_table)

# 查询一下数据
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(f"SELECT id, name FROM {Tenant._meta.db_table} WHERE id = 1")
    row = cursor.fetchone()
    if row:
        print(f"租户 ID {row[0]}: {row[1]}")
