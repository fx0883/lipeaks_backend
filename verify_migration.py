#!/usr/bin/env python3
"""验证迁移结果"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from cms.models import Article

print("=" * 60)
print("验证Article模型迁移结果")
print("=" * 60)

# 检查数据库schema
with connection.cursor() as cursor:
    # 检查新字段
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'multi_tenant_db_dev'
        AND TABLE_NAME = 'cms_article' 
        AND COLUMN_NAME IN ('author_content_type_id', 'author_object_id', 'author_id')
    """)
    columns = cursor.fetchall()
    
    print("\n📋 数据库字段状态:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]} (NULL={col[2]})")
    
    # 检查索引
    cursor.execute("""
        SELECT DISTINCT INDEX_NAME 
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = 'multi_tenant_db_dev'
        AND TABLE_NAME = 'cms_article'
        AND INDEX_NAME LIKE '%author%'
    """)
    indexes = cursor.fetchall()
    
    print("\n🔑 索引状态:")
    for idx in indexes:
        print(f"  - {idx[0]}")
    
    # 检查数据迁移
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN author_content_type_id IS NOT NULL THEN 1 ELSE 0 END) as migrated,
            SUM(CASE WHEN author_object_id IS NOT NULL THEN 1 ELSE 0 END) as has_author_id
        FROM cms_article
    """)
    stats = cursor.fetchone()
    
    print("\n📊 数据迁移统计:")
    print(f"  - 总文章数: {stats[0]}")
    print(f"  - 已迁移作者类型: {stats[1]}")
    print(f"  - 已迁移作者ID: {stats[2]}")

# 测试Django模型
print("\n🧪 测试Django模型:")
try:
    article = Article.objects.first()
    if article:
        print(f"  - 文章标题: {article.title}")
        print(f"  - 作者类型: {article.is_author_member and 'Member' or 'Admin'}")
        print(f"  - 作者: {article.author}")
        print("  ✅ Django模型工作正常")
    else:
        print("  ⚠ 没有文章数据")
except Exception as e:
    print(f"  ❌ 模型测试失败: {e}")

print("\n" + "=" * 60)
print("✅ 迁移验证完成！")
print("=" * 60)
