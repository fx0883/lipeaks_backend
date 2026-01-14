"""
租户隔离重构 - 直接应用数据库变更

解决问题：Django 迁移失败因为列已存在/不存在的不一致状态

使用方法：
    python scripts/apply_tenant_isolation_migration.py
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lipeaks_backend.settings')

import django
django.setup()

from django.db import connection


def check_column_exists(table, column):
    """检查列是否存在"""
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = '{table}' 
            AND column_name = '{column}'
        """)
        return cursor.fetchone()[0] > 0


def add_column_if_not_exists(table, column, definition):
    """如果列不存在则添加"""
    if not check_column_exists(table, column):
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        print(f"✓ Added column {table}.{column}")
    else:
        print(f"= Column {table}.{column} already exists")


def drop_column_if_exists(table, column):
    """如果列存在则删除"""
    if check_column_exists(table, column):
        with connection.cursor() as cursor:
            # 先删除可能存在的外键约束
            cursor.execute(f"""
                SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table}' 
                AND COLUMN_NAME = '{column}'
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            for row in cursor.fetchall():
                try:
                    cursor.execute(f"ALTER TABLE {table} DROP FOREIGN KEY {row[0]}")
                    print(f"  Dropped FK: {row[0]}")
                except Exception as e:
                    print(f"  FK drop failed (may not exist): {e}")
            
            cursor.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
        print(f"✓ Dropped column {table}.{column}")
    else:
        print(f"= Column {table}.{column} does not exist")


def drop_index_if_exists(table, index_name):
    """如果索引存在则删除"""
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT COUNT(*) FROM information_schema.STATISTICS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = '{table}' 
            AND INDEX_NAME = '{index_name}'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute(f"DROP INDEX {index_name} ON {table}")
            print(f"✓ Dropped index {index_name} on {table}")


def main():
    print("=" * 60)
    print("租户隔离重构 - 应用数据库变更")
    print("=" * 60)
    
    # ============ 1. 添加 is_deleted 字段 ============
    print("\n[Step 1] 添加 is_deleted 字段...")
    for table in ['task_category', 'task', 'check_record', 'task_template', 'checkin_cycle']:
        add_column_if_not_exists(table, 'is_deleted', 'TINYINT(1) NOT NULL DEFAULT 0')
    
    # ============ 2. 添加 updated_at 到 check_record ============
    print("\n[Step 2] 添加 updated_at 到 check_record...")
    add_column_if_not_exists('check_record', 'updated_at', 'DATETIME(6) NULL')
    
    # ============ 3. 添加 member_id 字段 ============
    print("\n[Step 3] 添加 member_id 字段...")
    add_column_if_not_exists('task', 'member_id', 'BIGINT NULL')
    add_column_if_not_exists('check_record', 'member_id', 'BIGINT NULL')
    add_column_if_not_exists('checkin_cycle', 'member_id', 'BIGINT NULL')
    
    # ============ 4. 删除 user_id 字段 ============
    print("\n[Step 4] 删除 user_id 字段...")
    for table in ['task_category', 'task', 'check_record', 'task_template', 'checkin_cycle']:
        drop_column_if_exists(table, 'user_id')
    
    # ============ 5. 修改 task_id 为可空 ============
    print("\n[Step 5] 修改 check_record.task_id 为可空...")
    with connection.cursor() as cursor:
        try:
            cursor.execute("""
                ALTER TABLE check_record 
                MODIFY COLUMN task_id BIGINT NULL
            """)
            print("✓ Modified check_record.task_id to nullable")
        except Exception as e:
            print(f"= Modification may not be needed: {e}")
    
    # ============ 6. 更新 unique_together ============
    print("\n[Step 6] 更新唯一约束...")
    # 删除旧的唯一约束
    drop_index_if_exists('task_category', 'task_category_name_user_id_tenant_id_uniq')
    drop_index_if_exists('task_category', 'task_category_name_user_id_tenant_id_c82af4d0_uniq')
    drop_index_if_exists('check_record', 'check_record_user_id_task_id_check_date_uniq')
    drop_index_if_exists('check_record', 'check_record_user_id_task_id_check_date_37c9aaef_uniq')
    
    # ============ 7. 添加外键 ============
    print("\n[Step 7] 添加 member 外键...")
    with connection.cursor() as cursor:
        for table in ['task', 'check_record', 'checkin_cycle']:
            try:
                cursor.execute(f"""
                    ALTER TABLE {table}
                    ADD CONSTRAINT fk_{table}_member
                    FOREIGN KEY (member_id) REFERENCES member(id)
                    ON DELETE CASCADE
                """)
                print(f"✓ Added FK for {table}.member_id")
            except Exception as e:
                print(f"= FK for {table}.member_id may already exist: {e}")
    
    # ============ 8. 标记迁移为已应用 ============
    print("\n[Step 8] 标记迁移为已应用...")
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied) 
            VALUES ('check_system', '0003_tenant_isolation_refactor', NOW())
            ON DUPLICATE KEY UPDATE applied = NOW()
        """)
    print("✓ Marked migration as applied")
    
    print("\n" + "=" * 60)
    print("完成！数据库已更新为租户隔离架构。")
    print("=" * 60)


if __name__ == '__main__':
    main()
