# Application-Bound Daily Check-in & Streak Reward System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-tenant, application-bound daily check-in and consecutive streak reward system supporting customizable reward ladders (e.g. Day 1: 10 pts, Day 2: 15 pts ... Day 7: 100 pts), atomic concurrency control, and automatic integration with application points balances and level upgrades.

**Architecture:** 
- Configurable rules per application (or tenant-global) via `CheckinConfig` specifying streak cycles and JSON reward ladders.
- User streak tracking in `UserCheckinStreak` (current streak, max streak, total days, last check-in date) protected by row-level locking.
- Ledger auditing via `UserCheckinRecord` with database unique constraint `(tenant, application, member, checkin_date)` to prevent double check-ins.
- Seamless dispatch to `AppUserPointsAccount` (and `TenantUserPoints`) with automatic level re-evaluation via `ApplicationUserLevel`.

**Tech Stack:** Python 3.12+, Django 5.x ORM, Django REST Framework, MySQL / SQLite (test).

---

## Task 1: Data Models Definition & Migrations

**Files:**
- Modify: `points/models.py`
- Create migration: `points/migrations/XXXX_checkin_models.py`
- Test: `points/tests/test_checkin_system.py`

**Interfaces:**
- `CheckinConfig`:
  - `tenant`, `application` (Nullable), `cycle_days` (default 7), `cycle_mode` ('repeat' / 'cap'), `reward_ladder` (JSONField), `allow_recheckin` (bool), `recheckin_cost` (int), `is_active` (bool)
  - Method `get_day_reward(day: int) -> int`
- `UserCheckinStreak`:
  - `tenant`, `application` (Nullable), `member`, `current_streak`, `max_streak`, `total_days`, `last_checkin_date`
  - Unique constraint on `[tenant, application, member]`
- `UserCheckinRecord`:
  - `tenant`, `application` (Nullable), `member`, `checkin_date`, `streak_day`, `reward_points`, `is_recheckin`
  - Unique constraint on `[tenant, application, member, checkin_date]`

- [x] **Step 1: Write model definitions in `points/models.py`**
- [x] **Step 2: Generate and apply migrations**
- [x] **Step 3: Register models in `points/admin.py`**

---

## Task 2: Check-in Core Service & Concurrency Engine

**Files:**
- Create: `points/services/checkin_service.py`
- Test: `points/tests/test_checkin_system.py`

**Interfaces:**
- `CheckinService`:
  - `get_or_create_config(tenant, application=None) -> CheckinConfig`
  - `get_checkin_status(member, tenant, application=None, today=None) -> dict`
    Returns: `{ has_checked_in_today, current_streak, max_streak, total_days, today_reward, tomorrow_reward, cycle_days, calendar: [...] }`
  - `execute_checkin(member, tenant, application=None, today=None) -> dict`
    - Acquires `select_for_update()` lock on `UserCheckinStreak`
    - Checks duplicate check-in for `today`
    - Computes streak: `streak = streak + 1 if last_checkin_date == yesterday else 1`
    - Resolves points from `reward_ladder`
    - Updates `AppUserPointsAccount` (or `TenantUserProfile`) + writes `TenantUserPoints` ledger
    - Checks level promotion via `account.check_level_upgrade()`
    - Persists `UserCheckinRecord` & updates `UserCheckinStreak`
    - Returns `{ success: True, points_earned: int, current_streak: int, new_balance: int, level_upgraded: bool, current_level: str }`

- [x] **Step 1: Implement `CheckinService` with atomic transaction & pessimistic locking**
- [x] **Step 2: Write unit tests covering first check-in, consecutive streak, broken streak reset, cycle repeat/cap, and duplicate rejection**
- [x] **Step 3: Verify all test cases pass**

---

## Task 3: REST API Endpoints (Admin Config & Member Operations)

**Files:**
- Modify: `points/api/serializers.py`
- Modify: `points/api/views.py`
- Modify: `points/api/urls.py`
- Test: `points/tests/test_checkin_system.py`

**Endpoints:**
- Admin:
  - `GET /api/v1/points/checkin-configs/`: List check-in configs (filterable by `application_id`)
  - `POST /api/v1/points/checkin-configs/`: Create/update check-in config
  - `GET/PUT/PATCH /api/v1/points/checkin-configs/<id>/`: Retrieve/update config
- Member / Client:
  - `GET /api/v1/points/checkin/status/?application_id=<id>`: Current checkin status & 7-day calendar
  - `POST /api/v1/points/checkin/execute/` `{ application_id: <id> }`: Perform daily checkin
  - `GET /api/v1/points/checkin/records/?application_id=<id>`: Paginated checkin history

- [x] **Step 1: Define serializers for `CheckinConfig`, `CheckinStatus`, and `UserCheckinRecord`**
- [x] **Step 2: Implement `CheckinConfigViewSet` and `MemberCheckinViewSet`**
- [x] **Step 3: Wire routes in `points/api/urls.py`**
- [x] **Step 4: Write comprehensive API integration tests in `test_checkin_system.py`**
- [x] **Step 5: Run tests and verify 100% pass rate**
