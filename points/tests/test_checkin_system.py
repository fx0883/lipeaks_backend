from datetime import date, timedelta
from django.test import TestCase
from rest_framework.test import APIClient
from common.exceptions import PointsException
from tenants.models import Tenant
from users.models import Member
from applications.models import Application
from points.models import (
    TenantUserProfile,
    ApplicationUserLevel,
    AppUserPointsAccount,
    TenantUserPoints,
    CheckinConfig,
    UserCheckinStreak,
    UserCheckinRecord
)
from points.services.checkin_service import CheckinService


class CheckinSystemServiceTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="打卡测试租户", code="t_chk_test", status="active")
        self.app1 = Application.objects.create(
            tenant=self.tenant,
            name="填色花园",
            code="app_coloring",
            status="active"
        )
        self.app2 = Application.objects.create(
            tenant=self.tenant,
            name="自然拼读",
            code="app_phonics",
            status="active"
        )
        self.member = Member.objects.create_user(
            username="chk_member",
            email="chk@example.com",
            password="Password123!",
            tenant=self.tenant
        )

    def test_first_checkin_and_duplicate_guard(self):
        d1 = date(2026, 11, 1)
        res = CheckinService.execute_checkin(
            member=self.member,
            tenant=self.tenant,
            application=self.app1,
            today=d1
        )
        self.assertTrue(res['success'])
        self.assertEqual(res['current_streak'], 1)
        self.assertEqual(res['points_earned'], 10)  # Day 1 default ladder is 10
        self.assertEqual(res['new_balance'], 10)

        # 检查账户与明细
        account = AppUserPointsAccount.objects.get(tenant=self.tenant, application=self.app1, member=self.member)
        self.assertEqual(account.available_points, 10)
        self.assertEqual(account.total_points, 10)

        # 检查流水
        ledger = TenantUserPoints.objects.filter(app_account=account, category='checkin')
        self.assertEqual(ledger.count(), 1)
        self.assertEqual(ledger.first().points, 10)

        # 同一天重复签到应抛出异常
        with self.assertRaises(PointsException) as ctx:
            CheckinService.execute_checkin(
                member=self.member,
                tenant=self.tenant,
                application=self.app1,
                today=d1
            )
        self.assertEqual(ctx.exception.error_code, "ALREADY_CHECKED_IN")

    def test_consecutive_checkin_ladder_rewards(self):
        # 连续签到 7 天
        base_date = date(2026, 11, 1)
        expected_ladder = [10, 15, 20, 25, 30, 40, 100]

        for i in range(7):
            cur_date = base_date + timedelta(days=i)
            res = CheckinService.execute_checkin(
                member=self.member,
                tenant=self.tenant,
                application=self.app1,
                today=cur_date
            )
            self.assertEqual(res['current_streak'], i + 1)
            self.assertEqual(res['points_earned'], expected_ladder[i])

        account = AppUserPointsAccount.objects.get(tenant=self.tenant, application=self.app1, member=self.member)
        self.assertEqual(account.available_points, sum(expected_ladder))

        # 第 8 天：repeat 模式循环回第 1 天
        d8 = base_date + timedelta(days=7)
        res8 = CheckinService.execute_checkin(
            member=self.member,
            tenant=self.tenant,
            application=self.app1,
            today=d8
        )
        self.assertEqual(res8['current_streak'], 8)
        self.assertEqual(res8['points_earned'], 10)  # (8 - 1) % 7 + 1 = 1 -> 10 pts

    def test_broken_streak_reset(self):
        d1 = date(2026, 11, 1)
        CheckinService.execute_checkin(member=self.member, tenant=self.tenant, application=self.app1, today=d1)

        d2 = date(2026, 11, 2)
        CheckinService.execute_checkin(member=self.member, tenant=self.tenant, application=self.app1, today=d2)

        # 第 3 天漏签，在第 4 天打卡 -> 断签，重置为第 1 天
        d4 = date(2026, 11, 4)
        res4 = CheckinService.execute_checkin(member=self.member, tenant=self.tenant, application=self.app1, today=d4)
        self.assertEqual(res4['current_streak'], 1)
        self.assertEqual(res4['points_earned'], 10)

    def test_checkin_triggers_level_upgrade(self):
        # 设置等级：LV1 (0-15分), LV2 (16分以上)
        lvl1 = ApplicationUserLevel.objects.create(
            tenant=self.tenant,
            application=self.app1,
            level_name="青铜画师",
            level_code="BRONZE",
            level_order=1,
            min_points=0,
            max_points=15,
            is_default=True
        )
        lvl2 = ApplicationUserLevel.objects.create(
            tenant=self.tenant,
            application=self.app1,
            level_name="白银画宗",
            level_code="SILVER",
            level_order=2,
            min_points=16,
            max_points=None,
            is_default=False
        )

        # 初始分配为 LV1 青铜画师
        profile = TenantUserProfile.objects.create(tenant=self.tenant, member=self.member)
        AppUserPointsAccount.objects.create(
            tenant=self.tenant,
            application=self.app1,
            member=self.member,
            tenant_user_profile=profile,
            current_level=lvl1,
            total_points=0,
            available_points=0
        )

        d1 = date(2026, 11, 1)
        res1 = CheckinService.execute_checkin(member=self.member, tenant=self.tenant, application=self.app1, today=d1)
        self.assertEqual(res1['current_level'], "青铜画师")
        self.assertFalse(res1['level_upgraded'])

        # 第2天打卡获 15 分，累计 25 分，跨越 16 门槛晋升白银
        d2 = date(2026, 11, 2)
        res2 = CheckinService.execute_checkin(member=self.member, tenant=self.tenant, application=self.app1, today=d2)
        self.assertTrue(res2['level_upgraded'])
        self.assertEqual(res2['current_level'], "白银画宗")

    def test_independent_application_checkin(self):
        # 用户在 app1 和 app2 签到互相独立
        d1 = date(2026, 11, 1)
        res_app1 = CheckinService.execute_checkin(member=self.member, tenant=self.tenant, application=self.app1, today=d1)
        res_app2 = CheckinService.execute_checkin(member=self.member, tenant=self.tenant, application=self.app2, today=d1)

        self.assertEqual(res_app1['current_streak'], 1)
        self.assertEqual(res_app2['current_streak'], 1)

        # 检查各自独立的 streak 统计
        streak1 = UserCheckinStreak.objects.get(tenant=self.tenant, application=self.app1, member=self.member)
        streak2 = UserCheckinStreak.objects.get(tenant=self.tenant, application=self.app2, member=self.member)
        self.assertEqual(streak1.current_streak, 1)
        self.assertEqual(streak2.current_streak, 1)


