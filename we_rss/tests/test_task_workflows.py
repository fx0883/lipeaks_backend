import time
from tempfile import TemporaryDirectory
from datetime import timedelta
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from tenants.models import Tenant
from users.models import Member
from we_rss.models import (
    MemberFeedSubscription,
    WechatArticle,
    WechatCredential,
    WechatCredentialLoginSession,
    WechatFeed,
    WechatSyncTask,
)
from we_rss.services.article_service import ArticleService
from we_rss.services.article_stats_service import ArticleStatsRefreshService
from we_rss.services.credential_service import CredentialService
from we_rss.services.feed_service import FeedService
from we_rss.services.task_service import dispatch_we_rss_task


class FakeAsyncCredentialGateway:
    def initialize_login_session(self, login_session, on_status=None):
        return {
            "status": "pending",
            "qr_code_url": "https://example.com/qr",
            "qr_code_image": "image-data",
            "scan_status": "waiting",
            "token_snapshot": '{"wechat_session_id": "session-async-1", "fingerprint": "fingerprint-1"}',
            "cookie_snapshot": '{"uuid": "session-async-1", "fingerprint": "fingerprint-1"}',
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
    def initialize_login_session(self, login_session, on_status=None):
        return {
            "status": "pending",
            "qr_code_url": "https://example.com/qr-expired",
            "qr_code_image": "image-data",
            "scan_status": "waiting",
            "token_snapshot": '{"wechat_session_id": "session-expired-1", "fingerprint": "fingerprint-expired"}',
            "cookie_snapshot": '{"uuid": "session-expired-1", "fingerprint": "fingerprint-expired"}',
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
    def collect_feed_batch(self, feed, credential, *, begin=0, batch_size=20, deadline_at=None):
        return {
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
            "failed_articles": [],
            "has_more": False,
            "next_begin": begin + 1,
            "detail_success_count": 1,
            "detail_failed_count": 0,
        }


class FakeDuplicateUrlFeedGateway:
    def collect_feed_batch(self, feed, credential, *, begin=0, batch_size=20, deadline_at=None):
        return {
            "articles": [
                {
                    "source_id": "feed-article-1",
                    "article_type": "newspic",
                    "title": "Synced Article",
                    "description": "Synced description",
                    "content": "<p>New synced html</p>",
                    "url": "https://mp.weixin.qq.com/s/duplicate-article?__biz=Qkl6&mid=1&idx=1&sn=abc",
                    "read_num": 9,
                }
            ],
            "feed_payload": {
                "biz": "Qkl6",
                "mp_name": "Synced Feed Name",
                "mp_cover": "https://example.com/feed-avatar.png",
            },
            "failed_articles": [],
            "has_more": False,
            "next_begin": begin + 1,
            "detail_success_count": 1,
            "detail_failed_count": 0,
        }


class FakeBatchedFeedGateway:
    def __init__(self, *, total_articles=27, timeout_on_begin=None):
        self.total_articles = total_articles
        self.timeout_on_begin = timeout_on_begin

    def collect_feed_batch(self, feed, credential, *, begin=0, batch_size=20, deadline_at=None):
        if self.timeout_on_begin is not None and begin >= self.timeout_on_begin:
            raise TimeoutError("Feed sync batch timed out.")

        remaining = max(self.total_articles - begin, 0)
        article_count = min(batch_size, remaining)
        articles = []
        for offset in range(article_count):
            index = begin + offset + 1
            articles.append(
                {
                    "source_id": f"feed-article-{index}",
                    "article_type": "newspic",
                    "title": f"Synced Article {index}",
                    "description": f"Synced description {index}",
                    "content": f"<p>Synced content {index}</p>",
                    "url": f"https://mp.weixin.qq.com/s/feed-article-{index}",
                    "pic_url": f"https://example.com/feed-article-{index}.png",
                    "status": "active",
                }
            )

        next_begin = begin + article_count
        return {
            "articles": articles,
            "feed_payload": {
                "biz": "Qkl6",
                "mp_name": "Synced Feed Name",
                "mp_cover": "https://example.com/feed-avatar.png",
            },
            "failed_articles": [],
            "has_more": next_begin < self.total_articles,
            "next_begin": next_begin,
            "detail_success_count": article_count,
            "detail_failed_count": 0,
        }


class FakeDeletedFeedGateway:
    def collect_feed_batch(self, feed, credential, *, begin=0, batch_size=20, deadline_at=None):
        return {
            "articles": [
                {
                    "source_id": "feed-article-active",
                    "article_type": "newspic",
                    "title": "Active Synced Article",
                    "description": "Active description",
                    "content": "<p>Active content</p>",
                    "url": "https://mp.weixin.qq.com/s/feed-article-active",
                    "pic_url": "https://example.com/feed-article-active.png",
                    "status": "active",
                },
                {
                    "source_id": "feed-article-deleted",
                    "article_type": "newspic",
                    "title": "Deleted Synced Article",
                    "description": "Deleted description",
                    "content": "DELETED",
                    "url": "https://mp.weixin.qq.com/s/feed-article-deleted",
                    "pic_url": "https://example.com/feed-article-deleted.png",
                    "status": "deleted",
                },
            ],
            "feed_payload": {
                "biz": "Qkl6",
                "mp_name": "Synced Feed Name",
                "mp_cover": "https://example.com/feed-avatar.png",
            },
            "failed_articles": [],
            "has_more": False,
            "next_begin": begin + 2,
            "detail_success_count": 2,
            "detail_failed_count": 0,
        }


class FakeLatestScopedFeedGateway:
    def collect_feed_batch(self, feed, credential, *, begin=0, batch_size=20, deadline_at=None):
        return {
            "articles": [
                {
                    "source_id": "feed-article-new-1",
                    "article_type": "newspic",
                    "title": "Newest Synced Article",
                    "description": "Newest description",
                    "content": "<p>Newest content</p>",
                    "url": "https://mp.weixin.qq.com/s/latest-new-1?__biz=Qkl6&mid=1&idx=1&sn=new1",
                    "pic_url": "https://example.com/latest-new-1.png",
                    "status": "active",
                },
                {
                    "source_id": "feed-article-existing",
                    "article_type": "newspic",
                    "title": "Existing Synced Article",
                    "description": "Existing description",
                    "content": "<p>Existing content</p>",
                    "url": "https://mp.weixin.qq.com/s/latest-existing?__biz=Qkl6&mid=1&idx=2&sn=existing",
                    "pic_url": "https://example.com/latest-existing.png",
                    "status": "active",
                },
                {
                    "source_id": "feed-article-older-should-stop",
                    "article_type": "newspic",
                    "title": "Should Not Be Persisted",
                    "description": "Should not persist",
                    "content": "<p>Should not persist</p>",
                    "url": "https://mp.weixin.qq.com/s/latest-older?__biz=Qkl6&mid=1&idx=3&sn=older",
                    "pic_url": "https://example.com/latest-older.png",
                    "status": "active",
                },
            ],
            "feed_payload": {
                "biz": "Qkl6",
                "mp_name": "Synced Feed Name",
                "mp_cover": "https://example.com/feed-avatar.png",
            },
            "failed_articles": [],
            "has_more": True,
            "next_begin": begin + 3,
            "detail_success_count": 3,
            "detail_failed_count": 0,
        }


class FakeLatestScopedIncompleteExistingFeedGateway:
    def collect_feed_batch(self, feed, credential, *, begin=0, batch_size=20, deadline_at=None):
        return {
            "articles": [
                {
                    "source_id": "feed-article-existing-current-1",
                    "article_type": "newspic",
                    "title": "Existing Current Article 1",
                    "description": "Existing current description 1",
                    "content": "<p>Existing current content 1</p>",
                    "url": "https://mp.weixin.qq.com/s/latest-existing-current-1?__biz=Qkl6&mid=1&idx=1&sn=current1",
                    "pic_url": "https://example.com/latest-existing-current-1.png",
                    "status": "active",
                    "publish_time": timezone.now(),
                },
                {
                    "source_id": "feed-article-existing-current-2",
                    "article_type": "newspic",
                    "title": "Existing Current Article 2",
                    "description": "Existing current description 2",
                    "content": "<p>Existing current content 2</p>",
                    "url": "https://mp.weixin.qq.com/s/latest-existing-current-2?__biz=Qkl6&mid=1&idx=2&sn=current2",
                    "pic_url": "https://example.com/latest-existing-current-2.png",
                    "status": "active",
                    "publish_time": timezone.now(),
                },
                {
                    "source_id": "feed-article-existing-complete",
                    "article_type": "newspic",
                    "title": "Existing Complete Article",
                    "description": "Existing complete description",
                    "content": "<p>Existing complete content</p>",
                    "url": "https://mp.weixin.qq.com/s/latest-existing-complete?__biz=Qkl6&mid=1&idx=3&sn=complete",
                    "pic_url": "https://example.com/latest-existing-complete.png",
                    "status": "active",
                    "publish_time": timezone.now() - timedelta(days=1),
                },
            ],
            "feed_payload": {
                "biz": "Qkl6",
                "mp_name": "Synced Feed Name",
                "mp_cover": "https://example.com/feed-avatar.png",
            },
            "failed_articles": [],
            "has_more": True,
            "next_begin": begin + 3,
            "detail_success_count": 3,
            "detail_failed_count": 0,
        }


class FakeWindowScopedFeedGateway:
    def __init__(self):
        now = timezone.now()
        self.articles = [
            {
                "source_id": "feed-article-window-new-1",
                "article_type": "newspic",
                "title": "Window Synced Article 1",
                "description": "Window description 1",
                "content": "<p>Window content 1</p>",
                "url": "https://mp.weixin.qq.com/s/window-new-1",
                "pic_url": "https://example.com/window-new-1.png",
                "status": "active",
                "publish_time": now - timedelta(days=1),
            },
            {
                "source_id": "feed-article-window-new-2",
                "article_type": "newspic",
                "title": "Window Synced Article 2",
                "description": "Window description 2",
                "content": "<p>Window content 2</p>",
                "url": "https://mp.weixin.qq.com/s/window-new-2",
                "pic_url": "https://example.com/window-new-2.png",
                "status": "active",
                "publish_time": now - timedelta(days=2),
            },
            {
                "source_id": "feed-article-window-old",
                "article_type": "newspic",
                "title": "Window Old Article",
                "description": "Window old description",
                "content": "<p>Window old content</p>",
                "url": "https://mp.weixin.qq.com/s/window-old",
                "pic_url": "https://example.com/window-old.png",
                "status": "active",
                "publish_time": now - timedelta(days=10),
            },
        ]

    def collect_feed_batch(self, feed, credential, *, begin=0, batch_size=20, deadline_at=None):
        return {
            "articles": list(self.articles),
            "feed_payload": {
                "biz": "Qkl6",
                "mp_name": "Synced Feed Name",
                "mp_cover": "https://example.com/feed-avatar.png",
            },
            "failed_articles": [],
            "has_more": True,
            "next_begin": begin + len(self.articles),
            "detail_success_count": len(self.articles),
            "detail_failed_count": 0,
        }


class FakeFailingFeedGateway:
    def collect_feed_batch(self, feed, credential, *, begin=0, batch_size=20, deadline_at=None):
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
    def initialize_login_session(self, login_session, on_status=None):
        return {
            "status": "pending",
            "qr_code_url": "https://example.com/qr-fail",
            "qr_code_image": "image-data",
            "scan_status": "waiting",
            "token_snapshot": '{"wechat_session_id": "session-fail-1", "fingerprint": "fingerprint-fail"}',
            "cookie_snapshot": '{"uuid": "session-fail-1", "fingerprint": "fingerprint-fail"}',
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


class FakeMarkdownGateway:
    def fetch_markdown_from_url(self, url):
        return f"# Markdown for {url}"


class WeRssTaskDispatchTests(SimpleTestCase):
    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_dispatch_uses_background_executor_when_celery_is_disabled(self):
        def task_func(*args, **kwargs):
            time.sleep(0.2)
            return None

        started_at = time.monotonic()
        result = dispatch_we_rss_task(task_func, 1, article_id=2)
        elapsed = time.monotonic() - started_at

        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "result"))
        self.assertLess(elapsed, 0.1)
        result.result(timeout=2)

    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    @patch("we_rss.services.task_service.logger")
    @patch("we_rss.services.task_service._run_task_inline")
    @patch("we_rss.services.task_service._task_executor.submit")
    def test_dispatch_runs_inline_when_executor_is_shutting_down(
        self,
        mock_submit,
        mock_run_inline,
        mock_logger,
    ):
        def task_func(*args, **kwargs):
            return None

        mock_submit.side_effect = RuntimeError("cannot schedule new futures after shutdown")

        dispatch_we_rss_task(task_func, 1, article_id=2)

        mock_run_inline.assert_called_once_with(task_func, 1, article_id=2)
        mock_logger.warning.assert_called_once()

    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    @patch("we_rss.services.task_service.logger")
    @patch("we_rss.services.task_service._run_task_inline")
    @patch("we_rss.services.task_service._task_executor.submit")
    def test_dispatch_runs_inline_when_executor_is_closing_with_interpreter_shutdown_error(
        self,
        mock_submit,
        mock_run_inline,
        mock_logger,
    ):
        def task_func(*args, **kwargs):
            return None

        mock_submit.side_effect = RuntimeError("cannot schedule new futures after interpreter shutdown")

        dispatch_we_rss_task(task_func, 1, article_id=2)

        mock_run_inline.assert_called_once_with(task_func, 1, article_id=2)
        mock_logger.warning.assert_called_once()

    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    @patch("we_rss.services.task_service.logger")
    @patch("we_rss.services.task_service._run_task_inline")
    @patch("we_rss.services.task_service._task_executor.submit")
    def test_dispatch_runs_inline_when_executor_submit_raises_invalid_argument_during_shutdown(
        self,
        mock_submit,
        mock_run_inline,
        mock_logger,
    ):
        def task_func(*args, **kwargs):
            return None

        mock_submit.side_effect = OSError(22, "Invalid argument")

        dispatch_we_rss_task(task_func, 1, article_id=2)

        mock_run_inline.assert_called_once_with(task_func, 1, article_id=2)
        mock_logger.warning.assert_called_once()


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
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
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
    def test_feed_sync_task_does_not_refresh_markdown_by_default(self, _mock_gateway):
        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        self.feed.refresh_from_db()
        article = WechatArticle.objects.get(source_id="feed-article-1")
        task.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(task.task_type, "feed_sync_run")
        self.assertEqual(article.feed_id, self.feed.id)
        self.assertEqual(article.title, "Synced Article")
        self.assertEqual(article.article_type, "newspic")
        self.assertIsNotNone(self.feed.last_synced_at)
        self.assertEqual(self.feed.biz, "Qkl6")
        self.assertEqual(self.feed.mp_name, "Synced Feed Name")
        self.assertEqual(self.feed.mp_cover, "https://example.com/feed-avatar.png")
        self.assertEqual(task.result_payload["run_status"], "success")
        self.assertEqual(task.result_payload["articles_synced"], 1)
        self.assertEqual(task.result_payload["articles_failed"], 0)
        self.assertFalse(task.request_payload["refresh_markdown"])
        self.assertFalse(task.result_payload["refresh_markdown"])
        self.assertEqual(task.result_payload["latest_completed_batch"]["article_count"], 1)
        self.assertEqual(task.result_payload["latest_completed_batch"]["failed_articles"], [])
        self.assertEqual(article.content, "")

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeAsyncFeedGateway())
    def test_feed_sync_task_refreshes_markdown_when_requested(self, _mock_gateway):
        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            task = FeedService.sync_feed(
                feed=self.feed,
                created_by=self.member,
                refresh_markdown=True,
            )

        article = WechatArticle.objects.get(source_id="feed-article-1")
        task.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertTrue(task.request_payload["refresh_markdown"])
        self.assertTrue(task.result_payload["refresh_markdown"])
        self.assertEqual(article.content, "# Markdown for https://mp.weixin.qq.com/s/feed-article-1")

    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_feed_sync_dispatches_background_worker_when_celery_disabled(self):
        with patch("we_rss.services.feed_service.dispatch_we_rss_task", create=True) as mock_dispatch:
            with patch(
                "we_rss.tasks.run_feed_sync_batch_task.delay",
                side_effect=AssertionError("feed sync task should not run inline"),
                create=True,
            ):
                task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        mock_dispatch.assert_called_once()
        self.assertEqual(task.status, "running")

    def test_feed_sync_returns_existing_running_task(self):
        existing = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync_run",
            status="running",
            target_type="feed",
            target_id=self.feed.id,
            message="Feed sync is running.",
            result_payload={"run_status": "running", "poll_after_seconds": 5},
            created_by=self.member,
        )

        task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        self.assertEqual(task.id, existing.id)
        self.assertEqual(task.message, "A feed sync task is already running.")

    def test_feed_sync_replaces_stale_legacy_feed_sync_task(self):
        stale = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync",
            status="running",
            target_type="feed",
            target_id=self.feed.id,
            result_payload={
                "last_progress_at": (timezone.now() - timedelta(hours=2)).isoformat(),
            },
            created_by=self.member,
        )
        stale.started_at = timezone.now() - timedelta(hours=2)
        stale.save(update_fields=["started_at", "updated_at"])

        with patch("we_rss.services.feed_service.dispatch_we_rss_task"):
            task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        stale.refresh_from_db()

        self.assertEqual(stale.status, "timed_out")
        self.assertEqual(task.task_type, "feed_sync_run")
        self.assertNotEqual(task.id, stale.id)

    def test_feed_sync_replaces_orphan_batch_tasks_from_stale_parent_run(self):
        stale_parent = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync_run",
            status="running",
            target_type="feed",
            target_id=self.feed.id,
            result_payload={
                "run_status": "running",
                "last_progress_at": (timezone.now() - timedelta(hours=2)).isoformat(),
            },
            created_by=self.member,
        )
        stale_parent.started_at = timezone.now() - timedelta(hours=2)
        stale_parent.save(update_fields=["started_at", "updated_at"])

        stale_batch = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync_batch",
            status="running",
            target_type="feed",
            target_id=self.feed.id,
            request_payload={
                "parent_task_id": stale_parent.id,
                "feed_id": self.feed.id,
                "batch_no": 3,
                "begin": 40,
                "batch_size": 20,
            },
            created_by=self.member,
        )
        stale_batch.started_at = timezone.now() - timedelta(hours=2)
        stale_batch.save(update_fields=["started_at", "updated_at"])

        with patch("we_rss.services.feed_service.dispatch_we_rss_task"):
            task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        stale_parent.refresh_from_db()
        stale_batch.refresh_from_db()

        self.assertEqual(stale_parent.status, "timed_out")
        self.assertEqual(stale_batch.status, "timed_out")
        self.assertEqual(stale_batch.result_payload["timeout_reason"], "orphan_batch")
        self.assertEqual(task.task_type, "feed_sync_run")
        self.assertNotEqual(task.id, stale_parent.id)

    def test_feed_sync_replaces_batch_tasks_without_active_parent(self):
        orphan_batch = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="feed_sync_batch",
            status="running",
            target_type="feed",
            target_id=self.feed.id,
            request_payload={
                "parent_task_id": 999999,
                "feed_id": self.feed.id,
                "batch_no": 1,
                "begin": 0,
                "batch_size": 20,
            },
            created_by=self.member,
        )
        orphan_batch.started_at = timezone.now() - timedelta(hours=2)
        orphan_batch.save(update_fields=["started_at", "updated_at"])

        with patch("we_rss.services.feed_service.dispatch_we_rss_task"):
            FeedService.sync_feed(feed=self.feed, created_by=self.member)

        orphan_batch.refresh_from_db()
        self.assertEqual(orphan_batch.status, "timed_out")
        self.assertEqual(orphan_batch.result_payload["timeout_reason"], "orphan_batch")

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeBatchedFeedGateway(total_articles=27))
    def test_feed_sync_batch_updates_parent_and_enqueues_next_batch(self, _mock_gateway):
        dispatch_calls = []

        def initial_dispatch_side_effect(task_func, task_id):
            dispatch_calls.append(task_id)
            return task_func.apply(args=(task_id,))

        with patch("we_rss.services.feed_service.dispatch_we_rss_task", side_effect=initial_dispatch_side_effect):
            with patch("we_rss.tasks.dispatch_we_rss_task") as chained_dispatch:
                with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
                    parent = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        parent.refresh_from_db()

        self.assertEqual(parent.task_type, "feed_sync_run")
        self.assertEqual(parent.status, "running")
        self.assertEqual(parent.result_payload["batches_completed"], 1)
        self.assertTrue(parent.result_payload["has_more"])
        self.assertEqual(parent.result_payload["latest_completed_batch"]["batch_no"], 1)
        self.assertEqual(len(parent.result_payload["latest_completed_batch"]["articles"]), 20)
        self.assertIsNotNone(parent.result_payload["current_batch_task_id"])
        chained_dispatch.assert_called_once()

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeBatchedFeedGateway(total_articles=27))
    def test_feed_sync_batch_keeps_completed_batch_successful_when_next_dispatch_fails(self, _mock_gateway):
        def initial_dispatch_side_effect(task_func, task_id):
            return task_func.apply(args=(task_id,))

        with patch("we_rss.services.feed_service.dispatch_we_rss_task", side_effect=initial_dispatch_side_effect):
            with patch(
                "we_rss.tasks.dispatch_we_rss_task",
                side_effect=RuntimeError("next batch dispatch failed"),
            ):
                with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
                    parent = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        parent.refresh_from_db()
        first_batch = WechatSyncTask.objects.get(
            tenant=self.tenant,
            task_type="feed_sync_batch",
            request_payload__parent_task_id=parent.id,
            request_payload__batch_no=1,
        )
        next_batch = WechatSyncTask.objects.get(
            tenant=self.tenant,
            task_type="feed_sync_batch",
            request_payload__parent_task_id=parent.id,
            request_payload__batch_no=2,
        )

        self.assertEqual(first_batch.status, "success")
        self.assertEqual(next_batch.status, "failed")
        self.assertEqual(parent.status, "partial_success")
        self.assertEqual(parent.result_payload["batches_completed"], 1)
        self.assertFalse(parent.result_payload["has_more"])
        self.assertEqual(parent.result_payload["latest_completed_batch"]["batch_no"], 1)
        self.assertEqual(parent.result_payload["current_batch_task_id"], next_batch.id)
        self.assertEqual(parent.result_payload["error"], "next batch dispatch failed")

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeBatchedFeedGateway(total_articles=7))
    def test_feed_sync_final_batch_marks_parent_success(self, _mock_gateway):
        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            parent = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        parent.refresh_from_db()

        self.assertEqual(parent.status, "success")
        self.assertEqual(parent.result_payload["run_status"], "success")
        self.assertFalse(parent.result_payload["has_more"])
        self.assertEqual(parent.result_payload["articles_synced"], 7)

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeDeletedFeedGateway())
    def test_feed_sync_skips_deleted_articles_during_persistence(self, _mock_gateway):
        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            parent = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        parent.refresh_from_db()

        self.assertTrue(WechatArticle.objects.filter(source_id="feed-article-active").exists())
        self.assertFalse(WechatArticle.objects.filter(source_id="feed-article-deleted").exists())
        self.assertEqual(parent.status, "success")
        self.assertEqual(parent.result_payload["articles_synced"], 1)
        self.assertEqual(parent.result_payload["articles_failed"], 1)
        self.assertEqual(parent.result_payload["latest_completed_batch"]["article_count"], 1)
        self.assertEqual(len(parent.result_payload["latest_completed_batch"]["failed_articles"]), 1)
        self.assertEqual(
            parent.result_payload["latest_completed_batch"]["failed_articles"][0]["source_id"],
            "feed-article-deleted",
        )
        self.assertEqual(
            parent.result_payload["latest_completed_batch"]["failed_articles"][0]["error"],
            "Wechat article is unavailable or has been deleted.",
        )

    @patch(
        "we_rss.tasks.get_feed_gateway",
        return_value=FakeBatchedFeedGateway(total_articles=27, timeout_on_begin=20),
    )
    def test_feed_sync_timeout_marks_parent_partial_success(self, _mock_gateway):
        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            parent = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        parent.refresh_from_db()

        self.assertEqual(parent.status, "partial_success")
        self.assertEqual(parent.result_payload["run_status"], "partial_success")
        self.assertEqual(parent.result_payload["timeout_reason"], "batch_timeout")

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeFailingFeedGateway())
    def test_feed_sync_task_records_structured_failure_payload(self, _mock_gateway):
        task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        task.refresh_from_db()

        self.assertEqual(task.status, "failed")
        self.assertEqual(task.result_payload["feed_id"], self.feed.id)
        self.assertEqual(task.result_payload["error"], "WeChat rate limit triggered")
        self.assertEqual(task.result_payload["run_status"], "failed")
        self.assertEqual(task.task_type, "feed_sync_run")

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeDuplicateUrlFeedGateway())
    def test_feed_sync_updates_existing_article_by_url_instead_of_creating_duplicate(self, _mock_gateway):
        existing = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="legacy-source-id",
            title="Old Title",
            url="https://mp.weixin.qq.com/s/duplicate-article?__biz=Qkl6&mid=1&idx=1&sn=abc&token=123",
            content="old markdown",
        )

        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        task.refresh_from_db()
        existing.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(WechatArticle.objects.count(), 1)
        self.assertEqual(existing.source_id, "feed-article-1")
        self.assertEqual(existing.title, "Synced Article")
        self.assertEqual(existing.content, "# Markdown for https://mp.weixin.qq.com/s/duplicate-article?__biz=Qkl6&mid=1&idx=1&sn=abc")

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeDuplicateUrlFeedGateway())
    def test_feed_sync_skips_updating_existing_complete_article_by_url(self, _mock_gateway):
        existing = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="existing-complete-source-id",
            title="Keep Existing Title",
            description="Keep existing description",
            url="https://mp.weixin.qq.com/s/duplicate-article?__biz=Qkl6&mid=1&idx=1&sn=abc&token=123",
            pic_url="https://example.com/existing-complete.png",
            content="existing markdown content",
            publish_time=timezone.now() - timedelta(days=1),
            read_num=101,
        )

        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

        task.refresh_from_db()
        existing.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(WechatArticle.objects.count(), 1)
        self.assertEqual(existing.source_id, "existing-complete-source-id")
        self.assertEqual(existing.title, "Keep Existing Title")
        self.assertEqual(existing.description, "Keep existing description")
        self.assertEqual(existing.pic_url, "https://example.com/existing-complete.png")
        self.assertEqual(existing.read_num, 101)
        self.assertEqual(existing.content, "existing markdown content")

    def test_upsert_article_from_payload_backfills_existing_incomplete_article(self):
        existing = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="existing-incomplete-source-id",
            title="Incomplete Title",
            description="Incomplete description",
            url="https://mp.weixin.qq.com/s/incomplete-article?__biz=Qkl6&mid=1&idx=1&sn=incomplete&token=123",
            content="existing markdown content",
            publish_time=None,
        )

        article, created = ArticleService.upsert_article_from_payload(
            tenant=self.tenant,
            feed=self.feed,
            payload={
                "source_id": "backfilled-source-id",
                "article_type": "newspic",
                "title": "Backfilled Title",
                "description": "Backfilled description",
                "content": "<p>Backfilled html</p>",
                "url": "https://mp.weixin.qq.com/s/incomplete-article?__biz=Qkl6&mid=1&idx=1&sn=incomplete",
                "pic_url": "https://example.com/backfilled.png",
                "publish_time": timezone.now(),
                "status": "active",
                "read_num": 88,
            },
            actor=self.member,
        )

        existing.refresh_from_db()

        self.assertFalse(created)
        self.assertEqual(article.id, existing.id)
        self.assertEqual(existing.source_id, "backfilled-source-id")
        self.assertEqual(existing.title, "Backfilled Title")
        self.assertIsNotNone(existing.publish_time)

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeLatestScopedFeedGateway())
    def test_feed_sync_latest_scope_stops_when_normalized_article_url_exists(self, _mock_gateway):
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="existing-source-id",
            title="Existing Latest Article",
            url="https://mp.weixin.qq.com/s/latest-existing?__biz=Qkl6&mid=1&idx=2&sn=existing&token=123",
            content="old markdown",
            publish_time=timezone.now() - timedelta(days=1),
        )

        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            task = FeedService.sync_feed(feed=self.feed, created_by=self.member, sync_scope="latest")

        task.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(task.request_payload["sync_scope"], "latest")
        self.assertEqual(task.result_payload["sync_scope"], "latest")
        self.assertEqual(task.result_payload["run_status"], "success")
        self.assertFalse(task.result_payload["has_more"])
        self.assertEqual(task.result_payload["articles_synced"], 1)
        self.assertEqual(task.result_payload["stop_reason"], "existing_article_detected")
        self.assertEqual(
            task.result_payload["stop_article_url"],
            "https://mp.weixin.qq.com/s/latest-existing?__biz=Qkl6&mid=1&idx=2&sn=existing",
        )
        self.assertEqual(task.result_payload["stop_article_source_id"], "feed-article-existing")
        self.assertEqual(task.result_payload["latest_completed_batch"]["article_count"], 1)
        self.assertEqual(
            [item["source_id"] for item in task.result_payload["latest_completed_batch"]["articles"]],
            ["feed-article-new-1"],
        )
        self.assertTrue(WechatArticle.objects.filter(source_id="feed-article-new-1").exists())
        self.assertFalse(WechatArticle.objects.filter(source_id="feed-article-older-should-stop").exists())

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeLatestScopedIncompleteExistingFeedGateway())
    def test_feed_sync_latest_scope_backfills_incomplete_existing_articles_before_stopping(self, _mock_gateway):
        incomplete_first = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="latest-existing-current-1",
            title="Incomplete Existing Current Article 1",
            url="https://mp.weixin.qq.com/s/latest-existing-current-1?__biz=Qkl6&mid=1&idx=1&sn=current1&token=123",
            content="old markdown",
            publish_time=None,
        )
        incomplete_second = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="latest-existing-current-2",
            title="Incomplete Existing Current Article 2",
            url="https://mp.weixin.qq.com/s/latest-existing-current-2?__biz=Qkl6&mid=1&idx=2&sn=current2&token=123",
            content="old markdown",
            publish_time=None,
        )
        WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="feed-article-existing-complete",
            title="Existing Complete Article",
            url="https://mp.weixin.qq.com/s/latest-existing-complete?__biz=Qkl6&mid=1&idx=3&sn=complete&token=123",
            content="complete markdown",
            publish_time=timezone.now() - timedelta(days=2),
        )

        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            task = FeedService.sync_feed(feed=self.feed, created_by=self.member, sync_scope="latest")

        task.refresh_from_db()
        incomplete_first.refresh_from_db()
        incomplete_second.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(task.result_payload["stop_reason"], "existing_article_detected")
        self.assertEqual(task.result_payload["articles_synced"], 2)
        self.assertEqual(
            [item["source_id"] for item in task.result_payload["latest_completed_batch"]["articles"]],
            ["feed-article-existing-current-1", "feed-article-existing-current-2"],
        )
        self.assertEqual(incomplete_first.source_id, "feed-article-existing-current-1")
        self.assertIsNotNone(incomplete_first.publish_time)
        self.assertEqual(incomplete_second.source_id, "feed-article-existing-current-2")
        self.assertIsNotNone(incomplete_second.publish_time)

    @patch("we_rss.tasks.get_feed_gateway", return_value=FakeWindowScopedFeedGateway())
    def test_feed_sync_window_scope_stops_when_article_is_older_than_requested_window(self, _mock_gateway):
        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            task = FeedService.sync_feed(feed=self.feed, created_by=self.member, sync_scope="window", window_days=3)

        task.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(task.request_payload["sync_scope"], "window")
        self.assertEqual(task.request_payload["window_days"], 3)
        self.assertEqual(task.result_payload["sync_scope"], "window")
        self.assertEqual(task.result_payload["window_days"], 3)
        self.assertEqual(task.result_payload["run_status"], "success")
        self.assertFalse(task.result_payload["has_more"])
        self.assertEqual(task.result_payload["articles_synced"], 2)
        self.assertEqual(task.result_payload["stop_reason"], "window_boundary_reached")
        self.assertEqual(task.result_payload["stop_article_source_id"], "feed-article-window-old")
        self.assertIsNotNone(task.result_payload["stop_publish_time"])
        self.assertEqual(task.result_payload["latest_completed_batch"]["article_count"], 2)
        self.assertEqual(
            [item["source_id"] for item in task.result_payload["latest_completed_batch"]["articles"]],
            ["feed-article-window-new-1", "feed-article-window-new-2"],
        )
        self.assertFalse(WechatArticle.objects.filter(source_id="feed-article-window-old").exists())

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeAsyncArticleGateway())
    def test_article_import_task_runs_in_background(self, _mock_gateway):
        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
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
        self.assertEqual(article.content, "# Markdown for https://mp.weixin.qq.com/s/import-async")

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

        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            task = ArticleService.refresh_article(article=article, created_by=self.member)

        task.refresh_from_db()
        article.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(task.task_type, "article_refresh")
        self.assertEqual(article.title, "Tenant Article Updated")
        self.assertEqual(article.article_type, "newspic")
        self.assertEqual(article.read_num, 88)
        self.assertEqual(article.content, "# Markdown for https://mp.weixin.qq.com/s/article-1")

    @patch("we_rss.tasks.get_article_gateway", return_value=FakeAsyncArticleGateway())
    def test_article_import_updates_existing_article_by_url(self, _mock_gateway):
        existing = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="old-import-source",
            title="Old Title",
            url="https://mp.weixin.qq.com/s/import-async?token=123",
            content="old markdown",
        )

        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            task = ArticleService.import_article_by_url(
                tenant=self.tenant,
                created_by=self.member,
                url="https://mp.weixin.qq.com/s/import-async",
            )

        task.refresh_from_db()
        existing.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(WechatArticle.objects.count(), 1)
        self.assertEqual(existing.source_id, "async-import-1")
        self.assertEqual(existing.title, "Imported Async Article")
        self.assertEqual(existing.content, "# Markdown for https://mp.weixin.qq.com/s/import-async")

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

    @patch("we_rss.tasks.ArticleStatsRefreshService.refresh_article_stats_for_article")
    def test_article_stats_batch_task_marks_success_with_failed_articles(self, refresh_mock):
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-stats-1",
            title="Stats Article 1",
            url="https://mp.weixin.qq.com/s/article-stats-1",
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-stats-2",
            title="Stats Article 2",
            url="https://mp.weixin.qq.com/s/article-stats-2",
        )

        def side_effect(*, article):
            if article.id == second_article.id:
                raise Exception("stats blocked")
            article.read_num = 99
            article.save(update_fields=["read_num", "updated_at"])
            return article

        refresh_mock.side_effect = side_effect

        task = ArticleStatsRefreshService.enqueue_batch_refresh(
            tenant=self.tenant,
            created_by=self.member,
            article_ids=[first_article.id, second_article.id],
        )
        task.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(task.task_type, "article_stats_refresh")
        self.assertEqual(task.result_payload["requested_count"], 2)
        self.assertEqual(task.result_payload["success_count"], 1)
        self.assertEqual(task.result_payload["failed_count"], 1)
        self.assertEqual(task.result_payload["selector_type"], "article_ids")
        self.assertEqual(task.result_payload["article_ids"], [first_article.id, second_article.id])
        self.assertEqual(task.result_payload["failed_articles"][0]["article_id"], second_article.id)
        self.assertEqual(task.result_payload["failed_articles"][0]["url"], second_article.url)
        self.assertEqual(task.result_payload["failed_articles"][0]["error"], "stats blocked")

    @patch("we_rss.tasks.ArticleStatsRefreshService.refresh_article_stats_for_article")
    def test_article_stats_feed_task_refreshes_all_feed_articles_not_stale_first_page_ids(self, refresh_mock):
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-stats-feed-1",
            title="Stats Feed Article 1",
            url="https://mp.weixin.qq.com/s/article-stats-feed-1",
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-stats-feed-2",
            title="Stats Feed Article 2",
            url="https://mp.weixin.qq.com/s/article-stats-feed-2",
        )

        refreshed_ids = []

        def side_effect(*, article):
            refreshed_ids.append(article.id)
            article.read_num = 100 + len(refreshed_ids)
            article.save(update_fields=["read_num", "updated_at"])
            return article

        refresh_mock.side_effect = side_effect

        task = WechatSyncTask.objects.create(
            tenant=self.tenant,
            task_type="article_stats_refresh",
            status="pending",
            target_type="article_stats",
            task_key=f"article_stats_refresh:feed:{self.feed.id}",
            created_by=self.member,
            request_payload={
                "selector_type": "feed_id",
                "article_ids": [first_article.id],
                "feed_id": self.feed.id,
                "member_id": None,
            },
        )

        from we_rss.tasks import run_article_stats_refresh_task

        run_article_stats_refresh_task.run(task.id)
        task.refresh_from_db()
        first_article.refresh_from_db()
        second_article.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(task.result_payload["selector_type"], "feed_id")
        self.assertEqual(task.result_payload["requested_count"], 2)
        self.assertEqual(task.result_payload["success_count"], 2)
        self.assertEqual(task.result_payload["failed_count"], 0)
        self.assertEqual(task.result_payload["article_ids"], [second_article.id, first_article.id])
        self.assertEqual(refreshed_ids, [second_article.id, first_article.id])
        self.assertEqual(first_article.read_num, 102)
        self.assertEqual(second_article.read_num, 101)

    def test_refresh_article_markdown_sleeps_before_generating_markdown(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-markdown-sleep-1",
            title="Sleep Test Article",
            url="https://mp.weixin.qq.com/s/article-markdown-sleep-1",
        )

        with patch("we_rss.services.article_service.get_article_markdown_service", return_value=FakeMarkdownGateway()):
            with patch("we_rss.services.article_service.time.sleep") as sleep_mock:
                markdown = ArticleService.refresh_article_markdown(article=article)

        article.refresh_from_db()

        sleep_mock.assert_called_once_with(0.2)
        self.assertEqual(markdown, "# Markdown for https://mp.weixin.qq.com/s/article-markdown-sleep-1")
        self.assertEqual(article.content, markdown)

    @patch("we_rss.tasks.ArticleService.refresh_article_markdown")
    def test_feed_content_refresh_task_marks_success_with_failed_articles(self, refresh_mock):
        first_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="feed-content-refresh-article-1",
            title="Feed Content Article 1",
            url="https://mp.weixin.qq.com/s/feed-content-refresh-article-1",
        )
        second_article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="feed-content-refresh-article-2",
            title="Feed Content Article 2",
            url="https://mp.weixin.qq.com/s/feed-content-refresh-article-2",
        )

        def side_effect(*, article, gateway=None):
            if article.id == second_article.id:
                raise Exception("markdown blocked")
            article.content = "# Batch Markdown"
            article.save(update_fields=["content", "updated_at"])
            return article.content

        refresh_mock.side_effect = side_effect

        task = FeedService.refresh_feed_content(feed=self.feed, created_by=self.member)
        task.refresh_from_db()
        first_article.refresh_from_db()
        second_article.refresh_from_db()

        self.assertEqual(task.status, "success")
        self.assertEqual(task.task_type, "feed_content_refresh")
        self.assertEqual(task.result_payload["feed_id"], self.feed.id)
        self.assertEqual(task.result_payload["requested_count"], 2)
        self.assertEqual(task.result_payload["success_count"], 1)
        self.assertEqual(task.result_payload["failed_count"], 1)
        self.assertEqual(task.result_payload["article_ids"], [first_article.id, second_article.id])
        self.assertEqual(task.result_payload["failed_articles"][0]["article_id"], second_article.id)
        self.assertEqual(task.result_payload["failed_articles"][0]["url"], second_article.url)
        self.assertEqual(task.result_payload["failed_articles"][0]["error"], "markdown blocked")
        self.assertEqual(first_article.content, "# Batch Markdown")
        self.assertEqual(second_article.content, "")

