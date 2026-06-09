from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(PROJECT_DIR / ".env")
_load_env_file(BACKEND_DIR / ".env")


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


@dataclass(frozen=True)
class Settings:
    llm_model: str = _env("LLM_GATEWAY_AGENT_MODEL", "openai:gpt-5.4")
    llm_base_url: str = _env("LLM_GATEWAY_AGENT_BASE_URL")
    llm_api_key: str = _env("LLM_GATEWAY_AGENT_API_KEY")
    comfyui_base_url: str = _env("COMFYUI_BASE_URL", "http://127.0.0.1:8188")
    api_host: str = _env("API_HOST", "127.0.0.1")
    api_port: int = int(_env("API_PORT", "8000"))
    allowed_origins: str = _env("ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")

    @property
    def backend_dir(self) -> Path:
        return BACKEND_DIR

    @property
    def project_dir(self) -> Path:
        return PROJECT_DIR

    @property
    def workspace_dir(self) -> Path:
        return self.project_dir.parent

    @property
    def output_dir(self) -> Path:
        return self.backend_dir / "outputs"

    @property
    def workflow_path(self) -> Path:
        override = _env("COMFYUI_WORKFLOW_PATH")
        if override:
            return Path(override)
        return self.workspace_dir / "skills" / "qwen-image-2512-comfyui" / "image_qwen_Image_2512.json"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
