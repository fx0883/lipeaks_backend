from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from llm_gateway.services.direct_model import (
    DirectModelDeltaEvent,
    DirectModelResultEvent,
    DirectModelService,
)


class DirectModelServiceTests(SimpleTestCase):
    @patch("llm_gateway.services.direct_model.Agent")
    @patch("llm_gateway.services.direct_model.LLMGatewayModelFactory")
    def test_stream_structured_yields_final_result_for_structured_output(
        self,
        factory_cls,
        agent_cls,
    ):
        streamed_result = Mock()
        streamed_result.stream_text.return_value = iter(["{", '"title"', "}"])
        streamed_result.get_output.return_value = {"title": "done"}

        agent = Mock()
        agent.run_stream_sync.return_value = streamed_result
        agent_cls.return_value = agent
        factory_cls.build_model.return_value = "openai:gpt-5.4"

        events = list(
            DirectModelService.stream_structured(
                system_prompt="sys",
                user_prompt="user",
                output_schema=dict,
                requested_by_app="image_prompt",
            )
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].output, {"title": "done"})
        self.assertIsInstance(events[0], DirectModelResultEvent)
        streamed_result.stream_text.assert_not_called()
        agent.run_stream_sync.assert_called_once_with(
            "user",
            model_settings=None,
        )

    @patch("llm_gateway.services.direct_model.Agent")
    @patch("llm_gateway.services.direct_model.LLMGatewayModelFactory")
    def test_stream_structured_accepts_non_context_manager_stream_result(
        self,
        factory_cls,
        agent_cls,
    ):
        streamed_result = Mock()
        streamed_result.stream_text.return_value = iter(["a", "b"])
        streamed_result.get_output.return_value = {"title": "done"}

        agent = Mock()
        agent.run_stream_sync.return_value = streamed_result
        agent_cls.return_value = agent
        factory_cls.build_model.return_value = "openai:gpt-5.4"

        events = list(
            DirectModelService.stream_structured(
                system_prompt="sys",
                user_prompt="user",
                output_schema=dict,
                requested_by_app="image_prompt",
            )
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].output, {"title": "done"})
        streamed_result.stream_text.assert_not_called()
        agent.run_stream_sync.assert_called_once_with(
            "user",
            model_settings=None,
        )

    @patch("llm_gateway.services.direct_model.Agent")
    @patch("llm_gateway.services.direct_model.LLMGatewayModelFactory")
    def test_stream_structured_yields_deltas_for_text_output(
        self,
        factory_cls,
        agent_cls,
    ):
        streamed_result = Mock()
        streamed_result.stream_text.return_value = iter(["hello", " world"])
        streamed_result.get_output.return_value = "hello world"

        agent = Mock()
        agent.run_stream_sync.return_value = streamed_result
        agent_cls.return_value = agent
        factory_cls.build_model.return_value = "openai:gpt-5.4"

        events = list(
            DirectModelService.stream_structured(
                system_prompt="sys",
                user_prompt="user",
                output_schema=str,
                requested_by_app="image_prompt",
            )
        )

        self.assertEqual([event.text for event in events[:-1]], ["hello", " world"])
        self.assertEqual(events[-1].output, "hello world")
        self.assertIsInstance(events[0], DirectModelDeltaEvent)
        self.assertIsInstance(events[-1], DirectModelResultEvent)
