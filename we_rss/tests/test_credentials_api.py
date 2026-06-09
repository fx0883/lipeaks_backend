import json
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from common.authentication.jwt_auth import generate_jwt_token
from we_rss.models import WechatCredential
from we_rss.serializers import CredentialUpdateSerializer
from we_rss.services.credential_service import CredentialService, WechatCredentialGateway
from we_rss.models import WechatCredentialLoginSession, WechatSyncTask
from tenants.models import Tenant
from users.models import Member


class CredentialSerializerTests(TestCase):
    def test_credential_update_disallows_manual_token_update(self):
        serializer = CredentialUpdateSerializer(data={"token": "manual-token"})

        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)

    def test_credential_update_disallows_manual_cookie_update(self):
        serializer = CredentialUpdateSerializer(data={"cookie": "manual-cookie"})

        self.assertFalse(serializer.is_valid())
        self.assertIn("cookie", serializer.errors)


class FakeCredentialGateway:
    def initialize_login_session(self, login_session, on_status=None):
        return {
            "status": "pending",
            "qr_code_url": "https://example.com/qr",
            "qr_code_image": "base64-image",
            "scan_status": "waiting",
            "expired_at": timezone.now(),
            "token_snapshot": json.dumps({"fingerprint": "fingerprint-123", "wechat_session_id": "session-123"}),
            "cookie_snapshot": json.dumps({"uuid": "session-123", "fingerprint": "fingerprint-123"}),
        }

    def wait_for_login(self, login_session):
        return {
            "status": "success",
            "scan_status": "confirmed",
            "token_snapshot": "token-from-login",
            "cookie_snapshot": "cookie-from-login",
            "credential_name": "Synced Credential",
        }

    def check_credential(self, credential):
        return {
            "valid": True,
            "status": "active",
            "message": "",
        }


class CredentialServiceTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )

    def test_create_login_session_returns_local_placeholder_before_background_qr_fetch(self):
        gateway = Mock()
        gateway.create_login_session.side_effect = AssertionError("request thread should not fetch WeChat QR data")

        with patch("we_rss.services.credential_service.dispatch_we_rss_task", create=True) as mock_dispatch:
            session = CredentialService.create_login_session(
                tenant=self.tenant,
                created_by=self.member,
                gateway=gateway,
            )

        self.assertTrue(session.session_id)
        self.assertEqual(session.status, "pending")
        self.assertEqual(session.qr_code_url, "")
        self.assertEqual(session.qr_code_image, "")
        self.assertEqual(session.scan_status, "waiting")
        self.assertEqual(session.tenant, self.tenant)
        self.assertEqual(session.created_by, self.member)
        self.assertEqual(session.token_snapshot, "")
        self.assertEqual(session.cookie_snapshot, "")
        self.assertIsNotNone(session.expired_at)
        mock_dispatch.assert_called_once()

    @override_settings(CELERY_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    @patch("we_rss.tasks.get_credential_gateway", return_value=FakeCredentialGateway())
    def test_create_login_session_dispatches_background_worker_when_celery_disabled(self, _mock_task_gateway):
        with patch("we_rss.services.credential_service.dispatch_we_rss_task", create=True) as mock_dispatch:
            with patch(
                "we_rss.tasks.run_credential_login_task.delay",
                side_effect=AssertionError("login task should not run inline"),
            ):
                session = CredentialService.create_login_session(
                    tenant=self.tenant,
                    created_by=self.member,
                    gateway=FakeCredentialGateway(),
                )

        task = WechatSyncTask.objects.get(task_type="credential_login", target_id=session.id)

        mock_dispatch.assert_called_once()
        self.assertEqual(session.status, "pending")
        self.assertEqual(task.status, "pending")

    def test_set_default_unsets_previous_default(self):
        first = WechatCredential.objects.create(
            tenant=self.tenant,
            name="First",
            status="active",
            token="token-1",
            cookie="cookie-1",
            is_default=True,
            created_by=self.member,
            updated_by=self.member,
        )
        second = WechatCredential.objects.create(
            tenant=self.tenant,
            name="Second",
            status="active",
            token="token-2",
            cookie="cookie-2",
            is_default=False,
            created_by=self.member,
            updated_by=self.member,
        )

        CredentialService.set_default_credential(second, updated_by=self.member)

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)
        self.assertEqual(second.updated_by, self.member)

    def test_persist_credential_from_login_session_updates_existing_credential_by_name(self):
        existing = WechatCredential.objects.create(
            tenant=self.tenant,
            name="Synced Credential",
            status="expired",
            token="old-token",
            cookie="old-cookie",
            is_default=True,
            created_by=self.member,
            updated_by=self.member,
        )
        login_session = WechatCredentialLoginSession.objects.create(
            tenant=self.tenant,
            session_id="session-existing-credential",
            status="confirmed",
            token_snapshot="new-token",
            cookie_snapshot="new-cookie",
            created_by=self.member,
        )

        credential = CredentialService.persist_credential_from_login_session(
            login_session=login_session,
            name="Synced Credential",
        )

        existing.refresh_from_db()
        login_session.refresh_from_db()

        self.assertEqual(credential.id, existing.id)
        self.assertEqual(existing.token, "new-token")
        self.assertEqual(existing.cookie, "new-cookie")
        self.assertEqual(existing.status, "active")
        self.assertEqual(login_session.credential_id, existing.id)


