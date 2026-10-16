"""
多租户积分系统对抗性安全测试 (SEC-05)
验证租户管理员跨租户隔离拦截、越权防篡改，以及只有全局超级管理员具备跨租户特权。
"""
from django.test import TestCase, override_settings, RequestFactory
from rest_framework.test import APIClient
from tenants.models import Tenant
from users.models import User, Member
from points.models import TenantUserProfile, TenantUserPoints
from points.api.permissions import (
    TenantUserProfilePermission,
    PointsManagementPermission,
    ensure_tenant_isolation
)
from common.authentication.jwt_auth import generate_jwt_token


@override_settings(ALLOWED_HOSTS=['*'])
class PointsTenantIsolationAdversarialTest(TestCase):
    """
    [SEC-05 对抗攻击] 测试套件
    """

    def setUp(self):
        # 创建两个独立租户
        self.tenant_a = Tenant.objects.create(name='Tenant A', code='tenant_a', status='active')
        self.tenant_b = Tenant.objects.create(name='Tenant B', code='tenant_b', status='active')

        # 创建租户 A 管理员 (普通租户管理员：is_admin=True, is_staff=True, is_super_admin=False)
        self.admin_a = User.objects.create_user(
            username='admin_a',
            password='pwd',
            tenant=self.tenant_a,
            is_admin=True
        )

        # 创建租户 B 管理员
        self.admin_b = User.objects.create_user(
            username='admin_b',
            password='pwd',
            tenant=self.tenant_b,
            is_admin=True
        )

        # 创建租户 B 成员 (攻击靶标属主)
        self.member_b = Member.objects.create_user(
            username='member_b',
            password='pwd',
            tenant=self.tenant_b
        )

        # 创建全局超级管理员 (is_super_admin=True, is_superuser=True, tenant=None)
        self.super_admin = User.objects.create_superuser(
            username='global_super_admin',
            password='pwd'
        )

        # 创建租户 B 成员积分档案 (基准 500 积分)
        self.profile_b = TenantUserProfile.objects.create(
            tenant=self.tenant_b,
            member=self.member_b,
            total_points=500,
            available_points=500
        )

        # 创建租户 B 成员积分记录
        self.record_b = TenantUserPoints.objects.create(
            tenant=self.tenant_b,
            member=self.member_b,
            tenant_user_profile=self.profile_b,
            points=500,
            balance_before=0,
            balance_after=500,
            point_type='earn',
            category='system',
            status='confirmed'
        )

        self.client = APIClient()
        self.token_admin_a = generate_jwt_token(self.admin_a)['access_token']
        self.token_super = generate_jwt_token(self.super_admin)['access_token']

    def test_tenant_a_admin_cannot_get_tenant_b_profile_detail(self):
        """
        [SEC-05-A1] 租户管理员直接跨租户读取档案：
        租户 A 管理员请求 GET /api/v1/points/profiles/{b_profile.id}/。
        期望：返回 404 Not Found (租户查询集自动隔离，查无此对象)。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')
        resp = self.client.get(f'/api/v1/points/profiles/{self.profile_b.id}/')
        self.assertIn(resp.status_code, [403, 404])

    def test_tenant_a_admin_forged_header_cross_tenant_blocked(self):
        """
        [SEC-05-A2] 租户管理员伪造 X-Tenant-ID 请求头越权：
        租户 A 管理员携带 X-Tenant-ID: {tenant_b.id} 试图强行穿透隔离。
        期望：被 TenantMiddleware 或 TenantModelViewSet 严格拦截 (400 或 403 Forbidden)。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')
        resp = self.client.get(
            f'/api/v1/points/profiles/{self.profile_b.id}/',
            HTTP_X_TENANT_ID=str(self.tenant_b.id)
        )
        self.assertIn(resp.status_code, [400, 403])

    def test_tenant_a_admin_forged_query_param_cross_tenant_blocked(self):
        """
        [SEC-05-A3] 租户管理员注入 ?tenant_id={b.id} 查询参数越权：
        期望：被拦截返回 400 或 403 Forbidden，禁止非超管跨租户切换。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')
        resp = self.client.get(f'/api/v1/points/profiles/{self.profile_b.id}/?tenant_id={self.tenant_b.id}')
        self.assertIn(resp.status_code, [400, 403])

    def test_tenant_a_admin_profile_list_does_not_leak_tenant_b_data(self):
        """
        [SEC-05-A4] 积分档案列表数据隔离泄露测试：
        租户 A 管理员查询积分档案列表。
        期望：仅返回租户 A 档案，绝对不包含租户 B 档案数据。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')
        resp = self.client.get('/api/v1/points/profiles/')
        self.assertEqual(resp.status_code, 200)

        results = resp.data.get('data', {}).get('results', [])
        returned_ids = [item['id'] for item in results]
        self.assertNotIn(self.profile_b.id, returned_ids)

    def test_tenant_a_admin_profile_list_with_forged_header_blocked(self):
        """
        [SEC-05-A5] 列表接口伪造 X-Tenant-ID 探测拦截：
        期望：被中间件拦截拒绝 (400/403)。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')
        resp = self.client.get('/api/v1/points/profiles/', HTTP_X_TENANT_ID=str(self.tenant_b.id))
        self.assertIn(resp.status_code, [400, 403])

    def test_tenant_a_admin_cannot_access_tenant_b_summary(self):
        """
        [SEC-05-A6] 租户 A 管理员尝试获取租户 B 成员积分摘要：
        GET /api/v1/points/profiles/{b.id}/summary/。
        期望：返回 404 或 403，拒绝访问。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')
        resp = self.client.get(f'/api/v1/points/profiles/{self.profile_b.id}/summary/')
        self.assertIn(resp.status_code, [403, 404])

    def test_tenant_a_admin_cannot_tamper_tenant_b_points(self):
        """
        [SEC-05-A7] 租户 A 管理员跨租户积分篡改攻击 (earn_points & adjust_points)：
        租户 A 管理员尝试向租户 B 成员发放或调整积分。
        期望：接口拒绝 (403/404)，且底层数据库中租户 B 成员的总积分严格保持 500 不变。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')

        # 尝试发放积分
        resp_earn = self.client.post(
            f'/api/v1/points/profiles/{self.profile_b.id}/earn_points/',
            {'points_amount': 100, 'category': 'system'}
        )
        self.assertIn(resp_earn.status_code, [403, 404])
        self.profile_b.refresh_from_db()
        self.assertEqual(self.profile_b.total_points, 500)

        # 尝试调整积分
        resp_adjust = self.client.post(
            f'/api/v1/points/profiles/{self.profile_b.id}/adjust_points/',
            {'points_amount': 200, 'category': 'system'}
        )
        self.assertIn(resp_adjust.status_code, [403, 404])
        self.profile_b.refresh_from_db()
        self.assertEqual(self.profile_b.total_points, 500)

    def test_tenant_a_admin_cannot_access_tenant_b_points_records(self):
        """
        [SEC-05-A8] 租户 A 管理员跨租户读取积分流水明细：
        GET /api/v1/points/points-records/{b_record.id}/。
        期望：返回 404 Not Found；带越权参数时返回 400/403。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')
        resp = self.client.get(f'/api/v1/points/points-records/{self.record_b.id}/')
        self.assertEqual(resp.status_code, 404)

        resp_param = self.client.get(f'/api/v1/points/points-records/?tenant_id={self.tenant_b.id}')
        self.assertIn(resp_param.status_code, [400, 403])

    def test_super_admin_can_access_cross_tenant_points_records(self):
        """
        [SEC-05-A9] 全局超级管理员合法跨租户访问验证：
        全局超管请求租户 B 积分流水明细。
        期望：返回 200 OK，积分数值与数据库一致。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_super}')
        resp = self.client.get(f'/api/v1/points/points-records/{self.record_b.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.get('data', {}).get('points'), 500)

        # 超管跨租户列表查询
        resp_list = self.client.get('/api/v1/points/points-records/')
        self.assertEqual(resp_list.status_code, 200)
        self.assertEqual(resp_list.data.get('data', {}).get('pagination', {}).get('count'), 1)

    def test_permissions_layer_enforces_super_admin_only_cross_tenant(self):
        """
        [SEC-05-A10] 权限策略类单体对抗测试：
        验证 TenantUserProfilePermission 与 PointsManagementPermission 对普通管理员与超管的裁决。
        """
        rf = RequestFactory()

        # 普通租户管理员请求
        req_admin_a = rf.get(f'/api/v1/points/profiles/{self.profile_b.id}/')
        req_admin_a.user = self.admin_a

        # 超管请求
        req_super = rf.get(f'/api/v1/points/profiles/{self.profile_b.id}/')
        req_super.user = self.super_admin

        # 档案权限验证
        perm_profile = TenantUserProfilePermission()
        self.assertFalse(perm_profile.has_object_permission(req_admin_a, None, self.profile_b))
        self.assertTrue(perm_profile.has_object_permission(req_super, None, self.profile_b))

        # 积分管理权限验证
        perm_points = PointsManagementPermission()
        req_admin_write = rf.post(f'/api/v1/points/profiles/{self.profile_b.id}/earn_points/')
        req_admin_write.user = self.admin_a
        self.assertFalse(perm_points.has_object_permission(req_admin_write, None, self.profile_b))

        req_super_write = rf.post(f'/api/v1/points/profiles/{self.profile_b.id}/earn_points/')
        req_super_write.user = self.super_admin
        self.assertTrue(perm_points.has_object_permission(req_super_write, None, self.profile_b))

        # 租户隔离过滤函数验证
        qs = TenantUserProfile.objects.all()
        admin_qs = ensure_tenant_isolation(req_admin_a, qs)
        self.assertNotIn(self.profile_b, list(admin_qs))

        super_qs = ensure_tenant_isolation(req_super, qs)
        self.assertIn(self.profile_b, list(super_qs))
