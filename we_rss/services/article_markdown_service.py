import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from we_rss.services.wechat_gateway import (
    build_wechat_session,
    normalize_wechat_article_url,
    parse_wechat_article_html,
)

try:
    import html2text
except ImportError:  # pragma: no cover - exercised in runtime environments missing the package
    html2text = None


IMAGE_MARKDOWN_PATTERN = re.compile(r"!\[[^\]]*]\([^)]*\)")


def _extract_author(soup):
    for selector in ("#js_author_name", ".rich_media_meta.rich_media_meta_text#js_author_name"):
        node = soup.select_one(selector)
        if node:
            author = node.get_text(strip=True)
            if author:
                return author
    return ""


def _format_publish_date(payload):
    publish_time = payload.get("publish_time")
    if publish_time is None:
        return ""
    return publish_time.strftime("%Y-%m-%d")


def _normalize_markdown_line(line):
    normalized = re.sub(r"^[#>*\-\s`._]+", "", str(line or "").strip())
    return normalized.replace(" ", "")


def _is_markdown_separator_line(line):
    compact = str(line or "").strip().replace(" ", "")
    return compact in {"---", "***", "___"}


def _strip_wechat_footer_sections(markdown):
    text = str(markdown or "").strip()
    if not text:
        return text

    lines = text.splitlines()
    search_start = len(lines) // 2
    cutoff = None
    footer_markers = (
        "\u5386\u53f2\u76d8\u70b9",
        "\u63a8\u8350\u9605\u8bfb",
    )

    for index in range(search_start, len(lines)):
        normalized = _normalize_markdown_line(lines[index])
        if any(normalized.startswith(marker) for marker in footer_markers):
            cutoff = index
            break

    if cutoff is None:
        return text

    kept_lines = lines[:cutoff]
    while kept_lines and (not kept_lines[-1].strip() or _is_markdown_separator_line(kept_lines[-1])):
        kept_lines.pop()
    return "\n".join(kept_lines).strip()


def _strip_yaml_front_matter(markdown):
    text = str(markdown or "").strip()
    if not text.startswith("---"):
        return text

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1 :]).strip()
    return text


def _strip_markdown_images(markdown):
    text = IMAGE_MARKDOWN_PATTERN.sub("", str(markdown or ""))
    lines = [line.rstrip() for line in text.splitlines()]
    compacted = []
    blank_seen = False
    for line in lines:
        if not line.strip():
            if not blank_seen:
                compacted.append("")
            blank_seen = True
            continue
        compacted.append(line)
        blank_seen = False
    return "\n".join(compacted).strip()


def _html_to_markdown(html):
    if html2text is None:
        raise RuntimeError("html2text is required to convert articles to Markdown.")

    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0
    return converter.handle(html or "").strip()


def _html_to_markdown_with_images(html):
    """与 _html_to_markdown 一致，但保留 <img> 为 ![](url)。"""
    if html2text is None:
        raise RuntimeError("html2text is required to convert articles to Markdown.")

    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.body_width = 0
    return converter.handle(html or "").strip()


