# Image prompt streaming design

This document defines a new public `image_prompt` app and a new direct-model
execution path inside `llm_gateway`. The goal is to migrate the existing
`backend` FastAPI business APIs into the Django project while keeping business
logic in `image_prompt` and all large-model access in `llm_gateway`.

The design keeps the public API pure streaming. Both endpoints accept JSON
request bodies and return `text/event-stream` responses. The stream carries
progress events, model text deltas, and one final `completed` event with the
full structured result.

## Goals

This design focuses on moving the current manga prompt generation workflow into
the main Django codebase without carrying over the old service shape.

- Add a new authenticated `image_prompt` Django app.
- Migrate the existing `analyze-series-characters` and `joke-to-comic`
  business APIs from `backend`.
- Keep `image_prompt` responsible for request validation, business prompts,
  post-processing, and response streaming.
- Keep `llm_gateway` responsible for all direct model access.
- Use the model configured through the existing `LLM_GATEWAY_AGENT_*` settings.
- Return only streaming responses for the new public API.
- Keep request and result field shapes close to the current `backend`
  contracts.

## Non-goals

The first release stays intentionally narrow so the migration remains focused.

- Do not migrate the old `GET /api/health` endpoint.
- Do not expose `llm_gateway` as a public HTTP API.
- Do not use skills, executors, or shell-command orchestration for these two
  features.
- Do not add database models or business persistence in `image_prompt`.
- Do not require tenant isolation or `X-Tenant-ID`.
- Do not provide non-streaming JSON variants of the two endpoints.
- Do not add WebSocket transport in the first release.

## Current project context

The current codebase has two separate shapes for related work.

The standalone `backend` service contains the business logic that this design
needs to migrate. Its public surface is currently limited to:

- `POST /api/analyze-series-characters`
- `POST /api/joke-to-comic`

That code performs direct large-model calls in
[`backend/agents/series_characters.py`](/D:/GitHub/lipeaks_backend/backend/agents/series_characters.py)
and
[`backend/agents/joke_to_comic.py`](/D:/GitHub/lipeaks_backend/backend/agents/joke_to_comic.py).

The main Django project already has an internal LLM layer in
[`llm_gateway`](/D:/GitHub/lipeaks_backend/llm_gateway). Today,
`llm_gateway` is mostly oriented around skill-backed capabilities such as
WeChat article search and Markdown formatting. It already owns model
configuration and can already instantiate `pydantic_ai.Agent`, but it does not
yet expose a reusable direct-model streaming service for business apps.

The public API style that the new app must follow is the current Django
project's `/api/v1/<app>/...` convention from
[`core/urls.py`](/D:/GitHub/lipeaks_backend/core/urls.py).

## Public API contract

The new app exposes two authenticated endpoints:

- `POST /api/v1/image-prompt/analyze-series-characters/`
- `POST /api/v1/image-prompt/joke-to-comic/`

Both endpoints accept JSON request bodies and always return
`text/event-stream`. They do not provide a plain JSON response mode.

The request bodies stay close to the current `backend` contracts.

`analyze-series-characters` request:

```json
{
  "source_text": "One story draft in Chinese",
  "series_name": "Optional series name"
}
```

`joke-to-comic` request:

```json
{
  "joke": "One joke or short comic premise",
  "confirmed_characters": [
    {
      "character_name": "Product manager",
      "series_role": "core protagonist",
      "core_identity": "Drives conflict",
      "visual_profile": "Business outfit",
      "personality_profile": "Pushes quickly",
      "speech_style": "Short direct lines",
      "relationship_to_others": "Pressures the engineer",
      "signature_elements": ["requirements doc"],
      "character_prompt": "Locked character prompt",
      "confidence_reason": "Core recurring role"
    }
  ]
}
```

The final `completed` event contains the full structured payload. For
`analyze-series-characters`, that payload keeps:

- `recommended_main_characters`
- `temporary_characters`
- `analysis_notes`

For `joke-to-comic`, that payload keeps:

- `title`
- `source_joke`
- `format`
- `story_summary`
- `humor_explanation`
- `negative_prompt`
- `generation_notes`
- `panels`
- `page_prompt`

## Streaming contract

The endpoints use server-sent event framing over a `POST` response. The
frontend reads the stream through `fetch(...).body.getReader()` rather than the
browser's native `EventSource`, because the requests need JSON bodies.

