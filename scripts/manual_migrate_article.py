#!/usr/bin/env python3
"""
手动执行Article模型的数据库迁移
绕过django-parler的迁移问题
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def execute_migration():
    """执行Article模型迁移SQL"""
    
    with connection.cursor() as cursor:
        try:
            print("=" * 60)
            print("开始执行Article模型迁移")
            print("=" * 60)
            
            # 步骤1: 添加新字段
            print("\n步骤1: 添加新字段...")
            try:
                cursor.execute("""
                    ALTER TABLE cms_article 
                    ADD COLUMN author_content_type_id INT NULL,
                    ADD COLUMN author_object_id INT UNSIGNED NULL,
                    ADD CONSTRAINT cms_article_author_content_type_fk 
                        FOREIGN KEY (author_content_type_id) 
                        REFERENCES django_content_type(id)
                """)
                print("✓ 新字段添加成功")
            except Exception as e:
                if "Duplicate column" in str(e):
                    print("⚠ 字段已存在，跳过此步骤")
                else:
                    raise
            
            # 步骤2: 迁移数据
            print("\n步骤2: 迁移现有数据...")
            cursor.execute("""
                UPDATE cms_article 
                SET author_content_type_id = (
                    SELECT id FROM django_content_type 
                    WHERE app_label='users' AND model='user' LIMIT 1
                ),
                author_object_id = author_id
                WHERE author_id IS NOT NULL
            """)
            affected_rows = cursor.rowcount
            print(f"✓ 成功迁移 {affected_rows} 篇文章的作者数据")
            
            # 步骤3: 删除旧字段
            print("\n步骤3: 删除旧字段...")
            cursor.execute("""
                ALTER TABLE cms_article 
                DROP FOREIGN KEY cms_article_author_id_7a9eef23_fk_user_id
            """)
            cursor.execute("""
                ALTER TABLE cms_article 
                DROP COLUMN author_id
            """)
            print("✓ 旧字段删除成功")
            
            # 步骤4: 添加索引
            print("\n步骤4: 添加索引...")
            cursor.execute("""
                CREATE INDEX cms_article_author__935039_idx 
                ON cms_article(author_content_type_id, author_object_id)
            """)
            cursor.execute("""
                CREATE INDEX cms_article_tenant__cc6d2a_idx 
                ON cms_article(tenant_id, author_content_type_id, author_object_id)
            """)
            print("✓ 索引创建成功")
            
            print("\n" + "=" * 60)
            print("✅ 数据库迁移成功完成！")
            print("=" * 60)
            print("\n下一步: 执行fake迁移标记")
            print("命令: python3 manage.py migrate cms 0007 --fake")
            
        except Exception as e:
            print(f"\n❌ 迁移失败: {str(e)}")
            print("\n尝试回滚...")
            connection.rollback()
            sys.exit(1)

if __name__ == '__main__':
    execute_migration()
