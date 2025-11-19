#!/usr/bin/env python3
"""
手动执行 cms 0009 迁移的 SQL 脚本
由于 parler 包的问题导致无法使用 migrate 命令，所以手动执行 SQL
"""
import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

# SQL 语句列表
sql_statements = [
    # 1. 添加 member 字段到 cms_comment
    """
    ALTER TABLE cms_comment 
    ADD COLUMN member_id INT NULL
    """,
    
    # 2. 修改 user_id 允许 NULL
    """
    ALTER TABLE cms_comment 
    MODIFY COLUMN user_id INT NULL
    """,
    
    # 3. 添加索引
    """
    CREATE INDEX cms_comment_member__139f28_idx ON cms_comment (member_id)
    """,
    
    """
    CREATE INDEX cms_comment_tenant__39f0ee_idx ON cms_comment (tenant_id, member_id)
    """,
    
    # 4. 添加外键约束
    """
    ALTER TABLE cms_comment 
    ADD CONSTRAINT cms_comment_member_fk 
    FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE CASCADE
    """,
    
    # 5. 添加 member 字段到 cms_operation_log
    """
    ALTER TABLE cms_operation_log 
    ADD COLUMN member_id INT NULL
    """,
    
    # 6. 修改 user_id 允许 NULL
    """
    ALTER TABLE cms_operation_log 
    MODIFY COLUMN user_id INT NULL
    """,
    
    # 7. 添加索引
    """
    CREATE INDEX cms_operati_member__fc506b_idx ON cms_operation_log (member_id)
    """,
    
    """
    CREATE INDEX cms_operati_tenant__ee93cb_idx ON cms_operation_log (tenant_id, member_id)
    """,
    
    # 8. 添加外键约束
    """
    ALTER TABLE cms_operation_log 
    ADD CONSTRAINT cms_operation_log_member_fk 
    FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE CASCADE
    """,
    
    # 9. 添加检查约束（MySQL 8.0.16+）
    """
    ALTER TABLE cms_comment
    ADD CONSTRAINT comment_one_author_type_required 
    CHECK (
        (user_id IS NOT NULL AND member_id IS NULL AND guest_name IS NULL) OR
        (user_id IS NULL AND member_id IS NOT NULL AND guest_name IS NULL) OR
        (user_id IS NULL AND member_id IS NULL AND guest_name IS NOT NULL)
    )
    """,
    
    """
    ALTER TABLE cms_operation_log
    ADD CONSTRAINT operation_log_one_operator_required 
    CHECK (
        (user_id IS NOT NULL AND member_id IS NULL) OR
        (user_id IS NULL AND member_id IS NOT NULL)
    )
    """,
]

def main():
    print("开始执行 cms 0009 迁移...")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        for i, sql in enumerate(sql_statements, 1):
            try:
                print(f"\n[{i}/{len(sql_statements)}] 执行 SQL:")
                print(sql.strip())
                cursor.execute(sql)
                print("✓ 成功")
            except Exception as e:
                print(f"✗ 失败: {e}")
                # 某些错误可以忽略（如索引已存在）
                if "Duplicate" in str(e) or "already exists" in str(e):
                    print("  (已存在，跳过)")
                    continue
                else:
                    print(f"\n错误详情: {e}")
                    response = input("是否继续？ (y/n): ")
                    if response.lower() != 'y':
                        print("迁移已中止")
                        return
    
    print("\n" + "=" * 60)
    print("迁移执行完成！")
    print("\n现在标记迁移为已应用...")
    
    # 标记迁移为已应用
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('cms', '0009_remove_article_article_one_author_required_and_more', NOW())
            """)
        print("✓ 迁移已标记为已应用")
    except Exception as e:
        print(f"✗ 标记迁移失败: {e}")
        print("  请手动执行: python3 manage.py migrate cms 0009 --fake")
    
    print("\n迁移完成！可以开始测试了。")

if __name__ == '__main__':
    main()
