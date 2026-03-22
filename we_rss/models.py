from django.db import models, transaction


class WechatCredential(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        INVALID = "invalid", "Invalid"
        DISABLED = "disabled", "Disabled"
        PENDING = "pending", "Pending"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_credentials",
    )
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    token = models.TextField()
    cookie = models.TextField()
    expires_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_check_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "users.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_we_rss_credentials",
    )
    updated_by = models.ForeignKey(
        "users.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_we_rss_credentials",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "we_rss_wechat_credential"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.is_default:
                type(self).objects.filter(tenant=self.tenant).exclude(pk=self.pk).update(is_default=False)


class WechatCredentialLoginSession(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SCANNED = "scanned", "Scanned"
        CONFIRMED = "confirmed", "Confirmed"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_login_sessions",
    )
    session_id = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    qr_code_url = models.TextField(blank=True, default="")
    qr_code_image = models.TextField(blank=True, default="")
    scan_status = models.CharField(max_length=50, blank=True, default="")
    token_snapshot = models.TextField(blank=True, default="")
    cookie_snapshot = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    expired_at = models.DateTimeField(null=True, blank=True)
    credential = models.ForeignKey(
        "we_rss.WechatCredential",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_sessions",
    )
    created_by = models.ForeignKey(
        "users.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_we_rss_login_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "we_rss_wechat_credential_login_session"
        ordering = ["-created_at"]


class WechatFeed(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_feeds",
    )
    credential = models.ForeignKey(
        "we_rss.WechatCredential",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feeds",
    )
    source_id = models.CharField(max_length=100, blank=True, default="")
    faker_id = models.CharField(max_length=100, blank=True, default="")
    biz = models.CharField(max_length=100, blank=True, default="")
    mp_name = models.CharField(max_length=255)
    mp_cover = models.TextField(blank=True, default="")
    mp_intro = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, default="active")
    sync_time = models.DateTimeField(null=True, blank=True)
    update_time = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "users.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_we_rss_feeds",
    )
    updated_by = models.ForeignKey(
        "users.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_we_rss_feeds",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "we_rss_wechat_feed"
        ordering = ["-created_at"]


class WechatArticle(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_articles",
    )
    feed = models.ForeignKey(
        "we_rss.WechatFeed",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    source_id = models.CharField(max_length=100, blank=True, default="")
    title = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    content = models.TextField(blank=True, default="")
    url = models.TextField(blank=True, default="")
    pic_url = models.TextField(blank=True, default="")
    publish_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default="active")
    is_read = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    last_refreshed_at = models.DateTimeField(null=True, blank=True)
    read_num = models.PositiveIntegerField(default=0)
    like_num = models.PositiveIntegerField(default=0)
    old_like_num = models.PositiveIntegerField(default=0)
    share_num = models.PositiveIntegerField(default=0)
    collect_num = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    comment_reply_count = models.PositiveIntegerField(default=0)
    comment_total_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "we_rss_wechat_article"
        ordering = ["-publish_time", "-created_at"]


class WechatSyncTask(models.Model):
    class TaskType(models.TextChoices):
        CREDENTIAL_LOGIN = "credential_login", "Credential Login"
        FEED_SYNC = "feed_sync", "Feed Sync"
        ARTICLE_REFRESH = "article_refresh", "Article Refresh"
        ARTICLE_IMPORT = "article_import", "Article Import"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_sync_tasks",
    )
    task_type = models.CharField(max_length=30, choices=TaskType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    task_key = models.CharField(max_length=255, blank=True, default="")
    target_type = models.CharField(max_length=30, blank=True, default="")
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    message = models.TextField(blank=True, default="")
    request_payload = models.JSONField(null=True, blank=True)
    result_payload = models.JSONField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        "users.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_we_rss_sync_tasks",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "we_rss_wechat_sync_task"
        ordering = ["-created_at"]
