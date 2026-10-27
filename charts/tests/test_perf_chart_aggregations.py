from datetime import date, datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from tenants.models import Tenant
from common.models import APILog
from charts.utils import get_active_users, get_user_growth_trend


class ChartAggregationPerfTests(APITestCase):
    """
    PERF-04 仪表盘图表数据库级 TruncDate 聚合与 0 值平滑补齐专项回归测试
    """

    def setUp(self):
        cache.clear()
        self.superadmin = User.objects.create_superuser(
            username='chart_superadmin',
            email='chart_superadmin@example.com',
            password='Password123!',
            is_super_admin=True,
            is_admin=False
        )

    def test_get_active_users_sql_query_count_under_threshold(self):
        """
        验证跨度 365 天时 get_active_users 执行的 SQL 查询次数 <= 3 次（原逻辑为 365+ 次循环 COUNT）
        """
        start_date = date(2025, 1, 1)
        end_date = date(2025, 12, 31)

        # 构造存量用户与区间内新增用户
        prior_time = timezone.make_aware(datetime(2024, 12, 1, 10, 0, 0))
        u_prior = User.objects.create(
            username='u_prior',
            email='u_prior@example.com',
            is_deleted=False
        )
        User.objects.filter(id=u_prior.id).update(date_joined=prior_time)

        mid_time = timezone.make_aware(datetime(2025, 6, 1, 10, 0, 0))
        u_mid = User.objects.create(
            username='u_mid',
            email='u_mid@example.com',
            is_deleted=False
        )
        User.objects.filter(id=u_mid.id).update(date_joined=mid_time)

        # 构造日志记录
        log = APILog.objects.create(
            user=u_mid,
            request_method='GET',
            request_path='/api/v1/test/',
            status_code=200,
            response_time=25,
            status_type='success',
            ip_address='127.0.0.1'
        )
        APILog.objects.filter(id=log.id).update(created_at=mid_time)

        with CaptureQueriesContext(connection) as ctx:
            result = get_active_users(start_date=start_date, end_date=end_date, period='daily')

        # 核心断言：查询次数必须 <= 3 次（存量1次 + 增量1次 + 活跃统计1次）
        self.assertLessEqual(len(ctx.captured_queries), 3)

        # 验证返回数据的完整性与平滑连续性
        self.assertEqual(result['chart_type'], 'line')
        self.assertEqual(len(result['labels']), 365)
        self.assertEqual(result['labels'][0], '2025-01-01')
        self.assertEqual(result['labels'][-1], '2025-12-31')

        # 验证 2025-06-01 处的活跃统计
        mid_idx = result['labels'].index('2025-06-01')
        active_dataset = next(ds for ds in result['datasets'] if ds['label'] == '活跃用户数')
        self.assertEqual(active_dataset['data'][mid_idx], 1)
        # 前一天的活跃数为 0（平滑补齐）
        self.assertEqual(active_dataset['data'][mid_idx - 1], 0)

    def test_get_user_growth_trend_zero_padding_and_continuity(self):
        """
        验证不连续日期下的 0 值平滑补齐与累计总用户数连续递增
        """
        start_date = date(2026, 3, 1)
        end_date = date(2026, 3, 5)

        t1 = timezone.make_aware(datetime(2026, 3, 1, 8, 0, 0))
        t5 = timezone.make_aware(datetime(2026, 3, 5, 12, 0, 0))

        u1 = User.objects.create(username='u_pad_1', email='u_pad_1@example.com')
        User.objects.filter(id=u1.id).update(date_joined=t1)

        u5 = User.objects.create(username='u_pad_5', email='u_pad_5@example.com')
        User.objects.filter(id=u5.id).update(date_joined=t5)

        result = get_user_growth_trend(start_date=start_date, end_date=end_date, period='daily')

        expected_labels = ['2026-03-01', '2026-03-02', '2026-03-03', '2026-03-04', '2026-03-05']
        self.assertEqual(result['labels'], expected_labels)

        new_users_ds = next(ds for ds in result['datasets'] if ds['label'] == '新增用户数')
        self.assertEqual(new_users_ds['data'], [1, 0, 0, 0, 1])

        total_users_ds = next(ds for ds in result['datasets'] if ds['label'] == '用户总数')
        # 起始前已有 superadmin，累计值平滑递增
        base_count = total_users_ds['data'][0]
        self.assertEqual(total_users_ds['data'], [base_count, base_count, base_count, base_count, base_count + 1])

    def test_tenant_trend_database_aggregation_api(self):
        """
        验证 TenantTrendChartView 数据库级聚合与 API 连通性
        """
        self.client.force_authenticate(user=self.superadmin)

        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 3)

        t1 = Tenant.objects.create(name='Tenant 1', code='t1', status='active')
        Tenant.objects.filter(id=t1.id).update(
            created_at=timezone.make_aware(datetime(2026, 1, 1, 9, 0, 0))
        )

        t3 = Tenant.objects.create(name='Tenant 3', code='t3', status='active')
        Tenant.objects.filter(id=t3.id).update(
            created_at=timezone.make_aware(datetime(2026, 1, 3, 11, 0, 0))
        )

        url = f"{reverse('charts:tenant-trend')}?period=daily&start_date=2026-01-01&end_date=2026-01-03"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data.get('data', response.data)
        self.assertEqual(data['labels'], ['2026-01-01', '2026-01-02', '2026-01-03'])
        # 累计值：1, 1, 2
        self.assertEqual(data['datasets'][0]['data'], [1, 1, 2])

    def test_tenant_creation_rate_aggregation_api(self):
        """
        验证 TenantCreationRateView 柱状图聚合统计与空周期平滑补齐
        """
        self.client.force_authenticate(user=self.superadmin)

        start_date = date(2026, 1, 1)
        end_date = date(2026, 3, 31)

        t_jan = Tenant.objects.create(name='Tenant Jan', code='t_jan', status='active')
        Tenant.objects.filter(id=t_jan.id).update(
            created_at=timezone.make_aware(datetime(2026, 1, 15, 10, 0, 0))
        )

        t_mar = Tenant.objects.create(name='Tenant Mar', code='t_mar', status='active')
        Tenant.objects.filter(id=t_mar.id).update(
            created_at=timezone.make_aware(datetime(2026, 3, 20, 10, 0, 0))
        )

        url = f"{reverse('charts:tenant-creation-rate')}?period=monthly&start_date=2026-01-01&end_date=2026-03-31"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data.get('data', response.data)
        self.assertEqual(data['labels'], ['2026-01', '2026-02', '2026-03'])
        # 1月有1个，2月补齐0个，3月有1个
        self.assertEqual(data['datasets'][0]['data'], [1, 0, 1])
        self.assertEqual(data['summary']['total_new'], 2)

    def test_empty_chart_responses(self):
        """
        验证无数据时返回正确的空图表响应结构
        """
        self.client.force_authenticate(user=self.superadmin)
        url = f"{reverse('charts:tenant-creation-rate')}?period=monthly&start_date=2020-01-01&end_date=2020-03-31"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('data', response.data)
        self.assertEqual(data['labels'], [])
        self.assertEqual(data['summary']['message'], "所选时间范围内没有新增租户")

