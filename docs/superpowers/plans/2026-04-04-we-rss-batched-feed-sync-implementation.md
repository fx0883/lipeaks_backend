# We RSS batched feed sync implementation plan

> **For agentic workers:** REQUIRED: Use
> superpowers:subagent-driven-development (if subagents available) or
> superpowers:executing-plans to implement this plan. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Replace the current one-task full-account feed sync with a parent
`feed_sync_run` task plus chained `feed_sync_batch` tasks so the backend
returns immediately, syncs at most 20 articles per batch, exposes incremental
progress every 5 seconds, reuses a non-stale running parent task, and returns a
terminal result on timeout instead of hanging forever.

**Architecture:** Keep `POST /api/v1/we-rss/feeds/{id}/sync/` and
`GET /api/v1/we-rss/tasks/{task_id}/` as the only frontend integration points.
The sync endpoint creates or reuses one parent task that owns progress state in
`result_payload`. Each child batch task fetches one bounded article increment,
upserts articles, updates the parent payload, and either dispatches the next
batch or marks the parent as terminal. Legacy `feed_sync` rows are treated as
stale blockers and must not prevent new batched runs.

**Tech Stack:** Django, Django REST Framework, drf-spectacular,
`WechatSyncTask`, Celery or local executor via `dispatch_we_rss_task`, Django
test runner, existing `we_rss` tenant-scoped services and models.

---

## Context and source of truth

This plan implements the approved design in:

- `docs/superpowers/specs/2026-04-04-we-rss-batched-feed-sync-design.md`

The implementation must preserve these product decisions:

- The frontend keeps polling instead of using WebSocket or SSE.
- The polling interval is 5 seconds.
- One batch syncs at most 20 articles.
- The backend returns the currently running parent task when one already exists
  for the same feed and is not stale.
- The backend must return a terminal state for timeout and stale-task cases.
- The frontend only needs the parent task plus the latest completed batch.

## File structure map

Map the work up front so the batching logic stays coherent and testable.

### Task model and dispatch files

- Modify: `we_rss/models.py`
- Create: `we_rss/migrations/0007_expand_feed_sync_task_types_and_statuses.py`
- Modify: `we_rss/services/task_service.py`
- Modify: `we_rss/tasks.py`

### Feed sync service and API files

- Modify: `we_rss/services/feed_service.py`
- Modify: `we_rss/serializers.py`
- Modify: `we_rss/views/feed_views.py`
- Modify: `we_rss/views/article_views.py`
- Modify: `we_rss/schema.py`

### Test files

- Modify: `we_rss/tests/test_feed_gateway_pagination.py`
- Modify: `we_rss/tests/test_task_workflows.py`
- Modify: `we_rss/tests/test_feeds_api.py`
- Modify: `we_rss/tests/test_articles_api.py`
- Modify: `we_rss/tests/test_schema.py`

## Implementation constraints

These rules keep the new flow aligned with the approved design.

- Use @superpowers:test-driven-development for each behavior change.
- Do not keep the old monolithic `run_feed_sync_task` flow as the primary path.
- Use `feed_sync_run` for the frontend-visible parent task.
- Use `feed_sync_batch` for child tasks only.
- Keep `TaskService.ACTIVE_STATUSES` limited to active states only.
- Add terminal task states for `partial_success` and `timed_out`.
- Store frontend progress on the parent task in `result_payload`.
- Return only the latest completed batch payload, not the full batch history.
- Preserve article upsert and markdown-refresh behavior from the current sync.
- Detect and retire stale running parent tasks before creating a new run.
- Legacy `feed_sync` rows must not block a new batched sync.
- Keep all lookups tenant-scoped.

## Chunk 1: Parent task contract and stale-task recovery

This chunk establishes the new task semantics before any batch execution code
is written. The endpoint must start returning a parent run task immediately,
and repeated sync calls must either reuse that active parent or replace a stale
one cleanly.

### Task 1: Add failing API and workflow tests for parent-run creation and reuse

