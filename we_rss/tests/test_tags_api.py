from django.test import TestCase
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import MemberFeedSubscription, WechatArticle, WechatFeed
from we_rss.serializers import MemberTagWriteSerializer


class MemberTagSerializerTests(TestCase):
    def test_tag_name_is_trimmed(self):
        serializer = MemberTagWriteSerializer(data={"name": "  AI  "})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name"], "AI")

    def test_blank_tag_name_is_rejected(self):
        serializer = MemberTagWriteSerializer(data={"name": "   "})

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)


class WeRssTagApiTestCase(APITestCase):
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
        self.feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Tenant Feed",
            source_id="feed-1",
            created_by=self.member,
            updated_by=self.member,
        )
        self.article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )

    def create_tag(self, name, **extra):
        payload = {"name": name, **extra}
        response = self.client.post("/api/v1/we-rss/tags/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        return response.data["data"]

    def create_other_member_tag(self, name):
        other_token = generate_jwt_token(self.other_member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {other_token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        response = self.client.post("/api/v1/we-rss/tags/", {"name": name}, format="json")
        self.assertEqual(response.status_code, 201)
        tag = response.data["data"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        return tag


class MemberTagApiTests(WeRssTagApiTestCase):
    def test_member_can_create_list_update_and_delete_private_tags(self):
        create_response = self.client.post(
            "/api/v1/we-rss/tags/",
            {
                "name": "AI",
                "color": "#008000",
                "description": "Interesting reads",
                "sort_order": 10,
                "is_pinned": True,
            },
            format="json",
        )
        tag_id = create_response.data["data"]["id"]

        list_response = self.client.get("/api/v1/we-rss/tags/")
        detail_response = self.client.get(f"/api/v1/we-rss/tags/{tag_id}/")
        update_response = self.client.put(
            f"/api/v1/we-rss/tags/{tag_id}/",
            {
                "name": "AI Updated",
                "color": "#00AA00",
                "description": "Updated description",
                "sort_order": 5,
                "is_pinned": False,
            },
            format="json",
        )
        delete_response = self.client.delete(f"/api/v1/we-rss/tags/{tag_id}/")
        after_delete_response = self.client.get("/api/v1/we-rss/tags/")

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(list_response.data["data"][0]["name"], "AI")
        self.assertEqual(list_response.data["data"][0]["feed_count"], 0)
        self.assertEqual(list_response.data["data"][0]["article_count"], 0)
        self.assertEqual(detail_response.data["data"]["name"], "AI")
        self.assertEqual(update_response.data["data"]["name"], "AI Updated")
        self.assertEqual(after_delete_response.data["data"], [])

    def test_member_cannot_read_other_members_tags(self):
        other_member_tag = self.create_other_member_tag("Private Tag")

        response = self.client.get("/api/v1/we-rss/tags/")
        detail_response = self.client.get(f"/api/v1/we-rss/tags/{other_member_tag['id']}/")

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["data"]]
        self.assertNotIn(other_member_tag["id"], returned_ids)
        self.assertEqual(detail_response.status_code, 404)

    def test_member_tag_name_is_case_insensitive_unique(self):
        first_response = self.client.post("/api/v1/we-rss/tags/", {"name": "AI"}, format="json")
        second_response = self.client.post("/api/v1/we-rss/tags/", {"name": "ai"}, format="json")

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 400)
        self.assertIn("name", second_response.data["data"])


class FeedTagApiTests(WeRssTagApiTestCase):
    def test_member_can_attach_list_and_detach_multiple_tags_on_subscribed_feed(self):
        tag_one = self.create_tag("AI")
        tag_two = self.create_tag("Digest")

        attach_response = self.client.post(
            f"/api/v1/we-rss/feeds/{self.feed.id}/tags/attach/",
            {"tag_ids": [tag_one["id"], tag_two["id"]]},
            format="json",
        )
        list_response = self.client.get(f"/api/v1/we-rss/feeds/{self.feed.id}/tags/")
        detach_response = self.client.post(
            f"/api/v1/we-rss/feeds/{self.feed.id}/tags/detach/",
            {"tag_ids": [tag_two["id"]]},
            format="json",
        )

        self.assertEqual(attach_response.status_code, 200)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detach_response.status_code, 200)
        self.assertEqual(
            {item["id"] for item in attach_response.data["data"]},
            {tag_one["id"], tag_two["id"]},
        )
        self.assertEqual(
            {item["id"] for item in list_response.data["data"]},
            {tag_one["id"], tag_two["id"]},
        )
        self.assertEqual([item["id"] for item in detach_response.data["data"]], [tag_one["id"]])

    def test_member_cannot_attach_tag_to_unsubscribed_feed(self):
        self.client.delete(f"/api/v1/we-rss/feeds/{self.feed.id}/subscribe/")
        tag = self.create_tag("AI")

        response = self.client.post(
            f"/api/v1/we-rss/feeds/{self.feed.id}/tags/attach/",
            {"tag_ids": [tag["id"]]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)


class ArticleTagApiTests(WeRssTagApiTestCase):
    def test_member_can_attach_list_and_detach_multiple_tags_on_article_without_subscription(self):
        other_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Unsubscribed Feed",
            source_id="feed-2",
            created_by=self.member,
            updated_by=self.member,
        )
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=other_feed,
            source_id="article-2",
            title="Detached Subscription Article",
        )
        tag_one = self.create_tag("Read Soon")
        tag_two = self.create_tag("Deep Dive")

        attach_response = self.client.post(
            f"/api/v1/we-rss/articles/{article.id}/tags/attach/",
            {"tag_ids": [tag_one["id"], tag_two["id"]]},
            format="json",
        )
        list_response = self.client.get(f"/api/v1/we-rss/articles/{article.id}/tags/")
        detach_response = self.client.post(
            f"/api/v1/we-rss/articles/{article.id}/tags/detach/",
            {"tag_ids": [tag_two["id"]]},
            format="json",
        )

        self.assertEqual(attach_response.status_code, 200)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detach_response.status_code, 200)
        self.assertEqual(
            {item["id"] for item in attach_response.data["data"]},
            {tag_one["id"], tag_two["id"]},
        )
        self.assertEqual(
            {item["id"] for item in list_response.data["data"]},
            {tag_one["id"], tag_two["id"]},
        )
        self.assertEqual([item["id"] for item in detach_response.data["data"]], [tag_one["id"]])

    def test_member_cannot_attach_other_members_tag_to_article(self):
        other_member_tag = self.create_other_member_tag("Other Member Tag")

        response = self.client.post(
            f"/api/v1/we-rss/articles/{self.article.id}/tags/attach/",
            {"tag_ids": [other_member_tag["id"]]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
