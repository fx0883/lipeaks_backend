# We RSS article stats refresh implementation plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development
> (if subagents available) or superpowers:executing-plans to implement this
> plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new independent article stats refresh API family for `we_rss`
that refreshes existing articles by URL, updates database stats fields, returns
the full article synchronously for single refreshes, and supports asynchronous
batch refresh by `article_ids`, `feed_id`, or `member_id`.

**Architecture:** Keep this feature separate from the existing article import
and article content refresh flow. Add a dedicated stats-refresh service that
adapts the `scripts/lipeaks_viral_articles` PoC, a synchronous endpoint that
refreshes one existing article by URL, and a new async task type for batch
refreshes with partial-failure reporting.

**Tech Stack:** Django, Django REST Framework, drf-spectacular, Celery-backed
task dispatch, Django test runner, existing `we_rss` tenant-scoped models.

---

## Context and source of truth

This plan implements the approved design in:

- `docs/superpowers/specs/2026-04-04-we-rss-article-stats-refresh-design.md`

The implementation must preserve these design decisions:

- Single refresh is synchronous.
- Single refresh accepts `url`, updates the existing `WechatArticle`, and
  returns the full serialized article.
- Batch refresh is asynchronous and only returns a task object.
- Batch refresh supports exactly one selector: `article_ids`, `feed_id`, or
  `member_id`.
- The new APIs are independent from `/articles/import-by-url/` and
  `/articles/{id}/refresh/`.
- The new logic only updates stats fields plus `last_refreshed_at`.

## File structure map

Map the work up front so responsibilities stay clear.

### New and modified service files

- Create: `we_rss/services/article_stats_service.py`
- Modify: `we_rss/services/task_service.py`
- Modify: `we_rss/services/__init__.py`

### New and modified API files

- Create: `we_rss/views/article_stats_views.py`
- Modify: `we_rss/urls.py`
- Modify: `we_rss/serializers.py`
- Modify: `we_rss/schema.py`

### New and modified task and model files

- Modify: `we_rss/models.py`
- Create: `we_rss/migrations/0006_alter_wechatsynctask_task_type.py`
- Modify: `we_rss/tasks.py`

### New and modified tests

- Create: `we_rss/tests/test_article_stats_service.py`
- Create: `we_rss/tests/test_article_stats_api.py`
- Modify: `we_rss/tests/test_task_workflows.py`
- Modify: `we_rss/tests/test_schema.py`

## Implementation constraints

- Use @superpowers:test-driven-development for every new behavior.
- Do not fold this behavior into `ArticleService.refresh_article()`.
- Do not create new articles from the sync URL endpoint.
- Do not update non-stats article fields from the new service.
- Use the real import path for the PoC module:
  `scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext`.
- Validate POC runtime files before calling `collect_stats()`.
- Keep all article lookups tenant-scoped.
- Preserve partial success for batch refreshes. Per-article failures must not
  fail the whole batch once execution has started.

## Chunk 1: Core stats refresh service

### Task 1: Add failing unit tests for the new stats refresh service

**Files:**

- Create: `we_rss/tests/test_article_stats_service.py`
- Test: `we_rss/services/article_stats_service.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from tenants.models import Tenant
from users.models import Member
from we_rss.models import WechatArticle, WechatFeed
from we_rss.services.article_stats_service import ArticleStatsRefreshService


class ArticleStatsRefreshServiceTests(TestCase):
    def test_refresh_by_url_updates_existing_article_stats(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Existing",
            url="https://mp.weixin.qq.com/s/article-1?token=123",
        )

        with patch(
            "we_rss.services.article_stats_service.collect_stats",
            return_value={"read_num": 9, "comment_total_count": 4},
        ):
            refreshed = ArticleStatsRefreshService.refresh_article_stats_by_url(
                tenant=self.tenant,
                article_url="https://mp.weixin.qq.com/s/article-1",
            )

        article.refresh_from_db()
        self.assertEqual(refreshed.id, article.id)
        self.assertEqual(article.read_num, 9)
        self.assertEqual(article.comment_total_count, 4)

    def test_refresh_by_url_rejects_missing_article(self):
        with self.assertRaisesMessage(ValidationError, "Article not found"):
            ArticleStatsRefreshService.refresh_article_stats_by_url(
                tenant=self.tenant,
                article_url="https://mp.weixin.qq.com/s/missing",
            )

    def test_refresh_by_url_rejects_unready_stats_runtime(self):
        with patch.object(Path, "exists", return_value=False):
            with self.assertRaisesMessage(ValidationError, "not ready"):
                ArticleStatsRefreshService.ensure_stats_runtime_ready()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_article_stats_service.ArticleStatsRefreshServiceTests -v 2`

