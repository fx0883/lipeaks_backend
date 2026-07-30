import json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "wechat-stats"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_LATEST_PATH = OUTPUT_DIR / "latest.json"
SESSION_PATH = OUTPUT_DIR / "session.json"
LIVE_LOG_PATH = OUTPUT_DIR / "proxy-live.log"
ARTICLE_SNAPSHOTS_DIR = OUTPUT_DIR / "article-requests"
ARTICLE_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def _as_int(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit() or ch == "-")
        if not digits or digits == "-":
            return None
        try:
            return int(digits)
        except ValueError:
            return None
    return None


def _merge(stats, key, value, source):
    parsed = _as_int(value)
    if parsed is None:
      return
    if stats[key] is None:
        stats[key] = parsed
        stats["sources"].append(f"{key}:{source}")


def append_live_log_line(log_path, line):
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")


def _parse_cookie_header(cookie_header):
    cookies = {}
    if not cookie_header:
        return cookies

    for chunk in cookie_header.split(";"):
        part = chunk.strip()
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        cookies[key.strip()] = value.strip()
    return cookies


def _first_query_value(query, key):
    return query.get(key, [""])[0]


def _extract_article_query(request_url, referer=""):
    parsed = urlparse(request_url or "")
    query = parse_qs(parsed.query)
    result = {key: _first_query_value(query, key) for key in ("__biz", "mid", "idx", "sn")}
    if all(result.values()):
        return result

    referer = (referer or "").replace("&amp;", "&")
    if referer.startswith("https://mp.weixin.qq.com/s?"):
        referer_query = parse_qs(urlparse(referer).query)
        for key in ("__biz", "mid", "idx", "sn"):
            if not result.get(key):
                result[key] = _first_query_value(referer_query, key)
    return result


def _article_snapshot_key(article_query):
    return "__".join(
        [
            article_query.get("__biz", "") or "unknown_biz",
            article_query.get("mid", "") or "unknown_mid",
            article_query.get("idx", "") or "unknown_idx",
        ]
    ).replace("/", "_").replace("\\", "_")


def _request_action_name(request_url):
    parsed = urlparse(request_url or "")
    query = parse_qs(parsed.query)
    action = _first_query_value(query, "action")
    if action:
        return action
    return Path(parsed.path).name or "request"


def write_article_request_snapshot(snapshot, article_query):
    if not article_query.get("__biz") or not article_query.get("mid") or not article_query.get("idx"):
        return

    article_dir = ARTICLE_SNAPSHOTS_DIR / _article_snapshot_key(article_query)
    article_dir.mkdir(parents=True, exist_ok=True)
    action_name = snapshot.get("action") or "request"
    snapshot_path = article_dir / f"{action_name}.json"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_session_from_flow_parts(request_url, headers):
    parsed = urlparse(request_url)
    query = parse_qs(parsed.query)
    if not query.get("key") or not query.get("uin"):
        referer = headers.get("referer", "").replace("&amp;", "&")
        if referer.startswith("https://mp.weixin.qq.com/s?"):
            referer_query = parse_qs(urlparse(referer).query)
            for key in ("key", "uin", "pass_ticket", "devicetype", "version"):
                if not query.get(key) and referer_query.get(key):
                    query[key] = referer_query[key]
    cookies = _parse_cookie_header(headers.get("cookie", ""))

    session = {
        "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "key": _first_query_value(query, "key"),
        "uin": _first_query_value(query, "uin"),
        "pass_ticket": cookies.get("pass_ticket") or _first_query_value(query, "pass_ticket"),
        "appmsg_token": cookies.get("appmsg_token") or _first_query_value(query, "appmsg_token"),
        "wap_sid2": cookies.get("wap_sid2", ""),
        "wxuin": cookies.get("wxuin", ""),
        "wxtokenkey": cookies.get("wxtokenkey") or _first_query_value(query, "wxtoken") or "777",
        "cookie_header": headers.get("cookie", ""),
        "devicetype": cookies.get("devicetype") or _first_query_value(query, "devicetype"),
        "version": cookies.get("version") or _first_query_value(query, "version"),
    }

    if not session["key"] or not session["uin"]:
        return None
    return session


def _merge_session(existing_session, new_session):
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


