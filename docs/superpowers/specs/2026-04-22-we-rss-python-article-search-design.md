# We-rss Python article search design

This document defines how `GET /api/v1/we-rss/articles/search/` moves from the
current `llm_gateway -> codex skill` chain to a native Python implementation
inside `we_rss`, while keeping Sogou Weixin search as the upstream source.

The goal is to preserve the existing frontend contract and remove the LLM
execution dependency from this specific request path.

## Goals

This change keeps the public API stable while simplifying the backend path.

- Keep the existing route: `/api/v1/we-rss/articles/search/`.
- Keep the existing request parameters: `query` and `limit`.
- Keep the existing response shape: `query`, `total`, and `items`.
- Continue using Sogou Weixin search as the upstream source.
- Remove `llm_gateway` from this execution path entirely.
- Keep the implementation inside `we_rss`.

## Non-goals

This change intentionally stays narrow.

- Do not change `/api/v1/we-rss/feeds/search/`.
- Do not add any LLM fallback for article search.
- Do not resolve Sogou redirect URLs to final `mp.weixin.qq.com` article URLs
  in this version.
- Do not add new persistence for search results.
- Do not remove the old `llm_gateway` capability from the repository yet.

## Current state

Today, `ArticleViewSet.search()` delegates to
`we_rss.services.article_search_service.ArticleSearchService`. That service
calls `LLMGatewayService.search_wechat_articles(...)`, which ultimately invokes
the shared `wechat-article-search` skill script through the LLM execution
stack.

That path is heavier than necessary for a deterministic scrape task and adds
operational dependencies that this endpoint does not need.

## Proposed approach

Use a dedicated Python service in `we_rss` that performs the same deterministic
Sogou search flow directly:

1. Fetch a Sogou cookie from `https://v.sogou.com/v?...`.
2. Request Sogou Weixin search pages with `type=2`.
3. Decode the returned HTML robustly.
4. Parse article items from the HTML.
5. Normalize the parsed items into the existing API response shape.

The recommended new service file is:

- `we_rss/services/sogou_article_search_service.py`

`ArticleSearchService` remains the app-facing facade so views and tests keep a
small stable boundary.

## Architecture

The implementation uses two layers so the scraping details stay isolated from
view-level API behavior.

### Sogou article search service

`SogouArticleSearchService` is responsible for:

- HTTP headers and user-agent rotation.
- Cookie bootstrap.
- HTML download.
- Charset and compression handling.
- HTML parsing.
- Pagination across Sogou result pages.
- Returning plain Python dictionaries for article items.

This service must not know about DRF serializers or response envelopes.

### Article search facade

`ArticleSearchService` remains responsible for:

- Calling the native Sogou service.
- Repairing mojibake where safe.
- Normalizing field names and empty values.
- Returning the final payload shape expected by the serializer:
  - `query`
  - `total`
  - `items`

This preserves the current boundary used by `ArticleViewSet.search()`.

## Data contract

The API contract stays unchanged.

Input:

- `query`: required string.
- `limit`: optional integer, default `10`, maximum `50`.

Output:

- `query`: normalized query string.
- `total`: number of returned items.
- `items`: list of objects with:
  - `title`
  - `url`
  - `summary`
  - `datetime`
  - `date_text`
  - `date_description`
  - `source`

The upstream Sogou parser may internally use `articles`, but the public service
must always expose `items`.

## Parsing behavior

The Python service should mirror the existing skill behavior closely enough to
avoid frontend regressions.

- Parse from `ul.news-list > li`.
- Read the title and Sogou article URL from `h3 a`.
- Read the summary from `p.txt-info`.
- Read source and time metadata from the `.s-p` block.
- Support both explicit timestamps and relative time text.
- Return at most `limit` items, capped at `50`.
- Request multiple pages when `limit > 10`.

## Failure handling

This endpoint is best-effort search, not a hard business transaction. The API
must prefer stable responses over surfacing scraper failures to end users.

- On request, decoding, or parsing failure, return:
  - the input `query`
  - `total = 0`
  - `items = []`
- Do not raise a `500` for expected upstream instability.
- Keep validation errors for bad input in the existing serializer layer.

This matches the current user expectation that search failures degrade to empty
results rather than breaking the page.

## Why this design

This design is recommended over the current LLM-driven chain for three reasons.

- It removes an unnecessary orchestration layer for deterministic scraping.
- It reduces latency and operational complexity.
- It keeps the public contract stable, so the frontend does not need to change.

## Testing strategy

The change needs focused coverage in `we_rss`.

- Add service tests for parsing and normalization.
- Update article search service tests to patch the native Sogou service instead
  of `LLMGatewayService`.
- Keep API tests validating the existing response shape.
- Update schema-facing tests and descriptions if they mention
  `llm_gateway`.

## Risks and limits

This design still depends on Sogou HTML structure and anti-bot behavior.

- Markup changes can reduce or break parsing accuracy.
- Cookie bootstrap can fail intermittently.
- Some returned URLs may remain Sogou redirect URLs in this version.

These risks already exist today in the skill-based implementation. This change
does not introduce them; it only moves the logic into deterministic Python code
owned by the app.

## Next steps

Implement the native Sogou service, refactor `ArticleSearchService` to call it,
update the endpoint description, and run the focused `we_rss` regression tests.