**Files:**

- Modify: `we_rss/tests/test_feeds_api.py`
- Modify: `we_rss/tests/test_task_workflows.py`
- Test: `we_rss/services/feed_service.py`
- Test: `we_rss/services/task_service.py`

- [ ] **Step 1: Write the failing tests**

```python
@patch("we_rss.services.feed_service.dispatch_we_rss_task")
def test_feed_sync_creates_parent_run_task_with_polling_contract(
    self,
    mock_dispatch,
):
    response = self.client.post(f"/api/v1/we-rss/feeds/{feed.id}/sync/")
    task = WechatSyncTask.objects.get(id=response.data["data"]["id"])

    self.assertEqual(response.status_code, 200)
    self.assertEqual(task.task_type, "feed_sync_run")
    self.assertEqual(task.status, "running")
    self.assertEqual(task.result_payload["run_status"], "running")
    self.assertEqual(task.result_payload["batch_size"], 20)
    self.assertEqual(task.result_payload["poll_after_seconds"], 5)
    mock_dispatch.assert_called_once()

def test_feed_sync_returns_existing_running_parent_task(self):
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
        result_payload={"last_progress_at": "2026-04-04T10:00:00Z"},
        created_by=self.member,
    )

    with patch("we_rss.services.feed_service.dispatch_we_rss_task"):
        task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

    stale.refresh_from_db()
    self.assertEqual(stale.status, "timed_out")
    self.assertEqual(task.task_type, "feed_sync_run")
    self.assertNotEqual(task.id, stale.id)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_feeds_api.FeedApiTests.test_feed_sync_creates_parent_run_task_with_polling_contract we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_returns_existing_running_parent_task we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_replaces_stale_legacy_feed_sync_task -v 2`

Expected: FAIL because the code still creates `feed_sync`, has no stale-task
recovery, and does not seed the parent polling payload.

- [ ] **Step 3: Implement the parent run contract**

Modify:

- `we_rss/models.py`
- `we_rss/migrations/0007_expand_feed_sync_task_types_and_statuses.py`
- `we_rss/services/task_service.py`
- `we_rss/services/feed_service.py`

Implementation requirements:

- Add `FEED_SYNC_RUN` and `FEED_SYNC_BATCH` to
  `WechatSyncTask.TaskType`.
- Add `PARTIAL_SUCCESS` and `TIMED_OUT` to `WechatSyncTask.Status`.
- Add `TaskService.mark_partial_success(...)`,
  `TaskService.mark_timed_out(...)`, and a stale-task helper that reads
  `result_payload.last_progress_at`, `started_at`, or `updated_at`.
- Add feed sync constants in `feed_service.py` for:
  - `BATCH_SIZE = 20`
  - `POLL_AFTER_SECONDS = 5`
  - `BATCH_TIMEOUT_SECONDS = 90`
  - `RUN_TIMEOUT_SECONDS = 900`
  - `STALE_AFTER_SECONDS`
- Replace `FeedService.sync_feed()` so it:
  - finds an active non-stale parent run task first
  - times out stale `feed_sync_run` and legacy `feed_sync` tasks
  - creates a new parent task with `status="running"`
  - seeds `request_payload` and `result_payload`
  - enqueues the first batch task
- Update the reused parent task message to:
  `"A feed sync task is already running."`

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_feeds_api.FeedApiTests.test_feed_sync_creates_parent_run_task_with_polling_contract we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_returns_existing_running_parent_task we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_replaces_stale_legacy_feed_sync_task -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/models.py we_rss/migrations/0007_expand_feed_sync_task_types_and_statuses.py we_rss/services/task_service.py we_rss/services/feed_service.py we_rss/tests/test_feeds_api.py we_rss/tests/test_task_workflows.py
git commit -m "feat: add parent feed sync run task contract"
```

### Task 2: Add failing schema tests for the new task vocabulary

**Files:**

- Modify: `we_rss/tests/test_schema.py`
- Test: `we_rss/schema.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_task_schema_documents_batched_feed_sync_types(self):
    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/we-rss/tasks/"]["get"]
    task_type_param = next(
        item for item in operation["parameters"] if item["name"] == "task_type"
    )

    self.assertIn("feed_sync_run", task_type_param["description"])
    self.assertIn("feed_sync_batch", task_type_param["description"])

