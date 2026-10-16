"""
Milestone M2 Security Hardening & Robustness Comprehensive Regression Test Suite
覆盖范围:
- SEC-07: 审计日志敏感字段递归脱敏与落盘防护
- SEC-09: 真实 IP 安全提取与密码重置双维度 (IP+Email) 频控防爆破
- SEC-10: CSRF 保护加固与许可证敏感端点防跨站攻击
- PERF-09: We-RSS 分页规范化与 PaginatedDict 迭代器兼容
- BUG-LOGIC-09: Member 账号注销全量社交互动关联清理 (ArticleLike, MemberLike, MemberFollow)
- BUG-LOGIC-10: 批量许可证分配除零边界防御
- BUG-LOGIC-11/12: 文章阅读统计并发原子递增更新 (F 表达式)
"""
import json
import inspect
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.contrib.messages.storage.fallback import FallbackStorage
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status

from common.utils.sensitive import mask_sensitive_data, is_sensitive_key
from common.utils.network import get_client_ip
from common.pagination import PaginatedDict
from common.models import APILog
from common.middleware.enhanced_api_logging_middleware import EnhancedAPILoggingMiddleware
from tenants.models import Tenant
from users.models import Member, User
from users.views.member_password_reset_views import (
    MemberPasswordResetRequestPageView,
    MemberPasswordResetFormView
)
from users.views.member_delete_account_views import MemberDeleteAccountConfirmView
from interactions.models import ArticleLike, MemberLike, MemberFollow
from cms.models import Article, ArticleStatistics
from cms.views.base_views import ArticleViewSet
from points.services.license_service import TenantAwareLicenseAssignmentService
import licenses.views.member_views as member_license_views


class TestSEC07SensitiveMasking(TestCase):
    """SEC-07: 递归敏感字段脱敏与 APILog 存储安全性"""

    def setUp(self):
        cache.clear()
        self.tenant = Tenant.objects.create(name="Tenant Log", code="tlog", status="active")

    def test_is_sensitive_key(self):
        """测试敏感键精确匹配与白名单放行"""
        # 敏感键识别
        self.assertTrue(is_sensitive_key("password"))
        self.assertTrue(is_sensitive_key("old_password"))
        self.assertTrue(is_sensitive_key("new_password_confirm"))
        self.assertTrue(is_sensitive_key("token"))
        self.assertTrue(is_sensitive_key("access_token"))
        self.assertTrue(is_sensitive_key("secret"))
        self.assertTrue(is_sensitive_key("api_key"))
        self.assertTrue(is_sensitive_key("authorization"))

        # 白名单安全键识别（严禁误杀）
        self.assertFalse(is_sensitive_key("status_code"))
        self.assertFalse(is_sensitive_key("error_code"))
        self.assertFalse(is_sensitive_key("code"))
        self.assertFalse(is_sensitive_key("sort_key"))
        self.assertFalse(is_sensitive_key("cache_key"))
        self.assertFalse(is_sensitive_key("token_type"))

    def test_mask_sensitive_data_nested_structures(self):
        """测试字典、列表、嵌套 JSON 字符串和循环引用的脱敏机制"""
        raw_data = {
            "username": "alice",
            "password": "SuperSecretPassword123!",
            "token": "jwt.token.string",
            "code": "SUCCESS",
            "status_code": 200,
            "profile": {
                "secret_key": "sk-123456",
                "sort_key": "created_at",
                "nested_tokens": ["token_val", {"sub_password": "123"}]
            },
            "meta_json": json.dumps({"app_secret": "my-secret-value", "name": "app1"})
        }

        masked = mask_sensitive_data(raw_data)

        self.assertEqual(masked["username"], "alice")
        self.assertEqual(masked["password"], "******")
        self.assertEqual(masked["token"], "******")
        self.assertEqual(masked["code"], "SUCCESS")
        self.assertEqual(masked["status_code"], 200)
        self.assertEqual(masked["profile"]["secret_key"], "******")
        self.assertEqual(masked["profile"]["sort_key"], "created_at")
        self.assertEqual(masked["profile"]["nested_tokens"][1]["sub_password"], "******")

        # 嵌套 JSON 字符串也被成功反序列化并脱敏后重新序列化
        meta_dict = json.loads(masked["meta_json"])
        self.assertEqual(meta_dict["app_secret"], "******")
        self.assertEqual(meta_dict["name"], "app1")

    def test_mask_circular_reference_protection(self):
        """测试循环引用保护不会导致 RecursionError"""
        node = {"name": "loop"}
        node["self"] = node

        masked = mask_sensitive_data(node)
        self.assertEqual(masked["name"], "loop")
        self.assertEqual(masked["self"], "<circular-reference>")

    @override_settings(API_LOG_SYNC=True)
    def test_enhanced_api_logging_middleware_masks_saved_log(self):
        """测试经过 EnhancedAPILoggingMiddleware 后，数据库 APILog 中的敏感字段 100% 脱敏"""
        factory = RequestFactory()
        payload = {
            "username": "testuser",
            "password": "MyPlainPassword!",
            "token": "plain_token_123",
            "status_code": 200
        }
        request = factory.post(
            "/api/v1/auth/login/",
            data=json.dumps(payload),
            content_type="application/json"
        )
        request.META["REMOTE_ADDR"] = "192.168.1.50"

        from django.http import JsonResponse
        response = JsonResponse({"access_token": "secret_jwt_access", "status": "ok"})
        middleware = EnhancedAPILoggingMiddleware(get_response=lambda r: response)

        middleware.process_request(request)
        middleware.process_response(request, response)

        # 验证数据库落盘记录
        log_entry = APILog.objects.filter(request_path="/api/v1/auth/login/").latest("id")
        self.assertEqual(log_entry.request_body["password"], "******")
        self.assertEqual(log_entry.request_body["token"], "******")
        self.assertEqual(log_entry.request_body["status_code"], 200)
        self.assertEqual(log_entry.response_body["access_token"], "******")
        self.assertEqual(log_entry.ip_address, "192.168.1.50")


