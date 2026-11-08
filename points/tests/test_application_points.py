from django.test import TestCase
from rest_framework.test import APIClient
from tenants.models import Tenant
from users.models import Member
from applications.models import Application
from points.models import (
    TenantUserProfile,
    ApplicationUserLevel,
    AppUserPointsAccount,
    TenantUserPoints
)


class ApplicationPointsTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", code="t_test", status="active")
        self.app = Application.objects.create(
            tenant=self.tenant,
            name="应用Alpha",
            code="app_alpha",
            status="active"
        )
        self.member = Member.objects.create_user(
            username="app_points_user",
            email="app_pts@example.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.profile = TenantUserProfile.objects.create(
            tenant=self.tenant,
            member=self.member,
            total_points=0,
            available_points=0
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.member)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id), HTTP_HOST='localhost')

    def test_application_level_and_account_upgrade(self):
        # 1. 创建两个等级
        lvl1 = ApplicationUserLevel.objects.create(
            tenant=self.tenant,
            application=self.app,
            level_name="青铜学员",
            level_code="BRONZE",
            level_order=1,
            min_points=0,
            max_points=499,
            icon="application/images/level_bronze.png",
            is_default=True
        )
        lvl2 = ApplicationUserLevel.objects.create(
            tenant=self.tenant,
            application=self.app,
            level_name="黄金大师",
            level_code="GOLD",
            level_order=2,
            min_points=500,
            max_points=None,
            icon="application/images/level_gold.png",
            is_default=False
        )

        # 2. 创建用户在该应用下的账户
        account = AppUserPointsAccount.objects.create(
            tenant_user_profile=self.profile,
            tenant=self.tenant,
            application=self.app,
            member=self.member,
            total_points=100,
            available_points=100,
            current_level=lvl1
        )
        self.assertEqual(account.current_level, lvl1)

        # 3. 调账接口测试 (+450分 -> 550分，应升级到 GOLD)
        res = self.client.post(f"/api/v1/points/app-accounts/{account.id}/adjust/", {
            "points": 450,
            "reason": "完成应用挑战",
            "category": "community"
        })
        self.assertEqual(res.status_code, 200)
        data = res.data.get("data", res.data)
        self.assertEqual(data["available_points"], 550)
        self.assertEqual(data["current_level_name"], "黄金大师")

        account.refresh_from_db()
        self.assertEqual(account.current_level, lvl2)
        self.assertEqual(account.total_points, 550)

        # 4. 扣减积分测试
        res_deduct = self.client.post(f"/api/v1/points/app-accounts/{account.id}/adjust/", {
            "points": -200,
            "reason": "兑换礼品"
        })
        self.assertEqual(res_deduct.status_code, 200)
        data_deduct = res_deduct.data.get("data", res_deduct.data)
        self.assertEqual(data_deduct["available_points"], 350)

        # 5. 验证流水生成
        records = TenantUserPoints.objects.filter(app_account=account)
        self.assertEqual(records.count(), 2)

    def test_preset_icons_api(self):
        res = self.client.get("/api/v1/points/app-levels/preset_icons/")
        self.assertEqual(res.status_code, 200)
        icons = res.data if isinstance(res.data, list) else res.data.get("data", [])
        filenames = [item["filename"] for item in icons]
        self.assertIn("level_bronze.png", filenames)
        self.assertIn("level_gold.png", filenames)
        self.assertIn("level_crown.png", filenames)
