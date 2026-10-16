"""
全局 API Redis 缓存中间件 (APICacheMiddleware)

核心设计目标：
1. 全局透明缓存：无需修改业务视图层代码，在中间件层对安全的读请求（GET/HEAD）自动缓存至 Redis；
2. 多租户与用户四重安全隔离：Key 结构深度融入 tenant_id, user_scope, path, query_params_hash，坚决杜绝越权；
3. 写操作联动清除：当非安全请求（POST/PUT/PATCH/DELETE）成功执行时，自动按路由资源前缀与租户精确失效相关缓存；
4. 客户端主动穿透：支持客户端通过请求头 Cache-Control: no-cache 或 Query 参数 ?nocache=1 主动刷新缓存；
5. 可观测性：在 HTTP 响应头打上 X-Cache: HIT / MISS 标识。
"""

import hashlib
import json
import logging
import re
from typing import Optional
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from common.utils.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class APICacheMiddleware(MiddlewareMixin):
    """
    企业级多租户全局 API 响应缓存中间件
    """

    # 默认缓存时间（秒）
    DEFAULT_TIMEOUT = getattr(settings, 'API_CACHE_DEFAULT_TIMEOUT', 120)

    # 绝对不缓存的敏感/实时路由黑名单前缀
    BLACKLIST_PREFIXES = (
        '/api/v1/auth/',
        '/api/v1/members/password-reset/',
        '/api/v1/members/delete-account/',
        '/api/v1/schema/',
        '/api/v1/docs/',
        '/api/v1/redoc/',
        '/api/v1/health/',
        '/api/v1/feedbacks/health/',
        '/api/v1/licenses/heartbeat/',
        '/api/v1/licenses/verify/',
        '/api/v1/licenses/activate/',
        '/api/v1/licenses/status/',
        '/api/v1/we-rss/images/proxy/',
    )

    def __init__(self, get_response=None):
        if get_response is None:
            get_response = lambda req: HttpResponse()
        super().__init__(get_response)
        self.enabled = getattr(settings, 'API_CACHE_ENABLED', True)
        logger.info(f"APICacheMiddleware 已初始化 (enabled={self.enabled}, default_timeout={self.DEFAULT_TIMEOUT}s)")

    def _should_cache_request(self, request) -> bool:
        """判断当前请求是否满足缓存提取/写入条件"""
        if not getattr(settings, 'API_CACHE_ENABLED', True):
            return False

        # 仅缓存 API 路由
        if not request.path.startswith('/api/'):
            return False

        # 仅缓存安全读方法
        if request.method not in ('GET', 'HEAD'):
            return False

        # 命中黑名单前缀直接跳过
        path = request.path
        for prefix in self.BLACKLIST_PREFIXES:
            if path.startswith(prefix):
                return False

        return True

    def _get_tenant_id(self, request) -> str:
        """安全提取租户 ID，多层级回退保障"""
        # 1. 优先从 ContextVar 获取
        tenant = get_current_tenant()
        if tenant and getattr(tenant, 'id', None):
            return str(tenant.id)

        # 2. 从 request.tenant 获取
        req_tenant = getattr(request, 'tenant', None)
        if req_tenant and getattr(req_tenant, 'id', None):
            return str(req_tenant.id)

        # 3. 从 request.user 获取
        user = getattr(request, 'user', None)
        if user and getattr(user, 'tenant_id', None):
            return str(user.tenant_id)

        # 4. 从 Header 获取
        header_tid = request.META.get('HTTP_X_TENANT_ID')
        if header_tid:
            return str(header_tid).strip()

        # 5. 从 QueryParams 获取
        query_tid = request.GET.get('tenant_id')
        if query_tid:
            return str(query_tid).strip()

        return 'public'

    def _get_user_scope(self, request) -> str:
        """获取用户身份作用域（已登录用户按 UID 严格隔离，未登录共用 anon）"""
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            return f"user_{user.id}"
        return "anon"

    def _build_cache_key(self, request) -> str:
        """构建具备四重安全隔离的缓存 Key"""
        tenant_id = self._get_tenant_id(request)
        user_scope = self._get_user_scope(request)
        normalized_path = request.path.rstrip('/')

        # 对 Query 参数排序并计算 SHA256 哈希，消除参数乱序影响
        query_items = sorted(
            (k, v) for k, v in request.GET.lists() if k.lower() not in ('nocache', 'refresh', '_')
        )
        query_str = json.dumps(query_items, sort_keys=True, separators=(',', ':'))
        query_hash = hashlib.sha256(query_str.encode('utf-8')).hexdigest()[:16]

        return f"api_cache:{tenant_id}:{user_scope}:{normalized_path}:{query_hash}"

    def process_request(self, request):
        """请求阶段：尝试从 Redis 读取缓存并命中返回"""
        if not self._should_cache_request(request):
            return None

        # 检查是否请求强制刷新或跳过缓存
        cache_control = request.META.get('HTTP_CACHE_CONTROL', '')
        pragma = request.META.get('HTTP_PRAGMA', '')
        if (
            'no-cache' in cache_control.lower()
            or 'no-cache' in pragma.lower()
            or request.GET.get('nocache') == '1'
            or request.GET.get('refresh') == '1'
        ):
            request._api_cache_bypass = True
            return None

        cache_key = self._build_cache_key(request)
        request._api_cache_key = cache_key

        try:
            cached_data = cache.get(cache_key)
            if cached_data is not None and isinstance(cached_data, dict):
                response = HttpResponse(
                    content=cached_data.get('content', b''),
                    status=cached_data.get('status', 200),
                    content_type=cached_data.get('content_type', 'application/json'),
                )
                response['X-Cache'] = 'HIT'
                response['X-Cache-Key'] = cache_key
                try:
                    response.data = json.loads(response.content.decode('utf-8'))
                except Exception:
                    pass
                logger.debug(f"[APICache] 命中缓存: {cache_key}")
                return response
        except Exception as e:
            logger.warning(f"[APICache] 读取缓存异常: {e}")

        return None

    def process_response(self, request, response):
        """响应阶段：回写读请求到 Redis，或在写请求时联动失效相关缓存"""
        # 1. 如果是 GET 请求且未被缓存直接返回，尝试将成功响应写入 Redis
        if self._should_cache_request(request):
            # 若已有 X-Cache: HIT，表示这是 process_request 直接返回的命中响应
            if response.get('X-Cache') == 'HIT':
                return response

            cache_key = getattr(request, '_api_cache_key', None) or self._build_cache_key(request)
            response['X-Cache'] = 'MISS'
            response['X-Cache-Key'] = cache_key

            # 只缓存 HTTP 200、非流式传输、且 Content-Type 为 JSON 的安全响应
            content_type = response.get('Content-Type', '')
            if (
                response.status_code == 200
                and not getattr(response, 'streaming', False)
                and 'application/json' in content_type
            ):
                try:
                    payload = {
                        'content': response.content,
                        'status': response.status_code,
                        'content_type': content_type,
                    }
                    timeout = self.DEFAULT_TIMEOUT
                    cache.set(cache_key, payload, timeout)
                    logger.debug(f"[APICache] 写入缓存成功: {cache_key} (TTL={timeout}s)")
                except Exception as e:
                    logger.warning(f"[APICache] 写入缓存失败: {e}")

            return response

        # 2. 如果是写操作（POST / PUT / PATCH / DELETE）且响应成功（2xx），触发联动缓存失效
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            if 200 <= response.status_code < 300 and request.path.startswith('/api/'):
                self._invalidate_related_cache(request)

        return response

    def _extract_resource_prefix(self, path: str) -> str:
        """从请求路径中提取业务资源路由前缀（剔除末尾 ID 或具体操作）"""
        normalized = path.rstrip('/')
        parts = normalized.split('/')
        if not parts:
            return normalized

        last_part = parts[-1]
        # 若尾部为纯数字 ID 或标准 UUID，则剥离最后一层
        if last_part.isdigit() or re.match(r'^[0-9a-fA-F-]{32,36}$', last_part):
            return '/'.join(parts[:-1])

        return normalized

    def _invalidate_related_cache(self, request):
        """当发生资源变更时，自动按租户与路由前缀批量清除相关 GET 缓存"""
        try:
            tenant_id = self._get_tenant_id(request)
            resource_prefix = self._extract_resource_prefix(request.path)

            # 构造通配匹配模式
            if tenant_id != 'public':
                pattern = f"*api_cache:{tenant_id}:*:{resource_prefix}*"
            else:
                pattern = f"*api_cache:*:*:{resource_prefix}*"

            if hasattr(cache, 'delete_pattern'):
                deleted_count = cache.delete_pattern(pattern)
                logger.info(
                    f"[APICache] 写操作触发缓存清除: Method={request.method}, Path={request.path}, "
                    f"Pattern={pattern}, DeletedCount={deleted_count}"
                )
            else:
                logger.debug(f"[APICache] 缓存后端不支持 delete_pattern，依赖短时 TTL 自然过期")
        except Exception as e:
            logger.warning(f"[APICache] 清除相关缓存失败: {e}")
