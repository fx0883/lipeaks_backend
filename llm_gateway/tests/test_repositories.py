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
