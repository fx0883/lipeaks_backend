# WeChat official API alignment implementation plan

> **For agentic workers:** REQUIRED: Use
> `superpowers:subagent-driven-development` (if subagents available) or
> `superpowers:executing-plans` to implement this plan. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing convenience-style WeChat draft endpoints with a
1:1 backend mapping to the official WeChat media and draft APIs.

**Architecture:** Keep `GET /api/v1/wechat/accounts/` as-is, remove the four
old draft convenience endpoints, and add three explicit endpoints for
`uploadimg`, `add_material`, and `draft/add`. Route handlers remain thin,
service-layer code keeps the WeChat HTTP calls, and OpenAPI plus frontend docs
describe the new frontend call sequence.

**Tech Stack:** Django REST Framework, drf-spectacular, pytest / Django test
suite, Markdown docs.

---

## Chunk 1: Test and contract reset

### Task 1: Replace endpoint contract tests

**Files:**
- Modify: `tests/wechat/test_draft_api.py`
- Modify: `tests/wechat/test_draft_api_author_defaults.py`

- [ ] **Step 1: Write failing tests for the new routes**

Add tests that expect:
- `POST /api/v1/wechat/media/uploadimg/`
- `POST /api/v1/wechat/material/add-material/`
- `POST /api/v1/wechat/draft/add/`

Add schema assertions that the old convenience routes are gone.

- [ ] **Step 2: Run the focused tests to verify they fail**

Run:

```bash
pytest tests/wechat/test_draft_api.py tests/wechat/test_draft_api_author_defaults.py -q
```

Expected: failures for missing routes or mismatched schema entries.

- [ ] **Step 3: Remove tests for deleted endpoints and add new behavior checks**

Cover:
- `uploadimg` returns a WeChat-hosted `url`
- `add-material` returns `media_id` and optional `url`
- `draft/add` accepts `articles` JSON and forwards it
- author fallback still works when `draft/add` omits `author`

- [ ] **Step 4: Re-run the focused tests**

Run:

```bash
pytest tests/wechat/test_draft_api.py tests/wechat/test_draft_api_author_defaults.py -q
```

Expected: still failing until implementation lands, but only for missing
behavior.

## Chunk 2: Backend implementation

### Task 2: Add official API route handlers and serializers

**Files:**
- Modify: `wechat/serializers.py`
- Modify: `wechat/views.py`
- Modify: `wechat/urls.py`
- Modify: `wechat/services/wechat.py`

- [ ] **Step 1: Add request and response serializers for the three new endpoints**

Implement serializers for:
- single uploaded article image
- single permanent material upload
- draft add request with `account_appid` and `articles`

- [ ] **Step 2: Add the failing validation paths**

Implement serializer validation for:
- required `account_appid`
- required `media`
- supported permanent material `type`
- non-empty `articles`

- [ ] **Step 3: Add minimal service support for official payloads**

Implement a generic material upload result that preserves `media_id` and
optional `url`, plus a generic `draft/add` call that posts the caller-provided
`articles`.

- [ ] **Step 4: Add the new route handlers**

Implement:
- `wechat_media_uploadimg`
- `wechat_material_add_material`
- `wechat_draft_add`

- [ ] **Step 5: Delete the four old convenience endpoints and their routes**

Remove:
- `draft/newspic/`
- `draft/newspic-upload/`
- `draft/news/`
- `draft/news-upload/`

- [ ] **Step 6: Re-run the focused tests**

Run:

```bash
pytest tests/wechat/test_draft_api.py tests/wechat/test_draft_api_author_defaults.py -q
```

Expected: pass.

## Chunk 3: Documentation and schema

### Task 3: Update OpenAPI and frontend integration docs

**Files:**
- Modify: `0330/wechat_newspic_draft_frontend_api.md`
- Modify: `swagger.json`
- Modify: `schema.yml`

- [ ] **Step 1: Rewrite the frontend integration document**

Document the new frontend flow:
1. upload正文图片
2. upload封面或图片素材
3. create draft

Explicitly remove references to the deleted convenience endpoints.

- [ ] **Step 2: Refresh schema artifacts**

Regenerate checked-in schema artifacts so they only expose the three new
endpoints.

- [ ] **Step 3: Verify docs and schema references**

Run:

```bash
pytest tests/wechat/test_draft_api.py tests/wechat/test_draft_api_author_defaults.py -q
```

Then inspect the generated paths for:
- `/api/v1/wechat/media/uploadimg/`
- `/api/v1/wechat/material/add-material/`
- `/api/v1/wechat/draft/add/`

Expected: present, documented, and the old paths absent.
