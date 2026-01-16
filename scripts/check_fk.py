#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT CONSTRAINT_NAME 
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
        WHERE TABLE_SCHEMA = 'multi_tenant_db_dev'
        AND TABLE_NAME = 'cms_article' 
        AND COLUMN_NAME = 'author_id'
        AND REFERENCED_TABLE_NAME IS NOT NULL
    """)
    results = cursor.fetchall()
    
    if results:
        for row in results:
            print(f"外键名称: {row[0]}")
    else:
        print("未找到author_id的外键约束（可能已被删除或不存在）")
        
    # 检查author_id列是否存在
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'multi_tenant_db_dev'
        AND TABLE_NAME = 'cms_article' 
        AND COLUMN_NAME = 'author_id'
    """)
    if cursor.fetchone():
        print("author_id列仍然存在")
    else:
        print("author_id列已不存在")
