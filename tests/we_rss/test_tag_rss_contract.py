from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import MemberFeedTagRelation, MemberTag, WechatArticle, WechatFeed


class WeRssTagRssContractTests(APITestCase):
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
        self.tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="AI",
        )
        self.feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Tagged Feed",
            source_id="feed-tagged",
            created_by=self.member,
            updated_by=self.member,
        )
        self.other_feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Other Feed",
            source_id="feed-other",
            created_by=self.member,
            updated_by=self.member,
        )
        self.tagged_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-tagged",
            title="Tagged Article",
            description="Tagged description",
            url="https://mp.weixin.qq.com/s/tagged",
        )
        self.other_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.other_feed,
            source_id="article-other",
            title="Other Article",
            description="Other description",
            url="https://mp.weixin.qq.com/s/other",
        )

    def test_tag_rss_uses_current_member_feed_tag_relations(self):
        other_member_tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.other_member,
            name="Other member tag",
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag,
            feed=self.feed,
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.other_member,
            tag=other_member_tag,
            feed=self.other_feed,
        )

        response = self.client.get(f"/api/v1/we-rss/rss/tags/{self.tag.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        content = response.content.decode("utf-8")
        self.assertIn("Tagged Article", content)
        self.assertNotIn("Other Article", content)
        self.assertIn("AI", content)

    def test_tag_rss_returns_empty_channel_when_tag_has_no_related_feeds(self):
        response = self.client.get(f"/api/v1/we-rss/rss/tags/{self.tag.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        content = response.content.decode("utf-8")
        self.assertIn("<channel>", content)
        self.assertNotIn("Tagged Article", content)
