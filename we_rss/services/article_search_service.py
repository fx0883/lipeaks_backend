from we_rss.services.sogou_article_search_service import SogouArticleSearchService
from we_rss.services.text_fixes import repair_utf8_as_gbk_mojibake


class ArticleSearchService:
    @staticmethod
    def search_wechat_articles(*, query, limit=10):
        try:
            result = SogouArticleSearchService.search_wechat_articles(
                query=query,
                limit=limit,
            )
        except Exception:
            result = {
                "query": str(query or "").strip(),
                "total": 0,
                "items": [],
            }

        items = []
        for item in result.get("items") or result.get("articles") or []:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "").strip()
            if not url:
                continue

            normalized_item = {}
            for key, value in item.items():
                if value is None:
                    continue
                if isinstance(value, str):
                    normalized_item[key] = repair_utf8_as_gbk_mojibake(value).strip()
                else:
                    normalized_item[key] = value

            normalized_item["url"] = url
            normalized_item["title"] = repair_utf8_as_gbk_mojibake(normalized_item.get("title") or "").strip()
            items.append(normalized_item)

        return {
            "query": str(result.get("query") or query).strip(),
            "total": int(result.get("total") or len(items)),
            "items": items,
        }
