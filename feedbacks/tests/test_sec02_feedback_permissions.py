"""
Adversarial Security Test Suite for SEC-02 (Feedback Replies and Attachments Protection)
Challenger 1 Empirical Verification Harness.
"""
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from tenants.models import Tenant
from users.models import User
from feedbacks.models import Feedback, FeedbackReply, FeedbackAttachment
from common.authentication.jwt_auth import generate_jwt_token


class Sec02AdversarialChallengeTests(TestCase):
    """
    SEC-02 对抗攻击实证测试套件
    挑战目标：
    1. 模拟未登录匿名请求，调用工单回复与附件的 POST/PUT/PATCH/DELETE 接口 -> 必须被 401 拦截
    2. 模拟不带租户上下文/未关联租户的用户，调用写操作接口 -> 必须被 400 严格拦截
    3. 模拟跨租户伪造请求 (User B 访问 Tenant A 的工单数据) -> 必须被 404/403/400 拦截，绝无法篡改或删除数据
    4. 验证数据物理完整性与软删除标记未被非法修改
    """

    def setUp(self):
        # 使用 localhost 避免 DisallowedHost 噪音
        self.client = APIClient(HTTP_HOST='localhost')

        # 租户 A 与其资源
        self.tenant_a = Tenant.objects.create(name="Tenant Alpha", code="alpha", status="active")
        self.tenant_a.ensure_quota()
        self.user_a = User.objects.create_user(
            username="user_alpha",
            email="alpha@test.com",
            password="Password123!",
            tenant=self.tenant_a,
            is_admin=True,
            is_staff=True
        )
        self.token_a = generate_jwt_token(self.user_a)["access_token"]

        # 租户 B (攻击者租户) 与其用户
        self.tenant_b = Tenant.objects.create(name="Tenant Beta", code="beta", status="active")
        self.tenant_b.ensure_quota()
        self.user_b = User.objects.create_user(
            username="attacker_beta",
            email="beta@attacker.com",
            password="Password123!",
            tenant=self.tenant_b,
            is_admin=True,
            is_staff=True
        )
        self.token_b = generate_jwt_token(self.user_b)["access_token"]

        # 无租户关联的合法认证用户 (模拟注册后未分配租户的普通账号)
        self.user_no_tenant = User.objects.create_user(
            username="user_homeless",
            email="homeless@test.com",
            password="Password123!",
            is_admin=False,
            is_staff=False
        )
        self.token_no_tenant = generate_jwt_token(self.user_no_tenant)["access_token"]

        # 在租户 A 下创建目标工单、回复、附件
        self.feedback_a = Feedback.objects.create(
            tenant=self.tenant_a,
            title="Confidential Alpha Ticket",
            description="Top secret vulnerability report for Alpha",
            status="submitted",
            user=self.user_a
        )
        self.reply_a = FeedbackReply.objects.create(
            tenant=self.tenant_a,
            feedback=self.feedback_a,
            content="Original Alpha Reply - Do Not Touch",
            user=self.user_a,
            is_internal_note=False
        )
        dummy_file = SimpleUploadedFile("secret_log.txt", b"Sensitive log content", content_type="text/plain")
        self.attachment_a = FeedbackAttachment.objects.create(
            tenant=self.tenant_a,
            feedback=self.feedback_a,
            file=dummy_file,
            filename="secret_log.txt",
            file_size=21,
            uploaded_by=self.user_a
        )

        # URL 路由定义
        self.url_replies_list = reverse('feedbacks:feedback-replies-list', kwargs={'feedback_pk': self.feedback_a.id})
        self.url_reply_detail = reverse('feedbacks:feedback-replies-detail', kwargs={'feedback_pk': self.feedback_a.id, 'pk': self.reply_a.id})
        self.url_attachments_list = reverse('feedbacks:feedback-attachments-list', kwargs={'feedback_pk': self.feedback_a.id})
        self.url_attachment_detail = reverse('feedbacks:feedback-attachments-detail', kwargs={'feedback_pk': self.feedback_a.id, 'pk': self.attachment_a.id})

    # =========================================================================
    # 维度一：未登录匿名攻击 (Anonymous Attack) -> 必须被 401 拦截
    # =========================================================================

    def test_01_anonymous_post_reply_blocked(self):
        """匿名攻击：未登录尝试 POST 创建工单回复 -> 401 Unauthorized"""
        self.client.credentials(HTTP_HOST='localhost')
        response = self.client.post(self.url_replies_list, {"content": "Hacked reply"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(FeedbackReply.objects.filter(feedback=self.feedback_a).count(), 1)

    def test_02_anonymous_put_reply_blocked(self):
        """匿名攻击：未登录尝试 PUT 全量修改工单回复 -> 401 Unauthorized"""
        self.client.credentials(HTTP_HOST='localhost')
        response = self.client.put(self.url_reply_detail, {"content": "Maliciously overwritten content"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.reply_a.refresh_from_db()
        self.assertEqual(self.reply_a.content, "Original Alpha Reply - Do Not Touch")

    def test_03_anonymous_patch_reply_blocked(self):
        """匿名攻击：未登录尝试 PATCH 部分修改工单回复 -> 401 Unauthorized"""
        self.client.credentials(HTTP_HOST='localhost')
        response = self.client.patch(self.url_reply_detail, {"content": "Maliciously patched content"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.reply_a.refresh_from_db()
        self.assertEqual(self.reply_a.content, "Original Alpha Reply - Do Not Touch")

    def test_04_anonymous_delete_reply_blocked(self):
        """匿名攻击：未登录尝试 DELETE 删除工单回复 -> 401 Unauthorized"""
        self.client.credentials(HTTP_HOST='localhost')
        response = self.client.delete(self.url_reply_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.reply_a.refresh_from_db()
        self.assertFalse(self.reply_a.is_deleted, "Reply must NOT be marked deleted")

    def test_05_anonymous_post_attachment_blocked(self):
        """匿名攻击：未登录尝试 POST 上传附件 -> 401 Unauthorized"""
        self.client.credentials(HTTP_HOST='localhost')
        fake_file = SimpleUploadedFile("malware.txt", b"evil script", content_type="text/plain")
        response = self.client.post(self.url_attachments_list, {"file": fake_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(FeedbackAttachment.objects.filter(feedback=self.feedback_a).count(), 1)

    def test_06_anonymous_delete_attachment_blocked(self):
        """匿名攻击：未登录尝试 DELETE 删除附件 -> 401 Unauthorized"""
        self.client.credentials(HTTP_HOST='localhost')
        response = self.client.delete(self.url_attachment_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.attachment_a.refresh_from_db()
        self.assertFalse(self.attachment_a.is_deleted, "Attachment must NOT be marked deleted")

    # =========================================================================
    # 维度二：缺失租户上下文攻击 (No Tenant Context) -> 必须被 400 拦截
    # =========================================================================

    def test_07_no_tenant_context_post_reply_blocked(self):
        """租户缺失攻击：已登录但无租户关联且无租户头，POST 创建回复 -> 400/403 严格拦截"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_no_tenant}"
        )
        response = self.client.post(self.url_replies_list, {"content": "Orphan reply"}, format="json")
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        self.assertEqual(FeedbackReply.objects.filter(feedback=self.feedback_a).count(), 1)

    def test_08_no_tenant_context_update_reply_blocked(self):
        """租户缺失攻击：已登录但无租户关联，PUT 修改回复 -> 400/403 严格拦截"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_no_tenant}"
        )
        response = self.client.put(self.url_reply_detail, {"content": "Orphan update"}, format="json")
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        self.reply_a.refresh_from_db()
        self.assertEqual(self.reply_a.content, "Original Alpha Reply - Do Not Touch")

    def test_09_no_tenant_context_delete_reply_blocked(self):
        """租户缺失攻击：已登录但无租户关联，DELETE 删除回复 -> 400/403 严格拦截"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_no_tenant}"
        )
        response = self.client.delete(self.url_reply_detail)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        self.reply_a.refresh_from_db()
        self.assertFalse(self.reply_a.is_deleted)

    def test_10_no_tenant_context_post_attachment_blocked(self):
        """租户缺失攻击：已登录但无租户关联，POST 上传附件 -> 400/403 严格拦截"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_no_tenant}"
        )
        fake_file = SimpleUploadedFile("orphan.txt", b"data", content_type="text/plain")
        response = self.client.post(self.url_attachments_list, {"file": fake_file}, format="multipart")
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_11_no_tenant_context_delete_attachment_blocked(self):
        """租户缺失攻击：已登录但无租户关联，DELETE 删除附件 -> 400/403 严格拦截"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_no_tenant}"
        )
        response = self.client.delete(self.url_attachment_detail)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        self.attachment_a.refresh_from_db()
        self.assertFalse(self.attachment_a.is_deleted)

    # =========================================================================
    # 维度三：跨租户横向越权攻击 (Cross-Tenant Attack) -> 必须被 404 严格拦截
    # =========================================================================

    def test_12_cross_tenant_post_reply_blocked(self):
        """跨租户攻击：租户 B 用户试图向租户 A 的工单注入回复 -> 404 Not Found"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_b}",
            HTTP_X_TENANT_ID=str(self.tenant_b.id)
        )
        response = self.client.post(self.url_replies_list, {"content": "Injected by Tenant B attacker"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(FeedbackReply.objects.filter(feedback=self.feedback_a).count(), 1)

    def test_13_cross_tenant_put_reply_blocked(self):
        """跨租户攻击：租户 B 用户试图修改租户 A 的工单回复 -> 404 Not Found"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_b}",
            HTTP_X_TENANT_ID=str(self.tenant_b.id)
        )
        response = self.client.put(self.url_reply_detail, {"content": "Tampered by Tenant B attacker"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.reply_a.refresh_from_db()
        self.assertEqual(self.reply_a.content, "Original Alpha Reply - Do Not Touch")

    def test_14_cross_tenant_patch_reply_blocked(self):
        """跨租户攻击：租户 B 用户试图 PATCH 修改租户 A 的工单回复 -> 404 Not Found"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_b}",
            HTTP_X_TENANT_ID=str(self.tenant_b.id)
        )
        response = self.client.patch(self.url_reply_detail, {"content": "Tampered partial"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.reply_a.refresh_from_db()
        self.assertEqual(self.reply_a.content, "Original Alpha Reply - Do Not Touch")

    def test_15_cross_tenant_delete_reply_blocked(self):
        """跨租户攻击：租户 B 用户试图软删除租户 A 的工单回复 -> 404 Not Found"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_b}",
            HTTP_X_TENANT_ID=str(self.tenant_b.id)
        )
        response = self.client.delete(self.url_reply_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.reply_a.refresh_from_db()
        self.assertFalse(self.reply_a.is_deleted, "Cross-tenant delete MUST fail, is_deleted must be False")

    def test_16_cross_tenant_post_attachment_blocked(self):
        """跨租户攻击：租户 B 用户试图向租户 A 的工单上传附件 -> 404 Not Found"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_b}",
            HTTP_X_TENANT_ID=str(self.tenant_b.id)
        )
        fake_file = SimpleUploadedFile("trojan.txt", b"trojan content", content_type="text/plain")
        response = self.client.post(self.url_attachments_list, {"file": fake_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(FeedbackAttachment.objects.filter(feedback=self.feedback_a).count(), 1)

    def test_17_cross_tenant_delete_attachment_blocked(self):
        """跨租户攻击：租户 B 用户试图删除租户 A 的工单附件 -> 404 Not Found"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_b}",
            HTTP_X_TENANT_ID=str(self.tenant_b.id)
        )
        response = self.client.delete(self.url_attachment_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.attachment_a.refresh_from_db()
        self.assertFalse(self.attachment_a.is_deleted, "Cross-tenant delete MUST fail, is_deleted must be False")

    # =========================================================================
    # 维度四：伪造 Header 欺诈攻击 (Forged X-Tenant-ID Header) -> 必须被拦截
    # =========================================================================

    def test_18_forged_header_impersonating_target_tenant_blocked(self):
        """伪造Header攻击：租户 B 用户伪造携带 X-Tenant-ID: <Tenant A> -> 中间件拦截报 403 (TENANT_ACCESS_DENIED)"""
        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_AUTHORIZATION=f"Bearer {self.token_b}",
            HTTP_X_TENANT_ID=str(self.tenant_a.id)  # 伪造目标租户 A 的 ID
        )
        response = self.client.delete(self.url_reply_detail)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        self.reply_a.refresh_from_db()
        self.assertFalse(self.reply_a.is_deleted)

    # =========================================================================
    # 维度五：安全方法 (GET) 租户过滤与内部备注保护
    # =========================================================================

    def test_19_safe_get_methods_allowed_and_filter_internal_notes(self):
        """安全读取：携带有效租户头的未认证用户可以 GET 列表，但内部备注对非管理员不可见"""
        # 创建内部备注回复
        FeedbackReply.objects.create(
            tenant=self.tenant_a,
            feedback=self.feedback_a,
            content="Internal admin secret note",
            user=self.user_a,
            is_internal_note=True
        )

        self.client.credentials(
            HTTP_HOST='localhost',
            HTTP_X_TENANT_ID=str(self.tenant_a.id)
        )
        response = self.client.get(self.url_replies_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 应该只看到 1 条公开回复，内部备注被严格过滤
        items = response.data.get('data', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["content"], "Original Alpha Reply - Do Not Touch")
