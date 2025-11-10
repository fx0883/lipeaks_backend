#!/usr/bin/env python3
"""
直接在数据库中标记迁移为已应用
绕过Django的迁移系统
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def mark_migration_applied():
    """在数据库中插入迁移记录"""
    
    with connection.cursor() as cursor:
        try:
            # 检查迁移是否已经标记
            cursor.execute("""
                SELECT COUNT(*) FROM django_migrations 
                WHERE app = 'cms' AND name = '0007_remove_article_author_article_author_content_type_and_more'
            """)
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("✓ 迁移已经标记为已应用")
                return
            
            # 插入迁移记录
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('cms', '0007_remove_article_author_article_author_content_type_and_more', NOW())
            """)
            
            print("=" * 60)
            print("✅ 迁移已成功标记为已应用！")
            print("=" * 60)
            print("\n现在可以重启Django服务测试新功能了")
            
        except Exception as e:
            print(f"❌ 标记迁移失败: {str(e)}")
            raise

if __name__ == '__main__':
    mark_migration_applied()
