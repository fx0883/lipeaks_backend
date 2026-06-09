from django.test import SimpleTestCase
from drf_spectacular.generators import SchemaGenerator


class ImagePromptSchemaTests(SimpleTestCase):
    def test_schema_includes_streaming_endpoints(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        analyze_path = "/api/v1/image-prompt/analyze-series-characters/"
        joke_path = "/api/v1/image-prompt/joke-to-comic/"

        self.assertIn(analyze_path, schema["paths"])
        self.assertIn(joke_path, schema["paths"])

        analyze_operation = schema["paths"][analyze_path]["post"]
        joke_operation = schema["paths"][joke_path]["post"]

        self.assertIn("text/event-stream", analyze_operation["responses"]["200"]["content"])
        self.assertIn("text/event-stream", joke_operation["responses"]["200"]["content"])
        self.assertIn("completed", analyze_operation["description"])
        self.assertIn("completed", joke_operation["description"])
