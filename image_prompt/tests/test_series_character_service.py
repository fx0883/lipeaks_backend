from django.test import SimpleTestCase

from image_prompt.serializers import AnalyzeSeriesCharactersRequestSerializer
from image_prompt.schemas import AnalyzeSeriesCharactersResult, CharacterCandidate
from llm_gateway.services.direct_model import DirectModelDeltaEvent, DirectModelResultEvent


class AnalyzeSeriesCharactersSerializerTests(SimpleTestCase):
    def test_rejects_blank_source_text(self):
        serializer = AnalyzeSeriesCharactersRequestSerializer(
            data={"source_text": "   "},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("source_text", serializer.errors)


class SeriesCharacterServiceTests(SimpleTestCase):
    @staticmethod
    def _candidate(name, *, role="核心主角", reason="核心 recurring 角色"):
        return CharacterCandidate(
            character_name=name,
            series_role=role,
            core_identity=f"{name} 的核心身份",
            visual_profile=f"{name} 的外形特征",
            personality_profile=f"{name} 的性格特征",
            speech_style=f"{name} 的说话方式",
            relationship_to_others="",
            signature_elements=[],
            character_prompt=f"{name} 的角色提示词",
            confidence_reason=reason,
        )

    def test_moves_tooling_roles_to_temporary_bucket(self):
        from image_prompt.services.series_character_service import SeriesCharacterService

        result = AnalyzeSeriesCharactersResult(
            recommended_main_characters=[
                self._candidate("阿明"),
                self._candidate("前台小妹", role="临时角色", reason="一次性工具角色"),
                self._candidate("小美"),
            ],
            temporary_characters=[],
            analysis_notes=["initial"],
        )

        with self.subTest("post process"):
            final_result = SeriesCharacterService.finalize_result(
                result,
                source_text="故事文本",
                series_name="连载名",
            )

        self.assertEqual(
            [item.character_name for item in final_result.recommended_main_characters],
            ["阿明", "小美"],
        )
        self.assertEqual(
            [item.character_name for item in final_result.temporary_characters],
            ["前台小妹"],
        )

    def test_deduplicates_candidates_by_character_name(self):
        from image_prompt.services.series_character_service import SeriesCharacterService

        result = AnalyzeSeriesCharactersResult(
            recommended_main_characters=[
                self._candidate("阿明"),
                self._candidate("阿明"),
                self._candidate("小美"),
            ],
            temporary_characters=[],
            analysis_notes=["initial"],
        )

        final_result = SeriesCharacterService.finalize_result(
            result,
            source_text="故事文本",
            series_name="",
        )

        self.assertEqual(
            [item.character_name for item in final_result.recommended_main_characters],
            ["阿明", "小美"],
        )

    def test_rejects_when_fewer_than_two_core_characters_remain(self):
        from image_prompt.services.series_character_service import (
            SeriesCharacterAnalysisError,
            SeriesCharacterService,
        )

        result = AnalyzeSeriesCharactersResult(
            recommended_main_characters=[
                self._candidate("阿明"),
                self._candidate("路人甲", role="临时角色", reason="一次性角色"),
            ],
            temporary_characters=[],
            analysis_notes=["initial"],
        )

        with self.assertRaises(SeriesCharacterAnalysisError):
            SeriesCharacterService.finalize_result(
                result,
                source_text="故事文本",
                series_name="",
            )

    def test_stream_analysis_relays_delta_and_completed_events(self):
        from image_prompt.services.series_character_service import SeriesCharacterService

        direct_events = iter(
            [
                DirectModelDeltaEvent(text='{"partial":'),
                DirectModelResultEvent(
                    output=AnalyzeSeriesCharactersResult(
                        recommended_main_characters=[
                            self._candidate("阿明"),
                            self._candidate("小美"),
                        ],
                        temporary_characters=[],
                        analysis_notes=["initial"],
                    )
                ),
            ]
        )

        from unittest.mock import patch

        with patch(
            "image_prompt.services.series_character_service.DirectModelService.stream_structured",
            return_value=direct_events,
        ):
            events = list(
                SeriesCharacterService.stream_analysis(
                    source_text="故事文本",
                    series_name="连载名",
                )
            )

        self.assertEqual(events[0]["event"], "progress")
        self.assertEqual(events[1]["event"], "delta")
        self.assertEqual(events[-1]["event"], "completed")
