# We RSS app design

This document defines the first implementation of a new `we_rss` Django app in
`lipeaks_backend`. The app ports only the WeChat article and public account
capabilities from `we-mp-rss-main`. It does not port that project's user
management, JWT, access key, or system auth model.

The design assumes the current Django project's `Member` authentication remains
the only caller identity for all `we_rss` APIs. All data is shared within a
tenant and isolated across tenants.

## Goals

This app builds a tenant-shared WeChat content domain inside the current Django
project.

- Manage WeChat platform scraping credentials through `WechatCredential`.
- Manage subscribed public accounts through `WechatFeed`.
- Manage scraped WeChat articles through `WechatArticle`.
- Output RSS-style content for authenticated member clients.
- Reuse the current Django project's auth, middleware, response format, and
  documentation stack.

## Non-goals

This first version intentionally excludes several parts of
`we-mp-rss-main`.

- Do not port `we-mp-rss-main` user management.
- Do not port `we-mp-rss-main` JWT, access key, or auth endpoints.
- Do not expose public RSS endpoints without member authentication.
- Do not implement tags, export tools, message tasks, GitHub update, or system
  info.
- Do not mix `WechatArticle` with existing `cms.Article`.

## Scope

This first version includes four functional areas.

1. WeChat scraping credential lifecycle, centered on QR-code login and
   automatic credential persistence.
2. Public account management and feed synchronization.
3. Article listing, detail, refresh, status updates, and direct import by
   article URL.
4. Authenticated RSS output for the current tenant.

## Architecture

The new app lives as a standard Django app named `we_rss`. It follows the
current project structure and uses DRF for JSON APIs plus authenticated Django
views for RSS output.

Recommended file structure:

- `we_rss/models.py`
- `we_rss/serializers.py`
- `we_rss/urls.py`
- `we_rss/views/credential_views.py`
- `we_rss/views/feed_views.py`
- `we_rss/views/article_views.py`
- `we_rss/views/rss_views.py`
- `we_rss/services/credential_service.py`
- `we_rss/services/feed_service.py`
- `we_rss/services/article_service.py`
- `we_rss/services/rss_service.py`
- `we_rss/tests/`

The app must use existing project auth and request context:

- Caller must be an authenticated `Member`.
- Caller must belong to an active `Tenant`.
- All app queries must be filtered by `request.user.tenant`.
- All app writes must attach the current tenant.

## Data ownership and permissions

All `we_rss` data is tenant-shared.

- Any authenticated `Member` in a tenant can read the tenant's credentials,
  feeds, articles, tasks, and RSS output.
- Any authenticated `Member` in a tenant can create and update that tenant's
  `we_rss` resources in the first version.
- Audit fields still record who created or updated data.
- Cross-tenant reads and writes are never allowed.

If a `Member` has no tenant, the app must reject access with a permission or
validation error.

## Domain models

This section defines the first version's core models.

### `WechatCredential`

`WechatCredential` stores the WeChat platform scraping credential used to search
public accounts and fetch article data. It is not a system user credential.

Fields:

- `tenant`
- `name`
- `status`
  Values: `active`, `expired`, `invalid`, `disabled`, `pending`
- `token`
- `cookie`
- `expires_at`
- `last_login_at`
- `last_check_at`
- `last_error`
- `is_default`
- `created_by`
- `updated_by`
- timestamps

Behavior:

- Credentials are shared by tenant.
- Multiple credentials may exist per tenant.
- At most one credential is default per tenant.
- Credentials are created or updated by QR-code login flow, not manual token or
  cookie entry.

### `WechatCredentialLoginSession`

`WechatCredentialLoginSession` tracks a QR-code login flow until the system can
save a valid `WechatCredential`.

Fields:

- `tenant`
- `session_id`
- `status`
  Values: `pending`, `scanned`, `confirmed`, `success`, `failed`, `expired`
- `qr_code_url`
- `qr_code_image`
- `scan_status`
- `token_snapshot`
- `cookie_snapshot`
- `error_message`
- `expired_at`
- `credential`
  Nullable FK to `WechatCredential` once persisted
- `created_by`
- timestamps

Behavior:

- Frontend starts a login session.
- Frontend polls session status.
- Backend persists or updates `WechatCredential` automatically when login
  succeeds.
- Frontend does not manually post token or cookie data.

### `WechatFeed`

`WechatFeed` represents a public account tracked by the tenant.

Fields:

- `tenant`
- `credential`
  Nullable FK to `WechatCredential`
- `source_id`
- `faker_id`
- `biz`
- `mp_name`
- `mp_cover`
- `mp_intro`
- `status`
- `sync_time`
- `update_time`
- `last_synced_at`
- `is_featured`
- `created_by`
- `updated_by`
- timestamps

Behavior:

- A tenant can track many feeds.
- A feed can use the tenant default credential or an explicitly assigned
  credential.
- `is_featured` supports a synthetic feed used for direct article URL imports.

### `WechatArticle`

`WechatArticle` stores scraped WeChat articles. It is fully separate from
`cms.Article`.

Fields:

- `tenant`
- `feed`
- `source_id`
- `title`
- `description`
- `content`
- `url`
- `pic_url`
- `publish_time`
- `status`
- `is_read`
- `is_favorite`
- `last_refreshed_at`
- `read_num`
- `like_num`
- `old_like_num`
- `share_num`
- `collect_num`
- `comment_count`
- `comment_reply_count`
- `comment_total_count`
- timestamps

Behavior:

