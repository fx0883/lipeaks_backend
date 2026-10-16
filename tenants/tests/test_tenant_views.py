"""
Tenants API 视图集成测试
覆盖超管 CRUD、搜索过滤、权限拦截、配额查询修改、配额使用率跨租户隔离、
状态机 (suspend/activate)、租户用户列表隔离与 comprehensive 聚合接口
"""
from rest_framework import status
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import Member, User


class TenantViewsTests(APITestCase):
    """租户 API 视图与权限隔离集成测试"""

    def setUp(self):
        self.super_admin = User.objects.create(
            username="super_admin_test",
            email="sa@example.com",
            is_super_admin=True,
            is_admin=True,
            is_staff=True,
            is_superuser=True,
        )
        self.tenant_a = Tenant.objects.create(
            name="Tenant Alpha",
            code="tenant_alpha",
            contact_name="Alice",
            contact_email="alice@alpha.com",
            status="active",
        )
        self.tenant_b = Tenant.objects.create(
            name="Tenant Beta",
            code="tenant_beta",
            contact_name="Bob",
            contact_email="bob@beta.com",
            status="active",
        )
        self.admin_a = User.objects.create(
            username="admin_alpha",
            email="admin@alpha.com",
            nick_name="AlphaAdmin",
            tenant=self.tenant_a,
            is_admin=True,
        )
        self.user_a = User.objects.create(
            username="staff_alpha",
            email="staff@alpha.com",
            nick_name="AlphaStaff",
            tenant=self.tenant_a,
            is_admin=False,
        )
        self.admin_b = User.objects.create(
            username="admin_beta",
            email="admin@beta.com",
            nick_name="BetaAdmin",
            tenant=self.tenant_b,
            is_admin=True,
        )
        self.member_a = Member.objects.create(
            username="member_alpha",
            email="member@alpha.com",
            tenant=self.tenant_a,
        )

    def _authenticate(self, user):
        token = generate_jwt_token(user)["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_tenant_list_and_search_filter_by_superadmin(self):
        """验证超级管理员获取租户列表及 search / status 过滤"""
        self._authenticate(self.super_admin)

        res = self.client.get("/api/v1/tenants/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 按关键词搜索
        res_search = self.client.get("/api/v1/tenants/?search=Alpha")
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        results = res_search.data.get("data", {}).get("results", res_search.data.get("results", []))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Tenant Alpha")

        # 按状态过滤
        res_status = self.client.get("/api/v1/tenants/?status=suspended")
        self.assertEqual(res_status.status_code, status.HTTP_200_OK)
        suspended_results = res_status.data.get("data", {}).get("results", res_status.data.get("results", []))
        self.assertEqual(len(suspended_results), 0)

    def test_tenant_list_forbidden_for_non_superadmin(self):
        """验证非超级管理员（租户管理员与普通非管理员用户）访问租户管理接口返回 403"""
        self._authenticate(self.admin_a)
        res_admin = self.client.get("/api/v1/tenants/")
        self.assertEqual(res_admin.status_code, status.HTTP_403_FORBIDDEN)

        self._authenticate(self.user_a)
        res_staff = self.client.get("/api/v1/tenants/")
        self.assertEqual(res_staff.status_code, status.HTTP_403_FORBIDDEN)

    def test_tenant_create_by_superadmin(self):
        """验证超级管理员创建新租户成功并自动初始化配额"""
        self._authenticate(self.super_admin)
        payload = {
            "name": "Tenant Gamma",
            "contact_name": "Charlie",
            "contact_email": "charlie@gamma.com",
            "contact_phone": "13800138000",
            "status": "active",
        }
        res = self.client.post("/api/v1/tenants/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data["success"])
        self.assertEqual(res.data["data"]["name"], "Tenant Gamma")
        self.assertIsNotNone(res.data["data"]["quota"])

    def test_tenant_retrieve_update_and_soft_delete(self):
        """验证超级管理员获取详情、更新及软删除租户"""
        self._authenticate(self.super_admin)
        url = f"/api/v1/tenants/{self.tenant_a.id}/"

        # 详情
        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        data = res_get.data.get("data", res_get.data)
        self.assertEqual(data["name"], "Tenant Alpha")

        # PATCH 更新
        res_patch = self.client.patch(url, {"contact_name": "Alice Updated"}, format="json")
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.tenant_a.refresh_from_db()
        self.assertEqual(self.tenant_a.contact_name, "Alice Updated")

        # DELETE 软删除
        res_del = self.client.delete(url)
        self.assertEqual(res_del.status_code, status.HTTP_204_NO_CONTENT)
        self.tenant_a.refresh_from_db()
        self.assertTrue(self.tenant_a.is_deleted)
        self.assertEqual(self.tenant_a.status, "deleted")

        # 已软删除租户再次获取应返回 404
        res_after = self.client.get(url)
        self.assertEqual(res_after.status_code, status.HTTP_404_NOT_FOUND)

    def test_tenant_quota_get_and_update(self):
        """验证超管获取与修改租户配额，以及非超管 403 拦截"""
        url = f"/api/v1/tenants/{self.tenant_a.id}/quota/"

        # 非超管被拒
        self._authenticate(self.admin_a)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        # 超管查询
        self._authenticate(self.super_admin)
        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data["data"]["max_users"], 10)

        # 超管更新配额
        update_payload = {
            "max_users": 50,
            "max_admins": 5,
            "max_storage_mb": 4096,
            "max_products": 300,
        }
        res_put = self.client.put(url, update_payload, format="json")
        self.assertEqual(res_put.status_code, status.HTTP_200_OK)
        self.tenant_a.quota.refresh_from_db()
        self.assertEqual(self.tenant_a.quota.max_users, 50)
        self.assertEqual(self.tenant_a.quota.max_admins, 5)
        self.assertEqual(self.tenant_a.quota.max_storage_mb, 4096)

    def test_tenant_quota_usage_isolation(self):
        """验证配额使用率接口：租户管理员仅能查本租户，查其他租户返回 403"""
        url_a = f"/api/v1/tenants/{self.tenant_a.id}/quota/usage/"
        url_b = f"/api/v1/tenants/{self.tenant_b.id}/quota/usage/"

        self._authenticate(self.admin_a)
        # 查自身租户成功
        res_own = self.client.get(url_a)
        self.assertEqual(res_own.status_code, status.HTTP_200_OK)
        self.assertIn("usage_percentage", res_own.data["data"])

        # 查他人租户返回 403
        res_other = self.client.get(url_b)
        self.assertEqual(res_other.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res_other.data["code"], 4003)

        # 超管可查任意租户
        self._authenticate(self.super_admin)
        res_sa = self.client.get(url_b)
        self.assertEqual(res_sa.status_code, status.HTTP_200_OK)

    def test_tenant_suspend_and_activate_state_machine(self):
        """验证租户 suspend / activate 状态机切换与重复操作 400 拦截"""
        self._authenticate(self.super_admin)
        suspend_url = f"/api/v1/tenants/{self.tenant_a.id}/suspend/"
        activate_url = f"/api/v1/tenants/{self.tenant_a.id}/activate/"

        # 初始 active 状态直接调用 activate 返回 400
        res_dup_act = self.client.post(activate_url)
        self.assertEqual(res_dup_act.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_dup_act.data["code"], 4000)

        # 正常暂停
        res_sus = self.client.post(suspend_url)
        self.assertEqual(res_sus.status_code, status.HTTP_200_OK)
        self.tenant_a.refresh_from_db()
        self.assertEqual(self.tenant_a.status, "suspended")

        # 重复暂停返回 400
        res_dup_sus = self.client.post(suspend_url)
        self.assertEqual(res_dup_sus.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_dup_sus.data["code"], 4000)

        # 重新激活
        res_act = self.client.post(activate_url)
        self.assertEqual(res_act.status_code, status.HTTP_200_OK)
        self.tenant_a.refresh_from_db()
        self.assertEqual(self.tenant_a.status, "active")

    def test_tenant_user_list_isolation_and_filters(self):
        """验证租户用户列表的跨租户隔离及 search / is_admin 筛选"""
        self._authenticate(self.admin_a)

        # 查询自身租户用户列表
        res_own = self.client.get(f"/api/v1/tenants/{self.tenant_a.id}/users/")
        self.assertEqual(res_own.status_code, status.HTTP_200_OK)
        data_own = res_own.data.get("data", res_own.data)
        self.assertEqual(data_own["count"], 2)

        # is_admin=true 过滤
        res_admin_only = self.client.get(f"/api/v1/tenants/{self.tenant_a.id}/users/?is_admin=true")
        data_admin = res_admin_only.data.get("data", res_admin_only.data)
        self.assertEqual(data_admin["count"], 1)
        self.assertEqual(data_admin["results"][0]["username"], "admin_alpha")

        # 跨租户查询他人用户列表：返回空结果，不泄露数据
        res_other = self.client.get(f"/api/v1/tenants/{self.tenant_b.id}/users/")
        self.assertEqual(res_other.status_code, status.HTTP_200_OK)
        data_other = res_other.data.get("data", res_other.data)
        self.assertEqual(data_other["count"], 0)
        self.assertEqual(data_other["results"], [])

    def test_tenant_comprehensive_view(self):
        """验证租户完整聚合信息接口及跨租户访问控制"""
        url_a = f"/api/v1/tenants/{self.tenant_a.id}/comprehensive/"
        url_b = f"/api/v1/tenants/{self.tenant_b.id}/comprehensive/"

        # 本租户管理员可访问本租户聚合信息
        self._authenticate(self.admin_a)
        res_own = self.client.get(url_a)
        self.assertEqual(res_own.status_code, status.HTTP_200_OK)
        self.assertEqual(res_own.data["data"]["name"], "Tenant Alpha")
        self.assertEqual(res_own.data["data"]["user_count"], 2)
        self.assertEqual(res_own.data["data"]["admin_count"], 1)
        self.assertIsNotNone(res_own.data["data"]["quota"])

        # 本租户管理员跨租户访问被拒绝 (403)
        res_other = self.client.get(url_b)
        self.assertEqual(res_other.status_code, status.HTTP_403_FORBIDDEN)

        # 超管访问不存在的租户返回 404
        self._authenticate(self.super_admin)
        res_not_found = self.client.get("/api/v1/tenants/999999/comprehensive/")
        self.assertEqual(res_not_found.status_code, status.HTTP_404_NOT_FOUND)
