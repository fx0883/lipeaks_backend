from __future__ import annotations

import argparse
import json
import re
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning


DEFAULT_DEBUG_OUTPUT_FILE = Path(__file__).resolve().parent.parent / "output" / "wechat-stats" / "latest.json"
DEFAULT_ARTICLE_URL = "https://mp.weixin.qq.com/s/-ayS5eVVksg9ZGa7vyU8hQ"
DEFAULT_SESSION_FILE = Path(__file__).resolve().parent.parent / "output" / "wechat-stats" / "session.json"
DEFAULT_LIVE_LOG_FILE = Path(__file__).resolve().parent.parent / "output" / "wechat-stats" / "proxy-live.log"

warnings.simplefilter("ignore", InsecureRequestWarning)

WECHAT_TIMEZONE = timezone(timedelta(hours=8))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch WeChat article stats using a captured session and optional proxy log."
    )
    parser.add_argument(
        "--log-file",
        help="Optional proxy log produced while opening the article in WeChat.",
    )
    parser.add_argument(
        "--mid",
        default="2247532288",
        help="Target article mid. Defaults to the current sample article.",
    )
    parser.add_argument(
        "--idx",
        default="1",
        help="Target article idx. Defaults to 1.",
    )
    parser.add_argument(
        "--sn",
        default="4d6252412cc5aa0d7b8ea98730957ee1",
        help="Target article sn. Defaults to the current sample article.",
    )
    parser.add_argument(
        "--article-url",
        default=DEFAULT_ARTICLE_URL,
        help="Short WeChat article URL used to fetch the page HTML for comment metadata.",
    )
    parser.add_argument(
        "--session-file",
        default=str(DEFAULT_SESSION_FILE),
        help="Optional session.json file. When present, its live cookies/tokens override stale log values.",
    )
    parser.add_argument(
        "--live-log-file",
        default=str(DEFAULT_LIVE_LOG_FILE),
        help="Optional live proxy log. When present, its newest key/pass_ticket/uin override older values.",
    )
    parser.add_argument(
        "--output-file",
        default=str(DEFAULT_DEBUG_OUTPUT_FILE),
        help=(
            "Where to write the resulting JSON payload. When you run this low-level "
            "script directly, it defaults to output/wechat-stats/latest.json."
        ),
    )
    return parser.parse_args()


def read_lines(log_file: Path) -> list[str]:
    for encoding in ("utf-16", "utf-8"):
        try:
            return log_file.read_text(encoding=encoding).splitlines()
        except UnicodeDecodeError:
            continue
    return log_file.read_text(encoding="utf-8", errors="ignore").splitlines()


def parse_live_request_entries(lines: list[str]) -> list[Dict[str, str]]:
    entries: list[Dict[str, str]] = []
    current: Optional[Dict[str, str]] = None
    request_line = re.compile(r"^(GET|POST)\s+(https://\S+)$")

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        match = request_line.match(line)
        if match:
            if current:
                entries.append(current)
            current = {
                "method": match.group(1),
                "url": match.group(2).replace("&amp;", "&"),
            }
            continue

        if current is None:
            continue

        if line.startswith("referer: "):
            current["referer"] = line.split("referer: ", 1)[1].replace("&amp;", "&")
        elif line.startswith("cookie_header: "):
            current["cookie_header"] = line.split("cookie_header: ", 1)[1]

    if current:
        entries.append(current)

    return entries


def _query_matches_article(candidate_url: str, article_query: Dict[str, str]) -> bool:
    parsed = urlparse(candidate_url or "")
    query = parse_qs(parsed.query)
    for key in ("__biz", "mid", "idx"):
        expected = article_query.get(key) or ""
        if not expected:
            continue
        if query.get(key, [""])[0] != expected:
            return False

    expected_sn = article_query.get("sn") or ""
    if expected_sn:
        candidate_sn = query.get("sn", [""])[0]
        if candidate_sn and candidate_sn != expected_sn:
            return False

    return True