def write_session_file(session, session_path=SESSION_PATH):
    existing_session = {}
    if session_path.exists():
        existing_session = json.loads(session_path.read_text(encoding="utf-8"))
    merged_session = _merge_session(existing_session, session)
    session_path.write_text(json.dumps(merged_session, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_stats_from_payload(payload):
    stats = {
        "read_num": None,
        "like_num": None,
        "old_like_num": None,
        "share_num": None,
        "comment_count": None,
        "comment_reply_count": None,
        "sources": [],
    }

    def walk(node, source):
        if isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{source}[{index}]")
            return

        if not isinstance(node, dict):
            return

        mapping = {
            "read_num": ("read_num",),
            "like_num": ("like_num",),
            "old_like_num": ("old_like_num",),
            "share_num": ("share_num", "share_count", "forward_count"),
            "comment_count": ("comment_count", "elected_comment_total_cnt"),
        }

        for key, candidates in mapping.items():
            for candidate in candidates:
                if candidate in node:
                    _merge(stats, key, node[candidate], f"{source}.{candidate}")

        for key, value in node.items():
            if isinstance(value, (dict, list)):
                walk(value, f"{source}.{key}")

        if "elected_comment" in node and isinstance(node["elected_comment"], list):
            reply_total = 0
            reply_seen = False
            for comment in node["elected_comment"]:
                if not isinstance(comment, dict):
                    continue

                for reply_key in ("reply_new", "reply"):
                    reply_block = comment.get(reply_key)
                    if not isinstance(reply_block, dict):
                        continue

                    parsed_total = _as_int(reply_block.get("reply_total_cnt"))
                    if parsed_total is not None:
                        reply_total += parsed_total
                        reply_seen = True
                        break

                    reply_list = reply_block.get("reply_list")
                    if isinstance(reply_list, list):
                        reply_total += len(reply_list)
                        reply_seen = True
                        break

            if reply_seen and stats["comment_reply_count"] is None:
                stats["comment_reply_count"] = reply_total
                stats["sources"].append(f"comment_reply_count:{source}.elected_comment")

    walk(payload, "payload")
    return stats


class WeChatStatsAddon:
    def __init__(self):
        self.last_stats = None

    def request(self, flow):
        if "mp.weixin.qq.com" not in flow.request.pretty_host:
            return

        append_live_log_line(LIVE_LOG_PATH, f"{flow.request.method} {flow.request.pretty_url}")

        referer = flow.request.headers.get("referer")
        if referer:
            append_live_log_line(LIVE_LOG_PATH, f"referer: {referer}")

        cookie = flow.request.headers.get("cookie")
        if cookie:
            append_live_log_line(LIVE_LOG_PATH, f"cookie_header: {cookie}")
            for key, value in _parse_cookie_header(cookie).items():
                if key in {
                    "appmsg_token",
                    "wap_sid2",
                    "wxuin",
                    "wxtokenkey",
                    "devicetype",
                    "version",
                    "pass_ticket",
                }:
                    append_live_log_line(LIVE_LOG_PATH, f"cookie: {key}={value}")

        session = extract_session_from_flow_parts(flow.request.pretty_url, flow.request.headers)
        if session:
            write_session_file(session)

    def response(self, flow):
        if "mp.weixin.qq.com" not in flow.request.pretty_host:
            return

        interesting_paths = (
            "/mp/getappmsgext",
            "/mp/appmsg_comment",
            "/mp/appmsg_like",
        )
        if not any(path in flow.request.path for path in interesting_paths):
            return

        content_type = flow.response.headers.get("content-type", "")
        if "json" not in content_type.lower():
            return

        try:
            payload = json.loads(flow.response.get_text(strict=False))
        except Exception:
            return

        referer = flow.request.headers.get("referer", "")
        article_query = _extract_article_query(flow.request.pretty_url, referer)
        response_snapshot = {
            "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "method": flow.request.method,
            "request_url": flow.request.pretty_url,
            "referer": referer,
            "cookie_header": flow.request.headers.get("cookie", ""),
            "action": _request_action_name(flow.request.pretty_url),
            "article_query": article_query,
            "response_payload": payload,
        }
        write_article_request_snapshot(response_snapshot, article_query)

        stats = extract_stats_from_payload(payload)
        if all(
            stats[key] is None
            for key in (
                "read_num",
                "like_num",
                "old_like_num",
                "share_num",
                "comment_count",
                "comment_reply_count",
            )
        ):
            return

        article_url = flow.request.query.get("source", "") or flow.request.pretty_url
        result = {
            "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "request_url": flow.request.pretty_url,
            "article_hint": article_url,
            "debug_file_role": "live proxy snapshot",
            **stats,
        }
        self.last_stats = result

        DEBUG_LATEST_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        print("\n[wechat-stats] Captured stats")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"[wechat-stats] Saved debug snapshot to {DEBUG_LATEST_PATH}")


addons = [WeChatStatsAddon()]
