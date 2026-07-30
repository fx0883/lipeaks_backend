from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("we_rss", "0005_membertag_memberfeedtagrelation_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wechatsynctask",
            name="task_type",
            field=models.CharField(
                choices=[
                    ("credential_login", "Credential Login"),
                    ("feed_sync", "Feed Sync"),
                    ("article_refresh", "Article Refresh"),
                    ("article_import", "Article Import"),
                    ("article_stats_refresh", "Article Stats Refresh"),
                ],
                max_length=30,
            ),
        ),
    ]
