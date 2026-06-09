from pathlib import Path

import yaml
from django.conf import settings

from llm_gateway.domain.entities import CatalogSkill


class SkillCatalogService:
    @staticmethod
    def list_global_skills():
        discovered = []
        seen_names = set()

        for skill_root in getattr(settings, "LLM_GATEWAY_SKILL_DIRS", []):
            root_path = Path(skill_root)
            if not root_path.exists() or not root_path.is_dir():
                continue

            for skill_dir in sorted(path for path in root_path.iterdir() if path.is_dir()):
                skill = SkillCatalogService._parse_skill_directory(skill_dir)
                if skill is None or skill.name in seen_names:
                    continue
                seen_names.add(skill.name)
                discovered.append(skill)

        return discovered

    @staticmethod
    def get_skill(name):
        for skill in SkillCatalogService.list_global_skills():
            if skill.name == name:
                return skill
        return None

    @staticmethod
    def _parse_skill_directory(skill_dir):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return None

        content = skill_file.read_text(encoding="utf-8")
        frontmatter = SkillCatalogService._parse_frontmatter(content)
        skill_name = frontmatter.get("name") or skill_dir.name
        description = frontmatter.get("description", "")

        return CatalogSkill(
            name=skill_name,
            description=description,
            source_dir=skill_dir.parent,
            skill_path=skill_dir,
        )

    @staticmethod
    def _parse_frontmatter(content):
        if not content.startswith("---"):
            return {}

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}

        parsed = yaml.safe_load(parts[1]) or {}
        return parsed if isinstance(parsed, dict) else {}
