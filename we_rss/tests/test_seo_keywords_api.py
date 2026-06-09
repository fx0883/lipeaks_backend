from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import MemberSeoKeyword, MemberTag, MemberTagSeoKeywordRelation


class SeoKeywordApiTestCase(APITestCase):
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
        self.token = generate_jwt_token(self.member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
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
            name="Other Member Tag",
        )


class SeoKeywordApiTests(SeoKeywordApiTestCase):
    def test_member_can_create_list_update_and_delete_keywords(self):
        create_response = self.client.post(
            "/api/v1/we-rss/seo-keywords/",
            {
                "member_id": self.member.id,
                "keyword": "Weight Loss",
                "search_index": 200,
                "tag_ids": [self.tag_one.id, self.tag_two.id],
            },
            format="json",
        )
        keyword_id = create_response.data["data"]["id"]

        list_response = self.client.get(
            f"/api/v1/we-rss/seo-keywords/?member_id={self.member.id}"
        )
        detail_response = self.client.get(
            f"/api/v1/we-rss/seo-keywords/{keyword_id}/?member_id={self.member.id}"
        )
        update_response = self.client.put(
            f"/api/v1/we-rss/seo-keywords/{keyword_id}/",
            {
                "member_id": self.member.id,
                "keyword": "Weight Loss Updated",
                "search_index": 300,
                "tag_ids": [self.tag_two.id],
            },
            format="json",
        )
        delete_response = self.client.delete(
            f"/api/v1/we-rss/seo-keywords/{keyword_id}/",
            {"member_id": self.member.id},
            format="json",
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(create_response.data["data"]["keyword"], "Weight Loss")
        self.assertEqual(create_response.data["data"]["tag_ids"], [self.tag_one.id, self.tag_two.id])
        self.assertEqual(list_response.data["data"][0]["id"], keyword_id)
        self.assertEqual(detail_response.data["data"]["id"], keyword_id)
        self.assertEqual(update_response.data["data"]["keyword"], "Weight Loss Updated")
        self.assertEqual(update_response.data["data"]["tag_ids"], [self.tag_two.id])

    def test_list_filters_by_search_and_tag(self):
        first_keyword = MemberSeoKeyword.objects.create(
            tenant=self.tenant,
            member=self.member,
            keyword="Weight Loss",
            search_index=100,
        )
        second_keyword = MemberSeoKeyword.objects.create(
            tenant=self.tenant,
            member=self.member,
            keyword="Low Carb Recipes",
            search_index=150,
        )
        MemberTagSeoKeywordRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag_one,
            seo_keyword=first_keyword,
        )
        MemberTagSeoKeywordRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag_two,
            seo_keyword=second_keyword,
        )

        search_response = self.client.get(
            f"/api/v1/we-rss/seo-keywords/?member_id={self.member.id}&search=carb"
        )
        tag_response = self.client.get(
            f"/api/v1/we-rss/seo-keywords/?member_id={self.member.id}&tag_id={self.tag_one.id}"
        )

        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(tag_response.status_code, 200)
        self.assertEqual([item["id"] for item in search_response.data["data"]], [second_keyword.id])
        self.assertEqual([item["id"] for item in tag_response.data["data"]], [first_keyword.id])


class SeoKeywordApiEdgeCaseTests(SeoKeywordApiTestCase):
    def test_create_rejects_duplicate_keyword_ignoring_case(self):
        self.client.post(
            "/api/v1/we-rss/seo-keywords/",
            {
                "member_id": self.member.id,
                "keyword": "Weight Loss",
                "search_index": 10,
            },
            format="json",
        )

        response = self.client.post(
            "/api/v1/we-rss/seo-keywords/",
            {
                "member_id": self.member.id,
                "keyword": "weight loss",
                "search_index": 20,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("keyword", response.data["data"])

    def test_request_rejects_other_member_scope(self):
        response = self.client.get(
            f"/api/v1/we-rss/seo-keywords/?member_id={self.other_member.id}"
        )

        self.assertEqual(response.status_code, 403)

    def test_keyword_can_exist_without_tags(self):
        response = self.client.post(
            "/api/v1/we-rss/seo-keywords/",
            {
                "member_id": self.member.id,
                "keyword": "Low Carb",
                "search_index": 55,
                "tag_ids": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["tag_ids"], [])

    def test_request_rejects_other_members_tag(self):
        response = self.client.post(
            "/api/v1/we-rss/seo-keywords/",
            {
                "member_id": self.member.id,
                "keyword": "Weight Loss Plans",
                "search_index": 44,
                "tag_ids": [self.other_member_tag.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("tag_ids", response.data["data"])
