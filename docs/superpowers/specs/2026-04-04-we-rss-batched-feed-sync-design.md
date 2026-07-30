# We RSS batched feed sync design

This document redefines the We RSS public account sync flow so the backend
returns incremental results instead of waiting for one long-running task to
finish. The new flow keeps the current polling-based client model, but changes
feed sync from "one task scans the whole account" to "one run is made of many
short batch tasks." Each batch syncs at most 20 articles, writes those
articles immediately, and exposes the latest batch result through the task
detail API.

## Goals

This design focuses on user-visible progress, bounded execution time, and safe
task reuse. The backend must make sync progress visible after each batch so the
frontend can poll every 5 seconds and append new articles without waiting for a
full account scan.

- Return a parent sync task immediately.
- Process at most 20 articles per batch task.
- Persist articles after each completed batch.
- Let the frontend poll every 5 seconds for the latest batch result.
- Reuse an existing running parent task when a member clicks sync again.
- End stale or slow tasks with explicit timeout states.
- Distinguish full success, partial success, timeout, and failure.

## Non-goals

This design keeps the transport and client interaction model simple. It does
not introduce push channels or a frontend-driven pagination workflow.

- Do not add WebSocket or Server-Sent Events.
- Do not make the frontend request the next page manually.
- Do not re-run a new sync when the same feed already has a running parent
  task.
- Do not require the client to merge raw task histories from multiple tasks.

## Problems in the current flow

The current implementation creates one `feed_sync` task and lets it crawl pages
until the WeChat feed is exhausted. That model makes task runtime depend on the
size of the account and the number of article detail requests. A large account
can stay in `running` for a long time, and the frontend cannot tell whether the
task is still progressing, blocked, or effectively dead.

The current reuse rule also returns the existing running task for repeated sync
requests. That behavior is correct in principle, but today it causes a bad user
experience because a single stuck task prevents fresh work and never returns
incremental results.

## Proposed architecture

The new model splits one logical feed sync into a parent run task and multiple
short batch tasks. The parent task owns the overall state for the sync run. A
batch task performs one bounded unit of work, writes articles, updates the
parent, and then decides whether another batch is needed.

The system keeps polling as the only frontend interaction model:

1. The client calls `POST /api/v1/we-rss/feeds/{id}/sync/`.
2. The backend returns a parent sync run task immediately.
3. The client polls `GET /api/v1/we-rss/tasks/{task_id}/` every 5 seconds.
4. The backend exposes the latest completed batch in the parent task payload.
5. The client appends the new batch to the article list.
6. Polling stops when the parent reaches a terminal state.

## Task model

The current `WechatSyncTask` table is enough to hold the new design if task
types and payload fields are extended. This avoids adding a second task table.

The backend must support two feed-sync task types:

- `feed_sync_run`
  The parent task for one complete feed sync run.
- `feed_sync_batch`
  A child task that fetches at most 20 articles and then exits.

The parent task remains the only task the frontend needs to poll directly. The
child task is internal execution detail, but it is still persisted for audit,
debugging, and stale-task recovery.

### Parent task payload

The parent task must expose a stable progress contract in `result_payload`. The
frontend reads this payload every 5 seconds.

Recommended parent payload fields:

- `run_status`
  Values: `pending`, `running`, `success`, `partial_success`, `failed`,
  `timed_out`.
- `feed_id`
- `batch_size`
  Fixed to `20` in this version.
- `poll_after_seconds`
  Fixed to `5`.
- `has_more`
- `next_begin`
  The next publish-list offset to scan.
- `batches_completed`
- `batches_failed`
- `articles_synced`
- `articles_failed`
- `article_ids`
  Cumulative synced article IDs for the current run.
- `current_batch_task_id`
- `latest_completed_batch`
  The most recent successful batch payload, or `null`.
- `last_progress_at`
  Timestamp updated when a batch finishes.
- `timeout_reason`
  Empty unless the run ends in a timeout state.

### Latest completed batch payload

The frontend needs one compact structure that it can append directly to the UI
without diffing the entire feed. The parent payload therefore includes only the
latest completed batch, not the full batch history.

Recommended `latest_completed_batch` fields:

- `batch_no`
- `begin`
- `end`
- `has_more`
- `article_count`
- `article_ids`
- `articles`
  A list of article summaries for immediate UI append.
- `failed_articles`
  A list of article-level errors for this batch only.
- `started_at`
- `finished_at`

Each article summary should include:

- `id`
- `source_id`
- `title`
- `url`
- `publish_time`
- `pic_url`
- `status`

### Child task payload

Child tasks are internal, but they still need enough data to resume work and
debug failures.

Recommended child `request_payload` fields:

- `parent_task_id`
- `feed_id`
- `batch_no`
- `begin`
- `batch_size`
- `deadline_at`

Recommended child `result_payload` fields:

- `parent_task_id`
- `batch_no`
- `has_more`
- `next_begin`
- `article_count`
- `article_ids`
- `articles`
- `failed_articles`

## API behavior

The new flow keeps the existing endpoints, but changes the feed sync response
shape to always speak in terms of the parent task.

### `POST /api/v1/we-rss/feeds/{id}/sync/`

This endpoint remains the trigger for a feed sync run. It no longer represents
one monolithic fetch.

Behavior:

1. Look for an active parent task with `task_type=feed_sync_run` and the same
   `feed_id`.
