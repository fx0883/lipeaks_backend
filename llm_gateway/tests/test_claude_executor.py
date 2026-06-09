from django.test import SimpleTestCase, override_settings

from llm_gateway.executors.claude import ClaudeExecutor


class ClaudeExecutorTests(SimpleTestCase):
    @override_settings(LLM_GATEWAY_CLAUDE_BIN="claude")
    def test_builds_claude_print_command(self):
        command = ClaudeExecutor.build_command(
            prompt="Use the wechat-article-search skill only.",
            schema_path="C:/tmp/schema.json",
            output_path="C:/tmp/result.json",
        )
        self.assertEqual(command[:2], ["claude", "-p"])
        self.assertIn("--json-schema", command)
        self.assertIn("--output-format", command)
