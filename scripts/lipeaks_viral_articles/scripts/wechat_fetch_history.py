"""
wechat_fetch_history.py
-----------------------
从微信公众号历史文章接口 (profile_ext?action=getmsg) 拉取文章列表。

凭证来源：复用 wechat_stats_mitm_addon.py 生成的 session.json。
不依赖微信公众平台后台登录态 (token/credential)。
本模块只做网络请求和数据解析，不做任何 Django/ORM 操作。
"""
from __future__ import annotations

import html
import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter("ignore", InsecureRequestWarning)

# ---------------------------------------------------------------------------
# 路径常量（与 wechat_replay_getappmsgext.py 保持一致）
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
_POC_ROOT = _SCRIPTS_DIR.parent
DEFAULT_SESSION_FILE = _POC_ROOT / "output" / "wechat-stats" / "session.json"

# 目标接口
_PROFILE_EXT_URL = "https://mp.weixin.qq.com/mp/profile_ext"

# 微信客户端 User-Agent（与现有重放脚本保持一致）
_WECHAT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 NetType/WIFI "
    "MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090a13) "
    "UnifiedPCWindowsWechat(0xf2541721) XWEB/19027"
)


# ---------------------------------------------------------------------------
# Session 加载（复用与 wechat_replay_getappmsgext.py 一致的接口）
# ---------------------------------------------------------------------------

