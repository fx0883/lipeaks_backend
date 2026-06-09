# LLM gateway design

This document defines an internal `llm_gateway` Django app for
`lipeaks_backend`. The app gives other Django apps one stable service layer for
LLM-backed capabilities without exposing any new HTTP endpoints of its own.

The first shipped capability is WeChat article search. Internally, the app uses
`PydanticAI` for orchestration and prefers `codex` CLI for execution, with
`claude` CLI available as a fallback executor. The app treats skills, prompts,
CLI execution, and result normalization as internal implementation details.

## Goals

This design introduces a reusable internal LLM capability layer that other apps
can call without knowing anything about skills or CLI runtimes.

- Add a new internal-only Django app named `llm_gateway`.
- Keep all integration behind Python service methods instead of public APIs.
- Let the app discover global shared skills from the local machine.
- Let the app orchestrate skill execution through `PydanticAI`.
- Prefer `codex` CLI as the default executor.
- Support `claude` CLI as a fallback or explicit override.
- Persist run state and event history in the Django database.
- Support asynchronous execution through the existing Celery setup.
- Support synchronous fallback when Celery is disabled.
- Return normalized capability results to calling apps.

## Non-goals

This first version intentionally keeps the scope narrow.

- Do not expose new REST or WebSocket endpoints from `llm_gateway`.
- Do not let business apps pass arbitrary skill names directly.
- Do not let business apps build their own prompts.
- Do not let models decide raw shell commands, file paths, or permissions.
- Do not implement a generic external skill marketplace.
- Do not introduce tenant-facing configuration UI in this version.
- Do not add user-facing streaming endpoints inside this app.

## Scope

This design covers the internal execution path required for capability-style
LLM tasks driven by shared skills.

1. Discover global shared skills from well-known local directories.
2. Route one internal capability to an execution plan.
3. Use `PydanticAI` to build executor instructions and normalize output.
4. Execute runs through `codex` CLI or `claude` CLI.
5. Persist run status, result payloads, and event logs.
6. Expose a Python service surface for other Django apps.

## Current project context

`lipeaks_backend` is a Django 5.2 project with many root-level apps registered
directly in `INSTALLED_APPS`, as shown in
[`core/settings.py`](/D:/GitHub/lipeaks_backend/core/settings.py). The project
already uses Celery and supports synchronous fallback when Celery is disabled.

