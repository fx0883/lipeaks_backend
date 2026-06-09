from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings

from llm_gateway.services.catalog import SkillCatalogService


class SkillCatalogServiceTests(SimpleTestCase):
    def test_discovers_skill_from_configured_directories(self):
        with TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "wechat-article-search"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: wechat-article-search\ndescription: Search wechat articles\n---\n",
                encoding="utf-8",
            )

            with override_settings(LLM_GATEWAY_SKILL_DIRS=[temp_dir]):
                skills = SkillCatalogService.list_global_skills()

        self.assertEqual(skills[0].name, "wechat-article-search")
