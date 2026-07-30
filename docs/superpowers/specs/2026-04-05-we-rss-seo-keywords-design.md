# We RSS SEO keywords design

This document defines a dedicated SEO keyword feature for the `we_rss` Django
app in `lipeaks_backend`. The feature adds member-scoped SEO search keywords
that can be managed independently from the existing private tag system and
linked to zero or more existing `MemberTag` records.

The design keeps `we_rss` aligned with the current project's auth, tenant
isolation, DRF response format, OpenAPI conventions, and service-oriented
layout. It also keeps "content tags" and "SEO keywords" as separate concepts
so each can evolve without overloading the other.

## Goals

This design adds a member-scoped SEO keyword library that supports both CRUD
management and filtered lookup.

- Let each `Member` create and manage SEO search keywords inside `we_rss`.
- Let each SEO keyword store its own `search_index` value.
- Let one SEO keyword link to multiple existing `MemberTag` records.
- Let one SEO keyword exist without any linked tags.
- Let SEO keyword names be unique per member, case-insensitively.
- Require all SEO keyword APIs to accept an explicit `member_id`.
- Let list APIs filter by keyword text and linked tag.

## Non-goals

This first version intentionally keeps the feature narrow and operationally
simple.

- Do not change the existing `MemberTag` ownership model.
- Do not make SEO keywords tenant-shared.
- Do not add historical search-index tracking.
- Do not auto-create tags from keyword input.
- Do not merge SEO keywords into existing feed or article tag APIs.
- Do not require every SEO keyword to be linked to at least one tag.
- Do not add bulk import or export in this version.

## Scope

This design covers three functional areas that ship together as one feature.

1. Member-scoped SEO keyword CRUD.
2. Many-to-many linking between SEO keywords and existing member-private tags.
3. SEO keyword list filtering by keyword text and tag.

## Current project context

The current `we_rss` app already has a member-private tag system with
`MemberTag`, `MemberFeedTagRelation`, and `MemberArticleTagRelation`. Those
records are scoped to one member and one tenant. The existing tag APIs also
work entirely in the current member scope.

That existing model matters because the new SEO keyword feature must align with
the same ownership boundary. A tenant-wide SEO keyword model would conflict
with the current private-tag design, so this feature keeps SEO keywords
member-scoped as well.

## Proposed architecture

The new SEO keyword feature lives entirely inside the existing `we_rss` Django
app. It adds one member-owned keyword model plus one explicit relation model
that links SEO keywords to member-owned tags. This keeps ownership,
constraints, and query behavior explicit.

Recommended file structure changes:

- Modify `we_rss/models.py`
- Modify `we_rss/serializers.py`
- Modify `we_rss/schema.py`
- Modify `we_rss/urls.py`
- Create `we_rss/services/seo_keyword_service.py`
- Create `we_rss/views/seo_keyword_views.py`
- Create `we_rss/migrations/0008_memberseokeyword_and_relations.py`
- Modify `we_rss/tests/test_models.py`
- Create `we_rss/tests/test_seo_keywords_api.py`

The design keeps SEO keyword APIs separate from feed, article, and tag APIs.
This avoids changing existing response contracts and keeps the new behavior
easy to reason about.

## Data ownership and visibility

The new feature follows the same ownership model as the current tag system.
Tenant still provides the isolation boundary, but the member owns both the SEO
keyword records and the keyword-tag relations.

- An SEO keyword belongs to exactly one tenant and exactly one member.
- An SEO keyword is visible only within its owner's member scope.
- A linked tag must belong to the same tenant and the same member.
- SEO keyword APIs must always include `member_id` explicitly.
- Passing `member_id` does not imply cross-member access is allowed.
- Normal member users can operate only on their own `member_id`.

## Domain models

This section defines the new models and the rules behind them.

### `MemberSeoKeyword`

`MemberSeoKeyword` stores one SEO search keyword owned by one member.

Fields:

- `tenant`
- `member`
- `keyword`
- `search_index`
- `created_at`
- `updated_at`
- `is_deleted`

Behavior:

- `keyword` is required.
- `keyword` is trimmed before validation and save.
- `keyword` is unique per member, case-insensitively.
- `search_index` lives directly on the keyword record.
- `search_index` is a current-value field, not a history table.
- One SEO keyword can exist without any linked tags.
- Deleting an SEO keyword deletes only its keyword-tag relations.

