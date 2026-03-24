import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("we_rss", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="wechatarticle",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, verbose_name="是否删除"),
        ),
        migrations.AddField(
            model_name="wechatcredential",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, verbose_name="是否删除"),
        ),
        migrations.AddField(
            model_name="wechatcredentialloginsession",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, verbose_name="是否删除"),
        ),
        migrations.AddField(
            model_name="wechatfeed",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, verbose_name="是否删除"),
        ),
        migrations.AddField(
            model_name="wechatsynctask",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False, verbose_name="是否删除"),
        ),
        migrations.AlterField(
            model_name="wechatarticle",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True, verbose_name="创建时间"),
        ),
        migrations.AlterField(
            model_name="wechatarticle",
            name="tenant",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="tenants.tenant",
                verbose_name="租户",
            ),
        ),
        migrations.AlterField(
            model_name="wechatarticle",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间"),
        ),
        migrations.AlterField(
            model_name="wechatcredential",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True, verbose_name="创建时间"),
        ),
        migrations.AlterField(
            model_name="wechatcredential",
            name="tenant",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="tenants.tenant",
                verbose_name="租户",
            ),
        ),
        migrations.AlterField(
            model_name="wechatcredential",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间"),
        ),
        migrations.AlterField(
            model_name="wechatcredentialloginsession",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True, verbose_name="创建时间"),
        ),
        migrations.AlterField(
            model_name="wechatcredentialloginsession",
            name="tenant",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="tenants.tenant",
                verbose_name="租户",
            ),
        ),
        migrations.AlterField(
            model_name="wechatcredentialloginsession",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间"),
        ),
        migrations.AlterField(
            model_name="wechatfeed",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True, verbose_name="创建时间"),
        ),
        migrations.AlterField(
            model_name="wechatfeed",
            name="tenant",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="tenants.tenant",
                verbose_name="租户",
            ),
        ),
        migrations.AlterField(
            model_name="wechatfeed",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间"),
        ),
        migrations.AlterField(
            model_name="wechatsynctask",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True, verbose_name="创建时间"),
        ),
        migrations.AlterField(
            model_name="wechatsynctask",
            name="tenant",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_set",
                to="tenants.tenant",
                verbose_name="租户",
            ),
        ),
        migrations.AlterField(
            model_name="wechatsynctask",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间"),
        ),
    ]
