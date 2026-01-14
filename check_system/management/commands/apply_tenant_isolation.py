"""
租户隔离重构 - 应用数据库变更

使用方法:
    python manage.py apply_tenant_isolation
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '直接应用租户隔离数据库变更'
    
    def check_column_exists(self, table, column):
        """检查列是否存在"""
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = '{table}' 
                AND column_name = '{column}'
            """)
            return cursor.fetchone()[0] > 0

    def add_column_if_not_exists(self, table, column, definition):
        """如果列不存在则添加"""
        if not self.check_column_exists(table, column):
            with connection.cursor() as cursor:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            self.stdout.write(self.style.SUCCESS(f"+ Added column {table}.{column}"))
        else:
            self.stdout.write(f"= Column {table}.{column} already exists")

    def drop_column_if_exists(self, table, column):
        """如果列存在则删除"""
        if self.check_column_exists(table, column):
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
                        self.stdout.write(f"  Dropped FK: {row[0]}")
                    except Exception as e:
                        self.stdout.write(f"  FK drop skipped: {e}")
                
                cursor.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
            self.stdout.write(self.style.SUCCESS(f"- Dropped column {table}.{column}"))
        else:
            self.stdout.write(f"= Column {table}.{column} does not exist")

    def drop_index_if_exists(self, table, index_name):
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
                self.stdout.write(self.style.SUCCESS(f"- Dropped index {index_name}"))

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("租户隔离重构 - 应用数据库变更")
        self.stdout.write("=" * 60)
        
        # 1. 添加 is_deleted
        self.stdout.write("\n[1] 添加 is_deleted 字段...")
        for table in ['task_category', 'task', 'check_record', 'task_template', 'checkin_cycle']:
            self.add_column_if_not_exists(table, 'is_deleted', 'TINYINT(1) NOT NULL DEFAULT 0')
        
        # 2. 添加 updated_at
        self.stdout.write("\n[2] 添加 updated_at 到 check_record...")
        self.add_column_if_not_exists('check_record', 'updated_at', 'DATETIME(6) NULL')
        
        # 3. 添加 member_id
        self.stdout.write("\n[3] 添加 member_id 字段...")
        self.add_column_if_not_exists('task', 'member_id', 'BIGINT NULL')
        self.add_column_if_not_exists('check_record', 'member_id', 'BIGINT NULL')
        self.add_column_if_not_exists('checkin_cycle', 'member_id', 'BIGINT NULL')
        
        # 4. 删除 user_id
        self.stdout.write("\n[4] 删除 user_id 字段...")
        for table in ['task_category', 'task', 'check_record', 'task_template', 'checkin_cycle']:
            self.drop_column_if_exists(table, 'user_id')
        
        # 5. 修改 task_id 可空
        self.stdout.write("\n[5] 修改 check_record.task_id 可空...")
        with connection.cursor() as cursor:
            try:
                cursor.execute("ALTER TABLE check_record MODIFY COLUMN task_id BIGINT NULL")
                self.stdout.write(self.style.SUCCESS("+ Modified task_id to nullable"))
            except Exception as e:
                self.stdout.write(f"= {e}")
        
        # 6. 更新约束
        self.stdout.write("\n[6] 删除旧约束...")
        for idx in ['task_category_name_user_id_tenant_id_uniq', 
                    'task_category_name_user_id_tenant_id_c82af4d0_uniq',
                    'check_record_user_id_task_id_check_date_uniq',
                    'check_record_user_id_task_id_check_date_37c9aaef_uniq']:
            table = 'task_category' if 'task_category' in idx else 'check_record'
            self.drop_index_if_exists(table, idx)
        
        # 7. 添加外键
        self.stdout.write("\n[7] 添加 member 外键...")
        with connection.cursor() as cursor:
            for table in ['task', 'check_record', 'checkin_cycle']:
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table}
                        ADD CONSTRAINT fk_{table}_member
                        FOREIGN KEY (member_id) REFERENCES member(id)
                        ON DELETE CASCADE
                    """)
                    self.stdout.write(self.style.SUCCESS(f"+ Added FK for {table}"))
                except Exception as e:
                    self.stdout.write(f"= FK exists or error: {e}")
        
        # 8. 标记迁移
        self.stdout.write("\n[8] 标记迁移...")
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('check_system', '0003_tenant_isolation_refactor', NOW())
                ON DUPLICATE KEY UPDATE applied = NOW()
            """)
        self.stdout.write(self.style.SUCCESS("+ Migration marked"))
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("完成！"))
