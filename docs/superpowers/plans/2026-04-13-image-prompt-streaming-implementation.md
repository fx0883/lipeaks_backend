# Image prompt streaming implementation plan

> **For agentic workers:** REQUIRED: Use
> superpowers:subagent-driven-development (if subagents available) or
> superpowers:executing-plans to implement this plan. Steps use checkbox
> (`- [x]`) syntax for tracking.

**Goal:** Add a new authenticated `image_prompt` Django app with two pure
streaming SSE endpoints that migrate the old `backend` manga prompt APIs while
moving all direct large-model access into a reusable `llm_gateway`
direct-model streaming service.

**Architecture:** Build a thin public `image_prompt` layer that validates JSON
input, streams SSE events, and applies business post-processing. Build a new
direct-model path in `llm_gateway` that creates `pydantic_ai.Agent` instances
from existing gateway settings, streams model deltas, and validates final
structured output against Pydantic schemas. Keep the old skill-backed
`llm_gateway` path intact and separate.

**Tech Stack:** Django 5.2, Django REST Framework, drf-spectacular,
`StreamingHttpResponse`, Pydantic 2, `pydantic-ai==1.78.0`, Django test
runner, existing `users.Member` auth model, current `/api/v1/<app>/...`
project routing pattern.

---

## Context and source of truth

This plan implements the approved design in:

- `docs/superpowers/specs/2026-04-13-image-prompt-streaming-design.md`

The implementation must preserve these decisions:

- The public API app is `image_prompt`.
- The public API exposes only:
  - `POST /api/v1/image-prompt/analyze-series-characters/`
  - `POST /api/v1/image-prompt/joke-to-comic/`
- Both endpoints accept JSON and return `text/event-stream`.
- Both endpoints require authenticated access but do not require tenant
  isolation.
- `image_prompt` owns business prompts, post-processing, and SSE formatting.
- `llm_gateway` owns direct model setup and streaming.
- The new path must not use skills, executor selection, or shell commands.
- `joke-to-comic` keeps the fallback plan behavior from the old `backend`.

## File structure map

Lock file responsibilities before implementation so boundaries stay clear.

### Public app bootstrap and docs

- Create: `image_prompt/__init__.py`
- Create: `image_prompt/apps.py`
- Create: `image_prompt/urls.py`
- Create: `image_prompt/views.py`
- Create: `image_prompt/serializers.py`
- Create: `image_prompt/schemas.py`
- Create: `image_prompt/schema.py`
- Modify: `core/settings.py`
- Modify: `core/urls.py`

### Public app services and tests

- Create: `image_prompt/services/__init__.py`
- Create: `image_prompt/services/sse.py`
- Create: `image_prompt/services/series_character_service.py`
- Create: `image_prompt/services/joke_to_comic_service.py`
- Create: `image_prompt/tests/__init__.py`
- Create: `image_prompt/tests/test_bootstrap.py`
- Create: `image_prompt/tests/test_sse.py`
- Create: `image_prompt/tests/test_series_character_service.py`
- Create: `image_prompt/tests/test_joke_to_comic_service.py`
- Create: `image_prompt/tests/test_streaming_api.py`
- Create: `image_prompt/tests/test_schema.py`

### `llm_gateway` direct-model infrastructure

- Create: `llm_gateway/services/model_factory.py`
- Create: `llm_gateway/services/direct_model.py`
- Create: `llm_gateway/tests/test_model_factory.py`
- Create: `llm_gateway/tests/test_direct_model.py`

### Optional touch points inside existing modules

- Modify: `llm_gateway/services/__init__.py` if the package uses explicit
  exports
- Modify: `requirements.txt` only if execution reveals a missing dependency
  rather than assuming changes are needed up front

## Implementation constraints

- Use @superpowers:test-driven-development for each new behavior.
- Use `APIView` plus `StreamingHttpResponse` for the public endpoints so the
  response bypasses the normal JSON renderer and standardization middleware.
- Use `python manage.py test ... --settings=core.settings_test -v 2` for plan
  verification commands.
- Keep the direct-model service generic. Do not hardcode manga-specific fields
  into `llm_gateway`.
- Keep public response field names aligned with the current `backend`
  contracts.
- Prefer small commits after each completed task.

## Chunk 1: Bootstrap the public app and streaming primitives

### Task 1: Register `image_prompt` and wire the public routes

**Files:**

