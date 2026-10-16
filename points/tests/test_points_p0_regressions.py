"""
BUG-LOGIC-01 & BUG-LOGIC-10 回归测试
验证积分发放与扣减行锁及原子操作、无效许可证动作的异常结构与无 NameError
"""
from django.test import TestCase
from tenants.models import Tenant
from users.models import Member
from points.models import TenantUserProfile
from points.services.points_engine import PointsEngine
from common.exceptions import PointsException, PointsInsufficientException


class PointsP0RegressionTests(TestCase):
    """测试 points_engine 并发原子控制与动作白名单校验"""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Points Tenant", code="pts_tenant", status="active")
        self.member = Member.objects.create_user(
            username="pts_member",
            email="pts@example.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.profile = TenantUserProfile.objects.create(
            tenant=self.tenant,
            member=self.member,
            total_points=200,
            available_points=200,
            points_earned_total=200,
            points_spent_total=0,
            is_points_enabled=True,
            points_multiplier=1.0
        )
        self.engine = PointsEngine()

    def test_award_points_atomic_update(self):
        """[BUG-LOGIC-01] 奖励积分原子累加与字段刷新验证"""
        record = self.engine.award_points(
            tenant_user_profile=self.profile,
            points=100,
            category='community',
            reason='社区活动奖励'
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.points, 100)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.total_points, 300)
        self.assertEqual(self.profile.available_points, 300)
        self.assertEqual(self.profile.points_earned_total, 300)

    def test_consume_points_atomic_update_and_insufficient_exception(self):
        """[BUG-LOGIC-01] 消费积分原子扣减与余额不足拦截验证"""
        # 正常消费 80
        record = self.engine.consume_points(
            tenant_user_profile=self.profile,
            points=80,
            category='system',
            reason='购买商品'
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.points, -80)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.available_points, 120)
        self.assertEqual(self.profile.points_spent_total, 80)

        # 余额不足消费（需要 150，但只有 120）
        with self.assertRaises(PointsInsufficientException) as cm:
            self.engine.consume_points(
                tenant_user_profile=self.profile,
                points=150,
                category='system',
                reason='超额消费'
            )
        self.assertEqual(cm.exception.extra.get('available_points'), 120)
        self.assertEqual(cm.exception.extra.get('required_points'), 150)

        # 校验数据库未被篡改
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.available_points, 120)

    def test_award_license_points_unsupported_action_no_name_error(self):
        """[BUG-LOGIC-10] 许可证未知动作异常不抛 NameError 并包含显式动作列表"""
        with self.assertRaises(PointsException) as cm:
            self.engine.award_license_points(
                tenant_user_profile=self.profile,
                action='unsupported_action_xyz',
                license_key='KEY-12345'
            )
        exc = cm.exception
        self.assertEqual(exc.error_code, 'UNSUPPORTED_LICENSE_ACTION')
        self.assertEqual(exc.extra.get('supported_actions'), ['activation', 'renewal'])
