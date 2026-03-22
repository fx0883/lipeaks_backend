# We RSS implementation plan

> **For agentic workers:** REQUIRED: Use
> superpowers:subagent-driven-development (if subagents available) or
> superpowers:executing-plans to implement this plan. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Build a new tenant-shared `we_rss` Django app for WeChat scraping
credentials, public account management, article storage, task tracking, and
authenticated RSS output without porting any `we-mp-rss-main` user-management
code.

**Architecture:** The app lives as a standard Django app under the current
project's `/api/v1/` routing and DRF auth stack. All APIs require current
project `Member` JWT authentication, all records are scoped to the caller's
tenant, and RSS output stays authenticated. The implementation follows a
pure-Django rewrite, with service modules encapsulating WeChat credential,
feed, article, and RSS logic.

**Tech Stack:** Django 5.2, Django REST Framework, drf-spectacular, MySQL,
project JWT auth, tenant-aware query filtering, Django test runner.

---

## Context and source of truth

This plan implements the approved design in:

- `docs/superpowers/specs/2026-03-20-we-rss-design.md`

The implementation must follow existing project conventions found in:

- `core/settings.py`
- `core/urls.py`
- `wechat/urls.py`
- `wechat/tests.py`
- `users/urls/member_urls.py`
- `cms/urls.py`

## File structure map

The implementation should create or modify the following files.

### App bootstrap and routing

- Create: `we_rss/__init__.py`
- Create: `we_rss/apps.py`
- Create: `we_rss/urls.py`
- Modify: `core/settings.py`
- Modify: `core/urls.py`

### Models and migrations

- Create: `we_rss/models.py`
- Create: `we_rss/migrations/__init__.py`
- Create: `we_rss/migrations/0001_initial.py`

### Serializers and app-level helpers

- Create: `we_rss/serializers.py`
- Create: `we_rss/permissions.py`
- Create: `we_rss/querysets.py`

### Services

- Create: `we_rss/services/__init__.py`
- Create: `we_rss/services/credential_service.py`
- Create: `we_rss/services/feed_service.py`
- Create: `we_rss/services/article_service.py`
- Create: `we_rss/services/rss_service.py`

### Views

- Create: `we_rss/views/__init__.py`
- Create: `we_rss/views/credential_views.py`
- Create: `we_rss/views/feed_views.py`
- Create: `we_rss/views/article_views.py`
- Create: `we_rss/views/rss_views.py`

### Tests

- Create: `we_rss/tests/__init__.py`
- Create: `we_rss/tests/test_models.py`
- Create: `we_rss/tests/test_permissions.py`
- Create: `we_rss/tests/test_credentials_api.py`
- Create: `we_rss/tests/test_feeds_api.py`
- Create: `we_rss/tests/test_articles_api.py`
- Create: `we_rss/tests/test_rss_api.py`

## Implementation constraints

The engineer implementing this plan must follow these rules.

- Use TDD for every new behavior. Write the failing test first and run it.
- Do not import or reuse `we-mp-rss-main` auth, user, JWT, or access-key code.
- Keep all `we_rss` data separate from `cms.Article`.
- Require authenticated `Member` access for all `we_rss` APIs, including RSS.
- Scope all read and write operations to `request.user.tenant`.
- Reject `Member` users with no tenant before performing app logic.
- Do not expose manual token or cookie creation for `WechatCredential`.
- Treat `WechatCredentialLoginSession` as the entry point for QR login flow.

## Chunk 1: App bootstrap, tenant rules, and models

### Task 1: Create app scaffolding and register the app

**Files:**

- Create: `we_rss/__init__.py`
- Create: `we_rss/apps.py`
- Create: `we_rss/urls.py`
- Modify: `core/settings.py`
- Modify: `core/urls.py`
- Test: `we_rss/tests/test_permissions.py`

- [ ] **Step 1: Write the failing test for URL registration and auth**

```python
from django.test import SimpleTestCase
from django.urls import resolve


class WeRssUrlRegistrationTest(SimpleTestCase):
    def test_we_rss_urls_are_registered(self):
        match = resolve("/api/v1/we-rss/credentials/")
        assert match.namespace == "we-rss"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test we_rss.tests.test_permissions.WeRssUrlRegistrationTest -v 2`

Expected: failure because the `we_rss` app or URL namespace does not exist.

- [ ] **Step 3: Create the minimal app bootstrap**

Implement:

- `we_rss/apps.py` with `WeRssConfig`
- empty package files
- `we_rss/urls.py` with an initial `app_name = "we-rss"`
- `core/settings.py` registration in `INSTALLED_APPS`
- `core/urls.py` mount at `/api/v1/we-rss/`

- [ ] **Step 4: Run the test to verify it passes**

