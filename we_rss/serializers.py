from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from we_rss.models import (
    WechatArticle,
    WechatCredential,
    WechatCredentialLoginSession,
    WechatFeed,
    WechatSyncTask,
)
from we_rss.services.credential_service import CredentialService


class WechatCredentialListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WechatCredential
        fields = [
            "id",
            "name",
            "status",
            "expires_at",
            "last_login_at",
            "last_check_at",
            "last_error",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class WechatCredentialDetailSerializer(WechatCredentialListSerializer):
    pass


class CredentialUpdateSerializer(serializers.ModelSerializer):
    token = serializers.CharField(required=False, write_only=True)
    cookie = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = WechatCredential
        fields = ["name", "token", "cookie"]

    def validate_token(self, value):
        raise serializers.ValidationError("Manual token updates are not supported.")

    def validate_cookie(self, value):
        raise serializers.ValidationError("Manual cookie updates are not supported.")


class CredentialLoginSessionCreateSerializer(serializers.Serializer):
    pass


class CredentialLoginSessionDetailSerializer(serializers.ModelSerializer):
    credential_id = serializers.IntegerField(read_only=True)
    task_id = serializers.SerializerMethodField()

    class Meta:
        model = WechatCredentialLoginSession
        fields = [
            "session_id",
            "status",
            "qr_code_url",
            "qr_code_image",
            "scan_status",
            "error_message",
            "expired_at",
            "credential_id",
            "task_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_task_id(self, obj):
        task = CredentialService.get_login_task(login_session=obj)
        return task.id if task else None


class CredentialCheckResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    status = serializers.CharField()
    message = serializers.CharField(required=False, allow_blank=True)


class WechatFeedSerializer(serializers.ModelSerializer):
    credential_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = WechatFeed
        fields = [
            "id",
            "credential_id",
            "source_id",
            "faker_id",
            "biz",
            "mp_name",
            "mp_cover",
            "mp_intro",
            "status",
            "sync_time",
            "update_time",
            "last_synced_at",
            "is_featured",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "sync_time", "update_time", "last_synced_at", "created_at", "updated_at"]


class FeedWriteSerializer(serializers.Serializer):
    credential_id = serializers.IntegerField(required=False, allow_null=True)
    source_id = serializers.CharField(required=False, allow_blank=True, default="")
    faker_id = serializers.CharField(required=False, allow_blank=True, default="")
    biz = serializers.CharField(required=False, allow_blank=True, default="")
    mp_name = serializers.CharField()
    mp_cover = serializers.CharField(required=False, allow_blank=True, default="")
    mp_intro = serializers.CharField(required=False, allow_blank=True, default="")
    status = serializers.CharField(required=False, default="active")
    is_featured = serializers.BooleanField(required=False, default=False)


class FeedSearchResultSerializer(serializers.Serializer):
    source_id = serializers.CharField(required=False, allow_blank=True)
    faker_id = serializers.CharField(required=False, allow_blank=True)
    biz = serializers.CharField(required=False, allow_blank=True)
    mp_name = serializers.CharField()
    mp_cover = serializers.CharField(required=False, allow_blank=True)
    mp_intro = serializers.CharField(required=False, allow_blank=True)


class FeedArticleClearResponseSerializer(serializers.Serializer):
    feed_id = serializers.IntegerField()
    deleted_count = serializers.IntegerField()


class WechatSyncTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WechatSyncTask
        fields = [
            "id",
            "task_type",
            "status",
            "task_key",
            "target_type",
            "target_id",
            "message",
            "request_payload",
            "result_payload",
            "celery_task_id",
            "started_at",
            "finished_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class WechatArticleSerializer(serializers.ModelSerializer):
    feed_id = serializers.IntegerField(read_only=True)
    url = serializers.URLField(
        read_only=True,
        help_text="Stable public WeChat article URL. Crawl-time parameters such as `token` are removed.",
    )

    class Meta:
        model = WechatArticle
        fields = [
            "id",
            "feed_id",
            "source_id",
            "article_type",
            "title",
            "description",
            "content",
            "url",
            "pic_url",
            "publish_time",
            "status",
            "is_read",
            "is_favorite",
            "last_refreshed_at",
            "read_num",
            "like_num",
            "old_like_num",
            "share_num",
            "collect_num",
            "comment_count",
            "comment_reply_count",
            "comment_total_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ArticleImportSerializer(serializers.Serializer):
    url = serializers.URLField(
        help_text=(
            "Public WeChat article URL. The backend normalizes it before deduplicating and persisting, "
            "and removes transient query parameters such as `token`."
        )
    )


class ArticleReadUpdateSerializer(serializers.Serializer):
    is_read = serializers.BooleanField()


class ArticleFavoriteUpdateSerializer(serializers.Serializer):
    is_favorite = serializers.BooleanField()
