from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from we_rss.models import (
    MemberSeoKeyword,
    MemberTag,
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
    is_subscribed = serializers.BooleanField(read_only=True, default=False)

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
            "is_subscribed",
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


class FeedSubscriptionWriteSerializer(serializers.Serializer):
    source_id = serializers.CharField(required=False, allow_blank=True, default="")
    faker_id = serializers.CharField(required=False, allow_blank=True, default="")
    biz = serializers.CharField(required=False, allow_blank=True, default="")
    mp_name = serializers.CharField()
    mp_cover = serializers.CharField(required=False, allow_blank=True, default="")
    mp_intro = serializers.CharField(required=False, allow_blank=True, default="")


class FeedArticleClearResponseSerializer(serializers.Serializer):
    feed_id = serializers.IntegerField()
    deleted_count = serializers.IntegerField()


class FeedSyncRequestSerializer(serializers.Serializer):
    SYNC_SCOPE_FULL = "full"
    SYNC_SCOPE_LATEST = "latest"
    SYNC_SCOPE_WINDOW = "window"
    SYNC_SCOPE_CHOICES = (
        (SYNC_SCOPE_FULL, "Full"),
        (SYNC_SCOPE_LATEST, "Latest"),
        (SYNC_SCOPE_WINDOW, "Window"),
    )

    sync_scope = serializers.ChoiceField(choices=SYNC_SCOPE_CHOICES, required=False, default=SYNC_SCOPE_FULL)
    window_days = serializers.IntegerField(required=False, min_value=1, max_value=180)
    refresh_markdown = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        sync_scope = attrs.get("sync_scope", self.SYNC_SCOPE_FULL)
        window_days = attrs.get("window_days")

        if sync_scope == self.SYNC_SCOPE_WINDOW:
            if window_days is None:
                raise serializers.ValidationError({"window_days": ["This field is required for window sync."]})
            return attrs

        if window_days is not None:
            raise serializers.ValidationError({"window_days": ["This field is only allowed when sync_scope=window."]})
        return attrs


class FeedSyncBatchRequestSerializer(serializers.Serializer):
    SYNC_SCOPE_FULL = FeedSyncRequestSerializer.SYNC_SCOPE_FULL
    SYNC_SCOPE_LATEST = FeedSyncRequestSerializer.SYNC_SCOPE_LATEST
    SYNC_SCOPE_WINDOW = FeedSyncRequestSerializer.SYNC_SCOPE_WINDOW
    SYNC_SCOPE_CHOICES = FeedSyncRequestSerializer.SYNC_SCOPE_CHOICES

    feed_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False,
        max_length=200,
    )
    sync_scope = serializers.ChoiceField(choices=SYNC_SCOPE_CHOICES, required=True)
    window_days = serializers.IntegerField(required=False, min_value=1, max_value=180)
    refresh_markdown = serializers.BooleanField(required=False, default=False)
    continue_on_error = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        sync_scope = attrs.get("sync_scope")
        window_days = attrs.get("window_days")

        if sync_scope == self.SYNC_SCOPE_WINDOW and window_days is None:
            raise serializers.ValidationError({"window_days": ["This field is required for window sync."]})

        return attrs


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
    is_favorite = serializers.BooleanField(read_only=True, default=False)
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


class WechatArticleSearchQuerySerializer(serializers.Serializer):
    query = serializers.CharField()
    limit = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)

    def validate_query(self, value):
        value = str(value or "").strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value


class WechatArticleSearchItemSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    url = serializers.URLField()
    summary = serializers.CharField(required=False, allow_blank=True)
    datetime = serializers.CharField(required=False, allow_blank=True)
    date_text = serializers.CharField(required=False, allow_blank=True)
    date_description = serializers.CharField(required=False, allow_blank=True)
    source = serializers.CharField(required=False, allow_blank=True)


class WechatArticleSearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    total = serializers.IntegerField(min_value=0)
    items = WechatArticleSearchItemSerializer(many=True)


class MarkdownFormatRequestSerializer(serializers.Serializer):
    content = serializers.CharField()
    mode = serializers.ChoiceField(choices=(("gentle", "Gentle"),), required=False, default="gentle")

    def validate_content(self, value):
        value = str(value or "").strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value


class MarkdownFormatResponseSerializer(serializers.Serializer):
    formatted_markdown = serializers.CharField()
    mode = serializers.ChoiceField(choices=(("gentle", "Gentle"),))
    executor = serializers.CharField()


class ArticleImportSerializer(serializers.Serializer):
    url = serializers.URLField(
        help_text=(
            "Public WeChat article URL. The backend normalizes it before deduplicating and persisting, "
            "and removes transient query parameters such as `token`."
        )
    )


