from unittest.mock import patch

from django.test import SimpleTestCase

from image_prompt.schemas import CharacterCandidate, ComicPlan, ComicPlanPanel
from llm_gateway.services.direct_model import DirectModelDeltaEvent, DirectModelResultEvent


class JokeToComicSerializerTests(SimpleTestCase):
    def test_rejects_blank_joke(self):
        from image_prompt.serializers import JokeToComicRequestSerializer

        serializer = JokeToComicRequestSerializer(data={"joke": "   "})

        self.assertFalse(serializer.is_valid())
        self.assertIn("joke", serializer.errors)


class JokeToComicServiceTests(SimpleTestCase):
    @staticmethod
    def _character(name):
        return CharacterCandidate(
            character_name=name,
            series_role="核心主角",
            core_identity=f"{name} 的核心身份",
            visual_profile=f"{name} 的外形特征",
            personality_profile=f"{name} 的性格特征",
            speech_style=f"{name} 的说话方式",
            relationship_to_others="",
            signature_elements=[],
            character_prompt=f"{name} 的角色提示词",
            confidence_reason="核心 recurring 角色",
        )

    @staticmethod
    def _plan():
        return ComicPlan(
            title="办公室笑话",
            story_summary="四格误会喜剧。",
            humor_explanation="误会在最后一格被揭开。",
            panels=[
                ComicPlanPanel(panel_number=1, role_in_joke="铺垫", visual="场景建立"),
                ComicPlanPanel(panel_number=2, role_in_joke="推进", visual="冲突升级"),
                ComicPlanPanel(panel_number=3, role_in_joke="误导", visual="误会加深"),
                ComicPlanPanel(panel_number=4, role_in_joke="包袱", visual="真相揭晓"),
            ],
        )

    @patch("image_prompt.services.joke_to_comic_service.DirectModelService.stream_structured")
    def test_builds_prompt_pack_from_structured_plan(self, stream_structured):
        from image_prompt.services.joke_to_comic_service import JokeToComicService

        stream_structured.return_value = iter(
            [
                DirectModelDeltaEvent(text='{"title":"办公室笑话"'),
                DirectModelResultEvent(output=self._plan()),
            ]
        )

        events = list(
            JokeToComicService.stream_prompt_pack(
                joke="一个程序员笑话",
                confirmed_characters=[],
            )
        )

        self.assertEqual(events[0]["event"], "progress")
        self.assertEqual(events[1]["event"], "delta")
        self.assertEqual(events[-1]["event"], "completed")
        self.assertEqual(events[-1]["result"].format.panel_count, 4)
        self.assertEqual(len(events[-1]["result"].panels), 4)

    def test_fallback_plan_keeps_four_panels(self):
        from image_prompt.services.joke_to_comic_service import JokeToComicService

        result = JokeToComicService.build_fallback_result(
            "一个程序员笑话",
            confirmed_characters=[],
        )

        self.assertEqual(len(result.panels), 4)
        self.assertEqual(result.format.panel_count, 4)

    def test_injects_confirmed_characters_into_prompts(self):
        from image_prompt.services.joke_to_comic_service import JokeToComicService

        result = JokeToComicService.build_result_from_plan(
            joke="一个产品经理和工程师的笑话",
            plan=self._plan(),
            confirmed_characters=[self._character("产品经理")],
            used_fallback=False,
        )

        self.assertIn("产品经理", result.panels[0].image_prompt)
        self.assertIn("产品经理", result.page_prompt)
