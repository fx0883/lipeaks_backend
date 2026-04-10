# We RSS markdown format design

This document defines a new internal `markdown_format` capability for
`llm_gateway` and a new tenant-scoped API in `we_rss` that exposes the
capability to clients. The goal is to accept a text string that may already be
Markdown or may be plain text, run a gentle correction-and-format pass through
`codex`, and return cleaned Markdown text.

The design follows the same internal execution path that `we_rss` already uses
for WeChat article search. `we_rss` owns the public API. `llm_gateway` owns
capability routing, prompt construction, executor selection, and normalized
results. The `baoyu-format-markdown` skill remains an internal implementation
detail.

## Goals

This design adds one narrow, reusable Markdown cleanup capability without
changing the existing execution model.

- Add an internal `markdown_format` capability to `llm_gateway`.
- Add one new authenticated API endpoint in `we_rss`.
- Accept one string input that may contain Markdown or plain text.
- Return only formatted Markdown text.
- Default to a gentle formatting mode that preserves the author's structure and
  intent as much as possible.
- Reuse the existing `llm_gateway -> codex` orchestration path.
- Instruct `codex` to follow the `baoyu-format-markdown` skill standards.

## Non-goals

This first version intentionally keeps scope small so the team can ship a
stable text-only workflow first.

- Do not add file upload support.
- Do not accept local file paths through the API.
- Do not expose `llm_gateway` as a public HTTP API.
- Do not return explanations, change summaries, or diffs.
- Do not add a strong rewrite mode in the first release.
- Do not execute the skill's script file directly.
- Do not add batch formatting or background task polling.

## Current project context

The current codebase already has the internal layers required for this feature.
`llm_gateway` provides capability routing and executor orchestration through
service methods, while `we_rss` exposes authenticated tenant APIs. The current
WeChat article search flow in
[`we_rss/services/article_search_service.py`](/D:/GitHub/lipeaks_backend/we_rss/services/article_search_service.py)
and
[`llm_gateway/services/gateway.py`](/D:/GitHub/lipeaks_backend/llm_gateway/services/gateway.py)
shows the target integration pattern.

The current `llm_gateway` implementation is capability specific. The router,
agent service, prompts, and normalizer each branch on
`wechat_article_search`. This means the new capability should follow the same
explicit pattern instead of introducing a more generic abstraction in the same
change.

The machine environment also already includes the
`baoyu-format-markdown` skill in the shared skill directory. The new capability
can therefore validate skill availability up front and keep the skill name out
of the public API surface.

## User-facing API contract

The `we_rss` app exposes one new `POST` endpoint:

- `POST /we-rss/markdown/format/`

The endpoint accepts JSON input only. The first version uses one required text
field and one optional mode field.

Request body:

```json
{
  "content": "# Title\nOriginal markdown or plain text",
  "mode": "gentle"
}
```

Response body:

```json
{
  "formatted_markdown": "# Title\n\nCleaned markdown text",
  "mode": "gentle",
  "executor": "codex"
}
```

The API contract follows these rules:

- `content` is required and must be a non-empty string after trimming.
- `mode` is optional and defaults to `gentle`.
- The first release only accepts `gentle`.
- The response returns only the final Markdown text and minimal metadata.
- The response does not expose `used_skill` or raw executor output.

## Default formatting behavior

The first release supports one formatting mode because the caller already chose
to prioritize stability over aggressive rewrites.

`gentle` means the formatter must:

- Correct obvious typos, punctuation mistakes, spacing issues, and awkward
  grammar.
- Preserve the original meaning.
- Preserve existing structure when that structure is already reasonable.
- Apply light Markdown improvements such as headings, lists, emphasis, and
  blockquotes when they improve readability.
- Avoid turning the output into a stronger editorial rewrite.
- Return Markdown only, with no prose before or after the result.

This behavior keeps the endpoint predictable for downstream publishing flows,
including WeChat-oriented formatting pipelines.

## Proposed architecture

The design keeps business responsibilities and LLM responsibilities separated.
`we_rss` remains the only public API layer, and `llm_gateway` remains an
internal orchestration layer.

### `we_rss`

`we_rss` owns request validation, permission checks, and HTTP responses.

Recommended additions:

- A request serializer for `content` and `mode`
- A response serializer for `formatted_markdown`, `mode`, and `executor`
- A thin service wrapper that calls `LLMGatewayService.format_markdown(...)`
- A new view that follows the existing tenant API conventions
- A new URL route at `markdown/format/`

### `llm_gateway`

`llm_gateway` owns capability resolution and normalized execution.

Recommended additions:

- `MarkdownFormatRequest` in `llm_gateway/schemas/requests.py`
- A new public service method named `format_markdown(...)`
- A new capability named `markdown_format`
- Prompt builders for orchestration and executor instructions
- Agent support that validates `baoyu-format-markdown`
- Normalization logic for formatted Markdown results

### `codex` and skill usage

The executor path stays consistent with existing capability runs. `codex`
receives a deterministic instruction that tells it to format the provided text
using the standards and workflow of the `baoyu-format-markdown` skill.

The design does not run the skill's script directly. This choice matters
because the skill's bundled script is file-oriented, while this API is
string-oriented and generation-heavy. The skill is still authoritative for the
formatting standard, but `codex` applies that standard inside the executor
prompt.

