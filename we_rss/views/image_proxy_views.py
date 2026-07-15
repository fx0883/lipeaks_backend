"""
微信公众号图片代理下载视图。

前端受微信图床 mmbiz.qpic.cn 的 CORS 限制无法直接 fetch 图片，
由本接口代理下载后流式返回二进制。

GET /api/v1/we-rss/image-proxy/?url={encodeURIComponent(图片URL)}

鉴权与现有 we-rss 接口一致：前端携带 ``Authorization: Bearer <token>``，
全局 ``APIAuthMiddleware`` 解析 JWT 并设置 ``request.user``；``/api/v1/we-rss/``
在租户隔离路径列表内，``TenantMiddleware`` 校验 ``X-Tenant-ID``。
本视图只额外校验登录态（无 token -> 401），不触碰租户数据，无需 DRF 内容协商
（前端发 ``Accept: image/*``，DRF 默认渲染器不匹配会 406，故用纯 Django 视图）。
"""
import logging

from django.http import JsonResponse, StreamingHttpResponse
from rest_framework import status

from we_rss.services.image_proxy_service import (
    ImageFetchError,
    fetch_image,
    get_image_proxy_config,
    resolve_content_type,
    validate_proxy_url,
    URLValidationError,
)

logger = logging.getLogger(__name__)


def _json_error(message, http_status, business_code):
    """构造标准错误响应 {success, code, message, data}，HTTP 状态码保持不变。"""
    return JsonResponse(
        {
            "success": False,
            "code": business_code,
            "message": message,
            "data": None,
        },
        status=http_status,
        json_dumps_params={"ensure_ascii": False},
    )


def image_proxy(request):
    """
    微信公众号图片代理下载。

    - 200：body 为图片二进制，Content-Type 透传源图 MIME，附带缓存头
    - 400：url 缺失 / 非 http(s) / 非白名单域名 / 内网地址
    - 401：未认证（无有效 Bearer token）
    - 502：源图下载失败（超时 / 404 / 重定向越界等）
    """
    # 鉴权：复用全局中间件解析的 JWT 用户；未认证直接 401。
    if not getattr(request.user, "is_authenticated", False):
        return _json_error("认证失败，请登录", status.HTTP_401_UNAUTHORIZED, 4001)

    config = get_image_proxy_config()
    raw_url = request.GET.get("url", "").strip()

    try:
        url, _parsed, _host = validate_proxy_url(raw_url, config["ALLOWED_HOSTS"])
    except URLValidationError as exc:
        logger.info("图片代理 URL 校验失败: %s", exc)
        return _json_error(str(exc), status.HTTP_400_BAD_REQUEST, 4000)

    try:
        upstream = fetch_image(
            url,
            allowed_hosts=config["ALLOWED_HOSTS"],
            user_agent=config["USER_AGENT"],
            timeout=config["TIMEOUT"],
            referer=config.get("REFERER", ""),
            max_redirects=config.get("MAX_REDIRECTS", 3),
        )
    except ImageFetchError as exc:
        logger.warning("图片代理下载失败 url=%s: %s", url, exc)
        return _json_error(str(exc), status.HTTP_502_BAD_GATEWAY, 5000)

    # 超大文件保护（基于上游声明的 Content-Length）
    max_size = config.get("MAX_CONTENT_LENGTH")
    if max_size:
        declared = upstream.headers.get("Content-Length")
        if declared and declared.isdigit() and int(declared) > max_size:
            upstream.close()
            logger.warning("图片代理源图过大 url=%s declared=%s", url, declared)
            return _json_error("upstream image too large", status.HTTP_502_BAD_GATEWAY, 5000)

    content_type = resolve_content_type(url, upstream.headers.get("Content-Type"))
    chunk_size = config.get("CHUNK_SIZE", 8192)

    response = StreamingHttpResponse(_iter_image(upstream, chunk_size), content_type=content_type)
    response["Cache-Control"] = f"public, max-age={config.get('CACHE_MAX_AGE', 86400)}"
    return response


def _iter_image(upstream, chunk_size):
    """逐块产出图片字节，结束后关闭上游连接，避免连接泄漏。"""
    try:
        for chunk in upstream.iter_content(chunk_size=chunk_size):
            if chunk:
                yield chunk
    finally:
        upstream.close()
