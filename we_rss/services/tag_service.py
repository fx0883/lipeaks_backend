from django.db import IntegrityError
from django.db.models import Count
from rest_framework.exceptions import ValidationError

from we_rss.models import (
    MemberArticleTagRelation,
    MemberFeedSubscription,
    MemberFeedTagRelation,
    MemberTag,
)


class TagService:
    @staticmethod
    def parse_tag_ids(raw_value):
        if raw_value is None:
            return []

        tag_ids = []
        seen_ids = set()
        for token in str(raw_value).split(","):
            token = token.strip()
            if not token:
                continue
            try:
                tag_id = int(token)
            except (TypeError, ValueError) as exc:
                raise ValidationError({"tag_ids": [f"Invalid tag id: {token}"]}) from exc
            if tag_id not in seen_ids:
                seen_ids.add(tag_id)
                tag_ids.append(tag_id)
        return tag_ids

    @staticmethod
    def list_member_tags(*, tenant, member):
        return (
            MemberTag.objects.filter(tenant=tenant, member=member)
            .annotate(
                feed_count=Count("feed_relations", distinct=True),
                article_count=Count("article_relations", distinct=True),
            )
            .order_by("-is_pinned", "sort_order", "-id")
        )

    @staticmethod
    def get_member_tag(*, tenant, member, tag_id):
        return TagService.list_member_tags(tenant=tenant, member=member).filter(pk=tag_id).first()

    @staticmethod
    def _normalize_name(name):
        return str(name or "").strip()

    @staticmethod
    def create_member_tag(*, tenant, member, data):
        payload = {
            "name": TagService._normalize_name(data.get("name")),
            "color": data.get("color", ""),
            "description": data.get("description", ""),
            "sort_order": data.get("sort_order", 0),
            "is_pinned": data.get("is_pinned", False),
        }
        try:
            tag = MemberTag.objects.create(
                tenant=tenant,
                member=member,
                **payload,
            )
        except IntegrityError as exc:
            raise ValidationError({"name": ["You already have a tag with this name."]}) from exc
        return TagService.get_member_tag(tenant=tenant, member=member, tag_id=tag.id)

    @staticmethod
    def update_member_tag(*, tag, data):
        tag.name = TagService._normalize_name(data.get("name", tag.name))
        tag.color = data.get("color", tag.color)
        tag.description = data.get("description", tag.description)
        tag.sort_order = data.get("sort_order", tag.sort_order)
        tag.is_pinned = data.get("is_pinned", tag.is_pinned)
        try:
            tag.save()
        except IntegrityError as exc:
            raise ValidationError({"name": ["You already have a tag with this name."]}) from exc
        return TagService.get_member_tag(tenant=tag.tenant, member=tag.member, tag_id=tag.id)

    @staticmethod
    def delete_member_tag(*, tag):
        tag.delete()

    @staticmethod
    def get_member_tags_for_ids(*, tenant, member, tag_ids):
        unique_tag_ids = []
        seen_ids = set()
        for tag_id in tag_ids:
            if tag_id not in seen_ids:
                seen_ids.add(tag_id)
                unique_tag_ids.append(tag_id)

        tags = list(
            MemberTag.objects.filter(
                tenant=tenant,
                member=member,
                id__in=unique_tag_ids,
            )
        )
        if len(tags) != len(unique_tag_ids):
            raise ValidationError({"tag_ids": ["One or more tags do not belong to the current member."]})

        tag_map = {tag.id: tag for tag in tags}
        return [tag_map[tag_id] for tag_id in unique_tag_ids]

    @staticmethod
    def list_feed_tags(*, feed, member):
        return (
            TagService.list_member_tags(tenant=feed.tenant, member=member)
            .filter(feed_relations__feed=feed, feed_relations__member=member)
            .distinct()
        )

    @staticmethod
    def attach_tags_to_feed(*, feed, member, tag_ids):
        has_subscription = MemberFeedSubscription.objects.filter(
            tenant=feed.tenant,
            member=member,
            feed=feed,
        ).exists()
        if not has_subscription:
            raise ValidationError({"tag_ids": ["The current member must subscribe to this feed before tagging it."]})

        tags = TagService.get_member_tags_for_ids(tenant=feed.tenant, member=member, tag_ids=tag_ids)
        if tags:
            MemberFeedTagRelation.objects.bulk_create(
                [
                    MemberFeedTagRelation(
                        tenant=feed.tenant,
                        member=member,
                        tag=tag,
                        feed=feed,
                    )
                    for tag in tags
                ],
                ignore_conflicts=True,
            )
        return TagService.list_feed_tags(feed=feed, member=member)

    @staticmethod
    def detach_tags_from_feed(*, feed, member, tag_ids):
        TagService.get_member_tags_for_ids(tenant=feed.tenant, member=member, tag_ids=tag_ids)
        MemberFeedTagRelation.objects.filter(
            tenant=feed.tenant,
            member=member,
            feed=feed,
            tag_id__in=tag_ids,
        ).delete()
        return TagService.list_feed_tags(feed=feed, member=member)

    @staticmethod
    def list_article_tags(*, article, member):
        return (
            TagService.list_member_tags(tenant=article.tenant, member=member)
            .filter(article_relations__article=article, article_relations__member=member)
            .distinct()
        )

    @staticmethod
    def attach_tags_to_article(*, article, member, tag_ids):
        tags = TagService.get_member_tags_for_ids(tenant=article.tenant, member=member, tag_ids=tag_ids)
        if tags:
            MemberArticleTagRelation.objects.bulk_create(
                [
                    MemberArticleTagRelation(
                        tenant=article.tenant,
                        member=member,
                        tag=tag,
                        article=article,
                    )
                    for tag in tags
                ],
                ignore_conflicts=True,
            )
        return TagService.list_article_tags(article=article, member=member)

    @staticmethod
    def detach_tags_from_article(*, article, member, tag_ids):
        TagService.get_member_tags_for_ids(tenant=article.tenant, member=member, tag_ids=tag_ids)
        MemberArticleTagRelation.objects.filter(
            tenant=article.tenant,
            member=member,
            article=article,
            tag_id__in=tag_ids,
        ).delete()
        return TagService.list_article_tags(article=article, member=member)

    @staticmethod
    def filter_feed_queryset_by_tag_ids(*, queryset, tenant, member, tag_ids):
        if not tag_ids:
            return queryset

        matching_feed_ids = (
            MemberFeedTagRelation.objects.filter(
                tenant=tenant,
                member=member,
                tag_id__in=tag_ids,
            )
            .values("feed_id")
            .annotate(tag_count=Count("tag_id", distinct=True))
            .filter(tag_count=len(tag_ids))
            .values("feed_id")
        )
        return queryset.filter(id__in=matching_feed_ids)

    @staticmethod
    def filter_article_queryset_by_tag_ids(*, queryset, tenant, member, tag_ids):
        if not tag_ids:
            return queryset

        matching_article_ids = (
            MemberArticleTagRelation.objects.filter(
                tenant=tenant,
                member=member,
                tag_id__in=tag_ids,
            )
            .values("article_id")
            .annotate(tag_count=Count("tag_id", distinct=True))
            .filter(tag_count=len(tag_ids))
            .values("article_id")
        )
        return queryset.filter(id__in=matching_article_ids)
