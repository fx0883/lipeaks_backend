from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("we_rss", "0006_add_article_stats_refresh_task_type"),
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
                    ("article_refresh", "Article Refresh"),
                    ("article_import", "Article Import"),
                    ("article_stats_refresh", "Article Stats Refresh"),
                ],
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="wechatsynctask",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("running", "Running"),
                    ("success", "Success"),
                    ("partial_success", "Partial Success"),
                    ("timed_out", "Timed Out"),
                    ("failed", "Failed"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
