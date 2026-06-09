from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Member


class ImagePromptStreamingApiTests(APITestCase):
    def setUp(self):
        self.member = Member.objects.create(
            username="image-prompt-member",
            email="image-prompt@example.com",
        )
        self.client.force_authenticate(user=self.member)

    @patch("image_prompt.views.SeriesCharacterService.stream_analysis")
    def test_analyze_series_characters_returns_sse_stream(self, stream_analysis):
        stream_analysis.return_value = iter(
            [
                {
                    "event": "progress",
                    "payload": {
                        "stage": "analyzing_characters",
                        "message": "正在分析",
                    },
                },
                {
                    "event": "completed",
                    "result": {
                        "recommended_main_characters": [],
                        "temporary_characters": [],
                        "analysis_notes": ["done"],
                    },
                },
            ]
        )

        response = self.client.post(
            "/api/v1/image-prompt/analyze-series-characters/",
            {"source_text": "故事文本", "series_name": "系列名"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/event-stream")

        body = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn("event: start", body)
        self.assertIn("event: completed", body)

    @patch("image_prompt.views.SeriesCharacterService.stream_analysis")
    def test_analyze_series_characters_accepts_text_event_stream_header(self, stream_analysis):
        stream_analysis.return_value = iter(
            [
                {
                    "event": "completed",
                    "result": {
                        "recommended_main_characters": [],
                        "temporary_characters": [],
                        "analysis_notes": ["done"],
                    },
                },
            ]
        )

        response = self.client.post(
            "/api/v1/image-prompt/analyze-series-characters/",
            {"source_text": "story text", "series_name": "series name"},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/event-stream")

    @patch("image_prompt.views.JokeToComicService.stream_prompt_pack")
    def test_joke_to_comic_returns_completed_event(self, stream_prompt_pack):
        stream_prompt_pack.return_value = iter(
            [
                {
                    "event": "progress",
                    "payload": {
                        "stage": "planning_comic",
                        "message": "正在规划",
                    },
                },
                {
                    "event": "completed",
                    "result": {
                        "title": "办公室笑话",
                        "source_joke": "一个程序员笑话",
                        "format": {
                            "panel_count": 4,
                            "image_width": 1080,
                            "image_height": 1440,
                            "page_layout": "2x2",
                        },
                        "story_summary": "summary",
                        "humor_explanation": "humor",
                        "negative_prompt": "negative",
                        "generation_notes": ["done"],
                        "panels": [],
                        "page_prompt": "2x2 comic page",
                    },
                },
            ]
        )

        response = self.client.post(
            "/api/v1/image-prompt/joke-to-comic/",
            {"joke": "一个程序员笑话", "confirmed_characters": []},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/event-stream")

        body = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn("event: start", body)
        self.assertIn("event: completed", body)

    @patch("image_prompt.views.JokeToComicService.stream_prompt_pack")
    def test_joke_to_comic_accepts_text_event_stream_header(self, stream_prompt_pack):
        stream_prompt_pack.return_value = iter(
            [
                {
                    "event": "completed",
                    "result": {
                        "title": "office joke",
                        "source_joke": "a programmer joke",
                        "format": {
                            "panel_count": 4,
                            "image_width": 1080,
                            "image_height": 1440,
                            "page_layout": "2x2",
                        },
                        "story_summary": "summary",
                        "humor_explanation": "humor",
                        "negative_prompt": "negative",
                        "generation_notes": ["done"],
                        "panels": [],
                        "page_prompt": "2x2 comic page",
                    },
                },
            ]
        )

        response = self.client.post(
            "/api/v1/image-prompt/joke-to-comic/",
            {"joke": "a programmer joke", "confirmed_characters": []},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/event-stream")

    @patch("image_prompt.views.JokeToComicService.stream_prompt_pack")
    def test_joke_to_comic_returns_error_event_when_service_fails(self, stream_prompt_pack):
        def raising_stream(*args, **kwargs):
            raise RuntimeError("comic planning failed")
            yield

        stream_prompt_pack.side_effect = raising_stream

        response = self.client.post(
            "/api/v1/image-prompt/joke-to-comic/",
            {"joke": "一个程序员笑话", "confirmed_characters": []},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn("event: error", body)
        self.assertNotIn("event: completed", body)
