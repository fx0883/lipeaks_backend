# Generated migration to replace GenericForeignKey with dual ForeignKeys

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


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


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0007_remove_article_author_article_author_content_type_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0001_initial'),
    ]

    operations = [
        # 步骤1: 添加新字段（使用BigIntegerField确保与User/Member.id类型匹配）
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
        
        # 步骤2: 数据迁移
        migrations.RunPython(
            migrate_author_to_dual_fk,
            reverse_migrate
        ),
        
        # 步骤3: 删除旧字段
        migrations.RemoveField(
            model_name='article',
            name='author_content_type',
        ),
        migrations.RemoveField(
            model_name='article',
            name='author_object_id',
        ),
        
        # 步骤4: 添加约束
        migrations.AddConstraint(
            model_name='article',
            constraint=models.CheckConstraint(
                check=models.Q(
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

