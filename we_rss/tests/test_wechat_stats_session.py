import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext import (
    extract_live_overrides,
    parse_cookie_header,
)
from scripts.lipeaks_viral_articles.scripts.wechat_session_from_log import (
    extract_session_from_lines,
)
from scripts.lipeaks_viral_articles.scripts.wechat_stats_mitm_addon import (
    _extract_article_query,
    extract_session_from_flow_parts,
    write_article_request_snapshot,
    write_session_file,
)


class WechatStatsSessionTests(SimpleTestCase):
    def test_extract_session_from_lines_uses_query_token_when_cookie_missing(self):
        lines = [
            (
                "POST https://mp.weixin.qq.com/mp/jsmonitor?uin=ODk2ODQwNjAw"
                "&key=test-key&pass_ticket=test-pass&wxtoken=888"
                "&devicetype=UnifiedPCWindows&version=f254181d"
                "&__biz=Mzk0ODM5NTEyNA%3D%3D&appmsg_token=query-token&x5=0&f=json"
            ),
            (
                "referer: https://mp.weixin.qq.com/s?__biz=Mzk0ODM5NTEyNA=="
                "&mid=2247505811&idx=1&sn=test-sn&key=test-key&uin=ODk2ODQwNjAw"
                "&devicetype=UnifiedPCWindows&version=f254181d&pass_ticket=test-pass"
            ),
        ]

        session = extract_session_from_lines(lines)

        self.assertEqual(session["appmsg_token"], "query-token")
        self.assertEqual(session["wxtokenkey"], "888")
        self.assertEqual(session["pass_ticket"], "test-pass")

    def test_extract_session_from_flow_parts_uses_query_token_when_cookie_missing(self):
        session = extract_session_from_flow_parts(
            (
                "https://mp.weixin.qq.com/mp/jsmonitor?uin=ODk2ODQwNjAw"
                "&key=test-key&pass_ticket=test-pass&wxtoken=777"
                "&devicetype=UnifiedPCWindows&version=f254181d"
                "&__biz=Mzk0ODM5NTEyNA%3D%3D&appmsg_token=query-token&x5=0&f=json"
            ),
            {"referer": "https://mp.weixin.qq.com/s?__biz=Mzk0ODM5NTEyNA==&mid=2247505811&idx=1&sn=test-sn"},
        )

        self.assertIsNotNone(session)
        self.assertEqual(session["appmsg_token"], "query-token")
        self.assertEqual(session["wxtokenkey"], "777")

    def test_extract_session_from_flow_parts_keeps_full_cookie_header(self):
        cookie_header = "foo=bar; appmsg_token=cookie-token; wap_sid2=wap-value"

        session = extract_session_from_flow_parts(
            "https://mp.weixin.qq.com/mp/jsmonitor?uin=ODk2ODQwNjAw&key=test-key",
            {"cookie": cookie_header},
        )

        self.assertIsNotNone(session)
        self.assertEqual(session["cookie_header"], cookie_header)
        self.assertEqual(session["appmsg_token"], "cookie-token")
        self.assertEqual(session["wap_sid2"], "wap-value")

    def test_extract_live_overrides_includes_query_appmsg_token(self):
        log_text = (
            "POST https://mp.weixin.qq.com/mp/jsmonitor?uin=ODk2ODQwNjAw"
            "&key=test-key&pass_ticket=test-pass&wxtoken=777"
            "&devicetype=UnifiedPCWindows&version=f254181d"
            "&__biz=Mzk0ODM5NTEyNA%3D%3D&appmsg_token=query-token&x5=0&f=json\n"
            "referer: https://mp.weixin.qq.com/s?__biz=Mzk0ODM5NTEyNA=="
            "&mid=2247505811&idx=1&sn=test-sn&key=test-key&uin=ODk2ODQwNjAw"
            "&devicetype=UnifiedPCWindows&version=f254181d&pass_ticket=test-pass\n"
        )

        overrides = extract_live_overrides(log_text)

        self.assertEqual(overrides["key"], "test-key")
        self.assertEqual(overrides["uin"], "ODk2ODQwNjAw")
        self.assertEqual(overrides["pass_ticket"], "test-pass")
        self.assertEqual(overrides["appmsg_token"], "query-token")
        self.assertEqual(overrides["wxtokenkey"], "777")

    def test_extract_session_from_lines_reads_full_cookie_header(self):
        lines = [
            "cookie_header: foo=bar; appmsg_token=cookie-token; wap_sid2=wap-value",
            (
                "referer: https://mp.weixin.qq.com/s?__biz=Mzk0ODM5NTEyNA=="
                "&mid=2247505811&idx=1&sn=test-sn&key=test-key&uin=ODk2ODQwNjAw"
                "&devicetype=UnifiedPCWindows&version=f254181d&pass_ticket=test-pass"
            ),
        ]

        session = extract_session_from_lines(lines)

        self.assertEqual(session["cookie_header"], "foo=bar; appmsg_token=cookie-token; wap_sid2=wap-value")
        self.assertEqual(session["appmsg_token"], "cookie-token")
        self.assertEqual(session["wap_sid2"], "wap-value")

    def test_write_session_file_preserves_existing_non_empty_values(self):
        with TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "captured_at": "2026-04-06T18:40:00+08:00",
                        "key": "old-key",
                        "uin": "old-uin",
                        "pass_ticket": "old-pass",
                        "appmsg_token": "old-token",
                        "wap_sid2": "old-wap",
                        "wxuin": "old-wxuin",
                        "wxtokenkey": "777",
                        "cookie_header": "foo=bar; appmsg_token=old-token; wap_sid2=old-wap",
                        "devicetype": "UnifiedPCWindows",
                        "version": "f254181d",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            write_session_file(
                {
                    "captured_at": "2026-04-06T18:51:35+08:00",
                    "key": "new-key",
                    "uin": "new-uin",
                    "pass_ticket": "new-pass",
                    "appmsg_token": "",
                    "wap_sid2": "",
                    "wxuin": "",
                    "wxtokenkey": "777",
                    "cookie_header": "",
                    "devicetype": "UnifiedPCWindows",
                    "version": "f254181d",
                },
                session_path,
            )

            merged = json.loads(session_path.read_text(encoding="utf-8"))

        self.assertEqual(merged["key"], "new-key")
        self.assertEqual(merged["uin"], "new-uin")
        self.assertEqual(merged["pass_ticket"], "new-pass")
        self.assertEqual(merged["appmsg_token"], "old-token")
        self.assertEqual(merged["wap_sid2"], "old-wap")
        self.assertEqual(merged["wxuin"], "old-wxuin")
        self.assertEqual(merged["cookie_header"], "foo=bar; appmsg_token=old-token; wap_sid2=old-wap")

    def test_parse_cookie_header_supports_comma_separated_proxy_format(self):
        cookies = parse_cookie_header(
            "wxtokenkey=777, wxuin=896840600, appmsg_token=query-token, "
            "pass_ticket=test-pass, wap_sid2=wap-value"
        )

        self.assertEqual(cookies["wxtokenkey"], "777")
        self.assertEqual(cookies["wxuin"], "896840600")
        self.assertEqual(cookies["appmsg_token"], "query-token")
        self.assertEqual(cookies["pass_ticket"], "test-pass")
        self.assertEqual(cookies["wap_sid2"], "wap-value")

    def test_extract_article_query_falls_back_to_referer(self):
        article_query = _extract_article_query(
            "https://mp.weixin.qq.com/mp/getappmsgext?f=json",
            (
                "https://mp.weixin.qq.com/s?__biz=MzUxNjg4NDEzNA=="
                "&mid=2247532690&idx=1&sn=aab67b46905b4219088b3d88f6f40ddb"
            ),
        )

        self.assertEqual(article_query["__biz"], "MzUxNjg4NDEzNA==")
        self.assertEqual(article_query["mid"], "2247532690")
        self.assertEqual(article_query["idx"], "1")
        self.assertEqual(article_query["sn"], "aab67b46905b4219088b3d88f6f40ddb")

    def test_write_article_request_snapshot_persists_per_article_file(self):
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            snapshot = {
                "captured_at": "2026-04-06T21:00:00+08:00",
                "action": "getappmsgext",
                "request_url": "https://mp.weixin.qq.com/mp/getappmsgext?__biz=Qkl6&mid=1&idx=1&sn=abc",
                "response_payload": {"base_resp": {"ret": 0}},
            }
            article_query = {"__biz": "Qkl6", "mid": "1", "idx": "1", "sn": "abc"}

            with self.settings():
                from scripts.lipeaks_viral_articles.scripts import wechat_stats_mitm_addon as addon

                original_dir = addon.ARTICLE_SNAPSHOTS_DIR
                addon.ARTICLE_SNAPSHOTS_DIR = temp_root
                try:
                    write_article_request_snapshot(snapshot, article_query)
                finally:
                    addon.ARTICLE_SNAPSHOTS_DIR = original_dir

            snapshot_path = temp_root / "Qkl6__1__1" / "getappmsgext.json"
            self.assertTrue(snapshot_path.exists())
            payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["request_url"], snapshot["request_url"])
