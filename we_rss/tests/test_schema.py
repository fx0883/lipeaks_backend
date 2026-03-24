from django.test import SimpleTestCase
from drf_spectacular.generators import SchemaGenerator


class WeRssSchemaTests(SimpleTestCase):
    def _resolve_schema(self, schema, schema_or_ref):
        if "$ref" not in schema_or_ref:
            return schema_or_ref

        ref = schema_or_ref["$ref"]
        prefix = "#/components/schemas/"
        self.assertTrue(ref.startswith(prefix), msg=ref)
        return schema["components"]["schemas"][ref.removeprefix(prefix)]

    def test_all_we_rss_operations_use_unified_tag_and_have_summary(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        we_rss_paths = {
            path: methods
            for path, methods in schema["paths"].items()
            if path.startswith("/api/v1/we-rss/")
        }

        self.assertTrue(we_rss_paths)

        for path, methods in we_rss_paths.items():
            for method, operation in methods.items():
                self.assertEqual(operation["tags"], ["we-rss"], msg=f"{method.upper()} {path}")
                self.assertTrue(operation.get("summary"), msg=f"{method.upper()} {path}")
                self.assertTrue(operation.get("description"), msg=f"{method.upper()} {path}")

    def test_we_rss_schema_includes_examples_for_json_and_rss_endpoints(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        login_create = schema["paths"]["/api/v1/we-rss/credentials/login-sessions/"]["post"]
        self.assertIn("examples", login_create["responses"]["201"]["content"]["application/json"])

        rss_tenant = schema["paths"]["/api/v1/we-rss/rss/"]["get"]
        self.assertIn("examples", rss_tenant["responses"]["200"]["content"]["application/xml"])

        rss_content = schema["paths"]["/api/v1/we-rss/rss/content/{article_id}/"]["get"]
        self.assertIn("examples", rss_content["responses"]["200"]["content"]["text/html"])

    def test_we_rss_json_responses_document_standard_response_envelope(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        for path, method, status_code in [
            ("/api/v1/we-rss/credentials/", "get", "200"),
            ("/api/v1/we-rss/feeds/", "post", "201"),
            ("/api/v1/we-rss/articles/import-by-url/", "post", "200"),
        ]:
            response_schema = self._resolve_schema(
                schema,
                schema["paths"][path][method]["responses"][status_code]["content"]["application/json"]["schema"],
            )
            properties = response_schema["properties"]

            self.assertIn("success", properties, msg=f"{method.upper()} {path}")
            self.assertIn("code", properties, msg=f"{method.upper()} {path}")
            self.assertIn("message", properties, msg=f"{method.upper()} {path}")
            self.assertIn("data", properties, msg=f"{method.upper()} {path}")

    def test_all_we_rss_operations_document_required_x_tenant_id_header(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        for path, methods in schema["paths"].items():
            if not path.startswith("/api/v1/we-rss/"):
                continue

            for method, operation in methods.items():
                parameters = operation.get("parameters", [])
                header = next(
                    (
                        parameter
                        for parameter in parameters
                        if parameter.get("in") == "header" and parameter.get("name") == "X-Tenant-ID"
                    ),
                    None,
                )
                self.assertIsNotNone(header, msg=f"{method.upper()} {path}")
                self.assertTrue(header.get("required"), msg=f"{method.upper()} {path}")

    def test_task_operations_document_detailed_sync_examples(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        sync_examples = schema["paths"]["/api/v1/we-rss/feeds/{id}/sync/"]["post"]["responses"]["200"]["content"][
            "application/json"
        ]["examples"]
        task_examples = schema["paths"]["/api/v1/we-rss/tasks/{task_id}/"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["examples"]

        sync_example_value = sync_examples["FeedSyncSuccessResponse"]["value"]
        failed_task_example = task_examples["FeedSyncTaskFailedResponse"]["value"]

        self.assertEqual(sync_example_value["data"]["result_payload"]["detail_success_count"], 2)
        self.assertEqual(sync_example_value["data"]["result_payload"]["detail_failed_count"], 1)
        self.assertEqual(len(sync_example_value["data"]["failed_articles"]), 1)
        self.assertEqual(failed_task_example["data"]["status"], "failed")
        self.assertEqual(failed_task_example["data"]["result_payload"]["task_type"], "feed_sync")

    def test_task_list_operation_documents_filter_parameters(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/tasks/"]["get"]
        parameter_names = {parameter["name"] for parameter in operation["parameters"]}

        self.assertIn("task_type", parameter_names)
        self.assertIn("status", parameter_names)
        self.assertIn("target_type", parameter_names)
        self.assertIn("target_id", parameter_names)

    def test_article_list_operation_documents_article_type_filter_and_field(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/articles/"]["get"]
        parameter_names = {parameter["name"] for parameter in operation["parameters"]}
        self.assertIn("article_type", parameter_names)

        response_schema = self._resolve_schema(
            schema,
            operation["responses"]["200"]["content"]["application/json"]["schema"],
        )
        article_list_schema = self._resolve_schema(schema, response_schema["properties"]["data"])
        article_schema = self._resolve_schema(schema, article_list_schema["items"])
        self.assertIn("article_type", article_schema["properties"])

    def test_detail_and_action_routes_document_id_parameter_description(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        for path, method in [
            ("/api/v1/we-rss/credentials/{id}/", "get"),
            ("/api/v1/we-rss/credentials/{id}/check/", "post"),
            ("/api/v1/we-rss/feeds/{id}/", "get"),
            ("/api/v1/we-rss/feeds/{id}/sync/", "post"),
            ("/api/v1/we-rss/feeds/{id}/articles/", "delete"),
            ("/api/v1/we-rss/articles/{id}/", "get"),
            ("/api/v1/we-rss/articles/{id}/refresh/", "post"),
        ]:
            operation = schema["paths"][path][method]
            parameter = next(
                parameter
                for parameter in operation["parameters"]
                if parameter["in"] == "path" and parameter["name"] == "id"
            )

            self.assertTrue(parameter.get("description"), msg=f"{method.upper()} {path}")

    def test_feed_article_clear_operation_documents_deleted_count_response(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/feeds/{id}/articles/"]["delete"]

        response_schema = self._resolve_schema(
            schema,
            operation["responses"]["200"]["content"]["application/json"]["schema"],
        )
        data_schema = self._resolve_schema(schema, response_schema["properties"]["data"])
        self.assertIn("feed_id", data_schema["properties"])
        self.assertIn("deleted_count", data_schema["properties"])

    def test_request_body_operations_include_examples_for_every_documented_media_type(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        for path, methods in schema["paths"].items():
            if not path.startswith("/api/v1/we-rss/"):
                continue

            for method, operation in methods.items():
                request_body = operation.get("requestBody", {})
                content = request_body.get("content", {}) if isinstance(request_body, dict) else {}
                for media_type, media_schema in content.items():
                    self.assertIn("examples", media_schema, msg=f"{method.upper()} {path} {media_type}")
