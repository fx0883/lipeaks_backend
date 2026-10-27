# Generated migration to replace GenericForeignKey with dual ForeignKeys

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def add_columns_safely(apps, schema_editor):
    """
    确保 cms_article 物理表存在 user_id 与 member_id 列
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cms_article' AND COLUMN_NAME = 'user_id';
        """)
        if cursor.fetchone()[0] == 0:
            schema_editor.execute("ALTER TABLE `cms_article` ADD COLUMN `user_id` BIGINT NULL;")

        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cms_article' AND COLUMN_NAME = 'member_id';
        """)
        if cursor.fetchone()[0] == 0:
            schema_editor.execute("ALTER TABLE `cms_article` ADD COLUMN `member_id` BIGINT NULL;")


def migrate_author_to_dual_fk(apps, schema_editor):
    """
    将GenericForeignKey的数据迁移到user和member字段
    使用原生SQL避免模型约束问题
    """
    from django.db import connection
    
    with connection.cursor() as cursor:
        # 获取User和Member的ContentType ID
        cursor.execute("""
            SELECT id FROM django_content_type 
            WHERE app_label='users' AND model='user'
        """)
        user_ct_result = cursor.fetchone()
        
        cursor.execute("""
            SELECT id FROM django_content_type 
            WHERE app_label='users' AND model='member'
        """)
        member_ct_result = cursor.fetchone()
        
        if not user_ct_result or not member_ct_result:
            print("Warning: ContentType not found, skipping migration")
            return
        
        user_ct_id = user_ct_result[0]
        member_ct_id = member_ct_result[0]
        
        # 迁移User作者
        cursor.execute(f"""
            UPDATE cms_article 
            SET user_id = author_object_id 
            WHERE author_content_type_id = {user_ct_id} 
            AND author_object_id IS NOT NULL
        """)
        user_count = cursor.rowcount
        print(f"Migrated {user_count} articles with User authors")
        
        # 迁移Member作者
        cursor.execute(f"""
            UPDATE cms_article 
            SET member_id = author_object_id 
            WHERE author_content_type_id = {member_ct_id} 
            AND author_object_id IS NOT NULL
        """)
        member_count = cursor.rowcount
        print(f"Migrated {member_count} articles with Member authors")
        
        print(f"Author migration completed! Total: {user_count + member_count} articles")


def reverse_migrate(apps, schema_editor):
    """
    反向迁移：从user和member字段恢复到GenericForeignKey
    使用原生SQL避免模型约束问题
    """
    from django.db import connection
    
    with connection.cursor() as cursor:
        # 获取User和Member的ContentType ID
        cursor.execute("""
            SELECT id FROM django_content_type 
            WHERE app_label='users' AND model='user'
        """)
        user_ct_result = cursor.fetchone()
        
        cursor.execute("""
            SELECT id FROM django_content_type 
            WHERE app_label='users' AND model='member'
        """)
        member_ct_result = cursor.fetchone()
        
        if not user_ct_result or not member_ct_result:
            print("Warning: ContentType not found, skipping reverse migration")
            return
        
        user_ct_id = user_ct_result[0]
        member_ct_id = member_ct_result[0]
        
        # 恢复User作者
        cursor.execute(f"""
            UPDATE cms_article 
            SET author_content_type_id = {user_ct_id},
                author_object_id = user_id
            WHERE user_id IS NOT NULL
        """)
        user_count = cursor.rowcount
        print(f"Reversed {user_count} articles with User authors")
        
        # 恢复Member作者
        cursor.execute(f"""
            UPDATE cms_article 
            SET author_content_type_id = {member_ct_id},
                author_object_id = member_id
            WHERE member_id IS NOT NULL
        """)
        member_count = cursor.rowcount
        print(f"Reversed {member_count} articles with Member authors")
        
        print(f"Reverse migration completed! Total: {user_count + member_count} articles")


def drop_generic_fields_safely(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT CONSTRAINT_NAME 
            FROM information_schema.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = DATABASE() 
              AND TABLE_NAME = 'cms_article' 
              AND COLUMN_NAME = 'author_content_type_id' 
              AND REFERENCED_TABLE_NAME IS NOT NULL;
        """)
        for row in cursor.fetchall():
            schema_editor.execute(f"ALTER TABLE `cms_article` DROP FOREIGN KEY `{row[0]}`;")
        
        for col in ['author_content_type_id', 'author_object_id']:
            cursor.execute(f"""
                SELECT COUNT(*) FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cms_article' AND COLUMN_NAME = '{col}';
            """)
            if cursor.fetchone()[0] > 0:
                schema_editor.execute(f"ALTER TABLE `cms_article` DROP COLUMN `{col}`;")


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('cms', '0007_remove_article_author_article_author_content_type_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # 步骤1: 物理添加新字段
                migrations.RunPython(
                    add_columns_safely,
                    migrations.RunPython.noop
                ),
                # 步骤2: 数据迁移
                migrations.RunPython(
                    migrate_author_to_dual_fk,
                    reverse_migrate
                ),
                # 步骤3: 安全删除旧字段
                migrations.RunPython(
                    drop_generic_fields_safely,
                    migrations.RunPython.noop
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='article',
                    name='user',
                    field=models.ForeignKey(
                        blank=True,
                        db_index=True,
                        help_text='如果作者是管理员User，此字段非空',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='articles',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='管理员作者',
                        db_column='user_id'  # 显式指定列名
                    ),
                ),
                migrations.AddField(
                    model_name='article',
                    name='member',
                    field=models.ForeignKey(
                        blank=True,
                        db_index=True,
                        help_text='如果作者是Member，此字段非空',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='articles',
                        to='users.member',
                        verbose_name='Member作者',
                        db_column='member_id'  # 显式指定列名
                    ),
                ),
            ]
        ),
        
        # 步骤4: 添加约束
        migrations.AddConstraint(
            model_name='article',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(('user__isnull', False), ('member__isnull', True)),
                    models.Q(('user__isnull', True), ('member__isnull', False)),
                    _connector='OR'
                ),
                name='article_one_author_required'
            ),
        ),
        
        # 步骤5: 更新索引
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['user'], name='cms_article_user_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['member'], name='cms_article_member_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['tenant', 'user'], name='cms_article_tenant_user_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['tenant', 'member'], name='cms_article_tenant_member_idx'),
        ),
    ]
