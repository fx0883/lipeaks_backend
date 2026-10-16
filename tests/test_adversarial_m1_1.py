"""
Milestone M1 (ARCH-07 JWT 认证中间件解耦与架构治理) 实证攻防与对抗测试套件

本套件由实证挑战者 (challenger_m1_1) 独立编写并执行，针对以下核心领域进行高强度对抗挑战：
1. [畸形与边界 Token 攻防] 非法签名、格式错误、过期、异常用户/租户状态等各类畸形 Token 流经系统，
   必须被确定性拒绝 (401 Unauthorized)，绝不在任何中间件或视图层抛出未捕获 500。
2. [多线程并发上下文隔离] 在多线程高并发请求下，验证 jwt_auth 已认证用户复用逻辑与 ContextVar 租户隔离
   的线程安全性，确保 0 cross-request 上下文泄漏。
3. [数据库查询数严格约束] 验证带合法 Token 的请求在中间件阶段数据库查询数严格为 0，
   且在整个 HTTP 请求生命周期内用户表查询次数被严格限制为至多 1 次（杜绝双重/多次查库）。
"""
import concurrent.futures
from datetime import datetime, timedelta
import jwt
from unittest.mock import MagicMock, patch

from django.test import TestCase, TransactionTestCase, RequestFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import Member
from common.authentication.jwt_auth import JWTAuthentication, generate_jwt_token, refresh_jwt_token
from common.middleware.api_auth_middleware import APIAuthMiddleware
from common.middleware.tenant_middleware import TenantMiddleware
from common.middleware.enhanced_api_logging_middleware import EnhancedAPILoggingMiddleware
from common.utils.tenant_context import get_current_tenant, clear_current_tenant
from we_rss.views.image_proxy_views import image_proxy

User = get_user_model()