def load_session_file(session_file: Path = DEFAULT_SESSION_FILE) -> Dict[str, str]:
    """读取 mitmproxy 生成的 session.json，返回凭证字典。"""
    if not session_file.exists():
        return {}
    try:
        return json.loads(session_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


# ---------------------------------------------------------------------------
# 内部辅助函数
# ---------------------------------------------------------------------------

def _unescape(value: Optional[str]) -> str:
    """对 HTML 实体和 URL 中的编码进行反转义。"""
    if not value:
        return ""
    return html.unescape(str(value))


def _parse_publish_time(unix_ts) -> Optional[datetime]:
    """将 Unix 时间戳转为 UTC datetime，容忍 None 和非法值。"""
    if unix_ts is None or unix_ts == "":
        return None
    try:
        return datetime.fromtimestamp(int(unix_ts), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def _build_http_session() -> requests.Session:
    """创建不走本机代理的 HTTP Session（避免流量再次经过 mitmproxy）。"""
    session = requests.Session()
    session.trust_env = False   # 忽略系统代理环境变量
    session.verify = False
    return session


def _build_request_params(*, biz: str, session: Dict[str, str], offset: int, count: int) -> Dict[str, str]:
    """组装 profile_ext 接口所需的 Query Parameters。"""
    return {
        "action": "getmsg",
        "__biz": biz,
        "f": "json",
        "offset": str(offset),
        "count": str(count),
        "is_ok": "1",
        "scene": "124",
        "uin": session.get("uin", ""),
        "key": session.get("key", ""),
        "pass_ticket": session.get("pass_ticket", ""),
    }


def _build_request_headers(session: Dict[str, str]) -> Dict[str, str]:
    """组装请求 Headers，携带 cookie 和微信客户端 UA。"""
    return {
        "User-Agent": _WECHAT_UA,
        "Cookie": session.get("cookie_header", ""),
    }


def _parse_article_entry(entry: dict, biz: str, publish_time: Optional[datetime]) -> Optional[Dict]:
    """
    从单条图文消息的 app_msg_ext_info 或 multi_app_msg_item_list 中提取文章字段。
    返回符合 _upsert_articles 期望的 payload 字典，缺少 URL 时返回 None。
    """
    title = _unescape(entry.get("title", ""))
    url = _unescape(entry.get("content_url", ""))
    if not url:
        return None

    # 将 &amp; 还原为 & （微信接口有时会做二次 HTML 实体编码）
    url = url.replace("&amp;", "&")

    return {
        "source_id": "",          # profile_ext 接口不返回 source_id
        "article_type": "news",   # 图文消息固定为 news
        "title": title,
        "description": _unescape(entry.get("digest", "")),
        "content": "",            # 历史接口不返回正文内容
        "url": url,
        "pic_url": _unescape(entry.get("cover", "")),
        "publish_time": publish_time,
        "status": "active",
        "read_num": 0,
        "like_num": 0,
        "old_like_num": 0,
        "share_num": 0,
        "collect_num": 0,
        "comment_count": 0,
        "comment_reply_count": 0,
        "comment_total_count": 0,
        "biz": biz,
    }


def _parse_msg_list(msg_list: list, biz: str) -> List[Dict]:
    """
    遍历 general_msg_list['list']，过滤出图文消息并展平多图文条目。
    返回文章 payload 列表（格式与 collect_feed_batch 返回的 articles 一致）。
    """
    articles: List[Dict] = []

    for msg in msg_list:
        comm_msg_info = msg.get("comm_msg_info") or {}
        # 图文消息的 type 值为 49
        if comm_msg_info.get("type") != 49:
            continue

        publish_time = _parse_publish_time(comm_msg_info.get("datetime"))
        app_msg_ext_info = msg.get("app_msg_ext_info") or {}

        if not app_msg_ext_info:
            continue

        # 主图文（头条）
        main_entry = _parse_article_entry(app_msg_ext_info, biz, publish_time)
        if main_entry:
            articles.append(main_entry)

        # 副图文（次条及以后）
        for sub_entry in app_msg_ext_info.get("multi_app_msg_item_list") or []:
            parsed = _parse_article_entry(sub_entry, biz, publish_time)
            if parsed:
                articles.append(parsed)

    return articles


# ---------------------------------------------------------------------------
# 公开接口：单批次拉取
# ---------------------------------------------------------------------------

def fetch_history_batch(
    *,
    biz: str,
    session: Dict[str, str],
    offset: int = 0,
    count: int = 10,
    timeout: int = 30,
    sleep_seconds: float = 2.0,
    _sleep_func=None,
) -> Dict:
    """
    拉取公众号历史文章的单个批次。

    :param biz:          目标公众号的 __biz 值（从 WechatFeed.biz 字段读取）
    :param session:      load_session_file() 返回的凭证字典
    :param offset:       翻页偏移量（第一页传 0）
    :param count:        每页条数（微信接口上限约 10，建议用默认值）
    :param timeout:      HTTP 请求超时秒数
    :param sleep_seconds: 请求前的节流等待，仅在 offset > 0 时生效
    :param _sleep_func:  注入点，用于单测 mock
    :return: {
        "articles": [...],   # 字段格式与 WechatFeedGateway.collect_feed_batch 一致
        "has_more": bool,
        "next_offset": int,
        "ret": int,          # 微信接口原始 ret 码
        "errmsg": str,
    }
    """
    sleep_fn = _sleep_func or time.sleep
    if offset > 0 and sleep_seconds > 0:
        sleep_fn(sleep_seconds)

    http_session = _build_http_session()
    params = _build_request_params(biz=biz, session=session, offset=offset, count=count)
    headers = _build_request_headers(session)

    response = http_session.get(
        _PROFILE_EXT_URL,
        params=params,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()

    try:
        data = response.json()
    except (ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"WeChat history API returned non-JSON response: {exc}") from exc

    ret = int(data.get("ret") or 0)
    errmsg = str(data.get("errmsg") or "")

    if ret != 0:
        return {
            "articles": [],
            "has_more": False,
            "next_offset": offset,
            "ret": ret,
            "errmsg": errmsg,
        }

    # 二次 JSON 解析 general_msg_list
    general_msg_list_raw = data.get("general_msg_list", "")
    if not general_msg_list_raw:
        return {
            "articles": [],
            "has_more": False,
            "next_offset": offset,
            "ret": ret,
            "errmsg": errmsg,
        }

    try:
        general_msg_list = json.loads(general_msg_list_raw)
    except (ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to parse general_msg_list as JSON: {exc}") from exc

    msg_list = general_msg_list.get("list") or []
    articles = _parse_msg_list(msg_list, biz)

    # can_msg_continue == 1 表示还有更多历史
    has_more = bool(int(data.get("can_msg_continue") or 0))
    # next_offset 由接口返回的 next_offset 字段决定，如果没有则用当前 offset + count
    raw_next = data.get("next_offset")
    if raw_next is not None:
        try:
            next_offset = int(raw_next)
        except (ValueError, TypeError):
            next_offset = offset + count
    else:
        next_offset = offset + count

    return {
        "articles": articles,
        "has_more": has_more,
        "next_offset": next_offset,
        "ret": ret,
        "errmsg": errmsg,
    }