## Execution flow

The full request path mirrors the existing WeChat article search pattern, with
the capability name and prompt strategy swapped for Markdown formatting.

1. A client calls `POST /we-rss/markdown/format/`.
2. `we_rss` validates the request and resolves tenant access.
3. `we_rss` calls `LLMGatewayService.format_markdown(...)`.
4. `LLMGatewayService` validates input through `MarkdownFormatRequest`.
5. `RunManager.run_capability(...)` creates and executes an internal
   `markdown_format` run.
6. `CapabilityRouter` returns an execution plan that prefers `codex`.
7. `LLMGatewayAgentService` verifies that `baoyu-format-markdown` is available
   and constructs the executor instruction.
8. `CodexExecutor` runs the prompt through the existing CLI path.
9. `ResultNormalizer` extracts one stable result shape for the capability.
10. `we_rss` maps the normalized payload into the HTTP response.

The endpoint behaves the same way as current `llm_gateway`-backed features with
respect to Celery. If Celery runs inline in the current environment, the
capability executes inline. If Celery runs asynchronously but blocks through the
same sync call path, this feature follows that behavior without introducing a
new transport contract.

## Prompt and skill strategy

The formatting result depends heavily on the executor prompt, so the prompt must
be constrained tightly.

The orchestration prompt must:

- Declare the internal capability name `markdown_format`
- Restrict allowed executors to the routed list
- Prefer `codex`
- Require the `baoyu-format-markdown` skill

The executor prompt must:

- State that the input may be Markdown or plain text
- State that the output must be Markdown only
- State that `mode=gentle` means preserve structure where possible
- Ask for typo fixes, punctuation fixes, spacing fixes, and light structural
  cleanup
- Forbid commentary, code fences around the whole result, JSON wrappers, or
  explanations
- Include the raw input text in a clear, bounded section

The prompt should not ask `codex` to invent shell commands, open arbitrary
files, or choose a different skill.

## Result normalization

The existing normalizer for WeChat article search expects JSON. That pattern is
not a fit for this capability because the desired output is raw Markdown text.

For `markdown_format`, the normalizer should:

- Trim leading and trailing whitespace
- Preserve the returned Markdown body
- Store the executor name
- Store `used_skill` internally for debugging consistency
- Keep `raw_text` internally for diagnostics

The normalized payload returned to calling code should contain:

- `formatted_markdown`
- `executor`
- `used_skill`
- `raw_text`

The public `we_rss` response should only expose:

- `formatted_markdown`
- `mode`
- `executor`

## Failure handling

The API must fail loudly when the system cannot guarantee a clean Markdown
response.

Validation failures return `400`:

- missing `content`
- blank `content`
- unsupported `mode`

Internal execution failures return server errors:

- missing `markdown_format` capability wiring
- missing `baoyu-format-markdown` skill
- executor failure
- timeout
- empty final output

The normalizer should reject obviously empty output after trimming. If the
executor returns explanation text mixed with Markdown, the normalizer may apply
small cleanup only when the body remains unambiguous. If the result is not
safely recoverable, the request should fail instead of returning polluted text.

## Testing strategy

The test plan focuses on capability wiring and HTTP contract stability rather
than on exact model phrasing.

### `llm_gateway` tests

The `llm_gateway` test suite should confirm that the new capability plugs into
the existing orchestration path correctly.

- Validate `MarkdownFormatRequest`
- Verify `CapabilityRouter.resolve(...)` for `markdown_format`
- Verify `LLMGatewayAgentService` prompt construction
- Verify required skill lookup for `baoyu-format-markdown`
- Verify `ResultNormalizer.normalize(...)` for Markdown output
- Verify `LLMGatewayService.format_markdown(...)`

Recommended test files:

- `llm_gateway/tests/test_capability_router.py`
- `llm_gateway/tests/test_agent.py`
- `llm_gateway/tests/test_normalizer.py`
- `llm_gateway/tests/test_gateway_service.py`

### `we_rss` tests

The `we_rss` test suite should confirm that the endpoint enforces the contract
and maps `llm_gateway` responses correctly.

- Markdown input returns `200`
- Plain text input returns `200`
- Blank `content` returns `400`
- Unsupported `mode` returns `400`
- Upstream gateway failure returns an error response without partial output

Recommended test file:

- `we_rss/tests/test_markdown_format_api.py`

## Acceptance criteria

The first release is complete when the feature meets all of these conditions.

1. `POST /we-rss/markdown/format/` is available to authenticated tenant users.
2. The endpoint accepts either Markdown text or plain text through one string
   field.
3. The endpoint defaults to `mode="gentle"` and rejects unsupported modes.
4. Successful responses contain only cleaned Markdown plus minimal metadata.
5. The implementation goes through `llm_gateway` and prefers `codex`.
6. The capability validates availability of `baoyu-format-markdown`.
7. The test suite covers both service wiring and public API behavior.

## Future extensions

This design leaves several useful extensions for later phases without blocking
the first release.

- Add `rewrite` mode for stronger structural edits
- Add file upload or file-based adapters on top of the same capability
- Add diff output for editorial workflows
- Add batch formatting
- Add prompt templates specialized for WeChat article polishing

## Next steps

Review this design in the repository, then write an implementation plan for the
`markdown_format` capability and the `we_rss` API endpoint that consumes it.
