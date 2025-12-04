# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0011_remove_articlestatistics_last_updated_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='is_locked',
            field=models.BooleanField(default=False, help_text='锁定后文章不可编辑', verbose_name='是否锁定'),
        ),
    ]
