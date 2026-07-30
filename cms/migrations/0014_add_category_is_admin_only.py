# Hand-written migration for adding is_admin_only field to Category
# (makemigrations could not run due to environment constraints)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0013_alter_categorytranslation_master'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='is_admin_only',
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text='标记为True时，该分类下的文章仅管理员可创建/编辑/删除，Member不可操作',
                verbose_name='管理员专属',
            ),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(
                fields=['tenant', 'is_admin_only'],
                name='cms_cat_tenant_admin_only_idx',
            ),
        ),
    ]
