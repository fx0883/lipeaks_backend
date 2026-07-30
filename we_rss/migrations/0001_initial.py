import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("tenants", "0002_alter_tenantquota_current_storage_used_mb"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WechatCredential",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("expired", "Expired"),
                            ("invalid", "Invalid"),
                            ("disabled", "Disabled"),
                            ("pending", "Pending"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("token", models.TextField()),
                ("cookie", models.TextField()),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("last_login_at", models.DateTimeField(blank=True, null=True)),
                ("last_check_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True, default="")),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_we_rss_credentials",
                        to="users.member",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="we_rss_credentials",
                        to="tenants.tenant",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_we_rss_credentials",
                        to="users.member",
                    ),
                ),
            ],
            options={
                "db_table": "we_rss_wechat_credential",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="WechatArticle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_id", models.CharField(blank=True, default="", max_length=100)),
                ("title", models.CharField(blank=True, default="", max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("content", models.TextField(blank=True, default="")),
                ("url", models.TextField(blank=True, default="")),
                ("pic_url", models.TextField(blank=True, default="")),
                ("publish_time", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(default="active", max_length=20)),
                ("is_read", models.BooleanField(default=False)),
                ("is_favorite", models.BooleanField(default=False)),
                ("last_refreshed_at", models.DateTimeField(blank=True, null=True)),
                ("read_num", models.PositiveIntegerField(default=0)),
                ("like_num", models.PositiveIntegerField(default=0)),
                ("old_like_num", models.PositiveIntegerField(default=0)),
                ("share_num", models.PositiveIntegerField(default=0)),
                ("collect_num", models.PositiveIntegerField(default=0)),
                ("comment_count", models.PositiveIntegerField(default=0)),
                ("comment_reply_count", models.PositiveIntegerField(default=0)),
                ("comment_total_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="we_rss_articles",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "we_rss_wechat_article",
                "ordering": ["-publish_time", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="WechatSyncTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "task_type",
                    models.CharField(
                        choices=[
                            ("credential_login", "Credential Login"),
                            ("feed_sync", "Feed Sync"),
                            ("article_refresh", "Article Refresh"),
                            ("article_import", "Article Import"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("task_key", models.CharField(blank=True, default="", max_length=255)),
                ("target_type", models.CharField(blank=True, default="", max_length=30)),
                ("target_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("message", models.TextField(blank=True, default="")),
                ("request_payload", models.JSONField(blank=True, null=True)),
                ("result_payload", models.JSONField(blank=True, null=True)),
                ("celery_task_id", models.CharField(blank=True, default="", max_length=255)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_we_rss_sync_tasks",
                        to="users.member",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="we_rss_sync_tasks",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "we_rss_wechat_sync_task",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="WechatCredentialLoginSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.CharField(max_length=64, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("scanned", "Scanned"),
                            ("confirmed", "Confirmed"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("expired", "Expired"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("qr_code_url", models.TextField(blank=True, default="")),
                ("qr_code_image", models.TextField(blank=True, default="")),
                ("scan_status", models.CharField(blank=True, default="", max_length=50)),
                ("token_snapshot", models.TextField(blank=True, default="")),
                ("cookie_snapshot", models.TextField(blank=True, default="")),
                ("error_message", models.TextField(blank=True, default="")),
                ("expired_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_we_rss_login_sessions",
                        to="users.member",
                    ),
                ),
                (
                    "credential",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="login_sessions",
                        to="we_rss.wechatcredential",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="we_rss_login_sessions",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "we_rss_wechat_credential_login_session",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="WechatFeed",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_id", models.CharField(blank=True, default="", max_length=100)),
                ("faker_id", models.CharField(blank=True, default="", max_length=100)),
                ("biz", models.CharField(blank=True, default="", max_length=100)),
                ("mp_name", models.CharField(max_length=255)),
                ("mp_cover", models.TextField(blank=True, default="")),
                ("mp_intro", models.TextField(blank=True, default="")),
                ("status", models.CharField(default="active", max_length=20)),
                ("sync_time", models.DateTimeField(blank=True, null=True)),
                ("update_time", models.DateTimeField(blank=True, null=True)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_we_rss_feeds",
                        to="users.member",
                    ),
                ),
                (
                    "credential",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="feeds",
                        to="we_rss.wechatcredential",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="we_rss_feeds",
                        to="tenants.tenant",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_we_rss_feeds",
                        to="users.member",
                    ),
                ),
            ],
            options={
                "db_table": "we_rss_wechat_feed",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="wechatarticle",
            name="feed",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="articles",
                to="we_rss.wechatfeed",
            ),
        ),
    ]
