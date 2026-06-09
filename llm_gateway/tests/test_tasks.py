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