The current Celery configuration in
[`core/settings.py`](/D:/GitHub/lipeaks_backend/core/settings.py#L559) and
[`core/celery.py`](/D:/GitHub/lipeaks_backend/core/celery.py) is important for
this design. It means `llm_gateway` does not need a new async framework. It can
follow the same pattern that `we_rss` already uses in
[`we_rss/services/task_service.py`](/D:/GitHub/lipeaks_backend/we_rss/services/task_service.py).

The machine environment already has shared skill directories and working CLI
executors. The design therefore treats local skill discovery and CLI execution
as first-class behavior rather than optional extensions.

## Proposed architecture

The new app lives as its own root-level Django app named `llm_gateway`. It is
not a public API app. Other apps call its Python services directly.

Recommended file structure changes:

- Create `llm_gateway/__init__.py`
- Create `llm_gateway/apps.py`
- Create `llm_gateway/admin.py`
- Create `llm_gateway/models.py`
- Create `llm_gateway/tasks.py`
- Create `llm_gateway/domain/enums.py`
- Create `llm_gateway/domain/entities.py`
- Create `llm_gateway/schemas/requests.py`
- Create `llm_gateway/schemas/results.py`
- Create `llm_gateway/schemas/events.py`
- Create `llm_gateway/services/gateway.py`
- Create `llm_gateway/services/capability_router.py`
- Create `llm_gateway/services/run_manager.py`
- Create `llm_gateway/services/catalog.py`
- Create `llm_gateway/services/normalizer.py`
- Create `llm_gateway/orchestration/agent.py`
- Create `llm_gateway/orchestration/prompts.py`
- Create `llm_gateway/executors/base.py`
- Create `llm_gateway/executors/process.py`
- Create `llm_gateway/executors/codex.py`
- Create `llm_gateway/executors/claude.py`
- Create `llm_gateway/repositories/runs.py`
- Create `llm_gateway/repositories/events.py`
- Create `llm_gateway/migrations/0001_initial.py`
- Modify `core/settings.py`
- Create `llm_gateway/tests/`

The app splits responsibilities into five layers:

- Business-facing service methods in `services/gateway.py`
- Capability and run orchestration in `services/*`
- LLM planning in `orchestration/*`
- CLI execution in `executors/*`
- Persistence in `models.py` and `repositories/*`

## Internal service boundary

Business apps only interact with `llm_gateway` through capability methods. They
define input and expected output, but they do not control prompts, skills,
executors, or shell commands.

For example, a calling app should request:

- `search_wechat_articles(query="Claude Code skills", limit=20)`

It must not request:

- `run_skill("wechat-article-search", payload=...)`

This boundary keeps the implementation replaceable. Today, WeChat article
search might use the `wechat-article-search` skill. In the future, the same
capability could switch to another skill, another prompt strategy, or a direct
integration without forcing business apps to change.

## Capability routing

Capability routing maps a business request to an internal execution plan.

Each capability definition stores:

- Capability name
- Input schema
- Output schema
- Allowed executors
- Preferred executor
- Streaming support
- Default timeout
- Skill hints or prompt hints

The first capability is `wechat_article_search`.

Recommended defaults for `wechat_article_search`:

- Preferred executor: `codex`
- Allowed executors: `codex`, `claude`
- Streaming enabled: yes
- Default timeout: 180 seconds
- Result schema: `WechatArticleSearchResult`
- Internal skill hint: `wechat-article-search`

## Global skill discovery

`llm_gateway` discovers globally shared skills from the local machine and keeps
that discovery logic centralized in `services/catalog.py`.

Discovery targets:

- `C:\Users\Administrator\.agents\skills`
- `C:\Users\Administrator\.codex\skills`

Discovery behavior:

- Enumerate skill directories.
- Read `SKILL.md` when present.
- Extract the skill name and description.
- Record the source directory and path.
- Mark the skill as globally shared.

Discovery is internal metadata, not a public business contract. Business apps
do not browse or choose skills directly.

## Execution flow

This section describes one full request lifecycle using WeChat article search.

1. A business app calls `gateway.search_wechat_articles(...)`.
2. `services/gateway.py` builds a capability request object.
3. `services/run_manager.py` creates an `LLMRun` record.
4. `tasks.py` schedules execution through Celery.
5. If Celery is disabled, the run executes inline using the project's existing
   sync-fallback pattern.
6. `services/capability_router.py` resolves the execution plan.
7. `orchestration/agent.py` uses `PydanticAI` to generate executor
   instructions.
8. `executors/codex.py` runs the task first.
9. If `codex` is unavailable or fails in a retryable way,
   `executors/claude.py` becomes the fallback executor.
10. Streaming stdout and stderr lines are stored as `LLMRunEvent` records.
11. `services/normalizer.py` converts the final output into a capability result.
12. `services/gateway.py` returns the normalized result to the calling app.

## Role of PydanticAI

`PydanticAI` participates in orchestration, not raw execution.

It is responsible for:

- Translating business input into a clear executor instruction
- Refining search intent when needed
- Choosing between allowed executors within hard rules
- Building structured prompts
- Enforcing output schemas
- Repairing malformed final output when the repair is safe and bounded

It is not responsible for:

- Starting shell processes
- Choosing arbitrary file paths
- Expanding permissions
- Deciding whether a capability is allowed
- Persisting run state directly

This split keeps model intelligence in the planning layer while keeping
security and execution in deterministic code.

## Executor strategy

The app supports two CLI executors.

### Codex executor

`codex` is the default and preferred executor for all capabilities in the first
version. The executor is responsible for:

- Building the `codex exec` command
- Passing the working directory
- Injecting the final prompt
- Optionally passing an output schema file
- Capturing stdout and stderr
- Reporting exit status and timing

### Claude executor

`claude` is the secondary executor. It is used when:

- A capability explicitly requests it
- `codex` is unavailable
- `codex` fails in a fallback-eligible way

### Shared process layer

Both executors share process management code that handles:

- Windows-safe subprocess startup
- Text decoding
- Timeout enforcement
- Incremental stream reads
- Cancellation
- Exit-code collection

## Data model

The app needs one model for run state and one model for event history.

### `LLMRun`

`LLMRun` stores one internal capability execution.

Fields:

- `capability`
- `status`
- `preferred_executor`
- `selected_executor`
- `input_payload`
- `result_payload`
- `error_message`
- `exit_code`
- `celery_task_id`
- `started_at`
- `finished_at`
- `duration_ms`
- `requested_by_app`
- `created_at`
- `updated_at`

Behavior:

- One row represents one business-level run.
- Status changes are explicit and ordered.
- `preferred_executor` stores the routing preference.
- `selected_executor` stores the executor that actually ran last.
- `result_payload` stores the normalized business result, not just raw output.

Recommended statuses:

- `pending`
- `running`
- `completed`
- `failed`
- `cancelled`
- `timed_out`

### `LLMRunEvent`

`LLMRunEvent` stores one event emitted during execution.

Fields:

- `run`
- `sequence`
- `event_type`
- `payload`
- `created_at`

Recommended event types:

- `run.created`
- `run.started`
- `executor.stdout`
- `executor.stderr`
- `run.progress`
- `run.completed`
- `run.failed`
- `run.cancelled`

## Result normalization

Executors may return raw markdown, plain text, JSON-looking text, or mixed
logs. The normalizer makes output safe for business apps to consume.

Normalization responsibilities:

- Parse structured final output when available.
- Preserve raw output for debugging.
- Emit one stable result shape per capability.
- Include executor metadata.
- Distinguish final business result from transport metadata.

For `wechat_article_search`, the normalized result should contain:

- `items`
- `total`
- `query`
- `executor`
- `used_skill`
- `raw_text` when available for debugging

## Task execution model

The app reuses the project's existing Celery conventions.

Execution rules:

- When `CELERY_ENABLED=True`, create background tasks through Celery.
- When `CELERY_ENABLED=False`, execute synchronously in-process.
- Keep one code path for business semantics regardless of async mode.
- Persist status transitions in both modes.

This keeps local development simple and aligns with how `we_rss` already
handles task dispatch.

## Streaming model

`llm_gateway` does not expose streaming endpoints itself, but it does persist
events so upstream apps can present streaming behavior if needed.

The app supports internal streaming by:

- Writing incremental stdout and stderr chunks to `LLMRunEvent`
- Storing event sequence numbers
- Providing a repository method that other internal apps can poll or transform
  into SSE responses

This keeps transport concerns outside `llm_gateway` while preserving rich
execution telemetry.

## Failure handling

The design must distinguish between recoverable and terminal failures.

Recoverable cases:

- `codex` executor unavailable at runtime
- `codex` returns a recognized retryable execution failure
- malformed but recoverable final output

Terminal cases:

- missing capability definition
- both executors unavailable
- capability input fails schema validation
- timeout after fallback attempt
- unsupported skill discovery path

Failure behavior:

- Persist the failure reason on `LLMRun`
- Append failure events to `LLMRunEvent`
- Return a normalized error envelope to the calling app
- Avoid hiding the selected executor and final exit code

## Security boundary

The server is considered trusted, but deterministic code still owns execution
boundaries.

Security rules:

- Business apps never pass shell commands directly.
- Business apps never pass skill names directly.
- Executors receive only validated internal instructions.
- Skill discovery reads only known global shared directories.
- Prompt generation does not let the model select arbitrary local file paths.
- Fallback between executors happens in code, not at model discretion alone.

## Testing strategy

The implementation needs unit and integration coverage.

Recommended test areas:

- Catalog discovery of shared skills
- Capability routing defaults
- `codex`-first executor selection
- Fallback from `codex` to `claude`
- Synchronous fallback when Celery is disabled
- Run persistence and status transitions
- Event ordering and event storage
- Result normalization for successful and malformed output
- Service-level behavior for `search_wechat_articles`

Recommended test files:

- `llm_gateway/tests/test_catalog.py`
- `llm_gateway/tests/test_capability_router.py`
- `llm_gateway/tests/test_run_manager.py`
- `llm_gateway/tests/test_codex_executor.py`
- `llm_gateway/tests/test_claude_executor.py`
- `llm_gateway/tests/test_normalizer.py`
- `llm_gateway/tests/test_gateway_service.py`

## Rollout plan

This feature should ship incrementally.

Phase 1:

- Add the app, models, task wiring, and executor abstractions.
- Implement `search_wechat_articles` as the first capability.
- Make `codex` the default executor.
- Add `claude` fallback.

Phase 2:

- Add more capabilities on the same service boundary.
- Improve output repair and result summarization.
- Add richer internal observability and admin views if needed.

## Open questions

The design is ready to move into implementation planning, but a few defaults
may need confirmation during implementation.

- How should upstream apps expose stored run events as SSE, if needed?
- Should run retention be bounded by a cleanup job in the first release?
- Should executor availability be cached or checked per run?

## Next steps

Review this design in the repository, then write an implementation plan for the
first capability slice inside `llm_gateway`.
