# We RSS markdown format implementation plan

> **For agentic workers:** REQUIRED: Use
> superpowers:subagent-driven-development (if subagents available) or
> superpowers:executing-plans to implement this plan. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Add a tenant-scoped `we_rss` API that accepts one text string and
returns gently corrected, lightly reformatted Markdown by calling a new
internal `markdown_format` capability in `llm_gateway`.

**Architecture:** Extend the existing `llm_gateway` capability pipeline instead
of creating a special-case API path. `we_rss` validates and exposes the public
HTTP contract, `llm_gateway` validates and routes the internal capability, and
`codex` applies the `baoyu-format-markdown` skill standard through a tightly
bounded prompt.

**Tech Stack:** Django 5.2, Django REST Framework, drf-spectacular,
Pydantic/PydanticAI-backed `llm_gateway`, `codex` CLI, Django test runner,
existing `we_rss` tenant viewset conventions.

---

## Context and source of truth

This plan implements the approved design in:

- `docs/superpowers/specs/2026-04-10-we-rss-markdown-format-design.md`

The implementation must preserve these decisions:

- The new public API lives in `we_rss`, not `llm_gateway`.
- The new internal capability name is `markdown_format`.
- The first release accepts a single string input named `content`.
- The first release defaults to and only supports `mode="gentle"`.
- The output is Markdown text only, with no diff and no explanation.
- `llm_gateway` must prefer `codex`.
- `llm_gateway` must validate availability of `baoyu-format-markdown`.
- The implementation must not run the skill's script file directly.

## File structure map

Map the work up front so responsibilities stay clear and changes remain small.

### `llm_gateway` files

- Modify: `llm_gateway/schemas/requests.py`
- Modify: `llm_gateway/services/capability_router.py`
- Modify: `llm_gateway/orchestration/prompts.py`
- Modify: `llm_gateway/orchestration/agent.py`
- Modify: `llm_gateway/services/normalizer.py`
- Modify: `llm_gateway/services/gateway.py`
- Modify: `llm_gateway/tests/test_capability_router.py`
- Modify: `llm_gateway/tests/test_agent.py`
- Modify: `llm_gateway/tests/test_normalizer.py`
- Modify: `llm_gateway/tests/test_gateway_service.py`

### `we_rss` files

- Modify: `we_rss/serializers.py`
- Create: `we_rss/services/markdown_format_service.py`
- Create: `we_rss/views/markdown_views.py`
- Modify: `we_rss/urls.py`
- Create: `we_rss/tests/test_markdown_format_api.py`

### OpenAPI and examples

- Modify: `we_rss/schema.py`

## Implementation constraints

- Use @superpowers:test-driven-development for each new behavior.
- Follow existing `we_rss` patterns for serializers, `@action`, and responses.
- Keep prompt text in `llm_gateway/orchestration/prompts.py`.
- Do not expose `used_skill` or `raw_text` in the public API response.
- Do not add file upload, path input, batch mode, or `rewrite` mode.
- Keep the normalizer strict enough to reject empty or unusable output.
- Prefer small, reviewable commits after each task group.

## Chunk 1: Extend `llm_gateway` for `markdown_format`

### Task 1: Add the internal request schema for Markdown formatting

**Files:**

- Modify: `llm_gateway/schemas/requests.py`
- Modify: `llm_gateway/tests/test_gateway_service.py`

- [x] **Step 1: Write the failing schema-focused gateway test**

```python
from unittest.mock import patch

from django.test import TestCase

from llm_gateway.services.gateway import LLMGatewayService


class LLMGatewayServiceTests(TestCase):
    @patch("llm_gateway.services.gateway.RunManager")
    def test_format_markdown_defaults_to_gentle_mode(self, run_manager):
        run_manager.run_capability.return_value = {
            "formatted_markdown": "# Title\n\nBody",
            "executor": "codex",
            "used_skill": "baoyu-format-markdown",
            "raw_text": "# Title\n\nBody",
        }

        result = LLMGatewayService.format_markdown(
            content="# Title\nBody",
            requested_by_app="we_rss",
        )

        self.assertEqual(result["formatted_markdown"], "# Title\n\nBody")
```