Run: `python manage.py test we_rss.tests.test_permissions.WeRssUrlRegistrationTest -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/__init__.py we_rss/apps.py we_rss/urls.py core/settings.py core/urls.py we_rss/tests/test_permissions.py
git commit -m "feat: register we_rss app skeleton"
```

### Task 2: Add tenant-aware permission and queryset helpers

**Files:**

- Create: `we_rss/permissions.py`
- Create: `we_rss/querysets.py`
- Test: `we_rss/tests/test_permissions.py`

- [ ] **Step 1: Write the failing tests for member-only tenant access**

```python
from rest_framework.test import APITestCase
from django.urls import reverse


class WeRssPermissionTests(APITestCase):
    def test_rejects_unauthenticated_request(self):
        response = self.client.get("/api/v1/we-rss/credentials/")
        self.assertEqual(response.status_code, 401)

    def test_rejects_member_without_tenant(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.member_token}")
        response = self.client.get("/api/v1/we-rss/credentials/")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python manage.py test we_rss.tests.test_permissions.WeRssPermissionTests -v 2`

Expected: failure because permission classes and placeholder views do not exist.

- [ ] **Step 3: Write minimal permission and tenant helper code**

Implement:

- `IsTenantMemberForWeRss` permission class
- queryset helper that always filters by current tenant
- reusable helper that raises an error if `request.user` is not a `Member` or
  has no tenant

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python manage.py test we_rss.tests.test_permissions.WeRssPermissionTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/permissions.py we_rss/querysets.py we_rss/tests/test_permissions.py
git commit -m "feat: add tenant-aware we_rss permissions"
```

### Task 3: Add core models and initial migration

**Files:**

- Create: `we_rss/models.py`
- Create: `we_rss/migrations/__init__.py`
- Create: `we_rss/migrations/0001_initial.py`
- Test: `we_rss/tests/test_models.py`

- [ ] **Step 1: Write the failing model tests**

```python
from django.test import TestCase
from tenants.models import Tenant
from users.models import Member
from we_rss.models import (
    WechatCredential,
    WechatCredentialLoginSession,
    WechatFeed,
    WechatArticle,
    WechatSyncTask,
)


class WeRssModelTests(TestCase):
    def test_article_statistics_default_to_zero(self):
        article = WechatArticle()
        self.assertEqual(article.read_num, 0)
        self.assertEqual(article.comment_total_count, 0)

    def test_only_one_default_credential_per_tenant(self):
        self.assertTrue(False)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python manage.py test we_rss.tests.test_models.WeRssModelTests -v 2`

Expected: failure because models do not exist.

- [ ] **Step 3: Implement the models and migration**

Create models for:

- `WechatCredential`
- `WechatCredentialLoginSession`
- `WechatFeed`
- `WechatArticle`
- `WechatSyncTask`

Requirements:

- include tenant FK on all persisted business models
- include `created_by` and `updated_by` where needed
- include all approved `WechatArticle` statistics fields
- enforce one default credential per tenant in model logic or migration-safe
  validation
- keep feed and article tables fully separate from CMS

- [ ] **Step 4: Run model tests to verify they pass**

Run: `python manage.py test we_rss.tests.test_models.WeRssModelTests -v 2`

Expected: PASS

- [ ] **Step 5: Verify migration state**

Run: `python manage.py makemigrations --check`

Expected: no pending migrations beyond `we_rss/migrations/0001_initial.py`

- [ ] **Step 6: Commit**

```bash
git add we_rss/models.py we_rss/migrations/__init__.py we_rss/migrations/0001_initial.py we_rss/tests/test_models.py
git commit -m "feat: add we_rss core models"
```

## Chunk 2: Credential QR login and credential management APIs

### Task 4: Add serializers for credential resources and login sessions

**Files:**

- Create: `we_rss/serializers.py`
- Test: `we_rss/tests/test_credentials_api.py`

- [ ] **Step 1: Write the failing serializer and request-validation tests**

```python
from django.test import TestCase
from we_rss.serializers import CredentialUpdateSerializer


class CredentialSerializerTests(TestCase):
    def test_credential_update_disallows_manual_token_update(self):
        serializer = CredentialUpdateSerializer(data={"token": "manual-token"})
        self.assertFalse(serializer.is_valid())
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python manage.py test we_rss.tests.test_credentials_api.CredentialSerializerTests -v 2`

Expected: failure because serializers do not exist.

- [ ] **Step 3: Implement minimal serializers**

Create serializers for:

- credential list and detail
- credential metadata update
- login-session create
- login-session detail
- credential check response

Rules:

- do not accept manual token or cookie creation
- expose only safe fields in list responses
- expose login-session QR data and status fields

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python manage.py test we_rss.tests.test_credentials_api.CredentialSerializerTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/serializers.py we_rss/tests/test_credentials_api.py
git commit -m "feat: add we_rss credential serializers"
```

### Task 5: Add credential service layer

**Files:**