def find_captured_request_entry(
    lines: list[str],
    *,
    path_fragment: str,
    article_query: Dict[str, str],
    action: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    matched: Optional[Dict[str, str]] = None

    for entry in parse_live_request_entries(lines):
        parsed = urlparse(entry["url"])
        if path_fragment not in parsed.path:
            continue

        entry_query = parse_qs(parsed.query)
        if action and entry_query.get("action", [""])[0] != action:
            continue

        if _query_matches_article(entry["url"], article_query):
            matched = entry
            continue

        referer = entry.get("referer", "")
        if referer and _query_matches_article(referer, article_query):
            matched = entry

    return matched


def find_referer_query(lines: list[str], *, mid: str, idx: str, sn: str) -> Dict[str, str]:
    for line in lines:
        stripped = line.strip().replace("&amp;", "&")
        if "referer:" not in stripped or "https://mp.weixin.qq.com/s?" not in stripped:
            continue
        if f"mid={mid}" not in stripped or f"idx={idx}" not in stripped or f"sn={sn}" not in stripped:
            continue
        url = stripped.split("referer: ", 1)[1]
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        result = {}
        for key in ("__biz", "mid", "idx", "sn", "key", "uin", "pass_ticket", "wxtoken", "devicetype", "version"):
            value = query.get(key, [""])[0]
            if value:
                result[key] = value
        return result
    raise RuntimeError("Could not find article referer in proxy log.")


def find_latest_cookie_value(lines: list[str], cookie_name: str) -> Optional[str]:
    prefix = f"cookie: {cookie_name}="
    value = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            value = stripped.split("=", 1)[1]
    return value


def build_cookies(lines: list[str]) -> Dict[str, str]:
    cookie_names = [
        "wxtokenkey",
        "wxuin",
        "devicetype",
        "version",
        "lang",
        "appmsg_token",
        "pass_ticket",
        "wap_sid2",
    ]
    cookies = {}
    for name in cookie_names:
        value = find_latest_cookie_value(lines, name)
        if value:
            cookies[name] = value
    return cookies


def parse_cookie_header(cookie_header: str) -> Dict[str, str]:
    cookies = {}
    if not cookie_header:
        return cookies
    # New proxy logs persist cookie_header as ", " joined pairs while some older
    # captures still use the canonical ";" cookie separator. Support both formats.
    for chunk in re.split(r";\s*|,\s*", cookie_header):
        part = chunk.strip()
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            cookies[key] = value
    return cookies


def load_session_file(session_file: Path) -> Dict[str, str]:
    if not session_file.exists():
        return {}
    return json.loads(session_file.read_text(encoding="utf-8"))


def extract_live_overrides(live_log_text: str) -> Dict[str, str]:
    params = {}
    referers = re.findall(r"referer: (https://mp\.weixin\.qq\.com/s\?[^\n]+)", live_log_text)
    if referers:
        parsed = urlparse(referers[-1].replace("&amp;", "&"))
        query = parse_qs(parsed.query)
        for key in ("key", "uin", "pass_ticket"):
            value = query.get(key, [""])[0]
            if value:
                params[key] = value

    if "key" not in params:
        values = re.findall(r"[?&]key=([^&\s]+)", live_log_text)
        if values:
            params["key"] = values[-1]
    if "uin" not in params:
        values = re.findall(r"[?&]uin=([^&\s]+)", live_log_text)
        if values:
            params["uin"] = values[-1]
    if "pass_ticket" not in params:
        values = re.findall(r"[?&]pass_ticket=([^&\s]+)", live_log_text)
        if values:
            params["pass_ticket"] = values[-1]
    values = re.findall(r"[?&]appmsg_token=([^&\s]+)", live_log_text)
    non_empty_values = [value for value in values if value]
    if non_empty_values:
        params["appmsg_token"] = non_empty_values[-1]

    values = re.findall(r"[?&]wxtoken=([^&\s]+)", live_log_text)
    non_empty_values = [value for value in values if value]
    if non_empty_values:
        params["wxtokenkey"] = non_empty_values[-1]

    values = re.findall(r"[?&]devicetype=([^&\s]+)", live_log_text)
    non_empty_values = [value for value in values if value]
    if non_empty_values:
        params["devicetype"] = non_empty_values[-1]

    values = re.findall(r"[?&]version=([^&\s]+)", live_log_text)
    non_empty_values = [value for value in values if value]
    if non_empty_values:
        params["version"] = non_empty_values[-1]

    return params


def load_live_overrides(live_log_file: Path) -> Dict[str, str]:
    if not live_log_file.exists():
        return {}
    return extract_live_overrides(live_log_file.read_text(encoding="utf-8"))


def apply_session_overrides(
    query: Dict[str, str],
    cookies: Dict[str, str],
    session: Dict[str, str],
) -> tuple[Dict[str, str], Dict[str, str]]:
    if not session:
        return query, cookies

    merged_query = dict(query)
    merged_cookies = dict(cookies)

    for key in ("key", "uin", "pass_ticket", "devicetype", "version"):
        value = session.get(key)
        if value:
            merged_query[key] = value

    for key in (
        "appmsg_token",
        "wap_sid2",
        "wxuin",
        "wxtokenkey",
        "devicetype",
        "version",
        "pass_ticket",
    ):
        value = session.get(key)
        if value:
            merged_cookies[key] = value

    return merged_query, merged_cookies


def apply_live_overrides(
    query: Dict[str, str],
    cookies: Dict[str, str],
    live_overrides: Dict[str, str],
) -> tuple[Dict[str, str], Dict[str, str]]:
    if not live_overrides:
        return query, cookies

    merged_query = dict(query)
    merged_cookies = dict(cookies)

    for key in ("key", "uin", "pass_ticket"):
        value = live_overrides.get(key)
        if value:
            merged_query[key] = value
            if key == "pass_ticket":
                merged_cookies["pass_ticket"] = value

    for cookie_key, override_key in (
        ("appmsg_token", "appmsg_token"),
        ("wxtokenkey", "wxtokenkey"),
        ("devicetype", "devicetype"),
        ("version", "version"),
    ):
        value = live_overrides.get(override_key)
        if value:
            merged_cookies[cookie_key] = value
            if cookie_key in ("devicetype", "version"):
                merged_query[cookie_key] = value

    return merged_query, merged_cookies


def create_http_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.verify = False
    return session


def build_article_url(query: Dict[str, str], cookies: Dict[str, str]) -> str:
    pass_ticket = cookies.get("pass_ticket") or query.get("pass_ticket", "")
    params = {
        "__biz": query["__biz"],
        "mid": query["mid"],
        "idx": query["idx"],
        "sn": query["sn"],
        "key": query["key"],
        "uin": query["uin"],
        "pass_ticket": pass_ticket,
        "devicetype": cookies.get("devicetype") or query.get("devicetype", "UnifiedPCWindows"),
        "version": cookies.get("version") or query.get("version", ""),
    }
    parts = [f"{key}={value}" for key, value in params.items() if value != ""]
    return "https://mp.weixin.qq.com/s?" + "&".join(parts)


def fetch_article_html(article_url: str, cookies: Dict[str, str]) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 NetType/WIFI "
            "MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090a13) "
            "UnifiedPCWindowsWechat(0xf2541721) XWEB/19027"
        ),
    }
    response = create_http_session().get(
        article_url,
        headers=headers,
        cookies=cookies,
        timeout=30,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.text


def replay_captured_request(
    entry: Dict[str, str],
    *,
    default_referer: Optional[str] = None,
    extra_cookies: Optional[Dict[str, str]] = None,
) -> Dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 NetType/WIFI "
            "MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090a13) "
            "UnifiedPCWindowsWechat(0xf2541721) XWEB/19027"
        ),
        "Origin": "https://mp.weixin.qq.com",
        "X-Requested-With": "XMLHttpRequest",
    }
    if entry.get("referer") or default_referer:
        headers["Referer"] = entry.get("referer") or default_referer or ""

    cookies = parse_cookie_header(entry.get("cookie_header", ""))
    if extra_cookies:
        for key, value in extra_cookies.items():
            if value:
                cookies[key] = value

    session = create_http_session()
    method = entry.get("method", "GET").upper()
    url = entry["url"]

    if method == "POST":
        data = None
        if "/mp/getappmsgext" in url:
            data = {
                "is_only_read": "1",
                "is_temp_url": "0",
                "appmsg_type": "9",
                "reward_uin_count": "0",
            }
        response = session.post(url, headers=headers, cookies=cookies, data=data, timeout=60)
    else:
        response = session.get(url, headers=headers, cookies=cookies, timeout=30)

    response.raise_for_status()
    return response.json()


