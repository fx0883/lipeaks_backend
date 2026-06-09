from django.test import SimpleTestCase

from image_prompt.services.sse import encode_sse_event


class ImagePromptSseTests(SimpleTestCase):
    def test_encodes_named_event_with_json_payload(self):
        payload = encode_sse_event(
            "progress",
            {"stage": "analyzing", "message": "Starting"},
        )

        self.assertEqual(
            payload.decode("utf-8"),
            'event: progress\ndata: {"stage":"analyzing","message":"Starting"}\n\n',
        )

    def test_encodes_error_event_without_ascii_escaping(self):
        payload = encode_sse_event("error", {"message": "角色分析服务暂时不可用"})

        self.assertIn("角色分析服务暂时不可用", payload.decode("utf-8"))
