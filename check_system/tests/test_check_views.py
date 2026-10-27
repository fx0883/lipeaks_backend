"""
Check System API 视图集成测试
覆盖管理端 API (TaskCategoryViewSet, TaskViewSet, CheckRecordViewSet, CheckinCycleViewSet.stats)
与成员端 API (/member/themes/, /member/tasks/ 所有权保护, /member/checkins/ 打卡与 today 查询, /member/cycles/current/)
"""
from datetime import date, time
from unittest.mock import patch
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APITestCase

from check_system.models import CheckinCycle, CheckRecord, Task, TaskCategory
from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member, User


class CheckSystemViewsTests(APITestCase):
    """打卡系统管理端与成员端 API 集成测试"""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="CheckAPI Tenant", code="check_api_tenant")
        self.other_tenant = Tenant.objects.create(name="Other Check Tenant", code="other_check_tenant")

        self.tenant_admin = User.objects.create(
            username="check_admin",
            email="admin@check.com",
            tenant=self.tenant,
            is_admin=True,
        )
        self.member1 = Member.objects.create(
            username="check_member1",
            email="m1@check.com",
            tenant=self.tenant,
        )
        self.member2 = Member.objects.create(
            username="check_member2",
            email="m2@check.com",
            tenant=self.tenant,
        )

        # 初始化主题分类
        self.theme = TaskCategory.objects.create(
            name="运动健身",
            description="每日保持运动",
            tenant=self.tenant,
            is_system=False,
            form_type="exercise",
        )
        # 初始化任务（category 设为 None 以聚焦测试 Task 视图逻辑）
        self.task1 = Task.objects.create(
            name="每日俯卧撑",
            description="做30个俯卧撑",
            member=self.member1,
            tenant=self.tenant,
            start_date=date.today(),
            frequency_type="daily",
        )
        self.task2 = Task.objects.create(
            name="Member2专属任务",
            description="他人任务",
            member=self.member2,
            tenant=self.tenant,
            start_date=date.today(),
            frequency_type="daily",
        )

    def _auth_admin(self, admin_user=None):
        user = admin_user or self.tenant_admin
        token = generate_jwt_token(user)["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _auth_member(self, member_user=None):
        user = member_user or self.member1
        token = generate_jwt_token(user)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT_ID=str(user.tenant_id),
        )

    def test_admin_task_category_permissions_and_crud(self):
        """验证 TaskCategoryViewSet：租户管理员可写 (更新/删除)，Member 只读（写操作返回 403）"""
        url = "/api/v1/check-system/task-categories/"
        detail_url = f"{url}{self.theme.id}/"

        # Member 可读列表与详情，但写操作 (POST/PATCH/DELETE) 返回 403
        self._auth_member(self.member1)
        res_list = self.client.get(url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        res_forbidden_post = self.client.post(url, {"form_type": "work"}, format="json")
        self.assertEqual(res_forbidden_post.status_code, status.HTTP_403_FORBIDDEN)
        res_forbidden_del = self.client.delete(detail_url)
        self.assertEqual(res_forbidden_del.status_code, status.HTTP_403_FORBIDDEN)

        # 租户管理员可更新与软删除分类
        self._auth_admin()
        res_patch = self.client.patch(
            detail_url,
            {
                "form_type": "work",
                "sort_order": 5,
                "translations": {"zh-hans": {"name": "高效工作", "description": "番茄钟打卡"}},
            },
            format="json",
        )
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.theme.refresh_from_db()
        self.assertEqual(self.theme.form_type, "work")
        self.assertEqual(self.theme.sort_order, 5)

        cat_to_del = TaskCategory.objects.create(
            name="待删除分类",
            description="测试软删除",
            tenant=self.tenant,
            is_system=False,
        )
        res_del = self.client.delete(f"{url}{cat_to_del.id}/")
        self.assertEqual(res_del.status_code, status.HTTP_204_NO_CONTENT)
        cat_to_del.refresh_from_db()
        self.assertTrue(cat_to_del.is_deleted)

    def test_admin_task_viewset_isolation_and_member_crud(self):
        """验证 TaskViewSet：租户管理员可查看租户内全部任务；Member 仅看自己任务且可创建/更新/删除"""
        url = "/api/v1/check-system/tasks/"

        # 租户管理员查看租户内所有 Member 的任务（task1 + task2 = 2）
        self._auth_admin()
        res_admin_list = self.client.get(url)
        self.assertEqual(res_admin_list.status_code, status.HTTP_200_OK)
        admin_data = res_admin_list.data.get("data", res_admin_list.data)
        self.assertEqual(admin_data["count"], 2)

        # Member1 只能看到自己的任务 (count = 1)
        self._auth_member(self.member1)
        res_member_list = self.client.get(url)
        self.assertEqual(res_member_list.status_code, status.HTTP_200_OK)
        member_data = res_member_list.data.get("data", res_member_list.data)
        self.assertEqual(member_data["count"], 1)
        self.assertEqual(member_data["results"][0]["id"], self.task1.id)

        # Member1 通过 TaskViewSet 创建新任务，自动绑定 member1 与 tenant
        res_create = self.client.post(
            url,
            {
                "name": "早起喝水",
                "description": "每天一杯温水",
                "start_date": date.today().isoformat(),
                "frequency_type": "daily",
            },
            format="json",
        )
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        created_id = res_create.data.get("data", res_create.data)["id"]
        created_task = Task.objects.get(pk=created_id)
        self.assertEqual(created_task.member, self.member1)
        self.assertEqual(created_task.tenant, self.tenant)

    def test_check_record_viewset_create_and_duplicate_rejection(self):
        """验证 CheckRecordViewSet 打卡创建、重复打卡 400 拦截及 IntegrityError 兜底转换"""
        url = "/api/v1/check-system/check-records/"
        self._auth_member(self.member1)
        today_str = date.today().isoformat()

        payload = {
            "task": self.task1.id,
            "check_date": today_str,
            "check_time": "08:00:00",
            "remarks": "首次打卡完成",
        }
        res1 = self.client.post(url, payload, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # 同一天重复打卡返回 400
        res_dup = self.client.post(url, payload, format="json")
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)

        # 模拟并发场景绕过序列化器预检直接触发数据库 IntegrityError 时，视图优雅返回 400
        task_new = Task.objects.create(
            name="并发测试任务",
            member=self.member1,
            tenant=self.tenant,
            start_date=date.today(),
        )
        with patch.object(CheckRecord, "save", side_effect=IntegrityError("duplicate key")):
            res_ie = self.client.post(
                url,
                {
                    "task": task_new.id,
                    "check_date": today_str,
                    "check_time": "09:00:00",
                },
                format="json",
            )
            self.assertEqual(res_ie.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_checkin_cycle_stats_action(self):
        """验证 CheckinCycleViewSet.stats 动作准确统计周期内打卡次数、天数与完成主题数"""
        today = date.today()
        cycle = CheckinCycle.objects.create(
            member=self.member1,
            tenant=self.tenant,
            start_date=today,
            selected_themes=[self.theme.id],
            is_active=True,
        )
        CheckRecord.objects.create(
            member=self.member1,
            tenant=self.tenant,
            theme=self.theme,
            check_date=today,
            check_time=time(10, 0),
        )

        self._auth_member(self.member1)
        res = self.client.get(f"/api/v1/check-system/cycles/{cycle.id}/stats/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        stats_data = res.data.get("data", res.data)
        self.assertEqual(stats_data["cycle_id"], cycle.id)
        self.assertEqual(stats_data["total_checkins"], 1)
        self.assertEqual(stats_data["unique_days"], 1)
        self.assertEqual(stats_data["themes_completed"], 1)
        self.assertEqual(stats_data["selected_themes_count"], 1)

    def test_member_themes_endpoint_readonly_and_role_guard(self):
        """验证 /member/themes/ 仅允许 Member 访问且为只读"""
        url = "/api/v1/check-system/member/themes/"

        # 租户管理员（非 Member）访问 /member/themes/ 返回 403
        self._auth_admin()
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        # Member 正常读取主题列表
        self._auth_member(self.member1)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        themes = res.data.get("data", res.data)
        self.assertTrue(any(t["id"] == self.theme.id for t in themes))

        # Member 尝试 POST 写操作返回 405 Method Not Allowed
        res_post = self.client.post(url, {"name": "New"}, format="json")
        self.assertEqual(res_post.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_member_tasks_crud_and_ownership_protection(self):
        """验证 /member/tasks/ 任务 CRUD 及跨成员所有权保护（无法查看/修改/删除他人任务）"""
        url = "/api/v1/check-system/member/tasks/"
        self._auth_member(self.member1)

        # 创建新任务
        res_create = self.client.post(
            url,
            {
                "name": "Member1新建任务",
                "description": "坚持每天打卡",
                "start_date": date.today().isoformat(),
                "frequency_type": "daily",
            },
            format="json",
        )
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)

        # Member1 尝试访问、更新或删除 Member2 的任务 (task2) -> 被查询集隔离拦截返回 404
        other_task_url = f"{url}{self.task2.id}/"
        self.assertEqual(self.client.get(other_task_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.patch(other_task_url, {"name": "篡改名称"}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(other_task_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_member_checkins_and_today_action(self):
        """验证 /member/checkins/ 打卡、防重复及 /member/checkins/today/ 今日汇总查询"""
        checkin_url = "/api/v1/check-system/member/checkins/"
        today_url = "/api/v1/check-system/member/checkins/today/"
        self._auth_member(self.member1)
        today_str = date.today().isoformat()

        # 打卡
        res_post = self.client.post(
            checkin_url,
            {
                "task": self.task1.id,
                "check_date": today_str,
                "check_time": "07:30:00",
                "remarks": "早起打卡",
            },
            format="json",
        )
        self.assertEqual(res_post.status_code, status.HTTP_201_CREATED)

        # 重复打卡被拒绝 (400)
        res_dup = self.client.post(
            checkin_url,
            {
                "task": self.task1.id,
                "check_date": today_str,
                "check_time": "08:30:00",
            },
            format="json",
        )
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)

        # 查询今日打卡状态 /today/
        res_today = self.client.get(today_url)
        self.assertEqual(res_today.status_code, status.HTTP_200_OK)
        today_data = res_today.data.get("data", res_today.data)
        self.assertEqual(today_data["date"], today_str)
        self.assertEqual(today_data["total"], 1)
        self.assertEqual(len(today_data["records"]), 1)

    def test_member_cycles_current_action(self):
        """验证 /member/cycles/current/ 在无活跃周期时返回 404，创建活跃周期后返回 200"""
        current_url = "/api/v1/check-system/member/cycles/current/"
        cycles_url = "/api/v1/check-system/member/cycles/"
        self._auth_member(self.member1)

        # 初始无活跃周期 -> 404
        res_empty = self.client.get(current_url)
        self.assertEqual(res_empty.status_code, status.HTTP_404_NOT_FOUND)

        # 创建新周期
        res_create = self.client.post(
            cycles_url,
            {
                "start_date": date.today().isoformat(),
                "selected_themes": [self.theme.id],
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)

        # 再次查询 current -> 200
        res_current = self.client.get(current_url)
        self.assertEqual(res_current.status_code, status.HTTP_200_OK)
        cycle_data = res_current.data.get("data", res_current.data)
        self.assertTrue(cycle_data["is_active"])
        self.assertEqual(cycle_data["current_day"], 1)
