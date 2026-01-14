# Generated manually for tenant isolation refactoring

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    租户隔离重构迁移
    
    变更内容：
    1. 所有模型添加 is_deleted 字段（BaseModel）
    2. TaskCategory：移除 user FK
    3. Task：移除 user FK，添加 member FK
    4. CheckRecord：移除 user FK，添加 member FK，task 改为可选
    5. TaskTemplate：移除 user FK
    6. CheckinCycle：移除 user FK，添加 member FK，移除独立的 tenant/created_at/updated_at
    """

    dependencies = [
        ('users', '__first__'),
        ('check_system', '0002_add_21day_checkin_fields'),
    ]

    operations = [
        # ============ 1. 添加 is_deleted 字段到所有模型 ============
        migrations.AddField(
            model_name='taskcategory',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='是否删除'),
        ),
        migrations.AddField(
            model_name='task',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='是否删除'),
        ),
        migrations.AddField(
            model_name='checkrecord',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='是否删除'),
        ),
        migrations.AddField(
            model_name='checkrecord',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name='更新时间'),
        ),
        migrations.AddField(
            model_name='tasktemplate',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='是否删除'),
        ),
        migrations.AddField(
            model_name='checkincycle',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='是否删除'),
        ),

        # ============ 2. 添加 member FK 到需要的模型（先添加后删除 user）============
        migrations.AddField(
            model_name='task',
            name='member',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tasks',
                to='users.member',
                verbose_name='所属成员'
            ),
        ),
        migrations.AddField(
            model_name='checkrecord',
            name='member',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='check_records',
                to='users.member',
                verbose_name='所属成员'
            ),
        ),
        migrations.AddField(
            model_name='checkincycle',
            name='member',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='checkin_cycles',
                to='users.member',
                verbose_name='所属成员'
            ),
        ),

        # ============ 3. 移除 user FK ============
        migrations.RemoveField(
            model_name='taskcategory',
            name='user',
        ),
        migrations.RemoveField(
            model_name='task',
            name='user',
        ),
        migrations.RemoveField(
            model_name='checkrecord',
            name='user',
        ),
        migrations.RemoveField(
            model_name='tasktemplate',
            name='user',
        ),
        migrations.RemoveField(
            model_name='checkincycle',
            name='user',
        ),

        # ============ 4. 修改 task 字段为可选 ============
        migrations.AlterField(
            model_name='checkrecord',
            name='task',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='check_records',
                to='check_system.task',
                verbose_name='所属任务'
            ),
        ),

        # ============ 5. 更新 unique_together ============
        migrations.AlterUniqueTogether(
            name='taskcategory',
            unique_together={('name', 'tenant')},
        ),
        migrations.AlterUniqueTogether(
            name='checkrecord',
            unique_together=set(),
        ),
    ]
