from datetime import datetime, timedelta, timezone as dt_timezone
import json
import re
from urllib.parse import parse_qs, parse_qsl, urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from requests.cookies import cookiejar_from_dict
from urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


WECHAT_ARTICLE_STABLE_QUERY_KEYS = ("__biz", "mid", "idx", "sn", "chksm")
WECHAT_ARTICLE_TIMEZONE = dt_timezone(timedelta(hours=8))
WECHAT_MOBILE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "MicroMessenger/8.0.42(0x18002a2a) NetType/WIFI Language/zh_CN"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://mp.weixin.qq.com/",
}


def build_wechat_session(session_factory=None):
    session = (session_factory or requests.Session)()
    session.headers.update(WECHAT_MOBILE_HEADERS)
    session.verify = False
    session.trust_env = False
    return session


def cookie_string_to_dict(cookie_string):
    cookie_dict = {}
    for pair in str(cookie_string or "").split(";"):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        cookie_dict[key.strip()] = value.strip()
    return cookie_dict


def load_credential_cookies(session, cookie_string):
    cookie_dict = cookie_string_to_dict(cookie_string)
    if cookie_dict:
        session.cookies.update(cookiejar_from_dict(cookie_dict))
    return cookie_dict


def extract_source_id_from_url(url):
    parsed = urlparse(url or "")
    path_parts = [part for part in parsed.path.split("/") if part]
    if path_parts == ["s"]:
        return ""
    if path_parts:
        return path_parts[-1]
    return ""


def normalize_wechat_article_url(url):
    raw_url = str(url or "").strip()
    if not raw_url:
        return ""

    parsed = urlparse(raw_url)
    stable_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=False)
        if key in WECHAT_ARTICLE_STABLE_QUERY_KEYS and value
    ]
    normalized_query = urlencode(stable_query, doseq=True)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            normalized_query,
            "",
        )
    )


def infer_article_type_from_url(url, default="news"):
    idx_value = parse_qs(urlparse(url or "").query).get("idx", [""])[0]
    try:
        return "newspic" if int(idx_value) > 1 else "news"
    except (TypeError, ValueError):
        return default


def infer_article_type_from_item(item, default="news"):
    try:
        item_show_type = int((item or {}).get("item_show_type"))
    except (TypeError, ValueError):
        return default

    if item_show_type == 8:
        return "newspic"
    if item_show_type == 0:
        return "news"
    return default


