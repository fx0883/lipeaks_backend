from llm_gateway.services.gateway import LLMGatewayService


class MarkdownFormatService:
    @staticmethod
    def format_content(*, content, mode="gentle"):
        result = LLMGatewayService.format_markdown(
            content=content,
            mode=mode,
            requested_by_app="we_rss",
        )
        return {
            "formatted_markdown": str(result.get("formatted_markdown") or ""),
            "mode": mode,
            "executor": str(result.get("executor") or ""),
        }