Expected: FAIL because `article_stats_service.py` does not exist yet.

- [ ] **Step 3: Create the minimal service skeleton**

Implement `we_rss/services/article_stats_service.py` with:

- `ArticleStatsRefreshService`
- `POC_STATS_FIELDS`
- `SESSION_FILE` and `LIVE_LOG_FILE` paths under
  `scripts/lipeaks_viral_articles/output/wechat-stats/`
- `ensure_stats_runtime_ready()`
- `refresh_article_stats_by_url()`
- `refresh_article_stats_for_article()`
- a private helper that filters PoC output to the approved stats field whitelist
- tenant-scoped existing-article lookup using normalized URL matching

Use the existing article URL normalization helper from
`we_rss.services.article_service.ArticleService._normalize_task_url()` or move a
small shared helper if that keeps responsibilities cleaner.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_article_stats_service.ArticleStatsRefreshServiceTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/article_stats_service.py we_rss/tests/test_article_stats_service.py
git commit -m "feat: add article stats refresh service"
```

### Task 2: Add service tests for allowed field updates only

**Files:**

- Modify: `we_rss/tests/test_article_stats_service.py`
- Test: `we_rss/services/article_stats_service.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_refresh_does_not_modify_non_stats_fields(self):
    article = WechatArticle.objects.create(
        tenant=self.tenant,
        feed=self.feed,
        source_id="article-2",
        title="Original title",
        description="Original description",
        content="Original content",
        url="https://mp.weixin.qq.com/s/article-2",
    )

    with patch(
        "we_rss.services.article_stats_service.collect_stats",
        return_value={
            "title": "Wrong title",
            "read_num": 100,
            "comment_count": 7,
            "comment_reply_count": 2,
            "comment_total_count": 9,
        },
    ):
        ArticleStatsRefreshService.refresh_article_stats_for_article(article=article)

    article.refresh_from_db()
    self.assertEqual(article.title, "Original title")
    self.assertEqual(article.description, "Original description")
    self.assertEqual(article.content, "Original content")
    self.assertEqual(article.read_num, 100)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
`python manage.py test we_rss.tests.test_article_stats_service.ArticleStatsRefreshServiceTests.test_refresh_does_not_modify_non_stats_fields -v 2`

Expected: FAIL until the service strictly filters the PoC payload.

- [ ] **Step 3: Tighten the update logic**

Update the service so it only writes:

- `read_num`
- `like_num`
- `old_like_num`
- `share_num`
- `collect_num`
- `comment_count`
- `comment_reply_count`
- `comment_total_count`
- `last_refreshed_at`

Leave all other article fields untouched.

- [ ] **Step 4: Run the test to verify it passes**

Run:
`python manage.py test we_rss.tests.test_article_stats_service.ArticleStatsRefreshServiceTests.test_refresh_does_not_modify_non_stats_fields -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/article_stats_service.py we_rss/tests/test_article_stats_service.py
git commit -m "feat: isolate article stats field updates"
```

## Chunk 2: Sync API and schema

### Task 3: Add failing API tests for sync refresh by URL

**Files:**

- Create: `we_rss/tests/test_article_stats_api.py`
- Test: `we_rss/views/article_stats_views.py`
- Test: `we_rss/serializers.py`
- Test: `we_rss/urls.py`

