from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import ANY, patch

from django.test import SimpleTestCase

from we_rss.services.sogou_article_search_service import (
    SOGOU_SEARCH_TIMEZONE,
    SogouArticleSearchService,
)


class SogouArticleSearchServiceTests(SimpleTestCase):
    def test_parse_search_html_extracts_full_public_article_fields(self):
        published_at = datetime(2026, 4, 21, 8, 0, tzinfo=dt_timezone.utc)
        timestamp = int(published_at.timestamp())
        html = f"""
        <html>
          <body>
            <ul class="news-list">
              <li>
                <h3>
                  <a href="/link?url=https%3A%2F%2Fmp.weixin.qq.com%2Fs%2Farticle-1">AI Agent \u5b9e\u6218</a>
                </h3>
                <p class="txt-info">Summary text</p>
                <div class="s-p">
                  <span class="s2"><script>document.write(timeConvert('{timestamp}'))</script></span>
                  <a class="account">OpenAI</a>
                </div>
              </li>
            </ul>
          </body>
        </html>
        """

        with patch(
            "we_rss.services.sogou_article_search_service.SogouArticleSearchService._describe_relative_time",
            return_value="1\u5929\u524d",
        ):
            items = SogouArticleSearchService._parse_search_html(html, max_results=10)

        self.assertEqual(
            items,
            [
                {
                    "title": "AI Agent \u5b9e\u6218",
                    "url": "https://weixin.sogou.com/link?url=https%3A%2F%2Fmp.weixin.qq.com%2Fs%2Farticle-1",
                    "summary": "Summary text",
                    "datetime": "2026-04-21 16:00:00",
                    "date_text": "2026\u5e7404\u670821\u65e5",
                    "date_description": "1\u5929\u524d",
                    "source": "OpenAI",
                }
            ],
        )

    def test_parse_relative_time_supports_relative_and_absolute_formats(self):
        fixed_now = datetime(2026, 4, 22, 12, 0, tzinfo=SOGOU_SEARCH_TIMEZONE)

        class FrozenDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed_now if tz is not None else fixed_now.replace(tzinfo=None)

        with patch("we_rss.services.sogou_article_search_service.datetime", FrozenDateTime):
            self.assertEqual(
                SogouArticleSearchService._parse_relative_time("2\u5929\u524d"),
                fixed_now - timedelta(days=2),
            )
            self.assertEqual(
                SogouArticleSearchService._parse_relative_time("2026-04-20"),
                datetime(2026, 4, 20, 0, 0, tzinfo=SOGOU_SEARCH_TIMEZONE),
            )
            self.assertEqual(
                SogouArticleSearchService._parse_relative_time("04\u670821\u65e5"),
                datetime(2026, 4, 21, 0, 0, tzinfo=SOGOU_SEARCH_TIMEZONE),
            )

    @patch("we_rss.services.sogou_article_search_service.SogouArticleSearchService._search_mobile_web_fallback")
    @patch("we_rss.services.sogou_article_search_service.SogouArticleSearchService._search_weixin_pages")
    def test_search_wechat_articles_returns_empty_items_when_all_strategies_fail(
        self,
        search_weixin_pages_mock,
        search_mobile_web_fallback_mock,
    ):
        search_weixin_pages_mock.side_effect = RuntimeError("boom")
        search_mobile_web_fallback_mock.return_value = []

        result = SogouArticleSearchService.search_wechat_articles(
            query="AI Agent",
            limit=3,
        )

        self.assertEqual(
            result,
            {
                "query": "AI Agent",
                "total": 0,
                "items": [],
            },
        )
        search_mobile_web_fallback_mock.assert_not_called()

    @patch("we_rss.services.sogou_article_search_service.SogouArticleSearchService._warmup_session")
    @patch("we_rss.services.sogou_article_search_service.SogouArticleSearchService._build_session")
    @patch("we_rss.services.sogou_article_search_service.SogouArticleSearchService._fetch_search_page")
    def test_search_wechat_articles_still_returns_results_when_warmup_fails(
        self,
        fetch_search_page_mock,
        build_session_mock,
        warmup_session_mock,
    ):
        build_session_mock.return_value = object()
        warmup_session_mock.side_effect = RuntimeError("warmup failed")
        fetch_search_page_mock.return_value = """
        <html>
          <body>
            <ul class="news-list">
              <li>
                <h3><a href="/article-1">Skills article</a></h3>
                <p class="txt-info">Summary text</p>
                <div class="s-p">
                  <span class="all-time-y2">OpenAI</span>
                </div>
              </li>
            </ul>
          </body>
        </html>
        """

        result = SogouArticleSearchService.search_wechat_articles(
            query="skills",
            limit=3,
        )

        self.assertEqual(result["query"], "skills")
        self.assertEqual(result["total"], 1)
        self.assertEqual(
            result["items"][0],
            {
                "title": "Skills article",
                "url": "https://weixin.sogou.com/article-1",
                "summary": "Summary text",
                "datetime": "",
                "date_text": "",
                "date_description": "",
                "source": "OpenAI",
            },
        )

    def test_extract_redirect_url_from_html_supports_split_url_assignment(self):
        html = """
        <meta content="always" name="referrer">
        <script>
          setTimeout(function () {
            var url = '';
            url += 'https://mp.';
            url += 'weixin.qq.com/s?src=11&timestamp=1';
            window.location.replace(url);
          }, 100);
        </script>
        """

        result = SogouArticleSearchService._extract_redirect_url_from_html(html)

        self.assertEqual(
            result,
            "https://mp.weixin.qq.com/s?src=11&timestamp=1",
        )

    def test_extract_canonical_wechat_url_from_html_builds_stable_public_url(self):
        html = """
        <html>
          <body>
            <script>
              window.biz = "MzA5NzQ1Mjg2NA==";
              window.mid = "2247486397";
              window.idx = "1";
              window.sn = "abcdef123456";
            </script>
          </body>
        </html>
        """

        result = SogouArticleSearchService._extract_canonical_wechat_url_from_html(
            html=html,
            fallback_url="https://mp.weixin.qq.com/s?src=11&timestamp=1&signature=abc",
        )

        self.assertEqual(
            result,
            "https://mp.weixin.qq.com/s?__biz=MzA5NzQ1Mjg2NA%3D%3D&mid=2247486397&idx=1&sn=abcdef123456",
        )

    @patch("we_rss.services.sogou_article_search_service.SogouArticleSearchService._resolve_canonical_wechat_url")
    def test_resolve_real_article_url_uses_redirect_page_extraction(self, resolve_canonical_url_mock):
        class FakeSession:
            def get(self, url, headers=None, timeout=None, allow_redirects=False):
                class Response:
                    status_code = 200
                    headers = {"Content-Type": "text/html; charset=utf-8"}
                    content = (
                        b"<script>var url='';url += 'https://mp.';url += 'weixin.qq.com/s?src=11';"
                        b"window.location.replace(url);</script>"
                    )

                return Response()

        resolve_canonical_url_mock.return_value = "https://mp.weixin.qq.com/s?__biz=Qkl6&mid=1&idx=1&sn=abc"

        result = SogouArticleSearchService._resolve_real_article_url(
            session=FakeSession(),
            url="https://weixin.sogou.com/link?url=test",
        )

        self.assertEqual(
            result,
            "https://mp.weixin.qq.com/s?__biz=Qkl6&mid=1&idx=1&sn=abc",
        )
        resolve_canonical_url_mock.assert_called_once_with(
            session=ANY,
            url="https://mp.weixin.qq.com/s?src=11",
        )

    def test_resolve_canonical_wechat_url_keeps_temporary_article_url_when_not_stable(self):
        candidate_url = (
            "https://mp.weixin.qq.com/s?src=11&timestamp=1&ver=1&signature=abc&new=1"
        )

        class FakeSession:
            def get(self, url, headers=None, timeout=None, allow_redirects=True):
                class Response:
                    status_code = 200
                    headers = {"Content-Type": "text/html; charset=utf-8"}
                    url = candidate_url
                    content = (
                        b"<script>"
                        b'var biz = "MzA5NzQ1Mjg2NA==";'
                        b'var mid = "2247486397";'
                        b'var idx = "1";'
                        b'var sn = "";'
                        b"</script>"
                    )

                return Response()

        result = SogouArticleSearchService._resolve_canonical_wechat_url(
            session=FakeSession(),
            url=candidate_url,
        )

        self.assertEqual(result, candidate_url)

    def test_resolve_canonical_wechat_url_ignores_captcha_redirect(self):
        candidate_url = (
            "https://mp.weixin.qq.com/s?src=11&timestamp=1&ver=1&signature=abc&new=1"
        )
        captcha_url = (
            "https://mp.weixin.qq.com/mp/wappoc_appmsgcaptcha"
            "?target_url=https%3A%2F%2Fmp.weixin.qq.com%2Fs%3F__biz%3DQkl6%26mid%3D1%26idx%3D1"
        )

        class FakeSession:
            def get(self, url, headers=None, timeout=None, allow_redirects=True):
                class Response:
                    status_code = 200
                    headers = {"Content-Type": "text/html; charset=utf-8"}
                    url = captcha_url
                    content = b"<html><body>captcha</body></html>"

                return Response()

        result = SogouArticleSearchService._resolve_canonical_wechat_url(
            session=FakeSession(),
            url=candidate_url,
        )

        self.assertEqual(result, candidate_url)

    def test_parse_mobile_web_search_html_extracts_article_result(self):
        html = """
        <html>
          <body>
            <div react_card_root="1">
              <a href="./tc?url=https%3A%2F%2Fmp.weixin.qq.com%2Fs%3Fsrc%3D11%26timestamp%3D1%26signature%3Dabc">
                <h2>Skills 到底是什么?</h2>
              </a>
              <div>Skills 是一个让 Claude 自动调用任务说明的机制。 微信公众号·微信公众平台 2026-04-08</div>
            </div>
          </body>
        </html>
        """

        result = SogouArticleSearchService._parse_mobile_web_search_html(
            html=html,
            max_results=5,
        )

        self.assertEqual(
            result,
            [
                {
                    "title": "Skills 到底是什么?",
                    "url": "https://mp.weixin.qq.com/s?src=11&timestamp=1&signature=abc",
                    "summary": "Skills 是一个让 Claude 自动调用任务说明的机制。",
                    "datetime": "2026-04-08 00:00:00",
                    "date_text": "2026年04月08日",
                    "date_description": "2026年04月08日",
                    "source": "微信公众号·微信公众平台",
                }
            ],
        )

    @patch("we_rss.services.sogou_article_search_service.SogouArticleSearchService._fetch_search_page_items_with_retries")
    def test_search_weixin_pages_combines_multiple_pages_and_skips_failed_page(self, fetch_page_items_mock):
        fetch_page_items_mock.side_effect = [
            {
                "items": [
                    {
                        "title": "page1-a",
                        "url": "https://mp.weixin.qq.com/s?src=11&signature=a",
                        "summary": "",
                        "datetime": "",
                        "date_text": "",
                        "date_description": "",
                        "source": "",
                    }
                ],
                "is_terminal_empty": False,
            },
            {"items": [], "is_terminal_empty": False},
            {
                "items": [
                    {
                        "title": "page3-a",
                        "url": "https://mp.weixin.qq.com/s?src=11&signature=b",
                        "summary": "",
                        "datetime": "",
                        "date_text": "",
                        "date_description": "",
                        "source": "",
                    }
                ],
                "is_terminal_empty": False,
            },
        ]

        result = SogouArticleSearchService._search_weixin_pages(
            query="skills",
            limit=30,
        )

        self.assertEqual(
            [item["title"] for item in result],
            ["page1-a", "page3-a"],
        )

    @patch("we_rss.services.sogou_article_search_service.SogouArticleSearchService._fetch_search_page_items_with_retries")
    def test_search_weixin_pages_stops_when_terminal_empty_page_is_reached(self, fetch_page_items_mock):
        fetch_page_items_mock.side_effect = [
            {
                "items": [
                    {
                        "title": "page1-a",
                        "url": "https://mp.weixin.qq.com/s?src=11&signature=a",
                        "summary": "",
                        "datetime": "",
                        "date_text": "",
                        "date_description": "",
                        "source": "",
                    }
                ],
                "is_terminal_empty": False,
            },
            {"items": [], "is_terminal_empty": True},
            {
                "items": [
                    {
                        "title": "page3-a",
                        "url": "https://mp.weixin.qq.com/s?src=11&signature=b",
                        "summary": "",
                        "datetime": "",
                        "date_text": "",
                        "date_description": "",
                        "source": "",
                    }
                ],
                "is_terminal_empty": False,
            },
        ]

        result = SogouArticleSearchService._search_weixin_pages(
            query="skills",
            limit=30,
        )

        self.assertEqual(
            [item["title"] for item in result],
            ["page1-a"],
        )
