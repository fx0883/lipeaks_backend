# We RSS SEO keywords Implementation Plan

> **For agentic workers:** REQUIRED: Use
> superpowers:subagent-driven-development (if subagents available) or
> superpowers:executing-plans to implement this plan. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Add member-scoped SEO keyword CRUD to `we_rss`, including
case-insensitive uniqueness per member, optional tag linking, explicit
`member_id` scope, filtering by keyword text and tag, and full schema plus
test coverage.

**Architecture:** The feature extends the existing `we_rss` app with one new
member-owned model and one explicit relation model. A dedicated
`seo_keyword_service.py` owns member-scope validation, keyword normalization,
relation synchronization, and list filtering, while a new viewset exposes
separate SEO keyword endpoints without changing the current tag, feed, or
article APIs.

**Tech Stack:** Django 5.2, Django REST Framework, drf-spectacular, MySQL,
project JWT auth, tenant-aware filtering, Django test runner.

---

This plan implements the approved design in
`docs/superpowers/specs/2026-04-05-we-rss-seo-keywords-design.md`. It assumes
you work inside the current `we_rss` app and preserve the existing API
contracts for feeds, articles, and tags.

Use these helper skills while executing the plan:

- `@test-driven-development`
- `@verification-before-completion`

## File structure map

This section fixes the file boundaries before implementation starts.

### Models and migrations

- Modify: `we_rss/models.py`
- Create: `we_rss/migrations/0008_memberseokeyword_and_relations.py`

### Serializers and schema

- Modify: `we_rss/serializers.py`
- Modify: `we_rss/schema.py`

### Services

- Create: `we_rss/services/seo_keyword_service.py`

### Views and routing

- Create: `we_rss/views/seo_keyword_views.py`
- Modify: `we_rss/urls.py`

### Tests

- Modify: `we_rss/tests/test_models.py`
- Create: `we_rss/tests/test_seo_keywords_service.py`
- Create: `we_rss/tests/test_seo_keywords_api.py`
- Modify: `we_rss/tests/test_schema.py`

## Implementation constraints

These rules keep the implementation aligned with the approved design.

- Keep SEO keywords private to the requested `member_id` scope.
- Require `member_id` on every SEO keyword endpoint.
- Do not treat `member_id` as permission to access another member's data.
- Enforce keyword uniqueness per member, ignoring case.
- Trim surrounding whitespace from `keyword` before validation and save.
- Store `search_index` directly on the keyword row as a current-value field.
- Allow `tag_ids` to be empty so keywords can exist without tags.
- Require every linked tag to belong to the same tenant and member.
- Replace tag relations on update instead of introducing separate attach or
  detach APIs.
- Return linked tag summaries inline in list and detail responses.
- Do not modify existing tag, feed, article, or RSS endpoint behavior.
- Do not revert or overwrite unrelated local changes already present in the
  working tree.

## Chunk 1: Data model and database constraints

This chunk adds the new models, migration, and low-level cleanup behavior that
the rest of the feature depends on.

### Task 1: Add SEO keyword models and migration

**Files:**

- Modify: `we_rss/models.py`
- Create: `we_rss/migrations/0008_memberseokeyword_and_relations.py`
- Test: `we_rss/tests/test_models.py`

- [ ] **Step 1: Write the failing model tests**

```python
from django.db import IntegrityError

from we_rss.models import MemberSeoKeyword, MemberTagSeoKeywordRelation


class WeRssSeoKeywordModelTests(TestCase):
    def test_member_seo_keyword_is_case_insensitive_unique_per_member(self):
        MemberSeoKeyword.objects.create(
            tenant=self.tenant,
            member=self.member,
            keyword="Weight Loss",
            search_index=100,
        )

        with self.assertRaises(IntegrityError):
            MemberSeoKeyword.objects.create(
                tenant=self.tenant,
                member=self.member,
                keyword="weight loss",
                search_index=200,
            )

    def test_other_member_can_reuse_same_keyword(self):
        MemberSeoKeyword.objects.create(
            tenant=self.tenant,
            member=self.member,
            keyword="Weight Loss",
            search_index=100,
        )

        keyword = MemberSeoKeyword.objects.create(
            tenant=self.tenant,
            member=self.other_member,
            keyword="weight loss",
            search_index=300,
        )

        self.assertEqual(keyword.member_id, self.other_member.id)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_models.WeRssSeoKeywordModelTests -v 2`

