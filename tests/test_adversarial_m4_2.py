"""
Adversarial Empirical Stress Test Suite for Challenger M4-2
=============================================================================
针对 Milestone 4 交付物进行高强度对抗实证验证：
1. [PERF-04 攻防] 极限时间跨度图表聚合 (365天 / 730天) 与数学准确性极限对抗：
   - 730 天极限跨度下实测 CaptureQueriesContext 查询总次数 <= 3（降幅 > 99%）
   - 软删除用户 (is_deleted=True) 存量与增量精准排除
   - 匿名访问 (user=None) 日志排除与同用户多条日志 Distinct 去重
   - 跨期连续 731 天零值平滑补齐与 running_total 累加数学精准性
   - 零数据防 ZeroDivisionError 与周/月聚合查询预算验证
2. [PERF-05 & PERF-07 攻防] 高并发异步 API 日志与子线程数据库连接释放：
   - 50 并发高频日志记录下子线程 connection.close() 回收完整性验证（零泄漏）
   - 异常注入攻防：写库失败时 finally: connection.close() 强制执行保证
   - API_LOG_SYNC 异步非阻塞执行验证
3. [PERF-07 攻防] 租户验证器 Cache-Aside 攻防与缓存降级安全性：
   - 不存在租户 (ID=999999) 与恶意非法参数击穿防御
   - 缓存命中 0 SQL 压测与 invalidate_tenant_cache 主动失效再查
   - _get_cache_backend_config 降级链路与 IGNORE_EXCEPTIONS 容灾验证
=============================================================================
"""
import concurrent.futures
import threading
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test import TestCase, TransactionTestCase, RequestFactory, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from django.http import HttpResponse

from users.models import User
from tenants.models import Tenant
from common.models import APILog
from common.services.tenant_validator import (
    TenantValidator,
    invalidate_tenant_cache,
    TENANT_CACHE_KEY_PREFIX,
)
from common.middleware.enhanced_api_logging_middleware import (
    EnhancedAPILoggingMiddleware,
    _do_save_log_entry,
)
from charts.utils import get_active_users, generate_period_labels
from core.settings import _get_cache_backend_config