- [x] **Step 2: Run the test to verify it fails**

Run:
`python manage.py test llm_gateway.tests.test_gateway_service.LLMGatewayServiceTests.test_format_markdown_defaults_to_gentle_mode -v 2`

Expected: FAIL because `format_markdown` and the request schema do not exist.

- [x] **Step 3: Add the minimal request schema**

Implement in `llm_gateway/schemas/requests.py`:

- `MarkdownFormatRequest`
- `content: str = Field(min_length=1)`
- `mode: str = Field(default="gentle")`
- validation that trims `content`
- validation that only accepts `gentle`

- [x] **Step 4: Run the test to verify it now fails for the next missing piece**

Run:
`python manage.py test llm_gateway.tests.test_gateway_service.LLMGatewayServiceTests.test_format_markdown_defaults_to_gentle_mode -v 2`

Expected: FAIL because the gateway service method is still missing, not because
the request schema is invalid.

- [x] **Step 5: Commit**

```bash
git add llm_gateway/schemas/requests.py llm_gateway/tests/test_gateway_service.py
git commit -m "test: add markdown format request coverage"
```

### Task 2: Route the new capability through the existing execution plan

**Files:**

- Modify: `llm_gateway/services/capability_router.py`
- Modify: `llm_gateway/tests/test_capability_router.py`

- [x] **Step 1: Write the failing router test**

```python
from django.test import SimpleTestCase

from llm_gateway.services.capability_router import CapabilityRouter


class CapabilityRouterTests(SimpleTestCase):
    def test_markdown_format_prefers_codex_and_baoyu_skill(self):
        plan = CapabilityRouter.resolve(
            capability="markdown_format",
            input_payload={"content": "# Title\nBody", "mode": "gentle"},
        )

        self.assertEqual(plan.preferred_executor, "codex")
        self.assertIn("codex", plan.allowed_executors)
        self.assertEqual(plan.skill_hint, "baoyu-format-markdown")
```

- [x] **Step 2: Run the test to verify it fails**

Run:
`python manage.py test llm_gateway.tests.test_capability_router.CapabilityRouterTests.test_markdown_format_prefers_codex_and_baoyu_skill -v 2`

Expected: FAIL because `markdown_format` is unsupported.

- [x] **Step 3: Add the minimal router support**

Implement in `llm_gateway/services/capability_router.py`:

- a `markdown_format` branch
- request validation through `MarkdownFormatRequest`
- `skill_hint="baoyu-format-markdown"`
- `preferred_executor` and `allowed_executors` using existing settings
- reuse of the current timeout setting

- [x] **Step 4: Run the focused router tests**

Run:
`python manage.py test llm_gateway.tests.test_capability_router -v 2`

Expected: PASS for both existing WeChat search coverage and new Markdown
format coverage.

- [x] **Step 5: Commit**

```bash
git add llm_gateway/services/capability_router.py llm_gateway/tests/test_capability_router.py
git commit -m "feat: route markdown format capability"
```

### Task 3: Add prompt builders and agent support for Markdown formatting

**Files:**

- Modify: `llm_gateway/orchestration/prompts.py`
- Modify: `llm_gateway/orchestration/agent.py`
- Modify: `llm_gateway/tests/test_agent.py`

- [x] **Step 1: Write the failing agent tests**

```python
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from llm_gateway.orchestration.agent import LLMGatewayAgentService


class LLMGatewayAgentServiceTests(SimpleTestCase):
    @patch("llm_gateway.orchestration.agent.SkillCatalogService")
    @patch("llm_gateway.orchestration.agent.Agent")
    def test_builds_markdown_format_instruction_with_baoyu_skill(self, agent_cls, catalog_cls):
        fake_agent = Mock()
        fake_agent.run_sync.return_value.output = {
            "prompt": "ignored",
            "selected_executor": "codex",
            "used_skill": "baoyu-format-markdown",
            "output_mode": "text",
        }
        agent_cls.return_value = fake_agent
        catalog_cls.get_skill.return_value = Mock()

        instruction = LLMGatewayAgentService.build_instruction(
            capability="markdown_format",
            input_payload={"content": "# Title\nBody", "mode": "gentle"},
            allowed_executors=["codex", "claude"],
            preferred_executor="codex",
        )

        self.assertEqual(instruction.selected_executor, "codex")
        self.assertEqual(instruction.used_skill, "baoyu-format-markdown")
        self.assertIn("Markdown", instruction.prompt)
        self.assertIn("gentle", instruction.prompt)
```