class TestSEC09SEC10ClientIPAndRateLimitingAndCSRF(TestCase):
    """SEC-09 & SEC-10: 客户端 IP 解析防伪造、双维度频控与 CSRF 加固"""

    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Tenant Sec", code="tsec", status="active")
        self.member = Member.objects.create_user(
            username="sec_member",
            email="sec_member@example.com",
            password="StrongPassword123!",
            tenant=self.tenant
        )

    def test_get_client_ip_security(self):
        """测试 get_client_ip：优先 X-Real-IP、REMOTE_ADDR，拒绝盲信 X-Forwarded-For 最左侧伪造"""
        # 1. 优先信任受信代理 X-Real-IP
        req1 = self.factory.get("/")
        req1.META["HTTP_X_REAL_IP"] = "10.0.0.1"
        req1.META["REMOTE_ADDR"] = "127.0.0.1"
        req1.META["HTTP_X_FORWARDED_FOR"] = "1.1.1.1, 2.2.2.2"
        self.assertEqual(get_client_ip(req1), "10.0.0.1")

        # 2. 无 X-Real-IP 时使用 REMOTE_ADDR
        req2 = self.factory.get("/")
        req2.META["REMOTE_ADDR"] = "10.0.0.2"
        self.assertEqual(get_client_ip(req2), "10.0.0.2")

        # 3. 仅有 X-Forwarded-For 时取最右侧反向代理 IP（防客户端左侧注入伪造）
        req3 = self.factory.get("/")
        del req3.META["REMOTE_ADDR"]
        req3.META["HTTP_X_FORWARDED_FOR"] = "attacker_spoofed_ip, trusted_proxy_ip"
        self.assertEqual(get_client_ip(req3), "trusted_proxy_ip")

    def test_member_password_reset_email_rate_limiting(self):
        """测试密码重置视图双维度频控：同一目标邮箱无法通过更换伪造 IP 绕过限流"""
        view = MemberPasswordResetRequestPageView()
        view.tenant = self.tenant
        view.tenant_id = self.tenant.id

        from users.forms import MemberPasswordResetRequestForm
        form_data = {
            "email": "sec_member@example.com",
            "tenant_id": str(self.tenant.id)
        }

        # 连续发送 3 次请求（每次即便 IP 不同）
        for i in range(3):
            req = self.factory.post(f"/api/v1/members/password-reset/?tenant_id={self.tenant.id}", data=form_data)
            req.META["REMOTE_ADDR"] = f"192.168.1.{i+1}"
            req.session = {}
            setattr(req, '_messages', FallbackStorage(req))
            view.request = req

            form = MemberPasswordResetRequestForm(data=form_data)
            self.assertTrue(form.is_valid())
            res = view.form_valid(form)
            self.assertEqual(res.status_code, 302)  # 重定向到成功提示页

        # 第 4 次请求，即便换全新 IP，因为针对同一邮箱，必须被限流拦截
        req4 = self.factory.post(f"/api/v1/members/password-reset/?tenant_id={self.tenant.id}", data=form_data)
        req4.META["REMOTE_ADDR"] = "203.0.113.99"
        req4.session = {}
        setattr(req4, '_messages', FallbackStorage(req4))
        view.request = req4

        form4 = MemberPasswordResetRequestForm(data=form_data)
        self.assertTrue(form4.is_valid())
        res4 = view.form_valid(form4)
        # 被拦截，返回 form_invalid (200 重新渲染表单)
        self.assertEqual(res4.status_code, 200)

    def test_auth_views_password_reset_request_email_rate_limiting(self):
        """测试 API 密码重置端点同样具备目标邮箱频限防御 (返回 429)"""
        req_data = {
            "email": "sec_member@example.com",
            "account_type": "member",
            "tenant_id": self.tenant.id
        }

        # 预先设置该邮箱的请求计数已达 3 次
        cache.set("password_reset_request:email:sec_member@example.com", 3, 600)

        resp = self.client.post(
            reverse("auth:password-reset-request"),
            req_data,
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant.id)
        )
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_member_views_csrf_exempt_removed(self):
        """测试 licenses/views/member_views.py 中的 apply_trial_license 与 unbind_device 源码已彻底清除 @csrf_exempt"""
        source = inspect.getsource(member_license_views)
        self.assertNotIn("@csrf_exempt", source)
        self.assertNotIn("from django.views.decorators.csrf import csrf_exempt", source)


