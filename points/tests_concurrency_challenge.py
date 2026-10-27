"""
BUG-LOGIC-01 对抗性并发挑战测试套件
验证:
1. 并发扣减超额拦截: 初始 100 积分，并发 2 个线程分别请求扣减 60。
   严格验证: 仅有 1 个请求能成功，另 1 个请求抛出 PointsInsufficientException，
   最终余额严格为 40，消费总额 60，绝不发生负余额或更新丢失。
2. 多线程并发超额扣减: 初始 100 积分，5 线程并发各扣 30 (总需 150)。
   严格验证: 仅有 3 个请求成功 (3 * 30 = 90)，其余 2 个抛出 PointsInsufficientException，
   最终余额严格为 10，消费记录严格为 3 条。
3. 多线程并发累加奖励: 初始 100 积分，10 线程并发各奖励 50 积分。
   严格验证: 10 个线程全部成功，最终余额严格为 100 + 10 * 50 = 600，绝无更新丢失。
"""
import os
import time
import uuid
import shutil
import tempfile
import threading
from unittest import TestCase
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.db.utils import OperationalError
from tenants.models import Tenant
from users.models import Member
from points.models import TenantUserProfile, TenantUserPoints
from points.services.points_engine import PointsEngine
from common.exceptions import PointsInsufficientException


