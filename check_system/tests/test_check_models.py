"""
Check System 模型单元测试
覆盖 TaskCategory (Parler 多语言与软删除)、Task (租户自动继承与频次判定边界)、
CheckRecord (条件唯一约束防重打卡与软删除重打卡)、CheckinCycle (21天周期排他激活与进度边界)
"""
from datetime import date, datetime, time, timedelta
from django.db import IntegrityError, transaction
from django.test import TestCase

from check_system.models import CheckinCycle, CheckRecord, Task, TaskCategory
from tenants.models import Tenant
from users.models import Member


class CheckSystemModelTests(TestCase):
    """打卡系统核心模型单元测试"""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Checkin Tenant", code="checkin_tenant")
        self.member = Member.objects.create(
            username="checkin_member",
            email="member@checkin.com",
            tenant=self.tenant,
        )

    def test_task_category_creation_and_soft_delete(self):
        """验证 TaskCategory 多语言模型创建、__str__ 展示及软删除标记"""
        sys_cat = TaskCategory.objects.create(
            name="早睡早起",
            description="系统预设睡眠打卡",
            is_system=True,
            form_type="sleep",
        )
        self.assertEqual(sys_cat.name, "早睡早起")
        self.assertIn("(系统)", str(sys_cat))

        tenant_cat = TaskCategory.objects.create(
            name="每日阅读",
            description="租户自定义阅读打卡",
            is_system=False,
            tenant=self.tenant,
            form_type="reading",
        )
        self.assertEqual(str(tenant_cat), "每日阅读")
        self.assertFalse(tenant_cat.is_deleted)

        tenant_cat.soft_delete()
        tenant_cat.refresh_from_db()
        self.assertTrue(tenant_cat.is_deleted)

    def test_task_auto_inherits_member_tenant(self):
        """验证 Task 保存时自动从关联的 member 继承 tenant"""
        task = Task.objects.create(
            name="晨跑5公里",
            member=self.member,
            start_date=date.today(),
            frequency_type="daily",
        )
        self.assertEqual(task.tenant, self.tenant)

    def test_task_is_check_required_today_daily_and_boundaries(self):
        """验证 is_check_required_today 对 daily 频率及状态、起止日期边界的判定"""
        today = date.today()

        # 1. 正常进行中的 daily 任务
        task = Task.objects.create(
            name="每日冥想",
            member=self.member,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=5),
            status="active",
            frequency_type="daily",
        )
        self.assertTrue(task.is_check_required_today())

        # 2. 非 active 状态（如 paused）返回 False
        task.status = "paused"
        task.save()
        self.assertFalse(task.is_check_required_today())

        # 3. 尚未到达开始日期返回 False
        task.status = "active"
        task.start_date = today + timedelta(days=1)
        task.save()
        self.assertFalse(task.is_check_required_today())

        # 4. 已超过结束日期返回 False
        task.start_date = today - timedelta(days=10)
        task.end_date = today - timedelta(days=1)
        task.save()
        self.assertFalse(task.is_check_required_today())

    def test_task_is_check_required_today_weekly_monthly_custom(self):
        """验证 weekly / monthly / custom 打卡频次判定"""
        today = date.today()
        current_weekday = datetime.now().weekday() + 1  # 1-7
        other_weekday = (current_weekday % 7) + 1

        # Weekly 匹配与不匹配
        weekly_task = Task.objects.create(
            name="周报总结",
            member=self.member,
            start_date=today,
            frequency_type="weekly",
            frequency_days=[current_weekday],
        )
        self.assertTrue(weekly_task.is_check_required_today())
        weekly_task.frequency_days = [other_weekday]
        self.assertFalse(weekly_task.is_check_required_today())

        # Monthly 匹配与不匹配
        monthly_task = Task.objects.create(
            name="月度复盘",
            member=self.member,
            start_date=today,
            frequency_type="monthly",
            frequency_days=[today.day],
        )
        self.assertTrue(monthly_task.is_check_required_today())
        monthly_task.frequency_days = [(today.day % 28) + 1]
        self.assertFalse(monthly_task.is_check_required_today())

        # Custom 匹配与不匹配
        today_str = today.strftime("%Y-%m-%d")
        custom_task = Task.objects.create(
            name="特定日打卡",
            member=self.member,
            start_date=today,
            frequency_type="custom",
            frequency_days=[today_str],
        )
        self.assertTrue(custom_task.is_check_required_today())
        custom_task.frequency_days = ["2099-12-31"]
        self.assertFalse(custom_task.is_check_required_today())

    def test_check_record_unique_constraint_and_soft_delete_recheckin(self):
        """验证同日同任务重复打卡触发 IntegrityError，软删除后允许重新打卡"""
        today = date.today()
        task = Task.objects.create(
            name="背单词",
            member=self.member,
            start_date=today,
        )

        record1 = CheckRecord.objects.create(
            member=self.member,
            task=task,
            check_date=today,
            check_time=time(8, 30),
        )
        self.assertEqual(record1.tenant, self.tenant)

        # 未软删除时，同一 member + task + check_date 触发数据库唯一约束异常
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CheckRecord.objects.create(
                    member=self.member,
                    task=task,
                    check_date=today,
                    check_time=time(9, 0),
                )

        # 软删除旧打卡记录后，允许在同一天重新打卡
        record1.soft_delete()
        record2 = CheckRecord.objects.create(
            member=self.member,
            task=task,
            check_date=today,
            check_time=time(10, 0),
        )
        self.assertIsNotNone(record2.pk)
        self.assertNotEqual(record1.pk, record2.pk)
        self.assertFalse(record2.is_deleted)

    def test_checkin_cycle_auto_end_date_and_exclusive_active(self):
        """验证 CheckinCycle 自动计算 end_date = start_date + 20天，且新活跃周期自动停用旧活跃周期"""
        start_1 = date(2026, 1, 1)
        cycle1 = CheckinCycle.objects.create(
            member=self.member,
            start_date=start_1,
            selected_themes=[1, 2],
            is_active=True,
        )
        self.assertEqual(cycle1.end_date, date(2026, 1, 21))
        self.assertEqual(cycle1.tenant, self.tenant)
        self.assertTrue(cycle1.is_active)

        # 创建第二个活跃周期，cycle1 应被自动置为 is_active=False
        start_2 = date(2026, 2, 1)
        cycle2 = CheckinCycle.objects.create(
            member=self.member,
            start_date=start_2,
            selected_themes=[3],
            is_active=True,
        )
        cycle1.refresh_from_db()
        self.assertFalse(cycle1.is_active)
        self.assertTrue(cycle2.is_active)

    def test_checkin_cycle_get_current_day_and_progress_boundaries(self):
        """验证 CheckinCycle.get_current_day() 与 get_progress() 的时间边界计算"""
        today = date.today()

        # 1. 尚未开始 (start_date 在未来) -> 第 0 天，进度 0%
        future_cycle = CheckinCycle.objects.create(
            member=self.member,
            start_date=today + timedelta(days=5),
            is_active=False,
        )
        self.assertEqual(future_cycle.get_current_day(), 0)
        self.assertEqual(future_cycle.get_progress(), 0)

        # 2. 周期第一天 (start_date == today) -> 第 1 天，进度 round(1/21*100) = 5%
        day1_cycle = CheckinCycle.objects.create(
            member=self.member,
            start_date=today,
            is_active=False,
        )
        self.assertEqual(day1_cycle.get_current_day(), 1)
        self.assertEqual(day1_cycle.get_progress(), 5)

        # 3. 周期最后一天 (start_date == today - 20 days, end_date == today) -> 第 21 天，进度 100%
        day21_cycle = CheckinCycle.objects.create(
            member=self.member,
            start_date=today - timedelta(days=20),
            is_active=False,
        )
        self.assertEqual(day21_cycle.get_current_day(), 21)
        self.assertEqual(day21_cycle.get_progress(), 100)

        # 4. 已过结束日期 (end_date < today) -> 封顶第 21 天，进度 100%
        past_cycle = CheckinCycle.objects.create(
            member=self.member,
            start_date=today - timedelta(days=30),
            is_active=False,
        )
        self.assertEqual(past_cycle.get_current_day(), 21)
        self.assertEqual(past_cycle.get_progress(), 100)
