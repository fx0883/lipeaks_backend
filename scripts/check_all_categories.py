#!/usr/bin/env python
"""
检查所有分类名称
"""
import os
import sys
import django
from pathlib import Path

# 设置Django环境
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def check_all_categories():
    """检查所有分类"""
    print("=" * 60)
    print("租户3的所有分类")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT c.id, ct.name, c.cover_image
            FROM cms_category c 
            LEFT JOIN cms_category_translation ct ON c.id = ct.master_id 
            WHERE c.tenant_id = 3 AND ct.language_code = %s AND c.is_deleted = FALSE
            ORDER BY c.id
        ''', ['zh-hans'])
        
        rows = cursor.fetchall()
        
        print(f"\n找到 {len(rows)} 个分类:\n")
        for r in rows:
            cat_id, name, cover = r
            print(f"ID {cat_id:2d}: {name:15s} | 封面: {cover or '无'}")

if __name__ == "__main__":
    check_all_categories()
