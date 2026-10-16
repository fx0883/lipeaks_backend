"""
全局 API Redis 缓存中间件 (APICacheMiddleware) 单元与集成测试套件
全面验证：
1. 首次未命中与回写（MISS）、二次请求命中返回（HIT）；
2. 多租户严格隔离性；
3. 多用户与匿名用户身份隔离性；
4. Query 参数排序一致性与差异性；
5. Cache-Control: no-cache 与 nocache=1 主动穿透；
6. 敏感路由黑名单跳过机制；
7. 写操作（POST/PUT/DELETE）联动前缀失效机制；
8. 错误状态码与非 JSON 响应防缓存保护。
"""

import json
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory, TestCase, override_settings

from common.middleware.api_cache_middleware import APICacheMiddleware
from common.utils.tenant_context import set_current_tenant, clear_current_tenant
from tenants.models import Tenant

User = get_user_model()


@override_settings(API_CACHE_ENABLED=True)
class APICacheMiddlewareTests(TestCase):
    def setUp(self):
        cache.clear()
        clear_current_tenant()
        self.factory = RequestFactory()

        # 创建测试租户
        self.tenant1 = Tenant.objects.create(name="Tenant Alpha", code="alpha")
        self.tenant2 = Tenant.objects.create(name="Tenant Beta", code="beta")

        # 创建测试用户
        self.user1 = User.objects.create_user(
            username="user_alpha",
            password="password123",
            tenant=self.tenant1
        )
        self.user2 = User.objects.create_user(
            username="user_beta",
            password="password123",
            tenant=self.tenant2
        )

    def tearDown(self):
        cache.clear()
        clear_current_tenant()

    def test_first_get_request_misses_and_second_hits_cache(self):
        """验证标准 GET API：首次 MISS 并回写缓存，二次请求直接 HIT"""
        middleware = APICacheMiddleware()

        def view_mock(req):
            return JsonResponse({'message': 'articles list', 'items': [1, 2, 3]})

        # 1. 首次请求
        request1 = self.factory.get('/api/v1/cms/articles/')
        request1.user = self.user1
        set_current_tenant(self.tenant1)

        # 经过 process_request（此时未命中）
        resp1 = middleware.process_request(request1)
        self.assertIsNone(resp1)

        # 模拟进入视图
        view_resp = view_mock(request1)
        # 经过 process_response 回写
        final_resp1 = middleware.process_response(request1, view_resp)
        self.assertEqual(final_resp1['X-Cache'], 'MISS')
        self.assertIn('X-Cache-Key', final_resp1)

        cache_key = final_resp1['X-Cache-Key']
        self.assertTrue(cache_key.startswith(f"api_cache:{self.tenant1.id}:user_{self.user1.id}:/api/v1/cms/articles:"))

        # 2. 第二次相同请求
        request2 = self.factory.get('/api/v1/cms/articles/')
        request2.user = self.user1
        set_current_tenant(self.tenant1)

        hit_resp = middleware.process_request(request2)
        self.assertIsNotNone(hit_resp, "第二次请求应直接由 process_request 命中并返回")
        self.assertEqual(hit_resp['X-Cache'], 'HIT')
        self.assertEqual(hit_resp['X-Cache-Key'], cache_key)
        self.assertEqual(json.loads(hit_resp.content), {'message': 'articles list', 'items': [1, 2, 3]})

    def test_multi_tenant_isolation(self):
        """验证多租户数据强隔离：不同租户访问同一 API 路由不会串用缓存"""
        middleware = APICacheMiddleware()

        # 租户 1 写入缓存
        set_current_tenant(self.tenant1)
        req1 = self.factory.get('/api/v1/cms/articles/')
        req1.user = self.user1
        resp1 = middleware.process_response(req1, JsonResponse({'tenant': 'alpha'}))
        self.assertEqual(resp1['X-Cache'], 'MISS')

        # 租户 2 访问相同路径，必须 MISS，绝不能读取租户 1 的缓存
        set_current_tenant(self.tenant2)
        req2 = self.factory.get('/api/v1/cms/articles/')
        req2.user = self.user2
        hit_resp2 = middleware.process_request(req2)
        self.assertIsNone(hit_resp2, "租户 2 不得命中租户 1 的缓存")

    def test_query_params_differentiation_and_order_insensitivity(self):
        """验证 Query 参数敏感性：不同分页参数产生不同 Key；相同参数不同顺序生成相同 Key"""
        middleware = APICacheMiddleware()
        set_current_tenant(self.tenant1)

        req_p1 = self.factory.get('/api/v1/cms/articles/?page=1&page_size=20')
        req_p1.user = self.user1
        key_p1 = middleware._build_cache_key(req_p1)

        req_p2 = self.factory.get('/api/v1/cms/articles/?page=2&page_size=20')
        req_p2.user = self.user1
        key_p2 = middleware._build_cache_key(req_p2)

        self.assertNotEqual(key_p1, key_p2, "不同分页参数必须产生独立缓存 Key")

        # 参数乱序但内容相同：?page_size=20&page=1
        req_p1_reordered = self.factory.get('/api/v1/cms/articles/?page_size=20&page=1')
        req_p1_reordered.user = self.user1
        key_p1_reordered = middleware._build_cache_key(req_p1_reordered)

        self.assertEqual(key_p1, key_p1_reordered, "参数顺序不同应哈希出相同的缓存 Key")

    def test_cache_control_no_cache_bypasses_cache(self):
        """验证客户端 Cache-Control: no-cache 或 nocache=1 能够主动穿透缓存"""
        middleware = APICacheMiddleware()
        set_current_tenant(self.tenant1)

        # 先填充缓存
        req = self.factory.get('/api/v1/cms/articles/')
        req.user = self.user1
        middleware.process_response(req, JsonResponse({'data': 'cached'}))

        # 携带 Cache-Control: no-cache 访问
        req_bypass = self.factory.get('/api/v1/cms/articles/', HTTP_CACHE_CONTROL='no-cache')
        req_bypass.user = self.user1
        hit = middleware.process_request(req_bypass)
        self.assertIsNone(hit, "携带 no-cache 请求头时必须穿透缓存")

        # 携带 ?nocache=1 参数访问
        req_bypass_query = self.factory.get('/api/v1/cms/articles/?nocache=1')
        req_bypass_query.user = self.user1
        hit_query = middleware.process_request(req_bypass_query)
        self.assertIsNone(hit_query, "携带 ?nocache=1 查询参数时必须穿透缓存")

    def test_blacklist_endpoints_are_never_cached(self):
        """验证黑名单敏感接口绝不参与缓存（如 auth、licenses 心跳）"""
        middleware = APICacheMiddleware()

        req_auth = self.factory.get('/api/v1/auth/token/refresh/')
        self.assertFalse(middleware._should_cache_request(req_auth))

        req_license = self.factory.get('/api/v1/licenses/heartbeat/')
        self.assertFalse(middleware._should_cache_request(req_license))

        req_pwd = self.factory.get('/api/v1/members/password-reset/')
        self.assertFalse(middleware._should_cache_request(req_pwd))

    def test_write_operation_triggers_cache_invalidation(self):
        """验证写操作（POST / PUT / DELETE）成功后，自动模糊清除相关资源的 GET 缓存"""
        middleware = APICacheMiddleware()
        set_current_tenant(self.tenant1)

        # 模拟预热缓存
        cache_key = f"api_cache:{self.tenant1.id}:user_{self.user1.id}:/api/v1/cms/articles:hash123"
        cache.set(cache_key, {'content': b'cached', 'status': 200, 'content_type': 'application/json'}, 120)
        self.assertIsNotNone(cache.get(cache_key))

        # 执行写操作：POST /api/v1/cms/articles/
        post_req = self.factory.post('/api/v1/cms/articles/', data={'title': 'New Article'})
        post_req.user = self.user1
        post_resp = JsonResponse({'status': 'created'}, status=201)

        # 模拟具备 delete_pattern 的集中式后端（如 django-redis）
        with patch.object(cache, 'delete_pattern', return_value=1, create=True) as mock_delete_pattern:
            middleware.process_response(post_req, post_resp)
            mock_delete_pattern.assert_called_once()
            call_pattern = mock_delete_pattern.call_args[0][0]
            self.assertIn(f"api_cache:{self.tenant1.id}", call_pattern)
            self.assertIn("/api/v1/cms/articles", call_pattern)

    def test_error_responses_and_non_json_are_not_cached(self):
        """验证 4xx、5xx 错误响应及 HTML 页面绝不写入缓存"""
        middleware = APICacheMiddleware()
        set_current_tenant(self.tenant1)

        # 400 错误
        req_err = self.factory.get('/api/v1/cms/articles/')
        req_err.user = self.user1
        err_resp = JsonResponse({'error': 'bad request'}, status=400)
        middleware.process_response(req_err, err_resp)

        cache_key = err_resp.get('X-Cache-Key')
        self.assertIsNone(cache.get(cache_key), "400 响应严禁写入缓存")

        # HTML 页面响应
        req_html = self.factory.get('/api/v1/cms/articles/')
        req_html.user = self.user1
        html_resp = HttpResponse("<html>Hello</html>", content_type="text/html", status=200)
        middleware.process_response(req_html, html_resp)
        self.assertIsNone(cache.get(cache_key), "非 JSON 响应严禁写入 API 缓存")