- Create: `image_prompt/__init__.py`
- Create: `image_prompt/apps.py`
- Create: `image_prompt/urls.py`
- Create: `image_prompt/views.py`
- Create: `image_prompt/tests/test_bootstrap.py`
- Modify: `core/settings.py`
- Modify: `core/urls.py`

- [x] **Step 1: Write the failing bootstrap tests**

```python
from django.apps import apps
from django.test import SimpleTestCase
from django.urls import resolve


class ImagePromptBootstrapTests(SimpleTestCase):
    def test_image_prompt_is_installed(self):
        self.assertTrue(apps.is_installed("image_prompt"))

    def test_public_routes_resolve(self):
        analyze_match = resolve("/api/v1/image-prompt/analyze-series-characters/")
        joke_match = resolve("/api/v1/image-prompt/joke-to-comic/")

        self.assertEqual(analyze_match.view_name, "image-prompt:analyze-series-characters")
        self.assertEqual(joke_match.view_name, "image-prompt:joke-to-comic")
```

- [x] **Step 2: Run the bootstrap tests to verify they fail**

Run:
`python manage.py test image_prompt.tests.test_bootstrap --settings=core.settings_test -v 2`

Expected: FAIL because the app package and URL wiring do not exist.

- [x] **Step 3: Add the minimal bootstrap code**

Implement:

- `image_prompt/apps.py` with `ImagePromptConfig`
- `image_prompt/urls.py` with named routes for both `POST` endpoints
- `image_prompt/views.py` with minimal placeholder `APIView` classes so URL
  resolution succeeds
- `core/settings.py` with `image_prompt` in `INSTALLED_APPS`
- `core/urls.py` with `path("image-prompt/", include("image_prompt.urls", namespace="image-prompt"))`

- [x] **Step 4: Run the bootstrap tests again**

Run:
`python manage.py test image_prompt.tests.test_bootstrap --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 5: Commit (skipped in this shared dirty worktree session)**

```bash
git add image_prompt/__init__.py image_prompt/apps.py image_prompt/urls.py image_prompt/views.py image_prompt/tests/test_bootstrap.py core/settings.py core/urls.py
git commit -m "feat: bootstrap image prompt app"
```

### Task 2: Add the shared SSE framing helper

**Files:**

- Create: `image_prompt/services/__init__.py`
- Create: `image_prompt/services/sse.py`
- Create: `image_prompt/tests/test_sse.py`

- [x] **Step 1: Write the failing SSE helper tests**

```python
from django.test import SimpleTestCase

from image_prompt.services.sse import encode_sse_event


class ImagePromptSseTests(SimpleTestCase):
    def test_encodes_named_event_with_json_payload(self):
        payload = encode_sse_event("progress", {"stage": "analyzing", "message": "Starting"})

        self.assertEqual(
            payload.decode("utf-8"),
            'event: progress\\ndata: {"stage":"analyzing","message":"Starting"}\\n\\n',
        )

    def test_encodes_error_event_without_ascii_escaping(self):
        payload = encode_sse_event("error", {"message": "角色分析服务暂时不可用"})
        self.assertIn("角色分析服务暂时不可用", payload.decode("utf-8"))
```

- [x] **Step 2: Run the SSE helper tests to verify they fail**

Run:
`python manage.py test image_prompt.tests.test_sse --settings=core.settings_test -v 2`

Expected: FAIL because the helper module does not exist.

- [x] **Step 3: Add the minimal SSE helper**

Implement in `image_prompt/services/sse.py`:

- `encode_sse_event(event_name, payload) -> bytes`
- compact JSON serialization with `ensure_ascii=False`
- trailing blank line required by SSE framing

- [x] **Step 4: Run the SSE helper tests again**

Run:
`python manage.py test image_prompt.tests.test_sse --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 5: Commit (skipped in this shared dirty worktree session)**

```bash
git add image_prompt/services/__init__.py image_prompt/services/sse.py image_prompt/tests/test_sse.py
git commit -m "feat: add image prompt sse helper"
```

## Chunk 2: Add the `llm_gateway` direct-model streaming layer

### Task 3: Add the reusable model factory

**Files:**

- Create: `llm_gateway/services/model_factory.py`
- Create: `llm_gateway/tests/test_model_factory.py`

- [x] **Step 1: Write the failing model factory tests**

