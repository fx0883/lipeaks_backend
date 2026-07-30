"""
微信公众号图片代理服务：SSRF 校验 + 流式下载 + Content-Type 解析。

微信图床 mmbiz.qpic.cn 受浏览器 CORS 限制无法直连，由后端带 UA/Referer
取图并流式透传二进制。下载逻辑等价于 wechat-article-fetcher skill 的
downloader.py，这里用 requests 流式转发，并对重定向目标重新做白名单 +
内网校验，避免被利用为内网探测跳板（SSRF）。
"""
import ipaddress
import logging
import os
import socket
from urllib.parse import parse_qs, urlparse, urljoin

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# wx_fmt / tp 参数（或路径扩展名）-> MIME 映射
_FORMAT_TO_MIME = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "svg": "image/svg+xml",
}

# 需要手动跟随的重定向状态码（关闭自动跟随以校验目标，防止跳内网）
_REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class URLValidationError(ValueError):
    """图片代理 URL 校验失败，message 可直接作为 400 响应信息。"""


class ImageFetchError(Exception):
    """图片下载失败：网络异常 / 上游错误状态码 / 重定向越界 / 目标非法。"""


def validate_proxy_url(url, allowed_hosts):
    """
    校验待代理的图片 URL。

    - 协议必须为 http / https
    - 域名必须在白名单内（精确或子域后缀匹配）
    - 解析后的 IP 不能是内网 / 回环 / 链路本地等私有地址

    Returns:
        tuple(normalized_url, parsed, host)

    Raises:
        URLValidationError: 校验失败。
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("missing url")

    url = url.strip()
    if not url:
        raise URLValidationError("missing url")

    # 兼容 //mmbiz.qpic.cn/... 协议相对 URL
    if url.startswith("//"):
        url = "https:" + url

    try:
        parsed = urlparse(url)
    except Exception as exc:  # noqa: BLE001 - urlparse 极少抛错，统一转校验失败
        raise URLValidationError("invalid url") from exc

    if parsed.scheme not in ("http", "https"):
        raise URLValidationError("url scheme must be http or https")

    host = (parsed.hostname or "").lower()
    if not host:
        raise URLValidationError("invalid url host")

    if not _host_allowed(host, allowed_hosts):
        raise URLValidationError("url host not allowed")

    _ensure_not_private(host)

    return url, parsed, host


def _host_allowed(host, allowed_hosts):
    """精确匹配或子域后缀匹配白名单域名。"""
    for allowed in allowed_hosts or []:
        normalized = allowed.lower().lstrip(".")
        if not normalized:
            continue
        if host == normalized or host.endswith("." + normalized):
            return True
    return False


def _ensure_not_private(host):
    """
    阻止内网 / 回环 / 链路本地等私有地址。

    - host 为 IP 字面量时直接判断；
    - host 为域名时解析后逐个判断（DNS rebinding 防护）。
      DNS 解析失败视为非致命（白名单已是主防线），交由下载环节处理。
    """
    literal = _try_parse_ip(host)
    if literal is not None:
        if _is_private_ip(literal):
            raise URLValidationError("internal host not allowed")
        return

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        logger.debug("host %s DNS 解析失败，跳过内网检查（白名单已校验）", host)
        return

    for info in infos:
        ip = _try_parse_ip(info[4][0])
        if ip is not None and _is_private_ip(ip):
            raise URLValidationError("internal host not allowed")


def _try_parse_ip(value):
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def _is_private_ip(ip):
    """是否为内网 / 回环 / 链路本地 / 保留 / 组播 / 未指定地址。"""
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def fetch_image(url, *, allowed_hosts, user_agent, timeout, referer="", max_redirects=3):
    """
    以流式方式下载图片，返回已打开的 ``requests.Response``（stream=True）。

    调用方需消费 ``iter_content`` 并在结束后 ``close``。
    重定向目标会重新走 :func:`validate_proxy_url`，避免跳转到内网或非白名单域名。

    Raises:
        ImageFetchError: 任何下载 / 状态码 / 重定向异常。
    """
    headers = {"User-Agent": user_agent}
    if referer:
        headers["Referer"] = referer

    current = url
    for _ in range(max_redirects + 1):
        try:
            response = requests.get(
                current,
                headers=headers,
                timeout=timeout,
                stream=True,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            logger.warning("图片下载请求失败 url=%s err=%s", current, exc)
            raise ImageFetchError("upstream image fetch failed") from exc

        if response.status_code in _REDIRECT_STATUSES:
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise ImageFetchError("upstream image fetch failed")
            location = urljoin(current, location)
            try:
                current, _parsed, _host = validate_proxy_url(location, allowed_hosts)
            except URLValidationError:
                raise ImageFetchError("upstream image fetch failed")
            continue

        if response.status_code >= 400:
            response.close()
            logger.warning("图片下载上游状态码异常 url=%s status=%s", current, response.status_code)
            raise ImageFetchError("upstream image fetch failed")

        return response

    raise ImageFetchError("upstream image fetch failed")


def resolve_content_type(url, upstream_content_type):
    """
    解析返回给客户端的 Content-Type：

    1. 上游返回了真正的 image/* 类型 -> 透传（去除 charset 等参数）
    2. 否则按 URL 的 wx_fmt / tp 参数推断
    3. 再按路径扩展名推断
    4. 兜底 image/jpeg
    """
    if upstream_content_type:
        ct = upstream_content_type.split(";")[0].strip().lower()
        if ct.startswith("image/"):
            return ct

    try:
        parsed = urlparse(url)
    except Exception:  # noqa: BLE001
        return "image/jpeg"

    query = parse_qs(parsed.query)
    for key in ("wx_fmt", "tp"):
        values = query.get(key)
        if values:
            mime = _FORMAT_TO_MIME.get(values[0].lower())
            if mime:
                return mime

    ext = os.path.splitext(parsed.path)[1].lower().lstrip(".")
    mime = _FORMAT_TO_MIME.get(ext)
    if mime:
        return mime

    return "image/jpeg"


# 与 wechat-article-fetcher skill 的 downloader.py 一致的桌面浏览器 UA
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_REFERER = "https://mp.weixin.qq.com/"

_CONFIG_DEFAULTS = {
    "ALLOWED_HOSTS": ["mmbiz.qpic.cn", "mmbiz.qlogo.cn"],
    "USER_AGENT": DEFAULT_USER_AGENT,
    "REFERER": DEFAULT_REFERER,
    "TIMEOUT": 15,
    "CACHE_MAX_AGE": 86400,
    "MAX_CONTENT_LENGTH": 25 * 1024 * 1024,
    "MAX_REDIRECTS": 3,
    "CHUNK_SIZE": 8192,
}


def get_image_proxy_config():
    """返回合并后的图片代理配置（settings.WE_RSS_IMAGE_PROXY 覆盖默认值）。"""
    overrides = getattr(settings, "WE_RSS_IMAGE_PROXY", None) or {}
    merged = {
        key: list(value) if isinstance(value, list) else value
        for key, value in _CONFIG_DEFAULTS.items()
    }
    for key, value in overrides.items():
        merged[key] = list(value) if isinstance(value, list) else value
    if not merged.get("ALLOWED_HOSTS"):
        merged["ALLOWED_HOSTS"] = list(_CONFIG_DEFAULTS["ALLOWED_HOSTS"])
    return merged
