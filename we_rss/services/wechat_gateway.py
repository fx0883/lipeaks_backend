from datetime import datetime, timezone as dt_timezone
import json
import re
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from requests.cookies import cookiejar_from_dict


def build_wechat_session(session_factory=None):
    session = (session_factory or requests.Session)()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://mp.weixin.qq.com/",
        }
    )
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
    if path_parts:
        return path_parts[-1]
    return ""


def normalize_publish_time(raw_value):
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
    publish_page = payload.get("publish_page")
    if isinstance(publish_page, str):
        publish_page = json.loads(publish_page)
    publish_list = (publish_page or {}).get("publish_list") or []
    articles = []
    for item in publish_list:
        publish_info = item.get("publish_info")
        if isinstance(publish_info, str):
            publish_info = json.loads(publish_info)
        publish_info = publish_info or {}

        appmsg = publish_info.get("appmsg")
        if isinstance(appmsg, dict):
            articles.append(appmsg)
        elif isinstance(appmsg, list):
            articles.extend(appmsg)

        appmsgex = publish_info.get("appmsgex") or []
        if isinstance(appmsgex, dict):
            articles.append(appmsgex)
        else:
            articles.extend(appmsgex)
    return articles
