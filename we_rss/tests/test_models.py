from django.test import TestCase

from common.models import BaseModel
from tenants.models import Tenant
from users.models import Member
from we_rss.models import (
    WechatArticle,
    WechatCredential,
    WechatCredentialLoginSession,
    WechatFeed,
    WechatSyncTask,
)


class WeRssModelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )

    def test_article_statistics_default_to_zero(self):
        article = WechatArticle()

        self.assertEqual(article.article_type, "news")
        self.assertEqual(article.read_num, 0)
        self.assertEqual(article.like_num, 0)
        self.assertEqual(article.old_like_num, 0)
        self.assertEqual(article.share_num, 0)
        self.assertEqual(article.collect_num, 0)
        self.assertEqual(article.comment_count, 0)
        self.assertEqual(article.comment_reply_count, 0)
        self.assertEqual(article.comment_total_count, 0)

    def test_all_we_rss_models_inherit_base_model(self):
        for model in (
            WechatCredential,
            WechatCredentialLoginSession,
            WechatFeed,
            WechatArticle,
            WechatSyncTask,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(issubclass(model, BaseModel))
                self.assertTrue(hasattr(model, "original_objects"))
                self.assertIsNotNone(model._meta.get_field("tenant"))
                self.assertIsNotNone(model._meta.get_field("created_at"))
                self.assertIsNotNone(model._meta.get_field("updated_at"))
                self.assertIsNotNone(model._meta.get_field("is_deleted"))

    def test_only_one_default_credential_per_tenant(self):
        first = WechatCredential.objects.create(
            tenant=self.tenant,
            name="First",
            status="active",
            token="token-1",
            cookie="cookie-1",
            is_default=True,
            created_by=self.member,
            updated_by=self.member,
        )
        second = WechatCredential.objects.create(
            tenant=self.tenant,
            name="Second",
            status="active",
            token="token-2",
            cookie="cookie-2",
            is_default=True,
            created_by=self.member,
            updated_by=self.member,
        )

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)

    def test_soft_delete_hides_credential_from_default_manager(self):
        credential = WechatCredential.objects.create(
            tenant=self.tenant,
            name="Disposable",
            status="active",
            token="token-1",
            cookie="cookie-1",
            is_default=False,
            created_by=self.member,
            updated_by=self.member,
        )

        credential.soft_delete()

        self.assertFalse(WechatCredential.objects.filter(pk=credential.pk).exists())
        self.assertTrue(WechatCredential.original_objects.filter(pk=credential.pk).exists())
