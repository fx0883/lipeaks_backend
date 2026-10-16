"""
里程碑 M1 (ARCH-07, ARCH-08, ARCH-09, ARCH-10) 架构重构与解耦回归测试
"""
import os
from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from common.middleware.api_auth_middleware import APIAuthMiddleware
from common.middleware.enhanced_api_logging_middleware import EnhancedAPILoggingMiddleware
from common.authentication.jwt_auth import JWTAuthentication, generate_jwt_token
from common.exceptions import (
    BusinessException,
    custom_exception_handler,
    LicenseException as CommonLicenseException,
    PointsException as CommonPointsException,
)
from licenses.exceptions import (
    LicenseException,
    LicenseQuotaExceededException,
    LicenseExpiredException,
)
from points.exceptions import (
    PointsException,
    PointsInsufficientException,
)
from cms.exceptions import (
    CMSException,
    ArticleNotFoundException,
)
from tenants.exceptions import (
    TenantException,
    TenantNotFoundException,
)
from users.exceptions import (
    UserException,
    UserPermissionDeniedException,
)
from we_rss.views.image_proxy_views import image_proxy

User = get_user_model()


class Milestone1ArchitectureCleanTests(TestCase):
    """M1 架构清理与解耦回归测试套件"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='m1_test_user',
            password='TestPassword123!',
            status='active'
        )

    def test_arch08_empty_views_and_orders_cleaned(self):
        """[ARCH-08] 验证 4 个空 views.py 与 orders 目录已彻底移除"""
        base_dir = str(settings.BASE_DIR)
        targets = [
            os.path.join(base_dir, 'customers', 'views.py'),
            os.path.join(base_dir, 'feedbacks', 'views.py'),
            os.path.join(base_dir, 'licenses', 'views.py'),
            os.path.join(base_dir, 'users', 'views.py'),
            os.path.join(base_dir, 'orders'),
        ]
        for t in targets:
            self.assertFalse(os.path.exists(t), f"Target should be removed: {t}")

        # 验证各业务包的 views 目录包依然可正常导入
        import customers.views
        import feedbacks.views
        import licenses.views
        import users.views
        self.assertTrue(hasattr(customers.views, '__file__') or hasattr(customers.views, '__path__'))
        self.assertTrue(hasattr(feedbacks.views, '__file__') or hasattr(feedbacks.views, '__path__'))
        self.assertTrue(hasattr(licenses.views, '__file__') or hasattr(licenses.views, '__path__'))
        self.assertTrue(hasattr(users.views, '__file__') or hasattr(users.views, '__path__'))

    def test_arch09_whitenoise_autorefresh_setting(self):
        """[ARCH-09] 验证 WHITENOISE_AUTOREFRESH 修正拼写并且旧拼写不再存在"""
        self.assertIsInstance(getattr(settings, 'WHITENOISE_AUTOREFRESH', None), bool)
        self.assertIsNone(getattr(settings, 'WHITENENOISE_AUTOREFRESH', None))

        # 检查 core/settings.py 源码中的配置行
        settings_file = os.path.join(settings.BASE_DIR, 'core', 'settings.py')
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('WHITENOISE_AUTOREFRESH = DEBUG', content)
        self.assertNotIn('WHITENENOISE_AUTOREFRESH', content)

    def test_arch07_api_auth_middleware_zero_db_queries(self):
        """[ARCH-07] 验证 APIAuthMiddleware 对带 Bearer Token 请求直接放行，零数据库查询"""
        tokens = generate_jwt_token(self.user)
        access_token = tokens['access_token']

        request = self.factory.get(
            '/api/v1/test-endpoint/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )

        middleware = APIAuthMiddleware(get_response=lambda req: HttpResponse("OK"))
        # 必须不发生任何数据库查询
        with self.assertNumQueries(0):
            response = middleware.process_request(request)

        # 中间件直接放行给视图层
        self.assertIsNone(response)

    def test_arch07_jwt_authentication_sets_auth_type(self):
        """[ARCH-07] 验证 DRF JWTAuthentication 认证成功时设置 request.auth_type = 'jwt'"""
        tokens = generate_jwt_token(self.user)
        access_token = tokens['access_token']

        request = self.factory.get(
            '/api/v1/test-endpoint/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )

        authenticator = JWTAuthentication()
        auth_result = authenticator.authenticate(request)

        self.assertIsNotNone(auth_result)
        auth_user, auth_token = auth_result
        self.assertEqual(auth_user.id, self.user.id)
        self.assertEqual(getattr(request, 'auth_type', None), 'jwt')

    def test_arch07_image_proxy_auth_on_demand(self):
        """[ARCH-07] 验证非 DRF 视图 image_proxy 能按需识别有效 Bearer Token"""
        # 1. 未携带 Token 请求 -> 401
        unauthed_request = self.factory.get('/api/v1/we-rss/image-proxy/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Ftest.png')
        unauthed_resp = image_proxy(unauthed_request)
        self.assertEqual(unauthed_resp.status_code, 401)

        # 2. 携带有效 Token 请求 -> 走通认证逻辑并成功返回 200
        tokens = generate_jwt_token(self.user)
        authed_request = self.factory.get(
            '/api/v1/we-rss/image-proxy/?url=https%3A%2F%2Fmmbiz.qpic.cn%2Ftest.png',
            HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}'
        )
        with patch('we_rss.views.image_proxy_views.validate_proxy_url', return_value=('https://mmbiz.qpic.cn/test.png', None, 'mmbiz.qpic.cn')), \
             patch('we_rss.views.image_proxy_views.fetch_image') as mock_fetch:
            mock_upstream = MagicMock()
            mock_upstream.headers = {'Content-Type': 'image/jpeg', 'Content-Length': '100'}
            mock_upstream.iter_content.return_value = [b'image_data']
            mock_fetch.return_value = mock_upstream

            authed_resp = image_proxy(authed_request)
            self.assertEqual(authed_resp.status_code, 200)

    def test_arch07_enhanced_api_logging_populates_user_info_on_response(self):
        """[ARCH-07] 验证日志中间件在 process_response 中补齐视图层认证后的用户信息"""
        tokens = generate_jwt_token(self.user)
        access_token = tokens['access_token']

        request = self.factory.get(
            '/api/v1/test-endpoint/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )

        logging_middleware = EnhancedAPILoggingMiddleware(get_response=lambda req: HttpResponse("OK"))
        # 请求进入时未认证
        logging_middleware.process_request(request)
        self.assertFalse(request.api_log_data.get('authenticated', True))

        # 模拟经过视图层 DRF 认证
        request.user = self.user

        # 响应离开时
        response = HttpResponse("OK", status=200)
        with self.settings(API_LOG_SYNC=True):
            logging_middleware.process_response(request, response)

        # 验证用户信息已补齐
        self.assertTrue(request.api_log_data.get('authenticated'))
        self.assertEqual(request.api_log_data.get('user_id'), self.user.id)
        self.assertEqual(request.api_log_data.get('username'), self.user.username)

    def test_arch10_domain_exceptions_and_dip(self):
        """[ARCH-10] 验证领域专属异常继承自 BusinessException 且全局处理器能统一处理"""
        # 1. 继承检查
        self.assertTrue(issubclass(LicenseException, BusinessException))
        self.assertTrue(issubclass(LicenseQuotaExceededException, LicenseException))
        self.assertTrue(issubclass(LicenseExpiredException, LicenseException))
        self.assertTrue(issubclass(PointsException, BusinessException))
        self.assertTrue(issubclass(PointsInsufficientException, PointsException))
        self.assertTrue(issubclass(CMSException, BusinessException))
        self.assertTrue(issubclass(ArticleNotFoundException, CMSException))
        self.assertTrue(issubclass(TenantException, BusinessException))
        self.assertTrue(issubclass(TenantNotFoundException, TenantException))
        self.assertTrue(issubclass(UserException, BusinessException))
        self.assertTrue(issubclass(UserPermissionDeniedException, UserException))

        # 2. 全局异常处理器处理业务异常
        exc = LicenseQuotaExceededException(detail="许可证配额已满", quota=10)
        context = {'request': self.factory.get('/api/v1/licenses/')}
        resp = custom_exception_handler(exc, context)

        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 429)
        self.assertFalse(resp.data['success'])
        self.assertEqual(resp.data['error_code'], 'LICENSE_QUOTA_EXCEEDED')

        # 3. 验证 handler.py 没有多余的 TenantException 导入
        with open(os.path.join(settings.BASE_DIR, 'common', 'exceptions', 'handler.py'), 'r', encoding='utf-8') as f:
            handler_code = f.read()
        self.assertNotIn('from .tenant import TenantException', handler_code)
