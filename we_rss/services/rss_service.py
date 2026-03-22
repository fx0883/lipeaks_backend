from xml.sax.saxutils import escape


class RssService:
    @staticmethod
    def _format_item(article):
        title = escape(article.title or "Untitled")
        description = escape(article.description or "")
        link = escape(article.url or "")
        guid = escape(article.source_id or str(article.id))
        pub_date = escape(article.publish_time.isoformat() if article.publish_time else article.created_at.isoformat())
        return (
            "<item>"
            f"<title>{title}</title>"
            f"<description>{description}</description>"
            f"<link>{link}</link>"
            f"<guid>{guid}</guid>"
            f"<pubDate>{pub_date}</pubDate>"
            "</item>"
        )

    @staticmethod
    def build_feed_xml(*, title, description, link, articles):
        items = "".join(RssService._format_item(article) for article in articles)
        safe_title = escape(title)
        safe_description = escape(description)
        safe_link = escape(link)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<rss version=\"2.0\">"
            "<channel>"
            f"<title>{safe_title}</title>"
            f"<description>{safe_description}</description>"
            f"<link>{safe_link}</link>"
            f"{items}"
            "</channel>"
            "</rss>"
        )

    @staticmethod
    def build_tenant_rss(*, tenant, articles):
        return RssService.build_feed_xml(
            title=f"{tenant.name} We RSS",
            description=f"Authenticated RSS feed for {tenant.name}",
            link="https://example.com/api/v1/we-rss/rss/",
            articles=articles,
        )

    @staticmethod
    def build_feed_rss(*, feed, articles):
        return RssService.build_feed_xml(
            title=feed.mp_name,
            description=feed.mp_intro or f"Authenticated RSS feed for {feed.mp_name}",
            link=f"https://example.com/api/v1/we-rss/rss/{feed.id}/",
            articles=articles,
        )

    @staticmethod
    def build_article_content(*, article):
        return article.content or ""
