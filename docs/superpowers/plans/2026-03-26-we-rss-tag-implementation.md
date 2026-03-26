# We RSS tag system Implementation Plan

> **For agentic workers:** REQUIRED: Use
> superpowers:subagent-driven-development (if subagents available) or
> superpowers:executing-plans to implement this plan. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Add a member-private tag system to `we_rss` with tag CRUD, feed and
article tag attachment, cleanup rules, and `AND`-style filtering on feed and
article list APIs.

**Architecture:** The feature extends the existing `we_rss` app instead of
changing its core response shape. One new tag model stores member-owned tag
definitions, and two relation models store feed and article tag attachments.
Dedicated tag APIs manage the private tag library, while existing feed and
article APIs gain tag-based filtering and per-object tag endpoints.

**Tech Stack:** Django 5.2, Django REST Framework, drf-spectacular, MySQL,
project JWT auth, tenant-aware filtering, Django test runner.

---

This plan implements the approved design in
`docs/superpowers/specs/2026-03-26-we-rss-tag-design.md`. It assumes you work
inside the current `we_rss` app and preserve the existing API contracts for
`feeds/` and `articles/`.

Use these helper skills while executing the plan:

- `@test-driven-development`
- `@verification-before-completion`

## File structure map

This section fixes the file boundaries before implementation starts.

### Models and migrations

- Modify: `we_rss/models.py`
- Create: `we_rss/migrations/0005_member_tags.py`

### Serializers and schema

- Modify: `we_rss/serializers.py`
- Modify: `we_rss/schema.py`

### Services

- Create: `we_rss/services/tag_service.py`
- Modify: `we_rss/services/feed_service.py`
- Modify: `we_rss/services/article_service.py`

### Views and routing

- Create: `we_rss/views/tag_views.py`
- Modify: `we_rss/views/feed_views.py`
- Modify: `we_rss/views/article_views.py`
- Modify: `we_rss/urls.py`

### Tests

- Modify: `we_rss/tests/test_models.py`
- Create: `we_rss/tests/test_tags_api.py`
- Modify: `we_rss/tests/test_feeds_api.py`
- Modify: `we_rss/tests/test_articles_api.py`

## Implementation constraints

These rules keep the implementation aligned with the approved design.

- Keep tags private to the current `Member`.
- Do not expose tags inline on existing `WechatFeedSerializer` or
  `WechatArticleSerializer`.
- Enforce case-insensitive tag name uniqueness per member.
- Require tags to exist before attach. Never auto-create tags from names.
- Allow bulk attach and bulk detach by `tag_ids`.
- Require feed subscription for feed tagging.
- Allow article tagging for any article in the current tenant.
- Delete feed-tag relations on unsubscribe.
- Delete all tag relations when the tag, feed, or article is deleted.
- Add tag filters to existing feed and article list endpoints with `AND`
  semantics.
- Do not revert or overwrite unrelated local changes already present in the
  working tree.

## Chunk 1: Data model and cleanup behavior

This chunk adds the new models, migration, and the low-level cleanup behavior
that the rest of the feature depends on.

### Task 1: Add tag models and migration

**Files:**

- Modify: `we_rss/models.py`
- Create: `we_rss/migrations/0005_member_tags.py`
- Test: `we_rss/tests/test_models.py`

- [ ] **Step 1: Write the failing model tests**

```python
from django.db import IntegrityError
from django.test import TestCase

from we_rss.models import (
    MemberArticleTagRelation,
    MemberFeedTagRelation,
    MemberTag,
)


class WeRssTagModelTests(TestCase):
    def test_member_tag_name_is_case_insensitive_unique_per_member(self):
        MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="AI",
        )

        with self.assertRaises(IntegrityError):
            MemberTag.objects.create(
                tenant=self.tenant,
                member=self.member,
                name="ai",
            )

    def test_other_member_can_reuse_same_tag_name(self):
        other_member = Member.objects.create(
            username="other_member",
            email="other@example.com",
            tenant=self.tenant,
        )
        MemberTag.objects.create(tenant=self.tenant, member=self.member, name="AI")
        tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=other_member,
            name="AI",
        )

        self.assertEqual(tag.name, "AI")

    def test_deleting_tag_cascades_feed_and_article_relations(self):
        tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="AI",
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            feed=self.feed,
        )
        MemberArticleTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            article=self.article,
        )

        tag.delete()

        self.assertFalse(
            MemberFeedTagRelation.objects.filter(member=self.member).exists()
        )
        self.assertFalse(
            MemberArticleTagRelation.objects.filter(member=self.member).exists()
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_models.WeRssTagModelTests -v 2`