Recommended defaults:

- `search_index`: `0`

Recommended constraints and indexes:

- Unique constraint on member plus normalized lower-case `keyword`.
- Index on `tenant`, `member`.
- Index on `tenant`, `member`, `search_index`.
- Index on `tenant`, `member`, `keyword`.
- Ordering by `-updated_at`, `-id`.

### `MemberTagSeoKeywordRelation`

`MemberTagSeoKeywordRelation` stores one member's link between one private tag
and one SEO keyword.

Fields:

- `tenant`
- `member`
- `tag`
- `seo_keyword`
- `created_at`

Behavior:

- A relation is valid only when `tag.member == seo_keyword.member == member`.
- A relation is valid only when all records belong to the same tenant.
- Each `(member, tag, seo_keyword)` tuple is unique.
- Deleting a tag deletes only the relation, not the SEO keyword itself.
- Deleting an SEO keyword deletes only the relation, not the tag itself.

Recommended indexes:

- Index on `tenant`, `member`
- Index on `tenant`, `tag`
- Index on `tenant`, `seo_keyword`

## Validation rules

The feature needs strict validation because `member_id` is explicit in every
request and keyword uniqueness is part of the business rule.

- All SEO keyword APIs must receive `member_id`.
- `member_id` must refer to a member in the current tenant scope.
- Normal member users must not operate on another member's `member_id`.
- Create and update must trim surrounding whitespace from `keyword`.
- An empty or whitespace-only `keyword` is invalid.
- Keyword name uniqueness must ignore case for the same member.
- `search_index` must be an integer greater than or equal to `0`.
- `tag_ids` may be empty or omitted.
- Every linked `tag_id` must belong to the same `member_id`.
- Duplicate `tag_ids` in one request should be tolerated and de-duplicated.
- Detail, update, and delete must fail when the keyword does not belong to the
  requested `member_id`.

## API design

All APIs stay under `/api/v1/we-rss/`. SEO keywords use dedicated endpoints so
the new feature stays independent from the existing tag and content APIs.

### List SEO keywords

This endpoint returns SEO keywords for one explicit member scope and supports
text search plus tag-based filtering.

- `GET /seo-keywords/?member_id={member_id}`

Optional query parameters:

- `search`
  Filter by keyword text using case-insensitive containment.
- `tag_id`
  Return only SEO keywords linked to one tag owned by the same member.

Behavior:

- `member_id` is required.
- The response returns only the requested member's SEO keywords.
- `tag_id` filtering uses relation existence, not `AND` semantics.
- The list returns linked tags inline to avoid extra frontend joins.

### Retrieve SEO keyword detail

This endpoint returns one SEO keyword plus its linked tags for one explicit
member scope.

- `GET /seo-keywords/{id}/?member_id={member_id}`

Behavior:

- `member_id` is required.
- The endpoint returns `404` when the keyword does not belong to the given
  member scope.

### Create SEO keyword

This endpoint creates one SEO keyword for the requested member and optionally
links it to one or more tags in the same request.

- `POST /seo-keywords/`

Suggested request body:

```json
{
  "member_id": 123,
  "keyword": "weight loss recipes",
  "search_index": 6800,
  "tag_ids": [1, 2, 3]
}
```

Behavior:

- `member_id` is required in the body.
- `tag_ids` may be empty.
- The service creates the keyword first, then creates the relation rows.
- If the keyword already exists for the same member, the API returns `400`.

### Update SEO keyword

This endpoint updates one SEO keyword and replaces its linked tags in one
request.

- `PUT /seo-keywords/{id}/`

Suggested request body:

```json
{
  "member_id": 123,
  "keyword": "weight loss menu",
  "search_index": 7200,
  "tag_ids": [2, 4]
}
```

Behavior:

- `member_id` is required in the body.
- The keyword must belong to the same `member_id`.
- `tag_ids` is treated as the full desired set.
- The service syncs relations by replacing old links with the provided set.

### Delete SEO keyword

This endpoint hard-deletes one SEO keyword for one explicit member scope.

- `DELETE /seo-keywords/{id}/`

Suggested request body:

```json
{
  "member_id": 123
}
```

Behavior:

- `member_id` is required.
- Delete removes the SEO keyword and all keyword-tag relations.
- Delete does not affect `MemberTag` records.

## Response shape

The response should follow the existing `we_rss` JSON wrapper style and include
enough tag data for direct frontend rendering.

Suggested SEO keyword response fields:

- `id`
- `member_id`
- `keyword`
- `search_index`
- `tag_ids`
- `tags`
  A list of linked tag summaries with `id`, `name`, `color`, and `sort_order`
- `created_at`
- `updated_at`

Suggested list example:

```json
{
  "id": 11,
  "member_id": 123,
  "keyword": "weight loss recipes",
  "search_index": 6800,
  "tag_ids": [1, 2],
  "tags": [
    {
      "id": 1,
      "name": "Weight Loss",
      "color": "#008000",
      "sort_order": 0
    },
    {
      "id": 2,
      "name": "Recipes",
      "color": "#FF8800",
      "sort_order": 10
    }
  ],
  "created_at": "2026-04-05T10:00:00Z",
  "updated_at": "2026-04-05T10:00:00Z"
}
```

## Error handling

The new APIs should mirror the current `we_rss` validation style so frontend
handling stays consistent.

Recommended error outcomes:

- `400` when `member_id` is missing.
- `400` when `keyword` is blank after trimming.
- `400` when `search_index` is negative or invalid.
- `400` when a duplicate keyword exists for the same member, ignoring case.
- `400` when one or more `tag_ids` do not belong to the requested member.
- `403` when the caller tries to operate on another member's scope.
- `404` when the keyword `id` does not exist in the requested member scope.

## Query and service behavior

The service layer should own all ownership checks, relation synchronization,
and filtered query logic. This keeps the views thin and matches the current
`we_rss` architecture.

Recommended service responsibilities:

- Parse and validate `member_id`.
- Resolve the target member within the current tenant.
- Normalize `keyword`.
- Create, update, and delete SEO keywords.
- Synchronize keyword-tag relations from `tag_ids`.
- Filter the SEO keyword queryset by `member_id`, `search`, and `tag_id`.
- Serialize linked tag summaries efficiently with `prefetch_related`.

## Testing strategy

This feature needs both model-level and API-level coverage because uniqueness,
scope rules, and relation synchronization are the core risk areas.

### Model tests

Model tests should cover the low-level database constraints and cleanup rules.

- Same member cannot create duplicate keywords that differ only by case.
- Different members can reuse the same keyword.
- Deleting an SEO keyword deletes its relations.
- Deleting a tag deletes only the relations, not the SEO keyword.

### API tests

API tests should cover the supported CRUD and filtering behavior end to end.

- Create one SEO keyword successfully.
- Create one SEO keyword with multiple tags.
- Create one SEO keyword with no tags.
- Reject duplicate keywords for the same member, ignoring case.
- List SEO keywords by explicit `member_id`.
- Filter the list by `search`.
- Filter the list by `tag_id`.
- Return linked tags in list and detail responses.
- Replace linked tags on update.
- Delete one SEO keyword successfully.
- Reject linking tags owned by another member.
- Reject operating on another member's `member_id`.

## Implementation notes

The implementation should reuse existing tag-system patterns wherever they fit,
but it should not force SEO-specific behavior into tag-specific service code.

Recommended implementation choices:

- Create a dedicated `seo_keyword_service.py` instead of extending
  `tag_service.py`.
- Use explicit relation models instead of Django's implicit `ManyToManyField`.
- Keep read and write serializers separate.
- Keep OpenAPI examples focused on `member_id`, `keyword`, `search_index`, and
  `tag_ids`.

## Risks and trade-offs

This design is intentionally narrow, but a few trade-offs are worth capturing
before implementation starts.

- Requiring `member_id` on every endpoint adds verbosity, but it makes the data
  scope explicit.
- A dedicated relation model adds one extra table, but it keeps the ownership
  and validation rules simple.
- Returning linked tags inline slightly increases response size, but it reduces
  follow-up calls for the frontend.
- Using a current-value `search_index` avoids time-series complexity, but it
  leaves historical trend analysis for a future feature.

## Next steps

This design is ready to turn into an implementation plan after written spec
review. The implementation plan should break the work into migration, service,
API, schema, and test chunks that follow the current `we_rss` patterns.