class FakeResponse:
    def __init__(self, *, status_code=200, headers=None, json_data=None, text="", content=b"", url=""):
        self.status_code = status_code
        self.headers = headers or {}
        self._json_data = json_data
        self.text = text
        self.content = content
        self.url = url
        self.cookies = {}

    def json(self):
        if self._json_data is None:
            raise ValueError("No JSON data configured")
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class CredentialGatewayTests(TestCase):
    @patch("we_rss.services.credential_service.uuid.uuid4")
    @patch("we_rss.services.credential_service.requests.Session")
    def test_initialize_login_session_returns_qr_payload_with_gateway_state(self, mock_session_cls, mock_uuid4):
        mock_uuid4.side_effect = [
            Mock(hex="uuid-session"),
            Mock(hex="uuid-fingerprint"),
            Mock(hex="uuid-fingerprint-prelogin"),
        ]
        session = mock_session_cls.return_value
        session.cookies.get.side_effect = lambda key, default=None: {"token": "", "uuid": "uuid-session"}.get(key, default)
        session.cookies.get_dict.return_value = {"uuid": "uuid-session", "fingerprint": "uuid-fingerprint"}
        session.get.side_effect = [
            FakeResponse(text="login page"),
            FakeResponse(json_data={"base_resp": {"ret": 0}}),
            FakeResponse(
                headers={"Content-Type": "image/png"},
                content=b"png-binary",
                url="https://mp.weixin.qq.com/cgi-bin/scanloginqrcode?action=getqrcode&uuid=uuid-session",
            ),
        ]
        start_login_response = FakeResponse(json_data={"base_resp": {"ret": 0}})
        start_login_response.cookies = {"uuid": "uuid-session"}
        session.post.return_value = start_login_response
        login_session = WechatCredentialLoginSession(session_id="local-session-id")

        payload = WechatCredentialGateway().initialize_login_session(login_session)

        self.assertEqual(payload["status"], "pending")
        self.assertEqual(payload["scan_status"], "waiting")
        self.assertTrue(payload["qr_code_image"].startswith("data:image/png;base64,"))
        token_state = json.loads(payload["token_snapshot"])
        self.assertEqual(token_state["fingerprint"], "uuid-fingerprint")
        self.assertEqual(token_state["wechat_session_id"], "uuid-session")
        self.assertEqual(json.loads(payload["cookie_snapshot"])["uuid"], "uuid-session")

    @patch("we_rss.services.credential_service.time.sleep", return_value=None)
    @patch("we_rss.services.credential_service.requests.Session")
    def test_wait_for_login_returns_token_and_cookie_snapshots(self, mock_session_cls, _mock_sleep):
        session = mock_session_cls.return_value
        session.cookies.get_dict.return_value = {
            "uuid": "uuid-session",
            "fingerprint": "uuid-fingerprint",
            "slave_sid": "sid-1",
        }
        session.get.side_effect = [
            FakeResponse(json_data={"status": 2}),
            FakeResponse(json_data={"status": 1}),
            FakeResponse(
                text='window.location.href = "/cgi-bin/home?t=home/index&lang=zh_CN&token=token-123";',
                url="https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=token-123",
            ),
            FakeResponse(
                json_data={
                    "biz_list": {
                        "list": [
                            {
                                "username": "Test Credential",
                                "headimgurl": "https://example.com/logo.png",
                            }
                        ]
                    }
                }
            ),
        ]
        session.post.return_value = FakeResponse(
            text='window.location.href = "/cgi-bin/home?t=home/index&lang=zh_CN&token=token-123";',
            url="https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=token-123",
        )
        login_session = WechatCredentialLoginSession(
            session_id="local-session-id",
            token_snapshot=json.dumps({"fingerprint": "uuid-fingerprint", "wechat_session_id": "uuid-session"}),
            cookie_snapshot=json.dumps({"uuid": "uuid-session", "fingerprint": "uuid-fingerprint"}),
        )

        payload = WechatCredentialGateway(poll_interval=0, max_poll_attempts=2).wait_for_login(login_session)

        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["scan_status"], "confirmed")
        self.assertEqual(payload["token_snapshot"], "token-123")
        self.assertIn("slave_sid=sid-1", payload["cookie_snapshot"])
        self.assertEqual(payload["credential_name"], "Test Credential")

    @patch("we_rss.services.credential_service.time.sleep", return_value=None)
    @patch("we_rss.services.credential_service.requests.Session")
    def test_wait_for_login_reports_intermediate_scan_states(self, mock_session_cls, _mock_sleep):
        session = mock_session_cls.return_value
        session.cookies.get_dict.return_value = {
            "uuid": "uuid-session",
            "fingerprint": "uuid-fingerprint",
            "slave_sid": "sid-1",
        }
        session.get.side_effect = [
            FakeResponse(json_data={"status": 2}),
            FakeResponse(json_data={"status": 4}),
            FakeResponse(json_data={"status": 1}),
            FakeResponse(
                text='window.location.href = "/cgi-bin/home?t=home/index&lang=zh_CN&token=token-123";',
                url="https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=token-123",
            ),
            FakeResponse(
                json_data={
                    "base_resp": {"ret": 0},
                    "acct_list": [
                        {
                            "user_name": "Fallback Credential",
                            "nick_name": "Fallback Credential",
                            "head_img": "https://example.com/logo.png",
                        }
                    ],
                }
            ),
        ]
        session.post.return_value = FakeResponse(
            text='window.location.href = "/cgi-bin/home?t=home/index&lang=zh_CN&token=token-123";',
            url="https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=token-123",
        )
        login_session = WechatCredentialLoginSession(
            session_id="local-session-id",
            token_snapshot=json.dumps({"fingerprint": "uuid-fingerprint", "wechat_session_id": "uuid-session"}),
            cookie_snapshot=json.dumps({"uuid": "uuid-session", "fingerprint": "uuid-fingerprint"}),
        )
        statuses = []

        payload = WechatCredentialGateway(poll_interval=0, max_poll_attempts=3).wait_for_login(
            login_session,
            on_status=statuses.append,
        )

        self.assertEqual(
            statuses,
            [
                {"status": "scanned", "scan_status": "scanned"},
                {"status": "confirmed", "scan_status": "confirmed"},
            ],
        )
        self.assertEqual(payload["credential_name"], "Fallback Credential")


class CredentialApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A", code="tenant_a")
        self.other_tenant = Tenant.objects.create(name="Tenant B", code="tenant_b")
        self.member = Member.objects.create(
            username="tenant_member",
            email="tenant-member@example.com",
            tenant=self.tenant,
        )
        self.token = generate_jwt_token(self.member)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )

    def test_member_can_list_tenant_credentials(self):
        WechatCredential.objects.create(
            tenant=self.tenant,
            name="Tenant Credential",
            status="active",
            token="token-1",
            cookie="cookie-1",
            created_by=self.member,
            updated_by=self.member,
        )
        other_member = Member.objects.create(
            username="other_member",
            email="other-member@example.com",
            tenant=self.other_tenant,
        )
        WechatCredential.objects.create(
            tenant=self.other_tenant,
            name="Other Credential",
            status="active",
            token="token-2",
            cookie="cookie-2",
            created_by=other_member,
            updated_by=other_member,
        )

        response = self.client.get("/api/v1/we-rss/credentials/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["name"], "Tenant Credential")

    @patch("we_rss.tasks.get_credential_gateway", return_value=FakeCredentialGateway())
    @patch("we_rss.views.credential_views.CredentialApiGatewayMixin.get_gateway", return_value=FakeCredentialGateway())
    def test_member_can_create_login_session(self, _mock_gateway, _mock_task_gateway):
        response = self.client.post("/api/v1/we-rss/credentials/login-sessions/", {}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["data"]["session_id"])
        self.assertEqual(response.data["data"]["qr_code_url"], "")
        self.assertEqual(response.data["data"]["qr_code_image"], "")
        self.assertEqual(response.data["data"]["scan_status"], "waiting")
        self.assertIsNotNone(response.data["data"]["task_id"])

    def test_member_can_get_login_session_detail(self):
        session = WechatCredentialLoginSession.objects.create(
            tenant=self.tenant,
            session_id="session-123",
            status="pending",
            qr_code_url="https://example.com/qr",
            created_by=self.member,
        )

        response = self.client.get(f"/api/v1/we-rss/credentials/login-sessions/{session.session_id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["session_id"], session.session_id)

    def test_member_can_update_credential_metadata(self):
        credential = WechatCredential.objects.create(
            tenant=self.tenant,
            name="Old Name",
            status="active",
            token="token-1",
            cookie="cookie-1",
            created_by=self.member,
            updated_by=self.member,
        )

        response = self.client.put(
            f"/api/v1/we-rss/credentials/{credential.id}/",
            {"name": "New Name"},
            format="json",
        )

        credential.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(credential.name, "New Name")

    def test_member_can_set_default_credential(self):
        first = WechatCredential.objects.create(
            tenant=self.tenant,
            name="First",
            status="active",
            token="token-1",
            cookie="cookie-1",
            is_default=True,
            created_by=self.member,
            updated_by=self.member,
        )
        second = WechatCredential.objects.create(
            tenant=self.tenant,
            name="Second",
            status="active",
            token="token-2",
            cookie="cookie-2",
            is_default=False,
            created_by=self.member,
            updated_by=self.member,
        )

        response = self.client.post(f"/api/v1/we-rss/credentials/{second.id}/set-default/")

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)

    @patch("we_rss.views.credential_views.CredentialApiGatewayMixin.get_gateway", return_value=FakeCredentialGateway())
    def test_member_can_check_credential(self, _mock_gateway):
        credential = WechatCredential.objects.create(
            tenant=self.tenant,
            name="Check Me",
            status="pending",
            token="token-1",
            cookie="cookie-1",
            created_by=self.member,
            updated_by=self.member,
        )

        response = self.client.post(f"/api/v1/we-rss/credentials/{credential.id}/check/")

        credential.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["valid"])
        self.assertEqual(credential.status, "active")
        self.assertIsNotNone(credential.last_check_at)
