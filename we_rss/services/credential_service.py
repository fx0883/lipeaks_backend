import base64
import json
import re
import time
import uuid
from datetime import timedelta

import requests
from django.utils import timezone
from requests.cookies import cookiejar_from_dict

from we_rss.models import WechatCredential, WechatCredentialLoginSession, WechatSyncTask
from we_rss.services.task_service import TaskService, dispatch_we_rss_task


class WechatCredentialGateway:
    base_url = "https://mp.weixin.qq.com"

    def __init__(self, *, session_factory=None, poll_interval=2, max_poll_attempts=90, timeout=15):
        self.session_factory = session_factory or requests.Session
        self.poll_interval = poll_interval
        self.max_poll_attempts = max_poll_attempts
        self.timeout = timeout

    def _build_session(self):
        session = self.session_factory()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Referer": f"{self.base_url}/",
            }
        )
        return session

    def _serialize_cookie_dict(self, cookie_dict):
        return json.dumps(cookie_dict, ensure_ascii=True, sort_keys=True)

    def _load_session_cookies(self, session, cookie_snapshot):
        try:
            cookie_dict = json.loads(cookie_snapshot or "{}")
        except json.JSONDecodeError:
            cookie_dict = self._cookie_string_to_dict(cookie_snapshot)
        if cookie_dict:
            session.cookies.update(cookiejar_from_dict(cookie_dict))
        return cookie_dict

    def _cookie_string_to_dict(self, cookie_string):
        cookie_dict = {}
        for pair in str(cookie_string or "").split(";"):
            pair = pair.strip()
            if not pair or "=" not in pair:
                continue
            key, value = pair.split("=", 1)
            cookie_dict[key.strip()] = value.strip()
        return cookie_dict

    def _format_cookie_string(self, cookie_dict):
        return "; ".join(f"{key}={value}" for key, value in cookie_dict.items())

    def _parse_token_state(self, token_snapshot):
        try:
            state = json.loads(token_snapshot or "{}")
            return state if isinstance(state, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _extract_token(self, response):
        candidates = [getattr(response, "url", ""), getattr(response, "text", "")]
        for candidate in candidates:
            match = re.search(r"token=([^&\\s\"']+)", candidate or "")
            if match:
                return match.group(1)
        return ""

    def _fetch_account_info(self, session, token, fingerprint=""):
        response = session.get(
            f"{self.base_url}/cgi-bin/switchacct",
            params={
                "action": "get_acct_list",
                "fingerprint": fingerprint or session.cookies.get("fingerprint", ""),
                "token": token,
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        account_list = payload.get("acct_list") or (payload.get("biz_list") or {}).get("list") or payload.get("list") or []
        if account_list:
            return account_list[0]

        response = session.get(
            f"{self.base_url}/cgi-bin/searchbiz",
            params={
                "action": "search_biz",
                "begin": 0,
                "count": 1,
                "query": "",
                "token": token,
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        biz_list = (payload.get("biz_list") or {}).get("list") or payload.get("list") or []
        return biz_list[0] if biz_list else {}

    def _finalize_login(self, session, fingerprint):
        response = session.post(
            f"{self.base_url}/cgi-bin/bizlogin?action=login",
            data={
                "userlang": "zh_CN",
                "redirect_url": "",
                "cookie_forbidden": "0",
                "cookie_cleaned": "0",
                "plugin_used": "0",
                "login_type": "3",
                "fingerprint": fingerprint,
                "token": "",
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        token = self._extract_token(response)
        if not token:
            raise ValueError("Unable to extract WeChat token from login response.")

        session.get(
            f"{self.base_url}/cgi-bin/home",
            params={"t": "home/index", "lang": "zh_CN", "token": token},
            timeout=self.timeout,
        )
        cookie_dict = session.cookies.get_dict()
        account = self._fetch_account_info(session, token, fingerprint=fingerprint)
        return {
            "status": WechatCredentialLoginSession.Status.SUCCESS,
            "scan_status": "confirmed",
            "token_snapshot": token,
            "cookie_snapshot": self._format_cookie_string(cookie_dict),
            "credential_name": (
                account.get("username")
                or account.get("nickname")
                or account.get("user_name")
                or account.get("nick_name")
                or "WeChat Credential"
            ),
        }

    def _emit_status(self, on_status, *, status, scan_status, error_message=""):
        if on_status is None:
            return
        payload = {
            "status": status,
            "scan_status": scan_status,
        }
        if error_message:
            payload["error_message"] = error_message
        on_status(payload)

    def create_login_session(self):
        session = self._build_session()
        session.get(f"{self.base_url}/", timeout=self.timeout)

        session_id = uuid.uuid4().hex
        fingerprint = uuid.uuid4().hex
        session.cookies.set("uuid", session_id)
        session.cookies.set("fingerprint", fingerprint)

        session.get(
            f"{self.base_url}/cgi-bin/bizlogin",
            params={
                "action": "prelogin",
                "fingerprint": uuid.uuid4().hex,
                "token": "",
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1",
            },
            timeout=self.timeout,
        )
        response = session.post(
            f"{self.base_url}/cgi-bin/bizlogin?action=startlogin",
            data={
                "fingerprint": fingerprint,
                "token": session.cookies.get("token", ""),
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1",
                "redirect_url": "/cgi-bin/settingpage?t=setting/index&action=index&lang=zh_CN",
                "login_type": "3",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        response_cookies = getattr(response, "cookies", None) or {}
        response_uuid = getattr(response_cookies, "get", lambda *args, **kwargs: None)("uuid")
        if response_uuid:
            session_id = response_uuid
            session.cookies.set("uuid", session_id)

        qr_response = session.get(
            f"{self.base_url}/cgi-bin/scanloginqrcode",
            params={
                "action": "getqrcode",
                "uuid": session_id,
                "random": int(time.time() * 1000),
            },
            allow_redirects=False,
            timeout=self.timeout,
        )
        qr_response.raise_for_status()
        qr_content_type = qr_response.headers.get("Content-Type", "")
        qr_code_image = ""
        qr_code_url = getattr(qr_response, "url", "")
        if "image" not in qr_content_type:
            redirect_url = qr_response.headers.get("Location")
            if redirect_url:
                redirect_response = session.get(redirect_url, timeout=self.timeout)
                redirect_response.raise_for_status()
                qr_response = redirect_response
                qr_content_type = qr_response.headers.get("Content-Type", "")
                qr_code_url = getattr(qr_response, "url", redirect_url)
        if "image" in qr_content_type and qr_response.content:
            qr_code_image = "data:image/png;base64," + base64.b64encode(qr_response.content).decode("ascii")

        return {
            "session_id": session_id,
            "status": WechatCredentialLoginSession.Status.PENDING,
            "qr_code_url": qr_code_url,
            "qr_code_image": qr_code_image,
            "scan_status": "waiting",
            "expired_at": timezone.now() + timedelta(minutes=10),
            "token_snapshot": self._serialize_cookie_dict({"fingerprint": fingerprint}),
            "cookie_snapshot": self._serialize_cookie_dict(session.cookies.get_dict()),
        }

    def wait_for_login(self, login_session, on_status=None):
        session = self._build_session()
        cookie_dict = self._load_session_cookies(session, login_session.cookie_snapshot)
        token_state = self._parse_token_state(login_session.token_snapshot)
        fingerprint = token_state.get("fingerprint") or cookie_dict.get("fingerprint") or uuid.uuid4().hex
        session.cookies.set("fingerprint", fingerprint)
        session.cookies.set("uuid", login_session.session_id)

        for _attempt in range(self.max_poll_attempts):
            response = session.get(
                f"{self.base_url}/cgi-bin/scanloginqrcode",
                params={
                    "action": "ask",
                    "fingerprint": fingerprint,
                    "lang": "zh_CN",
                    "f": "json",
                    "ajax": 1,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            status = payload.get("status", 0)
            if "invalid session" in str(payload).lower():
                return {
                    "status": WechatCredentialLoginSession.Status.FAILED,
                    "scan_status": "invalid_session",
                    "error_message": "Invalid WeChat login session.",
                }
            if status in {1, 3}:
                return self._finalize_login(session, fingerprint)
            if status == 2:
                self._emit_status(
                    on_status,
                    status=WechatCredentialLoginSession.Status.SCANNED,
                    scan_status="scanned",
                )
                time.sleep(self.poll_interval)
                continue
            if status == 4:
                self._emit_status(
                    on_status,
                    status=WechatCredentialLoginSession.Status.CONFIRMED,
                    scan_status="confirmed",
                )
                time.sleep(self.poll_interval)
                continue
            time.sleep(self.poll_interval)

        return {
            "status": WechatCredentialLoginSession.Status.EXPIRED,
            "scan_status": "expired",
            "error_message": "WeChat login session expired before confirmation.",
        }

    def check_credential(self, credential):
        session = self._build_session()
        cookie_dict = self._cookie_string_to_dict(credential.cookie)
        if cookie_dict:
            session.cookies.update(cookiejar_from_dict(cookie_dict))
        response = session.get(
            f"{self.base_url}/cgi-bin/home",
            params={"t": "home/index", "lang": "zh_CN", "token": credential.token},
            timeout=self.timeout,
        )
        valid = response.status_code < 400 and "token=" in (response.url or "")
        return {
            "valid": valid,
            "status": WechatCredential.Status.ACTIVE if valid else WechatCredential.Status.EXPIRED,
            "message": "" if valid else "WeChat credential is no longer valid.",
        }


class CredentialService:
    @staticmethod
    def create_login_session(*, tenant, created_by, gateway):
        payload = gateway.create_login_session()
        login_session = WechatCredentialLoginSession.objects.create(
            tenant=tenant,
            session_id=payload["session_id"],
            status=payload.get("status", WechatCredentialLoginSession.Status.PENDING),
            qr_code_url=payload.get("qr_code_url", ""),
            qr_code_image=payload.get("qr_code_image", ""),
            scan_status=payload.get("scan_status", ""),
            token_snapshot=payload.get("token_snapshot", ""),
            cookie_snapshot=payload.get("cookie_snapshot", ""),
            expired_at=payload.get("expired_at"),
            created_by=created_by,
        )
        task = TaskService.create_task(
            tenant=tenant,
            task_type=WechatSyncTask.TaskType.CREDENTIAL_LOGIN,
            created_by=created_by,
            target_type="login_session",
            target_id=login_session.id,
            message="Credential login task created.",
            request_payload={"session_id": login_session.session_id},
        )
        from we_rss.tasks import run_credential_login_task

        dispatch_we_rss_task(run_credential_login_task, task.id)
        return login_session

    @staticmethod
    def get_login_session(*, tenant, session_id):
        return WechatCredentialLoginSession.objects.get(tenant=tenant, session_id=session_id)

    @staticmethod
    def persist_credential_from_login_session(*, login_session, name=None):
        credential = login_session.credential
        now = timezone.now()
        resolved_name = name or f"WeChat Credential {login_session.session_id}"

        if credential is None:
            credential = (
                WechatCredential.objects.filter(tenant=login_session.tenant, name=resolved_name).order_by("-created_at").first()
            )

        if credential is None:
            credential = WechatCredential.objects.create(
                tenant=login_session.tenant,
                name=resolved_name,
                status=WechatCredential.Status.ACTIVE,
                token=login_session.token_snapshot,
                cookie=login_session.cookie_snapshot,
                is_default=not WechatCredential.objects.filter(tenant=login_session.tenant, is_default=True).exists(),
                last_login_at=now,
                created_by=login_session.created_by,
                updated_by=login_session.created_by,
            )
        else:
            credential.name = resolved_name
            credential.status = WechatCredential.Status.ACTIVE
            credential.token = login_session.token_snapshot
            credential.cookie = login_session.cookie_snapshot
            credential.last_login_at = now
            credential.updated_by = login_session.created_by
            credential.save()

        login_session.credential = credential
        login_session.status = WechatCredentialLoginSession.Status.SUCCESS
        login_session.save(update_fields=["credential", "status", "updated_at"])
        return credential

    @staticmethod
    def check_credential(*, credential, gateway):
        result = gateway.check_credential(credential)
        credential.status = result.get("status", credential.status)
        credential.last_error = result.get("message", "")
        credential.last_check_at = timezone.now()
        credential.save(update_fields=["status", "last_error", "last_check_at", "updated_at"])
        return result

    @staticmethod
    def set_default_credential(credential, *, updated_by):
        credential.is_default = True
        credential.updated_by = updated_by
        credential.save()
        return credential

    @staticmethod
    def get_login_task(*, login_session):
        return (
            WechatSyncTask.objects.filter(
                tenant=login_session.tenant,
                task_type=WechatSyncTask.TaskType.CREDENTIAL_LOGIN,
                target_type="login_session",
                target_id=login_session.id,
            )
            .order_by("-created_at")
            .first()
        )
