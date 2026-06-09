import json

from llm_gateway.services.text_fixes import repair_utf8_as_gbk_mojibake


class ResultNormalizer:
    @staticmethod
    def _looks_like_interactive_follow_up(text):
        normalized = str(text or "").strip().lower()
        if not normalized:
            return False

        suspicious_markers = (
            "i need the source content first",
            "the content itself wasn't included",
            "paste the text",
            "give me the file path",
            "send either:",
            "send the bounded task",
            "files or subsystem in scope",
            "once you provide that",
            "subagent-driven-development",
            "if the source is already markdown",
            "if you don't specify",
        )
        return any(marker in normalized for marker in suspicious_markers)

    @staticmethod
    def _normalize_article_item(item):
        if not isinstance(item, dict):
            return None

        url = str(item.get("url") or "").strip()
        if not url:
            return None

        normalized = {}
        for key, value in item.items():
            if value is None:
                continue
            if isinstance(value, str):
                normalized[key] = repair_utf8_as_gbk_mojibake(value).strip()
            else:
                normalized[key] = value

        normalized["url"] = url
        normalized["title"] = repair_utf8_as_gbk_mojibake(normalized.get("title") or "").strip()
        return normalized

    @staticmethod
    def _coerce_items(parsed):
        candidates = parsed.get("items")
        if not isinstance(candidates, list):
            candidates = parsed.get("articles")
        if not isinstance(candidates, list):
            return []

        normalized = []
        for item in candidates:
            normalized_item = ResultNormalizer._normalize_article_item(item)
            if normalized_item is not None:
                normalized.append(normalized_item)
        return normalized

    @staticmethod
    def normalize(*, capability, raw_stdout, executor_name, used_skill):
        if capability == "wechat_article_search":
            try:
                parsed = json.loads(raw_stdout)
            except json.JSONDecodeError:
                return {
                    "items": [],
                    "total": 0,
                    "query": "",
                    "executor": executor_name,
                    "used_skill": used_skill,
                    "raw_text": raw_stdout,
                }

            items = ResultNormalizer._coerce_items(parsed)
            return {
                "items": items,
                "total": parsed.get("total", len(items)),
                "query": parsed.get("query", ""),
                "executor": executor_name,
                "used_skill": used_skill,
                "raw_text": raw_stdout,
            }

        if capability == "markdown_format":
            formatted_markdown = str(raw_stdout or "").strip()
            if not formatted_markdown:
                raise ValueError("Formatted markdown content is empty.")
            if ResultNormalizer._looks_like_interactive_follow_up(formatted_markdown):
                raise ValueError("Formatted markdown content is not usable Markdown output.")
            return {
                "formatted_markdown": formatted_markdown,
                "executor": executor_name,
                "used_skill": used_skill,
                "raw_text": raw_stdout,
            }

        raise ValueError(f"Unsupported capability: {capability}")
