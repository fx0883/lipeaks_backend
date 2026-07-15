"""
按文章 url 现抓正文（保留内联图）+ 下载图片，流式打包成 ZIP。不落库。

用 stdlib zlib/struct 实现顺序流式 ZIP writer：每个 entry 的数据在写入前已
完整就绪（正文 string / 图片 bytes），故 CRC 与压缩后大小已知，可直接写 local
header，无需 seek；所有 entry 写完后追加中央目录。内存占用 ≈ 单个 entry 大小。

前端用单请求下载该流式响应，避免 100 篇文章产生数百个往返请求。
"""
import hashlib
import re
import struct
import time
import zlib
from concurrent.futures import ThreadPoolExecutor

from we_rss.services.article_markdown_service import fetch_article_markdown_with_images_from_url
from we_rss.services.image_proxy_service import (
    ImageFetchError,
    URLValidationError,
    fetch_image,
    get_image_proxy_config,
    resolve_content_type,
    validate_proxy_url,
)

_MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_HTML_IMAGE_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)

_MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/bmp": "bmp",
    "image/svg+xml": "svg",
}


def sanitize_filename(name):
    safe = re.sub(r"[\\/:*?\"<>|\r\n\t]+", "_", str(name or "").strip())
    safe = safe.strip().strip(".") or "article"
    return safe[:80]


def _normalize_url(raw):
    url = (raw or "").strip()
    if not url:
        return None
    if url.startswith("//"):
        url = "https:" + url
    if not re.match(r"^https?://", url, re.IGNORECASE):
        return None
    return url


def _extract_img_url_from_tag(tag):
    m = re.search(r"data-src\s*=\s*[\"']([^\"']+)[\"']", tag, re.IGNORECASE)
    if m and m.group(1).strip():
        return m.group(1).strip()
    m = re.search(r"\bsrc\s*=\s*[\"']([^\"']+)[\"']", tag, re.IGNORECASE)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return None


def _extract_image_urls(markdown):
    found = []
    seen = set()
    for m in _MARKDOWN_IMAGE_RE.finditer(markdown or ""):
        url = _normalize_url(m.group(2))
        if url and url not in seen:
            seen.add(url)
            found.append(url)
    for m in _HTML_IMAGE_RE.finditer(markdown or ""):
        raw = _extract_img_url_from_tag(m.group(0))
        if raw:
            url = _normalize_url(raw)
            if url and url not in seen:
                seen.add(url)
                found.append(url)
    return found


def _localize_markdown_images(markdown, url_to_path):
    if not url_to_path:
        return markdown or ""

    def repl_md(m):
        url = _normalize_url(m.group(2))
        local = url_to_path.get(url) if url else None
        return f"![{m.group(1)}]({local})" if local else m.group(0)

    text = _MARKDOWN_IMAGE_RE.sub(repl_md, markdown or "")

    def repl_html(m):
        tag = m.group(0)
        raw = _extract_img_url_from_tag(tag)
        if not raw:
            return tag
        url = _normalize_url(raw)
        local = url_to_path.get(url) if url else None
        return tag.replace(raw, local) if local else tag

    return _HTML_IMAGE_RE.sub(repl_html, text)


def _ext_for(url, content_type):
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct in _MIME_TO_EXT:
        return _MIME_TO_EXT[ct]
    m = re.search(r"[?&](?:wx_fmt|tp)=([a-z0-9]+)", url or "", re.IGNORECASE)
    if m:
        ext = m.group(1).lower()
        return "jpg" if ext == "jpeg" else ext
    m = re.search(r"\.([a-z0-9]{2,4})$", (url or "").split("?")[0], re.IGNORECASE)
    if m:
        ext = m.group(1).lower()
        return "jpg" if ext == "jpeg" else ext
    return "jpg"


def _hash_name(url):
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:16]


def _fetch_one_image(url, allowed_hosts, config):
    """下载单张图片，返回 (url, valid_url, data, ext) 或 None。供线程池并发调用。"""
    try:
        valid_url, _parsed, _host = validate_proxy_url(url, allowed_hosts)
    except URLValidationError:
        return None
    try:
        resp = fetch_image(
            valid_url,
            allowed_hosts=allowed_hosts,
            user_agent=config["USER_AGENT"],
            timeout=config["TIMEOUT"],
            referer=config.get("REFERER", ""),
            max_redirects=config.get("MAX_REDIRECTS", 3),
        )
    except ImageFetchError:
        return None
    try:
        content_type = resolve_content_type(valid_url, resp.headers.get("Content-Type"))
        data = resp.content
    finally:
        resp.close()
    if not data:
        return None
    return (url, valid_url, data, _ext_for(valid_url, content_type))


