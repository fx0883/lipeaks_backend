#!/usr/bin/env python
"""
检查分类数据
"""
import os
import sys
import django
from pathlib import Path

# 设置Django环境
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from cms.models import Category
from django.db import connection

def check_categories():
    """检查分类数据"""
    print("=" * 60)
    print("租户3的分类数据检查")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT c.id, c.slug, c.cover_image, ct.name 
            FROM cms_category c 
            LEFT JOIN cms_category_translation ct ON c.id = ct.master_id 
            WHERE c.tenant_id = 3 AND ct.language_code = %s 
            ORDER BY c.id
            LIMIT 10
        ''', ['zh-hans'])
        
        rows = cursor.fetchall()
        
        print(f"\n找到 {len(rows)} 个分类（显示前10个）:\n")
        for r in rows:
            cat_id, slug, cover_image, name = r
            print(f"ID: {cat_id:3d} | 名称: {name:15s} | 封面: {cover_image or '无'}")
    
    # 检查media文件夹
    media_dir = Path('d:/GitHub/lipeaks_backend/media/category_image')
    if media_dir.exists():
        print(f"\n{media_dir} 文件夹现有图片:")
        images = sorted(media_dir.glob('*.png'))
        for img in images[:10]:
            print(f"  - {img.name} ({img.stat().st_size / 1024:.1f} KB)")
        print(f"\n总共: {len(images)} 个PNG图片")
    else:
        print(f"\n{media_dir} 文件夹不存在")

if __name__ == "__main__":
    check_categories()
