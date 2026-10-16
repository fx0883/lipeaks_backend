"""
P1-12 (ARCH-02) 租户上下文 ContextVar 隔离与中间件清理回归测试套件
验证项目：
1. 基础 CRUD 与函数签名向后兼容性；
2. 上下文管理器 tenant_context 作用域与异常恢复；
3. 多线程并发隔离 (Thread Isolation)；
4. ASGI / asyncio 协程并发隔离 (Zero Cross-Task Tenant Bleed)；
5. TenantMiddleware 全生命周期与多分支异常安全清理 (WSGI & ASGI)。
"""
import asyncio
import inspect
import threading
import time
from unittest.mock import MagicMock

from django.test import SimpleTestCase, RequestFactory
from rest_framework.exceptions import ValidationError

from common.middleware.tenant_middleware import TenantMiddleware
from common.utils.tenant_context import (
    get_current_tenant,
    set_current_tenant,
    clear_current_tenant,
    tenant_context,
)


class DummyTenant:
    """轻量测试租户桩对象"""
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return f"<DummyTenant {self.id}: {self.name}>"


class TenantContextUnitAndConcurrencyTests(SimpleTestCase):
    """ContextVar 单元与并发隔离测试"""

    def setUp(self):
        super().setUp()
        clear_current_tenant()

    def tearDown(self):
        clear_current_tenant()
        super().tearDown()

    def test_default_tenant_is_none(self):
        """验证未设置时租户上下文默认为 None"""
        self.assertIsNone(get_current_tenant())

    def test_set_and_get_tenant(self):
        """验证设置和获取租户上下文正常运作"""
        tenant = DummyTenant(1, "Tenant A")
        set_current_tenant(tenant)
        self.assertEqual(get_current_tenant(), tenant)

    def test_clear_current_tenant(self):
        """验证 clear_current_tenant 能够清除租户上下文"""
        tenant = DummyTenant(1, "Tenant A")
        set_current_tenant(tenant)
        self.assertEqual(get_current_tenant(), tenant)

        clear_current_tenant()
        self.assertIsNone(get_current_tenant())

    def test_set_none_clears_tenant(self):
        """验证 set_current_tenant(None) 亦能清除租户上下文"""
        tenant = DummyTenant(1, "Tenant A")
        set_current_tenant(tenant)
        self.assertEqual(get_current_tenant(), tenant)

        set_current_tenant(None)
        self.assertIsNone(get_current_tenant())

    def test_clear_idempotency(self):
        """验证多次调用 clear_current_tenant 幂等且无异常"""
        clear_current_tenant()
        clear_current_tenant()
        self.assertIsNone(get_current_tenant())

    def test_function_signatures_backward_compatible(self):
        """验证向后兼容的函数签名"""
        sig_get = inspect.signature(get_current_tenant)
        self.assertEqual(len(sig_get.parameters), 0)

        sig_set = inspect.signature(set_current_tenant)
        self.assertEqual(len(sig_set.parameters), 1)

        sig_clear = inspect.signature(clear_current_tenant)
        self.assertEqual(len(sig_clear.parameters), 0)

    def test_context_manager_scope_and_restore(self):
        """验证 tenant_context 上下文管理器在退出时自动恢复前序上下文"""
        initial_tenant = DummyTenant(100, "Base Tenant")
        nested_tenant = DummyTenant(200, "Nested Tenant")

        set_current_tenant(initial_tenant)
        self.assertEqual(get_current_tenant(), initial_tenant)

        with tenant_context(nested_tenant):
            self.assertEqual(get_current_tenant(), nested_tenant)

        # 退出上下文管理器后必须恢复为 initial_tenant
        self.assertEqual(get_current_tenant(), initial_tenant)

        # 上下文管理器抛出异常时也必须恢复
        try:
            with tenant_context(nested_tenant):
                self.assertEqual(get_current_tenant(), nested_tenant)
                raise RuntimeError("Simulated error in context block")
        except RuntimeError:
            pass

        self.assertEqual(get_current_tenant(), initial_tenant)

    def test_multi_thread_isolation(self):
        """
        [并发隔离] 验证在多线程并发场景下，各工作线程拥有独立的 ContextVar 副本，互不干扰
        """
        thread_results = {}

        def thread_worker(tid):
            local_tenant = DummyTenant(tid, f"ThreadTenant_{tid}")
            set_current_tenant(local_tenant)
            time.sleep(0.01)  # 促使线程调度交错
            thread_results[tid] = (get_current_tenant() == local_tenant)
            clear_current_tenant()
            thread_results[f"{tid}_after"] = (get_current_tenant() is None)

        threads = [threading.Thread(target=thread_worker, args=(i,)) for i in range(1, 6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for tid in range(1, 6):
            self.assertTrue(thread_results[tid], f"Thread {tid} context was corrupted!")
            self.assertTrue(thread_results[f"{tid}_after"], f"Thread {tid} failed to clear!")

        # 主线程租户上下文仍然不受任何子线程污染
        self.assertIsNone(get_current_tenant())

    def test_asyncio_coroutine_isolation_zero_bleed(self):
        """
        [ARCH-02 核心验证] 验证 ASGI / asyncio 协程并发调度下，租户上下文绝对隔离，零跨租户串染
        """
        async def async_worker(cid, delay):
            coro_tenant = DummyTenant(cid, f"AsyncTenant_{cid}")
            set_current_tenant(coro_tenant)
            # 挂起协程，出让事件循环给其他并发协程
            await asyncio.sleep(delay)
            # 协程恢复后，断言租户未被其他协程覆写
            is_intact = (get_current_tenant() == coro_tenant)
            clear_current_tenant()
            return is_intact

        async def main_coro():
            # 5 个协程不同休眠时间并发执行
            tasks = [
                async_worker(1, 0.03),
                async_worker(2, 0.01),
                async_worker(3, 0.02),
                async_worker(4, 0.015),
                async_worker(5, 0.005),
            ]
            return await asyncio.gather(*tasks)

        results = asyncio.run(main_coro())
        self.assertTrue(all(results), "Async coroutines leaked tenant context to each other!")
        self.assertIsNone(get_current_tenant())


class TenantMiddlewareCleanupTests(SimpleTestCase):
    """TenantMiddleware 正常及多分支异常清理防护测试"""

    def setUp(self):
        super().setUp()
        clear_current_tenant()
        self.factory = RequestFactory()

    def tearDown(self):
        clear_current_tenant()
        super().tearDown()

    def test_middleware_cleans_up_on_successful_sync_request(self):
        """验证同步请求正常完成后，租户上下文被可靠清理"""
        tenant = DummyTenant(1, "ReqTenant")

        def mock_get_response(req):
            # 模拟在请求处理中已被设置租户
            set_current_tenant(tenant)
            return MagicMock(status_code=200)

        middleware = TenantMiddleware(mock_get_response)
        request = self.factory.get('/api/v1/test/')
        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(get_current_tenant(), "ContextVar was not cleared after sync request!")

    def test_middleware_cleans_up_on_view_exception_sync(self):
        """验证当下游视图抛出未捕获异常时，finally/process_exception 确保清理租户"""
        tenant = DummyTenant(2, "CrashingTenant")

        def crashing_view(req):
            set_current_tenant(tenant)
            raise RuntimeError("Database connection suddenly dropped")

        middleware = TenantMiddleware(crashing_view)
        request = self.factory.get('/api/v1/test/')

        with self.assertRaises(RuntimeError):
            middleware(request)

        self.assertIsNone(get_current_tenant(), "ContextVar leaked after downstream exception!")

    def test_middleware_cleans_up_on_process_request_validation_error(self):
        """验证 process_request 抛出 ValidationError 时租户上下文亦被可靠清理"""
        def dummy_view(req):
            return MagicMock(status_code=200)

        middleware = TenantMiddleware(dummy_view)
        # 模拟请求头带有无效租户ID，触发解析异常
        request = self.factory.get('/api/v1/points/', HTTP_X_TENANT_ID='invalid')
        middleware.path_checker.requires_tenant_verification = MagicMock(return_value=True)

        set_current_tenant(DummyTenant(3, "TempTenant"))
        with self.assertRaises(Exception):
            # 请求头无 token 且非公开，解析触发异常
            middleware(request)

        self.assertIsNone(get_current_tenant(), "ContextVar leaked on validation failure!")

    def test_middleware_cleans_up_on_async_successful_request(self):
        """验证 ASGI 异步请求正常完成后，__acall__ 可靠执行清理"""
        tenant = DummyTenant(4, "AsyncReqTenant")

        async def async_view(req):
            set_current_tenant(tenant)
            await asyncio.sleep(0.01)
            return MagicMock(status_code=200)

        middleware = TenantMiddleware(async_view)
        request = self.factory.get('/api/v1/test/')

        response = asyncio.run(middleware(request))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(get_current_tenant(), "ContextVar leaked after async request!")

    def test_middleware_cleans_up_on_async_exception(self):
        """验证 ASGI 异步视图抛出异常时，__acall__ finally 可靠执行清理"""
        tenant = DummyTenant(5, "AsyncCrashTenant")

        async def async_crashing_view(req):
            set_current_tenant(tenant)
            await asyncio.sleep(0.01)
            raise RuntimeError("Async view crashed")

        middleware = TenantMiddleware(async_crashing_view)
        request = self.factory.get('/api/v1/test/')

        with self.assertRaises(RuntimeError):
            asyncio.run(middleware(request))

        self.assertIsNone(get_current_tenant(), "ContextVar leaked after async crash!")
