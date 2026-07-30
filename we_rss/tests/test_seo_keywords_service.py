from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError

from tenants.models import Tenant
from users.models import Member
from we_rss.models import MemberSeoKeyword, MemberTag, MemberTagSeoKeywordRelation
from we_rss.serializers import SeoKeywordWriteSerializer
from we_rss.services.seo_keyword_service import SeoKeywordService


class SeoKeywordWriteSerializerTests(TestCase):
    def test_keyword_is_trimmed(self):
        serializer = SeoKeywordWriteSerializer(
            data={"member_id": 1, "keyword": "  Weight Loss  ", "search_index": 12}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["keyword"], "Weight Loss")

    def test_member_id_is_required(self):
        serializer = SeoKeywordWriteSerializer(
            data={"keyword": "Weight Loss", "search_index": 12}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("member_id", serializer.errors)

    def test_negative_search_index_is_rejected(self):
        serializer = SeoKeywordWriteSerializer(
            data={"member_id": 1, "keyword": "Weight Loss", "search_index": -1}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("search_index", serializer.errors)


class SeoKeywordServiceTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )
        self.other_member = Member.objects.create(
            username="other_member",
            email="other-member@example.com",
            tenant=self.tenant,
        )
        self.tag_one = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Weight Loss",
        )
        self.tag_two = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Recipes",
        )
        self.other_member_tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.other_member,
            name="Other Member",
        )
        self.keyword = MemberSeoKeyword.objects.create(
            tenant=self.tenant,
            member=self.member,
            keyword="Weight Loss",
            search_index=120,
        )
        MemberTagSeoKeywordRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag_one,
            seo_keyword=self.keyword,
        )

    def test_create_keyword_with_multiple_tags(self):
        keyword = SeoKeywordService.create_keyword(
            tenant=self.tenant,
            actor=self.member,
            member_id=self.member.id,
            keyword="Healthy Recipes",
            search_index=140,
            tag_ids=[self.tag_one.id, self.tag_two.id],
        )

        self.assertEqual(keyword.keyword, "Healthy Recipes")
        self.assertEqual(keyword.search_index, 140)
        self.assertEqual(keyword.keyword_tag_relations.count(), 2)

    def test_update_replaces_existing_tag_relations(self):
        updated = SeoKeywordService.update_keyword(
            tenant=self.tenant,
            actor=self.member,
            member_id=self.member.id,
            keyword_id=self.keyword.id,
            keyword="Weight Loss Updated",
            search_index=180,
            tag_ids=[self.tag_two.id],
        )

        self.assertEqual(updated.keyword, "Weight Loss Updated")
        self.assertEqual(updated.search_index, 180)
        self.assertEqual(
            list(
                updated.keyword_tag_relations.order_by("tag_id").values_list(
                    "tag_id", flat=True
                )
            ),
            [self.tag_two.id],
        )

    def test_rejects_operating_on_another_member_scope(self):
        with self.assertRaises(PermissionDenied):
            SeoKeywordService.list_keywords(
                tenant=self.tenant,
                actor=self.member,
                member_id=self.other_member.id,
            )

    def test_rejects_tag_from_another_member(self):
        with self.assertRaises(ValidationError):
            SeoKeywordService.create_keyword(
                tenant=self.tenant,
                actor=self.member,
                member_id=self.member.id,
                keyword="Weight Loss Plans",
                search_index=120,
                tag_ids=[self.other_member_tag.id],
            )

    def test_filter_by_search_and_tag(self):
        second_keyword = MemberSeoKeyword.objects.create(
            tenant=self.tenant,
            member=self.member,
            keyword="Low Carb Recipes",
            search_index=90,
        )
        MemberTagSeoKeywordRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag_two,
            seo_keyword=second_keyword,
        )

        search_results = SeoKeywordService.list_keywords(
            tenant=self.tenant,
            actor=self.member,
            member_id=self.member.id,
            search="carb",
        )
        tag_results = SeoKeywordService.list_keywords(
            tenant=self.tenant,
            actor=self.member,
            member_id=self.member.id,
            tag_id=self.tag_one.id,
        )

        self.assertEqual(list(search_results.values_list("id", flat=True)), [second_keyword.id])
        self.assertEqual(list(tag_results.values_list("id", flat=True)), [self.keyword.id])
