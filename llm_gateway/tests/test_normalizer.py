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

    def test_normalizes_skill_output_when_articles_key_is_used(self):
        result = ResultNormalizer.normalize(
            capability="wechat_article_search",
            raw_stdout='{"query": "AI Agent", "total": 1, "articles": [{"title": "A", "url": "https://example.com"}]}',
            executor_name="codex",
            used_skill="wechat-article-search",
        )
        self.assertEqual(result["query"], "AI Agent")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["title"], "A")

    def test_preserves_full_public_article_fields_from_skill_output(self):
        result = ResultNormalizer.normalize(
            capability="wechat_article_search",
            raw_stdout=(
                '{"query": "skill", "total": 1, "articles": ['
                '{"title": "Skill article", "url": "https://example.com", '
                '"summary": "Summary text", "datetime": "2026-04-10 10:00:00", '
                '"date_text": "2026-04-10", "date_description": "today", "source": "OpenAI"}]}'
            ),
            executor_name="codex",
            used_skill="wechat-article-search",
        )

        self.assertEqual(result["items"][0]["title"], "Skill article")
        self.assertEqual(result["items"][0]["summary"], "Summary text")
        self.assertEqual(result["items"][0]["datetime"], "2026-04-10 10:00:00")
        self.assertEqual(result["items"][0]["date_text"], "2026-04-10")
        self.assertEqual(result["items"][0]["date_description"], "today")
        self.assertEqual(result["items"][0]["source"], "OpenAI")

    def test_repairs_utf8_as_gbk_mojibake_in_wechat_article_fields(self):
        result = ResultNormalizer.normalize(
            capability="wechat_article_search",
            raw_stdout=(
                '{"query": "AI Agent", "total": 1, "articles": ['
                '{"title": "AI Agent \\u7039\\u70b4\\u57ac \\u9983\\u6b8c", "url": "https://example.com", '
                '"summary": "emoji \\u93c0\\ue21b\\u5bd4 \\u9983\\u6b8c", "date_description": "\\u6d60\\u5a42\\u3049"}]}'
            ),
            executor_name="codex",
            used_skill="wechat-article-search",
        )

        self.assertEqual(result["items"][0]["title"], "AI Agent \u5b9e\u6218 \U0001f680")
        self.assertEqual(result["items"][0]["summary"], "emoji \u652f\u6301 \U0001f680")
        self.assertEqual(result["items"][0]["date_description"], "\u4eca\u5929")

    def test_normalizes_markdown_format_text_output(self):
        result = ResultNormalizer.normalize(
            capability="markdown_format",
            raw_stdout="# Title\n\nBody",
            executor_name="codex",
            used_skill="baoyu-format-markdown",
        )

        self.assertEqual(result["formatted_markdown"], "# Title\n\nBody")
        self.assertEqual(result["executor"], "codex")

    def test_markdown_format_rejects_empty_output(self):
        with self.assertRaisesMessage(ValueError, "Formatted markdown content is empty."):
            ResultNormalizer.normalize(
                capability="markdown_format",
                raw_stdout="   ",
                executor_name="codex",
                used_skill="baoyu-format-markdown",
            )

    def test_markdown_format_rejects_interactive_follow_up_output(self):
        with self.assertRaisesMessage(ValueError, "Formatted markdown content is not usable Markdown output."):
            ResultNormalizer.normalize(
                capability="markdown_format",
                raw_stdout=(
                    "Using `baoyu-format-markdown` for this.\n\n"
                    "I need the source content first. Send either:\n"
                    "- the text to format, or\n"
                    "- a file path in this workspace\n"
                ),
                executor_name="codex",
                used_skill="baoyu-format-markdown",
            )

    def test_markdown_format_rejects_subagent_meta_output(self):
        with self.assertRaisesMessage(ValueError, "Formatted markdown content is not usable Markdown output."):
            ResultNormalizer.normalize(
                capability="markdown_format",
                raw_stdout=(
                    "Using `subagent-driven-development` only for the subagent constraint here.\n\n"
                    "Send the bounded task in this form:\n"
                    "1. Objective\n"
                    "2. Files or subsystem in scope\n"
                    "3. Expected output\n"
                    "4. Constraints\n"
                    "5. Verification criteria\n\n"
                    "Once you provide that, I'll execute just that slice.\n"
                ),
                executor_name="codex",
                used_skill="baoyu-format-markdown",
            )
