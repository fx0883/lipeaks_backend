from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CatalogSkill:
    name: str
    description: str
    source_dir: Path
    skill_path: Path
    is_global_shared: bool = True

