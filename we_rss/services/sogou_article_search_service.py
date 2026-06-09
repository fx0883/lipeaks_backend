import math
import random
import re
from datetime import datetime, timedelta, timezone as dt_timezone
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

from we_rss.services.wechat_gateway import normalize_wechat_article_url


SOGOU_SEARCH_TIMEZONE = dt_timezone(timedelta(hours=8))
DISPLAY_DATE_FORMAT = "%Y\u5e74%m\u6708%d\u65e5"
RELATIVE_DAY_PATTERN = r"(\d+)\s*\u5929\u524d"
RELATIVE_HOUR_PATTERN = r"(\d+)\s*\u5c0f\u65f6\u524d"
RELATIVE_MINUTE_PATTERN = r"(\d+)\s*\u5206\u949f\u524d"
TEXT_JUST_NOW = "\u521a\u521a"
TEXT_TODAY = "\u4eca\u5929"
TEXT_YESTERDAY = "\u6628\u5929"


class SogouArticleSearchService:
    WARMUP_URL = "https://weixin.sogou.com/"
    SEARCH_URL = "https://weixin.sogou.com/weixin"
    SEARCH_REFERER = "https://weixin.sogou.com/"
    MOBILE_SEARCH_URL = "https://m.sogou.com/web/searchList.jsp"
    MOBILE_REFERER = "https://m.sogou.com/"
    WECHAT_REFERER = "https://mp.weixin.qq.com/"
    MAX_LIMIT = 50
    PAGE_SIZE = 10
    REQUEST_TIMEOUT_SECONDS = 15
    SEARCH_PAGE_ATTEMPTS = 6
    USER_AGENTS = (
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.2 Safari/605.1.15"
        ),
        (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) "
            "Gecko/20100101 Firefox/123.0"
        ),
    )
    BASE_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "identity",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://weixin.sogou.com/",
    }
    MOBILE_USER_AGENT = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
        "Mobile/15E148 Safari/604.1"
    )

    @classmethod
    def search_wechat_articles(cls, *, query, limit=10):
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return {"query": "", "total": 0, "items": []}

        try:
            normalized_limit = max(1, min(int(limit), cls.MAX_LIMIT))
        except (TypeError, ValueError):
            normalized_limit = 10

        try:
            items = cls._search_weixin_pages(
                query=normalized_query,
                limit=normalized_limit,
            )
            if not items:
                items = cls._search_mobile_web_fallback(
                    query=normalized_query,
                    limit=normalized_limit,
                )
        except Exception:
            return {"query": normalized_query, "total": 0, "items": []}

        return {
            "query": normalized_query,
            "total": len(items),
            "items": items[:normalized_limit],
        }

    @classmethod
    def _search_weixin_pages(cls, *, query, limit):
        items = []
        seen_urls = set()
        pages_needed = int(math.ceil(limit / cls.PAGE_SIZE))

        for page in range(1, pages_needed + 1):
            page_result = cls._fetch_search_page_items_with_retries(
                query=query,
                page=page,
                max_results=limit - len(items),
            )
            page_items = page_result["items"]
            if not page_items and page_result["is_terminal_empty"]:
                break

            for item in page_items:
                item_url = str(item.get("url") or "").strip()
                if not item_url or item_url in seen_urls:
                    continue
                seen_urls.add(item_url)
                items.append(item)
                if len(items) >= limit:
                    return items

        return items

    @classmethod
    def _fetch_search_page_items_with_retries(cls, *, query, page, max_results):
        saw_terminal_empty = False
        param_variants = (
            {
                "query": query,
                "s_from": "input",
                "_sug_": "n",
                "type": 2,
                "page": page,
                "ie": "utf8",
            },
            {
                "query": query,
                "type": 2,
                "page": page,
                "ie": "utf8",
            },
            {
                "keyword": query,
                "query": query,
                "type": 2,
                "page": page,
                "ie": "utf8",
            },
        )

        for attempt_index in range(cls.SEARCH_PAGE_ATTEMPTS):
            session = cls._build_session()
            try:
                cls._warmup_session(session)
            except Exception:
                pass

            try:
                html = cls._fetch_search_page(
                    session,
                    param_variants[attempt_index % len(param_variants)],
                )
            except Exception:
                continue

            if cls._is_antispider_page(url=cls.SEARCH_URL, html=html):
                continue

            parsed_items = cls._parse_search_html(
                html,
                max_results=max_results,
            )
            if not parsed_items:
                saw_terminal_empty = True
                break

            return {
                "items": cls._resolve_article_urls(session, parsed_items),
                "is_terminal_empty": False,
            }

        return {"items": [], "is_terminal_empty": saw_terminal_empty}

    @classmethod
    def _build_session(cls):
        session = requests.Session()
        session.trust_env = False
        session.headers.update(cls.BASE_HEADERS)
        return session

    @classmethod
    def _warmup_session(cls, session):
        try:
            response = session.get(
                cls.WARMUP_URL,
                headers=cls._build_headers(),
                timeout=cls.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except Exception:
            # Search must not fail just because the optional warmup request is unavailable.
            return

    @classmethod
    def _fetch_search_page(cls, session, params):
        response = session.get(
            cls.SEARCH_URL,
            params=params,
            headers=cls._build_headers(referer=cls.SEARCH_REFERER),
            timeout=cls.REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return cls._decode_html_body(response.content, response.headers)

    @classmethod
    def _build_headers(cls, *, referer=None):
        return {
            **cls.BASE_HEADERS,
            "Host": "weixin.sogou.com",
            "Referer": referer or cls.SEARCH_REFERER,
            "User-Agent": random.choice(cls.USER_AGENTS),
        }

    @classmethod
    def _build_wechat_headers(cls):
        return {
            "Accept": cls.BASE_HEADERS["Accept"],
            "Accept-Language": cls.BASE_HEADERS["Accept-Language"],
            "Referer": cls.WECHAT_REFERER,
            "User-Agent": random.choice(cls.USER_AGENTS),
        }

    @classmethod
    def _build_mobile_search_headers(cls):
        return {
            "Accept": cls.BASE_HEADERS["Accept"],
            "Accept-Language": cls.BASE_HEADERS["Accept-Language"],
            "Referer": cls.MOBILE_REFERER,
            "User-Agent": cls.MOBILE_USER_AGENT,
        }

    @classmethod
    def _parse_search_html(cls, html, *, max_results):
        soup = BeautifulSoup(html or "", "html.parser")
        articles = []

        for element in soup.select("ul.news-list > li"):
            if len(articles) >= max_results:
                break
            article = cls._parse_article_item(element)
            if article:
                articles.append(article)

        return articles

    @classmethod
    def _parse_article_item(cls, element):
        title_link = element.select_one("h3 a")
        if title_link is None:
            return None

        href = str(title_link.get("href") or "").strip()
        if not href:
            return None

        article_url = urljoin("https://weixin.sogou.com", href)
        summary = cls._clean_text(element.select_one("p.txt-info"))
        source_box = element.select_one(".s-p")

        datetime_text = ""
        date_text = ""
        date_description = ""
        source = ""

        if source_box is not None:
            published_at = cls._extract_published_at(source_box)
            if published_at is not None:
                datetime_text = published_at.strftime("%Y-%m-%d %H:%M:%S")
                date_text = published_at.strftime(DISPLAY_DATE_FORMAT)
                date_description = cls._describe_relative_time(published_at)
            else:
                time_text = cls._extract_time_text(source_box)
                if time_text:
                    parsed_time = cls._parse_relative_time(time_text)
                    if parsed_time is not None:
                        datetime_text = parsed_time.strftime("%Y-%m-%d %H:%M:%S")
                        date_text = parsed_time.strftime(DISPLAY_DATE_FORMAT)
                    date_description = time_text

            source = cls._clean_text(source_box.select_one(".all-time-y2"))
            if not source:
                source = cls._clean_text(source_box.select_one("a.account"))

        return {
            "title": cls._clean_text(title_link),
            "url": article_url,
            "summary": summary,
            "datetime": datetime_text,
            "date_text": date_text,
            "date_description": date_description or date_text,
            "source": source,
        }

    @classmethod
    def _search_mobile_web_fallback(cls, *, query, limit):
        response = requests.get(
            cls.MOBILE_SEARCH_URL,
            params={
                "keyword": f"{query} site:mp.weixin.qq.com",
                "query": query,
                "ie": "utf8",
            },
            headers=cls._build_mobile_search_headers(),
            timeout=cls.REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        html = cls._decode_html_body(response.content, response.headers)
        if cls._is_antispider_page(url=response.url, html=html):
            return []
        return cls._parse_mobile_web_search_html(html=html, max_results=limit)

    @classmethod
    def _parse_mobile_web_search_html(cls, *, html, max_results):
        soup = BeautifulSoup(html or "", "html.parser")
        articles = []
        seen_urls = set()

        for card in soup.select('[react_card_root="1"]'):
            if len(articles) >= max_results:
                break
            article = cls._parse_mobile_web_search_item(card)
            if not article:
                continue
            if article["url"] in seen_urls:
                continue
            seen_urls.add(article["url"])
            articles.append(article)

        return articles

    @classmethod
    def _parse_mobile_web_search_item(cls, element):
        anchor = element.select_one(
            'a[href*="url=https%3A%2F%2Fmp.weixin.qq.com"],'
            'a[href*="url=http%3A%2F%2Fmp.weixin.qq.com"]'
        )
        if anchor is None:
            return None

        href = str(anchor.get("href") or "").strip()
        if not href:
            return None

        query_pairs = dict(parse_qsl(urlparse(href).query, keep_blank_values=True))
        raw_target_url = unquote(str(query_pairs.get("url") or "").strip())
        if "mp.weixin.qq.com" not in raw_target_url:
            return None

        title_node = element.select_one("h2")
        title = cls._clean_text(title_node) or cls._clean_text(anchor)
        full_text = cls._clean_text(element)
        footer_match = re.search(
            r"(?P<source>[^ ]+)\s+(?P<date>\d{4}-\d{2}-\d{2})$",
            full_text,
        )

        source = ""
        datetime_text = ""
        date_text = ""
        date_description = ""
        summary_text = full_text

        if title and summary_text.startswith(title):
            summary_text = summary_text[len(title):].strip()

        if footer_match:
            source = footer_match.group("source")
            raw_date = footer_match.group("date")
            summary_text = summary_text[: summary_text.rfind(footer_match.group(0))].strip()
            try:
                published_at = datetime.strptime(raw_date, "%Y-%m-%d").replace(
                    tzinfo=SOGOU_SEARCH_TIMEZONE
                )
            except ValueError:
                published_at = None
            if published_at is not None:
                datetime_text = published_at.strftime("%Y-%m-%d %H:%M:%S")
                date_text = published_at.strftime(DISPLAY_DATE_FORMAT)
                date_description = date_text

        return {
            "title": title,
            "url": raw_target_url,
            "summary": summary_text,
            "datetime": datetime_text,
            "date_text": date_text,
            "date_description": date_description,
            "source": source,
        }

    @classmethod
    def _resolve_article_urls(cls, session, items):
        resolved_items = []
        for item in items:
            resolved_item = dict(item)
            resolved_item["url"] = cls._resolve_real_article_url(
                session=session,
                url=resolved_item.get("url"),
            )
            resolved_items.append(resolved_item)
        return resolved_items

    @classmethod
    def _resolve_real_article_url(cls, *, session, url):
        raw_url = str(url or "").strip()
        if not raw_url or "weixin.sogou.com" not in raw_url:
            return raw_url

        try:
            response = session.get(
                raw_url,
                headers=cls._build_headers(referer=cls.SEARCH_REFERER),
                timeout=cls.REQUEST_TIMEOUT_SECONDS,
                allow_redirects=False,
            )
        except Exception:
            return raw_url

        if 300 <= response.status_code < 400:
            redirect_url = response.headers.get("Location") or response.headers.get("location") or ""
            if "mp.weixin.qq.com" in redirect_url:
                return cls._resolve_canonical_wechat_url(session=session, url=redirect_url)
            return raw_url

        html = cls._decode_html_body(response.content, response.headers)
        redirect_url = cls._extract_redirect_url_from_html(html)
        if redirect_url and "mp.weixin.qq.com" in redirect_url:
            return cls._resolve_canonical_wechat_url(session=session, url=redirect_url)
        return raw_url

    @classmethod
    def _resolve_canonical_wechat_url(cls, *, session, url):
        candidate_url = str(url or "").strip()
        if not candidate_url:
            return ""

        stable_candidate_url = cls._normalize_stable_wechat_article_url(candidate_url)
        if stable_candidate_url:
            return stable_candidate_url

        try:
            response = session.get(
                candidate_url,
                headers=cls._build_wechat_headers(),
                timeout=cls.REQUEST_TIMEOUT_SECONDS,
                allow_redirects=True,
            )
        except Exception:
            return candidate_url

        html = cls._decode_html_body(response.content, response.headers)
        canonical_url = cls._extract_canonical_wechat_url_from_html(
            html=html,
            fallback_url=response.url or candidate_url,
        )
        stable_canonical_url = cls._normalize_stable_wechat_article_url(canonical_url)
        if stable_canonical_url:
            return stable_canonical_url

        response_url = str(response.url or "").strip()
        if cls._looks_like_captcha_wechat_url(response_url):
            return candidate_url
        if cls._looks_like_wechat_article_url(response_url):
            return response_url
        return candidate_url

    @classmethod
    def _extract_redirect_url_from_html(cls, html):
        text = str(html or "")

        meta_match = re.search(
            r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\']\d+;\s*url=([^"\']+)["\'][^>]*>',
            text,
            flags=re.IGNORECASE,
        )
        if meta_match:
            return meta_match.group(1)

        for pattern in (
            r'location\.href\s*=\s*["\']([^"\']+)["\']',
            r'location\s*=\s*["\']([^"\']+)["\']',
            r'window\.location\s*=\s*["\']([^"\']+)["\']',
        ):
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1)

        url_parts = re.findall(r"url\s*\+=\s*'([^']*)'", text)
        url_parts += re.findall(r'url\s*\+=\s*"([^"]*)"', text)
        if url_parts:
            joined = "".join(url_parts)
            if "mp.weixin.qq.com" in joined:
                return joined

        return ""

    @classmethod
    def _extract_canonical_wechat_url_from_html(cls, *, html, fallback_url):
        text = str(html or "")
        script_text = "\n".join(
            script.get_text(" ", strip=False)
            for script in BeautifulSoup(text, "html.parser").find_all("script")
        )

        biz = cls._extract_script_value(
            script_text,
            (
                r'window\.__biz\s*=\s*"([^"]+)"',
                r'window\.biz\s*=\s*"([^"]+)"',
                r'var\s+biz\s*=\s*"([^"]+)"',
            ),
        )
        mid = cls._extract_script_value(
            script_text,
            (
                r'window\.mid\s*=\s*"?(?P<value>\d+)"?',
                r'var\s+mid\s*=\s*"?(?P<value>\d+)"?',
            ),
        )
        idx = cls._extract_script_value(
            script_text,
            (
                r'window\.idx\s*=\s*"?(?P<value>\d+)"?',
                r'var\s+idx\s*=\s*"?(?P<value>\d+)"?',
            ),
        )
        sn = cls._extract_script_value(
            script_text,
            (
                r'window\.sn\s*=\s*"([^"]+)"',
                r'var\s+sn\s*=\s*"([^"]+)"',
            ),
        )

        if biz and mid and idx and sn:
            canonical_url = "https://mp.weixin.qq.com/s?" + urlencode(
                {
                    "__biz": biz,
                    "mid": mid,
                    "idx": idx,
                    "sn": sn,
                }
            )
            return canonical_url

        return fallback_url

    @staticmethod
    def _is_antispider_page(*, url, html):
        normalized_url = str(url or "").lower()
        normalized_html = str(html or "").lower()
        if "antispider" in normalized_url:
            return True
        anti_markers = (
            'id="seccodeform"',
            "验证码",
            "解封失败",
            "向右滑动完成验证",
            "static/js/antispider.min.js",
        )
        return any(marker.lower() in normalized_html for marker in anti_markers)

    @staticmethod
    def _normalize_stable_wechat_article_url(url):
        raw_url = str(url or "").strip()
        if not raw_url:
            return ""
        parsed = urlparse(raw_url)
        if parsed.netloc != "mp.weixin.qq.com" or parsed.path != "/s":
            return ""
        query_values = dict(parse_qsl(parsed.query, keep_blank_values=False))
        if not (query_values.get("__biz") and query_values.get("mid") and query_values.get("idx")):
            return ""
        return normalize_wechat_article_url(raw_url) or raw_url

    @staticmethod
    def _looks_like_wechat_article_url(url):
        parsed = urlparse(str(url or "").strip())
        return parsed.netloc == "mp.weixin.qq.com" and parsed.path == "/s"

    @staticmethod
    def _looks_like_captcha_wechat_url(url):
        parsed = urlparse(str(url or "").strip())
        return parsed.netloc == "mp.weixin.qq.com" and "wappoc_appmsgcaptcha" in parsed.path

    @staticmethod
    def _extract_script_value(script_text, patterns):
        for pattern in patterns:
            match = re.search(pattern, script_text)
            if match:
                if "value" in match.groupdict():
                    return match.group("value")
                return match.group(1)
        return ""

    @classmethod
    def _extract_published_at(cls, source_box):
        for script in source_box.select(".s2 script"):
            script_text = script.get_text(" ", strip=False)
            timestamp_match = re.search(r"(\d{10})", script_text)
            if not timestamp_match:
                continue
            return datetime.fromtimestamp(
                int(timestamp_match.group(1)),
                tz=SOGOU_SEARCH_TIMEZONE,
            )
        return None

    @classmethod
    def _extract_time_text(cls, source_box):
        time_node = source_box.select_one(".s2")
        if time_node is None:
            return ""
        for script in time_node.select("script"):
            script.extract()
        return cls._clean_text(time_node)

    @classmethod
    def _parse_relative_time(cls, raw_text):
        text = str(raw_text or "").strip()
        if not text:
            return None

        now = datetime.now(tz=SOGOU_SEARCH_TIMEZONE)
        relative_patterns = (
            (RELATIVE_DAY_PATTERN, lambda value: now - timedelta(days=int(value))),
            (RELATIVE_HOUR_PATTERN, lambda value: now - timedelta(hours=int(value))),
            (RELATIVE_MINUTE_PATTERN, lambda value: now - timedelta(minutes=int(value))),
        )
        for pattern, builder in relative_patterns:
            match = re.fullmatch(pattern, text)
            if match:
                return builder(match.group(1))

        if text == TEXT_JUST_NOW:
            return now
        if text == TEXT_TODAY:
            return now
        if text == TEXT_YESTERDAY:
            return now - timedelta(days=1)

        for fmt in ("%Y-%m-%d", DISPLAY_DATE_FORMAT):
            try:
                parsed = datetime.strptime(text, fmt)
            except ValueError:
                continue
            return parsed.replace(tzinfo=SOGOU_SEARCH_TIMEZONE)

        try:
            parsed = datetime.strptime(text, "%m\u6708%d\u65e5")
        except ValueError:
            return None

        parsed = parsed.replace(year=now.year)
        aware = parsed.replace(tzinfo=SOGOU_SEARCH_TIMEZONE)
        if aware > now:
            aware = aware.replace(year=aware.year - 1)
        return aware

    @classmethod
    def _describe_relative_time(cls, published_at):
        now = datetime.now(tz=SOGOU_SEARCH_TIMEZONE)
        delta = now - published_at
        if delta.days > 0:
            return f"{delta.days}\u5929\u524d"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}\u5c0f\u65f6\u524d"
        minutes = delta.seconds // 60
        if minutes > 0:
            return f"{minutes}\u5206\u949f\u524d"
        return TEXT_JUST_NOW

    @staticmethod
    def _clean_text(node):
        if node is None:
            return ""
        return " ".join(node.get_text(" ", strip=True).split())

    @staticmethod
    def _extract_charset_from_content_type(content_type):
        match = re.search(
            r'charset\s*=\s*["\']?([a-zA-Z0-9._-]+)',
            str(content_type or ""),
            flags=re.IGNORECASE,
        )
        return match.group(1).lower() if match else ""

    @staticmethod
    def _extract_charset_from_html(buffer):
        probe = buffer[:4096].decode("ascii", errors="ignore")
        meta_charset_match = re.search(
            r"<meta[^>]+charset=[\"']?\s*([a-zA-Z0-9._-]+)",
            probe,
            flags=re.IGNORECASE,
        )
        if meta_charset_match:
            return meta_charset_match.group(1).lower()

        meta_content_match = re.search(
            r"<meta[^>]+content=[\"'][^\"']*charset\s*=\s*([a-zA-Z0-9._-]+)[^\"']*[\"']",
            probe,
            flags=re.IGNORECASE,
        )
        return meta_content_match.group(1).lower() if meta_content_match else ""

    @staticmethod
    def _normalize_charset(charset):
        normalized = str(charset or "").strip().lower()
        if normalized in {"gbk", "gb2312", "gb_2312-80"}:
            return "gb18030"
        if normalized == "utf8":
            return "utf-8"
        return normalized

    @staticmethod
    def _count_replacement_chars(text):
        return str(text or "").count("\ufffd")

    @staticmethod
    def _parse_numeric_entity(raw_value):
        normalized = str(raw_value or "").strip().lower()
        if not normalized:
            return None
        base = 16 if normalized.startswith("x") else 10
        try:
            return int(normalized[1:] if base == 16 else normalized, base)
        except ValueError:
            return None

    @classmethod
    def _restore_broken_surrogate_pair_entities(cls, html):
        def replace(match):
            high = cls._parse_numeric_entity(match.group(1))
            low = cls._parse_numeric_entity(match.group(2))
            if high is None or low is None:
                return match.group(0)
            if not (0xD800 <= high <= 0xDBFF and 0xDC00 <= low <= 0xDFFF):
                return match.group(0)
            code_point = ((high - 0xD800) << 10) + (low - 0xDC00) + 0x10000
            return chr(code_point)

        return re.sub(
            r"&#(x?[0-9a-fA-F]+);&#(x?[0-9a-fA-F]+);",
            replace,
            str(html or ""),
        )

    @classmethod
    def _decode_html_body(cls, buffer, headers):
        content_type = headers.get("Content-Type") or headers.get("content-type")
        content_type_charset = cls._normalize_charset(
            cls._extract_charset_from_content_type(content_type)
        )
        html_charset = cls._normalize_charset(cls._extract_charset_from_html(buffer))

        candidate_charsets = []
        for charset in (content_type_charset, html_charset, "utf-8", "gb18030"):
            if charset and charset not in candidate_charsets:
                candidate_charsets.append(charset)

        best_text = buffer.decode("utf-8", errors="replace")
        best_score = cls._count_replacement_chars(best_text)

        for charset in candidate_charsets:
            try:
                decoded = buffer.decode(charset, errors="replace")
            except LookupError:
                continue
            score = cls._count_replacement_chars(decoded)
            if score < best_score:
                best_text = decoded
                best_score = score
            if score == 0 and charset in {content_type_charset, html_charset}:
                return cls._restore_broken_surrogate_pair_entities(decoded)

        return cls._restore_broken_surrogate_pair_entities(best_text)