Expected: FAIL because the SEO keyword models and migration do not exist yet.

- [ ] **Step 3: Implement the minimal models and migration**

Add the following models in `we_rss/models.py`:

- `MemberSeoKeyword`
- `MemberTagSeoKeywordRelation`

Implement these rules:

- `MemberSeoKeyword` inherits `BaseModel`.
- `MemberSeoKeyword` has `member`, `keyword`, and `search_index`.
- `MemberSeoKeyword` orders by `-updated_at`, `-id`.
- `search_index` uses `PositiveIntegerField(default=0)`.
- `MemberTagSeoKeywordRelation` is a plain model with `tenant`, `member`,
  `tag`, `seo_keyword`, and `created_at`.
- The migration adds a case-insensitive uniqueness constraint for
  `(member, lower(keyword))`.
- The migration adds a unique constraint for `(member, tag, seo_keyword)`.
- The migration adds indexes for `tenant/member`, `tenant/tag`, and
  `tenant/seo_keyword`.

- [ ] **Step 4: Run the model tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_models.WeRssSeoKeywordModelTests -v 2`

Expected: PASS

- [ ] **Step 5: Verify migration state**

Run: `python manage.py makemigrations --check`

Expected: PASS with no extra migration drift beyond
`we_rss/migrations/0008_memberseokeyword_and_relations.py`.

- [ ] **Step 6: Commit**

```bash
git add we_rss/models.py \
  we_rss/migrations/0008_memberseokeyword_and_relations.py \
  we_rss/tests/test_models.py
