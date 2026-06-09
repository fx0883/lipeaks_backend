from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import (
    MemberArticleState,
    MemberFeedSubscription,
    MemberFeedTagRelation,
    MemberTag,
    WechatArticle,
    WechatCredential,
    WechatFeed,
)


class RssApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.other_tenant = Tenant.objects.create(name="Tenant B", code="tenant_b")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )
        self.other_member = Member.objects.create(
            username="other_member",
            email="other-member@example.com",
            tenant=self.other_tenant,
        )
        self.credential = WechatCredential.objects.create(
            tenant=self.tenant,
            name="Default Credential",
            status="active",
            token="token-1",
            cookie="cookie-1",
            is_default=True,
            created_by=self.member,
            updated_by=self.member,
        )
        self.feed = WechatFeed.objects.create(
            tenant=self.tenant,
            credential=self.credential,
            mp_name="Tenant Feed",
            source_id="feed-1",
            created_by=self.member,
            updated_by=self.member,
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )
        self.article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
            content="<p>Tenant Content</p>",
            url="https://mp.weixin.qq.com/s/article-1",
        )
        other_feed = WechatFeed.objects.create(
            tenant=self.other_tenant,
            mp_name="Other Feed",
            source_id="feed-2",
            created_by=self.other_member,
            updated_by=self.other_member,
        )
        WechatArticle.objects.create(
            tenant=self.other_tenant,
            feed=other_feed,
            source_id="article-2",
            title="Other Article",
            content="<p>Other Content</p>",
        )

    def test_rss_requires_member_token(self):
        response = self.client.get("/api/v1/we-rss/rss/")

        self.assertEqual(response.status_code, 400)

    def test_authenticated_member_can_get_tenant_rss(self):
        token = generate_jwt_token(self.member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )

        response = self.client.get("/api/v1/we-rss/rss/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn("Tenant Article", response.content.decode("utf-8"))
        self.assertNotIn("Other Article", response.content.decode("utf-8"))

    def test_authenticated_member_can_get_feed_rss(self):
        token = generate_jwt_token(self.member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )

        response = self.client.get(f"/api/v1/we-rss/rss/{self.feed.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn("Tenant Feed", response.content.decode("utf-8"))

    def test_authenticated_member_can_get_tag_rss(self):
        token = generate_jwt_token(self.member)["access_token"]
        tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="AI",
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            feed=self.feed,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )

        response = self.client.get(f"/api/v1/we-rss/rss/tags/{tag.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        content = response.content.decode("utf-8")
        self.assertIn("AI We RSS", content)
        self.assertIn("Tenant Article", content)

    def test_authenticated_member_can_get_article_content(self):
        token = generate_jwt_token(self.member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )

        response = self.client.get(f"/api/v1/we-rss/rss/content/{self.article.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/markdown")
        self.assertIn("Tenant Content", response.content.decode("utf-8"))

    def test_hidden_article_is_excluded_from_rss(self):
        token = generate_jwt_token(self.member)["access_token"]
        MemberArticleState.objects.create(
            tenant=self.tenant,
            member=self.member,
            article=self.article,
            is_hidden=True,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )

        response = self.client.get("/api/v1/we-rss/rss/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Tenant Article", response.content.decode("utf-8"))
