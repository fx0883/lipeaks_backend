from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from users.models import Member
from we_rss.models import MemberSeoKeyword, MemberTag, MemberTagSeoKeywordRelation


class SeoKeywordService:
    @staticmethod
    def _resolve_member(*, tenant, actor, member_id):
        member = Member.objects.filter(tenant=tenant, id=member_id).first()
        if member is None:
            raise ValidationError({"member_id": ["Member not found in current tenant."]})
        if actor.id != member.id:
            raise PermissionDenied("You do not have permission to access this member scope.")
        return member

    @staticmethod
    def _normalize_keyword(keyword):
        return str(keyword or "").strip()

    @staticmethod
    def _base_queryset(*, tenant, member):
        return (
            MemberSeoKeyword.objects.filter(tenant=tenant, member=member)
            .prefetch_related(
                Prefetch(
                    "keyword_tag_relations",
                    queryset=MemberTagSeoKeywordRelation.objects.select_related("tag").order_by("tag_id"),
                )
            )
            .order_by("-updated_at", "-id")
        )

    @staticmethod
    def _dedupe_ids(raw_ids):
        ordered_ids = []
        seen_ids = set()
        for raw_id in raw_ids or []:
            if raw_id in seen_ids:
                continue
            seen_ids.add(raw_id)
            ordered_ids.append(raw_id)
        return ordered_ids

    @classmethod
    def _get_tags_for_ids(cls, *, tenant, member, tag_ids):
        unique_tag_ids = cls._dedupe_ids(tag_ids)
        if not unique_tag_ids:
            return []

        tags = list(
            MemberTag.objects.filter(
                tenant=tenant,
                member=member,
                id__in=unique_tag_ids,
            )
        )
        if len(tags) != len(unique_tag_ids):
            raise ValidationError({"tag_ids": ["One or more tags do not belong to the requested member."]})

        tag_map = {tag.id: tag for tag in tags}
        return [tag_map[tag_id] for tag_id in unique_tag_ids]

    @classmethod
    def list_keywords(cls, *, tenant, actor, member_id, search=None, tag_id=None):
        member = cls._resolve_member(tenant=tenant, actor=actor, member_id=member_id)
        queryset = cls._base_queryset(tenant=tenant, member=member)
        search = str(search or "").strip()
        if search:
            queryset = queryset.filter(keyword__icontains=search)
        if tag_id is not None:
            if not MemberTag.objects.filter(tenant=tenant, member=member, id=tag_id).exists():
                raise ValidationError({"tag_id": ["Tag not found in requested member scope."]})
            queryset = queryset.filter(
                keyword_tag_relations__tag_id=tag_id,
                keyword_tag_relations__member=member,
            ).distinct()
        return queryset

    @classmethod
    def get_keyword(cls, *, tenant, actor, member_id, keyword_id):
        member = cls._resolve_member(tenant=tenant, actor=actor, member_id=member_id)
        keyword = cls._base_queryset(tenant=tenant, member=member).filter(id=keyword_id).first()
        if keyword is None:
            raise NotFound("SEO keyword not found.")
        return keyword

    @classmethod
    def _sync_tag_relations(cls, *, tenant, member, seo_keyword, tag_ids):
        tags = cls._get_tags_for_ids(tenant=tenant, member=member, tag_ids=tag_ids)
        MemberTagSeoKeywordRelation.objects.filter(
            tenant=tenant,
            member=member,
            seo_keyword=seo_keyword,
        ).delete()
        if tags:
            MemberTagSeoKeywordRelation.objects.bulk_create(
                [
                    MemberTagSeoKeywordRelation(
                        tenant=tenant,
                        member=member,
                        tag=tag,
                        seo_keyword=seo_keyword,
                    )
                    for tag in tags
                ]
            )

    @classmethod
    def create_keyword(cls, *, tenant, actor, member_id, keyword, search_index, tag_ids):
        member = cls._resolve_member(tenant=tenant, actor=actor, member_id=member_id)
        payload = {
            "keyword": cls._normalize_keyword(keyword),
            "search_index": search_index,
        }
        try:
            with transaction.atomic():
                seo_keyword = MemberSeoKeyword.objects.create(
                    tenant=tenant,
                    member=member,
                    **payload,
                )
                cls._sync_tag_relations(
                    tenant=tenant,
                    member=member,
                    seo_keyword=seo_keyword,
                    tag_ids=tag_ids,
                )
        except IntegrityError as exc:
            raise ValidationError({"keyword": ["You already have a SEO keyword with this name."]}) from exc
        return cls.get_keyword(
            tenant=tenant,
            actor=actor,
            member_id=member_id,
            keyword_id=seo_keyword.id,
        )

    @classmethod
    def update_keyword(cls, *, tenant, actor, member_id, keyword_id, keyword, search_index, tag_ids):
        seo_keyword = cls.get_keyword(
            tenant=tenant,
            actor=actor,
            member_id=member_id,
            keyword_id=keyword_id,
        )
        seo_keyword.keyword = cls._normalize_keyword(keyword)
        seo_keyword.search_index = search_index
        try:
            with transaction.atomic():
                seo_keyword.save()
                cls._sync_tag_relations(
                    tenant=tenant,
                    member=seo_keyword.member,
                    seo_keyword=seo_keyword,
                    tag_ids=tag_ids,
                )
        except IntegrityError as exc:
            raise ValidationError({"keyword": ["You already have a SEO keyword with this name."]}) from exc
        return cls.get_keyword(
            tenant=tenant,
            actor=actor,
            member_id=member_id,
            keyword_id=seo_keyword.id,
        )

    @classmethod
    def delete_keyword(cls, *, tenant, actor, member_id, keyword_id):
        seo_keyword = cls.get_keyword(
            tenant=tenant,
            actor=actor,
            member_id=member_id,
            keyword_id=keyword_id,
        )
        seo_keyword.delete()