```python
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from llm_gateway.services.model_factory import LLMGatewayModelFactory


class LLMGatewayModelFactoryTests(SimpleTestCase):
    @override_settings(
        LLM_GATEWAY_AGENT_MODEL="openai:gpt-5.4",
        LLM_GATEWAY_AGENT_BASE_URL="",
        LLM_GATEWAY_AGENT_API_KEY="",
    )
    def test_returns_model_name_when_provider_override_is_empty(self):
        self.assertEqual(LLMGatewayModelFactory.build_model(), "openai:gpt-5.4")

    @override_settings(
        LLM_GATEWAY_AGENT_MODEL="openai:gpt-5.4",
        LLM_GATEWAY_AGENT_BASE_URL="https://example.com/v1",
        LLM_GATEWAY_AGENT_API_KEY="secret",
    )
    @patch("llm_gateway.services.model_factory.OpenAIProvider")
    @patch("llm_gateway.services.model_factory.OpenAIChatModel")
    def test_builds_openai_compatible_model_when_provider_override_exists(
        self, chat_model_cls, provider_cls
    ):
        provider = Mock()
        model = Mock()
        provider_cls.return_value = provider
        chat_model_cls.return_value = model

        result = LLMGatewayModelFactory.build_model()

        self.assertIs(result, model)
        provider_cls.assert_called_once_with(base_url="https://example.com/v1", api_key="secret")
        chat_model_cls.assert_called_once_with("gpt-5.4", provider=provider)
```

- [x] **Step 2: Run the model factory tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_model_factory --settings=core.settings_test -v 2`

Expected: FAIL because the model factory does not exist.

- [x] **Step 3: Add the minimal model factory**

Implement in `llm_gateway/services/model_factory.py`:

- `LLMGatewayModelFactory.build_model()`
- provider-prefix normalization from `openai:gpt-5.4` to `gpt-5.4`
- direct string return when no provider override exists
- `OpenAIProvider` and `OpenAIChatModel` construction when override settings
  exist

- [x] **Step 4: Run the model factory tests again**

Run:
`python manage.py test llm_gateway.tests.test_model_factory --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 5: Commit (skipped in this shared dirty worktree session)**

```bash
git add llm_gateway/services/model_factory.py llm_gateway/tests/test_model_factory.py
git commit -m "feat: add llm gateway model factory"
```

### Task 4: Add the direct-model streaming service

**Files:**

- Create: `llm_gateway/services/direct_model.py`
- Create: `llm_gateway/tests/test_direct_model.py`

- [x] **Step 1: Write the failing direct-model tests**

```python
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from llm_gateway.services.direct_model import DirectModelDeltaEvent, DirectModelResultEvent, DirectModelService


class DirectModelServiceTests(SimpleTestCase):
    @patch("llm_gateway.services.direct_model.Agent")
    @patch("llm_gateway.services.direct_model.LLMGatewayModelFactory")
    def test_stream_structured_yields_deltas_and_final_result(self, factory_cls, agent_cls):
        streamed_result = Mock()
        streamed_result.stream_text.return_value = iter(["{", '"title"', "}"])
        streamed_result.get_output.return_value = {"title": "done"}

        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=streamed_result)
        context_manager.__exit__ = Mock(return_value=False)

        agent = Mock()
        agent.run_stream_sync.return_value = context_manager
        agent_cls.return_value = agent
        factory_cls.build_model.return_value = "openai:gpt-5.4"

        events = list(
            DirectModelService.stream_structured(
                system_prompt="sys",
                user_prompt="user",
                output_schema=dict,
                requested_by_app="image_prompt",
            )
        )

        self.assertIsInstance(events[0], DirectModelDeltaEvent)
        self.assertEqual(events[-1].output, {"title": "done"})
        agent.run_stream_sync.assert_called_once()
```

- [x] **Step 2: Run the direct-model tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_direct_model --settings=core.settings_test -v 2`

Expected: FAIL because the direct-model service does not exist.

- [x] **Step 3: Add the minimal direct-model implementation**

Implement in `llm_gateway/services/direct_model.py`:

- lightweight event dataclasses:
  - `DirectModelDeltaEvent`
  - `DirectModelResultEvent`
- gateway-specific exceptions for configuration or provider failures
- `DirectModelService.stream_structured(...)`
- `Agent(...)` construction using `LLMGatewayModelFactory.build_model()`
- `run_stream_sync(...)` with `output_type=output_schema`
- `stream_text(delta=True, debounce_by=None)` for incremental raw text
- `get_output()` for the final validated structured result

- [x] **Step 4: Run the direct-model tests again**

Run:
`python manage.py test llm_gateway.tests.test_direct_model --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 5: Commit (skipped in this shared dirty worktree session)**