def test_feed_sync_example_uses_parent_run_payload(self):
    schema = SchemaGenerator().get_schema(request=None, public=True)
    example = schema["paths"]["/api/v1/we-rss/feeds/{id}/sync/"]["post"][
        "responses"
    ]["200"]["content"]["application/json"]["examples"][
        "FeedSyncSuccessResponse"
    ]["value"]

    self.assertEqual(example["data"]["task_type"], "feed_sync_run")
    self.assertEqual(example["data"]["result_payload"]["poll_after_seconds"], 5)
    self.assertIn("latest_completed_batch", example["data"]["result_payload"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_schema.WeRssSchemaTests.test_task_schema_documents_batched_feed_sync_types we_rss.tests.test_schema.WeRssSchemaTests.test_feed_sync_example_uses_parent_run_payload -v 2`

Expected: FAIL because the schema still documents `feed_sync` as one monolithic
task.

- [ ] **Step 3: Update schema constants and task descriptions**

Modify `we_rss/schema.py` so it:

- documents `feed_sync_run` and `feed_sync_batch` in `TASK_TYPE_PARAMETER`
- documents `partial_success` and `timed_out` in `TASK_STATUS_PARAMETER`
- rewrites `FEED_SYNC_TASK_EXAMPLE` as a parent run example
- adds a second example that shows a reused running parent task
- includes `poll_after_seconds`, `batch_size`, `has_more`,
  `current_batch_task_id`, and `latest_completed_batch`

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_schema.WeRssSchemaTests.test_task_schema_documents_batched_feed_sync_types we_rss.tests.test_schema.WeRssSchemaTests.test_feed_sync_example_uses_parent_run_payload -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/schema.py we_rss/tests/test_schema.py
git commit -m "docs: describe batched feed sync task types"
```

## Chunk 2: Gateway-level batch collection

This chunk replaces the crawl-until-empty gateway path with a bounded collector
that can stop after 20 unique articles and report the next `begin` offset.

### Task 3: Add failing gateway tests for one bounded publish batch

**Files:**

- Modify: `we_rss/tests/test_feed_gateway_pagination.py`
- Test: `we_rss/services/feed_service.py`

- [ ] **Step 1: Write the failing tests**

```python
@patch("we_rss.services.feed_service.requests.Session")
def test_collect_feed_batch_returns_at_most_twenty_articles(self, mock_session_cls):
    session = mock_session_cls.return_value
    session.get.side_effect = build_publish_and_article_side_effects(total=23)

    payload = WechatFeedGateway(page_size=5).collect_feed_batch(
        self.feed,
        self.credential,
        begin=0,
        batch_size=20,
        deadline_at=None,
    )

    self.assertEqual(len(payload["articles"]), 20)
    self.assertTrue(payload["has_more"])
    self.assertEqual(payload["next_begin"], 20)

@patch("we_rss.services.feed_service.requests.Session")
def test_collect_feed_batch_returns_terminal_page_when_publish_list_is_exhausted(
    self,
    mock_session_cls,
):
    session = mock_session_cls.return_value
    session.get.side_effect = build_publish_and_article_side_effects(total=7)

    payload = WechatFeedGateway(page_size=5).collect_feed_batch(
        self.feed,
        self.credential,
        begin=0,
        batch_size=20,
        deadline_at=None,
    )

    self.assertEqual(len(payload["articles"]), 7)
    self.assertFalse(payload["has_more"])
    self.assertEqual(payload["next_begin"], 7)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_feed_gateway_pagination.FeedGatewayPaginationTests.test_collect_feed_batch_returns_at_most_twenty_articles we_rss.tests.test_feed_gateway_pagination.FeedGatewayPaginationTests.test_collect_feed_batch_returns_terminal_page_when_publish_list_is_exhausted -v 2`

Expected: FAIL because `WechatFeedGateway` only exposes the monolithic
`sync_feed()` method today.

- [ ] **Step 3: Implement the bounded batch collector**

Modify `we_rss/services/feed_service.py` and add a new gateway method:

- `WechatFeedGateway.collect_feed_batch(feed, credential, begin, batch_size,
  deadline_at)`

Behavior requirements:

- fetch publish pages starting from `begin`
- stop after collecting `batch_size` unique article candidates
- preserve dedupe by normalized article URL
- fetch detail pages only for the collected candidates
- return:
  - `articles`
  - `feed_payload`
  - `failed_articles`
  - `has_more`
  - `next_begin`
  - `detail_success_count`
  - `detail_failed_count`
- keep the existing throttle behavior between page and article requests

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_feed_gateway_pagination.FeedGatewayPaginationTests.test_collect_feed_batch_returns_at_most_twenty_articles we_rss.tests.test_feed_gateway_pagination.FeedGatewayPaginationTests.test_collect_feed_batch_returns_terminal_page_when_publish_list_is_exhausted -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/feed_service.py we_rss/tests/test_feed_gateway_pagination.py
git commit -m "feat: add bounded feed batch collection"
```

## Chunk 3: Batch worker orchestration and timeout paths

This chunk wires the gateway collector into task execution. Each child batch
must upsert articles, update the parent increment, and either queue the next
batch or finish the parent task with a terminal state.

### Task 4: Add failing workflow tests for incremental parent updates

**Files:**

- Modify: `we_rss/tests/test_task_workflows.py`
- Test: `we_rss/services/feed_service.py`
- Test: `we_rss/tasks.py`

- [ ] **Step 1: Write the failing tests**

```python
@patch("we_rss.tasks.get_feed_gateway", return_value=FakeBatchedFeedGateway())
def test_feed_sync_batch_updates_parent_and_enqueues_next_batch(self, _mock_gateway):
    parent = FeedService.sync_feed(feed=self.feed, created_by=self.member)
    parent.refresh_from_db()

    self.assertEqual(parent.task_type, "feed_sync_run")
    self.assertEqual(parent.status, "running")
    self.assertEqual(parent.result_payload["batches_completed"], 1)
    self.assertTrue(parent.result_payload["has_more"])
    self.assertEqual(
        parent.result_payload["latest_completed_batch"]["batch_no"],
        1,
    )
    self.assertEqual(
        len(parent.result_payload["latest_completed_batch"]["articles"]),
        20,
    )
    self.assertIsNotNone(parent.result_payload["current_batch_task_id"])

@patch("we_rss.tasks.get_feed_gateway", return_value=FakeFinalBatchFeedGateway())
def test_feed_sync_final_batch_marks_parent_success(self, _mock_gateway):
    parent = FeedService.sync_feed(feed=self.feed, created_by=self.member)
    parent.refresh_from_db()

    self.assertEqual(parent.status, "success")
    self.assertEqual(parent.result_payload["run_status"], "success")
    self.assertFalse(parent.result_payload["has_more"])
    self.assertEqual(parent.result_payload["articles_synced"], 7)

@patch("we_rss.tasks.get_feed_gateway", return_value=FakeTimeoutOnSecondBatchGateway())
def test_feed_sync_timeout_marks_parent_partial_success(self, _mock_gateway):
    parent = FeedService.sync_feed(feed=self.feed, created_by=self.member)
    parent.refresh_from_db()

    self.assertEqual(parent.status, "partial_success")
    self.assertEqual(parent.result_payload["run_status"], "partial_success")
    self.assertEqual(parent.result_payload["timeout_reason"], "batch_timeout")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_batch_updates_parent_and_enqueues_next_batch we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_final_batch_marks_parent_success we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_timeout_marks_parent_partial_success -v 2`

Expected: FAIL because there is no `feed_sync_batch` worker, no parent payload
aggregation, and no timeout path.

- [ ] **Step 3: Implement the batch worker and parent aggregation**

Modify:

- `we_rss/tasks.py`
- `we_rss/services/feed_service.py`

Implementation requirements:

- Replace the old `run_feed_sync_task` dispatch path with
  `run_feed_sync_batch_task`.
- When a parent run is created, create batch task `#1` and dispatch it.
- Add `FeedService.execute_sync_batch(...)` that:
  - loads the parent and child task
  - aborts if the parent is already terminal
  - enforces the total run timeout and per-batch timeout
  - calls `gateway.collect_feed_batch(...)`
  - upserts the batch articles
  - updates feed timestamps and feed metadata from `feed_payload`
  - writes child `result_payload`
  - updates parent `result_payload` with:
    - `run_status`
    - `has_more`
    - `next_begin`
    - `batches_completed`
    - `batches_failed`
    - `articles_synced`
    - `articles_failed`
    - `article_ids`
    - `current_batch_task_id`
    - `latest_completed_batch`
    - `last_progress_at`
    - `timeout_reason`
- Queue the next child task only when:
  - the batch completed
  - `has_more` is true
  - the parent has not hit the total run timeout
- Mark the parent:
  - `success` when no more articles remain and no failure occurred
  - `partial_success` when some batches succeeded but a later batch failed or
    timed out
  - `timed_out` when no batch produced useful progress before deadline

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_batch_updates_parent_and_enqueues_next_batch we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_final_batch_marks_parent_success we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_timeout_marks_parent_partial_success -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/tasks.py we_rss/services/feed_service.py we_rss/tests/test_task_workflows.py
git commit -m "feat: chain feed sync batch tasks through parent run"
```

### Task 5: Add failing workflow tests for disabled-Celery chaining

**Files:**

- Modify: `we_rss/tests/test_task_workflows.py`
- Test: `we_rss/services/feed_service.py`

- [ ] **Step 1: Write the failing test**

```python
@override_settings(
    CELERY_ENABLED=False,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
def test_feed_sync_run_dispatches_batch_worker_in_background_when_celery_disabled(
    self,
):
    with patch("we_rss.services.feed_service.dispatch_we_rss_task") as mock_dispatch:
        task = FeedService.sync_feed(feed=self.feed, created_by=self.member)

    self.assertEqual(task.status, "running")
    mock_dispatch.assert_called_once()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
`python manage.py test we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_run_dispatches_batch_worker_in_background_when_celery_disabled -v 2`

Expected: FAIL until the new parent-run path dispatches a child batch worker
instead of trying to execute synchronously.

- [ ] **Step 3: Re-check the dispatch path for the new worker**

Update `FeedService.sync_feed()` and any follow-up batch scheduling helpers so
every batch uses `dispatch_we_rss_task(run_feed_sync_batch_task, task.id)`.
Do not call the worker body directly.

- [ ] **Step 4: Run the test to verify it passes**

Run:
`python manage.py test we_rss.tests.test_task_workflows.WeRssTaskWorkflowTests.test_feed_sync_run_dispatches_batch_worker_in_background_when_celery_disabled -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/feed_service.py we_rss/tests/test_task_workflows.py
git commit -m "fix: dispatch feed sync batches through background worker"
```

## Chunk 4: Polling payload contract and endpoint documentation

This chunk makes the parent payload safe for frontend polling. The frontend
must be able to learn whether a task is already running, which batch just
finished, and whether polling should stop.

### Task 6: Add failing API tests for task-detail polling payload

**Files:**

- Modify: `we_rss/tests/test_articles_api.py`
- Test: `we_rss/serializers.py`
- Test: `we_rss/views/article_views.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_task_detail_returns_latest_completed_batch_payload(self):
    task = WechatSyncTask.objects.create(
        tenant=self.tenant,
        task_type="feed_sync_run",
        status="running",
        target_type="feed",
        target_id=self.feed.id,
        result_payload={
            "run_status": "running",
            "poll_after_seconds": 5,
            "latest_completed_batch": {
                "batch_no": 2,
                "article_count": 3,
                "articles": [{"id": 1, "title": "A"}],
            },
        },
        created_by=self.member,
    )

    response = self.client.get(f"/api/v1/we-rss/tasks/{task.id}/")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data["data"]["task_type"], "feed_sync_run")
    self.assertEqual(
        response.data["data"]["result_payload"]["latest_completed_batch"][
            "batch_no"
        ],
        2,
    )

def test_task_detail_surfaces_timed_out_parent_status(self):
    task = WechatSyncTask.objects.create(
        tenant=self.tenant,
        task_type="feed_sync_run",
        status="timed_out",
        target_type="feed",
        target_id=self.feed.id,
        result_payload={"run_status": "timed_out", "timeout_reason": "run_timeout"},
        created_by=self.member,
    )

    response = self.client.get(f"/api/v1/we-rss/tasks/{task.id}/")
    self.assertEqual(response.data["data"]["status"], "timed_out")
    self.assertEqual(
        response.data["data"]["result_payload"]["timeout_reason"],
        "run_timeout",
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_articles_api.ArticleTaskApiTests.test_task_detail_returns_latest_completed_batch_payload we_rss.tests.test_articles_api.ArticleTaskApiTests.test_task_detail_surfaces_timed_out_parent_status -v 2`

Expected: FAIL because the current task examples and task vocabulary do not yet
cover the new parent payload contract.

- [ ] **Step 3: Update serializers and endpoint descriptions**

Modify:

- `we_rss/serializers.py`
- `we_rss/views/feed_views.py`
- `we_rss/views/article_views.py`
- `we_rss/schema.py`

Implementation requirements:

- Keep `WechatSyncTaskSerializer` as the parent polling serializer.
- If a helper field is needed, add a serializer method that keeps
  `latest_completed_batch` and timeout metadata stable even when
  `result_payload` is `null`.
- Update sync endpoint descriptions so they say the response is a parent run
  task and may represent an already-running sync.
- Update task-detail descriptions so they explicitly tell the frontend to poll
  the parent every 5 seconds and append only when
  `latest_completed_batch.batch_no` changes.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_articles_api.ArticleTaskApiTests.test_task_detail_returns_latest_completed_batch_payload we_rss.tests.test_articles_api.ArticleTaskApiTests.test_task_detail_surfaces_timed_out_parent_status -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/serializers.py we_rss/views/feed_views.py we_rss/views/article_views.py we_rss/schema.py we_rss/tests/test_articles_api.py
git commit -m "feat: document parent task polling payload"
```

### Task 7: Add failing schema tests for incremental batch examples

**Files:**

- Modify: `we_rss/tests/test_schema.py`
- Test: `we_rss/schema.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_feed_sync_example_includes_latest_completed_batch_summary(self):
    schema = SchemaGenerator().get_schema(request=None, public=True)
    example = schema["paths"]["/api/v1/we-rss/tasks/{task_id}/"]["get"][
        "responses"
    ]["200"]["content"]["application/json"]["examples"][
        "FeedSyncTaskSuccessResponse"
    ]["value"]

    payload = example["data"]["result_payload"]
    self.assertEqual(payload["poll_after_seconds"], 5)
    self.assertIn("latest_completed_batch", payload)
    self.assertIn("articles", payload["latest_completed_batch"])

def test_feed_sync_timeout_example_is_terminal(self):
    schema = SchemaGenerator().get_schema(request=None, public=True)
    example = schema["paths"]["/api/v1/we-rss/tasks/{task_id}/"]["get"][
        "responses"
    ]["200"]["content"]["application/json"]["examples"][
        "FeedSyncTaskTimedOutResponse"
    ]["value"]

    self.assertEqual(example["data"]["status"], "timed_out")
    self.assertEqual(example["data"]["result_payload"]["run_status"], "timed_out")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_schema.WeRssSchemaTests.test_feed_sync_example_includes_latest_completed_batch_summary we_rss.tests.test_schema.WeRssSchemaTests.test_feed_sync_timeout_example_is_terminal -v 2`

Expected: FAIL because the schema still shows final-only monolithic sync
payloads.

- [ ] **Step 3: Expand the examples**

Update `we_rss/schema.py` so the task-detail examples include:

- one running parent run with `latest_completed_batch`
- one success example with `has_more = false`
- one timeout example with `status = timed_out`
- one partial-success example after an earlier successful batch

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_schema.WeRssSchemaTests.test_feed_sync_example_includes_latest_completed_batch_summary we_rss.tests.test_schema.WeRssSchemaTests.test_feed_sync_timeout_example_is_terminal -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/schema.py we_rss/tests/test_schema.py
git commit -m "docs: add incremental feed sync polling examples"
```

## Chunk 5: Full verification

This chunk proves the new flow works end to end and that the old hanging
behavior is gone for batched feed sync as well.

### Task 8: Run focused regressions and cleanup

**Files:**

- Modify: any implementation files required to fix regressions
- Test: `we_rss/tests/test_feed_gateway_pagination.py`
- Test: `we_rss/tests/test_task_workflows.py`
- Test: `we_rss/tests/test_feeds_api.py`
- Test: `we_rss/tests/test_articles_api.py`
- Test: `we_rss/tests/test_schema.py`

- [ ] **Step 1: Run the focused batched-sync suite**

Run:
`python manage.py test we_rss.tests.test_feed_gateway_pagination we_rss.tests.test_task_workflows we_rss.tests.test_feeds_api we_rss.tests.test_articles_api we_rss.tests.test_schema -v 2`

Expected: all feed-sync batching coverage passes.

- [ ] **Step 2: Run the broader `we_rss` regression slice**

Run:
`python manage.py test we_rss.tests -v 2`

Expected: all existing `we_rss` tests still pass after the task-type and
status changes.

- [ ] **Step 3: Verify migrations**

Run:
`python manage.py makemigrations we_rss --check`

Expected: no pending model drift beyond
`0007_expand_feed_sync_task_types_and_statuses.py`.

- [ ] **Step 4: Verify schema generation**

Run:
`python manage.py spectacular --file schema.yml`

Expected: schema generation completes and includes the parent-run task
examples.

- [ ] **Step 5: Commit the completed feature**

```bash
git add we_rss docs/superpowers/specs/2026-04-04-we-rss-batched-feed-sync-design.md docs/superpowers/plans/2026-04-04-we-rss-batched-feed-sync-implementation.md schema.yml
git commit -m "feat: add batched feed sync parent run workflow"
```

## Open implementation notes

These notes close the remaining design gaps before execution starts.

- The parent task should be marked `running` immediately when it is created so
  the frontend never sees a long-lived `pending` parent.
- A child batch task should store its own result payload for debugging, but the
  frontend should continue polling only the parent task.
- If a batch times out after some articles were already persisted, surface that
  increment through `latest_completed_batch` before marking the parent
  `partial_success` or `timed_out`.
- The active-task lookup should search both `feed_sync_run` and legacy
  `feed_sync` rows when cleaning stale blockers.
- Update any tests or docs that still hard-code `feed_sync` as the feed task
  type.

## Suggested execution order

Follow the chunks in order.

1. Parent task contract and stale-task recovery.
2. Gateway-level bounded batch collection.
3. Batch worker orchestration and timeout handling.
4. Polling payload contract and schema updates.
5. Full regression verification.

## Handoff

Plan complete and saved to
`docs/superpowers/plans/2026-04-04-we-rss-batched-feed-sync-implementation.md`.
Ready to execute?