Expected: FAIL because the tag models and migration do not exist yet.

- [ ] **Step 3: Implement the minimal models and migration**

Add the following models in `we_rss/models.py`:

- `MemberTag`
- `MemberFeedTagRelation`
- `MemberArticleTagRelation`

Implement these rules:

- `MemberTag` inherits `BaseModel`.
- `MemberTag` has `member`, `name`, `color`, `description`, `sort_order`, and
  `is_pinned`.
- `MemberTag` orders by `-is_pinned`, `sort_order`, `-id`.
- `MemberFeedTagRelation` and `MemberArticleTagRelation` are plain models with
  `tenant`, `member`, target FK, and `created_at`.
- Relation FKs use `on_delete=models.CASCADE`.
- The migration adds a case-insensitive uniqueness constraint for
  `(member, lower(name))`.
- The migration adds unique constraints for `(member, tag, feed)` and
  `(member, tag, article)`.

- [ ] **Step 4: Run the model tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_models.WeRssTagModelTests -v 2`

Expected: PASS

- [ ] **Step 5: Verify migration state**

Run: `python manage.py makemigrations --check`

Expected: PASS with no extra migration drift beyond
`we_rss/migrations/0005_member_tags.py`.

- [ ] **Step 6: Commit**

```bash
git add we_rss/models.py we_rss/migrations/0005_member_tags.py we_rss/tests/test_models.py
git commit -m "feat: add we_rss member tag models"
```

### Task 2: Add unsubscribe and delete cleanup coverage

**Files:**

- Modify: `we_rss/tests/test_models.py`
- Modify: `we_rss/services/feed_service.py`
- Test: `we_rss/tests/test_models.py`

- [ ] **Step 1: Write the failing cleanup tests**

```python
class WeRssTagCleanupTests(TestCase):
    def test_unsubscribe_removes_member_feed_tag_relations(self):
        tag = MemberTag.objects.create(
            tenant=self.tenant,
            member=self.member,
            name="Digest",
        )
        MemberFeedSubscription.objects.create(
            tenant=self.tenant,
            member=self.member,
            feed=self.feed,
        )
        MemberFeedTagRelation.objects.create(
            tenant=self.tenant,
            member=self.member,
            tag=tag,
            feed=self.feed,
        )

        FeedService.unsubscribe_member(feed=self.feed, member=self.member)

        self.assertFalse(
            MemberFeedTagRelation.objects.filter(
                member=self.member,
                feed=self.feed,
            ).exists()
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_models.WeRssTagCleanupTests -v 2`

Expected: FAIL because unsubscribe does not clear tag relations yet.

- [ ] **Step 3: Implement the cleanup logic**

Update `FeedService.unsubscribe_member` so it deletes
`MemberFeedTagRelation` rows for the current member and feed before returning.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_models.WeRssTagCleanupTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/feed_service.py we_rss/tests/test_models.py
git commit -m "feat: clean feed tags on unsubscribe"
```

## Chunk 2: Tag CRUD, serializers, and dedicated tag APIs

This chunk builds the member-private tag library before any feed or article
attachment logic is added.

### Task 3: Add tag serializers and tag service

**Files:**

- Modify: `we_rss/serializers.py`
- Create: `we_rss/services/tag_service.py`
- Test: `we_rss/tests/test_tags_api.py`

- [ ] **Step 1: Write the failing serializer and service tests**

```python
from django.test import TestCase

from we_rss.serializers import MemberTagWriteSerializer


class MemberTagSerializerTests(TestCase):
    def test_tag_name_is_trimmed(self):
        serializer = MemberTagWriteSerializer(
            data={"name": "  AI  "}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name"], "AI")

    def test_blank_tag_name_is_rejected(self):
        serializer = MemberTagWriteSerializer(data={"name": "   "})
        self.assertFalse(serializer.is_valid())
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_tags_api.MemberTagSerializerTests -v 2`

Expected: FAIL because the serializers and service do not exist yet.

- [ ] **Step 3: Implement minimal serializers and service methods**

Add these serializers in `we_rss/serializers.py`:

- `MemberTagSerializer`
- `MemberTagWriteSerializer`
- `TagRelationWriteSerializer`

Add these service methods in `we_rss/services/tag_service.py`:

- `list_member_tags`
- `create_member_tag`
- `update_member_tag`
- `delete_member_tag`
- `get_member_tags_for_ids`

Implement these rules:

- Trim `name`.
- Reject blank `name`.
- Surface case-insensitive duplicate-name errors cleanly.
- Return tag counts through queryset annotations or dedicated service helpers.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_tags_api.MemberTagSerializerTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/serializers.py we_rss/services/tag_service.py we_rss/tests/test_tags_api.py
git commit -m "feat: add member tag serializers and service"
```

### Task 4: Add tag management API endpoints

**Files:**

- Create: `we_rss/views/tag_views.py`
- Modify: `we_rss/urls.py`
- Modify: `we_rss/schema.py`
- Test: `we_rss/tests/test_tags_api.py`

- [ ] **Step 1: Write the failing tag CRUD API tests**

```python
from rest_framework.test import APITestCase


class MemberTagApiTests(APITestCase):
    def test_member_can_create_and_list_private_tags(self):
        create_response = self.client.post(
            "/api/v1/we-rss/tags/",
            {"name": "AI", "color": "#008000"},
            format="json",
        )
        list_response = self.client.get("/api/v1/we-rss/tags/")

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["data"][0]["name"], "AI")

    def test_member_cannot_read_other_members_tags(self):
        response = self.client.get("/api/v1/we-rss/tags/")
        returned_ids = [item["id"] for item in response.data["data"]]
        self.assertNotIn(self.other_member_tag.id, returned_ids)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_tags_api.MemberTagApiTests -v 2`

Expected: FAIL because the tag routes and viewset do not exist.

- [ ] **Step 3: Implement the tag CRUD endpoints**

Create `we_rss/views/tag_views.py` with a `MemberTagViewSet` that uses
`WeRssTenantModelViewSet` or `WeRssTenantGenericViewSet` patterns already used
in the app.

Add endpoints:

- `GET /tags/`
- `POST /tags/`
- `GET /tags/{id}/`
- `PUT /tags/{id}/`
- `DELETE /tags/{id}/`

Add schema helpers in `we_rss/schema.py` for:

- tag list and detail examples
- tag write request example
- tag path parameter

Make sure `GET /tags/` returns `feed_count` and `article_count`.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_tags_api.MemberTagApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/views/tag_views.py we_rss/urls.py we_rss/schema.py we_rss/tests/test_tags_api.py
git commit -m "feat: add we_rss tag management APIs"
```