```bash
git add llm_gateway/services/direct_model.py llm_gateway/tests/test_direct_model.py
git commit -m "feat: add direct model streaming service"
```

## Chunk 3: Implement `analyze-series-characters`

### Task 5: Add shared schemas and request serializers

**Files:**

- Create: `image_prompt/schemas.py`
- Create: `image_prompt/serializers.py`
- Create: `image_prompt/tests/test_series_character_service.py`

- [x] **Step 1: Write the failing schema and serializer tests**

```python
from django.test import SimpleTestCase
from image_prompt.serializers import AnalyzeSeriesCharactersRequestSerializer


class AnalyzeSeriesCharactersSerializerTests(SimpleTestCase):
    def test_rejects_blank_source_text(self):
        serializer = AnalyzeSeriesCharactersRequestSerializer(data={"source_text": "   "})
        self.assertFalse(serializer.is_valid())
        self.assertIn("source_text", serializer.errors)
```

- [x] **Step 2: Run the focused tests to verify they fail**

Run:
`python manage.py test image_prompt.tests.test_series_character_service --settings=core.settings_test -v 2`

Expected: FAIL because the schema and serializer modules do not exist.

- [x] **Step 3: Add the minimal shared schemas**

Implement in `image_prompt/schemas.py`:

- `CharacterCandidate`
- `AnalyzeSeriesCharactersResult`
- `ComicPlanPanel`
- `ComicPlan`
- `PromptPackFormat`
- `PromptPackPanel`
- `JokeToComicResult`

Implement in `image_prompt/serializers.py`:

- `AnalyzeSeriesCharactersRequestSerializer`
- request validation for trimmed `source_text`
- optional `series_name`

- [x] **Step 4: Run the focused tests again**

Run:
`python manage.py test image_prompt.tests.test_series_character_service --settings=core.settings_test -v 2`

Expected: FAIL because the business service is still missing.

- [x] **Step 5: Commit (skipped in this shared dirty worktree session)**

```bash
git add image_prompt/schemas.py image_prompt/serializers.py image_prompt/tests/test_series_character_service.py
git commit -m "feat: add image prompt shared schemas"
```

### Task 6: Add the series character business service

**Files:**

- Create: `image_prompt/services/series_character_service.py`
- Modify: `image_prompt/tests/test_series_character_service.py`

- [x] **Step 1: Write the failing business-service tests**

```python
from unittest.mock import patch

from django.test import SimpleTestCase

from image_prompt.schemas import AnalyzeSeriesCharactersResult, CharacterCandidate
from image_prompt.services.series_character_service import SeriesCharacterService


class SeriesCharacterServiceTests(SimpleTestCase):
    @patch("image_prompt.services.series_character_service.DirectModelService")
    def test_moves_tooling_roles_to_temporary_bucket(self, direct_model_cls):
        direct_model_cls.stream_structured.return_value = iter(
            [
                AnalyzeSeriesCharactersResult(
                    recommended_main_characters=[
                        CharacterCandidate(...),
                        CharacterCandidate(...),
                        CharacterCandidate(...),
                    ],
                    temporary_characters=[],
                    analysis_notes=["initial"],
                )
            ]
        )
```

- [x] **Step 2: Run the service tests to verify they fail**

Run:
`python manage.py test image_prompt.tests.test_series_character_service --settings=core.settings_test -v 2`

Expected: FAIL because the service implementation is missing.

- [x] **Step 3: Add the minimal business service**

Implement in `image_prompt/services/series_character_service.py`:

- `SeriesCharacterService.stream_analysis(source_text, series_name="")`
- business `progress` stage markers before model invocation
- call to `DirectModelService.stream_structured(...)`
- de-duplication by character name
- tooling-role detection and transfer to `temporary_characters`
- final validation that at least two reusable core characters remain
- final normalized result with stable `analysis_notes`

- [x] **Step 4: Run the service tests again**

Run:
`python manage.py test image_prompt.tests.test_series_character_service --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 5: Commit (skipped in this shared dirty worktree session)**

```bash
git add image_prompt/services/series_character_service.py image_prompt/tests/test_series_character_service.py
git commit -m "feat: add series character streaming service"
```

### Task 7: Add the streaming API view for series character analysis

**Files:**

- Modify: `image_prompt/views.py`
- Create: `image_prompt/tests/test_streaming_api.py`

- [x] **Step 1: Write the failing API tests**

```python
import json

from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Member


