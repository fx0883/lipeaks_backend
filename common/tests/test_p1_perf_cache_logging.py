from unittest.mock import patch
from django.test import TestCase, RequestFactory, override_settings
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.http import HttpResponse

from tenants.models import Tenant
from common.models import APILog
from common.services.tenant_validator import TenantValidator, invalidate_tenant_cache, TENANT_CACHE_KEY_PREFIX
from common.middleware.enhanced_api_logging_middleware import (
    EnhancedAPILoggingMiddleware,
    _do_save_log_entry
)
from core.settings import _get_cache_backend_config


class CacheAndLoggingPerfTests(TestCase):
    """
    PERF-05 & PERF-07 集中式缓存、租户缓存命中与非阻塞 API 日志回归测试
    """

    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        self.tenant = Tenant.objects.create(
            name="Cache Test Tenant",
            code="cache_test",
            status="active"
        )

    def test_cache_configuration_fallback(self):
        """
        验证缓存配置函数根据环境与 REDIS_URL 自适应选择后端
        """
        redis_url = "redis://127.0.0.1:6379/1"
        config = _get_cache_backend_config(redis_url)
        self.assertIn(config['BACKEND'], [
            'django_redis.cache.RedisCache',
            'django.core.cache.backends.redis.RedisCache'
        ])
        self.assertEqual(config['LOCATION'], redis_url)
        self.assertEqual(config['KEY_PREFIX'], 'lipeaks')

        # 验证当前测试环境中 CACHES 配置为独立 LocMemCache
        from django.conf import settings
        self.assertEqual(
            settings.CACHES['default']['BACKEND'],
            'django.core.cache.backends.locmem.LocMemCache'
        )

    def test_tenant_validator_cache_hit_and_invalidation(self):
        """
        验证租户验证器 Cache-Aside：首次查库、二次缓存命中（0 SQL）、主动失效生效
        """
        request = self.factory.get('/api/v1/test/')
        validator = TenantValidator(request)

        # 1. 首次查询：缓存未命中，执行数据库查询并填充缓存
        tenant_1 = validator._get_tenant_by_id(self.tenant.id)
        self.assertIsNotNone(tenant_1)
        self.assertEqual(tenant_1.id, self.tenant.id)

        # 验证缓存已经写入
        cached_val = cache.get(f"{TENANT_CACHE_KEY_PREFIX}{self.tenant.id}")
        self.assertIsNotNone(cached_val)
        self.assertEqual(cached_val.id, self.tenant.id)

        # 2. 二次查询：必须从缓存读取，SQL 查询次数为 0
        with CaptureQueriesContext(connection) as ctx:
            tenant_2 = validator._get_tenant_by_id(self.tenant.id)
            self.assertEqual(len(ctx.captured_queries), 0)
        self.assertEqual(tenant_2.id, self.tenant.id)

        # 3. 主动失效：调用 invalidate_tenant_cache
        invalidate_tenant_cache(self.tenant.id)
        self.assertIsNone(cache.get(f"{TENANT_CACHE_KEY_PREFIX}{self.tenant.id}"))

        # 4. 失效后再查：重新查询数据库
        with CaptureQueriesContext(connection) as ctx:
            tenant_3 = validator._get_tenant_by_id(self.tenant.id)
            self.assertEqual(len(ctx.captured_queries), 1)
        self.assertEqual(tenant_3.id, self.tenant.id)

    def test_api_logging_middleware_sync_in_test(self):
        """
        验证 API_LOG_SYNC=True 时日志同步落库且字段完整
        """
        middleware = EnhancedAPILoggingMiddleware(get_response=lambda r: HttpResponse(b'{"status": "ok"}', content_type='application/json'))
        request = self.factory.get('/api/v1/applications/')
        
        # 模拟中间件流程
        middleware.process_request(request)
        response = HttpResponse(b'{"status": "ok"}', content_type='application/json', status=200)
        middleware.process_response(request, response)

        # 验证 APILog 成功同步落库
        log = APILog.objects.filter(request_path='/api/v1/applications/').order_by('-created_at').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.request_method, 'GET')
        self.assertEqual(log.status_type, 'success')

    def test_api_logging_middleware_non_blocking_async(self):
        """
        验证 API_LOG_SYNC=False 时中间件通过线程池非阻塞异步提交写库任务
        """
        with override_settings(API_LOG_SYNC=False):
            with patch('common.middleware.enhanced_api_logging_middleware._log_executor.submit') as mock_submit:
                middleware = EnhancedAPILoggingMiddleware(get_response=lambda r: HttpResponse(b'{"ok": true}'))
                request = self.factory.get('/api/v1/feedbacks/')
                middleware.process_request(request)
                response = HttpResponse(b'{"ok": true}', status=200)
                middleware.process_response(request, response)

                # 核心断言：必须调用了线程池 submit，主线程无阻塞
                self.assertTrue(mock_submit.called)
                args, _ = mock_submit.call_args
                self.assertEqual(args[0], _do_save_log_entry)
                self.assertEqual(args[1]['request_path'], '/api/v1/feedbacks/')