class AdversarialMalformedTokenTests(TestCase):
    """
    【挑战 1：畸形与边界 Token 对抗实测】
    测试各类非法、篡改、畸形 Token 经过系统所有中间件与视图层时，
    是否均被优雅拒绝（401 Unauthorized），且绝对不发生未捕获 500 异常。
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.client = APIClient(raise_request_exception=False)

        # 创建有效租户与充足配额
        self.tenant = Tenant.objects.create(
            name="Adv Tenant A",
            code="adv_tenant_a",
            status="active"
        )
        quota = self.tenant.ensure_quota()
        quota.max_admins = 50
        quota.max_users = 100
        quota.save()

        self.user = User.objects.create_user(
            username="adv_normal_user",
            password="StrongPassword123!",
            email="adv_normal@test.com",
            tenant=self.tenant,
            status="active"
        )

        self.valid_tokens = generate_jwt_token(self.user)
        self.valid_access_token = self.valid_tokens['access_token']

    # ------------------------------------------------------------------
    # 1. 签名伪造与密钥篡改攻击
    # ------------------------------------------------------------------
    def test_tampered_signature_rejected_401(self):
        """[攻防] 伪造密钥签发的合法格式 Token 必须被 401 拦截，严禁 500"""
        payload = {
            'user_id': self.user.id,
            'username': self.user.username,
            'exp': datetime.now() + timedelta(hours=1),
            'model_type': 'user'
        }
        forged_token = jwt.encode(payload, 'malicious_attacker_secret_key_999', algorithm='HS256')

        # 测试纯认证端点 (/api/v1/auth/verify/)
        resp1 = self.client.get(
            '/api/v1/auth/verify/',
            HTTP_AUTHORIZATION=f'Bearer {forged_token}',
            HTTP_HOST='localhost'
        )
        self.assertEqual(resp1.status_code, 401, f"伪造签名应返回 401，实际为 {resp1.status_code}")
        self.assertNotEqual(resp1.status_code, 500)

        # 测试租户隔离业务端点 (/api/v1/cms/articles/) - 携带合法租户请求头
        resp2 = self.client.get(
            '/api/v1/cms/articles/',
            HTTP_AUTHORIZATION=f'Bearer {forged_token}',
            HTTP_X_TENANT_ID=str(self.tenant.id),
            HTTP_HOST='localhost'
        )
        self.assertEqual(resp2.status_code, 401, f"业务端点伪造签名应返回 401，实际为 {resp2.status_code}")
        self.assertNotEqual(resp2.status_code, 500)

        # 测试租户隔离业务端点 - 未携带租户头时中间件拦截 (400 TENANT_ID_REQUIRED)，必须不能 500
        resp3 = self.client.get(
            '/api/v1/cms/articles/',
            HTTP_AUTHORIZATION=f'Bearer {forged_token}',
            HTTP_HOST='localhost'
        )
        self.assertIn(resp3.status_code, [400, 401])
        self.assertNotEqual(resp3.status_code, 500)

    # ------------------------------------------------------------------
    # 2. 过期 Token 攻击
    # ------------------------------------------------------------------
    def test_expired_token_rejected_401(self):
        """[攻防] 过期 Token 必须被正确拒绝 (401)，中间件与视图层不抛出未捕获 500"""
        payload = {
            'user_id': self.user.id,
            'username': self.user.username,
            'exp': datetime.now() - timedelta(days=1),
            'model_type': 'user'
        }
        expired_token = jwt.encode(payload, settings.JWT_AUTH['JWT_SECRET_KEY'], algorithm='HS256')

        resp = self.client.get(
            '/api/v1/auth/verify/',
            HTTP_AUTHORIZATION=f'Bearer {expired_token}',
            HTTP_HOST='localhost'
        )
        self.assertEqual(resp.status_code, 401)
        self.assertNotEqual(resp.status_code, 500)

    # ------------------------------------------------------------------
    # 3. 乱码与非 JWT 格式攻击
    # ------------------------------------------------------------------
    def test_random_garbage_string_rejected_401(self):
        """[攻防] 随机乱码字符串、非 Base64 特殊字符流经系统必须拒绝为 401，不能 500"""
        garbage_tokens = [
            'this_is_not_a_jwt_at_all',
            '!!!@@@###$$$%%%^^^&&&***()_+',
            'eyJhbGciOi.truncated_base64',
            'a' * 5000,  # 超长 payload
            'None',
            'null',
            '1234567890',
        ]
        for g_token in garbage_tokens:
            resp = self.client.get(
                '/api/v1/auth/verify/',
                HTTP_AUTHORIZATION=f'Bearer {g_token}',
                HTTP_HOST='localhost'
            )
            self.assertEqual(
                resp.status_code, 401,
                f"畸形 Token '{g_token[:20]}' 未被正确拒绝为 401，得到 {resp.status_code}"
            )
            self.assertNotEqual(resp.status_code, 500)

    # ------------------------------------------------------------------
    # 4. Bearer 头部格式边界畸变
    # ------------------------------------------------------------------
    def test_empty_and_variant_bearer_headers_rejected_401(self):
        """[攻防] 缺失 Token、多余空格、制表符等畸变 Authorization 头部必须拒绝为 401"""
        malformed_headers = [
            'Bearer',
            'Bearer ',
            'Bearer   ',
            'Bearer \t',
            'Bearer  \n ',
            'Bearer token1 token2 extra',
            'Token ' + self.valid_access_token,
            'Basic YWRtaW46cGFzc3dvcmQ=',
        ]
        for header in malformed_headers:
            resp = self.client.get(
                '/api/v1/auth/verify/',
                HTTP_AUTHORIZATION=header,
                HTTP_HOST='localhost'
            )
            self.assertEqual(
                resp.status_code, 401,
                f"畸变头 '{header}' 未返回 401，实际返回 {resp.status_code}"
            )
            self.assertNotEqual(resp.status_code, 500)

    # ------------------------------------------------------------------
    # 5. JWT 段数异常（非 3 段）
    # ------------------------------------------------------------------
    def test_jwt_segment_count_anomaly_rejected_401(self):
        """[攻防] 1 段、2 段、4 段 JWT 必须被规范拦截 401"""
        abnormal_tokens = [
            'eyJhbGciOiJIUzI1NiJ9',  # 只有 1 段
            'eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ',  # 只有 2 段
            'a.b.c.d',  # 4 段
            'a.b.c.d.e',  # 5 段
        ]
        for token in abnormal_tokens:
            resp = self.client.get(
                '/api/v1/auth/verify/',
                HTTP_AUTHORIZATION=f'Bearer {token}',
                HTTP_HOST='localhost'
            )
            self.assertEqual(resp.status_code, 401)
            self.assertNotEqual(resp.status_code, 500)

    # ------------------------------------------------------------------
    # 6. alg: none 漏洞注入攻击
    # ------------------------------------------------------------------
    def test_alg_none_injection_rejected_401(self):
        """[攻防] 算法为 none 的未签名攻击 Token 必须被拒绝 401"""
        import base64
        import json
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip('=')
        payload = base64.urlsafe_b64encode(json.dumps({"user_id": self.user.id, "exp": 9999999999}).encode()).decode().rstrip('=')
        none_token = f"{header}.{payload}."

        resp = self.client.get(
            '/api/v1/auth/verify/',
            HTTP_AUTHORIZATION=f'Bearer {none_token}',
            HTTP_HOST='localhost'
        )
        self.assertEqual(resp.status_code, 401)
        self.assertNotEqual(resp.status_code, 500)

    # ------------------------------------------------------------------
    # 7. Payload 异常值对抗（user_id 为 None / 不存在）
    # ------------------------------------------------------------------
    def test_malformed_payload_missing_or_nonexistent_user_id_rejected_401(self):
        """
        [攻防] Token 正确签名但 Payload 缺失 user_id、为 None 或为不存在 ID
        必须被安全拒绝（401 Unauthorized），严禁 500
        """
        test_payloads = [
            ({}, "缺失 user_id"),
            ({'user_id': None}, "user_id 为 None"),
            ({'user_id': 99999999}, "库中不存在的用户 ID"),
            ({'user_id': -1}, "负数 ID"),
        ]

        for p, desc in test_payloads:
            p_full = {
                'exp': datetime.now() + timedelta(hours=1),
                **p
            }
            tok = jwt.encode(p_full, settings.JWT_AUTH['JWT_SECRET_KEY'], algorithm='HS256')
            resp = self.client.get(
                '/api/v1/auth/verify/',
                HTTP_AUTHORIZATION=f'Bearer {tok}',
                HTTP_HOST='localhost'
            )
            self.assertEqual(
                resp.status_code, 401,
                f"异常 Payload [{desc}] ({p}) 应被安全拒绝为 401 Unauthorized，但系统返回了 {resp.status_code}！"
            )
            self.assertNotEqual(resp.status_code, 500)

    # ------------------------------------------------------------------
    # 8. [漏洞实证] 非整型 user_id（字符串/列表）触发未捕获 500 缺陷
    # ------------------------------------------------------------------
    def test_malformed_payload_non_integer_user_id_raises_uncaught_500_defect(self):
        """
        [经验实证缺陷曝光 1: JWT 认证接口]
        当合法签名的 Token 中携带非整型 user_id（如 'invalid_string' 或 [1, 2]）时，
        jwt_auth.py:84 的 `User.objects.get(pk=user_id)` 抛出未捕获的 ValueError / TypeError，
        导致 DRF 视图层直接崩溃并返回 500 Internal Server Error，而非预期的 401 Unauthorized！
        """
        bad_payloads = [
            ({'user_id': 'invalid_string'}, "字符串 user_id 导致 ValueError 500"),
            ({'user_id': [1, 2, 3]}, "列表 user_id 导致 TypeError 500"),
        ]

        for p, desc in bad_payloads:
            p_full = {
                'exp': datetime.now() + timedelta(hours=1),
                **p
            }
            tok = jwt.encode(p_full, settings.JWT_AUTH['JWT_SECRET_KEY'], algorithm='HS256')
            resp = self.client.get(
                '/api/v1/auth/verify/',
                HTTP_AUTHORIZATION=f'Bearer {tok}',
                HTTP_HOST='localhost'
            )
            # 实证断言：此处应该返回 401，但系统当前实现缺陷导致返回了 500
            self.assertEqual(
                resp.status_code, 401,
                f"【实证缺陷证实】[{desc}] 应被优雅拒绝为 401，但后端抛出未捕获异常返回了 {resp.status_code} (Internal Server Error)！"
            )

    def test_refresh_token_non_integer_user_id_raises_500_defect(self):
        """
        [经验实证缺陷曝光 2: Token 刷新接口]
        当刷新令牌包含非整型 user_id 时，refresh_jwt_token() 同样抛出未捕获的 ValueError，
        导致 /api/v1/auth/refresh/ 返回 500 Internal Server Error，而非规范的 400/401。
        """
        bad_refresh = jwt.encode(
            {'token_type': 'refresh', 'user_id': 'invalid_string', 'exp': datetime.now() + timedelta(days=7)},
            settings.JWT_AUTH['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        resp = self.client.post(
            '/api/v1/auth/refresh/',
            {'refresh_token': bad_refresh},
            format='json',
            HTTP_HOST='localhost'
        )
        self.assertIn(
            resp.status_code, [400, 401],
            f"【实证缺陷证实】非整型 user_id 刷新令牌应被拒绝为 400/401，但系统返回了 {resp.status_code} (Internal Server Error)！"
        )

    # ------------------------------------------------------------------
    # 9. 用户状态异常对抗（禁用、软删除、子账号、租户禁用）
    # ------------------------------------------------------------------
    def test_abnormal_user_states_rejected_401(self):
        """[攻防] 状态异常（禁用/删除/租户封禁/子账号）的用户合法 Token 必须被 401 拦截"""
        # Case A: 用户 is_active = False
        inactive_user = User.objects.create_user(
            username="adv_inactive_user",
            password="Password123!",
            is_active=False,
            status="active",
            tenant=self.tenant
        )
        tok_inactive = generate_jwt_token(inactive_user)['access_token']
        resp = self.client.get('/api/v1/auth/verify/', HTTP_AUTHORIZATION=f'Bearer {tok_inactive}', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 401)

        # Case B: 用户 status = 'disabled'
        disabled_user = User.objects.create_user(
            username="adv_disabled_user",
            password="Password123!",
            status="disabled",
            tenant=self.tenant
        )
        tok_disabled = generate_jwt_token(disabled_user)['access_token']
        resp = self.client.get('/api/v1/auth/verify/', HTTP_AUTHORIZATION=f'Bearer {tok_disabled}', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 401)

        # Case C: 用户 is_deleted = True
        deleted_user = User.objects.create_user(
            username="adv_deleted_user",
            password="Password123!",
            is_deleted=True,
            status="active",
            tenant=self.tenant
        )
        tok_deleted = generate_jwt_token(deleted_user)['access_token']
        resp = self.client.get('/api/v1/auth/verify/', HTTP_AUTHORIZATION=f'Bearer {tok_deleted}', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 401)

        # Case D: 子账号 Member (parent is not None)
        parent_member = Member.objects.create_user(
            username="adv_parent_member",
            password="Password123!",
            email="parent@member.com",
            status="active",
            tenant=self.tenant
        )
        sub_member = Member.objects.create_user(
            username="adv_sub_member",
            password="Password123!",
            email="sub@member.com",
            status="active",
            tenant=self.tenant,
            parent=parent_member
        )
        tok_sub = generate_jwt_token(sub_member)['access_token']
        resp = self.client.get('/api/v1/auth/verify/', HTTP_AUTHORIZATION=f'Bearer {tok_sub}', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 401)

        # Case E: 用户租户 status = 'inactive'
        inactive_tenant = Tenant.objects.create(name="Inactive T", code="inact_t", status="inactive")
        user_in_bad_tenant = User.objects.create_user(
            username="adv_bad_tenant_user",
            password="Password123!",
            status="active",
            tenant=inactive_tenant
        )
        tok_bad_tenant = generate_jwt_token(user_in_bad_tenant)['access_token']
        resp = self.client.get('/api/v1/auth/verify/', HTTP_AUTHORIZATION=f'Bearer {tok_bad_tenant}', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 401)

    # ------------------------------------------------------------------
    # 10. 纯 Django 视图 image_proxy 异常 Token 健壮性
    # ------------------------------------------------------------------
    def test_image_proxy_handles_all_malformed_tokens_without_500(self):
        """[攻防] 非 DRF 函数视图 image_proxy 遇到各种畸形 Token 必须返回 401，严禁 500"""
        malformed_samples = [
            'invalid_token',
            'Bearer ',
            'Bearer forged.token.signature',
            'Bearer a.b',
        ]
        for sample in malformed_samples:
            header_val = sample if sample.startswith('Bearer') else f'Bearer {sample}'
            req = self.factory.get(
                '/api/v1/we-rss/image-proxy/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Ftest.png',
                HTTP_AUTHORIZATION=header_val
            )
            resp = image_proxy(req)
            self.assertEqual(resp.status_code, 401, f"image_proxy 应返回 401，实际返回 {resp.status_code}")


class AdversarialConcurrencyIsolationTests(TransactionTestCase):
    """
    【挑战 2：多线程并发请求下的线程安全与上下文隔离实测】
    测试高并发多线程场景下：
    1. 不同租户、不同用户的请求并发交叉执行，验证 jwt_auth 用户复用逻辑不会发生 cross-request 泄漏；
    2. 工作线程在处理完一次请求后立即处理下一次匿名或另一用户请求，验证无残留状态污染。
    """

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

        # 配置 WAL 与超时，支持多线程并发读取
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA busy_timeout = 10000;")

        # 创建 3 个独立租户
        self.tenant_a = Tenant.objects.create(name="Concurrency A", code="conc_a", status="active")
        self.tenant_a.ensure_quota()
        self.tenant_b = Tenant.objects.create(name="Concurrency B", code="conc_b", status="active")
        self.tenant_b.ensure_quota()
        self.tenant_c = Tenant.objects.create(name="Concurrency C", code="conc_c", status="active")
        self.tenant_c.ensure_quota()

        # 创建 3 个对应用户
        self.user_a = User.objects.create_user(
            username="user_alpha",
            password="Password123!",
            tenant=self.tenant_a,
            status="active"
        )
        self.user_b = User.objects.create_user(
            username="user_beta",
            password="Password123!",
            tenant=self.tenant_b,
            status="active"
        )
        self.user_c = User.objects.create_user(
            username="user_gamma",
            password="Password123!",
            tenant=self.tenant_c,
            status="active"
        )

        self.token_a = generate_jwt_token(self.user_a)['access_token']
        self.token_b = generate_jwt_token(self.user_b)['access_token']
        self.token_c = generate_jwt_token(self.user_c)['access_token']

    def tearDown(self):
        connection.close()
        super().tearDown()

    def test_adversarial_multithread_request_isolation(self):
        """
        [攻防] 10 个工作线程并发执行 100 次交叉请求，
        验证每个请求的认证用户与租户上下文严格对应，0 交叉污染
        """
        def execute_authenticated_flow(user_expected_id, token, tenant_expected_id):
            """执行一次完整的请求与认证流，并在子线程中验证上下文隔离"""
            connection.close()
            try:
                authenticator = JWTAuthentication()
                req = self.factory.get(
                    '/api/v1/auth/verify/',
                    HTTP_AUTHORIZATION=f'Bearer {token}'
                )
                # 模拟中间件通过
                api_auth = APIAuthMiddleware(get_response=lambda r: None)
                api_auth.process_request(req)

                # 视图层执行认证
                auth_res = authenticator.authenticate(req)
                if auth_res is None:
                    return False, "Authentication returned None for valid token"
                auth_user, auth_tok = auth_res

                # 模拟视图层设置 req.user
                req.user = auth_user

                # 再次调用验证复用机制
                reuse_res = authenticator.authenticate(req)
                reused_user, _ = reuse_res

                # 校验隔离性
                if auth_user.id != user_expected_id:
                    return False, f"User ID mismatch: expected {user_expected_id}, got {auth_user.id}"
                if reused_user.id != user_expected_id:
                    return False, f"Reused User ID mismatch: expected {user_expected_id}, got {reused_user.id}"
                if auth_user.tenant.id != tenant_expected_id:
                    return False, f"Tenant mismatch: expected {tenant_expected_id}, got {auth_user.tenant.id}"

                return True, "OK"
            except Exception as e:
                return False, f"Exception in worker thread: {str(e)}"
            finally:
                connection.close()

        def execute_anonymous_flow():
            """执行一次匿名请求流"""
            connection.close()
            try:
                authenticator = JWTAuthentication()
                req = self.factory.get('/api/v1/auth/verify/')
                auth_res = authenticator.authenticate(req)
                if auth_res is not None:
                    return False, f"Anonymous request unexpectedly authenticated: {auth_res}"
                if getattr(req, 'auth_type', None) is not None:
                    return False, f"req.auth_type should be None for anonymous, got {req.auth_type}"
                return True, "OK"
            except Exception as e:
                return False, f"Exception in anonymous thread: {str(e)}"
            finally:
                connection.close()

        test_matrix = []
        for _ in range(25):
            test_matrix.append((self.user_a.id, self.token_a, self.tenant_a.id))
            test_matrix.append((self.user_b.id, self.token_b, self.tenant_b.id))
            test_matrix.append((self.user_c.id, self.token_c, self.tenant_c.id))

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for uid, tok, tid in test_matrix:
                futures.append(executor.submit(execute_authenticated_flow, uid, tok, tid))
            for _ in range(25):
                futures.append(executor.submit(execute_anonymous_flow))

            for fut in concurrent.futures.as_completed(futures):
                results.append(fut.result())

        failures = [msg for success, msg in results if not success]
        self.assertEqual(len(failures), 0, f"并发请求上下文隔离存在失败项: {failures}")
        self.assertEqual(len(results), 100, "100 次并发测试必须全部完成")

    def test_adversarial_worker_thread_reuse_no_context_bleed(self):
        """
        [攻防] 模拟同一工作线程连续处理 用户A -> 匿名 -> 用户B -> 畸形Token，
        验证线程局部变量与 contextvars 不发生残留泄漏
        """
        authenticator = JWTAuthentication()
        tenant_middleware = TenantMiddleware(get_response=lambda r: None)

        for cycle in range(10):
            # Step 1: 用户 A 请求
            req_a = self.factory.get(
                '/api/v1/cms/articles/',
                HTTP_AUTHORIZATION=f'Bearer {self.token_a}',
                HTTP_X_TENANT_ID=str(self.tenant_a.id)
            )
            tenant_middleware.process_request(req_a)
            auth_res_a = authenticator.authenticate(req_a)
            self.assertEqual(auth_res_a[0].id, self.user_a.id)
            tenant_middleware.process_response(req_a, None)
            self.assertIsNone(get_current_tenant(), "处理响应后 current_tenant 必须清空")

            # Step 2: 同一线程立即处理匿名请求
            req_anon = self.factory.get('/api/v1/cms/articles/')
            tenant_middleware.process_request(req_anon)
            auth_res_anon = authenticator.authenticate(req_anon)
            self.assertIsNone(auth_res_anon, "匿名请求不可继承上一请求的认证态")
            self.assertIsNone(getattr(req_anon, 'auth_type', None))
            tenant_middleware.process_response(req_anon, None)
            self.assertIsNone(get_current_tenant())

            # Step 3: 同一线程处理 用户 B 请求
            req_b = self.factory.get(
                '/api/v1/cms/articles/',
                HTTP_AUTHORIZATION=f'Bearer {self.token_b}',
                HTTP_X_TENANT_ID=str(self.tenant_b.id)
            )
            tenant_middleware.process_request(req_b)
            auth_res_b = authenticator.authenticate(req_b)
            self.assertEqual(auth_res_b[0].id, self.user_b.id, "用户 B 请求不能继承用户 A")
            tenant_middleware.process_response(req_b, None)
            self.assertIsNone(get_current_tenant())


class AdversarialDBQueryLimitsTests(TestCase):
    """
    【挑战 3：数据库查询数严格约束实测】
    1. 中间件阶段数据库查询数确实为 0；
    2. 全请求周期内用户实体查询被严格限制（杜绝双重解码与重复查库）。
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.client = APIClient()

        self.tenant = Tenant.objects.create(name="DB Limit Tenant", code="db_lim_t", status="active")
        self.tenant.ensure_quota()

        self.user = User.objects.create_user(
            username="db_lim_user",
            password="Password123!",
            tenant=self.tenant,
            status="active"
        )
        self.tokens = generate_jwt_token(self.user)
        self.access_token = self.tokens['access_token']

        # 创建 Member 用户
        self.member = Member.objects.create_user(
            username="db_lim_member",
            password="Password123!",
            email="member@dblim.com",
            tenant=self.tenant,
            status="active"
        )
        self.member_tokens = generate_jwt_token(self.member)
        self.member_access_token = self.member_tokens['access_token']

    def test_api_auth_middleware_strictly_zero_db_queries_all_paths(self):
        """
        [实测] APIAuthMiddleware 必须对所有路径（无论带不带 Token、合法或非法）
        在中间件阶段数据库查询数严格为 0 (assertNumQueries(0))
        """
        middleware = APIAuthMiddleware(get_response=lambda r: None)
        test_requests = [
            # 合法 Bearer Token
            self.factory.get('/api/v1/auth/verify/', HTTP_AUTHORIZATION=f'Bearer {self.access_token}'),
            self.factory.get('/api/v1/cms/articles/', HTTP_AUTHORIZATION=f'Bearer {self.access_token}'),
            self.factory.get('/api/v1/licenses/', HTTP_AUTHORIZATION=f'Bearer {self.access_token}'),
            # 非法/过期 Token
            self.factory.get('/api/v1/auth/verify/', HTTP_AUTHORIZATION='Bearer invalid_token_123'),
            # 无 Token
            self.factory.get('/api/v1/auth/verify/'),
            # 静态与文档白名单
            self.factory.get('/static/admin/css/base.css'),
            self.factory.get('/api/v1/schema/'),
        ]

        for req in test_requests:
            with self.assertNumQueries(0):
                res = middleware.process_request(req)
                self.assertIsNone(res)

    def test_cached_jwt_auth_strictly_zero_queries_on_repeated_calls(self):
        """
        [实测] jwt_auth 用户复用机制：
        在请求绑定了认证用户后，后续在同一请求内重复调用必须为 0 次数据库查询 (assertNumQueries(0))
        """
        authenticator = JWTAuthentication()
        req = self.factory.get('/api/v1/auth/verify/', HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        # 首次认证
        user, token = authenticator.authenticate(req)
        self.assertEqual(user.id, self.user.id)
        self.assertEqual(getattr(req, 'auth_type', None), 'jwt')
        req.user = user

        # 再次调用：触发 raw_req 缓存复用，严格 0 次数据库查询
        with self.assertNumQueries(0):
            reused_user, reused_tok = authenticator.authenticate(req)
            self.assertEqual(reused_user.id, self.user.id)

        # 第三次调用：依然严格 0 次数据库查询
        with self.assertNumQueries(0):
            reused_user_3, _ = authenticator.authenticate(req)
            self.assertEqual(reused_user_3.id, self.user.id)

    def test_full_request_cycle_user_query_bounded_to_at_most_one(self):
        """
        [实测] 全请求生命周期对抗检验：
        通过 APIClient 发起完整 HTTP 请求至受保护视图，
        整周期内针对用户表 (user) 的查询次数被严格限制为至多 1 次（杜绝双重查询）
        """
        with CaptureQueriesContext(connection) as queries_ctx:
            resp = self.client.get(
                '/api/v1/auth/verify/',
                HTTP_AUTHORIZATION=f'Bearer {self.access_token}',
                HTTP_HOST='localhost'
            )

        self.assertEqual(resp.status_code, 200)

        # 统计所有涉及 user 模型的 SELECT 查询
        user_queries = [
            q['sql'] for q in queries_ctx.captured_queries
            if 'FROM "user"' in q['sql'] or 'FROM `user`' in q['sql'] or 'FROM users_user' in q['sql']
        ]

        # 严格断言：用户认证查库次数严格 <= 1（杜绝了原来的双倍冗余查库）
        self.assertLessEqual(
            len(user_queries), 1,
            f"全生命周期内用户表查询次数超标 (实际 {len(user_queries)} 次, 预期至多 1 次): {user_queries}"
        )
        self.assertEqual(len(user_queries), 1, "全生命周期内用户表查询次数应恰好为 1 次")

    def test_full_request_cycle_member_query_bounded_to_at_most_one(self):
        """
        [实测] Member 类型用户全生命周期查库次数同样被严格限制为至多 1 次
        """
        with CaptureQueriesContext(connection) as queries_ctx:
            resp = self.client.get(
                '/api/v1/auth/verify/',
                HTTP_AUTHORIZATION=f'Bearer {self.member_access_token}',
                HTTP_HOST='localhost'
            )

        self.assertEqual(resp.status_code, 200)

        member_queries = [
            q['sql'] for q in queries_ctx.captured_queries
            if 'FROM "member"' in q['sql'] or 'FROM `member`' in q['sql'] or 'FROM users_member' in q['sql']
        ]

        self.assertLessEqual(
            len(member_queries), 1,
            f"全生命周期内 Member 表查询次数超标 (实际 {len(member_queries)} 次, 预期至多 1 次): {member_queries}"
        )
        self.assertEqual(len(member_queries), 1, "全生命周期内 Member 表查询次数应恰好为 1 次")
