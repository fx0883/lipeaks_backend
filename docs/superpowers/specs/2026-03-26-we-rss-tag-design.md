# We RSS tag system design

This document defines the first dedicated tag system for the `we_rss` Django
app in `lipeaks_backend`. The design adds private member-owned tags that can be
attached to subscribed WeChat feeds and tenant-visible WeChat articles without
changing the existing feed and article API response shapes.

The design keeps `we_rss` aligned with the current project's auth, tenant
isolation, DRF response format, and OpenAPI conventions. It also keeps tag
state separate from tenant-shared content state so different members can tag
the same feed or article differently.

## Goals

This design adds a member-private tagging system that supports both management
and query use cases.

- Let each `Member` create and manage a personal tag library inside `we_rss`.
- Let a member attach existing tags to subscribed `WechatFeed` records.
- Let a member attach existing tags to tenant-visible `WechatArticle` records.
- Let feed and article list APIs filter by one or more tag IDs.
- Keep all tag ownership and visibility private to the tag owner.
- Preserve the current `feeds/` and `articles/` response contracts.

## Non-goals

This first version intentionally excludes broader taxonomy features.

- Do not create tenant-shared tags.
- Do not create public tags that other members can read or reuse.
- Do not auto-create tags during feed or article tagging.
- Do not add tags inline to existing feed or article serializers.
- Do not support sub-account-specific tag inheritance rules.
- Do not add generic polymorphic tagging across unrelated apps.

## Scope

This design covers three functional areas that work together as one feature.

1. Member-owned tag management.
2. Feed and article tag attachment and detachment.
3. Feed and article filtering by tag IDs with `AND` semantics.

## Architecture

The tag system lives entirely inside the existing `we_rss` Django app. It uses
one member-owned tag model plus two explicit relation models, one for feeds and
one for articles. This keeps validation and query behavior clear because feed
tagging and article tagging already have different business rules.

Recommended file structure changes:

- Modify `we_rss/models.py`
- Modify `we_rss/serializers.py`
- Modify `we_rss/urls.py`
- Modify `we_rss/views/feed_views.py`
- Modify `we_rss/views/article_views.py`
- Create `we_rss/views/tag_views.py`
- Modify `we_rss/schema.py`
- Create or modify `we_rss/services/tag_service.py`
- Modify `we_rss/services/feed_service.py`
- Modify `we_rss/tests/test_models.py`
- Create `we_rss/tests/test_tags_api.py`
- Modify `we_rss/tests/test_feeds_api.py`
- Modify `we_rss/tests/test_articles_api.py`

The design keeps existing feed and article APIs stable. Tag operations use
dedicated endpoints so member-private metadata does not leak into tenant-shared
content payloads.

## Data ownership and visibility

The tag system mixes tenant scoping with member ownership. The tenant still
provides the isolation boundary, but the member owns the tag records and the
tag relations.

- A tag belongs to exactly one tenant and exactly one member.
- A tag is visible only to its owner.
- A tag owner is the only caller who can create, list, update, delete, attach,
  detach, or query that tag.
- Tenant admins and super admins do not manage member-private tags through
  these APIs.
- Two different members in the same tenant can tag the same feed or article
  independently without seeing each other's tag state.

## Domain models

This section defines the tag-specific models and the rules behind them.

### `MemberTag`

`MemberTag` stores the tag definition owned by one member.

Fields:

- `tenant`
- `member`
- `name`
- `color`
- `description`
- `sort_order`
- `is_pinned`
- `created_at`
- `updated_at`

Behavior:

- `name` is required.
- `name` is unique per member, case-insensitively.
- A tag can be attached to feeds, articles, or both.
- A tag is hard-deleted.
- Deleting a tag must also delete all feed and article tag relations for that
  tag.

Recommended defaults:

- `color`: `""`
- `description`: `""`
- `sort_order`: `0`
- `is_pinned`: `False`

Recommended constraints and indexes:

- Unique constraint on member plus normalized lower-case name.
- Index on `tenant`, `member`.
- Ordering by `-is_pinned`, `sort_order`, `-id`.