class ArticleMarkdownService:
    def __init__(self, *, session_factory=None, timeout=120):
        self.session_factory = session_factory or requests.Session
        self.timeout = timeout

    def _is_wechat_article_url(self, url):
        return urlparse(url or "").netloc.lower() == "mp.weixin.qq.com"

    def _build_regular_session(self):
        return self.session_factory()

    def _fetch_response(self, url, *, use_wechat_session):
        session = build_wechat_session(self.session_factory) if use_wechat_session else self._build_regular_session()
        response = session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _fetch_wechat_markdown(self, url):
        normalized_url = normalize_wechat_article_url(url) or str(url or "").strip()
        response = self._fetch_response(normalized_url, use_wechat_session=True)
        return self.convert_wechat_html_to_markdown(
            html=response.text,
            url=response.url or normalized_url,
        )

    def _fetch_regular_markdown(self, url):
        response = self._fetch_response(url, use_wechat_session=False)
        body = _strip_yaml_front_matter(_html_to_markdown(response.text))
        body = _strip_markdown_images(body)
        if not body:
            raise ValueError("Article markdown content is empty.")
        return body

    def convert_wechat_html_to_markdown(self, *, html, url):
        normalized_url = normalize_wechat_article_url(url) or str(url or "").strip()
        payload = parse_wechat_article_html(html, normalized_url)
        content_html = str(payload.get("content") or "").strip()
        if payload.get("status") == "deleted" or content_html == "DELETED":
            raise ValueError("Wechat article is unavailable or has been deleted.")
        if not content_html:
            raise ValueError("Wechat article content is empty.")

        soup = BeautifulSoup(html or "", "html.parser")
        author = _extract_author(soup)
        markdown_body = _strip_wechat_footer_sections(_html_to_markdown(content_html))
        markdown_body = _strip_markdown_images(markdown_body)
        if not markdown_body:
            raise ValueError("Wechat article markdown content is empty.")

        meta_lines = []
        mp_name = str(payload.get("mp_name") or "").strip()
        publish_date = _format_publish_date(payload)
        if mp_name:
            meta_lines.append(f"> 公众号: {mp_name}")
        if author:
            meta_lines.append(f"> 作者: {author}")
        if publish_date:
            meta_lines.append(f"> 日期: {publish_date}")

        sections = [f"# {payload.get('title') or 'Untitled'}"]
        if meta_lines:
            sections.append("\n".join(meta_lines))
            sections.append("---")
        sections.append(markdown_body)
        return "\n\n".join(section for section in sections if section).strip()

    def convert_wechat_html_to_markdown_with_images(self, *, html, url):
        """
        与 convert_wechat_html_to_markdown 一致，但保留正文内联图片。

        微信 <img> 真实地址在 data-src（src 多为占位图），html2text 只读 src，
        故先把每个 <img> 的 src 指向 data-src，再用 ignore_images=False 转换，
        得到 ![](mmbiz_url) 形式的图片引用，供前端本地化。不落库。
        """
        normalized_url = normalize_wechat_article_url(url) or str(url or "").strip()
        payload = parse_wechat_article_html(html, normalized_url)
        content_html = str(payload.get("content") or "").strip()
        if payload.get("status") == "deleted" or content_html == "DELETED":
            raise ValueError("Wechat article is unavailable or has been deleted.")
        if not content_html:
            raise ValueError("Wechat article content is empty.")

        soup = BeautifulSoup(content_html, "html.parser")
        for img in soup.find_all("img"):
            real = (img.get("data-src") or img.get("src") or "").strip()
            if real.startswith("//"):
                real = "https:" + real
            if real:
                img["src"] = real

        author = _extract_author(BeautifulSoup(html or "", "html.parser"))
        markdown_body = _strip_wechat_footer_sections(_html_to_markdown_with_images(str(soup)))
        if not markdown_body:
            raise ValueError("Wechat article markdown content is empty.")

        meta_lines = []
        mp_name = str(payload.get("mp_name") or "").strip()
        publish_date = _format_publish_date(payload)
        if mp_name:
            meta_lines.append(f"> 公众号: {mp_name}")
        if author:
            meta_lines.append(f"> 作者: {author}")
        if publish_date:
            meta_lines.append(f"> 日期: {publish_date}")

        sections = [f"# {payload.get('title') or 'Untitled'}"]
        if meta_lines:
            sections.append("\n".join(meta_lines))
            sections.append("---")
        sections.append(markdown_body)
        return "\n\n".join(section for section in sections if section).strip()

    def fetch_markdown_with_images_from_url(self, url):
        """现抓文章原文并转为保留内联图片的 Markdown（不落库）。"""
        raw_url = str(url or "").strip()
        if not raw_url:
            raise ValueError("Article URL is required.")

        if self._is_wechat_article_url(raw_url):
            normalized_url = normalize_wechat_article_url(raw_url) or raw_url
            response = self._fetch_response(normalized_url, use_wechat_session=True)
            return self.convert_wechat_html_to_markdown_with_images(
                html=response.text,
                url=response.url or normalized_url,
            )

        response = self._fetch_response(raw_url, use_wechat_session=False)
        body = _strip_yaml_front_matter(_html_to_markdown_with_images(response.text))
        if not body:
            raise ValueError("Article markdown content is empty.")
        return body

    def fetch_markdown_from_url(self, url):
        raw_url = str(url or "").strip()
        if not raw_url:
            raise ValueError("Article URL is required.")

        if self._is_wechat_article_url(raw_url):
            return self._fetch_wechat_markdown(raw_url)

        return self._fetch_regular_markdown(raw_url)


def fetch_article_markdown_from_url(url):
    return ArticleMarkdownService().fetch_markdown_from_url(url)


def fetch_article_markdown_with_images_from_url(url):
    """现抓文章原文并转为保留内联图片的 Markdown（不落库）。"""
    return ArticleMarkdownService().fetch_markdown_with_images_from_url(url)