## Chunk 3: Feed and article tagging workflows

This chunk adds tag attachment and detachment to feeds and articles through
separate APIs, while keeping the original feed and article serializers stable.

### Task 5: Add feed tag APIs and service logic

**Files:**

- Modify: `we_rss/services/tag_service.py`
- Modify: `we_rss/views/feed_views.py`
- Modify: `we_rss/urls.py`
- Modify: `we_rss/schema.py`
- Test: `we_rss/tests/test_feeds_api.py`
- Test: `we_rss/tests/test_tags_api.py`

- [ ] **Step 1: Write the failing feed-tag tests**

```python
class FeedTagApiTests(APITestCase):
    def test_member_can_attach_multiple_tags_to_subscribed_feed(self):
        response = self.client.post(
            f"/api/v1/we-rss/feeds/{self.feed.id}/tags/attach/",
            {"tag_ids": [self.tag_one.id, self.tag_two.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 2)

    def test_member_cannot_attach_tag_to_unsubscribed_feed(self):
        response = self.client.post(
            f"/api/v1/we-rss/feeds/{self.feed.id}/tags/attach/",
            {"tag_ids": [self.tag_one.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_tags_api.FeedTagApiTests -v 2`

Expected: FAIL because feed tag endpoints and relation logic do not exist.