class PointsConcurrencyChallengeTests(TestCase):
    """对抗实测: points_engine 并发安全与悲观锁/CAS 原子更新防御"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, 'points_challenge_test.sqlite3')
        cls.orig_db_name = settings.DATABASES['default']['NAME']
        settings.DATABASES['default']['NAME'] = cls.db_path
        connection.close()

        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA busy_timeout = 5000;")

        call_command('migrate', run_syncdb=True, verbosity=0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        connection.close()
        settings.DATABASES['default']['NAME'] = cls.orig_db_name
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        super().setUp()
        uid = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name=f"Pts Tenant {uid}", code=f"c_pts_{uid}", status="active")
        self.member = Member.objects.create_user(
            username=f"c_pts_user_{uid}",
            email=f"pts_{uid}@example.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.engine = PointsEngine()

    def _create_profile(self, initial_points=100):
        return TenantUserProfile.objects.create(
            tenant=self.tenant,
            member=self.member,
            total_points=initial_points,
            available_points=initial_points,
            points_earned_total=initial_points,
            points_spent_total=0,
            is_points_enabled=True,
            points_multiplier=1.0
        )

    def test_concurrent_consume_points_two_threads(self):
        """
        [BUG-LOGIC-01 并发挑战 1]
        初始积分 100，并发 2 个线程分别请求扣减 60。
        严格验证:
        - 仅有 1 个请求成功
        - 另 1 个请求抛出 PointsInsufficientException
        - 最终余额严格为 40，绝不发生负余额或更新丢失
        """
        profile = self._create_profile(initial_points=100)
        barrier = threading.Barrier(2)
        results = []
        insufficient_errors = []
        other_errors = []

        def worker(thread_idx):
            barrier.wait()
            for attempt in range(25):
                try:
                    record = self.engine.consume_points(
                        tenant_user_profile=profile,
                        points=60,
                        category="system",
                        reason=f"并发扣减线程-{thread_idx}"
                    )
                    results.append((thread_idx, record))
                    break
                except OperationalError:
                    time.sleep(0.05)
                    continue
                except PointsInsufficientException as pie:
                    insufficient_errors.append((thread_idx, pie))
                    break
                except Exception as ex:
                    other_errors.append((thread_idx, ex))
                    break
            connection.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(other_errors), 0, f"不应出现未预期的错误: {other_errors}")
        self.assertEqual(len(results), 1, f"严格仅允许 1 个请求成功，实际成功数: {len(results)}")
        self.assertEqual(len(insufficient_errors), 1, f"严格有 1 个请求抛出余额不足异常，实际: {len(insufficient_errors)}")

        profile.refresh_from_db()
        self.assertEqual(profile.available_points, 40, f"最终余额必须严格为 40，实际为: {profile.available_points}")
        self.assertEqual(profile.points_spent_total, 60, f"累计消费必须严格为 60，实际为: {profile.points_spent_total}")

        spend_count = TenantUserPoints.objects.filter(tenant_user_profile=profile, point_type='spend').count()
        self.assertEqual(spend_count, 1, f"数据库消费记录数必须严格为 1，实际为: {spend_count}")

    def test_concurrent_consume_points_multi_threads(self):
        """
        [BUG-LOGIC-01 并发挑战 2 极限压测]
        初始 100 积分，5 线程并发各扣 30 (总需 150)。
        严格验证:
        - 仅允许 3 个请求成功 (扣除 90)
        - 另外 2 个请求抛出 PointsInsufficientException (剩余 10 < 30)
        - 最终余额严格为 10，消费流水严格为 3 条
        """
        profile = self._create_profile(initial_points=100)
        num_threads = 5
        barrier = threading.Barrier(num_threads)
        results = []
        insufficient_errors = []
        other_errors = []

        def worker(thread_idx):
            barrier.wait()
            for attempt in range(25):
                try:
                    record = self.engine.consume_points(
                        tenant_user_profile=profile,
                        points=30,
                        category="system",
                        reason=f"压测扣减线程-{thread_idx}"
                    )
                    results.append((thread_idx, record))
                    break
                except OperationalError:
                    time.sleep(0.05)
                    continue
                except PointsInsufficientException as pie:
                    insufficient_errors.append((thread_idx, pie))
                    break
                except Exception as ex:
                    other_errors.append((thread_idx, ex))
                    break
            connection.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(other_errors), 0, f"不应出现未预期的错误: {other_errors}")
        self.assertEqual(len(results), 3, f"严格允许 3 个线程成功，实际成功数: {len(results)}")
        self.assertEqual(len(insufficient_errors), 2, f"严格拦截 2 个线程，实际拦截数: {len(insufficient_errors)}")

        profile.refresh_from_db()
        self.assertEqual(profile.available_points, 10, f"最终可用余额必须严格等于 10，实际为: {profile.available_points}")
        self.assertEqual(profile.points_spent_total, 90, f"累计消费必须严格等于 90，实际为: {profile.points_spent_total}")

        records_count = TenantUserPoints.objects.filter(tenant_user_profile=profile, point_type='spend').count()
        self.assertEqual(records_count, 3, f"数据库流水必须仅记录 3 条消费流水，实际为: {records_count}")

    def test_concurrent_award_points_multi_threads(self):
        """
        [BUG-LOGIC-01 并发挑战 3 累加奖励压测]
        初始 100 积分，10 线程并发各奖励 50 积分。
        严格验证:
        - 10 个线程全部成功
        - 最终余额严格为 100 + 10 * 50 = 600
        - 绝无任何更新丢失 (Lost Update)
        """
        profile = self._create_profile(initial_points=100)
        num_threads = 10
        barrier = threading.Barrier(num_threads)
        results = []
        exceptions = []

        def worker(thread_idx):
            barrier.wait()
            for attempt in range(25):
                try:
                    record = self.engine.award_points(
                        tenant_user_profile=profile,
                        points=50,
                        category="community",
                        reason=f"并发奖励线程-{thread_idx}"
                    )
                    results.append((thread_idx, record))
                    break
                except OperationalError:
                    time.sleep(0.05)
                    continue
                except Exception as ex:
                    exceptions.append((thread_idx, ex))
                    break
            connection.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(exceptions), 0, f"奖励积分不应抛出任何异常，实际异常: {exceptions}")
        self.assertEqual(len(results), 10, f"10 个并发奖励请求必须全部成功，实际成功数: {len(results)}")

        profile.refresh_from_db()
        expected_points = 100 + 10 * 50
        self.assertEqual(
            profile.available_points,
            expected_points,
            f"并发累加后可用积分必须严格为 {expected_points}，实际为: {profile.available_points}"
        )
        self.assertEqual(
            profile.total_points,
            expected_points,
            f"并发累加后总积分必须严格为 {expected_points}，实际为: {profile.total_points}"
        )
        self.assertEqual(
            profile.points_earned_total,
            expected_points,
            f"并发累加后累计获得积分必须严格为 {expected_points}，实际为: {profile.points_earned_total}"
        )

        records_count = TenantUserPoints.objects.filter(tenant_user_profile=profile, point_type='earn').count()
        self.assertEqual(records_count, 10, f"数据库流水必须记录 10 条奖励流水，实际为: {records_count}")