The event protocol is shared by both endpoints.

- `start`: signals that request validation and processing began.
- `progress`: signals a named business stage.
- `delta`: carries incremental model text as it streams.
- `completed`: carries the final structured result as JSON.
- `error`: carries a terminal error payload and ends the stream.

Each event uses standard SSE framing:

```text
event: progress
data: {"stage":"analyzing_characters","message":"Analyzing character roles"}

```

The `completed` event is the canonical result. Consumers must treat all earlier
events as informational only.

## Proposed architecture

The design introduces one new public app and one new internal direct-model
service. The public app owns business behavior. The internal service owns model
execution.

### `image_prompt`

`image_prompt` owns HTTP concerns and business-specific prompt shaping.

Recommended files:

- `image_prompt/apps.py`
- `image_prompt/urls.py`
- `image_prompt/views.py`
- `image_prompt/serializers.py`
- `image_prompt/services/series_character_service.py`
- `image_prompt/services/joke_to_comic_service.py`
- `image_prompt/services/sse.py`
- `image_prompt/tests/test_views.py`
- `image_prompt/tests/test_services.py`

Responsibilities:

- Validate request bodies with DRF serializers.
- Enforce authenticated access without tenant checks.
- Build business-specific system and user prompts.
- Stream progress and model deltas to clients.
- Apply business post-processing to final structured model output.
- Convert internal failures into terminal `error` events.

### `llm_gateway`

`llm_gateway` owns direct interaction with the configured large model.

Recommended files:

- `llm_gateway/services/model_factory.py`
- `llm_gateway/services/direct_model.py`
- `llm_gateway/tests/test_model_factory.py`
- `llm_gateway/tests/test_direct_model.py`

Responsibilities:

- Read the existing `LLM_GATEWAY_AGENT_MODEL`,
  `LLM_GATEWAY_AGENT_BASE_URL`, and `LLM_GATEWAY_AGENT_API_KEY` settings.
- Build a reusable `pydantic_ai` model instance.
- Run the model in streaming mode.
- Emit incremental events that `image_prompt` can translate into SSE frames.
- Validate the final model output against the target schema.
- Raise clear internal exceptions for configuration, provider, timeout, or
  schema-validation failures.

This direct-model path is separate from the current skill-backed capability
path. These new APIs do not use `RunManager`, executor selection, or any
skill-resolution logic.

## Execution flow

The full request path is synchronous from the client's perspective, but the
response body streams as work progresses.

1. A client sends a `POST` request to one of the `image_prompt` endpoints.
2. The view validates the JSON body and starts a `StreamingHttpResponse`.
3. The view yields a `start` event.
4. The business service yields one or more `progress` events.
5. The business service calls `llm_gateway` direct-model streaming.
6. `llm_gateway` streams incremental model text back to the business service.
7. The view emits those increments as `delta` events.
8. When the model completes, `llm_gateway` validates the final structured
   output.
9. The business service applies business post-processing and validation.
10. The view emits one `completed` event with the final structured payload.
11. If any terminal error occurs before completion, the view emits one `error`
    event and closes the stream.

## Direct-model service design

The direct-model path must be reusable beyond this one app, so the API should
be generic rather than tied to manga-specific tasks.

Recommended entry point:

`DirectModelService.stream_structured(...)`

Recommended inputs:

- `system_prompt`
- `user_prompt`
- `output_schema`
- `requested_by_app`
- optional model settings for temperature or similar controls

Recommended outputs:

- an iterator of internal events for text deltas and lifecycle markers
- one validated final output object of the requested schema

Implementation notes:

- Reuse `pydantic_ai.Agent` with the provided `output_schema`.
- Reuse `Agent.run_stream_sync(...)` so the public Django view can stay sync.
- Keep the direct-model service free of business-specific field names.
- Normalize provider-specific exceptions into gateway-specific exceptions.

This design gives future apps one stable path for direct prompt-and-schema
model calls without reintroducing model setup code in each business module.

## Business service behavior

The migrated business logic stays close to the current `backend` behavior, but
the code moves to Django service modules.

### Series character analysis

The character analysis flow keeps the existing business rules from
[`backend/agents/series_characters.py`](/D:/GitHub/lipeaks_backend/backend/agents/series_characters.py).

