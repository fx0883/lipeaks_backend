from django.db import IntegrityError
from django.test import TestCase

from common.models import BaseModel
from tenants.models import Tenant
from users.models import Member
from we_rss.models import (
    MemberArticleState,
    MemberArticleTagRelation,
    MemberFeedSubscription,
    MemberFeedTagRelation,
    MemberSeoKeyword,
    MemberTag,
    MemberTagSeoKeywordRelation,
    WechatArticle,
    WechatCredential,
    WechatCredentialLoginSession,
    WechatFeed,
    WechatSyncTask,
)
from we_rss.services.feed_service import FeedService


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


class WeRssTagModelTests(TestCase):
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

    def test_member_tag_name_is_case_insensitive_unique_per_member(self):
        MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="AI",
        )

        with self.assertRaises(IntegrityError):
            MemberTag.objects.create(
                tenant=self.tenant,
                member=self.member,
                name="ai",
            )

    def test_other_member_can_reuse_same_tag_name(self):
        MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="AI",
        )

        tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.other_member,
            name="AI",
        )

        self.assertEqual(tag.name, "AI")

    def test_deleting_tag_cascades_feed_and_article_relations(self):
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
        MemberArticleTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            article=self.article,
        )

        tag.delete()

        self.assertFalse(MemberFeedTagRelation.objects.filter(member=self.member).exists())
        self.assertFalse(MemberArticleTagRelation.objects.filter(member=self.member).exists())

    def test_deleting_feed_cascades_feed_tag_relations(self):
        tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Digest",
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            feed=self.feed,
        )

        self.feed.delete()

        self.assertFalse(MemberFeedTagRelation.objects.filter(member=self.member).exists())

    def test_deleting_article_cascades_article_tag_relations(self):
        tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Longform",
        )
        MemberArticleTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            article=self.article,
        )

        self.article.delete()

        self.assertFalse(MemberArticleTagRelation.objects.filter(member=self.member).exists())

    def test_member_article_state_is_unique_per_member_and_article(self):
        MemberArticleState.objects.create(
            tenant=self.tenant,
            member=self.member,
            article=self.article,
            is_favorite=True,
        )

        with self.assertRaises(IntegrityError):
            MemberArticleState.objects.create(
                tenant=self.tenant,
                member=self.member,
                article=self.article,
                is_hidden=True,
            )


class WeRssTagCleanupTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )
        self.feed = WechatFeed.objects.create(
            tenant=self.tenant,
            mp_name="Tenant Feed",
            source_id="feed-1",
            created_by=self.member,
            updated_by=self.member,
        )

    def test_unsubscribe_removes_member_feed_tag_relations(self):
        tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Digest",
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            feed=self.feed,
        )

        FeedService.unsubscribe_member(feed=self.feed, member=self.member)

        self.assertFalse(
            MemberFeedTagRelation.objects.filter(
                member=self.member,
                feed=self.feed,
            ).exists()
        )


class WeRssSeoKeywordModelTests(TestCase):
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
        self.tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Weight Loss",
        )
        self.keyword = MemberSeoKeyword.objects.create(
            tenant=self.tenant,
            member=self.member,
            keyword="Weight Loss",
            search_index=100,
        )

    def test_member_seo_keyword_is_case_insensitive_unique_per_member(self):
        with self.assertRaises(IntegrityError):
            MemberSeoKeyword.objects.create(
                tenant=self.tenant,
                member=self.member,
                keyword="weight loss",
                search_index=200,
            )

    def test_other_member_can_reuse_same_keyword(self):
        keyword = MemberSeoKeyword.objects.create(
            tenant=self.tenant,
            member=self.other_member,
            keyword="weight loss",
            search_index=300,
        )

        self.assertEqual(keyword.member_id, self.other_member.id)


class WeRssSeoKeywordRelationCleanupTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )
        self.tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Weight Loss",
        )
        self.keyword = MemberSeoKeyword.objects.create(
            tenant=self.tenant,
            member=self.member,
            keyword="Weight Loss Recipes",
            search_index=100,
        )

    def test_deleting_keyword_cascades_keyword_tag_relations(self):
        relation = MemberTagSeoKeywordRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag,
            seo_keyword=self.keyword,
        )

        self.keyword.delete()

        self.assertFalse(
            MemberTagSeoKeywordRelation.objects.filter(id=relation.id).exists()
        )

    def test_deleting_tag_cascades_keyword_tag_relations_only(self):
        MemberTagSeoKeywordRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag,
            seo_keyword=self.keyword,
        )

        self.tag.delete()

        self.assertTrue(MemberSeoKeyword.objects.filter(id=self.keyword.id).exists())
        self.assertFalse(
            MemberTagSeoKeywordRelation.objects.filter(
                seo_keyword_id=self.keyword.id
            ).exists()
        )