- Create: `we_rss/services/__init__.py`
- Create: `we_rss/services/credential_service.py`
- Test: `we_rss/tests/test_credentials_api.py`

- [ ] **Step 1: Write the failing service tests**

```python
from django.test import TestCase


class CredentialServiceTests(TestCase):
    def test_create_login_session_returns_qr_payload(self):
        self.assertTrue(False)

    def test_set_default_unsets_previous_default(self):
        self.assertTrue(False)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python manage.py test we_rss.tests.test_credentials_api.CredentialServiceTests -v 2`

Expected: failure because the service layer does not exist.

- [ ] **Step 3: Implement minimal credential service methods**

Implement service methods for:

- creating a login session
- loading a login session by tenant and `session_id`
- auto-persisting a credential after successful login
- checking credential validity
- setting and unsetting tenant default credentials

Keep the WeChat-driver integration behind small methods so it can be mocked
cleanly in tests.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python manage.py test we_rss.tests.test_credentials_api.CredentialServiceTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/__init__.py we_rss/services/credential_service.py we_rss/tests/test_credentials_api.py
git commit -m "feat: add credential service workflow"
```

### Task 6: Add credential and login-session API views

**Files:**

- Create: `we_rss/views/__init__.py`
- Create: `we_rss/views/credential_views.py`
- Modify: `we_rss/urls.py`
- Test: `we_rss/tests/test_credentials_api.py`

- [ ] **Step 1: Write the failing API tests**

```python
from rest_framework.test import APITestCase


class CredentialApiTests(APITestCase):
    def test_member_can_list_tenant_credentials(self):
        response = self.client.get("/api/v1/we-rss/credentials/")
        self.assertEqual(response.status_code, 200)

    def test_member_can_create_login_session(self):
        response = self.client.post("/api/v1/we-rss/credentials/login-sessions/", {}, format="json")
        self.assertEqual(response.status_code, 201)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python manage.py test we_rss.tests.test_credentials_api.CredentialApiTests -v 2`

Expected: failure because views and routes do not exist.

- [ ] **Step 3: Implement minimal API views and routes**

Add endpoints for:

- `GET /credentials/`
- `GET /credentials/{id}/`
- `PUT /credentials/{id}/`
- `DELETE /credentials/{id}/`
- `POST /credentials/{id}/check/`
- `POST /credentials/{id}/set-default/`
- `POST /credentials/login-sessions/`
- `GET /credentials/login-sessions/{session_id}/`

Requirements:

- require member JWT
- filter by current tenant
- use project-standard JSON responses
- annotate schema for each endpoint

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python manage.py test we_rss.tests.test_credentials_api.CredentialApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/views/__init__.py we_rss/views/credential_views.py we_rss/urls.py we_rss/tests/test_credentials_api.py
git commit -m "feat: add credential management APIs"
```

## Chunk 3: Feed, article, and task APIs

### Task 7: Add feed service and feed APIs

**Files:**

- Create: `we_rss/services/feed_service.py`
- Create: `we_rss/views/feed_views.py`
- Modify: `we_rss/serializers.py`
- Modify: `we_rss/urls.py`
- Test: `we_rss/tests/test_feeds_api.py`

- [ ] **Step 1: Write the failing feed tests**

```python
from rest_framework.test import APITestCase


class FeedApiTests(APITestCase):
    def test_member_can_list_tenant_feeds(self):
        response = self.client.get("/api/v1/we-rss/feeds/")
        self.assertEqual(response.status_code, 200)

    def test_feed_search_requires_active_credential(self):
        response = self.client.get("/api/v1/we-rss/feeds/search/?keyword=test")
        self.assertEqual(response.status_code, 400)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python manage.py test we_rss.tests.test_feeds_api.FeedApiTests -v 2`

Expected: failure because feed service and views do not exist.

- [ ] **Step 3: Implement feed serializers, service, views, and routes**

Add endpoints for:

- `GET /feeds/`
- `POST /feeds/`
- `GET /feeds/{id}/`
- `PUT /feeds/{id}/`
- `DELETE /feeds/{id}/`
- `GET /feeds/search/`
- `POST /feeds/{id}/sync/`

Rules:

- list and detail only show current tenant data
- search hits the WeChat-side service through active or explicit credential
- sync creates `WechatSyncTask` and updates feed sync fields

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python manage.py test we_rss.tests.test_feeds_api.FeedApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/feed_service.py we_rss/views/feed_views.py we_rss/serializers.py we_rss/urls.py we_rss/tests/test_feeds_api.py
git commit -m "feat: add we_rss feed APIs"
```

### Task 8: Add article service and article APIs

**Files:**

- Create: `we_rss/services/article_service.py`
- Create: `we_rss/views/article_views.py`
- Modify: `we_rss/serializers.py`
- Modify: `we_rss/urls.py`
- Test: `we_rss/tests/test_articles_api.py`

- [ ] **Step 1: Write the failing article tests**

```python
from rest_framework.test import APITestCase


