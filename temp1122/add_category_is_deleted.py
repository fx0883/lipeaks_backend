#!/usr/bin/env python3
"""
手动添加Category的is_deleted字段的脚本
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def add_category_is_deleted():
    """添加is_deleted字段到cms_category表"""
    with connection.cursor() as cursor:
        try:
            # 检查字段是否已存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'cms_category' 
                AND COLUMN_NAME = 'is_deleted'
            """)
            exists = cursor.fetchone()[0]
            
            if exists:
                print("✅ is_deleted字段已存在，无需添加")
                return True
            
            # 添加字段
            print("🔧 正在添加is_deleted字段...")
            cursor.execute("""
                ALTER TABLE cms_category 
                ADD COLUMN is_deleted TINYINT(1) NOT NULL DEFAULT 0
            """)
            print("✅ is_deleted字段添加成功")
            
            # 创建索引
            print("🔧 正在创建索引...")
            cursor.execute("""
                CREATE INDEX cms_category_is_deleted_idx 
                ON cms_category(is_deleted)
            """)
            print("✅ 索引创建成功")
            
            # 验证
            cursor.execute("""
                SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_DEFAULT
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'cms_category' 
                AND COLUMN_NAME = 'is_deleted'
            """)
            result = cursor.fetchone()
            print(f"\n✅ 验证成功: {result}")
            
            return True
            
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("Category is_deleted字段添加脚本")
    print("=" * 60)
    
    success = add_category_is_deleted()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 成功！Category表已准备就绪")
        print("=" * 60)
        print("\n下一步：修改migration文件，然后执行 python3 manage.py migrate")
    else:
        print("\n" + "=" * 60)
        print("❌ 失败！请检查错误信息")
        print("=" * 60)
        sys.exit(1)