class TestPERF09WeRssPaginationAndPaginatedDict(TestCase):
    """PERF-09: We-RSS 分页规范化与 PaginatedDict 迭代器支持"""

    def test_paginated_dict_supports_iteration_and_dict_access(self):
        """测试 PaginatedDict 具备字典特性且完美支持列表推导式迭代"""
        items = [{"id": 1, "source_id": "feed-1"}, {"id": 2, "source_id": "feed-2"}]
        data_dict = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": items
        }

        pdict = PaginatedDict(data_dict, items)

        # 字典特性
        self.assertEqual(pdict["count"], 2)
        self.assertEqual(pdict["results"], items)

        # 整数下标与长度兼容
        self.assertEqual(len(pdict), 2)
        self.assertEqual(pdict[0]["source_id"], "feed-1")

        # 列表推导式迭代遍历（关键修复项）
        source_ids = [item["source_id"] for item in pdict]
        self.assertEqual(source_ids, ["feed-1", "feed-2"])

        # 集合推导式遍历
        id_set = {item["id"] for item in pdict}
        self.assertEqual(id_set, {1, 2})

    def test_we_rss_viewset_inherits_pagination_class(self):
        """测试 WeRssTenantModelViewSet 与 WeRssTenantGenericViewSet 不再覆盖 pagination_class 为 None"""
        from we_rss.views.base import WeRssTenantModelViewSet, WeRssTenantGenericViewSet
        self.assertNotEqual(WeRssTenantModelViewSet.pagination_class, None)
        self.assertNotEqual(WeRssTenantGenericViewSet.pagination_class, None)


