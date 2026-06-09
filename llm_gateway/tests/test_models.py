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
