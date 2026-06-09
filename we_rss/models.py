from django.db import models, transaction
from django.db.models.functions import Lower

from common.models import BaseModel


class WechatCredential(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        INVALID = "invalid", "Invalid"
        DISABLED = "disabled", "Disabled"
        PENDING = "pending", "Pending"

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
    class Meta:
        db_table = "we_rss_wechat_credential"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.is_default:
                type(self).objects.filter(tenant=self.tenant).exclude(pk=self.pk).update(is_default=False)


class WechatCredentialLoginSession(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SCANNED = "scanned", "Scanned"
        CONFIRMED = "confirmed", "Confirmed"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"

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
    class Meta:
        db_table = "we_rss_wechat_credential_login_session"
        ordering = ["-created_at"]


class WechatFeed(BaseModel):
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
    class Meta:
        db_table = "we_rss_wechat_feed"
        ordering = ["-created_at"]


class WechatArticle(BaseModel):
    class ArticleType(models.TextChoices):
        NEWS = "news", "News"
        NEWSPIC = "newspic", "Newspic"

    feed = models.ForeignKey(
        "we_rss.WechatFeed",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    source_id = models.CharField(max_length=100, blank=True, default="")
    article_type = models.CharField(max_length=20, choices=ArticleType.choices, default=ArticleType.NEWS)
    title = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    content = models.TextField(blank=True, default="")
    url = models.TextField(blank=True, default="")
    pic_url = models.TextField(blank=True, default="")
    publish_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default="active")
    last_refreshed_at = models.DateTimeField(null=True, blank=True)
    read_num = models.PositiveIntegerField(default=0)
    like_num = models.PositiveIntegerField(default=0)
    old_like_num = models.PositiveIntegerField(default=0)
    share_num = models.PositiveIntegerField(default=0)
    collect_num = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    comment_reply_count = models.PositiveIntegerField(default=0)
    comment_total_count = models.PositiveIntegerField(default=0)
    class Meta:
        db_table = "we_rss_wechat_article"
        ordering = ["-publish_time", "-created_at"]


class MemberFeedSubscription(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_member_feed_subscriptions",
    )
    member = models.ForeignKey(
        "users.Member",
        on_delete=models.CASCADE,
        related_name="we_rss_feed_subscriptions",
    )
    feed = models.ForeignKey(
        "we_rss.WechatFeed",
        on_delete=models.CASCADE,
        related_name="member_subscriptions",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "we_rss_member_feed_subscription"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["member", "feed"], name="we_rss_member_feed_subscription_unique"),
        ]
        indexes = [
            models.Index(fields=["tenant", "member"]),
            models.Index(fields=["tenant", "feed"]),
        ]


class MemberArticleFavorite(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_member_article_favorites",
    )
    member = models.ForeignKey(
        "users.Member",
        on_delete=models.CASCADE,
        related_name="we_rss_article_favorites",
    )
    article = models.ForeignKey(
        "we_rss.WechatArticle",
        on_delete=models.CASCADE,
        related_name="member_favorites",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "we_rss_member_article_favorite"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["member", "article"], name="we_rss_member_article_favorite_unique"),
        ]
        indexes = [
            models.Index(fields=["tenant", "member"]),
            models.Index(fields=["tenant", "article"]),
        ]


class MemberArticleState(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_member_article_states",
    )
    member = models.ForeignKey(
        "users.Member",
        on_delete=models.CASCADE,
        related_name="we_rss_article_states",
    )
    article = models.ForeignKey(
        "we_rss.WechatArticle",
        on_delete=models.CASCADE,
        related_name="member_states",
    )
    is_hidden = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    hidden_at = models.DateTimeField(null=True, blank=True)
    favorited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "we_rss_member_article_state"
        ordering = ["-updated_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["member", "article"], name="we_rss_member_article_state_unique"),
        ]
        indexes = [
            models.Index(fields=["tenant", "member", "article"]),
            models.Index(fields=["tenant", "member", "is_hidden", "article"]),
            models.Index(fields=["tenant", "member", "is_favorite", "article"]),
            models.Index(fields=["tenant", "article"]),
        ]


class MemberTag(BaseModel):
    member = models.ForeignKey(
        "users.Member",
        on_delete=models.CASCADE,
        related_name="we_rss_member_tags",
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=32, blank=True, default="")
    description = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        db_table = "we_rss_member_tag"
        ordering = ["-is_pinned", "sort_order", "-id"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "member",
                name="we_rss_member_tag_member_lower_name_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "member"]),
        ]