class ImagePromptStreamingApiTests(APITestCase):
    def setUp(self):
        self.member = Member.objects.create(username="image-prompt-member", email="image-prompt@example.com")
        self.client.force_authenticate(user=self.member)

    def test_analyze_series_characters_returns_sse_stream(self):
        response = self.client.post(
            "/api/v1/image-prompt/analyze-series-characters/",
            {"source_text": "故事文本", "series_name": "系列"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/event-stream")
```

- [x] **Step 2: Run the API tests to verify they fail**

Run:
`python manage.py test image_prompt.tests.test_streaming_api.ImagePromptStreamingApiTests.test_analyze_series_characters_returns_sse_stream --settings=core.settings_test -v 2`

Expected: FAIL because the view still uses a placeholder implementation.

- [x] **Step 3: Add the minimal streaming view**

Implement in `image_prompt/views.py`:

- `AnalyzeSeriesCharactersStreamView(APIView)`
- `permission_classes = [IsAuthenticated]`
- request validation through `AnalyzeSeriesCharactersRequestSerializer`
- `StreamingHttpResponse` body that:
  - emits `start`
  - relays service progress and delta events
  - emits one final `completed`
  - emits one terminal `error` on failure

- [x] **Step 4: Expand the API tests to inspect the stream body**

Add assertions that the collected `b"".join(response.streaming_content)` body
contains:

- `event: start`
- `event: completed`

- [x] **Step 5: Run the focused API tests again**

Run:
`python manage.py test image_prompt.tests.test_streaming_api.ImagePromptStreamingApiTests.test_analyze_series_characters_returns_sse_stream --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 6: Commit (skipped in this shared dirty worktree session)**

```bash
git add image_prompt/views.py image_prompt/tests/test_streaming_api.py
git commit -m "feat: add series character streaming api"
```

## Chunk 4: Implement `joke-to-comic`

### Task 8: Add request serializers and the joke-to-comic business service

**Files:**

- Modify: `image_prompt/serializers.py`
- Create: `image_prompt/services/joke_to_comic_service.py`
- Create: `image_prompt/tests/test_joke_to_comic_service.py`

- [x] **Step 1: Write the failing joke-to-comic tests**

```python
from unittest.mock import patch

from django.test import SimpleTestCase

from image_prompt.services.joke_to_comic_service import JokeToComicService


class JokeToComicServiceTests(SimpleTestCase):
    @patch("image_prompt.services.joke_to_comic_service.DirectModelService")
    def test_builds_prompt_pack_from_structured_plan(self, direct_model_cls):
        ...

    def test_fallback_plan_keeps_four_panels(self):
        result = JokeToComicService.build_fallback_result("一个笑话", confirmed_characters=[])
        self.assertEqual(len(result.panels), 4)
        self.assertEqual(result.format.panel_count, 4)
```

- [x] **Step 2: Run the joke-to-comic tests to verify they fail**

Run:
`python manage.py test image_prompt.tests.test_joke_to_comic_service --settings=core.settings_test -v 2`

Expected: FAIL because the serializer and service implementation do not exist.

- [x] **Step 3: Add the minimal serializers and service**

Implement in `image_prompt/serializers.py`:

- `CharacterCandidateSerializer`
- `JokeToComicRequestSerializer`
- trimmed `joke`
- optional `confirmed_characters`

Implement in `image_prompt/services/joke_to_comic_service.py`:

- `JokeToComicService.stream_prompt_pack(joke, confirmed_characters=None)`
- structured comic-plan prompt generation
- four-panel normalization
- panel prompt and page prompt generation
- confirmed-character context injection
- fallback-plan creation when direct model fails before a valid result exists

- [x] **Step 4: Run the focused service tests again**

Run:
`python manage.py test image_prompt.tests.test_joke_to_comic_service --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 5: Commit (skipped in this shared dirty worktree session)**

```bash
git add image_prompt/serializers.py image_prompt/services/joke_to_comic_service.py image_prompt/tests/test_joke_to_comic_service.py
git commit -m "feat: add joke to comic streaming service"
```

### Task 9: Add the streaming API view for joke-to-comic

**Files:**

- Modify: `image_prompt/views.py`
- Modify: `image_prompt/tests/test_streaming_api.py`

- [x] **Step 1: Add the failing joke-to-comic API tests**

```python
class ImagePromptStreamingApiTests(APITestCase):
    def test_joke_to_comic_returns_completed_event(self):
        response = self.client.post(
            "/api/v1/image-prompt/joke-to-comic/",
            {"joke": "一个程序员笑话", "confirmed_characters": []},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
```

- [x] **Step 2: Run the focused API test to verify it fails**

Run:
`python manage.py test image_prompt.tests.test_streaming_api.ImagePromptStreamingApiTests.test_joke_to_comic_returns_completed_event --settings=core.settings_test -v 2`

Expected: FAIL because the route still points to a placeholder view.

- [x] **Step 3: Add the minimal streaming view**

Implement in `image_prompt/views.py`:

- `JokeToComicStreamView(APIView)`
- request validation through `JokeToComicRequestSerializer`
- `StreamingHttpResponse` that mirrors the series-character event lifecycle
- fallback handling that still ends in `completed` when fallback succeeds

- [x] **Step 4: Add an explicit error-path API test**

Mock the service to raise a terminal business error and assert the stream
contains:

- `event: error`
- no `event: completed`

- [x] **Step 5: Run the focused API tests again**

Run:
`python manage.py test image_prompt.tests.test_streaming_api --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 6: Commit (skipped in this shared dirty worktree session)**

```bash
git add image_prompt/views.py image_prompt/tests/test_streaming_api.py
git commit -m "feat: add joke to comic streaming api"
```

## Chunk 5: Add schema metadata and run regressions

### Task 10: Document the streaming endpoints for OpenAPI

**Files:**

- Create: `image_prompt/schema.py`
- Modify: `image_prompt/views.py`
- Create: `image_prompt/tests/test_schema.py`

- [x] **Step 1: Write the failing schema tests**

```python
from django.test import SimpleTestCase
from drf_spectacular.generators import SchemaGenerator


class ImagePromptSchemaTests(SimpleTestCase):
    def test_schema_includes_streaming_endpoints(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        self.assertIn("/api/v1/image-prompt/analyze-series-characters/", schema["paths"])
        self.assertIn("/api/v1/image-prompt/joke-to-comic/", schema["paths"])
```

- [x] **Step 2: Run the schema tests to verify they fail or lack metadata**

Run:
`python manage.py test image_prompt.tests.test_schema --settings=core.settings_test -v 2`

Expected: FAIL because the schema metadata does not exist yet or is incomplete.

- [x] **Step 3: Add the minimal schema metadata**

Implement in `image_prompt/schema.py`:

- request examples for both endpoints
- one reusable description for the `text/event-stream` response contract

Implement in `image_prompt/views.py`:

- `@extend_schema(...)` entries for both endpoints
- explicit note that the final business payload is delivered in the
  `completed` SSE event

- [x] **Step 4: Run the schema tests again**

Run:
`python manage.py test image_prompt.tests.test_schema --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 5: Commit (skipped in this shared dirty worktree session)**

```bash
git add image_prompt/schema.py image_prompt/views.py image_prompt/tests/test_schema.py
git commit -m "docs: add image prompt streaming schema metadata"
```

### Task 11: Run final focused regressions

**Files:**

- Modify: `docs/superpowers/plans/2026-04-13-image-prompt-streaming-implementation.md`

- [x] **Step 1: Run the new `llm_gateway` direct-model tests**

Run:
`python manage.py test llm_gateway.tests.test_model_factory llm_gateway.tests.test_direct_model --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 2: Run the full `image_prompt` test suite**

Run:
`python manage.py test image_prompt.tests --settings=core.settings_test -v 2`

Expected: PASS

- [x] **Step 3: Run one adjacent auth-scoped API regression suite**

Run:
`python manage.py test tests.wechat.test_draft_api --settings=core.settings_test -v 2`

Expected: PASS so the new authenticated non-tenant routing does not disturb an
adjacent API app.

- [x] **Step 4: Smoke-test imports in the Django shell**

Run:
`python manage.py shell --settings=core.settings_test`

Then:

```python
from image_prompt.services.series_character_service import SeriesCharacterService
from image_prompt.services.joke_to_comic_service import JokeToComicService
from llm_gateway.services.direct_model import DirectModelService
```

Expected: All imports succeed.

- [x] **Step 5: Mark completed steps and prepare execution handoff**

Update this plan file's checkboxes as each task completes so the executing
worker can resume precisely.

## Plan review notes

This session performed a self-review of the plan against the approved spec and
the current codebase. A dedicated review subagent was not dispatched because
delegation was not explicitly requested in this session.

## Execution handoff

Plan complete and saved to
`docs/superpowers/plans/2026-04-13-image-prompt-streaming-implementation.md`.
Ready to execute?
