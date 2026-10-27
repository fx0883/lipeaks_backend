from django.db.models import BooleanField, Exists, OuterRef, Value

from users.models import Member
from we_rss.models import MemberArticleState, MemberFeedSubscription, WechatArticle


class ArticleVisibilityService:
    @staticmethod
    def _annotate_member_state(*, tenant, member, queryset):
        if member is None or not isinstance(member, Member):
            return queryset.annotate(
                is_hidden=Value(False, output_field=BooleanField()),
                is_favorite=Value(False, output_field=BooleanField()),
            )
        hidden_state_exists = MemberArticleState.objects.filter(
            tenant=tenant,
            member=member,
            article_id=OuterRef("pk"),
            is_hidden=True,
        )
        favorite_state_exists = MemberArticleState.objects.filter(
            tenant=tenant,
            member=member,
            article_id=OuterRef("pk"),
            is_favorite=True,
        )
        return queryset.annotate(
            is_hidden=Exists(hidden_state_exists),
            is_favorite=Exists(favorite_state_exists),
        )

    @staticmethod
    def get_tenant_visible_article_queryset(*, tenant, member, queryset=None):
        if queryset is None:
            queryset = WechatArticle.objects.all()

        qs = queryset.filter(tenant=tenant) if tenant else queryset
        return (
            ArticleVisibilityService._annotate_member_state(
                tenant=tenant,
                member=member,
                queryset=qs,
            )
            .filter(is_hidden=False)
        )

    @staticmethod
    def get_visible_article_queryset(*, tenant, member, queryset=None):
        if queryset is None:
            queryset = WechatArticle.objects.all()
        if member is None or not isinstance(member, Member):
            qs = queryset.filter(tenant=tenant) if tenant else queryset
            return (
                ArticleVisibilityService._annotate_member_state(
                    tenant=tenant,
                    member=member,
                    queryset=qs,
                )
                .filter(is_hidden=False)
            )

        subscribed_feed_ids = MemberFeedSubscription.objects.filter(
            tenant=tenant,
            member=member,
        ).values("feed_id")
        return (
            ArticleVisibilityService._annotate_member_state(
                tenant=tenant,
                member=member,
                queryset=queryset.filter(tenant=tenant, feed_id__in=subscribed_feed_ids),
            )
            .filter(is_hidden=False)
        )

    @staticmethod
    def get_visible_article(*, tenant, member, article_id, queryset=None):
        return ArticleVisibilityService.get_visible_article_queryset(
            tenant=tenant,
            member=member,
            queryset=queryset,
        ).filter(pk=article_id).first()

    @staticmethod
    def get_tenant_visible_article(*, tenant, member, article_id, queryset=None):
        return ArticleVisibilityService.get_tenant_visible_article_queryset(
            tenant=tenant,
            member=member,
            queryset=queryset,
        ).filter(pk=article_id).first()