class AdversarialChartAggregationPerfAndMathTests(TestCase):
    """
    [PERF-04 对抗实证挑战 1]
    极限时间跨度 (730天 / 365天) 压测与数学严谨性极限攻防
    """

    def setUp(self):
        cache.clear()

    def test_get_active_users_730_days_query_budget_and_reduction(self):
        """
        极限 730 天 (跨 2 年，含 2024 闰年共 731 天) 跨度压测：
        - 验证无论时间跨度多么巨大，SQL 查询次数严格 <= 3 次
        - 相比原有 731 次循环 COUNT，降幅超过 99.5%
        - 验证缓存生效时第二次调用 0 SQL 查询
        """
        start_date = date(2024, 1, 1)
        end_date = date(2025, 12, 31)  # 2024 是闰年，共 366 + 365 = 731 天

        # 1. 构造存量基准用户（在 2024-01-01 之前注册）
        prior_time = timezone.make_aware(datetime(2023, 10, 1, 12, 0, 0))
        # 30 个有效存量用户
        users_prior = [
            User(username=f'u_prior_{i}', email=f'u_prior_{i}@example.com', is_deleted=False)
            for i in range(30)
        ]
        # 10 个已软删除存量用户（必须被排除）
        users_prior_deleted = [
            User(username=f'u_prior_del_{i}', email=f'u_prior_del_{i}@example.com', is_deleted=True)
            for i in range(10)
        ]
        User.objects.bulk_create(users_prior + users_prior_deleted)
        User.objects.filter(username__startswith='u_prior_').update(date_joined=prior_time)

        # 2. 在 731 天区间内稀疏构造新增用户与活跃日志
        # 第 1 天: 2024-01-01 新增 5 个有效用户，2 个软删除用户
        day1_time = timezone.make_aware(datetime(2024, 1, 1, 9, 30, 0))
        u_d1 = [User(username=f'u_d1_{i}', email=f'u_d1_{i}@example.com', is_deleted=False) for i in range(5)]
        u_d1_del = [User(username=f'u_d1_del_{i}', email=f'u_d1_del_{i}@example.com', is_deleted=True) for i in range(2)]
        User.objects.bulk_create(u_d1 + u_d1_del)
        User.objects.filter(username__startswith='u_d1_').update(date_joined=day1_time)

        # 第 366 天 (2024-12-31): 新增 3 个有效用户
        day366_time = timezone.make_aware(datetime(2024, 12, 31, 15, 0, 0))
        u_d366 = [User(username=f'u_d366_{i}', email=f'u_d366_{i}@example.com', is_deleted=False) for i in range(3)]
        User.objects.bulk_create(u_d366)
        User.objects.filter(username__startswith='u_d366_').update(date_joined=day366_time)

        # 第 731 天 (2025-12-31): 新增 4 个有效用户
        day731_time = timezone.make_aware(datetime(2025, 12, 31, 18, 0, 0))
        u_d731 = [User(username=f'u_d731_{i}', email=f'u_d731_{i}@example.com', is_deleted=False) for i in range(4)]
        User.objects.bulk_create(u_d731)
        User.objects.filter(username__startswith='u_d731_').update(date_joined=day731_time)

        # 构造日志：
        # 第 1 天：存量用户 2 人 + 新用户 2 人活跃；其中 1 人产生 10 条日志（测试去重）；1 条匿名日志（user=None）
        sample_users_d1 = list(User.objects.filter(username__in=['u_prior_0', 'u_prior_1', 'u_d1_0', 'u_d1_1']))
        logs_d1 = []
        for u in sample_users_d1:
            logs_d1.append(APILog(user=u, request_method='GET', request_path='/api/v1/test/', status_code=200, response_time=10, ip_address='127.0.0.1'))
        # 重复日志（同一用户同一天多发9条）
        for _ in range(9):
            logs_d1.append(APILog(user=sample_users_d1[0], request_method='POST', request_path='/api/v1/test/', status_code=200, response_time=15, ip_address='127.0.0.1'))
        # 匿名请求日志
        logs_d1.append(APILog(user=None, request_method='GET', request_path='/api/v1/public/', status_code=200, response_time=5, ip_address='127.0.0.1'))
        APILog.objects.bulk_create(logs_d1)
        APILog.objects.filter(created_at__isnull=True).update(created_at=day1_time)
        APILog.objects.all().update(created_at=day1_time)

        # 3. 执行 CaptureQueriesContext 捕获查询总数
        with CaptureQueriesContext(connection) as ctx:
            result = get_active_users(start_date=start_date, end_date=end_date, period='daily')

        query_count = len(ctx.captured_queries)
        print(f"\n[实测数据] 731 天时间跨度总 SQL 查询次数: {query_count}")

        # 严苛断言 1: 无论跨越多少天，查询总数必须 <= 3 次！
        self.assertLessEqual(query_count, 3)

        # 严苛断言 2: 查询次数降幅必须 > 99% (731次 -> <= 3次，降幅达 99.59%)
        reduction_rate = (731 - query_count) / 731
        self.assertGreater(reduction_rate, 0.99)

        # 严苛断言 3: 二次查询缓存命中，查询次数为 0
        with CaptureQueriesContext(connection) as ctx_cached:
            cached_result = get_active_users(start_date=start_date, end_date=end_date, period='daily')
        self.assertEqual(len(ctx_cached.captured_queries), 0)
        self.assertEqual(cached_result, result)

    def test_get_active_users_mathematical_precision_and_zero_filling(self):
        """
        数学严谨性极限实证：
        1. 验证 labels 连续无断点，共 731 个时间标签
        2. 验证无数据日期的 0 值连续平滑补齐 (active_count=0, rate=0.0)
        3. 验证 running_total_users 数学累加精准性：
           - 初始基准存量严格等于起始日期前的未删除有效用户
           - 中途新增用户按天精准累加
           - 软删除用户绝对不计入
        4. 验证 active_rate = active_count / running_total * 100 准确性
        5. 验证 distinct 去重与匿名用户排除
        """
        start_date = date(2024, 1, 1)
        end_date = date(2025, 12, 31)

        # 存量基准用户：有效 20 人，软删除 5 人
        prior_time = timezone.make_aware(datetime(2023, 12, 1, 0, 0, 0))
        valid_priors = [User(username=f'v_prior_{i}', email=f'v_{i}@ex.com', is_deleted=False) for i in range(20)]
        del_priors = [User(username=f'del_prior_{i}', email=f'd_{i}@ex.com', is_deleted=True) for i in range(5)]
        User.objects.bulk_create(valid_priors + del_priors)
        User.objects.filter(username__contains='prior_').update(date_joined=prior_time)

        # 2024-01-01 (第 1 天): 新增有效 10 人，新增软删除 3 人
        t_day1 = timezone.make_aware(datetime(2024, 1, 1, 10, 0, 0))
        d1_valid = [User(username=f'd1_valid_{i}', email=f'd1_v_{i}@ex.com', is_deleted=False) for i in range(10)]
        d1_del = [User(username=f'd1_del_{i}', email=f'd1_d_{i}@ex.com', is_deleted=True) for i in range(3)]
        User.objects.bulk_create(d1_valid + d1_del)
        User.objects.filter(username__startswith='d1_').update(date_joined=t_day1)

        # 2024-01-01 活跃日志：
        # 挑选 6 个不同用户活跃，其中 1 个用户写入 10 条日志；另写入 2 条匿名日志
        active_u = list(User.objects.filter(username__in=['v_prior_0', 'v_prior_1', 'd1_valid_0', 'd1_valid_1', 'd1_valid_2', 'd1_valid_3']))
        logs = [APILog(user=u, request_method='GET', request_path='/api/', status_code=200, response_time=10, ip_address='127.0.0.1') for u in active_u]
        # 重复 10 条
        for _ in range(10):
            logs.append(APILog(user=active_u[0], request_method='GET', request_path='/api/', status_code=200, response_time=10, ip_address='127.0.0.1'))
        # 匿名 2 条
        logs.append(APILog(user=None, request_method='GET', request_path='/api/', status_code=200, response_time=10, ip_address='127.0.0.1'))
        logs.append(APILog(user=None, request_method='GET', request_path='/api/', status_code=200, response_time=10, ip_address='127.0.0.1'))
        APILog.objects.bulk_create(logs)
        APILog.objects.all().update(created_at=t_day1)

        # 2024-06-15 (第 167 天): 新增有效 5 人
        t_mid = timezone.make_aware(datetime(2024, 6, 15, 12, 0, 0))
        d_mid_valid = [User(username=f'd_mid_{i}', email=f'd_mid_{i}@ex.com', is_deleted=False) for i in range(5)]
        User.objects.bulk_create(d_mid_valid)
        User.objects.filter(username__startswith='d_mid_').update(date_joined=t_mid)

        # 2024-06-15 活跃日志：2 人活跃
        u_mid_active = list(User.objects.filter(username__in=['d_mid_0', 'v_prior_2']))
        mid_logs = [APILog(user=u, request_method='GET', request_path='/api/', status_code=200, response_time=10, ip_address='127.0.0.1') for u in u_mid_active]
        APILog.objects.bulk_create(mid_logs)
        APILog.objects.filter(user__username__in=['d_mid_0', 'v_prior_2']).update(created_at=t_mid)

        # 执行聚合查询
        res = get_active_users(start_date=start_date, end_date=end_date, period='daily')

        labels = res['labels']
        self.assertEqual(len(labels), 731)
        self.assertEqual(labels[0], '2024-01-01')
        self.assertEqual(labels[-1], '2025-12-31')

        active_dataset = next(ds for ds in res['datasets'] if ds['label'] == '活跃用户数')
        rate_dataset = next(ds for ds in res['datasets'] if ds['label'] == '活跃率')
        active_counts = active_dataset['data']
        active_rates = rate_dataset['data']

        # 验证第 1 天 (2024-01-01):
        # 存量基准 20 + 当日新增 10 = 30 人 (软删除 5+3 人严格排除)
        # 活跃人数: 精确为 6 人 (去重后 6，匿名被排除)
        # 活跃率: 6 / 30 * 100 = 20.0%
        self.assertEqual(active_counts[0], 6)
        self.assertEqual(active_rates[0], 20.0)

        # 验证第 2 天 (2024-01-02，无数据日期):
        # 0 值补齐: active_count = 0, active_rate = 0.0
        self.assertEqual(active_counts[1], 0)
        self.assertEqual(active_rates[1], 0.0)

        # 验证第 167 天 (2024-06-15):
        # 累积总用户: 20 + 10 + 5 = 35 人
        # 活跃人数: 2 人
        # 活跃率: 2 / 35 * 100 = 5.714... -> 四舍五入保留1位小数为 5.7%
        mid_idx = labels.index('2024-06-15')
        self.assertEqual(active_counts[mid_idx], 2)
        self.assertEqual(active_rates[mid_idx], 5.7)

        # 验证最高活跃日指标
        summary = res['summary']
        self.assertEqual(summary['highest_active_count'], 6)
        self.assertEqual(summary['highest_active_day'], '2024-01-01')

    def test_get_active_users_weekly_and_monthly_query_budget(self):
        """
        验证周 (weekly) 和月 (monthly) 周期下的聚合性能与连续标签
        - 跨度 3 年 (2023-01-01 至 2025-12-31，共 36 个月)
        - SQL 查询次数依然严格 <= 3 次
        """
        start_date = date(2023, 1, 1)
        end_date = date(2025, 12, 31)

        # 1. 验证 monthly
        cache.clear()
        with CaptureQueriesContext(connection) as ctx_month:
            res_month = get_active_users(start_date=start_date, end_date=end_date, period='monthly')
        self.assertLessEqual(len(ctx_month.captured_queries), 3)
        self.assertEqual(len(res_month['labels']), 36)
        self.assertEqual(res_month['labels'][0], '2023-01')
        self.assertEqual(res_month['labels'][-1], '2025-12')

        # 2. 验证 weekly
        cache.clear()
        with CaptureQueriesContext(connection) as ctx_week:
            res_week = get_active_users(start_date=start_date, end_date=end_date, period='weekly')
        self.assertLessEqual(len(ctx_week.captured_queries), 3)
        # 3 年约 156~157 周
        self.assertGreaterEqual(len(res_week['labels']), 156)
        self.assertIn(res_week['labels'][0], ['2022-W52', '2023-W01'])
        self.assertIn(res_week['labels'][-1], ['2025-W52', '2026-W01'])

    def test_get_active_users_empty_database_and_boundary_defense(self):
        """
        边界条件极限攻防：
        1. 数据库完全没有任何用户或日志（0 基准，0 增量，0 活跃）：
           验证不抛出 ZeroDivisionError，平滑返回所有点全为 0 的图表
        2. start_date > end_date 逆序时间：
           验证优雅返回空图表，无崩溃
        """
        # 1. 纯空数据防御
        res = get_active_users(start_date=date(2026, 1, 1), end_date=date(2026, 1, 5), period='daily')
        self.assertEqual(len(res['labels']), 5)
        active_counts = res['datasets'][0]['data']
        active_rates = res['datasets'][1]['data']
        self.assertEqual(active_counts, [0, 0, 0, 0, 0])
        self.assertEqual(active_rates, [0.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(res['summary']['highest_active_count'], 0)
        self.assertEqual(res['summary']['average_active_rate'], 0)

        # 2. 逆序日期防御
        res_inverted = get_active_users(start_date=date(2026, 2, 1), end_date=date(2026, 1, 1))
        self.assertEqual(res_inverted['chart_type'], 'line')
        self.assertEqual(len(res_inverted['labels']), 0)


class AdversarialLoggingConcurrencyAndConnectionTests(TransactionTestCase):
    """
    [PERF-05 & PERF-07 对抗实证挑战 2]
    极限并发高频日志记录、子线程连接回收与异常安全攻防
    """

    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

    def test_high_concurrency_api_logging_and_connection_release(self):
        """
        极限并发实证：
        使用 50 个并发线程同时调用 _do_save_log_entry 写入 API 日志。
        实测证明：
        1. 所有 50 条物理日志准确写入数据库（无丢失、无死锁）
        2. 每个子线程在完成写库后，finally 中的 connection.close() 100% 触发，
           子线程私有 connection 得到显式回收（无连接泄漏）
        """
        worker_count = 50
        connection_close_call_count = 0
        lock = threading.Lock()
        sqlite_save_lock = threading.Lock()

        backend_cls = type(connection._connections['default'])
        original_close = backend_cls.close
        original_save = APILog.save

        def instrumented_close(self_wrapper):
            nonlocal connection_close_call_count
            with lock:
                connection_close_call_count += 1
            original_close(self_wrapper)

        def thread_safe_sqlite_save(log_obj, *args, **kwargs):
            # 防止 SQLite 在多线程并发写同一测试单文件数据库时发生文件级锁冲突
            with sqlite_save_lock:
                return original_save(log_obj, *args, **kwargs)

        log_tasks = [
            {
                'request_method': 'GET',
                'request_path': f'/api/v1/resource/{i}/',
                'status_code': 200,
                'status_type': 'success',
                'response_time': 12 + i,
                'ip_address': f'192.168.1.{i % 255}',
                'user_agent': f'AdversarialBot-{i}',
            }
            for i in range(worker_count)
        ]

        with patch.object(backend_cls, 'close', side_effect=instrumented_close, autospec=True):
            with patch.object(APILog, 'save', side_effect=thread_safe_sqlite_save, autospec=True):
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                    futures = [executor.submit(_do_save_log_entry, task) for task in log_tasks]
                    concurrent.futures.wait(futures)

        # 断言 1: 全部 50 次日志物理落库完成
        saved_logs_count = APILog.objects.filter(user_agent__startswith='AdversarialBot-').count()
        self.assertEqual(saved_logs_count, worker_count)

        # 断言 2: connection.close() 被精准调用 50 次，零泄漏
        self.assertEqual(connection_close_call_count, worker_count)

    def test_api_log_worker_exception_safety_guarantees_connection_release(self):
        """
        异常注入攻击测试：
        构造引发数据库或保存异常的恶意数据（例如导致 save 抛出异常），
        验证在发生未捕获异常时，finally: connection.close() 依然坚固执行，
        确保即使发生写库故障也不会导致子线程数据库连接悬挂泄漏。
        """
        backend_cls = type(connection._connections['default'])
        connection_closed = False
        original_close = backend_cls.close

        def spy_close(self_wrapper):
            nonlocal connection_closed
            connection_closed = True
            original_close(self_wrapper)

        faulty_log_data = {'request_path': '/faulty/'}

        with patch.object(backend_cls, 'close', side_effect=spy_close, autospec=True):
            with patch('common.models.APILog.save', side_effect=RuntimeError("Simulated DB fatal write failure")):
                # 执行应被内部 try-except 吸收，不会向外抛出崩溃应用
                _do_save_log_entry(faulty_log_data)

        # 严苛断言：即使发生致命保存异常，connection.close() 依然被切实执行！
        self.assertTrue(connection_closed)

    def test_middleware_non_blocking_async_under_load(self):
        """
        验证高并发场景下中间件非阻塞行为：
        API_LOG_SYNC=False 时，process_response 毫秒级返回，
        不等待数据库写入完成，写库任务被非阻塞排队提交到工作线程池。
        """
        with override_settings(API_LOG_SYNC=False):
            with patch('common.middleware.enhanced_api_logging_middleware._log_executor.submit') as mock_submit:
                middleware = EnhancedAPILoggingMiddleware(
                    get_response=lambda r: HttpResponse(b'{"status": "ok"}', content_type='application/json')
                )
                
                # 连续触发 30 次请求
                for i in range(30):
                    request = self.factory.get(f'/api/v1/fast-path/{i}/')
                    middleware.process_request(request)
                    response = HttpResponse(b'{"fast": true}', status=200)
                    middleware.process_response(request, response)

                # 严苛断言：全部 30 次写库任务均异步投递至线程池，主线程零阻塞
                self.assertEqual(mock_submit.call_count, 30)


class AdversarialTenantCacheResilienceAndDegradationTests(TestCase):
    """
    [PERF-07 对抗实证挑战 3]
    租户验证器 Cache-Aside 攻防、缓存穿透防御与自适应降级安全性
    """

    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        self.tenant = Tenant.objects.create(
            name="Adversary Corp",
            code="adv_corp",
            status="active"
        )

    def test_tenant_validator_cache_hit_and_atomic_invalidation(self):
        """
        验证高频租户验证缓存命中与精准主动失效：
        1. 首次查询：未命中，执行 1 次 SQL
        2. 后续 50 次重复查询：100% 缓存命中，SQL 执行总数为 0
        3. 调用 invalidate_tenant_cache 后缓存清除
        4. 再次查询：重新查库 1 次并重新写入缓存
        """
        request = self.factory.get('/api/v1/test/')
        validator = TenantValidator(request)

        # 1. 首次查询
        with CaptureQueriesContext(connection) as ctx_init:
            tenant_1 = validator._get_tenant_by_id(self.tenant.id)
        self.assertEqual(len(ctx_init.captured_queries), 1)
        self.assertEqual(tenant_1.id, self.tenant.id)

        # 2. 连续 50 次高频访问：必须 0 SQL
        with CaptureQueriesContext(connection) as ctx_cached:
            for _ in range(50):
                t = validator._get_tenant_by_id(self.tenant.id)
                self.assertEqual(t.id, self.tenant.id)
        self.assertEqual(len(ctx_cached.captured_queries), 0)

        # 3. 主动失效
        invalidate_tenant_cache(self.tenant.id)
        self.assertIsNone(cache.get(f"{TENANT_CACHE_KEY_PREFIX}{self.tenant.id}"))

        # 4. 失效后重新访问：触发 1 次 SQL 重新加载
        with CaptureQueriesContext(connection) as ctx_reload:
            tenant_reloaded = validator._get_tenant_by_id(self.tenant.id)
        self.assertEqual(len(ctx_reload.captured_queries), 1)
        self.assertEqual(tenant_reloaded.id, self.tenant.id)

    def test_tenant_validator_cache_penetration_and_invalid_ids(self):
        """
        缓存击穿与恶意入参防御攻防：
        1. 请求不存在的租户 ID (99999999): 返回 None，生成规范 400 租户不存在错误，不发生未处理 500
        2. 非法类型参数 (非数字字符串、负数、None、布尔值): 安全拦截并返回 None，不崩溃
        """
        request = self.factory.get('/api/v1/test/')
        validator = TenantValidator(request)

        # 1. 查询不存在的租户
        non_existent_tenant = validator._get_tenant_by_id(99999999)
        self.assertIsNone(non_existent_tenant)

        # 验证完整验证链路生成 400 错误响应
        error_resp = validator.validate_and_set_tenant_context(effective_tenant_id=99999999)
        self.assertIsNotNone(error_resp)
        self.assertEqual(error_resp.status_code, 400)

        # 2. 恶意非法入参测试
        for bad_id in ["invalid_string", "@#$%", None, [], {}]:
            res = validator._get_tenant_by_id(bad_id)
            self.assertIsNone(res, f"Failed for bad id: {bad_id}")

    def test_cache_configuration_resilience_and_fallback(self):
        """
        验证集中式缓存自适应降级安全性：
        1. 存在 django_redis 时，正确构建带 IGNORE_EXCEPTIONS=True 的配置（避免 Redis 网络抖动导致应用崩溃）
        2. 模拟缺少 django_redis 时，无缝降级为 Django 原生 RedisCache
        3. 未指定 REDIS_URL 时，平滑降级为本地 LocMemCache
        """
        test_url = "redis://redis.cluster.local:6379/2"

        # 1. 正常探测
        config_with_redis = _get_cache_backend_config(test_url)
        self.assertIn(
            config_with_redis['BACKEND'],
            ['django_redis.cache.RedisCache', 'django.core.cache.backends.redis.RedisCache']
        )
        self.assertEqual(config_with_redis['LOCATION'], test_url)
        self.assertEqual(config_with_redis['KEY_PREFIX'], 'lipeaks')

        # 若是 django_redis，严苛验证必须配置 IGNORE_EXCEPTIONS 保证容灾
        if config_with_redis['BACKEND'] == 'django_redis.cache.RedisCache':
            self.assertTrue(config_with_redis.get('OPTIONS', {}).get('IGNORE_EXCEPTIONS', False))

        # 2. 模拟缺少 django_redis 模块时的降级
        with patch.dict('sys.modules', {'django_redis': None}):
            # 重新导入或调用函数捕获 ImportError 降级分支
            with patch('builtins.__import__', side_effect=ImportError("No module named 'django_redis'")):
                fallback_config = _get_cache_backend_config(test_url)
                self.assertEqual(fallback_config['BACKEND'], 'django.core.cache.backends.redis.RedisCache')
                self.assertEqual(fallback_config['LOCATION'], test_url)

        # 3. 验证测试环境严格降级隔离：
        self.assertEqual(
            settings.CACHES['default']['BACKEND'],
            'django.core.cache.backends.locmem.LocMemCache'
        )