- [ ] **Step 3: Implement feed-tag service methods and endpoints**

Add these methods to `TagService`:

- `list_feed_tags`
- `attach_tags_to_feed`
- `detach_tags_from_feed`

Update `FeedViewSet` with actions for:

- `GET /feeds/{id}/tags/`
- `POST /feeds/{id}/tags/attach/`
- `POST /feeds/{id}/tags/detach/`

Implement these rules:

- Require the current member to own all requested tags.
- Require an existing `MemberFeedSubscription`.
- Make attach idempotent with `get_or_create`.
- Return the feed's current tag list after attach or detach.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_tags_api.FeedTagApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/tag_service.py we_rss/views/feed_views.py we_rss/urls.py we_rss/schema.py we_rss/tests/test_tags_api.py
git commit -m "feat: add feed tag attach and detach APIs"
```

### Task 6: Add article tag APIs and service logic

**Files:**

- Modify: `we_rss/services/tag_service.py`
- Modify: `we_rss/views/article_views.py`
- Modify: `we_rss/urls.py`
- Modify: `we_rss/schema.py`
- Test: `we_rss/tests/test_articles_api.py`
- Test: `we_rss/tests/test_tags_api.py`

- [ ] **Step 1: Write the failing article-tag tests**

```python
class ArticleTagApiTests(APITestCase):
    def test_member_can_attach_multiple_tags_to_article(self):
        response = self.client.post(
            f"/api/v1/we-rss/articles/{self.article.id}/tags/attach/",
            {"tag_ids": [self.tag_one.id, self.tag_two.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 2)

    def test_member_cannot_attach_other_members_tag_to_article(self):
        response = self.client.post(
            f"/api/v1/we-rss/articles/{self.article.id}/tags/attach/",
            {"tag_ids": [self.other_member_tag.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_tags_api.ArticleTagApiTests -v 2`

Expected: FAIL because article tag endpoints and relation logic do not exist.

- [ ] **Step 3: Implement article-tag service methods and endpoints**

Add these methods to `TagService`:

- `list_article_tags`
- `attach_tags_to_article`
- `detach_tags_from_article`

Update `ArticleViewSet` with actions for:

- `GET /articles/{id}/tags/`
- `POST /articles/{id}/tags/attach/`
- `POST /articles/{id}/tags/detach/`

Implement these rules:

- Require the article to belong to the current tenant.
- Require the current member to own all requested tags.
- Do not require feed subscription.
- Return the article's current tag list after attach or detach.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_tags_api.ArticleTagApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/services/tag_service.py we_rss/views/article_views.py we_rss/urls.py we_rss/schema.py we_rss/tests/test_tags_api.py
git commit -m "feat: add article tag attach and detach APIs"
```

## Chunk 4: Tag filtering, verification, and finish-up

This chunk makes the feature useful in the existing feed and article list
screens and then verifies the full tag slice end to end.

### Task 7: Add `AND`-style tag filtering to feed list API

**Files:**

- Modify: `we_rss/views/feed_views.py`
- Modify: `we_rss/schema.py`
- Test: `we_rss/tests/test_feeds_api.py`

- [ ] **Step 1: Write the failing feed filter tests**

```python
class FeedTagFilterApiTests(APITestCase):
    def test_feed_list_filters_by_all_requested_tag_ids(self):
        response = self.client.get(
            f"/api/v1/we-rss/feeds/?tag_ids={self.tag_one.id},{self.tag_two.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["data"]],
            [self.feed_with_both_tags.id],
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_feeds_api.FeedTagFilterApiTests -v 2`

Expected: FAIL because `tag_ids` filtering does not exist yet.

- [ ] **Step 3: Implement the feed list filter**

Update `FeedViewSet.get_queryset()` to:

- parse `tag_ids` from a comma-separated query parameter
- ignore empty tokens
- filter using the current member's `MemberFeedTagRelation`
- require `AND` behavior by counting distinct matched tags per feed

Update schema docs with a new optional `tag_ids` query parameter example.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_feeds_api.FeedTagFilterApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/views/feed_views.py we_rss/schema.py we_rss/tests/test_feeds_api.py
git commit -m "feat: add feed list tag filtering"
```

### Task 8: Add `AND`-style tag filtering to article list API

**Files:**

- Modify: `we_rss/views/article_views.py`
- Modify: `we_rss/schema.py`
- Test: `we_rss/tests/test_articles_api.py`

- [ ] **Step 1: Write the failing article filter tests**

```python
class ArticleTagFilterApiTests(APITestCase):
    def test_article_list_filters_by_all_requested_tag_ids(self):
        response = self.client.get(
            f"/api/v1/we-rss/articles/?tag_ids={self.tag_one.id},{self.tag_two.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["data"]],
            [self.article_with_both_tags.id],
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
`python manage.py test we_rss.tests.test_articles_api.ArticleTagFilterApiTests -v 2`

Expected: FAIL because `tag_ids` filtering does not exist yet.

- [ ] **Step 3: Implement the article list filter**

Update `ArticleViewSet.get_queryset()` to:

- parse `tag_ids` from a comma-separated query parameter
- filter using the current member's `MemberArticleTagRelation`
- keep existing `article_type`, `search`, and `favorite_only` behavior intact
- enforce `AND` semantics the same way as feed filtering

Update schema docs with a matching `tag_ids` query parameter.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
`python manage.py test we_rss.tests.test_articles_api.ArticleTagFilterApiTests -v 2`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add we_rss/views/article_views.py we_rss/schema.py we_rss/tests/test_articles_api.py
git commit -m "feat: add article list tag filtering"
```

### Task 9: Run full tag-system verification

**Files:**

- Modify: any failing implementation files from previous tasks
- Test: `we_rss/tests/test_models.py`
- Test: `we_rss/tests/test_tags_api.py`
- Test: `we_rss/tests/test_feeds_api.py`
- Test: `we_rss/tests/test_articles_api.py`

- [ ] **Step 1: Run the model test slices**

Run:
`python manage.py test we_rss.tests.test_models.WeRssTagModelTests we_rss.tests.test_models.WeRssTagCleanupTests -v 2`

Expected: PASS

- [ ] **Step 2: Run the tag API test file**

Run: `python manage.py test we_rss.tests.test_tags_api -v 2`

Expected: PASS

- [ ] **Step 3: Run the feed and article regression slices**

Run:
`python manage.py test we_rss.tests.test_feeds_api we_rss.tests.test_articles_api -v 2`

Expected: PASS with existing subscribe, favorite, search, and sync behavior
still green.

- [ ] **Step 4: Verify migration and schema generation**

Run: `python manage.py makemigrations --check`

Expected: PASS

Run:
`python manage.py spectacular --file schema.yml`

Expected: PASS with the new tag endpoints and query parameters included.

- [ ] **Step 5: Fix any failures and rerun only the failing commands**

Repeat targeted test commands until all checks are clean.

- [ ] **Step 6: Commit**

```bash
git add we_rss docs/superpowers/specs/2026-03-26-we-rss-tag-design.md schema.yml
git commit -m "feat: implement we_rss member tag system"
```

## Open implementation notes

This section captures a few decisions that are easy to lose during execution.

- Prefer explicit relation models over a generic `target_type` and `target_id`
  table. The business rules already differ between feeds and articles.
- If the database backend makes functional unique constraints awkward, keep the
  database constraint and also add serializer-level validation so the API
  returns a clean duplicate-name error.
- Keep relation list responses small. Return only tag data needed by the UI,
  not feed or article payloads.
- If a helper for parsing `tag_ids` starts getting reused, extract it into
  `we_rss/services/tag_service.py` or a small utility instead of duplicating it
  in both viewsets.

## Suggested execution order

Follow the chunks in order because each chunk depends on the previous one.

1. Add models and cleanup rules.
2. Add tag CRUD serializers, service methods, and routes.
3. Add feed and article tag attachment endpoints.
4. Add feed and article list filtering.
5. Run the full verification slice.

## Handoff

Plan complete and saved to
`docs/superpowers/plans/2026-03-26-we-rss-tag-implementation.md`. Ready to
execute?