- [ ] **Step 1: Write the failing tests**

```python
from unittest.mock import patch

from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member
from we_rss.models import WechatArticle, WechatFeed


class ArticleStatsSyncApiTests(APITestCase):
    def test_refresh_by_url_updates_article_and_returns_full_article(self):
        article = WechatArticle.objects.create(
            tenant=self.tenant,
            feed=self.feed,
            source_id="article-1",
            title="Tenant Article",
            url="https://mp.weixin.qq.com/s/article-1?token=123",
        )

        with patch(
            "we_rss.views.article_stats_views.ArticleStatsRefreshService.refresh_article_stats_by_url"
        ) as refresh_mock:
            refresh_mock.return_value = article
            response = self.client.post(
                "/api/v1/we-rss/article-stats/refresh-by-url/",
                {"url": "https://mp.weixin.qq.com/s/article-1"},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["id"], article.id)
        self.assertIn("read_num", response.data["data"])
        self.assertIn("title", response.data["data"])

    def test_refresh_by_url_returns_404_when_article_missing(self):
        response = self.client.post(
            "/api/v1/we-rss/article-stats/refresh-by-url/",
            {"url": "https://mp.weixin.qq.com/s/missing"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_article_stats_api.ArticleStatsSyncApiTests -v 2`

Expected: FAIL because the endpoint, serializer, and view do not exist.

- [ ] **Step 3: Add request serializer and sync view**

Implement:

- `ArticleStatsRefreshByUrlSerializer` in `we_rss/serializers.py`
- `ArticleStatsViewSet` or a focused view in
  `we_rss/views/article_stats_views.py`
- URL route in `we_rss/urls.py`:
  `POST /api/v1/we-rss/article-stats/refresh-by-url/`

Behavior requirements:

