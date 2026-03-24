from unittest.mock import patch

from django.test import TestCase, override_settings

from tenants.models import Tenant
from users.models import Member
from we_rss.models import WechatArticle, WechatCredential, WechatCredentialLoginSession, WechatFeed, WechatSyncTask
from we_rss.services.article_service import ArticleService
from we_rss.services.credential_service import CredentialService
from we_rss.services.feed_service import FeedService
from we_rss.services.task_service import dispatch_we_rss_task


class FakeAsyncCredentialGateway:
    def create_login_session(self):
        return {
            "session_id": "session-async-1",
            "status": "pending",
            "qr_code_url": "https://example.com/qr",
            "qr_code_image": "image-data",
            "scan_status": "waiting",
        }

    def wait_for_login(self, login_session):
        return {
            "status": "success",
            "scan_status": "confirmed",
            "token_snapshot": "token-from-login",
            "cookie_snapshot": "cookie-from-login",
            "credential_name": "Worker Credential",
        }


class FakeExpiredCredentialGateway:
    def create_login_session(self):
        return {
            "session_id": "session-expired-1",
            "status": "pending",
            "qr_code_url": "https://example.com/qr-expired",
            "qr_code_image": "image-data",
            "scan_status": "waiting",
        }

    def wait_for_login(self, login_session, on_status=None):
        if on_status is not None:
            on_status({"status": "scanned", "scan_status": "scanned"})
        return {
            "status": "expired",
            "scan_status": "expired",
            "error_message": "WeChat login session expired before confirmation.",
        }


class FakeAsyncFeedGateway:
    def sync_feed(self, feed, credential):
        return {
            "message": "Feed sync complete",
            "articles": [
                {
                    "source_id": "feed-article-1",
                    "article_type": "newspic",
                    "title": "Synced Article",
                    "description": "Synced description",
                    "content": "<p>Synced content</p>",
                    "url": "https://mp.weixin.qq.com/s/feed-article-1",
                    "read_num": 9,
                }
            ],
            "feed_payload": {
                "biz": "Qkl6",
                "mp_name": "Synced Feed Name",
                "mp_cover": "https://example.com/feed-avatar.png",
            },
            "result_payload": {
                "fetched_count": 1,
                "detail_success_count": 1,
                "detail_failed_count": 0,
                "errors": [],
            },
        }


class FakeFailingFeedGateway:
    def sync_feed(self, feed, credential):
        raise Exception("WeChat rate limit triggered")


class FakeAsyncArticleGateway:
    def import_article_by_url(self, url, credential):
        return {
            "source_id": "async-import-1",
            "article_type": "newspic",
            "title": "Imported Async Article",
            "description": "Imported description",
            "content": "<p>Imported async content</p>",
            "url": url,
            "comment_total_count": 3,
        }

    def refresh_article(self, article, credential):
        return {
            "article_type": "newspic",
            "title": f"{article.title} Updated",
            "description": "Updated description",
            "content": "<p>Updated content</p>",
            "url": article.url,
            "read_num": 88,
            "comment_total_count": 13,
        }


class FakeDeletedImportArticleGateway:
    def import_article_by_url(self, url, credential):
        return {
            "source_id": "deleted-import-1",
            "title": "Deleted Import Article",
            "description": "Deleted description",
            "content": "DELETED",
            "status": "deleted",
            "url": url,
        }

    def refresh_article(self, article, credential):
        raise NotImplementedError


class FakeFailingCredentialGateway:
    def create_login_session(self):
        return {
            "session_id": "session-fail-1",
            "status": "pending",
            "qr_code_url": "https://example.com/qr-fail",
            "qr_code_image": "image-data",
            "scan_status": "waiting",
        }

    def wait_for_login(self, login_session, on_status=None):
        return {
            "status": "failed",
            "scan_status": "failed",
            "error_message": "WeChat rejected the QR login.",
        }


class FakeFailingArticleGateway:
    def import_article_by_url(self, url, credential):
        raise Exception("WeChat import blocked by anti-bot")

    def refresh_article(self, article, credential):
        raise Exception("WeChat refresh blocked by anti-bot")


class WeRssTaskDispatchTests(TestCase):
    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_dispatch_runs_inline_when_eager_mode_is_enabled(self):
        captured = []

        def task_func(*args, **kwargs):
            captured.append((args, kwargs))

        result = dispatch_we_rss_task(task_func, 1, article_id=2)

        self.assertIsNone(result)
        self.assertEqual(captured, [((1,), {"article_id": 2})])


