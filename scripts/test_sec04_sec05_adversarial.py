"""
SEC-04 & SEC-05 对抗性安全攻击渗透检验脚本
用于经验实证 Worker M1 的安全修复成效
执行方式：
python scripts/test_sec04_sec05_adversarial.py
"""
import os
import sys

# 将项目根目录添加到 sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import django

# 设置测试环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_test')
django.setup()

from django.test.runner import DiscoverRunner
from django.test import TestCase, override_settings, RequestFactory
from rest_framework.test import APIClient
from tenants.models import Tenant
from users.models import User, Member
from notifications.models import Notification, NotificationRecipient
from points.models import TenantUserProfile, TenantUserPoints
from points.api.permissions import (
    TenantUserProfilePermission,
    PointsManagementPermission,
    ensure_tenant_isolation
)
from common.authentication.jwt_auth import generate_jwt_token


@override_settings(ALLOWED_HOSTS=['*'])
class AdversarialPenetrationTestSuite(TestCase):
    """
    经验实证对抗攻击执行套件
    """

    def setUp(self):
        # 1. 租户初始化
        self.tenant_a = Tenant.objects.create(name='Tenant A Corp', code='tenant_a', status='active')
        self.tenant_b = Tenant.objects.create(name='Tenant B Ltd', code='tenant_b', status='active')

        # 2. 用户主体构建
        # 租户 A 管理员 (普通租户管理)
        self.admin_a = User.objects.create_user(
            username='attacker_admin_a',
            password='Password123!',
            tenant=self.tenant_a,
            is_admin=True
        )

        # 租户 A 成员
        self.member_a = Member.objects.create_user(
            username='victim_member_a',
            password='Password123!',
            tenant=self.tenant_a
        )

        # 租户 B 管理员
        self.admin_b = User.objects.create_user(
            username='admin_b',
            password='Password123!',
            tenant=self.tenant_b,
            is_admin=True
        )

        # 租户 B 成员 (主要攻击目标)
        self.member_b = Member.objects.create_user(
            username='target_member_b',
            password='Password123!',
            tenant=self.tenant_b
        )

        # 全局超级管理员 (唯一允许跨租户)
        self.super_admin = User.objects.create_superuser(
            username='global_super_admin',
            password='Password123!'
        )

        # 3. 业务数据靶标构建
        # 通知系统靶标
        self.notice_a = Notification.objects.create(
            tenant=self.tenant_a,
            title='Notice for Member A',
            content='Content for Member A',
            status='published'
        )
        self.recip_a = NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=self.notice_a,
            member=self.member_a,
            is_read=False
        )

        self.notice_b = Notification.objects.create(
            tenant=self.tenant_b,
            title='Confidential Strategy Notice',
            content='Super Secret Internal Memo for Tenant B',
            status='published'
        )
        self.recip_b = NotificationRecipient.objects.create(
            tenant=self.tenant_b,
            notification=self.notice_b,
            member=self.member_b,
            is_read=False
        )

        # 积分系统靶标
        self.profile_b = TenantUserProfile.objects.create(
            tenant=self.tenant_b,
            member=self.member_b,
            total_points=1000,
            available_points=1000
        )
        self.record_b = TenantUserPoints.objects.create(
            tenant=self.tenant_b,
            member=self.member_b,
            tenant_user_profile=self.profile_b,
            points=1000,
            balance_before=0,
            balance_after=1000,
            point_type='earn',
            category='system',
            status='confirmed'
        )

        self.client = APIClient()
        self.token_member_a = generate_jwt_token(self.member_a)['access_token']
        self.token_admin_a = generate_jwt_token(self.admin_a)['access_token']
        self.token_super = generate_jwt_token(self.super_admin)['access_token']

    def test_sec04_adversarial_matrix(self):
        """SEC-04 对抗攻击完整矩阵验证"""
        print('\n=== [SEC-04] 对抗攻击实测开始 ===')

        # 1. 匿名用户尝试读取用户 B 通知详情
        r_anon_detail = self.client.get(f'/api/v1/notifications/{self.recip_b.id}/')
        print(f'[-] 攻击 1 (匿名请求目标详情): HTTP {r_anon_detail.status_code} (期望: 400/401/403)')
        self.assertIn(r_anon_detail.status_code, [400, 401, 403])
        self.recip_b.refresh_from_db()
        self.assertFalse(self.recip_b.is_read)
        self.assertIsNone(self.recip_b.read_at)
        print('    [PASS] 防御生效：匿名访问被拦截，is_read 保持 False，read_at 保持 None')

        # 2. 匿名用户尝试伪造租户头读取详情
        r_anon_header = self.client.get(
            f'/api/v1/notifications/{self.recip_b.id}/',
            HTTP_X_TENANT_ID=str(self.tenant_b.id)
        )
        print(f'[-] 攻击 2 (匿名携带伪造 X-Tenant-ID): HTTP {r_anon_header.status_code} (期望: 401/403)')
        self.assertIn(r_anon_header.status_code, [401, 403])
        self.recip_b.refresh_from_db()
        self.assertFalse(self.recip_b.is_read)
        print('    [PASS] 防御生效：未认证请求被拦截，状态未被篡改')

        # 3. 匿名用户尝试注入 member_id 遍历通知列表
        r_anon_list = self.client.get(f'/api/v1/notifications/?member_id={self.member_b.id}')
        print(f'[-] 攻击 3 (匿名注入 member_id 遍历列表): HTTP {r_anon_list.status_code} (期望: 400/401/403)')
        self.assertIn(r_anon_list.status_code, [400, 401, 403])
        print('    [PASS] 防御生效：未认证用户无法遍历列表')

        # 4. 用户 A (Member A) 尝试 IDOR 读取用户 B 通知详情
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_member_a}')
        r_idor_detail = self.client.get(f'/api/v1/notifications/{self.recip_b.id}/')
        print(f'[-] 攻击 4 (用户 A 水平越权 IDOR 读取用户 B 详情): HTTP {r_idor_detail.status_code} (期望: 403/404)')
        self.assertIn(r_idor_detail.status_code, [403, 404])
        self.recip_b.refresh_from_db()
        self.assertFalse(self.recip_b.is_read)
        self.assertIsNone(self.recip_b.read_at)
        print('    [PASS] 防御生效：返回 404/403，用户 B 通知未被窃取，且 is_read 未被篡改')

        # 5. 用户 A 尝试带 query 参数 ?member_id={b.id}
        r_idor_list = self.client.get(f'/api/v1/notifications/?member_id={self.member_b.id}')
        print(f'[-] 攻击 5 (用户 A 注入 ?member_id 越权查询列表): HTTP {r_idor_list.status_code} (期望: 200且结果完全隔离)')
        self.assertEqual(r_idor_list.status_code, 200)
        items = r_idor_list.data.get('data', {}).get('results', [])
        returned_ids = [item['id'] for item in items]
        self.assertNotIn(self.recip_b.id, returned_ids)
        self.assertIn(self.recip_a.id, returned_ids)
        print('    [PASS] 防御生效：列表强制绑定当前登录用户，目标通知 0 泄漏')

        # 6. 用户 A 尝试越权标记用户 B 通知为已读
        r_idor_mark = self.client.post(f'/api/v1/notifications/{self.recip_b.id}/read/')
        print(f'[-] 攻击 6 (用户 A 尝试 mark_read 用户 B 通知): HTTP {r_idor_mark.status_code} (期望: 403/404)')
        self.assertIn(r_idor_mark.status_code, [403, 404])
        self.recip_b.refresh_from_db()
        self.assertFalse(self.recip_b.is_read)
        print('    [PASS] 防御生效：越权标记被拦截，目标通知 is_read 仍为 False')

        # 7. 用户 A 调用 read-all 测试是否越权影响用户 B
        r_read_all = self.client.post('/api/v1/notifications/read-all/')
        print(f'[-] 攻击 7 (用户 A 调用 read-all 污染测试): HTTP {r_read_all.status_code}')
        self.assertEqual(r_read_all.status_code, 200)
        self.recip_a.refresh_from_db()
        self.assertTrue(self.recip_a.is_read)
        self.recip_b.refresh_from_db()
        self.assertFalse(self.recip_b.is_read)
        print('    [PASS] 防御生效：仅标记自身通知，目标租户成员通知完全未受污染')

        # 8. 用户 A 尝试探测用户 B 未读数量
        r_count = self.client.get(f'/api/v1/notifications/unread-count/?member_id={self.member_b.id}')
        print(f'[-] 攻击 8 (用户 A 探测未读数量注入): HTTP {r_count.status_code}')
        self.assertEqual(r_count.status_code, 200)
        unread_count = r_count.data.get('data', {}).get('unread_count')
        self.assertEqual(unread_count, 0) # member_a 刚刚 read_all 了，所以是 0
        print('    [PASS] 防御生效：返回当前用户真实未读数，未泄漏目标未读数')

    def test_sec05_adversarial_matrix(self):
        """SEC-05 对抗攻击完整矩阵验证"""
        print('\n=== [SEC-05] 对抗攻击实测开始 ===')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')

        # 1. 租户 A 管理员直接跨租户请求租户 B 档案
        r_admin_detail = self.client.get(f'/api/v1/points/profiles/{self.profile_b.id}/')
        print(f'[-] 攻击 1 (租户 A 管理员跨租户读取档案详情): HTTP {r_admin_detail.status_code} (期望: 403/404)')
        self.assertIn(r_admin_detail.status_code, [403, 404])
        print('    [PASS] 防御生效：跨租户档案读取被拦截')

        # 2. 租户 A 管理员伪造 X-Tenant-ID 请求头
        r_fake_header = self.client.get(
            f'/api/v1/points/profiles/{self.profile_b.id}/',
            HTTP_X_TENANT_ID=str(self.tenant_b.id)
        )
        print(f'[-] 攻击 2 (租户 A 管理员携带伪造 X-Tenant-ID): HTTP {r_fake_header.status_code} (期望: 400/403)')
        self.assertIn(r_fake_header.status_code, [400, 403])
        print('    [PASS] 防御生效：多租户中间件严格拒绝非自身租户头')

        # 3. 租户 A 管理员注入 ?tenant_id 参数
        r_fake_param = self.client.get(
            f'/api/v1/points/profiles/{self.profile_b.id}/?tenant_id={self.tenant_b.id}'
        )
        print(f'[-] 攻击 3 (租户 A 管理员注入 ?tenant_id): HTTP {r_fake_param.status_code} (期望: 400/403)')
        self.assertIn(r_fake_param.status_code, [400, 403])
        print('    [PASS] 防御生效：查询参数跨租户请求被拦截')

        # 4. 租户 A 管理员查询档案列表数据隔离
        r_list = self.client.get('/api/v1/points/profiles/')
        print(f'[-] 攻击 4 (租户 A 管理员列表查询): HTTP {r_list.status_code}')
        self.assertEqual(r_list.status_code, 200)
        items = r_list.data.get('data', {}).get('results', [])
        returned_ids = [item['id'] for item in items]
        self.assertNotIn(self.profile_b.id, returned_ids)
        print('    [PASS] 防御生效：列表仅包含所属租户档案，租户 B 档案 0 泄露')

        # 5. 租户 A 管理员尝试跨租户获取积分摘要
        r_summary = self.client.get(f'/api/v1/points/profiles/{self.profile_b.id}/summary/')
        print(f'[-] 攻击 5 (租户 A 管理员获取租户 B 积分摘要): HTTP {r_summary.status_code} (期望: 403/404)')
        self.assertIn(r_summary.status_code, [403, 404])
        print('    [PASS] 防御生效：跨租户积分摘要请求被拒绝')

        # 6. 租户 A 管理员尝试向租户 B 成员发放积分 (篡改积分)
        r_tamper_earn = self.client.post(
            f'/api/v1/points/profiles/{self.profile_b.id}/earn_points/',
            {'points_amount': 500, 'category': 'system'}
        )
        print(f'[-] 攻击 6 (租户 A 管理员尝试跨租户 earn_points 篡改): HTTP {r_tamper_earn.status_code} (期望: 403/404)')
        self.assertIn(r_tamper_earn.status_code, [403, 404])
        self.profile_b.refresh_from_db()
        self.assertEqual(self.profile_b.total_points, 1000)
        print(f'    [PASS] 防御生效：接口拒绝，数据库总积分仍为 {self.profile_b.total_points}，防篡改成功')

        # 7. 租户 A 管理员尝试调整租户 B 积分
        r_tamper_adj = self.client.post(
            f'/api/v1/points/profiles/{self.profile_b.id}/adjust_points/',
            {'points_amount': -500, 'category': 'system'}
        )
        print(f'[-] 攻击 7 (租户 A 管理员尝试跨租户 adjust_points 扣除): HTTP {r_tamper_adj.status_code} (期望: 403/404)')
        self.assertIn(r_tamper_adj.status_code, [403, 404])
        self.profile_b.refresh_from_db()
        self.assertEqual(self.profile_b.total_points, 1000)
        print(f'    [PASS] 防御生效：接口拒绝，数据库总积分仍为 {self.profile_b.total_points}，防篡改成功')

        # 8. 租户 A 管理员尝试读取租户 B 积分流水记录
        r_record = self.client.get(f'/api/v1/points/points-records/{self.record_b.id}/')
        print(f'[-] 攻击 8 (租户 A 管理员读取租户 B 积分流水明细): HTTP {r_record.status_code} (期望: 404)')
        self.assertEqual(r_record.status_code, 404)
        print('    [PASS] 防御生效：积分流水严格按所属租户隔离')

        # 9. 超级管理员跨租户能力验证
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_super}')
        r_super = self.client.get(f'/api/v1/points/points-records/{self.record_b.id}/')
        print(f'[-] 权限 9 (全局超管跨租户访问流水明细): HTTP {r_super.status_code} (期望: 200)')
        self.assertEqual(r_super.status_code, 200)
        self.assertEqual(r_super.data.get('data', {}).get('points'), 1000)
        print('    [PASS] 契约成立：全局超级管理员合法拥有跨租户管理权限')

        # 10. 权限层单体对比断言
        rf = RequestFactory()
        req_admin_a = rf.get(f'/api/v1/points/profiles/{self.profile_b.id}/')
        req_admin_a.user = self.admin_a

        req_super = rf.get(f'/api/v1/points/profiles/{self.profile_b.id}/')
        req_super.user = self.super_admin

        perm = TenantUserProfilePermission()
        self.assertFalse(perm.has_object_permission(req_admin_a, None, self.profile_b))
        self.assertTrue(perm.has_object_permission(req_super, None, self.profile_b))

        qs = TenantUserProfile.objects.all()
        admin_qs = ensure_tenant_isolation(req_admin_a, qs)
        super_qs = ensure_tenant_isolation(req_super, qs)
        self.assertNotIn(self.profile_b, list(admin_qs))
        self.assertIn(self.profile_b, list(super_qs))
        print('    [PASS] 权限策略层严格断言：租户管理员无跨租户权限，仅超管具备跨租户权限')


def run():
    print('===============================================================')
    print(' 开始执行 SEC-04 & SEC-05 对抗性安全攻击渗透全自动化验证')
    print('===============================================================')
    runner = DiscoverRunner(verbosity=0)
    suite = runner.test_suite()
    suite.addTest(AdversarialPenetrationTestSuite('test_sec04_adversarial_matrix'))
    suite.addTest(AdversarialPenetrationTestSuite('test_sec05_adversarial_matrix'))
    cfg = runner.setup_databases()
    res = runner.run_suite(suite)
    runner.teardown_databases(cfg)

    print('\n===============================================================')
    if res.wasSuccessful():
        print(' 渗透攻击测试结果：全部攻击向量均被成功拦截，防御体系有效！')
        print(' 最终经验实证裁决结论：APPROVE')
        print('===============================================================')
        sys.exit(0)
    else:
        print(' 渗透攻击测试结果：存在未被拦截的安全绕过漏洞！')
        print(' 最终经验实证裁决结论：REQUEST_CHANGES')
        print('===============================================================')
        sys.exit(1)


if __name__ == '__main__':
    run()