- Statistics fields are stored as article snapshots.
- All statistics fields default to `0`.
- `comment_total_count` is stored directly and refreshed together with comment
  fields in the same transaction.

### `WechatSyncTask`

`WechatSyncTask` persists async or long-running sync operations.

Fields:

- `tenant`
- `task_type`
  Values such as `feed_sync`, `article_refresh`, `article_import`
- `status`
  Values such as `pending`, `running`, `success`, `failed`
- `target_type`
- `target_id`
- `message`
- `result_payload`
- `started_at`
- `finished_at`
- `created_by`
- timestamps

Behavior:

- Replace in-memory task tracking.
- Support task polling APIs.
- Record sync failures and partial results.

## API design

All APIs are mounted under `/api/v1/we-rss/`.

All APIs require current-project `Member` JWT authentication, including RSS
output.

### Credential APIs

These APIs manage tenant-shared `WechatCredential` records and QR-code login
sessions.

#### Credential resources

- `GET /credentials/`
- `GET /credentials/{id}/`
- `PUT /credentials/{id}/`
- `DELETE /credentials/{id}/`
- `POST /credentials/{id}/check/`
- `POST /credentials/{id}/set-default/`

Notes:

- No `POST /credentials/` endpoint for manual token or cookie creation.
- `PUT /credentials/{id}/` updates metadata only, such as `name`.
- `POST /credentials/{id}/check/` validates whether token and cookie still
  work.

#### QR login session resources

- `POST /credentials/login-sessions/`
- `GET /credentials/login-sessions/{session_id}/`

Recommended flow:

1. Client creates a login session and receives QR-code data.
2. Client polls the session endpoint.
3. Backend updates session state.
4. Backend auto-creates or auto-updates `WechatCredential` after successful
   login.

### Feed APIs

These APIs manage tenant feeds and trigger article synchronization.

- `GET /feeds/`
- `POST /feeds/`
- `GET /feeds/{id}/`
- `PUT /feeds/{id}/`
- `DELETE /feeds/{id}/`
- `GET /feeds/search/`
- `POST /feeds/{id}/sync/`

Notes:

- `GET /feeds/search/` searches WeChat-side public accounts through an active
  credential.
- Search results do not automatically create feed records.
- `POST /feeds/{id}/sync/` creates a `WechatSyncTask`, fetches articles, and
  upserts `WechatArticle`.

### Article APIs

These APIs manage stored article data and article refresh behavior.

- `GET /articles/`
- `GET /articles/{id}/`
- `DELETE /articles/{id}/`
- `POST /articles/import-by-url/`
- `POST /articles/{id}/refresh/`
- `GET /tasks/{task_id}/`
- `PUT /articles/{id}/read/`
- `PUT /articles/{id}/favorite/`

Notes:

- `POST /articles/import-by-url/` imports a single article by WeChat article
  URL. The backend may attach it to the synthetic featured feed.
- `POST /articles/{id}/refresh/` refreshes content and statistics fields.
- `PUT /articles/{id}/read/` and `PUT /articles/{id}/favorite/` update tenant
  article state in place.

### RSS APIs

These APIs output subscription content for authenticated member clients.

- `GET /rss/`
- `GET /rss/{feed_id}/`
- `GET /rss/content/{article_id}/`

Notes:

- RSS endpoints still require `Member` JWT authentication.
- First version may start with RSS XML only.
- Output can expand later to Atom or JSON feed formats.

## Response and rendering rules

Management APIs must use the current project's standard DRF JSON response
format.

RSS endpoints have different output rules:

- Subscription endpoints return XML or HTML directly.
- RSS authentication still runs before response rendering.
- RSS responses do not wrap output in standard JSON.

## Integration with existing project

The app must integrate with existing project conventions.

- Add `we_rss` to `INSTALLED_APPS`.
- Mount app URLs under `/api/v1/we-rss/` in `core/urls.py`.
- Reuse current JWT auth and DRF defaults.
- Add schema annotations that match the project's OpenAPI setup.
- Reuse tenant isolation rules by filtering with `request.user.tenant`.

## Testing strategy

This first version must include automated coverage for the critical tenant and
member behavior.

- Authentication success and failure for `Member`.
- Rejection when a member has no tenant.
- Tenant isolation for credentials, feeds, articles, and tasks.
- QR login session success path and auto-persisted `WechatCredential`.
- Feed creation and feed sync.
- Article import by URL.
- Article refresh with statistics updates.
- RSS output under authenticated access.

Tests should follow the current project's Django and DRF testing style. RSS
tests may validate content type, auth behavior, and minimal XML or HTML output.

## Risks and constraints

This implementation has a few explicit constraints.

- QR-code login depends on WeChat platform behavior and may require careful
  driver isolation.
- Existing `we-mp-rss-main` logic cannot be copied as-is because it assumes
  FastAPI, SQLAlchemy, and a different auth stack.
- RSS endpoints protected by JWT work for internal clients, but not for
  unauthenticated third-party readers.
- Long-running sync logic should avoid unmanaged background threads inside
  request handlers where possible.

## Future expansion

This design intentionally leaves room for later features.

- Feed tags
- Export tools
- Scheduled sync
- Richer RSS formats
- Per-member write permissions inside a tenant

## Summary

The `we_rss` app is a tenant-shared, member-authenticated Django app for
WeChat scraping credentials, public account management, article storage, and
authenticated RSS output. It uses the current project's auth and tenant model,
while keeping all `we-mp-rss-main` user-management concerns out of scope.