class MemberFeedTagRelation(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_member_feed_tag_relations",
    )
    member = models.ForeignKey(
        "users.Member",
        on_delete=models.CASCADE,
        related_name="we_rss_feed_tag_relations",
    )
    tag = models.ForeignKey(
        "we_rss.MemberTag",
        on_delete=models.CASCADE,
        related_name="feed_relations",
    )
    feed = models.ForeignKey(
        "we_rss.WechatFeed",
        on_delete=models.CASCADE,
        related_name="member_tag_relations",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "we_rss_member_feed_tag_relation"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "tag", "feed"],
                name="we_rss_member_feed_tag_relation_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "member"]),
            models.Index(fields=["tenant", "feed"]),
            models.Index(fields=["tenant", "tag"]),
        ]


class MemberArticleTagRelation(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_member_article_tag_relations",
    )
    member = models.ForeignKey(
        "users.Member",
        on_delete=models.CASCADE,
        related_name="we_rss_article_tag_relations",
    )
    tag = models.ForeignKey(
        "we_rss.MemberTag",
        on_delete=models.CASCADE,
        related_name="article_relations",
    )
    article = models.ForeignKey(
        "we_rss.WechatArticle",
        on_delete=models.CASCADE,
        related_name="member_tag_relations",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "we_rss_member_article_tag_relation"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "tag", "article"],
                name="we_rss_member_article_tag_relation_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "member"]),
            models.Index(fields=["tenant", "article"]),
            models.Index(fields=["tenant", "tag"]),
        ]


class MemberSeoKeyword(BaseModel):
    member = models.ForeignKey(
        "users.Member",
        on_delete=models.CASCADE,
        related_name="we_rss_seo_keywords",
    )
    keyword = models.CharField(max_length=255)
    search_index = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "we_rss_member_seo_keyword"
        ordering = ["-updated_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                Lower("keyword"),
                "member",
                name="we_rss_member_seo_keyword_member_lower_keyword_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "member"], name="we_rss_memb_tenant__a1adcc_idx"),
            models.Index(fields=["tenant", "member", "search_index"], name="we_rss_memb_tenant__40fb9f_idx"),
            models.Index(fields=["tenant", "member", "keyword"], name="we_rss_memb_tenant__1bedf6_idx"),
        ]


class MemberTagSeoKeywordRelation(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="we_rss_member_tag_seo_keyword_relations",
    )
    member = models.ForeignKey(
        "users.Member",
        on_delete=models.CASCADE,
        related_name="we_rss_tag_seo_keyword_relations",
    )
    tag = models.ForeignKey(
        "we_rss.MemberTag",
        on_delete=models.CASCADE,
        related_name="seo_keyword_relations",
    )
    seo_keyword = models.ForeignKey(
        "we_rss.MemberSeoKeyword",
        on_delete=models.CASCADE,
        related_name="keyword_tag_relations",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "we_rss_member_tag_seo_keyword_relation"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "tag", "seo_keyword"],
                name="we_rss_member_tag_seo_keyword_relation_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "member"], name="we_rss_memb_tenant__bf5f23_idx"),
            models.Index(fields=["tenant", "tag"], name="we_rss_memb_tenant__7ca45b_idx"),
            models.Index(fields=["tenant", "seo_keyword"], name="we_rss_memb_tenant__c97fb7_idx"),
        ]


class WechatSyncTask(BaseModel):
    class TaskType(models.TextChoices):
        CREDENTIAL_LOGIN = "credential_login", "Credential Login"
        FEED_SYNC = "feed_sync", "Feed Sync"
        FEED_SYNC_RUN = "feed_sync_run", "Feed Sync Run"
        FEED_SYNC_BATCH = "feed_sync_batch", "Feed Sync Batch"
        FEED_CONTENT_REFRESH = "feed_content_refresh", "Feed Content Refresh"
        ARTICLE_REFRESH = "article_refresh", "Article Refresh"
        ARTICLE_IMPORT = "article_import", "Article Import"
        ARTICLE_STATS_REFRESH = "article_stats_refresh", "Article Stats Refresh"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        PARTIAL_SUCCESS = "partial_success", "Partial Success"
        TIMED_OUT = "timed_out", "Timed Out"
        FAILED = "failed", "Failed"

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
    class Meta:
        db_table = "we_rss_wechat_sync_task"
        ordering = ["-created_at"]