git commit -m "feat: add we_rss seo keyword models"
```

### Task 2: Add relation cleanup coverage

**Files:**

- Modify: `we_rss/tests/test_models.py`
- Test: `we_rss/tests/test_models.py`

- [ ] **Step 1: Write the failing cleanup tests**

```python
class WeRssSeoKeywordRelationCleanupTests(TestCase):
    def test_deleting_keyword_cascades_keyword_tag_relations(self):
        relation = MemberTagSeoKeywordRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag,
            seo_keyword=self.keyword,
        )

        self.keyword.delete()

        self.assertFalse(
            MemberTagSeoKeywordRelation.objects.filter(id=relation.id).exists()
        )

    def test_deleting_tag_cascades_keyword_tag_relations_only(self):
        MemberTagSeoKeywordRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=self.tag,
            seo_keyword=self.keyword,
        )

        self.tag.delete()

        self.assertTrue(
            MemberSeoKeyword.objects.filter(id=self.keyword.id).exists()
        )
        self.assertFalse(
            MemberTagSeoKeywordRelation.objects.filter(
                seo_keyword_id=self.keyword.id
            ).exists()
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_models.WeRssSeoKeywordRelationCleanupTests -v 2`

Expected: FAIL until the new relation coverage exists.

- [ ] **Step 3: Add the missing test fixtures and model assertions**

Update `we_rss/tests/test_models.py` so the SEO keyword cleanup test class
creates:

- `self.tenant`
- `self.member`
- `self.other_member`
- `self.feed`
- `self.article`
- `self.tag`
- `self.keyword`

Use the final model definitions from Task 1. Do not add custom delete hooks
unless the FK cascade behavior is actually missing.

- [ ] **Step 4: Run the focused model tests**

Run:
`python manage.py test we_rss.tests.test_models.WeRssSeoKeywordModelTests we_rss.tests.test_models.WeRssSeoKeywordRelationCleanupTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/tests/test_models.py
git commit -m "test: cover seo keyword relation cleanup"
```

## Chunk 2: Serializers and service behavior

This chunk adds request validation, nested response serialization, and the
service layer that owns keyword CRUD plus relation synchronization.

### Task 3: Add serializer coverage for explicit member scope and write inputs

**Files:**

- Modify: `we_rss/serializers.py`
- Create: `we_rss/tests/test_seo_keywords_service.py`
- Test: `we_rss/tests/test_seo_keywords_service.py`

- [ ] **Step 1: Write the failing serializer validation tests**

```python
from we_rss.serializers import SeoKeywordWriteSerializer


class SeoKeywordWriteSerializerTests(TestCase):
    def test_keyword_is_trimmed(self):
        serializer = SeoKeywordWriteSerializer(
            data={"member_id": 1, "keyword": "  Weight Loss  ", "search_index": 12}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["keyword"], "Weight Loss")

    def test_member_id_is_required(self):
        serializer = SeoKeywordWriteSerializer(
            data={"keyword": "Weight Loss", "search_index": 12}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("member_id", serializer.errors)

    def test_negative_search_index_is_rejected(self):
        serializer = SeoKeywordWriteSerializer(
            data={"member_id": 1, "keyword": "Weight Loss", "search_index": -1}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("search_index", serializer.errors)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_seo_keywords_service.SeoKeywordWriteSerializerTests -v 2`

Expected: FAIL because the serializer does not exist yet.

- [ ] **Step 3: Add the minimal serializers**

Implement these serializers in `we_rss/serializers.py`:

- `MemberTagSummarySerializer`
- `SeoKeywordSerializer`
- `SeoKeywordWriteSerializer`
- `SeoKeywordDeleteSerializer`

Implement these rules:

- `SeoKeywordWriteSerializer` requires `member_id`, `keyword`, and
  `search_index`.
- `tag_ids` is optional and defaults to an empty list.
- `keyword` is stripped and cannot be blank.
- `search_index` uses `min_value=0`.
- `SeoKeywordSerializer` exposes `id`, `member_id`, `keyword`, `search_index`,
  `tag_ids`, `tags`, `created_at`, and `updated_at`.

- [ ] **Step 4: Run the serializer tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_seo_keywords_service.SeoKeywordWriteSerializerTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/serializers.py we_rss/tests/test_seo_keywords_service.py
git commit -m "feat: add seo keyword serializers"
```

### Task 4: Add service-level CRUD, scope validation, and relation sync

**Files:**

- Create: `we_rss/services/seo_keyword_service.py`
- Modify: `we_rss/tests/test_seo_keywords_service.py`
- Test: `we_rss/tests/test_seo_keywords_service.py`

- [ ] **Step 1: Write the failing service tests**

```python
from rest_framework.exceptions import PermissionDenied, ValidationError

from we_rss.services.seo_keyword_service import SeoKeywordService


class SeoKeywordServiceTests(TestCase):
    def test_create_keyword_with_multiple_tags(self):
        keyword = SeoKeywordService.create_keyword(
            tenant=self.tenant,
            actor=self.member,
            member_id=self.member.id,
            keyword="Weight Loss",
            search_index=120,
            tag_ids=[self.tag_one.id, self.tag_two.id],
        )

        self.assertEqual(keyword.keyword, "Weight Loss")
        self.assertEqual(keyword.keyword_tag_relations.count(), 2)

    def test_update_replaces_existing_tag_relations(self):
        SeoKeywordService.update_keyword(
            tenant=self.tenant,
            actor=self.member,
            member_id=self.member.id,
            keyword_id=self.keyword.id,
            keyword="Weight Loss Updated",
            search_index=180,
            tag_ids=[self.tag_two.id],
        )

        self.assertEqual(
            list(
                self.keyword.keyword_tag_relations.order_by("tag_id").values_list(
                    "tag_id", flat=True
                )
            ),
            [self.tag_two.id],
        )

    def test_rejects_operating_on_another_member_scope(self):
        with self.assertRaises(PermissionDenied):
            SeoKeywordService.list_keywords(
                tenant=self.tenant,
                actor=self.member,
                member_id=self.other_member.id,
            )

    def test_rejects_tag_from_another_member(self):
        with self.assertRaises(ValidationError):
            SeoKeywordService.create_keyword(
                tenant=self.tenant,
                actor=self.member,
                member_id=self.member.id,
                keyword="Weight Loss",
                search_index=120,
                tag_ids=[self.other_member_tag.id],
            )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_seo_keywords_service.SeoKeywordServiceTests -v 2`

Expected: FAIL because the service does not exist yet.

- [ ] **Step 3: Implement the minimal service**

Create `we_rss/services/seo_keyword_service.py` with a `SeoKeywordService`
class that owns:

- resolving and validating the requested `member_id`
- checking that `actor.id == member_id` for normal member calls
- normalizing `keyword`
- enforcing case-insensitive uniqueness through `IntegrityError` translation
- validating `tag_ids` against `MemberTag`
- de-duplicating `tag_ids`
- creating, updating, retrieving, listing, and deleting keywords
- replacing keyword-tag relation rows during update
- filtering by `search` and `tag_id`
- applying `prefetch_related` for linked tags

Suggested method surface:

```python
class SeoKeywordService:
    @staticmethod
    def list_keywords(*, tenant, actor, member_id, search=None, tag_id=None): ...

    @staticmethod
    def get_keyword(*, tenant, actor, member_id, keyword_id): ...

    @staticmethod
    def create_keyword(*, tenant, actor, member_id, keyword, search_index, tag_ids): ...

    @staticmethod
    def update_keyword(*, tenant, actor, member_id, keyword_id, keyword, search_index, tag_ids): ...

    @staticmethod
    def delete_keyword(*, tenant, actor, member_id, keyword_id): ...
```

- [ ] **Step 4: Run the service tests**

Run:
`python manage.py test we_rss.tests.test_seo_keywords_service.SeoKeywordServiceTests -v 2`

Expected: PASS

- [ ] **Step 5: Run the whole service test file**

Run:
`python manage.py test we_rss.tests.test_seo_keywords_service -v 2`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add we_rss/services/seo_keyword_service.py \
  we_rss/tests/test_seo_keywords_service.py
git commit -m "feat: add seo keyword service"
```

## Chunk 3: HTTP API, routing, and schema

This chunk exposes the new service through REST endpoints and documents the new
contract in drf-spectacular.

### Task 5: Add SEO keyword viewset and routes

**Files:**

- Create: `we_rss/views/seo_keyword_views.py`
- Modify: `we_rss/urls.py`
- Create: `we_rss/tests/test_seo_keywords_api.py`
- Test: `we_rss/tests/test_seo_keywords_api.py`

- [ ] **Step 1: Write the failing API tests for CRUD and filtering**

```python
class SeoKeywordApiTests(APITestCase):
    def test_member_can_create_list_update_and_delete_keywords(self):
        create_response = self.client.post(
            "/api/v1/we-rss/seo-keywords/",
            {
                "member_id": self.member.id,
                "keyword": "Weight Loss",
                "search_index": 200,
                "tag_ids": [self.tag_one.id, self.tag_two.id],
            },
            format="json",
        )

        keyword_id = create_response.data["data"]["id"]

        list_response = self.client.get(
            f"/api/v1/we-rss/seo-keywords/?member_id={self.member.id}"
        )
        detail_response = self.client.get(
            f"/api/v1/we-rss/seo-keywords/{keyword_id}/?member_id={self.member.id}"
        )
        update_response = self.client.put(
            f"/api/v1/we-rss/seo-keywords/{keyword_id}/",
            {
                "member_id": self.member.id,
                "keyword": "Weight Loss Updated",
                "search_index": 300,
                "tag_ids": [self.tag_two.id],
            },
            format="json",
        )
        delete_response = self.client.delete(
            f"/api/v1/we-rss/seo-keywords/{keyword_id}/",
            {"member_id": self.member.id},
            format="json",
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(delete_response.status_code, 204)

    def test_list_filters_by_search_and_tag(self):
        search_response = self.client.get(
            f"/api/v1/we-rss/seo-keywords/?member_id={self.member.id}&search=loss"
        )
        tag_response = self.client.get(
            f"/api/v1/we-rss/seo-keywords/?member_id={self.member.id}&tag_id={self.tag_one.id}"
        )

        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(tag_response.status_code, 200)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_seo_keywords_api -v 2`

Expected: FAIL because the viewset and routes do not exist yet.

- [ ] **Step 3: Implement the viewset and routes**

Create `we_rss/views/seo_keyword_views.py` with a
`MemberSeoKeywordViewSet(WeRssTenantGenericViewSet)` that provides:

- `list`
- `create`
- `retrieve`
- `update`
- `destroy`

Implement these rules:

- `list` reads `member_id`, `search`, and `tag_id` from query params
- `retrieve` requires `member_id` in query params
- `create`, `update`, and `destroy` read `member_id` from request body
- all actions delegate to `SeoKeywordService`
- responses reuse the existing `we_rss` response envelope style

Add these routes in `we_rss/urls.py`:

- `path("seo-keywords/", ...)`
- `path("seo-keywords/<int:pk>/", ...)`

- [ ] **Step 4: Run the API tests**

Run:
`python manage.py test we_rss.tests.test_seo_keywords_api -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/views/seo_keyword_views.py we_rss/urls.py \
  we_rss/tests/test_seo_keywords_api.py
git commit -m "feat: add seo keyword api endpoints"
```

### Task 6: Add OpenAPI schema coverage for the new endpoints

**Files:**

- Modify: `we_rss/schema.py`
- Modify: `we_rss/tests/test_schema.py`
- Test: `we_rss/tests/test_schema.py`

- [ ] **Step 1: Write the failing schema tests**

```python
class WeRssSeoKeywordSchemaTests(SimpleTestCase):
    def test_seo_keyword_operations_are_documented(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        list_operation = schema["paths"]["/api/v1/we-rss/seo-keywords/"]["get"]
        detail_operation = schema["paths"]["/api/v1/we-rss/seo-keywords/{id}/"]["get"]

        self.assertEqual(list_operation["operationId"], "we_rss_seo_keywords_list")
        self.assertEqual(detail_operation["operationId"], "we_rss_seo_keywords_retrieve")

    def test_seo_keyword_request_and_response_examples_exist(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        create_operation = schema["paths"]["/api/v1/we-rss/seo-keywords/"]["post"]

        self.assertIn("examples", create_operation["requestBody"]["content"]["application/json"])
        self.assertIn("examples", create_operation["responses"]["201"]["content"]["application/json"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_schema.WeRssSeoKeywordSchemaTests -v 2`

Expected: FAIL because the schema constants and endpoint docs do not exist yet.

- [ ] **Step 3: Add schema constants and endpoint documentation**

Update `we_rss/schema.py` to add:

- query parameter docs for `member_id`, `search`, and `tag_id`
- request and response examples for SEO keyword create, update, list, and detail
- response examples that use the standard JSON envelope
- path parameter docs for the new detail route

Decorate the new viewset actions with `extend_schema` in
`we_rss/views/seo_keyword_views.py` using the new schema helpers and examples.

- [ ] **Step 4: Run the focused schema tests**

Run:
`python manage.py test we_rss.tests.test_schema.WeRssSeoKeywordSchemaTests -v 2`

Expected: PASS

- [ ] **Step 5: Run the full schema suite**

Run:
`python manage.py test we_rss.tests.test_schema -v 2`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add we_rss/schema.py we_rss/views/seo_keyword_views.py \
  we_rss/tests/test_schema.py
git commit -m "docs: document seo keyword endpoints"
```

## Chunk 4: Integration verification and regression safety

This chunk closes the feature by covering cross-component behavior and running
the focused `we_rss` regression set.

### Task 7: Add remaining API edge cases and regression coverage

**Files:**

- Modify: `we_rss/tests/test_seo_keywords_api.py`
- Test: `we_rss/tests/test_seo_keywords_api.py`

- [ ] **Step 1: Write the failing edge-case API tests**

```python
class SeoKeywordApiEdgeCaseTests(APITestCase):
    def test_create_rejects_duplicate_keyword_ignoring_case(self):
        self.client.post(
            "/api/v1/we-rss/seo-keywords/",
            {
                "member_id": self.member.id,
                "keyword": "Weight Loss",
                "search_index": 10,
            },
            format="json",
        )

        response = self.client.post(
            "/api/v1/we-rss/seo-keywords/",
            {
                "member_id": self.member.id,
                "keyword": "weight loss",
                "search_index": 20,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_request_rejects_other_member_scope(self):
        response = self.client.get(
            f"/api/v1/we-rss/seo-keywords/?member_id={self.other_member.id}"
        )

        self.assertEqual(response.status_code, 403)

    def test_keyword_can_exist_without_tags(self):
        response = self.client.post(
            "/api/v1/we-rss/seo-keywords/",
            {
                "member_id": self.member.id,
                "keyword": "Low Carb",
                "search_index": 55,
                "tag_ids": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["tag_ids"], [])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_seo_keywords_api.SeoKeywordApiEdgeCaseTests -v 2`

Expected: FAIL until the edge-case behavior is fully implemented.

- [ ] **Step 3: Implement the missing API and service fixes**

Adjust only the minimum code needed in:

- `we_rss/services/seo_keyword_service.py`
- `we_rss/views/seo_keyword_views.py`
- `we_rss/serializers.py`

Fix any gaps found by the edge-case tests, especially:

- duplicate keyword translation to `400`
- `403` on another member's scope
- stable empty-tag behavior in response serialization

- [ ] **Step 4: Run the full SEO keyword API suite**

Run:
`python manage.py test we_rss.tests.test_seo_keywords_api -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/seo_keyword_service.py \
  we_rss/views/seo_keyword_views.py \
  we_rss/serializers.py \
  we_rss/tests/test_seo_keywords_api.py
git commit -m "test: cover seo keyword api edge cases"
```

### Task 8: Run focused regression and final verification

**Files:**

- Modify: no source changes expected
- Test: `we_rss/tests/test_models.py`
- Test: `we_rss/tests/test_seo_keywords_service.py`
- Test: `we_rss/tests/test_seo_keywords_api.py`
- Test: `we_rss/tests/test_schema.py`

- [ ] **Step 1: Run the focused SEO keyword verification suite**

Run:

```bash
python manage.py test \
  we_rss.tests.test_models.WeRssSeoKeywordModelTests \
  we_rss.tests.test_models.WeRssSeoKeywordRelationCleanupTests \
  we_rss.tests.test_seo_keywords_service \
  we_rss.tests.test_seo_keywords_api \
  we_rss.tests.test_schema.WeRssSeoKeywordSchemaTests -v 2
```

Expected: PASS

- [ ] **Step 2: Run adjacent tag regressions**

Run:

```bash
python manage.py test \
  we_rss.tests.test_tags_api \
  we_rss.tests.test_models.WeRssTagModelTests \
  we_rss.tests.test_models.WeRssTagCleanupTests -v 2
```

Expected: PASS

- [ ] **Step 3: Run schema regression**

Run: `python manage.py test we_rss.tests.test_schema -v 2`

Expected: PASS

- [ ] **Step 4: Inspect migration drift one last time**

Run: `python manage.py makemigrations --check`

Expected: PASS

- [ ] **Step 5: Commit the final verified state**

```bash
git add -A
git commit -m "feat: add member scoped seo keywords"
```

## Notes for the implementing agent

These reminders reduce avoidable rework during execution.

- Reuse the existing `MemberTag` model instead of adding a second tag type.
- Keep `member_id` handling explicit in serializers and views instead of
  implicitly reading `request.user.id`.
- Translate `IntegrityError` into a serializer-style `ValidationError`
  message that mirrors the current tag API.
- Prefer `prefetch_related` and ordered relation loading so list responses stay
  deterministic.
- Keep schema examples in ASCII to avoid terminal encoding noise during review.

Plan complete and saved to
`docs/superpowers/plans/2026-04-05-we-rss-seo-keywords-implementation.md`.
Ready to execute?
