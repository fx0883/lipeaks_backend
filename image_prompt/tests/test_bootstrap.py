from django.apps import apps
from django.test import SimpleTestCase
from django.urls import resolve


class ImagePromptBootstrapTests(SimpleTestCase):
    def test_image_prompt_is_installed(self):
        self.assertTrue(apps.is_installed("image_prompt"))

    def test_public_routes_resolve(self):
        analyze_match = resolve("/api/v1/image-prompt/analyze-series-characters/")
        joke_match = resolve("/api/v1/image-prompt/joke-to-comic/")

        self.assertEqual(
            analyze_match.view_name,
            "image-prompt:analyze-series-characters",
        )
        self.assertEqual(
            joke_match.view_name,
            "image-prompt:joke-to-comic",
        )