### `MemberFeedTagRelation`

`MemberFeedTagRelation` stores one member's tag attachment to one feed.

Fields:

- `tenant`
- `member`
- `tag`
- `feed`
- `created_at`

Behavior:

- A member can attach an owned tag only to a feed the same member currently
  subscribes to.
- Each `(member, tag, feed)` tuple is unique.
- Deleting a tag deletes the relation.
- Deleting a feed deletes the relation.
- Unsubscribing from a feed deletes that member's feed-tag relations for the
  feed.

Recommended indexes:

- Index on `tenant`, `member`
- Index on `tenant`, `feed`
- Index on `tenant`, `tag`

### `MemberArticleTagRelation`

`MemberArticleTagRelation` stores one member's tag attachment to one article.

Fields:

- `tenant`
- `member`
- `tag`
- `article`
- `created_at`

Behavior:

- A member can attach an owned tag to any article that exists in the current
  tenant.
- Feed subscription is not required for article tagging.
- Each `(member, tag, article)` tuple is unique.
- Deleting a tag deletes the relation.
- Deleting an article deletes the relation.

Recommended indexes:

- Index on `tenant`, `member`
- Index on `tenant`, `article`
- Index on `tenant`, `tag`

## Validation rules

The system needs strict validation because all tags are member-private and name
uniqueness is important.

- Tag create and update must trim surrounding whitespace from `name`.
- An empty or whitespace-only `name` is invalid.
- Tag name uniqueness must ignore case for the same member.
- Tag attach and detach endpoints accept multiple `tag_ids`.
- Attach requests must fail if any `tag_id` does not belong to the current
  member.
- Attach requests for feeds must fail if the current member is not subscribed
  to the target feed.
- Attach requests for articles must fail if the article does not belong to the
  current tenant.
- The system must not auto-create missing tags from tag names during attach.

## API design

All APIs remain under `/api/v1/we-rss/`. Existing feed and article endpoints
stay in place, while tag behavior is added through dedicated endpoints and
query parameters.

### Tag management APIs

These APIs manage the current member's private tag library.

- `GET /tags/`
- `POST /tags/`
- `GET /tags/{id}/`
- `PUT /tags/{id}/`
- `DELETE /tags/{id}/`

Notes:

- `GET /tags/` returns only the current member's tags.
- `GET /tags/` can include `feed_count` and `article_count` for each tag.
- `DELETE /tags/{id}/` hard-deletes the tag and all its relations.

Suggested response fields for tag detail and list:

- `id`
- `name`
- `color`
- `description`
- `sort_order`
- `is_pinned`
- `feed_count`
- `article_count`
- `created_at`
- `updated_at`

### Feed tag APIs

These APIs manage the current member's tags on one feed.

- `GET /feeds/{id}/tags/`
- `POST /feeds/{id}/tags/attach/`
- `POST /feeds/{id}/tags/detach/`

Suggested request body for attach and detach:

```json
{
  "tag_ids": [1, 2, 3]
}
```

Notes:

- `GET /feeds/{id}/tags/` returns only the current member's tags attached to
  that feed.
- `POST /feeds/{id}/tags/attach/` is additive and idempotent.
- `POST /feeds/{id}/tags/detach/` removes only the requested relations.
- Feed tag attach requires an active `MemberFeedSubscription` for that feed.

### Article tag APIs

These APIs manage the current member's tags on one article.

- `GET /articles/{id}/tags/`
- `POST /articles/{id}/tags/attach/`
- `POST /articles/{id}/tags/detach/`

Suggested request body for attach and detach:

```json
{
  "tag_ids": [1, 2, 3]
}
```

Notes:

- `GET /articles/{id}/tags/` returns only the current member's tags attached
  to that article.
- `POST /articles/{id}/tags/attach/` is additive and idempotent.
- `POST /articles/{id}/tags/detach/` removes only the requested relations.
- Article tagging does not require a feed subscription.

## Feed and article filtering

Tagging becomes useful only when the existing list APIs can query by tag
membership. This version adds filtering without changing existing response
shapes.