The migrated service must:

- build the character-analysis prompt in Chinese
- request a structured result matching the current response schema
- de-duplicate character candidates by name
- move obvious tooling or one-off roles into the temporary bucket
- require at least two reusable core characters after post-processing
- trim the final `recommended_main_characters` list to the intended size
- add stable `analysis_notes` entries that explain important adjustments

### Joke to comic

The comic generation flow keeps the existing prompt-pack assembly behavior from
[`backend/agents/joke_to_comic.py`](/D:/GitHub/lipeaks_backend/backend/agents/joke_to_comic.py).

The migrated service must:

- ask the model for one four-panel comic plan
- normalize the plan to exactly four panels
- preserve the current panel and page prompt formats
- inject confirmed character context when provided
- preserve the current `1080x1440` single-panel prompt requirement
- preserve the current `2x2` page layout requirement
- keep the existing fallback plan behavior when the model call fails before a
  valid structured result is available

## Error handling

The API must expose stable business errors while keeping provider details
internal.

Request validation failures remain standard authentication or validation
responses before streaming starts.

Once streaming starts, terminal failures are emitted as one `error` event with
a compact JSON payload. Recommended terminal cases:

- missing model configuration
- model timeout
- provider failure
- structured-output validation failure
- final business validation failure

Business-specific error policy:

- `analyze-series-characters` emits `error` if fewer than two reusable core
  characters remain after post-processing
- `joke-to-comic` first tries the existing fallback plan if the model call
  fails; it emits `error` only if no valid final prompt pack can be built

The stream ends immediately after `completed` or `error`.

## Middleware and renderer compatibility

The current project wraps normal JSON responses through DRF renderers and
`ResponseStandardizationMiddleware`. This design avoids that path by returning
`StreamingHttpResponse` with `content_type='text/event-stream'`.

This matters because the middleware currently targets JSON-like responses only.
The new endpoints therefore do not need special bypass flags as long as they
avoid DRF `Response` objects for the streaming body.

## Testing strategy

The test plan must verify both streaming behavior and business correctness.

### `llm_gateway` tests

The internal tests should cover the new direct-model layer.

- verify model-name normalization and provider construction
- verify `DirectModelService` passes prompts and schema to `pydantic_ai.Agent`
- verify incremental events are surfaced to callers
- verify the final structured result is returned when validation succeeds
- verify configuration, provider, timeout, and schema failures are wrapped

### `image_prompt` service tests

The business tests should focus on post-processing and payload assembly.

- character de-duplication works
- tooling roles are moved to `temporary_characters`
- character analysis rejects results with fewer than two reusable core roles
- comic plan normalization always returns four panels
- confirmed characters are injected into generated panel and page prompts
- fallback plan generation works when the model path fails

### `image_prompt` view tests

The public API tests should verify the streaming contract.

- authenticated users can call both endpoints
- unauthenticated users are rejected before streaming begins
- the response content type is `text/event-stream`
- successful streams include `start` and `completed`
- error cases include one terminal `error` event
- the final `completed` payload matches the migrated business contract

## Acceptance criteria

This design is complete when the implementation meets all of these conditions.

1. The Django project contains a new `image_prompt` app registered in
   `INSTALLED_APPS`.
2. The public API exposes only these two endpoints:
   `analyze-series-characters` and `joke-to-comic`.
3. Both endpoints accept JSON request bodies and return `text/event-stream`.
4. Both endpoints require authenticated access but do not require tenant
   headers.
5. `image_prompt` contains business prompt building and post-processing only.
6. `llm_gateway` contains the reusable direct-model streaming service.
7. The new APIs do not use skills, executor orchestration, or shell commands.
8. The final `completed` event for each endpoint returns a structured payload
   compatible with the current `backend` business shape.
9. Tests cover direct-model streaming, business rules, and public SSE
   responses.

## Future extensions

This design leaves room for later work without expanding the first release.

- add optional non-streaming adapters for internal consumers only
- add partial structured snapshots during long generations
- add richer progress metadata, such as stage percentages
- add tracing or persistent run records if product needs justify them
- reuse the same direct-model service in other apps that need structured
  generation

## Next steps

Review this design in the repository, confirm the public streaming contract,
and then write the implementation plan for the new `image_prompt` app and the
new `llm_gateway` direct-model service.