- validate the URL with a dedicated serializer
- call `ArticleStatsRefreshService.refresh_article_stats_by_url(...)`
- return the updated article using `WechatArticleSerializer`
- translate missing article to HTTP `404`
- keep tenant scoping consistent with the rest of `we_rss`

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_article_stats_api.ArticleStatsSyncApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/serializers.py we_rss/views/article_stats_views.py we_rss/urls.py we_rss/tests/test_article_stats_api.py
git commit -m "feat: add sync article stats refresh api"
```

### Task 4: Document the new sync endpoint in schema tests

**Files:**

- Modify: `we_rss/schema.py`
- Modify: `we_rss/tests/test_schema.py`

- [ ] **Step 1: Write the failing schema tests**

```python
def test_article_stats_refresh_by_url_operation_is_documented(self):
    schema = self._load_schema()
    operation = schema["paths"]["/api/v1/we-rss/article-stats/refresh-by-url/"]["post"]
    self.assertEqual(operation["operationId"], "we_rss_article_stats_refresh_by_url")
    self.assertEqual(
        operation["responses"]["200"]["content"]["application/json"]["schema"]["type"],
        "object",
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_schema.WeRssSchemaTests.test_article_stats_refresh_by_url_operation_is_documented -v 2`

Expected: FAIL because the path is not described yet.

- [ ] **Step 3: Add schema examples and operation metadata**

Update `we_rss/schema.py` to include:

- a request example for `{"url": "..."}`
- a success example that returns the full article payload
- an operation summary and description that say this endpoint updates database
  stats and returns the refreshed article

Annotate the new view with `extend_schema(...)` using existing `json_response()`
helpers.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_schema.WeRssSchemaTests.test_article_stats_refresh_by_url_operation_is_documented -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/schema.py we_rss/tests/test_schema.py we_rss/views/article_stats_views.py
git commit -m "docs: document sync article stats refresh endpoint"
```

## Chunk 3: Batch async selector flow

### Task 5: Add failing tests for batch request validation

**Files:**

- Modify: `we_rss/tests/test_article_stats_api.py`
- Test: `we_rss/serializers.py`

- [ ] **Step 1: Write the failing tests**

```python
class ArticleStatsBatchApiTests(APITestCase):
    def test_batch_refresh_accepts_article_ids(self):
        response = self.client.post(
            "/api/v1/we-rss/article-stats/refresh/",
            {"article_ids": [1, 2, 2]},
            format="json",
        )
        self.assertNotEqual(response.status_code, 400)

    def test_batch_refresh_rejects_multiple_selectors(self):
        response = self.client.post(
            "/api/v1/we-rss/article-stats/refresh/",
            {"article_ids": [1], "feed_id": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_article_stats_api.ArticleStatsBatchApiTests -v 2`

Expected: FAIL because batch serializer and route do not exist.

- [ ] **Step 3: Add the batch request serializer**

Implement `ArticleStatsBatchRefreshSerializer` in `we_rss/serializers.py` with:

- optional `article_ids`
- optional `feed_id`
- optional `member_id`
- validation that exactly one selector mode is provided
- list deduping delegated to the service layer, not the serializer

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_article_stats_api.ArticleStatsBatchApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/serializers.py we_rss/tests/test_article_stats_api.py
git commit -m "feat: add batch article stats refresh validation"
```

### Task 6: Add failing workflow tests for async batch execution

**Files:**

- Modify: `we_rss/tests/test_task_workflows.py`
- Test: `we_rss/tasks.py`
- Test: `we_rss/services/article_stats_service.py`
- Test: `we_rss/models.py`

- [ ] **Step 1: Write the failing tests**

```python
class FakeArticleStatsGateway:
    def __call__(self, article):
        return article


@patch("we_rss.tasks.ArticleStatsRefreshService.refresh_article_stats_for_article")
def test_article_stats_batch_task_marks_success_with_failed_articles(self, refresh_mock):
    first_article = WechatArticle.objects.create(...)
    second_article = WechatArticle.objects.create(...)

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
    self.assertEqual(task.result_payload["success_count"], 1)
    self.assertEqual(task.result_payload["failed_count"], 1)
    self.assertEqual(task.result_payload["failed_articles"][0]["article_id"], second_article.id)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_article_stats_batch_task_marks_success_with_failed_articles -v 2`

Expected: FAIL because the task type, enqueue flow, and worker do not exist.

- [ ] **Step 3: Implement the async task type and batch enqueue flow**

Modify:

- `we_rss/models.py` to add `ARTICLE_STATS_REFRESH` to task type choices
- `we_rss/migrations/0006_alter_wechatsynctask_task_type.py`
- `we_rss/services/article_stats_service.py` to add:
  - selector resolution
  - `enqueue_batch_refresh(...)`
  - helper methods for `article_ids`, `feed_id`, `member_id`
- `we_rss/tasks.py` to add `run_article_stats_refresh_task`

Behavior requirements:

- create one task per batch request
- resolve all target article IDs before dispatch
- run per-article refreshes sequentially inside the worker
- collect `requested_count`, `success_count`, `failed_count`, `article_ids`,
  and `failed_articles`
- mark the task `success` after execution completes, even if some articles fail

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_article_stats_batch_task_marks_success_with_failed_articles -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/models.py we_rss/migrations/0006_alter_wechatsynctask_task_type.py we_rss/services/article_stats_service.py we_rss/tasks.py we_rss/tests/test_task_workflows.py
git commit -m "feat: add async batch article stats refresh task"
```

### Task 7: Add failing API tests for batch task creation

**Files:**

- Modify: `we_rss/tests/test_article_stats_api.py`
- Test: `we_rss/views/article_stats_views.py`
- Test: `we_rss/urls.py`

- [ ] **Step 1: Write the failing tests**

```python
@patch("we_rss.views.article_stats_views.ArticleStatsRefreshService.enqueue_batch_refresh")
def test_batch_refresh_returns_task_payload(self, enqueue_mock):
    task = WechatSyncTask.objects.create(
        tenant=self.tenant,
        task_type="article_stats_refresh",
        status="pending",
        target_type="article_stats",
        created_by=self.member,
    )
    enqueue_mock.return_value = task

    response = self.client.post(
        "/api/v1/we-rss/article-stats/refresh/",
        {"feed_id": self.feed.id},
        format="json",
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data["data"]["task_type"], "article_stats_refresh")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_article_stats_api.ArticleStatsBatchApiTests.test_batch_refresh_returns_task_payload -v 2`

Expected: FAIL because the batch endpoint does not exist yet.

- [ ] **Step 3: Add the batch API endpoint**

Implement:

- `POST /api/v1/we-rss/article-stats/refresh/`
- use `ArticleStatsBatchRefreshSerializer`
- call `ArticleStatsRefreshService.enqueue_batch_refresh(...)`
- return `WechatSyncTaskSerializer`

Also add schema metadata in `we_rss/schema.py` for:

- request examples using `article_ids`, `feed_id`, and `member_id`
- success example returning a task
- clear description that the endpoint is async and does not return per-article
  data

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_article_stats_api.ArticleStatsBatchApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/views/article_stats_views.py we_rss/urls.py we_rss/schema.py we_rss/tests/test_article_stats_api.py we_rss/tests/test_schema.py
git commit -m "feat: add batch article stats refresh api"
```

## Chunk 4: Full verification

### Task 8: Run focused regression and schema verification

**Files:**

- Modify: any implementation files required to fix regressions
- Test: `we_rss/tests/test_article_stats_service.py`
- Test: `we_rss/tests/test_article_stats_api.py`
- Test: `we_rss/tests/test_task_workflows.py`
- Test: `we_rss/tests/test_schema.py`

- [ ] **Step 1: Run the new focused test suite**

Run:
`python manage.py test we_rss.tests.test_article_stats_service we_rss.tests.test_article_stats_api we_rss.tests.test_task_workflows we_rss.tests.test_schema -v 2`

Expected: all new stats-refresh coverage passes.

- [ ] **Step 2: Run the broader `we_rss` regression slice**

Run:
`python manage.py test we_rss.tests -v 2`

Expected: all existing `we_rss` tests still pass.

- [ ] **Step 3: Verify migrations**

Run:
`python manage.py makemigrations we_rss --check`

Expected: no pending model drift after `0006_alter_wechatsynctask_task_type.py`.

- [ ] **Step 4: Verify OpenAPI generation**

Run:
`python manage.py spectacular --file schema.yml`

Expected: schema generation completes and includes both
`/api/v1/we-rss/article-stats/refresh-by-url/` and
`/api/v1/we-rss/article-stats/refresh/`.

- [ ] **Step 5: Commit the completed feature**

```bash
git add we_rss docs/superpowers/specs/2026-04-04-we-rss-article-stats-refresh-design.md docs/superpowers/plans/2026-04-04-we-rss-article-stats-refresh-implementation.md schema.yml
git commit -m "feat: add we_rss article stats refresh apis"
```

## Open implementation notes

- If `ArticleService._normalize_task_url()` is the cleanest existing URL
  normalizer, reuse it directly. If importing it creates a circular dependency,
  move the normalization helper into a smaller shared module.
- Keep the POC integration behind the new service. Views and tasks should not
  call `collect_stats()` directly.
- Prefer a focused `article_stats_views.py` file instead of growing
  `article_views.py` further.
- Keep `task_key` deterministic for `feed_id` and `member_id` batch requests so
  duplicate in-flight tasks can be de-duplicated later if needed.
- If `member_id` resolves to zero subscribed feeds, create a completed-success
  task with `requested_count = 0` rather than treating it as an error.

## Suggested execution order

1. Implement the core stats service.
2. Add the sync refresh endpoint and schema.
3. Add the batch selector serializer and async task flow.
4. Add the batch API endpoint and schema.
5. Run the full verification block.

## Handoff

Plan complete and saved to
`docs/superpowers/plans/2026-04-04-we-rss-article-stats-refresh-implementation.md`.
Ready to execute?