def _match_first(patterns: list[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def _as_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit() or ch == "-")
    if not digits or digits == "-":
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _normalize_publish_time_text(raw_value: str) -> Optional[datetime]:
    raw_text = str(raw_value or "").strip()
    if not raw_text:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            parsed = datetime.strptime(raw_text, fmt)
            return parsed.replace(tzinfo=WECHAT_TIMEZONE)
        except ValueError:
            continue
    return None


def extract_article_publish_time(html: str) -> Optional[datetime]:
    for pattern in (
        r"var\s+createTime\s*=\s*'([^']+)'",
        r'var\s+createTime\s*=\s*"([^"]+)"',
        r"create_time:\s*JsDecode\('([^']+)'\)",
    ):
        match = re.search(pattern, html)
        if not match:
            continue
        publish_time = _normalize_publish_time_text(match.group(1))
        if publish_time is not None:
            return publish_time.astimezone(timezone.utc)

    for pattern in (
        r"var\s+oriCreateTime\s*=\s*'(\d+)'",
        r'var\s+create_time\s*=\s*"(\d+)"\s*\*\s*1',
        r'var\s+ct\s*=\s*"(\d+)"',
        r"ori_create_time:\s*'(\d+)'\s*\*\s*1",
        r"create_timestamp:\s*'(\d+)'\s*\*\s*1",
    ):
        match = re.search(pattern, html)
        if not match:
            continue
        try:
            return datetime.fromtimestamp(int(match.group(1)), tz=timezone.utc)
        except ValueError:
            continue

    return None


def extract_article_comment_metadata(html: str) -> Dict[str, Optional[str] | Optional[int]]:
    metadata = {
        "__biz": _match_first([r'var biz = "([^"]+)"'], html),
        "appmsgid": _match_first([r'appmsgid = "(\d+)"'], html),
        "comment_id": _match_first(
            [
                r"var comment_id = '([^']+)'",
                r"comment_id:\s*JsDecode\('([^']+)'\)",
            ],
            html,
        ),
        "sessionid": _match_first(
            [
                r'var sessionid = "" \|\| "([^"]+)"',
                r"sessionid:\s*JsDecode\('([^']+)'\)",
            ],
            html,
        ),
        "comment_scene": _match_first([r"var scene = (\d+);"], html),
        "scene": _match_first([r'var source = "([^"]*)";'], html) or "",
        "subscene": _match_first([r'var subscene = "([^"]*)";'], html) or "",
        "send_time": _match_first(
            [
                r"send_time: '(\d+)' \* 1",
                r'var ct = "(\d+)"',
            ],
            html,
        ),
        "enterid": _match_first([r"enterid: '(\d+)' \* 1"], html),
        "comment_count": _as_int(
            _match_first([r"elected_comment_total_cnt: '(\d+)' \* 1"], html)
        ),
    }
    return metadata


def extract_article_query_from_html(html: str) -> Dict[str, str]:
    result = {
        "__biz": _match_first([r'var biz = "([^"]+)"'], html) or "",
        "mid": _match_first([r'var mid = "(\d+)"'], html) or "",
        "idx": _match_first([r'var idx = "(\d+)"'], html) or "",
        "sn": _match_first([r'var sn = "([^"]+)"'], html) or "",
    }
    if not all(result.values()):
        raise RuntimeError("Could not extract __biz/mid/idx/sn from article HTML.")
    return result


def extract_article_query_from_url(article_url: str) -> Dict[str, str]:
    query = parse_qs(urlparse(article_url or "").query)
    return {
        "__biz": query.get("__biz", [""])[0],
        "mid": query.get("mid", [""])[0],
        "idx": query.get("idx", [""])[0],
        "sn": query.get("sn", [""])[0],
    }


def replay_appmsg_comment(
    query: Dict[str, str],
    cookies: Dict[str, str],
    article_meta: Dict[str, Optional[str] | Optional[int]],
    article_url: str,
) -> Dict:
    if not article_meta.get("appmsgid") or not article_meta.get("comment_id"):
        return {"base_resp": {"ret": -1, "errmsg": "comment metadata missing"}}

    url = "https://mp.weixin.qq.com/mp/appmsg_comment"
    params = {
        "action": "getcomment",
        "comment_scene": str(article_meta.get("comment_scene") or "75"),
        "scene": str(article_meta.get("scene") or ""),
        "subscene": str(article_meta.get("subscene") or ""),
        "__biz": query["__biz"],
        "appmsgid": str(article_meta["appmsgid"]),
        "idx": query["idx"],
        "comment_id": str(article_meta["comment_id"]),
        "offset": "0",
        "limit": "999",
        "send_time": str(article_meta.get("send_time") or ""),
        "sessionid": str(article_meta.get("sessionid") or ""),
        "enterid": str(article_meta.get("enterid") or ""),
        "uin": query["uin"],
        "key": query["key"],
        "pass_ticket": cookies.get("pass_ticket") or query["pass_ticket"],
        "wxtoken": cookies.get("wxtokenkey") or query.get("wxtoken", "777"),
        "devicetype": cookies.get("devicetype") or query.get("devicetype", "UnifiedPCWindows"),
        "clientversion": cookies.get("version") or query.get("version", ""),
        "appmsg_token": cookies.get("appmsg_token", ""),
        "x5": "0",
        "f": "json",
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 NetType/WIFI "
            "MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090a13) "
            "UnifiedPCWindowsWechat(0xf2541721) XWEB/19027"
        ),
        "Referer": article_url,
        "Origin": "https://mp.weixin.qq.com",
        "X-Requested-With": "XMLHttpRequest",
    }
    response = create_http_session().get(
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def extract_comment_metrics(payload: Dict) -> Dict[str, Optional[int]]:
    base_resp = payload.get("base_resp", {})
    if base_resp.get("ret") not in (None, 0):
        return {
            "comment_count": None,
            "comment_reply_count": None,
        }

    comment_count = _as_int(payload.get("elected_comment_total_cnt"))
    elected_comment = payload.get("elected_comment") or []
    reply_total = 0
    reply_seen = False

    for comment in elected_comment:
        if not isinstance(comment, dict):
            continue

        reply_new = comment.get("reply_new")
        if isinstance(reply_new, dict):
            reply_total_cnt = _as_int(reply_new.get("reply_total_cnt"))
            if reply_total_cnt is not None:
                reply_total += reply_total_cnt
                reply_seen = True
                continue

            reply_list = reply_new.get("reply_list") or []
            if isinstance(reply_list, list):
                reply_total += len(reply_list)
                reply_seen = True
                continue

        reply = comment.get("reply")
        if isinstance(reply, dict):
            reply_total_cnt = _as_int(reply.get("reply_total_cnt"))
            if reply_total_cnt is not None:
                reply_total += reply_total_cnt
                reply_seen = True
                continue

            reply_list = reply.get("reply_list") or []
            if isinstance(reply_list, list):
                reply_total += len(reply_list)
                reply_seen = True

    return {
        "comment_count": comment_count,
        "comment_reply_count": reply_total if reply_seen else None,
    }


def replay_getappmsgext(
    query: Dict[str, str],
    cookies: Dict[str, str],
    referer_url: Optional[str] = None,
) -> Dict:
    url = "https://mp.weixin.qq.com/mp/getappmsgext"
    params = {
        "__biz": query["__biz"],
        "mid": query["mid"],
        "idx": query["idx"],
        "sn": query["sn"],
        "key": query["key"],
        "uin": query["uin"],
        "pass_ticket": cookies.get("pass_ticket") or query["pass_ticket"],
        "wxtoken": cookies.get("wxtokenkey") or query.get("wxtoken", "777"),
        "appmsg_token": cookies.get("appmsg_token", ""),
        "x5": "0",
        "f": "json",
        "user_article_role": "0",
        "devicetype": cookies.get("devicetype") or query.get("devicetype", "UnifiedPCWindows"),
        "clientversion": cookies.get("version") or query.get("version", ""),
        "version": cookies.get("version") or query.get("version", ""),
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 NetType/WIFI "
            "MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090a13) "
            "UnifiedPCWindowsWechat(0xf2541721) XWEB/19027"
        ),
        "Referer": referer_url or build_article_url(query, cookies),
        "Origin": "https://mp.weixin.qq.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
    }
    data = {
        "is_only_read": "1",
        "is_temp_url": "0",
        "appmsg_type": "9",
        "reward_uin_count": "0",
    }

    response = create_http_session().post(
        url,
        params=params,
        data=data,
        headers=headers,
        cookies=cookies,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def write_result_json(result: Dict, output_file: Path = DEFAULT_DEBUG_OUTPUT_FILE) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_latest_result(result: Dict, output_file: Path = DEFAULT_DEBUG_OUTPUT_FILE) -> None:
    write_result_json(result, output_file)


def build_result_metadata(article_url: str) -> Dict[str, str]:
    return {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "article_url": article_url,
    }


def build_output_result(
    stats: Dict[str, Optional[int] | Optional[bool]],
    comment_metrics: Dict[str, Optional[int]],
    comment_error: Optional[str] = None,
    publish_time: Optional[datetime] = None,
    article_url: str = "",
) -> Dict:
    comment_count = comment_metrics.get("comment_count")
    comment_reply_count = comment_metrics.get("comment_reply_count")
    comment_total_count = None
    if comment_count is not None and comment_reply_count is not None:
        comment_total_count = comment_count + comment_reply_count

    result = {
        **build_result_metadata(article_url),
        "publish_time": publish_time.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if publish_time is not None
        else None,
        "read_num": stats.get("read_num"),
        "like_num": stats.get("like_num"),
        "old_like_num": stats.get("old_like_num"),
        "share_num": stats.get("share_num"),
        "collect_num": stats.get("collect_num"),
        "is_login": stats.get("is_login"),
        "comment_count": comment_count,
        "comment_reply_count": comment_reply_count,
        "comment_total_count": comment_total_count,
    }
    if comment_error:
        result["comment_reply_count_error"] = comment_error
    return result


def collect_stats(
    *,
    article_url: str,
    session_file: Path = DEFAULT_SESSION_FILE,
    live_log_file: Path = DEFAULT_LIVE_LOG_FILE,
    log_file: Optional[Path] = None,
    mid: str = "2247532288",
    idx: str = "1",
    sn: str = "4d6252412cc5aa0d7b8ea98730957ee1",
) -> Dict:
    session = load_session_file(session_file)
    live_lines = read_lines(live_log_file) if live_log_file.exists() else []
    cookies = parse_cookie_header(session.get("cookie_header", ""))
    for key in (
        "appmsg_token",
        "wap_sid2",
        "wxuin",
        "wxtokenkey",
        "devicetype",
        "version",
        "pass_ticket",
    ):
        value = session.get(key)
        if value:
            cookies[key] = value

    query = {}
    if log_file:
        lines = read_lines(log_file)
        query = find_referer_query(lines, mid=mid, idx=idx, sn=sn)
        cookies.update(build_cookies(lines))

    query, cookies = apply_session_overrides(query, cookies, session)
    live_overrides = load_live_overrides(live_log_file)
    query, cookies = apply_live_overrides(query, cookies, live_overrides)
    url_query = extract_article_query_from_url(article_url)
    for key, value in url_query.items():
        if value and not query.get(key):
            query[key] = value
    article_html = fetch_article_html(article_url, cookies)
    # Follow the old project logic: once the article page is available, the
    # actual page variables are the source of truth for __biz/mid/idx/sn.
    try:
        html_query = extract_article_query_from_html(article_html)
    except RuntimeError:
        html_query = {}
    for key in ("__biz", "mid", "idx", "sn"):
        value = html_query.get(key)
        if value:
            query[key] = value

    canonical_article_url = build_article_url(query, cookies)

    captured_getappmsgext = find_captured_request_entry(
        live_lines,
        path_fragment="/mp/getappmsgext",
        article_query=query,
    )
    if captured_getappmsgext:
        payload = replay_captured_request(
            captured_getappmsgext,
            default_referer=canonical_article_url,
            extra_cookies=cookies,
        )
    else:
        payload = replay_getappmsgext(query, cookies, referer_url=canonical_article_url)
    stats = payload.get("appmsgstat", {})
    article_meta = extract_article_comment_metadata(article_html)
    publish_time = extract_article_publish_time(article_html)
    comment_metrics = {
        "comment_count": article_meta.get("comment_count"),
        "comment_reply_count": None,
    }
    comment_payload = None
    comment_error = None

    try:
        captured_comment = find_captured_request_entry(
            live_lines,
            path_fragment="/mp/appmsg_comment",
            article_query=query,
            action="getcomment",
        )
        if captured_comment:
            comment_payload = replay_captured_request(
                captured_comment,
                default_referer=canonical_article_url,
                extra_cookies=cookies,
            )
        else:
            comment_payload = replay_appmsg_comment(
                query,
                cookies,
                article_meta,
                canonical_article_url,
            )
        api_comment_metrics = extract_comment_metrics(comment_payload)
        if api_comment_metrics["comment_count"] is not None:
            comment_metrics["comment_count"] = api_comment_metrics["comment_count"]
        comment_metrics["comment_reply_count"] = api_comment_metrics["comment_reply_count"]
        if comment_payload.get("base_resp", {}).get("ret") not in (None, 0):
            comment_error = comment_payload.get("base_resp", {}).get("errmsg") or comment_payload.get("errmsg")
    except requests.RequestException as exc:
        comment_error = str(exc)

    return build_output_result(
        stats,
        comment_metrics,
        comment_error,
        publish_time=publish_time,
        article_url=article_url,
    )


def main() -> None:
    args = parse_args()
    result = collect_stats(
        article_url=args.article_url,
        session_file=Path(args.session_file),
        live_log_file=Path(args.live_log_file),
        log_file=Path(args.log_file) if args.log_file else None,
        mid=args.mid,
        idx=args.idx,
        sn=args.sn,
    )
    write_result_json(result, Path(args.output_file))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
