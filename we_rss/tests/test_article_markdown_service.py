from unittest.mock import patch

from django.test import SimpleTestCase

from we_rss.services.article_markdown_service import ArticleMarkdownService


class FakeResponse:
    def __init__(self, *, text="", url=""):
        self.text = text
        self.url = url

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.requested_urls = []
        self.headers = {}

    def get(self, url, timeout):
        self.requested_urls.append((url, timeout))
        return self.response


class ArticleMarkdownServiceTests(SimpleTestCase):
    def test_fetch_markdown_from_wechat_url_returns_document_without_images(self):
        html = """
        <html>
          <head>
            <meta property="og:title" content="测试文章" />
          </head>
          <body>
            <div id="js_name">测试公众号</div>
            <span id="js_author_name">测试作者</span>
            <em id="publish_time">2026-05-03 12:30</em>
            <div>微信扫一扫赞赏作者</div>
            <div id="js_content">
              <p>第一段正文</p>
              <p><img src="https://example.com/a.png" alt="封面图" /></p>
              <p>第二段正文</p>
            </div>
            <div>写留言</div>
          </body>
        </html>
        """
        session = FakeSession(FakeResponse(text=html, url="https://mp.weixin.qq.com/s/test?token=123"))
        service = ArticleMarkdownService(session_factory=lambda: session)

        markdown = service.fetch_markdown_from_url("https://mp.weixin.qq.com/s/test?token=123")

        self.assertIn("# 测试文章", markdown)
        self.assertIn("> 公众号: 测试公众号", markdown)
        self.assertIn("> 作者: 测试作者", markdown)
        self.assertIn("> 日期: 2026-05-03", markdown)
        self.assertIn("第一段正文", markdown)
        self.assertIn("第二段正文", markdown)
        self.assertNotIn("![", markdown)
        self.assertNotIn("https://example.com/a.png", markdown)
        self.assertNotIn("赞赏作者", markdown)
        self.assertNotIn("写留言", markdown)
        self.assertEqual(session.requested_urls, [("https://mp.weixin.qq.com/s/test", 120)])

    def test_fetch_markdown_from_wechat_url_removes_recommended_reading_footer(self):
        history_marker = "\u5386\u53f2\u76d8\u70b9"
        recommended_marker = "\u63a8\u8350\u9605\u8bfb"
        html = f"""
        <html>
          <head>
            <meta property="og:title" content="Test Article" />
            <meta property="og:description" content="Summary" />
          </head>
          <body>
            <div id="js_name">Test Feed</div>
            <div id="js_content">
              <p>Intro body.</p>
              <p>Useful content.</p>
              <p>{history_marker}</p>
              <p>Footer links.</p>
              <p>{recommended_marker} 1. Link A 2. Link B</p>
            </div>
          </body>
        </html>
        """
        session = FakeSession(FakeResponse(text=html, url="https://mp.weixin.qq.com/s/test-footer?token=123"))
        service = ArticleMarkdownService(session_factory=lambda: session)

        markdown = service.fetch_markdown_from_url("https://mp.weixin.qq.com/s/test-footer?token=123")

        self.assertIn("Intro body.", markdown)
        self.assertIn("Useful content.", markdown)
        self.assertNotIn(history_marker, markdown)
        self.assertNotIn("Footer links.", markdown)
        self.assertNotIn(recommended_marker, markdown)

    def test_fetch_markdown_from_wechat_url_raises_when_body_missing(self):
        html = """
        <html>
          <head>
            <meta property="og:title" content="测试文章" />
          </head>
          <body>
            <div>微信扫一扫赞赏作者</div>
            <div>写留言</div>
          </body>
        </html>
        """
        session = FakeSession(FakeResponse(text=html, url="https://mp.weixin.qq.com/s/test?token=123"))
        service = ArticleMarkdownService(session_factory=lambda: session)

        with self.assertRaisesMessage(ValueError, "Wechat article content is empty."):
            service.fetch_markdown_from_url("https://mp.weixin.qq.com/s/test?token=123")

    def test_fetch_markdown_from_regular_url_uses_requests_and_html2text(self):
        html = """
        <html>
          <head><title>Regular Page</title></head>
          <body>
            <main>
              <h1>Regular Page</h1>
              <p>Body text.</p>
              <img src="https://example.com/image.png" alt="Image" />
            </main>
          </body>
        </html>
        """
        session = FakeSession(FakeResponse(text=html, url="https://example.com/page"))
        service = ArticleMarkdownService(session_factory=lambda: session)

        markdown = service.fetch_markdown_from_url("https://example.com/page")

        self.assertIn("# Regular Page", markdown)
        self.assertIn("Body text.", markdown)
        self.assertNotIn("![", markdown)
        self.assertNotIn("https://example.com/image.png", markdown)
        self.assertEqual(session.requested_urls, [("https://example.com/page", 120)])


class ArticleMarkdownServiceIntegrationTests(SimpleTestCase):
    @patch("we_rss.services.article_service.get_article_markdown_service")
    def test_refresh_article_markdown_uses_new_service_without_credentials(self, service_factory):
        from we_rss.services.article_service import ArticleService

        class FakeArticle:
            url = "https://mp.weixin.qq.com/s/article-1"
            content = ""

            def save(self, update_fields):
                self.saved_update_fields = update_fields

        class FakeService:
            def __init__(self):
                self.urls = []

            def fetch_markdown_from_url(self, url):
                self.urls.append(url)
                return "# Markdown"

        fake_service = FakeService()
        service_factory.return_value = fake_service
        article = FakeArticle()

        markdown = ArticleService.refresh_article_markdown(
            article=article,
            sleep_seconds=0,
        )

        self.assertEqual(markdown, "# Markdown")
        self.assertEqual(article.content, "# Markdown")
        self.assertEqual(article.saved_update_fields, ["content", "updated_at"])
        self.assertEqual(fake_service.urls, ["https://mp.weixin.qq.com/s/article-1"])