class CheckinAPITests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="打卡API测试租户", code="t_chk_api", status="active")
        self.app = Application.objects.create(
            tenant=self.tenant,
            name="色彩工坊",
            code="app_color_workshop",
            status="active"
        )
        self.member = Member.objects.create_user(
            username="api_chk_user",
            email="chk_api@example.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.member)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id), HTTP_HOST='localhost')

    def test_default_ladder_endpoint(self):
        res = self.client.get("/api/v1/points/checkin-configs/default_ladder/")
        self.assertEqual(res.status_code, 200)
        ladder = res.data if isinstance(res.data, list) else res.data.get("data", [])
        self.assertIsInstance(ladder, list)
        self.assertEqual(len(ladder), 7)
        self.assertEqual(ladder[0]['points'], 10)
        self.assertEqual(ladder[6]['points'], 100)

    def test_checkin_config_crud_api(self):
        # 1. 创建配置
        create_res = self.client.post("/api/v1/points/checkin-configs/", {
            "application": self.app.id,
            "name": "色彩工坊专属签到",
            "cycle_days": 7,
            "cycle_mode": "repeat",
            "reward_ladder": [
                {"day": 1, "points": 20},
                {"day": 2, "points": 30},
                {"day": 3, "points": 40},
                {"day": 4, "points": 50},
                {"day": 5, "points": 60},
                {"day": 6, "points": 80},
                {"day": 7, "points": 200}
            ],
            "allow_recheckin": True,
            "recheckin_cost": 30,
            "is_active": True
        }, format='json')
        self.assertEqual(create_res.status_code, 201)

        # 2. 查询列表过滤
        list_res = self.client.get(f"/api/v1/points/checkin-configs/?application={self.app.id}")
        self.assertEqual(list_res.status_code, 200)
        data = list_res.data.get("data", list_res.data)
        results = data.get("results", data) if isinstance(data, dict) else data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "色彩工坊专属签到")

    def test_member_checkin_flow_api(self):
        # 1. 查询签到初始状态
        status_res = self.client.get(f"/api/v1/points/checkin/status/?application_id={self.app.id}")
        self.assertEqual(status_res.status_code, 200)
        s_data = status_res.data.get("data", status_res.data)
        self.assertFalse(s_data["has_checked_in_today"])
        self.assertEqual(s_data["current_streak"], 0)
        self.assertEqual(len(s_data["calendar"]), 7)

        # 2. 执行签到打卡
        exec_res = self.client.post("/api/v1/points/checkin/execute/", {
            "application_id": self.app.id
        }, format='json')
        self.assertEqual(exec_res.status_code, 200)
        e_data = exec_res.data.get("data", exec_res.data)
        self.assertTrue(e_data["success"])
        self.assertEqual(e_data["current_streak"], 1)
        self.assertEqual(e_data["points_earned"], 10)

        # 3. 再次查询状态 -> 今日已签到
        status_res2 = self.client.get(f"/api/v1/points/checkin/status/?application_id={self.app.id}")
        self.assertEqual(status_res2.status_code, 200)
        s_data2 = status_res2.data.get("data", status_res2.data)
        self.assertTrue(s_data2["has_checked_in_today"])
        self.assertEqual(s_data2["current_streak"], 1)

        # 4. 当天重复签到 -> 400
        exec_dup = self.client.post("/api/v1/points/checkin/execute/", {
            "application_id": self.app.id
        }, format='json')
        self.assertEqual(exec_dup.status_code, 400)
        err_data = exec_dup.data.get("data", exec_dup.data)
        self.assertEqual(err_data.get("error_code") or exec_dup.data.get("error_code"), "ALREADY_CHECKED_IN")

        # 5. 查看流水记录
        records_res = self.client.get(f"/api/v1/points/checkin/records/?application_id={self.app.id}")
        self.assertEqual(records_res.status_code, 200)
        r_data = records_res.data.get("data", records_res.data)
        items = r_data.get("results", r_data) if isinstance(r_data, dict) else r_data
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["streak_day"], 1)
        self.assertEqual(items[0]["reward_points"], 10)

    def test_recheckin_workflow_and_api(self):
        # 1. 开启补签配置，补签消耗 20 积分
        config = CheckinService.get_or_create_config(self.tenant, self.app)
        config.allow_recheckin = True
        config.recheckin_cost = 20
        config.save()

        # 2. 为用户赋予初始可用积分 50
        profile, _ = TenantUserProfile.objects.get_or_create(
            tenant=self.tenant,
            member=self.member,
            defaults={'is_points_enabled': True}
        )
        account, _ = AppUserPointsAccount.objects.get_or_create(
            tenant=self.tenant,
            application=self.app,
            member=self.member,
            defaults={
                'tenant_user_profile': profile,
                'available_points': 50,
                'total_points': 50,
                'is_enabled': True
            }
        )
        account.available_points = 50
        account.total_points = 50
        account.save()

        # 3. 模拟前天已签到 (Day 1)
        yesterday = date.today() - timedelta(days=1)
        day_before = yesterday - timedelta(days=1)

        CheckinService.execute_checkin(
            member=self.member,
            tenant=self.tenant,
            application=self.app,
            today=day_before
        )

        # 4. 昨天漏签，通过 API 补签昨天
        res = self.client.post("/api/v1/points/checkin/recheckin/", {
            "application_id": self.app.id,
            "target_date": yesterday.isoformat()
        }, format='json')
        self.assertEqual(res.status_code, 200)
        data = res.data.get("data", res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["cost_points"], 20)
        self.assertEqual(data["points_earned"], 15)  # Day 2 reward is 15
        self.assertEqual(data["current_streak"], 2)

        # 5. 校验今日打卡后连签接续为第 3 天 (+20 分)
        today_res = self.client.post("/api/v1/points/checkin/execute/", {
            "application_id": self.app.id
        }, format='json')
        self.assertEqual(today_res.status_code, 200)
        t_data = today_res.data.get("data", today_res.data)
        self.assertEqual(t_data["current_streak"], 3)
        self.assertEqual(t_data["points_earned"], 20)

        # 6. 管理员端查询用户签到总览与明细
        streak_res = self.client.get(f"/api/v1/points/checkin-streaks/?application={self.app.id}")
        self.assertEqual(streak_res.status_code, 200)
        s_data = streak_res.data.get("data", streak_res.data)
        s_items = s_data.get("results", s_data) if isinstance(s_data, dict) else s_data
        self.assertEqual(len(s_items), 1)
        self.assertEqual(s_items[0]["current_streak"], 3)
        self.assertEqual(s_items[0]["total_days"], 3)

        records_res = self.client.get(f"/api/v1/points/checkin-records/?application={self.app.id}")
        self.assertEqual(records_res.status_code, 200)
        r_data = records_res.data.get("data", records_res.data)
        r_items = r_data.get("results", r_data) if isinstance(r_data, dict) else r_data
        self.assertEqual(len(r_items), 3)
        # 应该有一条 is_recheckin=True 的记录
        self.assertTrue(any(item["is_recheckin"] for item in r_items))


