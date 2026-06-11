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
        self.assertIn("examples", rss_content["responses"]["200"]["content"]["text/markdown"])

        article_export = schema["paths"]["/api/v1/we-rss/articles/export/"]["post"]
        self.assertIn("examples", article_export["requestBody"]["content"]["application/json"])
        self.assertIn("examples", article_export["responses"]["200"]["content"]["text/csv"])

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
            "text/event-stream"
        ]["examples"]
        task_examples = schema["paths"]["/api/v1/we-rss/tasks/{task_id}/"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["examples"]

        sync_example_value = sync_examples["FeedSyncStreamExample"]["value"]
        failed_task_example = task_examples["FeedSyncTaskFailedResponse"]["value"]

        self.assertIn("event: start", sync_example_value)
        self.assertIn("event: batch", sync_example_value)
        self.assertIn("event: done", sync_example_value)
        self.assertEqual(failed_task_example["data"]["status"], "failed")
        self.assertEqual(failed_task_example["data"]["task_type"], "feed_sync_run")
        self.assertEqual(failed_task_example["data"]["result_payload"]["run_status"], "failed")

    def test_task_schema_documents_batched_feed_sync_types(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/tasks/"]["get"]
        task_type_param = next(
            item for item in operation["parameters"] if item["name"] == "task_type"
        )

        self.assertIn("feed_sync_run", task_type_param["description"])
        self.assertIn("feed_sync_batch", task_type_param["description"])

    def test_feed_sync_examples_include_incremental_and_terminal_parent_payloads(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        task_examples = schema["paths"]["/api/v1/we-rss/tasks/{task_id}/"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["examples"]

        running_example = task_examples["FeedSyncTaskSuccessResponse"]["value"]
        timed_out_example = task_examples["FeedSyncTaskTimedOutResponse"]["value"]
        partial_example = task_examples["FeedSyncTaskPartialSuccessResponse"]["value"]

        self.assertEqual(running_example["data"]["result_payload"]["poll_after_seconds"], 5)
        self.assertIn("articles", running_example["data"]["result_payload"]["latest_completed_batch"])
        self.assertEqual(timed_out_example["data"]["status"], "timed_out")
        self.assertEqual(timed_out_example["data"]["result_payload"]["run_status"], "timed_out")
        self.assertEqual(partial_example["data"]["status"], "partial_success")
        self.assertEqual(partial_example["data"]["result_payload"]["run_status"], "partial_success")

    def test_feed_sync_operation_documents_scope_request_body(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/feeds/{id}/sync/"]["post"]

        request_schema = self._resolve_schema(
            schema,
            operation["requestBody"]["content"]["application/json"]["schema"],
        )
        examples = operation["requestBody"]["content"]["application/json"]["examples"]

        self.assertIn("sync_scope", request_schema["properties"])
        self.assertIn("window_days", request_schema["properties"])
        self.assertIn("refresh_markdown", request_schema["properties"])
        self.assertEqual(request_schema["properties"]["window_days"]["minimum"], 1)
        self.assertEqual(request_schema["properties"]["window_days"]["maximum"], 180)
        self.assertIn("FeedSyncFullRequest", examples)
        self.assertIn("FeedSyncLatestRequest", examples)
        self.assertIn("FeedSyncWindowRequest", examples)

    def test_task_list_operation_documents_filter_parameters(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/tasks/"]["get"]
        parameter_names = {parameter["name"] for parameter in operation["parameters"]}

        self.assertIn("task_type", parameter_names)
        self.assertIn("status", parameter_names)
        self.assertIn("target_type", parameter_names)
        self.assertIn("target_id", parameter_names)

    def test_article_list_operation_documents_filters_and_article_type_field(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/articles/"]["get"]
        parameter_names = {parameter["name"] for parameter in operation["parameters"]}
        self.assertIn("article_type", parameter_names)
        self.assertIn("feed_id", parameter_names)
        self.assertIn("page", parameter_names)
        self.assertIn("page_size", parameter_names)

        response_schema = self._resolve_schema(
            schema,
            operation["responses"]["200"]["content"]["application/json"]["schema"],
        )
        article_list_schema = self._resolve_schema(schema, response_schema["properties"]["data"])
        self.assertIn("pagination", article_list_schema["properties"])
        self.assertIn("results", article_list_schema["properties"])
        results_schema = self._resolve_schema(schema, article_list_schema["properties"]["results"])
        article_schema = self._resolve_schema(schema, results_schema["items"])
        self.assertIn("article_type", article_schema["properties"])

    def test_article_search_operation_is_documented(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/articles/search/"]["get"]

        self.assertEqual(operation["operationId"], "we_rss_articles_search")
        self.assertIn("Sogou", operation["description"])
        self.assertNotIn("llm_gateway", operation["description"])
        parameter_names = {parameter["name"] for parameter in operation["parameters"]}
        self.assertIn("query", parameter_names)
        self.assertIn("limit", parameter_names)

        response_schema = self._resolve_schema(
            schema,
            operation["responses"]["200"]["content"]["application/json"]["schema"],
        )
        data_schema = self._resolve_schema(schema, response_schema["properties"]["data"])
        item_schema = self._resolve_schema(schema, data_schema["properties"]["items"]["items"])

        self.assertIn("query", data_schema["properties"])
        self.assertIn("total", data_schema["properties"])
        self.assertIn("items", data_schema["properties"])
        self.assertIn("title", item_schema["properties"])
        self.assertIn("url", item_schema["properties"])

    def test_article_stats_refresh_by_url_operation_is_documented(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/article-stats/refresh-by-url/"]["post"]

        self.assertEqual(operation["operationId"], "we_rss_article_stats_refresh_by_url")
        self.assertIn("examples", operation["requestBody"]["content"]["application/json"])

        response_content = operation["responses"]["200"]["content"]
        self.assertIn("text/event-stream", response_content)
        examples = response_content["text/event-stream"]["examples"]
        self.assertIn("ArticleStatsRefreshStreamExample", examples)
        self.assertIn("event: progress", examples["ArticleStatsRefreshStreamExample"]["value"])

    def test_article_stats_batch_refresh_operation_is_documented(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/article-stats/refresh/"]["post"]

        self.assertEqual(operation["operationId"], "we_rss_article_stats_batch_refresh")
        self.assertIn("examples", operation["requestBody"]["content"]["application/json"])

        request_schema = self._resolve_schema(
            schema,
            operation["requestBody"]["content"]["application/json"]["schema"],
        )
        self.assertIn("article_ids", request_schema["properties"])
        self.assertIn("feed_id", request_schema["properties"])
        self.assertIn("member_id", request_schema["properties"])

        response_content = operation["responses"]["200"]["content"]
        self.assertIn("text/event-stream", response_content)
        examples = response_content["text/event-stream"]["examples"]
        self.assertIn("ArticleStatsBatchRefreshStreamExample", examples)
        self.assertIn("event: start", examples["ArticleStatsBatchRefreshStreamExample"]["value"])
        self.assertIn("event: done", examples["ArticleStatsBatchRefreshStreamExample"]["value"])

    def test_markdown_format_operation_is_documented(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/markdown/format/"]["post"]

        self.assertEqual(operation["operationId"], "we_rss_markdown_format")
        self.assertIn("examples", operation["requestBody"]["content"]["application/json"])

        request_schema = self._resolve_schema(
            schema,
            operation["requestBody"]["content"]["application/json"]["schema"],
        )
        self.assertIn("content", request_schema["properties"])
        self.assertIn("mode", request_schema["properties"])

        response_schema = self._resolve_schema(
            schema,
            operation["responses"]["200"]["content"]["application/json"]["schema"],
        )
        data_schema = self._resolve_schema(schema, response_schema["properties"]["data"])
        self.assertIn("formatted_markdown", data_schema["properties"])
        self.assertIn("mode", data_schema["properties"])
        self.assertIn("executor", data_schema["properties"])

    def test_feed_content_refresh_operation_is_documented(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/feeds/{id}/refresh-content/"]["post"]

        self.assertEqual(operation["operationId"], "we_rss_feeds_refresh_content")
        response_content = operation["responses"]["200"]["content"]
        self.assertIn("text/event-stream", response_content)
        examples = response_content["text/event-stream"]["examples"]
        self.assertIn("FeedContentRefreshStreamExample", examples)
        self.assertIn("event: progress", examples["FeedContentRefreshStreamExample"]["value"])

    def test_article_content_refresh_operation_is_documented(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/articles/{id}/refresh/"]["post"]

        self.assertEqual(operation["operationId"], "we_rss_articles_refresh")
        self.assertEqual(operation["responses"]["200"]["description"], "No response body")

    def test_detail_and_action_routes_document_id_parameter_description(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        for path, method in [
            ("/api/v1/we-rss/credentials/{id}/", "get"),
            ("/api/v1/we-rss/credentials/{id}/check/", "post"),
            ("/api/v1/we-rss/feeds/{id}/", "get"),
            ("/api/v1/we-rss/feeds/{id}/sync/", "post"),
            ("/api/v1/we-rss/feeds/{id}/refresh-content/", "post"),
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

    def test_article_export_operation_documents_csv_response_and_export_selectors(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/articles/export/"]["post"]

        request_schema = self._resolve_schema(
            schema,
            operation["requestBody"]["content"]["application/json"]["schema"],
        )

        self.assertIn("article_ids", request_schema["properties"])
        self.assertIn("member_id", request_schema["properties"])
        self.assertIn("feed_id", request_schema["properties"])
        self.assertIn("text/csv", operation["responses"]["200"]["content"])

    def test_article_batch_delete_operation_documents_request_and_response_shape(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"]["/api/v1/we-rss/articles/batch-delete/"]["post"]

        request_schema = self._resolve_schema(
            schema,
            operation["requestBody"]["content"]["application/json"]["schema"],
        )
        self.assertIn("article_ids", request_schema["properties"])

        response_schema = self._resolve_schema(
            schema,
            operation["responses"]["200"]["content"]["application/json"]["schema"],
        )
        data_schema = self._resolve_schema(schema, response_schema["properties"]["data"])
        self.assertIn("deleted_count", data_schema["properties"])
        self.assertIn("article_ids", data_schema["properties"])

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

    def test_seo_keyword_operations_are_documented(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        list_operation = schema["paths"]["/api/v1/we-rss/seo-keywords/"]["get"]
        detail_operation = schema["paths"]["/api/v1/we-rss/seo-keywords/{id}/"]["get"]

        self.assertEqual(list_operation["operationId"], "we_rss_seo_keywords_list")
        self.assertEqual(detail_operation["operationId"], "we_rss_seo_keywords_retrieve")

    def test_seo_keyword_request_and_response_examples_exist(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        create_operation = schema["paths"]["/api/v1/we-rss/seo-keywords/"]["post"]

        self.assertIn("examples", create_operation["requestBody"]["content"]["application/json"])
        self.assertIn("examples", create_operation["responses"]["201"]["content"]["application/json"])
