"""
通知系统对抗性安全测试 (SEC-04)
验证未授权/匿名访问拦截、IDOR 水平越权拦截、member_id 参数注入防护以及状态防篡改。
"""
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from tenants.models import Tenant
from users.models import User, Member
from notifications.models import Notification, NotificationRecipient
from common.authentication.jwt_auth import generate_jwt_token


@override_settings(ALLOWED_HOSTS=['*'])
class NotificationAdversarialSecurityTest(TestCase):
    """
    [SEC-04 对抗攻击] 测试套件
    """

    def setUp(self):
        # 创建两个隔离租户
        self.tenant_a = Tenant.objects.create(name='Tenant A', code='tenant_a', status='active')
        self.tenant_b = Tenant.objects.create(name='Tenant B', code='tenant_b', status='active')

        # 创建租户成员
        self.member_a = Member.objects.create_user(username='member_a', password='pwd', tenant=self.tenant_a)
        self.member_b = Member.objects.create_user(username='member_b', password='pwd', tenant=self.tenant_b)

        # 创建普通系统用户（非 Member）
        # 使用不与当前 Member ID 冲突的 ID (例如 9999) 检验非 Member 拒绝
        self.user_non_member = User(id=9999, username='user_non_member', tenant=self.tenant_a)
        self.user_non_member.set_password('pwd')
        self.user_non_member.save()

        # 为租户 A 创建通知与接收记录
        self.notice_a = Notification.objects.create(
            tenant=self.tenant_a,
            title='Tenant A Notice',
            content='Content A',
            status='published'
        )
        self.recip_a = NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=self.notice_a,
            member=self.member_a,
            is_read=False
        )

        # 为租户 B 创建通知与接收记录 (攻击靶标)
        self.notice_b = Notification.objects.create(
            tenant=self.tenant_b,
            title='Tenant B Secret Notice',
            content='Content B Confidential',
            status='published'
        )
        self.recip_b = NotificationRecipient.objects.create(
            tenant=self.tenant_b,
            notification=self.notice_b,
            member=self.member_b,
            is_read=False
        )

        self.client = APIClient()
        self.token_member_a = generate_jwt_token(self.member_a)['access_token']
        self.token_non_member = generate_jwt_token(self.user_non_member)['access_token']

    def test_anonymous_cannot_access_notification_detail(self):
        """
        [SEC-04-A1] 匿名未认证攻击：
        未携带凭证尝试通过 GET 读取租户 B 成员通知详情。
        期望：返回 400/401/403 拦截，且通知在数据库中保持未读状态 (is_read=False, read_at=None)。
        """
        resp = self.client.get(f'/api/v1/notifications/{self.recip_b.id}/')
        self.assertIn(resp.status_code, [400, 401, 403])

        self.recip_b.refresh_from_db()
        self.assertFalse(self.recip_b.is_read)
        self.assertIsNone(self.recip_b.read_at)

    def test_anonymous_with_tenant_header_cannot_access_detail(self):
        """
        [SEC-04-A2] 匿名伪造租户头攻击：
        携带 X-Tenant-ID 尝试越权读取通知详情。
        期望：返回 401/403 未授权拦截，通知状态未篡改。
        """
        resp = self.client.get(
            f'/api/v1/notifications/{self.recip_b.id}/',
            HTTP_X_TENANT_ID=str(self.tenant_b.id)
        )
        self.assertIn(resp.status_code, [401, 403])

        self.recip_b.refresh_from_db()
        self.assertFalse(self.recip_b.is_read)
        self.assertIsNone(self.recip_b.read_at)

    def test_anonymous_cannot_list_notifications_or_inject_member_id(self):
        """
        [SEC-04-A3] 匿名列表渗透与参数遍历：
        未认证用户尝试 GET /api/v1/notifications/?member_id={b.id}。
        期望：返回 400/401/403 拦截，不可获取任何数据。
        """
        resp = self.client.get(f'/api/v1/notifications/?member_id={self.member_b.id}')
        self.assertIn(resp.status_code, [400, 401, 403])

    def test_member_a_cannot_read_member_b_notification_detail(self):
        """
        [SEC-04-A4] 认证用户水平越权 (IDOR) 攻击：
        用户 A (Member A) 尝试 GET 读取用户 B (Member B) 的通知接收记录 ID。
        期望：返回 404 Not Found (对象不在当前用户的 queryset 中)。
        状态保护断言：用户 B 的通知 is_read 绝不被触发修改为 True，read_at 仍为 None。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_member_a}')
        resp = self.client.get(f'/api/v1/notifications/{self.recip_b.id}/')
        self.assertIn(resp.status_code, [403, 404])

        self.recip_b.refresh_from_db()
        self.assertFalse(self.recip_b.is_read)
        self.assertIsNone(self.recip_b.read_at)

    def test_member_a_query_param_member_id_injection_blocked(self):
        """
        [SEC-04-A5] 成员端列表查询参数注入攻击：
        用户 A 在查询通知列表时附带 ?member_id={b.id} 试图横向遍历。
        期望：接口忽略越权参数，仅返回当前登录用户 A 自身的通知，绝对不包含用户 B 的通知。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_member_a}')
        resp = self.client.get(f'/api/v1/notifications/?member_id={self.member_b.id}')
        self.assertEqual(resp.status_code, 200)

        results = resp.data.get('data', {}).get('results', [])
        returned_ids = [item['id'] for item in results]
        self.assertNotIn(self.recip_b.id, returned_ids)
        self.assertIn(self.recip_a.id, returned_ids)

    def test_member_a_cannot_mark_read_member_b_notification(self):
        """
        [SEC-04-A6] 显式标记他人通知已读攻击：
        用户 A 尝试 POST /api/v1/notifications/{b.id}/read/。
        期望：返回 404 Not Found，用户 B 的通知 is_read 保持 False。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_member_a}')
        resp = self.client.post(f'/api/v1/notifications/{self.recip_b.id}/read/')
        self.assertIn(resp.status_code, [403, 404])

        self.recip_b.refresh_from_db()
        self.assertFalse(self.recip_b.is_read)

    def test_member_a_read_all_does_not_affect_member_b(self):
        """
        [SEC-04-A7] 批量标记已读越权影响攻击：
        用户 A 调用 POST /api/v1/notifications/read-all/。
        期望：仅将用户 A 自身的通知标记为已读，用户 B 的通知状态完全不受污染。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_member_a}')
        resp = self.client.post('/api/v1/notifications/read-all/')
        self.assertEqual(resp.status_code, 200)

        self.recip_a.refresh_from_db()
        self.assertTrue(self.recip_a.is_read)

        self.recip_b.refresh_from_db()
        self.assertFalse(self.recip_b.is_read)

    def test_member_a_unread_count_query_injection_ignored(self):
        """
        [SEC-04-A8] 未读数量统计越权探测攻击：
        用户 A 请求 GET /api/v1/notifications/unread-count/?member_id={b.id}。
        期望：返回用户 A 自身的未读数量，不泄漏用户 B 的未读计数。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_member_a}')
        resp = self.client.get(f'/api/v1/notifications/unread-count/?member_id={self.member_b.id}')
        self.assertEqual(resp.status_code, 200)

        # member_a 此时有 1 条未读通知
        count = resp.data.get('data', {}).get('unread_count')
        self.assertEqual(count, 1)

    def test_non_member_user_blocked_by_permission(self):
        """
        [SEC-04-A9] 非 Member 认证账户访问权限拦截：
        普通 User 账户尝试访问成员通知接口。
        期望：被 MemberNotificationPermission 拦截拒绝 (403 Forbidden)。
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_non_member}')
        resp = self.client.get('/api/v1/notifications/')
        self.assertEqual(resp.status_code, 403)