### Feed list filtering

`GET /feeds/` gains an optional `tag_ids` query parameter.

Suggested format:

- `GET /feeds/?tag_ids=1,2,3`

Behavior:

- The filter applies only to the current member's tag relations.
- Multiple tags use `AND` semantics.
- A feed matches only if the current member attached all requested tags.

### Article list filtering

`GET /articles/` gains an optional `tag_ids` query parameter.

Suggested format:

- `GET /articles/?tag_ids=1,2,3`

Behavior:

- The filter applies only to the current member's tag relations.
- Multiple tags use `AND` semantics.
- An article matches only if the current member attached all requested tags.

## Serializer and view strategy

The design should follow the existing `we_rss` style that uses explicit
serializers, viewsets, and schema annotations.

- Keep feed and article serializers unchanged for the main endpoints.
- Add dedicated serializers for tag CRUD and attach or detach operations.
- Add tag list and detail schema examples in `we_rss/schema.py`.
- Keep tag permission rules aligned with `WeRssTenantContextMixin`.
- Validate ownership in view or service code instead of trusting raw IDs from
  the request body.

## Service-layer behavior

The service layer should enforce business rules so views stay thin and model
rules stay consistent.

Recommended service responsibilities:

- Create, update, delete, and list member-owned tags.
- Normalize tag names before uniqueness checks.
- Attach tags to feeds in bulk with subscription validation.
- Detach tags from feeds in bulk.
- Attach tags to articles in bulk with tenant validation.
- Detach tags from articles in bulk.
- Remove feed tag relations when unsubscribe logic runs.
- Build list-query helpers for `AND`-style tag filtering on feeds and
  articles.

## Deletion and cleanup rules

The tag system has explicit cleanup behavior to avoid stale member-private
relations.

- Deleting a `MemberTag` must delete all related feed and article tag
  relations.
- Deleting a `WechatFeed` must delete related feed-tag relations.
- Deleting a `WechatArticle` must delete related article-tag relations.
- Unsubscribing a member from a feed must delete that member's feed-tag
  relations for the feed.

## Testing strategy

This feature needs model, API, and query coverage because it mixes tenant
scope, member ownership, uniqueness, and cleanup rules.

Required test areas:

- Tag create, list, detail, update, and delete for the current member.
- Case-insensitive tag name uniqueness per member.
- Reuse of the same tag name by different members in the same tenant.
- Feed tag attach and detach with bulk `tag_ids`.
- Rejection when attaching a feed tag without a subscription.
- Article tag attach and detach with bulk `tag_ids`.
- Rejection when attaching someone else's tag.
- Feed list filtering by one tag.
- Feed list filtering by multiple tags with `AND` behavior.
- Article list filtering by one tag.
- Article list filtering by multiple tags with `AND` behavior.
- Automatic cleanup when a tag is deleted.
- Automatic cleanup when a feed is unsubscribed.
- Automatic cleanup when a feed or article is deleted.

## Risks and constraints

The feature is small in surface area, but a few risks are easy to miss if the
implementation is rushed.

- Case-insensitive uniqueness must work reliably with the project's database.
- Filtering with multiple tag IDs can become incorrect if the query uses `OR`
  logic by accident.
- Feed tagging depends on subscription validation, which must stay in sync with
  existing unsubscribe behavior.
- Member-private tags must never leak through tenant-shared list APIs.

## Future expansion

This design leaves room for later product work without changing the core
ownership model.

- Batch tag lookup for many feeds or many articles in one request.
- Tag usage history or recent tags.
- Tag color presets or UI themes.
- Pinned-tag shortcuts in member clients.
- Export or import of a member's tag library.

## Summary

The `we_rss` tag system is a member-private layer on top of tenant-shared feeds
and articles. `MemberTag` owns the label definition, `MemberFeedTagRelation`
stores tags on subscribed feeds, and `MemberArticleTagRelation` stores tags on
tenant-visible articles. Existing feed and article payloads stay stable, while
new tag APIs and tag-based filters provide the member-specific behavior.
