from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils.dateparse import parse_datetime

from scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext import collect_stats


class WechatStatsCollectorTests(SimpleTestCase):
    def test_collect_stats_prefers_article_html_query_and_uses_canonical_referer(self):
        article_url = "https://mp.weixin.qq.com/s?__biz=Qkl6&mid=2247486397&idx=1&sn=abcdef"

        with patch(
            "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.load_session_file",
            return_value={
                "key": "session-key",
                "uin": "session-uin",
                "pass_ticket": "session-pass",
            },
        ):
            with patch(
                "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.load_live_overrides",
                return_value={},
            ):
                with patch(
                    "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.fetch_article_html",
                    return_value="""
                    <html>
                      <script>
                        var biz = "HTML_BIZ";
                        var sn = "html-sn";
                        var mid = "2247555555";
                        var idx = "2";
                      </script>
                    </html>
                    """,
                ):
                    with patch(
                        "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.extract_article_query_from_html",
                        return_value={
                            "__biz": "HTML_BIZ",
                            "mid": "2247555555",
                            "idx": "2",
                            "sn": "html-sn",
                        },
                    ):
                        with patch(
                            "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.replay_getappmsgext",
                            return_value={"appmsgstat": {"read_num": 18}},
                        ) as replay_mock:
                            with patch(
                                "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.extract_article_comment_metadata",
                                return_value={"comment_count": 3},
                            ):
                                with patch(
                                    "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.replay_appmsg_comment",
                                    return_value={"base_resp": {"ret": -1, "errmsg": "comment metadata missing"}},
                                ) as comment_mock:
                                    result = collect_stats(
                                        article_url=article_url,
                                        session_file=Path("session.json"),
                                        live_log_file=Path("proxy-live.log"),
                                    )

        query, _cookies = replay_mock.call_args.args[:2]
        self.assertEqual(query["__biz"], "HTML_BIZ")
        self.assertEqual(query["mid"], "2247555555")
        self.assertEqual(query["idx"], "2")
        self.assertEqual(query["sn"], "html-sn")
        expected_referer = (
            "https://mp.weixin.qq.com/s?__biz=HTML_BIZ&mid=2247555555&idx=2&sn=html-sn"
            "&key=session-key&uin=session-uin&pass_ticket=session-pass"
            "&devicetype=UnifiedPCWindows"
        )
        self.assertEqual(
            replay_mock.call_args.kwargs["referer_url"],
            expected_referer,
        )
        self.assertEqual(
            comment_mock.call_args.args[3],
            expected_referer,
        )
        self.assertEqual(result["read_num"], 18)

    def test_collect_stats_prefers_captured_live_requests_when_present(self):
        article_url = "https://mp.weixin.qq.com/s/demo-short-link"
        live_lines = [
            "POST https://mp.weixin.qq.com/mp/getappmsgext?__biz=HTML_BIZ&mid=2247555555&idx=2&sn=html-sn",
            "referer: https://mp.weixin.qq.com/s?__biz=HTML_BIZ&mid=2247555555&idx=2&sn=html-sn",
            "cookie_header: wxtokenkey=777, appmsg_token=captured-token, pass_ticket=captured-pass",
            (
                "GET https://mp.weixin.qq.com/mp/appmsg_comment?action=getcomment"
                "&__biz=HTML_BIZ&appmsgid=2247555555&idx=2&comment_id=comment-1"
            ),
            "referer: https://mp.weixin.qq.com/s?__biz=HTML_BIZ&mid=2247555555&idx=2&sn=html-sn",
            "cookie_header: wxtokenkey=777, appmsg_token=captured-token, pass_ticket=captured-pass",
        ]

        with patch(
            "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.load_session_file",
            return_value={
                "key": "session-key",
                "uin": "session-uin",
                "pass_ticket": "session-pass",
            },
        ):
            with patch(
                "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.read_lines",
                return_value=live_lines,
            ):
                with patch(
                    "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.load_live_overrides",
                    return_value={},
                ):
                    with patch(
                        "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.fetch_article_html",
                        return_value="<html></html>",
                    ):
                        with patch(
                            "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.extract_article_query_from_html",
                            return_value={
                                "__biz": "HTML_BIZ",
                                "mid": "2247555555",
                                "idx": "2",
                                "sn": "html-sn",
                            },
                        ):
                            with patch(
                                "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.extract_article_comment_metadata",
                                return_value={
                                    "appmsgid": "2247555555",
                                    "comment_id": "comment-1",
                                },
                            ):
                                with patch(
                                    "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.replay_captured_request",
                                    side_effect=[
                                        {"appmsgstat": {"read_num": 66}},
                                        {
                                            "base_resp": {"ret": 0},
                                            "elected_comment_total_cnt": 5,
                                            "elected_comment": [],
                                        },
                                    ],
                                ) as captured_mock:
                                    with patch(
                                        "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.replay_getappmsgext",
                                        side_effect=AssertionError("should prefer captured getappmsgext"),
                                    ):
                                        with patch(
                                            "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.replay_appmsg_comment",
                                            side_effect=AssertionError("should prefer captured comment request"),
                                        ):
                                            result = collect_stats(
                                                article_url=article_url,
                                                session_file=Path(__file__),
                                                live_log_file=Path(__file__),
                                            )

        self.assertEqual(captured_mock.call_count, 2)
        self.assertEqual(result["read_num"], 66)
        self.assertEqual(result["comment_count"], 5)

    def test_collect_stats_extracts_publish_time_from_article_script_and_returns_utc_iso(self):
        article_url = "https://mp.weixin.qq.com/s/demo-short-link"
        article_html = """
        <html>
          <script>
            var biz = "HTML_BIZ";
            var sn = "html-sn";
            var mid = "2247555555";
            var idx = "2";
            var oriCreateTime = '1775355233';
            var createTime = '2026-04-05 10:13';
          </script>
        </html>
        """

        with patch(
            "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.load_session_file",
            return_value={
                "key": "session-key",
                "uin": "session-uin",
                "pass_ticket": "session-pass",
            },
        ):
            with patch(
                "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.load_live_overrides",
                return_value={},
            ):
                with patch(
                    "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.fetch_article_html",
                    return_value=article_html,
                ):
                    with patch(
                        "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.extract_article_query_from_html",
                        return_value={
                            "__biz": "HTML_BIZ",
                            "mid": "2247555555",
                            "idx": "2",
                            "sn": "html-sn",
                        },
                    ):
                        with patch(
                            "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.replay_getappmsgext",
                            return_value={"appmsgstat": {"read_num": 18}},
                        ):
                            with patch(
                                "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.extract_article_comment_metadata",
                                return_value={"comment_count": 3},
                            ):
                                with patch(
                                    "scripts.lipeaks_viral_articles.scripts.wechat_replay_getappmsgext.replay_appmsg_comment",
                                    return_value={"base_resp": {"ret": -1, "errmsg": "comment metadata missing"}},
                                ):
                                    result = collect_stats(
                                        article_url=article_url,
                                        session_file=Path("session.json"),
                                        live_log_file=Path("proxy-live.log"),
                                    )

        self.assertEqual(result["publish_time"], "2026-04-05T02:13:00Z")
        self.assertEqual(parse_datetime(result["publish_time"]).isoformat(), "2026-04-05T02:13:00+00:00")
