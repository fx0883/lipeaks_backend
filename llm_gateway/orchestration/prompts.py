def build_executor_system_prompt():
    return (
        "You are the llm_gateway orchestration agent. "
        "You only create structured executor instructions for internal capabilities. "
        "Never invent shell commands, file paths, or skill names outside the provided hints."
    )


def build_wechat_search_prompt(*, query, limit, allowed_executors, preferred_executor):
    executors = ", ".join(allowed_executors)
    return (
        "Build a structured instruction for the internal capability "
        "'wechat_article_search'. "
        "Use the wechat-article-search skill only. "
        f"Allowed executors: {executors}. "
        f"Prefer {preferred_executor} unless a hard restriction requires another allowed executor. "
        "Return a JSON object with prompt, selected_executor, used_skill, and output_mode. "
        f"Search query: {query}. "
        f"Result limit: {limit}."
    )


def build_wechat_search_executor_prompt(*, script_path, query, limit):
    script = str(script_path)
    command = f'node "{script}" "{query}" -n {limit}'
    return (
        f"Run this exact shell command verbatim with no changes: {command}\n\n"
        "After the command completes, print only the command stdout with no markdown fences "
        "and no extra commentary."
    )


def build_markdown_format_prompt(*, mode, allowed_executors, preferred_executor):
    executors = ", ".join(allowed_executors)
    return (
        "Build a structured instruction for the internal capability 'markdown_format'. "
        "Use the baoyu-format-markdown skill only. "
        f"Allowed executors: {executors}. "
        f"Prefer {preferred_executor} unless a hard restriction requires another allowed executor. "
        "Return a JSON object with prompt, selected_executor, used_skill, and output_mode. "
        "The input text may already be Markdown or may be plain text. "
        f"Formatting mode: {mode}. "
        "The final output must be Markdown text only."
    )


def build_markdown_format_executor_prompt(*, content, mode):
    return (
        "Execute this single internal formatting request in non-interactive mode.\n"
        "Do not start any skill workflow or planning workflow.\n"
        "Format the provided content using the internal markdown-formatting standard.\n\n"
        "Requirements:\n"
        "- The input may already be Markdown or may be plain text.\n"
        "- The full source content is already included in this message.\n"
        "- Output Markdown only.\n"
        "- Preserve the original meaning.\n"
        '- `mode=\"gentle\"` means make only gentle fixes to typos, punctuation, spacing, and light structure.\n'
        "- Keep reasonable existing structure when possible.\n"
        "- Do not ask for more input.\n"
        "- Do not ask clarifying questions.\n"
        "- Do not inspect repository files, AGENTS.md, skill files, or any other instructions outside this prompt.\n"
        "- Do not run tools, use tools, or open files.\n"
        "- Do not say that content is missing.\n"
        "- Do not output explanations, summaries, JSON, diffs, or code fences around the whole result.\n\n"
        "Input content:\n"
        "<<MARKDOWN_INPUT>>\n"
        f"{content}\n"
        "<<END_MARKDOWN_INPUT>>"
    )