2. If one exists and is not stale, return that task instead of creating a new
   run.
3. If none exists, create a new parent run task, then enqueue the first batch
   task.
4. Return the parent task immediately.

When a running task is reused, the response message must make that clear, for
example:

- `"A feed sync task is already running."`

The response data must include:

- `id`
- `task_type`
- `status`
- `message`
- `result_payload.poll_after_seconds = 5`

### `GET /api/v1/we-rss/tasks/{task_id}/`

This endpoint remains the frontend polling endpoint. The client does not need a
new polling API if the parent task serializer exposes the new payload fields.

Polling behavior:

- The frontend polls the parent task every 5 seconds.
- If `latest_completed_batch.batch_no` changes, the frontend appends that batch
  to the list.
- If `run_status` is terminal, polling stops.

Terminal parent run states:

- `success`
  The full feed is exhausted with no batch-level timeout.
- `partial_success`
  At least one batch succeeded, but the run ended with some batch failures.
- `failed`
  No useful batch completed, or a fatal error prevented progress.
- `timed_out`
  The run stopped because a batch or the total run exceeded a deadline.

## Batch execution flow

Each batch task must be short and deterministic. It reads the parent state,
fetches one bounded batch, writes articles, updates the parent, and exits.

Recommended execution flow:

1. Load the parent task and verify it is still runnable.
2. Read `next_begin`, `batch_size`, and timeout settings from the parent.
3. Request WeChat publish pages until either:
   - 20 unique articles are collected, or
   - no more articles are available.
4. For the collected articles, fetch article detail pages and parse them.
5. Upsert the articles and enqueue markdown refresh tasks as today.
6. Build the batch payload and write it to the child task result.
7. Update the parent task cumulative counters and `latest_completed_batch`.
8. If `has_more=true` and the run has not timed out, enqueue the next batch.
9. If no more data remains, mark the parent task as `success` or
   `partial_success`.

This design intentionally keeps page traversal server-side. The frontend only
observes progress; it does not own pagination state.

## Timeout and stale-task policy

Timeout handling must be explicit at both batch and run level. Returning a
permanent `running` task is not acceptable.

### Batch timeout

Each batch task must have a hard deadline, for example 90 seconds from batch
start. If the deadline is hit:

- Stop processing the current batch.
- Mark the child task as `failed` or `timed_out`.
- Update the parent with:
  - `run_status = timed_out` if no prior batch succeeded.
  - `run_status = partial_success` if earlier batches succeeded.
- Set `timeout_reason` with a clear machine-readable string.

### Total run timeout

Each parent run must also have a total deadline, for example 15 minutes from
run start. Once reached:

- Do not enqueue more batch tasks.
- Mark the parent as `timed_out` or `partial_success`, depending on completed
  batches.
- Return the already-synced results to the client.

### Stale running task recovery

The backend must detect active parent tasks that stopped making progress. A
task is stale if:

- `status = running`, and
- `last_progress_at` is older than the allowed inactivity window.

When `POST /feeds/{id}/sync/` sees a stale parent task, the backend must mark
that stale task as `timed_out` before creating a new parent run.

This rule prevents one bad run from locking the feed forever.

## Frontend integration contract

The frontend will continue to poll every 5 seconds. The backend must therefore
make every important state transition visible through the parent task detail.

Recommended frontend rules:

1. Call the sync endpoint once.
2. Store the returned parent `task_id`.
3. Poll the task detail every 5 seconds.
4. Append `latest_completed_batch.articles` only when `batch_no` changes.
5. Stop polling when `run_status` becomes terminal.
6. Show one of these final messages:
   - full success
   - partial success
   - timeout
   - failure

If the sync trigger returns an already-running parent task, the frontend must
show a message that a sync is already in progress and continue polling that
same task.

## Backward compatibility

This design changes feed sync semantics from "one task equals one full crawl"
to "one parent task equals one run made of many batches." Existing task APIs
can remain in place if serializers and task types are updated.

The main compatibility requirements are:

- Keep `POST /feeds/{id}/sync/`.
- Keep `GET /tasks/{task_id}/`.
- Preserve existing article persistence behavior.
- Preserve current tenant isolation and permission model.

The frontend will need to read the new parent payload fields, but it does not
need a new endpoint shape or push channel.

## Testing strategy

This design changes behavior, so tests must cover progress semantics, reuse,
and timeout handling rather than only final success.

Required coverage:

- Creating a new parent run returns immediately.
- Repeated sync calls return the same active parent task.
- Each batch processes at most 20 articles.
- Parent payload updates after each completed batch.
- The parent stops with `success` when no more data remains.
- The parent stops with `partial_success` when at least one batch succeeds and
  a later batch times out or fails.
- The parent stops with `timed_out` when no progress is made before deadline.
- Stale parent tasks are marked terminal and replaced by a new run.
- Task detail polling exposes the latest completed batch correctly.

## Open questions resolved for this version

This section records the product decisions already agreed in discussion so
implementation does not revisit them.

- The frontend will keep polling, not use push updates.
- The polling interval is 5 seconds.
- The backend returns the current running parent task if the same feed is
  already syncing.
- A batch contains 20 articles in this version.

## Next steps

The next implementation plan should update the task model semantics, extend the
task serializer payload contract, split feed sync into parent and batch tasks,
and add timeout recovery before changing the frontend integration logic.
