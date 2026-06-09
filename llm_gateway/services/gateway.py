from llm_gateway.schemas.requests import MarkdownFormatRequest, WechatArticleSearchRequest
from llm_gateway.services.run_manager import RunManager


class LLMGatewayService:
    @staticmethod
    def search_wechat_articles(*, query, limit=10, requested_by_app=""):
        request = WechatArticleSearchRequest(query=query, limit=limit)
        result = RunManager.run_capability(
            capability="wechat_article_search",
            input_payload=request.model_dump(),
            requested_by_app=requested_by_app,
        )
        if not result:
            return {
                "query": query,
                "total": 0,
                "items": [],
                "executor": "",
                "raw_text": "",
            }
        return {key: value for key, value in result.items() if key != "used_skill"}

    @staticmethod
    def format_markdown(*, content, mode="gentle", requested_by_app=""):
        request = MarkdownFormatRequest(content=content, mode=mode)
        result = RunManager.run_capability(
            capability="markdown_format",
            input_payload=request.model_dump(),
            requested_by_app=requested_by_app,
        )
        if not result:
            return {
                "formatted_markdown": "",
                "executor": "",
            }
        return {
            key: value
            for key, value in result.items()
            if key not in {"used_skill", "raw_text"}
        }