class ArticleApiTests(APITestCase):
    def test_member_can_list_tenant_articles(self):
        response = self.client.get("/api/v1/we-rss/articles/")
        self.assertEqual(response.status_code, 200)

    def test_refresh_updates_statistics_snapshot(self):
        self.assertTrue(False)

    def test_import_by_url_creates_featured_article(self):
        self.assertTrue(False)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python manage.py test we_rss.tests.test_articles_api.ArticleApiTests -v 2`

Expected: failure because article service and views do not exist.

- [ ] **Step 3: Implement article serializers, service, views, and routes**

Add endpoints for:

- `GET /articles/`
- `GET /articles/{id}/`
- `DELETE /articles/{id}/`
- `POST /articles/import-by-url/`
- `POST /articles/{id}/refresh/`
- `GET /tasks/{task_id}/`
- `PUT /articles/{id}/read/`
- `PUT /articles/{id}/favorite/`

Rules:

- refresh updates content and all statistics fields in one transaction
- direct import by URL creates or reuses the synthetic featured feed
- task endpoint loads the task by current tenant and task id

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python manage.py test we_rss.tests.test_articles_api.ArticleApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/article_service.py we_rss/views/article_views.py we_rss/serializers.py we_rss/urls.py we_rss/tests/test_articles_api.py
git commit -m "feat: add we_rss article APIs"
```

## Chunk 4: RSS output, full verification, and documentation touch-ups

### Task 9: Add RSS service and authenticated RSS endpoints

**Files:**

- Create: `we_rss/services/rss_service.py`
- Create: `we_rss/views/rss_views.py`
- Modify: `we_rss/urls.py`
- Test: `we_rss/tests/test_rss_api.py`

- [ ] **Step 1: Write the failing RSS tests**

```python
from rest_framework.test import APITestCase


class RssApiTests(APITestCase):
    def test_rss_requires_member_token(self):
        response = self.client.get("/api/v1/we-rss/rss/")
        self.assertEqual(response.status_code, 401)

    def test_authenticated_member_can_get_tenant_rss(self):
        response = self.client.get("/api/v1/we-rss/rss/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python manage.py test we_rss.tests.test_rss_api.RssApiTests -v 2`

Expected: failure because RSS service and views do not exist.

- [ ] **Step 3: Implement RSS service, views, and routes**

Add endpoints for:

- `GET /rss/`
- `GET /rss/{feed_id}/`
- `GET /rss/content/{article_id}/`

Rules:

- require member JWT before output
- limit output to current tenant data
- return XML for feed responses and HTML for article content
- do not wrap XML or HTML in the standard JSON renderer

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python manage.py test we_rss.tests.test_rss_api.RssApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/rss_service.py we_rss/views/rss_views.py we_rss/urls.py we_rss/tests/test_rss_api.py
git commit -m "feat: add authenticated we_rss rss endpoints"
```

### Task 10: Run full app verification and schema checks

**Files:**

- Modify: any failing implementation files from previous tasks
- Test: `we_rss/tests/*.py`

- [ ] **Step 1: Run the `we_rss` test suite**

Run: `python manage.py test we_rss.tests -v 2`

Expected: all `we_rss` tests pass

- [ ] **Step 2: Run a broader regression slice**

Run: `python manage.py test wechat.tests -v 2`

Expected: existing WeChat login tests still pass

- [ ] **Step 3: Verify migrations**

Run: `python manage.py makemigrations --check`

Expected: no unexpected model drift

- [ ] **Step 4: Verify the schema endpoint still loads**

Run: `python manage.py spectacular --file schema.yml`

Expected: schema generation completes without new blocking errors

- [ ] **Step 5: Fix any regressions found**

Re-run only failing commands until all checks are clean.

- [ ] **Step 6: Commit**

```bash
git add we_rss core/settings.py core/urls.py schema.yml
git commit -m "feat: complete we_rss implementation"
```

## Open implementation notes

The engineer should make these choices deliberately during implementation.

- Prefer small service functions over large view methods.
- Keep QR-code driver integration behind mockable interfaces.
- If RSS responses conflict with the global JSON renderer, use explicit view
  classes or renderer overrides for RSS endpoints only.
- For task execution, start with synchronous persistence-backed tasks if needed
  to keep the first version simple, then expand later.
- If feed search and sync require external I/O, isolate parsing and persistence
  so tests can fake external responses.

## Suggested execution order

Follow the chunks in order.

1. App bootstrap and tenant-aware models
2. Credential workflow
3. Feed and article APIs
4. RSS output
5. Full verification

## Handoff

Plan complete and saved to
`docs/superpowers/plans/2026-03-20-we-rss-implementation.md`. Ready to
execute.