def _fetch_images_concurrent(urls, allowed_hosts, config):
    """并发下载一批图片（保持输入顺序），单张失败返回 None 并被过滤。"""
    if not urls:
        return []
    worker_count = min(6, len(urls))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        results = list(
            pool.map(lambda u: _fetch_one_image(u, allowed_hosts, config), urls)
        )
    return [r for r in results if r]


# --------------------------------------------------------------------------
# 顺序流式 ZIP writer（无第三方依赖）
# --------------------------------------------------------------------------

_LOCAL_SIG = b"PK\x03\x04"
_CENTRAL_SIG = b"PK\x01\x02"
_END_SIG = b"PK\x05\x06"


def _dos_datetime(epoch):
    t = time.localtime(epoch)
    dos_time = (t.tm_hour << 11) | (t.tm_min << 5) | (t.tm_sec // 2)
    dos_date = ((t.tm_year - 1980) << 9) | (t.tm_mon << 5) | t.tm_mday
    return dos_time, dos_date


class StreamingZipWriter:
    """顺序写入 entry 的流式 ZIP writer。调用 add_entry 得到该 entry 的字节，
    全部写完后调用 finish 得到中央目录与结尾记录。"""

    def __init__(self, compress=True):
        self._compress = compress
        self._entries = []
        self._offset = 0

    @staticmethod
    def _deflate(data):
        co = zlib.compressobj(9, zlib.DEFLATED, -15)
        return co.compress(data) + co.flush()

    def add_entry(self, name, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        crc = zlib.crc32(data) & 0xFFFFFFFF
        if self._compress:
            payload = self._deflate(data)
            method = 8
        else:
            payload = data
            method = 0
        name_bytes = name.encode("utf-8")
        dos_time, dos_date = _dos_datetime(time.time())
        # bit 11 (0x0800) = 文件名按 UTF-8 编码，否则解压工具按 CP437 解码中文会乱码
        header = struct.pack(
            "<4s5H3L2H",
            _LOCAL_SIG, 20, 0x0800, method, dos_time, dos_date,
            crc, len(payload), len(data), len(name_bytes), 0,
        )
        chunk = header + name_bytes + payload
        self._entries.append(
            (name_bytes, method, dos_time, dos_date, crc, len(payload), len(data), self._offset)
        )
        self._offset += len(chunk)
        return chunk

    def finish(self):
        parts = []
        cd_start = self._offset
        for (name_bytes, method, dos_time, dos_date, crc,
             comp_size, uncomp_size, offset) in self._entries:
            rec = struct.pack(
                "<4s6H3L5H2L",
                _CENTRAL_SIG, 20, 20, 0x0800, method, dos_time, dos_date,
                crc, comp_size, uncomp_size,
                len(name_bytes), 0, 0, 0, 0, 0, offset,
            )
            parts.append(rec + name_bytes)
        central = b"".join(parts)
        end = struct.pack(
            "<4s4H2LH",
            _END_SIG, 0, 0, len(self._entries), len(self._entries),
            len(central), cd_start, 0,
        )
        return central + end


def _unique_folder(base, used):
    if base not in used:
        return base
    index = 1
    while f"{base}-{index}" in used:
        index += 1
    return f"{base}-{index}"


def stream_articles_markdown_with_images_zip(articles, *, config=None):
    """
    生成器：按文章顺序现抓正文+图片，逐 entry 产出 ZIP 字节。

    - 单篇正文抓取失败：写一个占位 index.md（注明失败），不阻断。
    - 单张图片失败/非白名单：跳过，index.md 保留原远程链接。
    - 不落库；内存占用 ≈ 单篇文章 + 单张图片。

    Args:
        articles: 可迭代的 WechatArticle（需 .id .title .url）。
        config: get_image_proxy_config() 结果；为 None 时自动读取。
    """
    if config is None:
        config = get_image_proxy_config()

    writer = StreamingZipWriter(compress=True)
    allowed_hosts = config["ALLOWED_HOSTS"]
    used_folders = set()

    for article in articles:
        title = getattr(article, "title", None) or f"article-{getattr(article, 'id', 'untitled')}"
        folder = _unique_folder(sanitize_filename(title), used_folders)
        used_folders.add(folder)

        try:
            markdown = fetch_article_markdown_with_images_from_url(article.url)
        except Exception as exc:  # noqa: BLE001 - 单篇失败不阻断整体
            yield writer.add_entry(
                f"{folder}/index.md",
                f"# {title}\n\n> 原文获取失败：{exc}\n",
            )
            continue

        url_to_path = {}
        for url, valid_url, data, ext in _fetch_images_concurrent(
            _extract_image_urls(markdown), allowed_hosts, config
        ):
            fname = f"images/{_hash_name(valid_url)}.{ext}"
            url_to_path[url] = fname
            yield writer.add_entry(f"{folder}/{fname}", data)

        localized = _localize_markdown_images(markdown, url_to_path)
        yield writer.add_entry(f"{folder}/index.md", localized)

    yield writer.finish()
