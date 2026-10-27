"""
LiPeaks M2 里程碑对抗验证测试套件 (Challenger 2)
聚焦验证：会员认证 (Login)、Token 签发、凭据对抗、租户隔离、受保护接口鉴权 (Members Me)、Token 刷新

执行环境: 本地 MySQL81 (multi_tenant_db)
"""
import os
import sys
import unittest
import django
import jwt
from datetime import datetime, timedelta

# 确保工程根目录在 sys.path 中
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 初始化 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.conf import settings
from tenants.models import Tenant
from users.models import Member, User


class M2MemberAuthAdversarialTestSuite(unittest.TestCase):
    """M2 会员认证与鉴权完整对抗实机验证"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client(HTTP_HOST='localhost')
        cls.tenant_id = 100
        cls.tenant_code = 'espressox'
        cls.username = 'testmember'
        cls.valid_password = 'Password123!'
        cls.wrong_password = 'WrongPassword999!'

        # 校验数据库前置环境
        try:
            cls.tenant = Tenant.objects.get(code=cls.tenant_code)
            cls.member = Member.objects.get(tenant=cls.tenant, username=cls.username)
        except Exception as e:
            raise RuntimeError(f"测试前置数据不存在，请先运行 seed_espressox_data.py: {e}")

    # =========================================================================
    # 1. 正向功能验证 (Happy Path)
    # =========================================================================

    def test_01_valid_login_happy_path(self):
        """【正向】测试账号带正确的 X-Tenant-ID 成功登录，返回 200 及完整 JWT 与会员实体"""
        resp = self.client.post(
            '/api/v1/auth/login/',
            data={'username': self.username, 'password': self.valid_password},
            content_type='application/json',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertEqual(resp.status_code, 200, f"登录失败响应: {resp.content}")
        data = resp.json()

        self.assertTrue(data.get('success'), "返回体 success 应为 True")
        self.assertEqual(data.get('code'), 2000, "成功返回业务码应为 2000")
        self.assertIn('data', data)

        res_data = data['data']
        self.assertIn('token', res_data, "必须包含 token (access token)")
        self.assertIn('refresh_token', res_data, "必须包含 refresh_token")
        self.assertIn('user', res_data, "必须包含 user 实体")

        # 校验 JWT Payload
        access_token = res_data['token']
        payload = jwt.decode(
            access_token,
            settings.JWT_AUTH['JWT_SECRET_KEY'],
            algorithms=[settings.JWT_AUTH['JWT_ALGORITHM']]
        )
        self.assertEqual(payload['user_id'], self.member.id)
        self.assertEqual(payload['username'], self.username)
        self.assertEqual(payload['model_type'], 'member')

        # 校验 User 实体结构
        user_data = res_data['user']
        self.assertEqual(user_data['id'], self.member.id)
        self.assertEqual(user_data['username'], self.username)
        self.assertEqual(user_data['email'], self.member.email)
        self.assertTrue(user_data['is_member'])
        self.assertFalse(user_data['is_admin'])
        self.assertFalse(user_data['is_super_admin'])
        self.assertEqual(user_data['tenant_id'], self.tenant_id)
        self.assertEqual(user_data['tenant_name'], self.tenant.name)

    def test_02_access_protected_endpoint_with_valid_token(self):
        """【正向】使用有效 Access Token 访问 GET /api/v1/members/me/，返回 200 及个人资料"""
        # 先登录获取 token
        login_resp = self.client.post(
            '/api/v1/auth/login/',
            data={'username': self.username, 'password': self.valid_password},
            content_type='application/json',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        token = login_resp.json()['data']['token']

        # 请求受保护接口
        resp = self.client.get(
            '/api/v1/members/me/',
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertEqual(resp.status_code, 200, f"获取个人资料失败: {resp.content}")
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('code'), 2000)
        user_info = data['data']
        self.assertEqual(user_info['id'], self.member.id)
        self.assertEqual(user_info['username'], self.username)
        self.assertEqual(user_info['email'], self.member.email)
        self.assertEqual(user_info['tenant'], self.tenant_id)

    # =========================================================================
    # 2. 凭据对抗攻击测试 (Credential Attacks)
    # =========================================================================

    def test_03_wrong_password_rejected(self):
        """【对抗】使用错误密码登录，必须准确返回 HTTP 401 且 code=4002"""
        resp = self.client.post(
            '/api/v1/auth/login/',
            data={'username': self.username, 'password': self.wrong_password},
            content_type='application/json',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertFalse(data.get('success'))
        self.assertEqual(data.get('code'), 4002)
        self.assertEqual(data.get('message'), "Invalid username/email or password")

    def test_04_nonexistent_user_rejected(self):
        """【对抗】使用不存在的用户登录，必须返回 HTTP 401 且 code=4002"""
        resp = self.client.post(
            '/api/v1/auth/login/',
            data={'username': 'ghost_user_not_exist', 'password': self.valid_password},
            content_type='application/json',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertFalse(data.get('success'))
        self.assertEqual(data.get('code'), 4002)

    def test_05_empty_credentials_rejected(self):
        """【对抗】空密码或空用户名登录，必须拦截并拒绝"""
        resp1 = self.client.post(
            '/api/v1/auth/login/',
            data={'username': self.username, 'password': ''},
            content_type='application/json',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertIn(resp1.status_code, [400, 401])

        resp2 = self.client.post(
            '/api/v1/auth/login/',
            data={'username': '', 'password': self.valid_password},
            content_type='application/json',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertIn(resp2.status_code, [400, 401])

    def test_06_sql_injection_payload_rejected(self):
        """【对抗】SQL 注入字符串登录，框架安全防御并返回 401，不得出现 500 崩溃"""
        resp = self.client.post(
            '/api/v1/auth/login/',
            data={'username': "' OR '1'='1' --", 'password': "' OR '1'='1' --"},
            content_type='application/json',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json().get('code'), 4002)

    # =========================================================================
    # 3. 租户隔离与 Header 对抗测试 (Tenant Boundary Attacks)
    # =========================================================================

    def test_07_missing_tenant_header_rejected_with_4001(self):
        """【对抗】成员账号登录若缺失 X-Tenant-ID 请求头，必须被识别并拦截为 4100/4001 (TenantHeaderInvalidOrMissing/TENANT_ERROR)"""
        resp = self.client.post(
            '/api/v1/auth/login/',
            data={'username': self.username, 'password': self.valid_password},
            content_type='application/json'
        )
        # 缺失头触发 TenantHeaderInvalidOrMissing，状态码应为 400 且业务码 4100 (TENANT_ERROR)
        self.assertIn(resp.status_code, [400, 401])
        data = resp.json()
        self.assertEqual(data.get('code'), 4100)

    def test_08_cross_tenant_login_rejected(self):
        """【对抗】携带错误/不属于本成员的租户 ID (如 99999) 尝试登录，必须返回 401"""
        resp = self.client.post(
            '/api/v1/auth/login/',
            data={'username': self.username, 'password': self.valid_password},
            content_type='application/json',
            HTTP_X_TENANT_ID='99999'
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json().get('code'), 4002)

    def test_09_malformed_tenant_header_rejected(self):
        """【对抗】携带非整数或恶意畸形 X-Tenant-ID，必须安全拦截并返回 4100/4002，绝不出现 500 崩溃"""
        # 非整型恶意注入头：触发 TenantHeaderInvalidOrMissing (4100)
        for malformed in ['abc', '100; DROP TABLE users', '3.14']:
            resp = self.client.post(
                '/api/v1/auth/login/',
                data={'username': self.username, 'password': self.valid_password},
                content_type='application/json',
                HTTP_X_TENANT_ID=malformed
            )
            self.assertIn(resp.status_code, [400, 401])
            self.assertEqual(resp.json().get('code'), 4100)

        # 负数整型租户头：有效整数但租户不存在，被成员查找判定为 not_found 触发 4002 (401)
        resp_neg = self.client.post(
            '/api/v1/auth/login/',
            data={'username': self.username, 'password': self.valid_password},
            content_type='application/json',
            HTTP_X_TENANT_ID='-100'
        )
        self.assertEqual(resp_neg.status_code, 401)
        self.assertEqual(resp_neg.json().get('code'), 4002)

    # =========================================================================
    # 4. 受保护接口鉴权对抗 (Protected Endpoint Attacks: /api/v1/members/me/)
    # =========================================================================

    def test_10_protected_endpoint_no_token_rejected(self):
        """【对抗】未携带 Authorization 访问受保护接口，必须返回 HTTP 401"""
        resp = self.client.get(
            '/api/v1/members/me/',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertEqual(resp.status_code, 401)

    def test_11_protected_endpoint_malformed_token_rejected(self):
        """【对抗】携带格式错乱/伪造字符串 Token 访问，必须返回 HTTP 401"""
        resp = self.client.get(
            '/api/v1/members/me/',
            HTTP_AUTHORIZATION='Bearer totally_invalid_jwt_garbage_string',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertEqual(resp.status_code, 401)

    def test_12_protected_endpoint_forged_secret_token_rejected(self):
        """【对抗】使用错误密钥签发的伪造 JWT，必须验证签名失败并返回 HTTP 401"""
        forged_payload = {
            'user_id': self.member.id,
            'username': self.username,
            'exp': datetime.now() + timedelta(hours=1),
            'model_type': 'member',
            'is_admin': False,
            'is_super_admin': False,
            'is_staff': False
        }
        forged_token = jwt.encode(forged_payload, 'attacker_fake_secret_key_666', algorithm='HS256')

        resp = self.client.get(
            '/api/v1/members/me/',
            HTTP_AUTHORIZATION=f'Bearer {forged_token}',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertEqual(resp.status_code, 401)

    def test_13_protected_endpoint_expired_token_rejected(self):
        """【对抗】携带已过期的 Token 访问受保护接口，必须返回 HTTP 401"""
        expired_payload = {
            'user_id': self.member.id,
            'username': self.username,
            'exp': datetime.now() - timedelta(days=1),  # 昨天过期
            'model_type': 'member',
            'is_admin': False,
            'is_super_admin': False,
            'is_staff': False
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.JWT_AUTH['JWT_SECRET_KEY'],
            algorithm=settings.JWT_AUTH['JWT_ALGORITHM']
        )
        resp = self.client.get(
            '/api/v1/members/me/',
            HTTP_AUTHORIZATION=f'Bearer {expired_token}',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertEqual(resp.status_code, 401)

    # =========================================================================
    # 5. Token 刷新链路对抗测试 (Refresh Token Flow)
    # =========================================================================

    def test_14_token_refresh_successful(self):
        """【正向】使用登录获取的 refresh_token 换发新 access_token 成功"""
        login_resp = self.client.post(
            '/api/v1/auth/login/',
            data={'username': self.username, 'password': self.valid_password},
            content_type='application/json',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        refresh_token = login_resp.json()['data']['refresh_token']

        # 请求刷新
        resp = self.client.post(
            '/api/v1/auth/refresh/',
            data={'refresh_token': refresh_token},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200, f"Token 刷新失败: {resp.content}")
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('code'), 2000)
        new_token = data['data']['token']

        # 验证新 Token 可以正常请求受保护接口
        me_resp = self.client.get(
            '/api/v1/members/me/',
            HTTP_AUTHORIZATION=f'Bearer {new_token}',
            HTTP_X_TENANT_ID=str(self.tenant_id)
        )
        self.assertEqual(me_resp.status_code, 200)

    def test_15_invalid_token_refresh_rejected(self):
        """【对抗】使用伪造/非法的 refresh_token 刷新，必须返回 HTTP 400/401"""
        resp = self.client.post(
            '/api/v1/auth/refresh/',
            data={'refresh_token': 'fake_garbage_refresh_token'},
            content_type='application/json'
        )
        self.assertIn(resp.status_code, [400, 401])


if __name__ == '__main__':
    unittest.main()
