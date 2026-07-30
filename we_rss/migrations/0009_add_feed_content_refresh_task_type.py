from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("we_rss", "0008_memberseokeyword_and_relations"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wechatsynctask",
            name="task_type",
            field=models.CharField(
                choices=[
                    ("credential_login", "Credential Login"),
                    ("feed_sync", "Feed Sync"),
                    ("feed_sync_run", "Feed Sync Run"),
                    ("feed_sync_batch", "Feed Sync Batch"),
                    ("feed_content_refresh", "Feed Content Refresh"),
                    ("article_refresh", "Article Refresh"),
                    ("article_import", "Article Import"),
                    ("article_stats_refresh", "Article Stats Refresh"),
                ],
                max_length=30,
            ),
        ),
    ]
