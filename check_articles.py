#!/usr/bin/env python
"""
检查文章数据
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

def check_articles():
    """检查租户1的文章"""
    print("=" * 60)
    print("租户1的文章列表")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT id, title, cover_image, status, published_at
            FROM cms_article
            WHERE tenant_id = 1 AND is_deleted = FALSE
            ORDER BY id
            LIMIT 20
        ''')
        
        rows = cursor.fetchall()
        
        print(f"\n找到 {len(rows)} 个文章（显示前20个）:\n")
        for r in rows:
            art_id, title, cover, status, pub_date = r
            cover_short = (cover[:50] + '...') if cover and len(cover) > 50 else (cover or '无')
            print(f"ID {art_id:3d}: {title[:30]:30s} | 状态: {status:10s} | 封面: {cover_short}")
        
        # 统计总数
        cursor.execute('''
            SELECT COUNT(*) FROM cms_article WHERE tenant_id = 1 AND is_deleted = FALSE
        ''')
        total = cursor.fetchone()[0]
        print(f"\n总计: {total} 篇文章")
        
        # 统计有/无封面的数量
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN cover_image IS NOT NULL AND cover_image != '' THEN 1 END) as has_cover,
                COUNT(CASE WHEN cover_image IS NULL OR cover_image = '' THEN 1 END) as no_cover
            FROM cms_article WHERE tenant_id = 1 AND is_deleted = FALSE
        ''')
        has_cover, no_cover = cursor.fetchone()
        print(f"有封面: {has_cover} 篇")
        print(f"无封面: {no_cover} 篇")

if __name__ == "__main__":
    check_articles()