- [x] **Step 2: Run the test to verify it fails**

Run:
`python manage.py test llm_gateway.tests.test_agent.LLMGatewayAgentServiceTests.test_builds_markdown_format_instruction_with_baoyu_skill -v 2`

Expected: FAIL because the capability-specific prompt builder does not exist.

- [x] **Step 3: Add the minimal prompt and agent implementation**

Implement in `llm_gateway/orchestration/prompts.py`:

- `build_markdown_format_prompt(...)`
- `build_markdown_format_executor_prompt(...)`

The executor prompt must:

- mention Markdown or plain text input
- require Markdown-only output
- require typo, punctuation, spacing, and light structure fixes
- explain `mode="gentle"`
- forbid explanations and fences around the whole output

Implement in `llm_gateway/orchestration/agent.py`:

- capability handling for `markdown_format`
- skill lookup for `baoyu-format-markdown`
- deterministic executor prompt generation

- [x] **Step 4: Run the focused agent tests**

Run:
`python manage.py test llm_gateway.tests.test_agent -v 2`

Expected: PASS for existing WeChat tests and new Markdown tests.

- [x] **Step 5: Commit**

```bash
git add llm_gateway/orchestration/prompts.py llm_gateway/orchestration/agent.py llm_gateway/tests/test_agent.py
git commit -m "feat: add markdown format orchestration prompts"
```

### Task 4: Normalize Markdown results and expose a gateway method

**Files:**

- Modify: `llm_gateway/services/normalizer.py`
- Modify: `llm_gateway/services/gateway.py`
- Modify: `llm_gateway/tests/test_normalizer.py`
- Modify: `llm_gateway/tests/test_gateway_service.py`

- [x] **Step 1: Write the failing normalizer and gateway tests**

```python
from django.test import SimpleTestCase

from llm_gateway.services.normalizer import ResultNormalizer


class ResultNormalizerTests(SimpleTestCase):
    def test_normalizes_markdown_format_text_output(self):
        result = ResultNormalizer.normalize(
            capability="markdown_format",
            raw_stdout="# Title\n\nBody",
            executor_name="codex",
            used_skill="baoyu-format-markdown",
        )

        self.assertEqual(result["formatted_markdown"], "# Title\n\nBody")
        self.assertEqual(result["executor"], "codex")
```

```python
from unittest.mock import patch

from django.test import TestCase

from llm_gateway.services.gateway import LLMGatewayService


class LLMGatewayServiceTests(TestCase):
    @patch("llm_gateway.services.gateway.RunManager")
    def test_format_markdown_hides_skill_details(self, run_manager):
        run_manager.run_capability.return_value = {
            "formatted_markdown": "# Title\n\nBody",
            "executor": "codex",
            "used_skill": "baoyu-format-markdown",
            "raw_text": "# Title\n\nBody",
        }

        result = LLMGatewayService.format_markdown(
            content="# Title\nBody",
            mode="gentle",
            requested_by_app="we_rss",
        )

        self.assertEqual(result["executor"], "codex")
        self.assertNotIn("used_skill", result)
        self.assertNotIn("raw_text", result)
```

- [x] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_normalizer llm_gateway.tests.test_gateway_service -v 2`

Expected: FAIL because `markdown_format` is not normalized and the gateway
service does not expose the new method.

- [x] **Step 3: Add the minimal implementation**

Implement in `llm_gateway/services/normalizer.py`:

- a `markdown_format` branch
- whitespace trimming
- rejection of empty output
- normalized return shape with `formatted_markdown`, `executor`, `used_skill`,
  and `raw_text`

Implement in `llm_gateway/services/gateway.py`:

- `format_markdown(content, mode="gentle", requested_by_app="")`
- request validation through `MarkdownFormatRequest`
- `RunManager.run_capability(...)` with `capability="markdown_format"`
- safe fallback return for null results
- filtering of internal keys before returning to callers

- [x] **Step 4: Run the focused tests**

Run:
`python manage.py test llm_gateway.tests.test_normalizer llm_gateway.tests.test_gateway_service -v 2`

Expected: PASS

- [x] **Step 5: Run the full `llm_gateway` suite**

Run:
`python manage.py test llm_gateway.tests -v 2`

Expected: PASS without regressions in WeChat article search tests.

- [x] **Step 6: Commit**

```bash
git add llm_gateway/services/normalizer.py llm_gateway/services/gateway.py llm_gateway/tests/test_normalizer.py llm_gateway/tests/test_gateway_service.py
git commit -m "feat: add markdown format gateway result handling"
```

## Chunk 2: Add the `we_rss` business service and API contract

### Task 5: Add request and response serializers for the new endpoint

**Files:**

- Modify: `we_rss/serializers.py`
- Create: `we_rss/tests/test_markdown_format_api.py`

- [x] **Step 1: Write the failing serializer-driven API tests**

```python
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class MarkdownFormatApiTests(APITestCase):
    def test_rejects_blank_content(self):
        response = self.client.post(
            reverse("we-rss:markdown-format"),
            {"content": "   ", "mode": "gentle"},
            format="json",
            HTTP_X_TENANT_ID="1",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_unsupported_mode(self):
        response = self.client.post(
            reverse("we-rss:markdown-format"),
            {"content": "# Title", "mode": "rewrite"},
            format="json",
            HTTP_X_TENANT_ID="1",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
```

- [x] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_markdown_format_api.MarkdownFormatApiTests -v 2`

Expected: FAIL because the route, view, and serializers do not exist.

- [x] **Step 3: Add the minimal serializers**

Implement in `we_rss/serializers.py`:

- `MarkdownFormatRequestSerializer`
- `MarkdownFormatResponseSerializer`

Validation rules:

- trim `content`
- reject blank `content`
- default `mode` to `gentle`
- reject unsupported modes

- [x] **Step 4: Run the same tests**

Run:
`python manage.py test we_rss.tests.test_markdown_format_api.MarkdownFormatApiTests -v 2`

Expected: FAIL because the view and route are still missing, not because
serializer validation is wrong.

- [x] **Step 5: Commit**

```bash
git add we_rss/serializers.py we_rss/tests/test_markdown_format_api.py
git commit -m "test: add markdown format api validation coverage"
```

### Task 6: Add the `we_rss` service wrapper for `llm_gateway`

**Files:**

- Create: `we_rss/services/markdown_format_service.py`
- Modify: `we_rss/tests/test_markdown_format_api.py`

- [x] **Step 1: Extend the API test to describe the service result shape**

```python
from unittest.mock import patch


class MarkdownFormatApiTests(APITestCase):
    @patch("we_rss.services.markdown_format_service.LLMGatewayService.format_markdown")
    def test_service_returns_public_shape(self, format_mock):
        format_mock.return_value = {
            "formatted_markdown": "# Title\n\nBody",
            "mode": "gentle",
            "executor": "codex",
        }
```

- [x] **Step 2: Run the test to verify it fails**

Run:
`python manage.py test we_rss.tests.test_markdown_format_api.MarkdownFormatApiTests.test_service_returns_public_shape -v 2`

Expected: FAIL because the service module does not exist.

- [x] **Step 3: Add the minimal business service**

Implement in `we_rss/services/markdown_format_service.py`:

- `MarkdownFormatService.format_content(content, mode="gentle")`
- call `LLMGatewayService.format_markdown(...)`
- pass `requested_by_app="we_rss"`
- return only:
  - `formatted_markdown`
  - `mode`
  - `executor`

- [x] **Step 4: Run the focused test**

Run:
`python manage.py test we_rss.tests.test_markdown_format_api.MarkdownFormatApiTests.test_service_returns_public_shape -v 2`

Expected: FAIL because the view and route are still missing.

- [x] **Step 5: Commit**

```bash
git add we_rss/services/markdown_format_service.py we_rss/tests/test_markdown_format_api.py
git commit -m "feat: add we rss markdown format service"
```

### Task 7: Add the new tenant API view and URL route

**Files:**

- Create: `we_rss/views/markdown_views.py`
- Modify: `we_rss/urls.py`
- Modify: `we_rss/tests/test_markdown_format_api.py`

- [x] **Step 1: Write the full success-path API test**

```python
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class MarkdownFormatApiTests(APITestCase):
    @patch("we_rss.views.markdown_views.MarkdownFormatService.format_content")
    def test_formats_markdown_text(self, format_mock):
        format_mock.return_value = {
            "formatted_markdown": "# Title\n\nBody",
            "mode": "gentle",
            "executor": "codex",
        }

        response = self.client.post(
            reverse("we-rss:markdown-format"),
            {"content": "# Title\nBody", "mode": "gentle"},
            format="json",
            HTTP_X_TENANT_ID="1",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["formatted_markdown"], "# Title\n\nBody")
        self.assertEqual(response.data["mode"], "gentle")
        self.assertEqual(response.data["executor"], "codex")
```

- [x] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_markdown_format_api -v 2`

Expected: FAIL because the view and URL are missing.

- [x] **Step 3: Add the minimal API implementation**

Implement in `we_rss/views/markdown_views.py`:

- a tenant-scoped view based on `WeRssTenantGenericViewSet`
- a `create` action that:
  - validates request data
  - calls `MarkdownFormatService.format_content(...)`
  - returns `MarkdownFormatResponseSerializer(...)`

Implement in `we_rss/urls.py`:

- `path("markdown/format/", MarkdownFormatViewSet.as_view({"post": "create"}), name="markdown-format")`

- [x] **Step 4: Run the focused API tests**

Run:
`python manage.py test we_rss.tests.test_markdown_format_api -v 2`

Expected: PASS

- [x] **Step 5: Commit**

```bash
git add we_rss/views/markdown_views.py we_rss/urls.py we_rss/tests/test_markdown_format_api.py
git commit -m "feat: add we rss markdown format api"
```

## Chunk 3: Add schema examples and failure coverage

### Task 8: Document the endpoint in `we_rss` schema helpers

**Files:**

- Modify: `we_rss/schema.py`
- Modify: `we_rss/views/markdown_views.py`

- [x] **Step 1: Write the failing documentation-oriented test or snapshot assertion**

If an existing schema test pattern is available, add one focused assertion for
the new endpoint. If not, add this verification to the API smoke test instead:

```python
response = self.client.options(reverse("we-rss:markdown-format"), HTTP_X_TENANT_ID="1")
assert response.status_code in {200, 405}
```

- [x] **Step 2: Run the targeted schema-related test**

Run:
`python manage.py test we_rss.tests.test_schema -v 2`

Expected: Either FAIL due to missing examples or reveal that no additional
schema test is needed.

- [x] **Step 3: Add the minimal schema support**

Implement in `we_rss/schema.py`:

- request example for Markdown format input
- response example for formatted Markdown output
- any reusable parameters or helper descriptions needed by the new view

Implement in `we_rss/views/markdown_views.py`:

- `@extend_schema(...)` metadata using existing helper style

- [x] **Step 4: Run the schema-related tests**

Run:
`python manage.py test we_rss.tests.test_schema -v 2`

Expected: PASS

- [x] **Step 5: Commit**

```bash
git add we_rss/schema.py we_rss/views/markdown_views.py
git commit -m "docs: add markdown format api schema metadata"
```

### Task 9: Cover upstream failures and empty executor output

**Files:**

- Modify: `llm_gateway/tests/test_normalizer.py`
- Modify: `we_rss/tests/test_markdown_format_api.py`

- [x] **Step 1: Add the failing tests**

```python
from django.test import SimpleTestCase

from llm_gateway.services.normalizer import ResultNormalizer


class ResultNormalizerTests(SimpleTestCase):
    def test_markdown_format_rejects_empty_output(self):
        with self.assertRaisesMessage(ValueError, "Formatted markdown content is empty."):
            ResultNormalizer.normalize(
                capability="markdown_format",
                raw_stdout="   ",
                executor_name="codex",
                used_skill="baoyu-format-markdown",
            )
```

```python
from unittest.mock import patch

from rest_framework import status


class MarkdownFormatApiTests(APITestCase):
    @patch("we_rss.views.markdown_views.MarkdownFormatService.format_content")
    def test_returns_server_error_when_gateway_fails(self, format_mock):
        format_mock.side_effect = RuntimeError("executor failed")

        response = self.client.post(
            reverse("we-rss:markdown-format"),
            {"content": "# Title\nBody", "mode": "gentle"},
            format="json",
            HTTP_X_TENANT_ID="1",
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
```

- [x] **Step 2: Run the failing tests**

Run:
`python manage.py test llm_gateway.tests.test_normalizer we_rss.tests.test_markdown_format_api -v 2`

Expected: FAIL because empty-output rejection and error mapping are incomplete.

- [x] **Step 3: Add the minimal fixes**

Implement:

- strict empty-output rejection in `llm_gateway/services/normalizer.py`
- consistent error propagation in `we_rss/views/markdown_views.py`

If your API layer uses a custom exception style elsewhere, match it instead of
inventing a new envelope.

- [x] **Step 4: Run the focused tests**

Run:
`python manage.py test llm_gateway.tests.test_normalizer we_rss.tests.test_markdown_format_api -v 2`

Expected: PASS

- [x] **Step 5: Commit**

```bash
git add llm_gateway/tests/test_normalizer.py we_rss/tests/test_markdown_format_api.py llm_gateway/services/normalizer.py we_rss/views/markdown_views.py
git commit -m "test: harden markdown format failure handling"
```

## Chunk 4: Final verification

### Task 10: Run focused regression suites and capture the final contract

**Files:**

- Modify: `docs/superpowers/plans/2026-04-10-we-rss-markdown-format-implementation.md`

- [x] **Step 1: Run the `llm_gateway` tests**

Run:
`python manage.py test llm_gateway.tests -v 2`

Expected: PASS

- [x] **Step 2: Run the new `we_rss` API tests**

Run:
`python manage.py test we_rss.tests.test_markdown_format_api -v 2`

Expected: PASS

- [x] **Step 3: Run one adjacent `we_rss` regression suite**

Run:
`python manage.py test we_rss.tests.test_articles_api -v 2`

Expected: PASS so the new route and serializers do not break adjacent article
APIs.

- [x] **Step 4: Smoke-test the public contract manually**

Run:
`python manage.py shell`

Then:

```python
from we_rss.services.markdown_format_service import MarkdownFormatService
```

Expected: Import succeeds and the service is available without creating a new
public dependency on `llm_gateway`.

- [x] **Step 5: Mark completed steps and prepare execution handoff**

Update this plan file checkboxes as work completes so the next worker can pick
up exactly where execution stopped.

## Execution handoff

Plan complete and saved to
`docs/superpowers/plans/2026-04-10-we-rss-markdown-format-implementation.md`.
Ready to execute?


## Execution notes

- Implemented the markdown_format capability and the POST /we-rss/markdown/format/ API.
- Verified focused llm_gateway tests, the new we_rss API tests, and we_rss schema tests with --settings=core.settings_test.
- Ran the adjacent we_rss.tests.test_articles_api suite and observed two existing unrelated failures:
  ArticleApiTests.test_task_detail_marks_stale_feed_sync_run_as_partial_success_when_batch_stops_making_progress
  and ArticleGatewayTests.test_import_article_by_url_builds_summary_and_parses_chinese_publish_time.
- Ran focused public article search regression tests separately; they passed.
- Ran llm_gateway.tests and observed one environment-driven existing failure in llm_gateway.tests.test_bootstrap.LLMGatewayBootstrapTests.test_llm_gateway_is_registered_with_defaults because local agent base URL settings are non-empty in this environment.

