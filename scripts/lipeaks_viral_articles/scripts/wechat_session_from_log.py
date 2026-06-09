from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict
from urllib.parse import parse_qs, urlparse


DEFAULT_SESSION_FILE = Path(__file__).resolve().parent.parent / "output" / "wechat-stats" / "session.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract reusable WeChat session parameters from a proxy log."
    )
    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to the proxy log produced while opening an article in WeChat.",
    )
    parser.add_argument(
        "--output-file",
        default=str(DEFAULT_SESSION_FILE),
        help="Where to write the extracted session JSON.",
    )
    return parser.parse_args()


def read_lines(log_file: Path) -> list[str]:
    for encoding in ("utf-16", "utf-8"):
        try:
            return log_file.read_text(encoding=encoding).splitlines()
        except UnicodeDecodeError:
            continue
    return log_file.read_text(encoding="utf-8", errors="ignore").splitlines()


def find_latest_cookie_value(lines: list[str], cookie_name: str) -> str | None:
    prefix = f"cookie: {cookie_name}="
    value = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            value = stripped.split("=", 1)[1]
    return value


def find_latest_cookie_header(lines: list[str]) -> str | None:
    prefix = "cookie_header: "
    value = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            value = stripped.split(prefix, 1)[1]
    return value


def parse_cookie_header(cookie_header: str) -> Dict[str, str]:
    cookies = {}
    if not cookie_header:
        return cookies
    for chunk in cookie_header.split(";"):
        part = chunk.strip()
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            cookies[key] = value
    return cookies


def find_latest_query_value(lines: list[str], query_name: str) -> str | None:
    value = None
    marker = f"{query_name}="
    for line in lines:
        stripped = line.strip().replace("&amp;", "&")
        if "https://mp.weixin.qq.com/" not in stripped or marker not in stripped:
            continue

        url = None
        if stripped.startswith(("POST https://", "GET https://")):
            parts = stripped.split(" ", 1)
            if len(parts) == 2:
                url = parts[1]
        elif stripped.startswith("referer: https://"):
            url = stripped.split("referer: ", 1)[1]

        if not url:
            continue

        query = parse_qs(urlparse(url).query)
        candidate = query.get(query_name, [""])[0]
        if candidate:
            value = candidate
    return value


def find_latest_referer_query(lines: list[str]) -> Dict[str, str]:
    referer_url = None
    for line in lines:
        stripped = line.strip().replace("&amp;", "&")
        if stripped.startswith("referer: https://mp.weixin.qq.com/s?__biz="):
            referer_url = stripped.split("referer: ", 1)[1]

    if not referer_url:
        raise RuntimeError("Could not find article referer in proxy log.")

    parsed = urlparse(referer_url)
    query = parse_qs(parsed.query)
    result = {}
    for key in ("key", "uin", "pass_ticket", "devicetype", "version"):
        value = query.get(key, [""])[0]
        if value:
            result[key] = value
    return result


def extract_session_from_lines(lines: list[str]) -> Dict[str, str]:
    query = find_latest_referer_query(lines)
    cookie_header = find_latest_cookie_header(lines) or ""
    header_cookie_map = parse_cookie_header(cookie_header)
    cookie_map = {
        "appmsg_token": find_latest_cookie_value(lines, "appmsg_token") or header_cookie_map.get("appmsg_token"),
        "wap_sid2": find_latest_cookie_value(lines, "wap_sid2") or header_cookie_map.get("wap_sid2"),
        "wxuin": find_latest_cookie_value(lines, "wxuin") or header_cookie_map.get("wxuin"),
        "wxtokenkey": find_latest_cookie_value(lines, "wxtokenkey") or header_cookie_map.get("wxtokenkey"),
        "devicetype": find_latest_cookie_value(lines, "devicetype") or header_cookie_map.get("devicetype"),
        "version": find_latest_cookie_value(lines, "version") or header_cookie_map.get("version"),
        "pass_ticket": find_latest_cookie_value(lines, "pass_ticket") or header_cookie_map.get("pass_ticket"),
    }
    query_map = {
        "appmsg_token": find_latest_query_value(lines, "appmsg_token"),
        "wxtoken": find_latest_query_value(lines, "wxtoken"),
    }

    session = {
        "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "key": query.get("key", ""),
        "uin": query.get("uin", ""),
        "pass_ticket": cookie_map["pass_ticket"] or query.get("pass_ticket", ""),
        "appmsg_token": cookie_map["appmsg_token"] or query_map["appmsg_token"] or "",
        "wap_sid2": cookie_map["wap_sid2"] or "",
        "wxuin": cookie_map["wxuin"] or "",
        "wxtokenkey": cookie_map["wxtokenkey"] or query_map["wxtoken"] or "777",
        "cookie_header": cookie_header,
        "devicetype": cookie_map["devicetype"] or query.get("devicetype", ""),
        "version": cookie_map["version"] or query.get("version", ""),
    }
    return session


def merge_session(existing_session: Dict[str, str], new_session: Dict[str, str]) -> Dict[str, str]:
    merged = dict(existing_session or {})
    for key, value in (new_session or {}).items():
        if key == "captured_at":
            merged[key] = value
            continue
        if value:
            merged[key] = value
            continue
        merged.setdefault(key, value)
    return merged


def write_session_file(session: Dict[str, str], output_file: Path = DEFAULT_SESSION_FILE) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    existing_session = {}
    if output_file.exists():
        existing_session = json.loads(output_file.read_text(encoding="utf-8"))
    merged_session = merge_session(existing_session, session)
    output_file.write_text(
        json.dumps(merged_session, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    lines = read_lines(Path(args.log_file))
    session = extract_session_from_lines(lines)
    write_session_file(session, Path(args.output_file))
    print(json.dumps(session, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