def _legacy_normalize_publish_time(raw_value):
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, (int, float)):
        return timezone.datetime.fromtimestamp(raw_value, tz=dt_timezone.utc)
    parsed = parse_datetime(str(raw_value))
    if parsed is not None:
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed
    raw_text = str(raw_value).strip()
    try:
        parsed = datetime.strptime(raw_text, "%Y-%m-%d %H:%M")
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    except ValueError:
        pass
    for fmt in ("%Y年%m月%d日 %H:%M", "%Y年%m月%d日", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(raw_text, fmt)
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        except ValueError:
            continue
    for fmt in ("%m月%d日",):
        try:
            current_time = timezone.localtime()
            parsed = datetime.strptime(raw_text, fmt).replace(year=current_time.year)
            aware = timezone.make_aware(parsed, timezone.get_current_timezone())
            if aware > current_time:
                aware = aware.replace(year=aware.year - 1)
            return aware
        except ValueError:
            continue
    return None


def normalize_publish_time(raw_value):
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, (int, float)):
        return timezone.datetime.fromtimestamp(raw_value, tz=dt_timezone.utc)

    parsed = parse_datetime(str(raw_value))
    if parsed is not None:
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, WECHAT_ARTICLE_TIMEZONE)
        return parsed

    raw_text = str(raw_value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            parsed = datetime.strptime(raw_text, fmt)
            return timezone.make_aware(parsed, WECHAT_ARTICLE_TIMEZONE)
        except ValueError:
            continue

    return None


def extract_script_publish_time(script_text):
    text_patterns = [
        r"var\s+createTime\s*=\s*'([^']+)'",
        r'var\s+createTime\s*=\s*"([^"]+)"',
        r"create_time:\s*JsDecode\('([^']+)'\)",
    ]
    for pattern in text_patterns:
        match = re.search(pattern, script_text)
        if not match:
            continue
        publish_time = normalize_publish_time(match.group(1))
        if publish_time is not None:
            return publish_time

    timestamp_patterns = [
        r"var\s+oriCreateTime\s*=\s*'(\d+)'",
        r'var\s+create_time\s*=\s*"(\d+)"\s*\*\s*1',
        r'var\s+ct\s*=\s*"(\d+)"',
        r"ori_create_time:\s*'(\d+)'\s*\*\s*1",
        r"create_timestamp:\s*'(\d+)'\s*\*\s*1",
    ]
    for pattern in timestamp_patterns:
        match = re.search(pattern, script_text)
        if not match:
            continue
        publish_time = normalize_publish_time(int(match.group(1)))
        if publish_time is not None:
            return publish_time

    return None


def build_description_from_content(content, *, max_length=200):
    soup = BeautifulSoup(content or "", "html.parser")
    text = soup.get_text(" ", strip=True)
    if len(text) <= max_length:
        return text
    return f"{text[:max_length].rstrip()}..."


def get_wechat_article_page_status(page_text):
    environment_error_markers = {
        "当前环境异常，完成验证后即可继续访问": "当前环境异常，完成验证后即可继续访问",
    }
    for marker, message in environment_error_markers.items():
        if marker in page_text:
            raise ValueError(message)

    deleted_markers = [
        "该内容已被发布者删除",
        "The content has been deleted by the author.",
        "该内容暂时无法查看",
        "Unable to view this content because it violates regulation",
        "内容审核中",
        "违规无法查看",
        "发送失败无法查看",
    ]
    return "deleted" if any(marker in page_text for marker in deleted_markers) else "active"


def parse_wechat_article_html(html, url):
    soup = BeautifulSoup(html or "", "html.parser")
    page_text = soup.get_text(" ", strip=True)
    content_node = soup.select_one("#js_content") or soup.select_one("#js_article")
    content = content_node.decode_contents().strip() if content_node else ""

    title = ""
    description = ""
    pic_url = ""
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_description = soup.find("meta", attrs={"property": "og:description"})
    twitter_image = soup.find("meta", attrs={"property": "twitter:image"})
    if og_title:
        title = og_title.get("content", "")
    if og_description:
        description = og_description.get("content", "")
    if twitter_image:
        pic_url = twitter_image.get("content", "")

    mp_name = ""
    mp_name_node = soup.select_one("#js_name") or soup.select_one("#js_wx_follow_nickname")
    if mp_name_node:
        mp_name = mp_name_node.get_text(strip=True)

    mp_cover = ""
    mp_cover_node = soup.select_one("#js_like_profile_bar .wx_follow_avatar img")
    if mp_cover_node:
        mp_cover = mp_cover_node.get("src", "")

    publish_time = None
    publish_node = soup.select_one("#publish_time")
    if publish_node:
        publish_time = normalize_publish_time(publish_node.get_text(strip=True))

    script_text = "\n".join(script.get_text(" ", strip=False) for script in soup.find_all("script"))
    if publish_time is None:
        publish_time = extract_script_publish_time(script_text)
    biz = ""
    biz_match = re.search(r'var\s+biz\s*=\s*"([^"]+)"', script_text)
    if biz_match:
        biz = biz_match.group(1)
    if not biz:
        biz_match = re.search(r'window\.__biz\s*=\s*"([^"]+)"', script_text)
        if biz_match:
            biz = biz_match.group(1)
    if not biz:
        biz = parse_qs(urlparse(url or "").query).get("__biz", [""])[0]

    deleted_markers = [
        "该内容已被发布者删除",
        "The content has been deleted by the author.",
        "该内容暂时无法查看",
        "Unable to view this content because it violates regulation",
    ]
    status = get_wechat_article_page_status(page_text)
    if not description:
        description = build_description_from_content(content)
    if status == "deleted":
        content = "DELETED"
    stats = {}
    for field in [
        "read_num",
        "like_num",
        "old_like_num",
        "share_num",
        "collect_num",
        "comment_count",
        "comment_reply_count",
        "comment_total_count",
    ]:
        match = re.search(rf'["\']?{field}["\']?\s*[:=]\s*["\']?(\d+)', script_text)
        if match:
            stats[field] = int(match.group(1))

    payload = {
        "source_id": extract_source_id_from_url(url),
        "article_type": infer_article_type_from_url(url),
        "title": title,
        "description": description,
        "content": content,
        "url": url,
        "pic_url": pic_url,
        "publish_time": publish_time,
        "status": status,
        "biz": biz,
        "mp_name": mp_name,
        "mp_cover": mp_cover,
    }
    payload.update(stats)
    return payload


def parse_publish_page_articles(payload):
    publish_list = get_publish_page_records(payload)
    articles = []
    for item in publish_list:
        publish_info = item.get("publish_info")
        if isinstance(publish_info, str):
            try:
                publish_info = json.loads(publish_info)
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
        publish_info = publish_info or {}

        appmsg = publish_info.get("appmsg")
        if isinstance(appmsg, dict):
            articles.append({**appmsg, "article_type": infer_article_type_from_item(appmsg, default="news")})
        elif isinstance(appmsg, list):
            articles.extend(
                {**item, "article_type": infer_article_type_from_item(item, default="news")}
                for item in appmsg
            )

        appmsgex = publish_info.get("appmsgex") or []
        if isinstance(appmsgex, dict):
            articles.append({**appmsgex, "article_type": infer_article_type_from_item(appmsgex, default="newspic")})
        else:
            articles.extend(
                {**item, "article_type": infer_article_type_from_item(item, default="newspic")}
                for item in appmsgex
            )
    return articles


def get_publish_page_records(payload):
    publish_page = payload.get("publish_page")
    if isinstance(publish_page, str):
        publish_page = json.loads(publish_page)
    return (publish_page or {}).get("publish_list") or []