class ArticleStatsRefreshByUrlSerializer(serializers.Serializer):
    url = serializers.URLField(
        help_text=(
            "Public WeChat article URL for an existing tenant article. The backend normalizes it before "
            "matching and refreshing stats."
        )
    )


class ArticleStatsBatchRefreshSerializer(serializers.Serializer):
    article_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False,
        help_text="Refresh the selected tenant article IDs asynchronously in the same order sent by the frontend.",
    )
    member_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Refresh all articles under feeds subscribed by this member within the current tenant.",
    )
    feed_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Refresh all articles under one feed within the current tenant.",
    )

    def validate(self, attrs):
        selectors = [
            bool(attrs.get("article_ids")),
            attrs.get("feed_id") is not None,
            attrs.get("member_id") is not None,
        ]
        if sum(selectors) != 1:
            raise serializers.ValidationError("Provide exactly one of article_ids, feed_id, or member_id.")
        return attrs


class ArticleExportSerializer(serializers.Serializer):
    article_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False,
        help_text="Explicit article IDs to export. When present, this selector takes priority over the others.",
    )
    member_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Export all articles under feeds subscribed by this member within the current tenant.",
    )
    feed_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Export all articles under one feed within the current tenant.",
    )

    def validate(self, attrs):
        article_ids = attrs.get("article_ids") or []
        member_id = attrs.get("member_id")
        feed_id = attrs.get("feed_id")

        if article_ids:
            return attrs

        selected_modes = [value for value in (member_id, feed_id) if value is not None]
        if not selected_modes:
            raise serializers.ValidationError("Provide article_ids, member_id, or feed_id.")
        if len(selected_modes) > 1:
            raise serializers.ValidationError("Provide only one of member_id or feed_id when article_ids is absent.")
        return attrs


class ArticleBatchDeleteSerializer(serializers.Serializer):
    article_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="Delete the selected tenant article IDs in one request.",
    )


class ArticleBatchDeleteResponseSerializer(serializers.Serializer):
    deleted_count = serializers.IntegerField()
    article_ids = serializers.ListField(child=serializers.IntegerField(min_value=1))


class ArticleFavoriteUpdateSerializer(serializers.Serializer):
    is_favorite = serializers.BooleanField()


class MemberTagSerializer(serializers.ModelSerializer):
    feed_count = serializers.IntegerField(read_only=True)
    article_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = MemberTag
        fields = [
            "id",
            "name",
            "color",
            "description",
            "sort_order",
            "is_pinned",
            "feed_count",
            "article_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MemberTagWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberTag
        fields = ["name", "color", "description", "sort_order", "is_pinned"]

    def validate_name(self, value):
        value = str(value or "").strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value


class MemberTagSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberTag
        fields = ["id", "name", "color", "sort_order"]
        read_only_fields = fields


class SeoKeywordSerializer(serializers.ModelSerializer):
    member_id = serializers.IntegerField(read_only=True)
    tag_ids = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = MemberSeoKeyword
        fields = [
            "id",
            "member_id",
            "keyword",
            "search_index",
            "tag_ids",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.ListField(child=serializers.IntegerField(min_value=1)))
    def get_tag_ids(self, obj):
        relations = getattr(obj, "_prefetched_objects_cache", {}).get("keyword_tag_relations")
        if relations is None:
            relations = obj.keyword_tag_relations.select_related("tag").all()
        return [relation.tag_id for relation in relations]

    @extend_schema_field(MemberTagSummarySerializer(many=True))
    def get_tags(self, obj):
        relations = getattr(obj, "_prefetched_objects_cache", {}).get("keyword_tag_relations")
        if relations is None:
            relations = obj.keyword_tag_relations.select_related("tag").all()
        tags = [relation.tag for relation in relations]
        return MemberTagSummarySerializer(tags, many=True).data


class SeoKeywordWriteSerializer(serializers.Serializer):
    member_id = serializers.IntegerField(min_value=1)
    keyword = serializers.CharField()
    search_index = serializers.IntegerField(min_value=0)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        required=False,
        default=list,
    )

    def validate_keyword(self, value):
        value = str(value or "").strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value


class SeoKeywordDeleteSerializer(serializers.Serializer):
    member_id = serializers.IntegerField(min_value=1)


class SeoKeywordQuerySerializer(serializers.Serializer):
    member_id = serializers.IntegerField(min_value=1)
    search = serializers.CharField(required=False, allow_blank=True, default="")
    tag_id = serializers.IntegerField(required=False, min_value=1)


class TagRelationWriteSerializer(serializers.Serializer):
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )
