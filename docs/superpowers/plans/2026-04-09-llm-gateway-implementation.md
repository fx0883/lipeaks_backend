# LLM gateway implementation plan

> **For agentic workers:** REQUIRED: Use
> superpowers:subagent-driven-development (if subagents available) or
> superpowers:executing-plans to implement this plan. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Add an internal-only `llm_gateway` Django app that lets other apps
request LLM-backed capabilities, starting with WeChat article search, while
keeping skills, prompts, and CLI execution hidden behind one service layer.

**Architecture:** Create a root-level Django app that exposes capability
services instead of HTTP endpoints. Use `PydanticAI` as the orchestration
layer, prefer `codex` CLI as the primary skill executor, fall back to `claude`
CLI when needed, and persist run state plus streaming events in dedicated
models.

**Tech Stack:** Django 5.2, Celery, Redis-backed or eager task execution,
`PydanticAI`, `codex` CLI, `claude` CLI, Django test runner, existing project
settings and service conventions.

---

## Context and source of truth

This plan implements the approved design in:

- `docs/superpowers/specs/2026-04-09-llm-gateway-design.md`

The implementation must preserve these design decisions:

- `llm_gateway` is an internal Django app, not a public API app.
- Business apps call capability services, not raw skill runners.
- `PydanticAI` participates in orchestration only.
- `codex` is the default executor.
- `claude` is the fallback executor.
- Skill discovery only reads globally shared skill directories.
- Celery is the default async path, with synchronous fallback when Celery is
  disabled.
- The first capability is `search_wechat_articles`.

## File structure map

Map the work up front so responsibilities stay clear.

### New app files

- Create: `llm_gateway/__init__.py`
- Create: `llm_gateway/apps.py`
- Create: `llm_gateway/admin.py`
- Create: `llm_gateway/models.py`
- Create: `llm_gateway/tasks.py`

### New domain and schema files

- Create: `llm_gateway/domain/enums.py`
- Create: `llm_gateway/domain/entities.py`
- Create: `llm_gateway/schemas/requests.py`
- Create: `llm_gateway/schemas/results.py`
- Create: `llm_gateway/schemas/events.py`

### New orchestration, service, executor, and repository files

- Create: `llm_gateway/services/gateway.py`
- Create: `llm_gateway/services/capability_router.py`
- Create: `llm_gateway/services/run_manager.py`
- Create: `llm_gateway/services/catalog.py`
- Create: `llm_gateway/services/normalizer.py`
- Create: `llm_gateway/orchestration/agent.py`
- Create: `llm_gateway/orchestration/prompts.py`
- Create: `llm_gateway/executors/base.py`
- Create: `llm_gateway/executors/process.py`
- Create: `llm_gateway/executors/codex.py`
- Create: `llm_gateway/executors/claude.py`
- Create: `llm_gateway/repositories/runs.py`
- Create: `llm_gateway/repositories/events.py`

### New and modified project integration files

- Modify: `core/settings.py`
- Modify: `requirements.txt`
- Create: `llm_gateway/migrations/0001_initial.py`

### New tests

- Create: `llm_gateway/tests/__init__.py`
- Create: `llm_gateway/tests/test_bootstrap.py`
- Create: `llm_gateway/tests/test_catalog.py`
- Create: `llm_gateway/tests/test_capability_router.py`
- Create: `llm_gateway/tests/test_process_executor.py`
- Create: `llm_gateway/tests/test_codex_executor.py`
- Create: `llm_gateway/tests/test_claude_executor.py`
- Create: `llm_gateway/tests/test_agent.py`
- Create: `llm_gateway/tests/test_normalizer.py`
- Create: `llm_gateway/tests/test_run_manager.py`
- Create: `llm_gateway/tests/test_gateway_service.py`
- Create: `llm_gateway/tests/test_tasks.py`

## Implementation constraints

- Use @superpowers:test-driven-development for each new behavior.
- Do not add URLs, viewsets, serializers for external HTTP use.
- Do not let business apps pass raw shell commands or raw skill names.
- Do not let `PydanticAI` choose arbitrary executors outside allowed lists.
- Keep `codex` as the preferred executor unless the request or failure path
  requires `claude`.
- Preserve Celery-disabled synchronous execution for local and test workflows.
- Keep all prompt text in `llm_gateway/orchestration/prompts.py`.
- Keep all subprocess logic out of service classes.

## Chunk 1: App bootstrap and persistence

### Task 1: Add app bootstrap, settings defaults, and dependency wiring

**Files:**

- Create: `llm_gateway/__init__.py`
- Create: `llm_gateway/apps.py`
- Create: `llm_gateway/tests/__init__.py`
- Create: `llm_gateway/tests/test_bootstrap.py`
- Modify: `core/settings.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Write the failing bootstrap test**

```python
from django.apps import apps
from django.conf import settings
from django.test import TestCase


class LLMGatewayBootstrapTests(TestCase):
    def test_llm_gateway_is_registered_with_defaults(self):
        self.assertTrue(apps.is_installed("llm_gateway"))
        self.assertEqual(settings.LLM_GATEWAY_DEFAULT_EXECUTOR, "codex")
        self.assertEqual(settings.LLM_GATEWAY_FALLBACK_EXECUTOR, "claude")
        self.assertIn(
            r"C:\Users\Administrator\.agents\skills",
            settings.LLM_GATEWAY_SKILL_DIRS,
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
`python manage.py test llm_gateway.tests.test_bootstrap.LLMGatewayBootstrapTests -v 2`

Expected: FAIL because the app is not registered and the settings do not exist.

- [ ] **Step 3: Add the minimal bootstrap implementation**

Implement:

- `llm_gateway/apps.py` with `LLMGatewayConfig`
- `llm_gateway/__init__.py`
- `core/settings.py` additions:
  - `llm_gateway` in `INSTALLED_APPS`
  - `LLM_GATEWAY_DEFAULT_EXECUTOR = "codex"`
  - `LLM_GATEWAY_FALLBACK_EXECUTOR = "claude"`
  - `LLM_GATEWAY_CODEX_BIN`
  - `LLM_GATEWAY_CLAUDE_BIN`
  - `LLM_GATEWAY_EXECUTION_TIMEOUT_SECONDS = 180`
  - `LLM_GATEWAY_SKILL_DIRS`
  - `LLM_GATEWAY_AGENT_MODEL`
- `requirements.txt` additions for `pydantic-ai`

- [ ] **Step 4: Run the test to verify it passes**

Run:
`python manage.py test llm_gateway.tests.test_bootstrap.LLMGatewayBootstrapTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/settings.py requirements.txt llm_gateway/__init__.py llm_gateway/apps.py llm_gateway/tests/__init__.py llm_gateway/tests/test_bootstrap.py
git commit -m "feat: bootstrap llm gateway app"
```

### Task 2: Add run and event models with migration

**Files:**

- Create: `llm_gateway/models.py`
- Create: `llm_gateway/domain/enums.py`
- Create: `llm_gateway/migrations/0001_initial.py`
- Create: `llm_gateway/tests/test_models.py`

- [ ] **Step 1: Write the failing model tests**

```python
from django.test import TestCase

from llm_gateway.domain.enums import ExecutorType, RunStatus
from llm_gateway.models import LLMRun, LLMRunEvent


class LLMGatewayModelTests(TestCase):
    def test_run_defaults_to_pending_and_codex_preference(self):
        run = LLMRun.objects.create(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills", "limit": 10},
        )
        self.assertEqual(run.status, RunStatus.PENDING)
        self.assertEqual(run.preferred_executor, ExecutorType.CODEX)

    def test_event_sequence_is_stored_per_run(self):
        run = LLMRun.objects.create(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills"},
        )
        event = LLMRunEvent.objects.create(
            run=run,
            sequence=1,
            event_type="run.started",
            payload={"message": "started"},
        )
        self.assertEqual(event.run_id, run.id)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_models.LLMGatewayModelTests -v 2`

Expected: FAIL because models and enums do not exist.

- [ ] **Step 3: Add the minimal model implementation**

Implement:

- `RunStatus` and `ExecutorType` enums in `domain/enums.py`
- `LLMRun` model with:
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
  - timestamps
- `LLMRunEvent` model with:
  - FK to `LLMRun`
  - `sequence`
  - `event_type`
  - `payload`
  - `created_at`
- migration file

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_models.LLMGatewayModelTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add llm_gateway/domain/enums.py llm_gateway/models.py llm_gateway/migrations/0001_initial.py llm_gateway/tests/test_models.py
git commit -m "feat: add llm gateway run persistence models"
```

### Task 3: Add repository helpers for runs and events

**Files:**

- Create: `llm_gateway/repositories/runs.py`
- Create: `llm_gateway/repositories/events.py`
- Modify: `llm_gateway/tests/test_models.py`
- Create: `llm_gateway/tests/test_repositories.py`

- [ ] **Step 1: Write the failing repository tests**

```python
from django.test import TestCase

from llm_gateway.repositories.events import EventRepository
from llm_gateway.repositories.runs import RunRepository


class LLMGatewayRepositoryTests(TestCase):
    def test_run_repository_marks_running(self):
        run = RunRepository.create_run(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills"},
        )
        RunRepository.mark_running(run, selected_executor="codex")
        run.refresh_from_db()
        self.assertEqual(run.status, "running")
        self.assertEqual(run.selected_executor, "codex")

    def test_event_repository_appends_ordered_events(self):
        run = RunRepository.create_run(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills"},
        )
        EventRepository.append(run, "run.started", {"message": "started"})
        EventRepository.append(run, "executor.stdout", {"chunk": "hello"})
        self.assertEqual(run.events.order_by("sequence").count(), 2)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_repositories.LLMGatewayRepositoryTests -v 2`

Expected: FAIL because repositories do not exist.

- [ ] **Step 3: Add the minimal repository implementation**

Implement helper methods for:

- creating runs
- marking runs running, completed, failed, cancelled, timed out
- appending ordered events
- listing events by sequence

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_repositories.LLMGatewayRepositoryTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add llm_gateway/repositories/runs.py llm_gateway/repositories/events.py llm_gateway/tests/test_repositories.py
git commit -m "feat: add llm gateway repositories"
```

## Chunk 2: Skill discovery and executor layer

### Task 4: Add global skill discovery catalog

**Files:**

- Create: `llm_gateway/domain/entities.py`
- Create: `llm_gateway/services/catalog.py`
- Create: `llm_gateway/tests/test_catalog.py`

- [ ] **Step 1: Write the failing catalog tests**

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings

from llm_gateway.services.catalog import SkillCatalogService


class SkillCatalogServiceTests(SimpleTestCase):
    def test_discovers_skill_from_configured_directories(self):
        with TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "wechat-article-search"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: wechat-article-search\ndescription: Search wechat articles\n---\n",
                encoding="utf-8",
            )

            with override_settings(LLM_GATEWAY_SKILL_DIRS=[temp_dir]):
                skills = SkillCatalogService.list_global_skills()

        self.assertEqual(skills[0].name, "wechat-article-search")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_catalog.SkillCatalogServiceTests -v 2`

Expected: FAIL because the catalog service does not exist.

- [ ] **Step 3: Add the minimal catalog implementation**

Implement:

- `CatalogSkill` entity in `domain/entities.py`
- `SkillCatalogService.list_global_skills()`
- `SkillCatalogService.get_skill(name)`
- parsing of `SKILL.md` frontmatter for `name` and `description`

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_catalog.SkillCatalogServiceTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add llm_gateway/domain/entities.py llm_gateway/services/catalog.py llm_gateway/tests/test_catalog.py
git commit -m "feat: add global skill catalog discovery"
```

### Task 5: Add shared subprocess execution helpers

**Files:**

- Create: `llm_gateway/executors/process.py`
- Create: `llm_gateway/tests/test_process_executor.py`

- [ ] **Step 1: Write the failing process tests**

```python
from django.test import SimpleTestCase

from llm_gateway.executors.process import ProcessRunner


class ProcessRunnerTests(SimpleTestCase):
    def test_captures_stdout_and_exit_code(self):
        result = ProcessRunner.run(
            ["python", "-c", "print('hello')"],
            timeout_seconds=5,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("hello", result.stdout)

    def test_times_out_long_running_process(self):
        with self.assertRaises(TimeoutError):
            ProcessRunner.run(
                ["python", "-c", "import time; time.sleep(10)"],
                timeout_seconds=1,
            )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_process_executor.ProcessRunnerTests -v 2`

Expected: FAIL because `ProcessRunner` does not exist.

- [ ] **Step 3: Add the minimal process implementation**

Implement:

- `ProcessRunResult`
- `ProcessRunner.run(...)`
- timeout handling
- UTF-8 decoding
- Windows-safe `subprocess` usage

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_process_executor.ProcessRunnerTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add llm_gateway/executors/process.py llm_gateway/tests/test_process_executor.py
git commit -m "feat: add llm gateway process runner"
```

### Task 6: Add Codex and Claude executors

**Files:**

- Create: `llm_gateway/executors/base.py`
- Create: `llm_gateway/executors/codex.py`
- Create: `llm_gateway/executors/claude.py`
- Create: `llm_gateway/tests/test_codex_executor.py`
- Create: `llm_gateway/tests/test_claude_executor.py`

- [ ] **Step 1: Write the failing executor tests**

```python
from django.test import SimpleTestCase, override_settings

from llm_gateway.executors.codex import CodexExecutor


class CodexExecutorTests(SimpleTestCase):
    @override_settings(LLM_GATEWAY_CODEX_BIN="codex")
    def test_builds_codex_exec_command(self):
        command = CodexExecutor.build_command(
            prompt="Use the wechat-article-search skill only.",
            schema_path="C:/tmp/schema.json",
            output_path="C:/tmp/result.json",
        )
        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn("--output-schema", command)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_codex_executor.CodexExecutorTests llm_gateway.tests.test_claude_executor.ClaudeExecutorTests -v 2`

Expected: FAIL because the executor classes do not exist.

- [ ] **Step 3: Add the minimal executor implementation**

Implement:

- abstract executor contract in `base.py`
- `CodexExecutor.build_command(...)`
- `ClaudeExecutor.build_command(...)`
- `run(...)` methods that delegate to `ProcessRunner`
- structured return objects that include:
  - `stdout`
  - `stderr`
  - `exit_code`
  - `executor_name`

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_codex_executor.CodexExecutorTests llm_gateway.tests.test_claude_executor.ClaudeExecutorTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add llm_gateway/executors/base.py llm_gateway/executors/codex.py llm_gateway/executors/claude.py llm_gateway/tests/test_codex_executor.py llm_gateway/tests/test_claude_executor.py
git commit -m "feat: add codex and claude executors"
```

## Chunk 3: Orchestration and capability services

### Task 7: Add capability request and result schemas plus router

**Files:**

- Create: `llm_gateway/schemas/requests.py`
- Create: `llm_gateway/schemas/results.py`
- Create: `llm_gateway/schemas/events.py`
- Create: `llm_gateway/services/capability_router.py`
- Create: `llm_gateway/tests/test_capability_router.py`

- [ ] **Step 1: Write the failing router tests**

```python
from django.test import SimpleTestCase

from llm_gateway.services.capability_router import CapabilityRouter


class CapabilityRouterTests(SimpleTestCase):
    def test_wechat_article_search_prefers_codex(self):
        plan = CapabilityRouter.resolve(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills", "limit": 10},
        )
        self.assertEqual(plan.preferred_executor, "codex")
        self.assertIn("claude", plan.allowed_executors)
        self.assertEqual(plan.skill_hint, "wechat-article-search")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_capability_router.CapabilityRouterTests -v 2`

Expected: FAIL because the router does not exist.

- [ ] **Step 3: Add the minimal router and schemas**

Implement:

- request schema for `WechatArticleSearchRequest`
- result schema for `WechatArticleSearchResult`
- event schema for run events
- capability router returning an `ExecutionPlan`

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_capability_router.CapabilityRouterTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add llm_gateway/schemas/requests.py llm_gateway/schemas/results.py llm_gateway/schemas/events.py llm_gateway/services/capability_router.py llm_gateway/tests/test_capability_router.py
git commit -m "feat: add llm gateway capability router"
```

### Task 8: Add PydanticAI orchestration and prompt templates

**Files:**

- Create: `llm_gateway/orchestration/prompts.py`
- Create: `llm_gateway/orchestration/agent.py`
- Create: `llm_gateway/tests/test_agent.py`

- [ ] **Step 1: Write the failing orchestration tests**

```python
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from llm_gateway.orchestration.agent import LLMGatewayAgentService


class LLMGatewayAgentServiceTests(SimpleTestCase):
    @patch("llm_gateway.orchestration.agent.Agent")
    def test_builds_executor_instruction_for_wechat_search(self, agent_cls):
        fake_agent = Mock()
        fake_agent.run_sync.return_value.output = {
            "prompt": "Use the wechat-article-search skill only.",
            "selected_executor": "codex",
            "output_mode": "json",
        }
        agent_cls.return_value = fake_agent

        instruction = LLMGatewayAgentService.build_instruction(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills", "limit": 10},
            allowed_executors=["codex", "claude"],
            preferred_executor="codex",
        )

        self.assertEqual(instruction.selected_executor, "codex")
        self.assertIn("wechat-article-search", instruction.prompt)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_agent.LLMGatewayAgentServiceTests -v 2`

Expected: FAIL because the orchestration layer does not exist.

- [ ] **Step 3: Add the minimal orchestration implementation**

Implement:

- prompt builders in `prompts.py`
- `LLMGatewayAgentService.build_instruction(...)`
- environment-backed `PydanticAI` model wiring
- an output schema for executor instruction objects

Keep tests fully mocked so no network model call happens.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_agent.LLMGatewayAgentServiceTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add llm_gateway/orchestration/prompts.py llm_gateway/orchestration/agent.py llm_gateway/tests/test_agent.py
git commit -m "feat: add llm gateway orchestration layer"
```

### Task 9: Add output normalization

**Files:**

- Create: `llm_gateway/services/normalizer.py`
- Create: `llm_gateway/tests/test_normalizer.py`

- [ ] **Step 1: Write the failing normalizer tests**

```python
from django.test import SimpleTestCase

from llm_gateway.services.normalizer import ResultNormalizer


class ResultNormalizerTests(SimpleTestCase):
    def test_normalizes_wechat_article_search_json_output(self):
        result = ResultNormalizer.normalize(
            capability="wechat_article_search",
            raw_stdout='{"items": [{"title": "A", "url": "https://example.com"}], "total": 1}',
            executor_name="codex",
            used_skill="wechat-article-search",
        )
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["executor"], "codex")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_normalizer.ResultNormalizerTests -v 2`

Expected: FAIL because the normalizer does not exist.

- [ ] **Step 3: Add the minimal normalizer implementation**

Implement:

- JSON parsing first
- fallback to raw text envelope
- capability-specific shape for `wechat_article_search`

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_normalizer.ResultNormalizerTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add llm_gateway/services/normalizer.py llm_gateway/tests/test_normalizer.py
git commit -m "feat: add llm gateway result normalizer"
```

## Chunk 4: Run lifecycle, tasks, and business-facing service

### Task 10: Add run manager lifecycle orchestration

**Files:**

- Create: `llm_gateway/services/run_manager.py`
- Create: `llm_gateway/tests/test_run_manager.py`

- [ ] **Step 1: Write the failing run manager tests**

```python
from unittest.mock import Mock, patch

from django.test import TestCase

from llm_gateway.services.run_manager import RunManager


class RunManagerTests(TestCase):
    @patch("llm_gateway.services.run_manager.LLMGatewayAgentService")
    @patch("llm_gateway.services.run_manager.CodexExecutor")
    def test_executes_run_with_codex_first(self, codex_cls, agent_cls):
        agent_cls.build_instruction.return_value = Mock(
            selected_executor="codex",
            prompt="Use the wechat-article-search skill only.",
            used_skill="wechat-article-search",
        )
        codex_cls.return_value.run.return_value = Mock(
            stdout='{"items": [], "total": 0}',
            stderr="",
            exit_code=0,
            executor_name="codex",
        )

        run = RunManager.create_run(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills", "limit": 10},
        )
        completed = RunManager.execute_run(run.id)
        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.selected_executor, "codex")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_run_manager.RunManagerTests -v 2`

Expected: FAIL because `RunManager` does not exist.

- [ ] **Step 3: Add the minimal run manager implementation**

Implement:

- `create_run(...)`
- `execute_run(run_id)`
- codex-first execution
- claude fallback on eligible failure
- repository status updates
- event appends for started, stdout, stderr, completed, failed

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_run_manager.RunManagerTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add llm_gateway/services/run_manager.py llm_gateway/tests/test_run_manager.py
git commit -m "feat: add llm gateway run manager"
```

### Task 11: Add Celery task entry points and sync fallback coverage

**Files:**

- Create: `llm_gateway/tasks.py`
- Create: `llm_gateway/tests/test_tasks.py`

- [ ] **Step 1: Write the failing task tests**

```python
from unittest.mock import patch

from django.test import TestCase, override_settings

from llm_gateway.services.run_manager import RunManager
from llm_gateway.tasks import execute_llm_run


class LLMGatewayTaskTests(TestCase):
    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True)
    @patch("llm_gateway.tasks.RunManager.execute_run")
    def test_execute_llm_run_calls_run_manager(self, execute_run_mock):
        run = RunManager.create_run(
            capability="wechat_article_search",
            input_payload={"query": "Claude Code skills"},
        )
        execute_llm_run.run(run.id)
        execute_run_mock.assert_called_once_with(run.id)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_tasks.LLMGatewayTaskTests -v 2`

Expected: FAIL because the task module does not exist.

- [ ] **Step 3: Add the minimal task implementation**

Implement:

- `@shared_task(bind=True)` execute task
- populate `celery_task_id` when available
- call `RunManager.execute_run(...)`

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_tasks.LLMGatewayTaskTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add llm_gateway/tasks.py llm_gateway/tests/test_tasks.py
git commit -m "feat: add llm gateway celery tasks"
```

### Task 12: Add the business-facing gateway service for WeChat article search

**Files:**

- Create: `llm_gateway/services/gateway.py`
- Create: `llm_gateway/tests/test_gateway_service.py`

- [ ] **Step 1: Write the failing gateway tests**

```python
from unittest.mock import patch

from django.test import TestCase

from llm_gateway.services.gateway import LLMGatewayService


class LLMGatewayServiceTests(TestCase):
    @patch("llm_gateway.services.gateway.RunManager")
    def test_search_wechat_articles_hides_skill_details(self, run_manager):
        run_manager.run_capability.return_value = {
            "items": [{"title": "A", "url": "https://example.com"}],
            "total": 1,
            "executor": "codex",
            "used_skill": "wechat-article-search",
        }

        result = LLMGatewayService.search_wechat_articles(
            query="Claude Code skills",
            limit=10,
            requested_by_app="wechat",
        )

        self.assertEqual(result["total"], 1)
        self.assertNotIn("used_skill", result)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test llm_gateway.tests.test_gateway_service.LLMGatewayServiceTests -v 2`

Expected: FAIL because the gateway service does not exist.

- [ ] **Step 3: Add the minimal gateway implementation**

Implement:

- `LLMGatewayService.search_wechat_articles(...)`
- request validation through schema objects
- delegation to `RunManager`
- stripping of internal implementation details before returning to callers

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test llm_gateway.tests.test_gateway_service.LLMGatewayServiceTests -v 2`

Expected: PASS

- [ ] **Step 5: Run the focused app test suite**

Run:
`python manage.py test llm_gateway.tests -v 2`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add llm_gateway/services/gateway.py llm_gateway/tests/test_gateway_service.py
git commit -m "feat: add llm gateway business capability service"
```

## Final verification

- [ ] **Step 1: Run migrations**

Run:
`python manage.py makemigrations llm_gateway`

Expected: No unexpected model changes beyond `0001_initial.py`

- [ ] **Step 2: Run the full llm_gateway test suite**

Run:
`python manage.py test llm_gateway.tests -v 2`

Expected: PASS

- [ ] **Step 3: Run a targeted project regression suite**

Run:
`python manage.py test we_rss.tests.test_task_workflows -v 2`

Expected: PASS so the Celery integration pattern stays compatible with
existing code.

- [ ] **Step 4: Smoke-test skill discovery and a mocked capability run in the shell**

Run:
`python manage.py shell`

Then:

```python
from llm_gateway.services.gateway import LLMGatewayService
```

Expected: Import succeeds without requiring public URLs or views.

## Execution handoff

Plan complete and saved to
`docs/superpowers/plans/2026-04-09-llm-gateway-implementation.md`. Ready to
execute?
