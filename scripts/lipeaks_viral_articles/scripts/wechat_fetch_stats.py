from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlparse

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.wechat_replay_getappmsgext import (
    DEFAULT_LIVE_LOG_FILE,
    DEFAULT_SESSION_FILE,
    collect_stats,
    write_result_json,
)


OUTPUT_DIR = REPO_ROOT / "output" / "wechat-stats"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch WeChat article stats directly from an article URL."
    )
    parser.add_argument("article_url", help="WeChat article URL, usually https://mp.weixin.qq.com/s/...")
    parser.add_argument(
        "--output-file",
        help="Optional explicit output path. Defaults to output/wechat-stats/<short-id>.json.",
    )
    parser.add_argument(
        "--session-file",
        default=str(DEFAULT_SESSION_FILE),
        help="Path to session.json captured from the live proxy.",
    )
    parser.add_argument(
        "--live-log-file",
        default=str(DEFAULT_LIVE_LOG_FILE),
        help="Path to proxy-live.log captured by the live proxy.",
    )
    return parser.parse_args()


def build_article_output_path(article_url: str, output_dir: Path = OUTPUT_DIR) -> Path:
    parsed = urlparse(article_url)
    short_id = parsed.path.rstrip("/").split("/")[-1]
    if not short_id or short_id == "s":
        raise ValueError(f"Could not derive article short id from URL: {article_url}")
    return output_dir / f"{short_id}.json"


def fetch_and_write(
    article_url: str,
    output_file: Path | None = None,
    *,
    output_dir: Path = OUTPUT_DIR,
    session_file: Path = DEFAULT_SESSION_FILE,
    live_log_file: Path = DEFAULT_LIVE_LOG_FILE,
) -> dict:
    target_output = output_file or build_article_output_path(article_url, output_dir)
    result = collect_stats(
        article_url=article_url,
        session_file=session_file,
        live_log_file=live_log_file,
    )
    write_result_json(result, target_output)
    return result


def main() -> None:
    args = parse_args()
    output_file = Path(args.output_file) if args.output_file else None
    result = fetch_and_write(
        args.article_url,
        output_file,
        output_dir=OUTPUT_DIR,
        session_file=Path(args.session_file),
        live_log_file=Path(args.live_log_file),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