class TestBUGLOGIC09to12Safeguards(TestCase):
    """BUG-LOGIC-09~12: 账号注销全量清理、除零防御与阅读量原子递增"""

    def setUp(self):
        cache.clear()
        self.tenant = Tenant.objects.create(name="Tenant Logic", code="tlogic", status="active")
        self.member_a = Member.objects.create_user(
            username="member_a",
            email="ma@logic.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.member_b = Member.objects.create_user(
            username="member_b",
            email="mb@logic.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.article = Article.objects.create(
            title="Logic Test Article",
            slug="logic-test-art",
            content="Logic article content",
            member=self.member_b,
            tenant=self.tenant
        )

    def test_bug_logic_09_account_deletion_cleans_all_interactions(self):
        """测试注销账号时彻底删除 ArticleLike, MemberLike(双向), MemberFollow(双向) 无 FieldError"""
        member_a_id = self.member_a.id

        # 创建涉及 member_a 的互动记录
        ArticleLike.objects.create(article=self.article, from_member=self.member_a, tenant=self.tenant)
        MemberLike.objects.create(from_member=self.member_a, to_member=self.member_b, tenant=self.tenant)
        MemberLike.objects.create(from_member=self.member_b, to_member=self.member_a, tenant=self.tenant)
        MemberFollow.objects.create(follower=self.member_a, following=self.member_b, tenant=self.tenant)
        MemberFollow.objects.create(follower=self.member_b, following=self.member_a, tenant=self.tenant)

        # 执行删除方法
        view = MemberDeleteAccountConfirmView()
        deleted_data = view.delete_member_data(self.member_a)

        # 验证关联记录已完全清除（使用 id 查询，因为 member_a 对象已执行 delete()）
        self.assertEqual(ArticleLike.objects.filter(from_member_id=member_a_id).count(), 0)
        self.assertEqual(MemberLike.objects.filter(from_member_id=member_a_id).count(), 0)
        self.assertEqual(MemberLike.objects.filter(to_member_id=member_a_id).count(), 0)
        self.assertEqual(MemberFollow.objects.filter(follower_id=member_a_id).count(), 0)
        self.assertEqual(MemberFollow.objects.filter(following_id=member_a_id).count(), 0)

        # 验证返回的 deleted_data 摘要正确记载了清理条数
        self.assertTrue(any("Article likes: 1" in s for s in deleted_data))
        self.assertTrue(any("Member likes: 2" in s for s in deleted_data))
        self.assertTrue(any("Follows: 2" in s for s in deleted_data))

    def test_bug_logic_10_license_batch_assignment_zero_division_guard(self):
        """测试 batch_assign_licenses 传入空列表时不触发 ZeroDivisionError 并返回 0.0 成功率"""
        service = TenantAwareLicenseAssignmentService()
        results = service.batch_assign_licenses([])

        self.assertEqual(results["total_requested"], 0)
        self.assertEqual(results["successful"], 0)
        self.assertEqual(results["failed"], 0)
        self.assertEqual(results["summary"]["success_rate"], 0.0)

    def test_bug_logic_11_12_record_view_atomic_increment(self):
        """测试 record_view 防御性创建 ArticleStatistics 并通过 F() 表达式原子累加"""
        rf = APIRequestFactory()
        view = ArticleViewSet.as_view({"post": "record_view"})

        # 清除可能由 signal 初始化创建的记录，模拟无统计行的极端边界情况
        ArticleStatistics.objects.filter(article=self.article).delete()
        self.assertFalse(ArticleStatistics.objects.filter(article=self.article).exists())

        # 第一次请求
        req1 = rf.post(f"/api/v1/articles/{self.article.id}/view/")
        req1.META["REMOTE_ADDR"] = "127.0.0.1"
        resp1 = view(req1, pk=self.article.id)
        self.assertEqual(resp1.status_code, 200)

        stats = ArticleStatistics.objects.get(article=self.article)
        self.assertEqual(stats.views_count, 1)

        # 第二次请求
        req2 = rf.post(f"/api/v1/articles/{self.article.id}/view/")
        req2.META["REMOTE_ADDR"] = "127.0.0.1"
        resp2 = view(req2, pk=self.article.id)
        self.assertEqual(resp2.status_code, 200)

        stats.refresh_from_db()
        self.assertEqual(stats.views_count, 2)