@override_settings(CELERY_ENABLED=True, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class WeRssTaskWorkflowTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
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

    @patch("we_rss.tasks.get_credential_gateway", return_value=FakeAsyncCredentialGateway())
    def test_login_session_enqueues_and_completes_credential_login_task(self, _mock_gateway):
        session = CredentialService.create_login_session(
            tenant=self.tenant,
            created_by=self.member,
            gateway=FakeAsyncCredentialGateway(),
        )

        task = WechatSyncTask.objects.get(task_type="credential_login", target_id=session.id)
        session.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(session.status, "success")
        self.assertIsNotNone(session.credential_id)
        self.assertEqual(session.credential.name, "Worker Credential")

    @patch("we_rss.tasks.get_credential_gateway", return_value=FakeExpiredCredentialGateway())
    def test_login_session_keeps_expired_status_when_qr_expires(self, _mock_gateway):
        session = CredentialService.create_login_session(
            tenant=self.tenant,
            created_by=self.member,
            gateway=FakeExpiredCredentialGateway(),
        )

        task = WechatSyncTask.objects.get(task_type="credential_login", target_id=session.id)
        session.refresh_from_db()

        self.assertEqual(task.status, "failed")
        self.assertEqual(session.status, "expired")
        self.assertEqual(session.scan_status, "expired")
        self.assertEqual(session.error_message, "WeChat login session expired before confirmation.")

    @patch("we_rss.tasks.get_credential_gateway", return_value=FakeFailingCredentialGateway())
    def test_login_session_task_records_structured_failure_payload(self, _mock_gateway):
        session = CredentialService.create_login_session(
            tenant=self.tenant,
            created_by=self.member,
            gateway=FakeFailingCredentialGateway(),
        )

        task = WechatSyncTask.objects.get(task_type="credential_login", target_id=session.id)
        task.refresh_from_db()

        self.assertEqual(task.status, "failed")
        self.assertEqual(task.result_payload["session_id"], session.session_id)
        self.assertEqual(task.result_payload["task_type"], "credential_login")
        self.assertEqual(task.result_payload["status"], "failed")
        self.assertEqual(task.result_payload["error"], "WeChat rejected the QR login.")

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeAsyncFeedGateway())
    def test_feed_sync_task_persists_articles(self, _mock_gateway):
        task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        self.feed.refresh_from_db()
        article = WechatArticle.objects.get(source_id="feed-article-1")
        task.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(task.task_type, "feed_sync")
        self.assertEqual(article.feed_id, self.feed.id)
        self.assertEqual(article.title, "Synced Article")
        self.assertEqual(article.article_type, "newspic")
        self.assertIsNotNone(self.feed.last_synced_at)
        self.assertEqual(self.feed.biz, "Qkl6")
        self.assertEqual(self.feed.mp_name, "Synced Feed Name")
        self.assertEqual(self.feed.mp_cover, "https://example.com/feed-avatar.png")
        self.assertEqual(task.result_payload["detail_success_count"], 1)
        self.assertEqual(task.result_payload["detail_failed_count"], 0)
        self.assertEqual(task.result_payload["failed_articles"], [])

    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_feed_sync_dispatches_background_worker_when_celery_disabled(self):
        with patch("we_rss.services.feed_service.dispatch_we_rss_task", create=True) as mock_dispatch:
            with patch(
                "we_rss.tasks.run_feed_sync_task.delay",
                side_effect=AssertionError("feed sync task should not run inline"),
            ):
                task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        mock_dispatch.assert_called_once()
        self.assertEqual(task.status, "pending")

    def test_feed_sync_returns_existing_running_task(self):
        existing = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync",
            status="running",
            target_type="feed",
            target_id=self.feed.id,
            created_by=self.member,
        )

        task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        self.assertEqual(task.id, existing.id)

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeFailingFeedGateway())
    def test_feed_sync_task_records_structured_failure_payload(self, _mock_gateway):
        task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        task.refresh_from_db()

        self.assertEqual(task.status, "failed")
        self.assertEqual(task.result_payload["feed_id"], self.feed.id)
        self.assertEqual(task.result_payload["error"], "WeChat rate limit triggered")
        self.assertEqual(task.result_payload["task_type"], "feed_sync")

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeAsyncArticleGateway())
    def test_article_import_task_runs_in_background(self, _mock_gateway):
        task = ArticleService.import_article_by_url(
            tenant=self.tenant,
            created_by=self.member,
            url="https://mp.weixin.qq.com/s/import-async",
        )

        task.refresh_from_db()
        article = WechatArticle.objects.get(source_id="async-import-1")

        self.assertEqual(task.status, "success")
        self.assertEqual(task.task_type, "article_import")
        self.assertEqual(article.title, "Imported Async Article")
        self.assertEqual(article.article_type, "newspic")

    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_article_import_dispatches_background_worker_when_celery_disabled(self):
        with patch("we_rss.services.article_service.dispatch_we_rss_task", create=True) as mock_dispatch:
            with patch(
                "we_rss.tasks.run_article_import_task.delay",
                side_effect=AssertionError("article import task should not run inline"),
            ):
                task = ArticleService.import_article_by_url(
                    tenant=self.tenant,
                    created_by=self.member,
                    url="https://mp.weixin.qq.com/s/import-disabled",
                )

        mock_dispatch.assert_called_once()
        self.assertEqual(task.status, "pending")

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeDeletedImportArticleGateway())
    def test_article_import_task_fails_for_deleted_article_payload(self, _mock_gateway):
        task = ArticleService.import_article_by_url(
            tenant=self.tenant,
            created_by=self.member,
            url="https://mp.weixin.qq.com/s/deleted-import",
        )

        task.refresh_from_db()

        self.assertEqual(task.status, "failed")
        self.assertFalse(WechatArticle.objects.filter(source_id="deleted-import-1").exists())

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeFailingArticleGateway())
    def test_article_import_task_records_structured_failure_payload(self, _mock_gateway):
        task = ArticleService.import_article_by_url(
            tenant=self.tenant,
            created_by=self.member,
            url="https://mp.weixin.qq.com/s/import-fail",
        )

        task.refresh_from_db()

        self.assertEqual(task.status, "failed")
        self.assertEqual(task.result_payload["task_type"], "article_import")
        self.assertEqual(task.result_payload["url"], "https://mp.weixin.qq.com/s/import-fail")
        self.assertEqual(task.result_payload["error"], "WeChat import blocked by anti-bot")

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeAsyncArticleGateway())
    def test_article_refresh_task_runs_in_background(self, _mock_gateway):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
            url="https://mp.weixin.qq.com/s/article-1",
        )

        task = ArticleService.refresh_article(article=article, created_by=self.member)

        task.refresh_from_db()
        article.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(task.task_type, "article_refresh")
        self.assertEqual(article.title, "Tenant Article Updated")
        self.assertEqual(article.article_type, "newspic")
        self.assertEqual(article.read_num, 88)

    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_article_refresh_dispatches_background_worker_when_celery_disabled(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-disabled-refresh-1",
            title="Tenant Article",
            url="https://mp.weixin.qq.com/s/article-disabled-refresh-1",
        )

        with patch("we_rss.services.article_service.dispatch_we_rss_task", create=True) as mock_dispatch:
            with patch(
                "we_rss.tasks.run_article_refresh_task.delay",
                side_effect=AssertionError("article refresh task should not run inline"),
            ):
                task = ArticleService.refresh_article(article=article, created_by=self.member)

        mock_dispatch.assert_called_once()
        self.assertEqual(task.status, "pending")

    def test_article_refresh_returns_existing_running_task(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
            url="https://mp.weixin.qq.com/s/article-1",
        )
        existing = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="article_refresh",
            status="running",
            target_type="article",
            target_id=article.id,
            created_by=self.member,
        )

        task = ArticleService.refresh_article(article=article, created_by=self.member)

        self.assertEqual(task.id, existing.id)

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeFailingArticleGateway())
    def test_article_refresh_task_records_structured_failure_payload(self, _mock_gateway):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-fail-1",
            title="Tenant Article",
            url="https://mp.weixin.qq.com/s/article-fail-1",
        )

        task = ArticleService.refresh_article(article=article, created_by=self.member)
        task.refresh_from_db()

        self.assertEqual(task.status, "failed")
        self.assertEqual(task.result_payload["task_type"], "article_refresh")
        self.assertEqual(task.result_payload["article_id"], article.id)
        self.assertEqual(task.result_payload["error"], "WeChat refresh blocked by anti-bot")

    def test_article_import_returns_existing_running_task_for_same_url(self):
        existing = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="article_import",
            status="pending",
            target_type="article",
            task_key="article_import:https://mp.weixin.qq.com/s/dup",
            created_by=self.member,
        )

        task = ArticleService.import_article_by_url(
            tenant=self.tenant,
            created_by=self.member,
            url="https://mp.weixin.qq.com/s/dup",
        )

        self.assertEqual(task.id, existing.id)
