# Convert TaskCategory to use django-parler TranslatableModel
import django.db.models.deletion
import parler.models
from django.db import migrations, models
import json


def migrate_to_parler(apps, schema_editor):
    """迁移数据到parler翻译表"""
    from django.db import connection
    
    languages = ['zh-hans', 'en', 'zh-hant', 'ja', 'ko', 'fr']
    
    with connection.cursor() as cursor:
        # 检查旧字段是否存在
        cursor.execute("SHOW COLUMNS FROM task_category LIKE 'name'")
        if not cursor.fetchone():
            print("Already migrated")
            return
            
        # 读取旧数据
        cursor.execute("""
            SELECT id, name, description, goal, tip, quote, translations
            FROM task_category
            WHERE is_deleted = 0
        """)
        rows = cursor.fetchall()
    
    # 为每个category创建翻译
    for row in rows:
        cid, name, desc, goal, tip, quote, trans_json = row
        
        try:
            old_trans = json.loads(trans_json) if trans_json else {}
        except:
            old_trans = {}
        
        for lang in languages:
            t_name = old_trans.get('name', {}).get(lang, name or f'Cat{cid}')
            t_desc = old_trans.get('description', {}).get(lang, desc or '')
            t_goal = old_trans.get('goal', {}).get(lang, goal or '')
            t_tip = old_trans.get('tip', {}).get(lang, tip or '')
            t_quote = old_trans.get('quote', {}).get(lang, quote or '')
            
            with connection.cursor() as c:
                c.execute("""
                    INSERT INTO task_category_translation 
                    (master_id, language_code, name, description, goal, tip, quote)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [cid, lang, t_name, t_desc, t_goal, t_tip, t_quote])


class Migration(migrations.Migration):

    dependencies = [
        ('check_system', '0003_tenant_isolation_refactor'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # 数据库操作：创建表，迁移数据，删除旧列
                migrations.RunSQL("""
                    CREATE TABLE IF NOT EXISTS `task_category_translation` (
                        `id` bigint NOT NULL AUTO_INCREMENT,
                        `language_code` varchar(15) NOT NULL,
                        `name` varchar(50) NOT NULL,
                        `description` varchar(200) NOT NULL DEFAULT '',
                        `goal` longtext NOT NULL,
                        `tip` longtext NOT NULL,
                        `quote` varchar(200) NOT NULL DEFAULT '',
                        `master_id` bigint DEFAULT NULL,
                        PRIMARY KEY (`id`),
                        UNIQUE KEY `task_category_translati_language_code_master_i_3b129a6c_uniq` (`language_code`,`master_id`),
                        KEY `task_category_trans_master_id_a9e60e91_fk_task_cate` (`master_id`),
                        KEY `task_category_translation_language_code_8aae49f6` (`language_code`),
                        CONSTRAINT `task_category_trans_master_id_a9e60e91_fk_task_cate` 
                            FOREIGN KEY (`master_id`) REFERENCES `task_category` (`id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """, reverse_sql="DROP TABLE IF EXISTS `task_category_translation`"),
                
                migrations.RunPython(migrate_to_parler, reverse_code=migrations.RunPython.noop),
                
                migrations.RunSQL("ALTER TABLE task_category DROP COLUMN name", reverse_sql=""),
                migrations.RunSQL("ALTER TABLE task_category DROP COLUMN description", reverse_sql=""),
                migrations.RunSQL("ALTER TABLE task_category DROP COLUMN goal", reverse_sql=""),
                migrations.RunSQL("ALTER TABLE task_category DROP COLUMN tip", reverse_sql=""),
                migrations.RunSQL("ALTER TABLE task_category DROP COLUMN quote", reverse_sql=""),
                migrations.RunSQL("ALTER TABLE task_category DROP COLUMN translations", reverse_sql=""),
            ],
            state_operations=[
                # Django状态操作：告诉Django模型现在是什么样子
                migrations.CreateModel(
                    name='TaskCategoryTranslation',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                        ('language_code', models.CharField(db_index=True, max_length=15, verbose_name='Language')),
                        ('name', models.CharField(max_length=50, verbose_name='类型名称')),
                        ('description', models.CharField(blank=True, max_length=200, verbose_name='类型描述')),
                        ('goal', models.TextField(blank=True, verbose_name='主题目标')),
                        ('tip', models.TextField(blank=True, verbose_name='小贴士')),
                        ('quote', models.CharField(blank=True, max_length=200, verbose_name='名言')),
                        ('master', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='check_system.taskcategory')),
                    ],
                    options={
                        'verbose_name': '打卡类型 Translation',
                        'db_table': 'task_category_translation',
                        'managed': True,
                        'default_permissions': (),
                        'unique_together': {('language_code', 'master')},
                    },
                    bases=(parler.models.TranslatedFieldsModelMixin, models.Model),
                ),
                migrations.RemoveField(model_name='taskcategory', name='name'),
                migrations.RemoveField(model_name='taskcategory', name='description'),
                migrations.RemoveField(model_name='taskcategory', name='goal'),
                migrations.RemoveField(model_name='taskcategory', name='tip'),
                migrations.RemoveField(model_name='taskcategory', name='quote'),
                migrations.RemoveField(model_name='taskcategory', name='translations'),
            ],
        ),
    ]
