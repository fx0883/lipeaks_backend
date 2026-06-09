from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from backend.config import settings


POSITIVE_NODE_ID = "197:180"
NEGATIVE_NODE_ID = "197:195"
LATENT_NODE_ID = "197:179"

DEFAULT_NEGATIVE_PROMPT = (
    "low resolution, blurry, noisy, jpeg artifacts, deformed anatomy, extra fingers, "
    "fused fingers, distorted face, waxy skin, oversaturated, text, watermark, logo, ai artifacts"
)

PRESET_SIZES = {
    "square": (1024, 1024),
    "portrait": (1080, 1440),
    "landscape": (900, 383),
}


def parse_size(size_text: str) -> tuple[int, int]:
    return PRESET_SIZES.get(size_text.lower().strip(), PRESET_SIZES["square"])


def load_workflow_template(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def apply_workflow_inputs(
    workflow: dict[str, Any], optimized_prompt: str, width: int, height: int
) -> dict[str, Any]:
    workflow[POSITIVE_NODE_ID]["inputs"]["text"] = optimized_prompt
    workflow[NEGATIVE_NODE_ID]["inputs"]["text"] = DEFAULT_NEGATIVE_PROMPT
    workflow[LATENT_NODE_ID]["inputs"]["width"] = width
    workflow[LATENT_NODE_ID]["inputs"]["height"] = height
    return workflow


def _http_json_request(
    url: str, method: str = "GET", payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def _submit_prompt(base_url: str, workflow: dict[str, Any]) -> str:
    payload = {"prompt": workflow, "client_id": str(uuid.uuid4())}
    result = _http_json_request(f"{base_url}/prompt", method="POST", payload=payload)
    prompt_id = result.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI did not return prompt_id. Response: {result}")
    return str(prompt_id)


def _extract_images(history_item: dict[str, Any]) -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []
    outputs = history_item.get("outputs", {})
    if not isinstance(outputs, dict):
        return images
    for output in outputs.values():
        if not isinstance(output, dict):
            continue
        for image in output.get("images", []):
            if isinstance(image, dict) and image.get("filename"):
                images.append(image)
    return images


def _wait_for_images(base_url: str, prompt_id: str, timeout_seconds: int = 300) -> list[dict[str, Any]]:
    start = time.time()
    history_url = f"{base_url}/history/{urllib.parse.quote(prompt_id)}"
    while time.time() - start <= timeout_seconds:
        history = _http_json_request(history_url)
        history_item = history.get(prompt_id)
        if isinstance(history_item, dict):
            images = _extract_images(history_item)
            if images:
                return images
        time.sleep(1)
    raise TimeoutError(f"Timed out waiting for prompt_id={prompt_id}")


def _download_image(base_url: str, image_meta: dict[str, Any], output_dir: Path) -> Path:
    query = urllib.parse.urlencode(
        {
            "filename": image_meta.get("filename", ""),
            "subfolder": image_meta.get("subfolder", ""),
            "type": image_meta.get("type", "output"),
        }
    )
    image_url = f"{base_url}/view?{query}"
    destination = output_dir / Path(str(image_meta["filename"])).name
    with urllib.request.urlopen(image_url, timeout=30) as response:
        destination.write_bytes(response.read())
    return destination


def image_url_for(path: Path) -> str:
    return f"/outputs/{path.name}"


def generate_comic_image(prompt: str, size: str = "square") -> Path:
    workflow = load_workflow_template(settings.workflow_path)
    width, height = parse_size(size)
    workflow = apply_workflow_inputs(workflow, prompt, width, height)
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    prompt_id = _submit_prompt(settings.comfyui_base_url, workflow)
    images = _wait_for_images(settings.comfyui_base_url, prompt_id)
    if not images:
        raise RuntimeError("ComfyUI completed but returned no images.")
    return _download_image(settings.comfyui_base_url, images[0], settings.output_dir)

