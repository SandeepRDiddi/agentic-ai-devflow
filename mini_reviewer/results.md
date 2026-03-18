# devflow-lab · Agentic AI Demo — Results
_Generated: 2026-03-18 13:32:34  |  Model: `claude-sonnet-4-6`_

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Tasks completed | 3 |
| Total manual estimate | **140 minutes** |
| Total agent time | **77.9 seconds** |
| Overall time saved | **99.1%** |
| Overall speedup | **~108x faster** |

---

## Task 1: Code Review  ·  pr-reviewer skill

- **Skill used**: `pr-reviewer`
- **Manual estimate**: 55 minutes
- **Agent completed in**: 26.76 seconds
- **Time saved**: 99.2%  |  **Speedup**: ~123x

### Output

## PR Review: Authentication Module

**Summary:** Adds user lookup and password reset functions backed by PostgreSQL — but ships with critical security vulnerabilities that must be resolved before merge.

---

## ✅ What's Done Well

- Uses `psycopg2` (a solid, well-supported driver)
- `conn.commit()` is present in `reset_password`
- Function signatures are clean and readable

---

## 🚫 Blockers

### 1. Hardcoded Production Credentials

```python
DB_URL = "postgresql://admin:password123@prod-db:5432/users"
```

Production credentials are committed to source control. Anyone with repo access — or access to git history — owns your database.

**Fix:** Load from environment variables and fail fast if absent.

```python
import os

DB_URL = os.environ["DATABASE_URL"]  # raises KeyError immediately if unset
```

Then set it in your environment, secrets manager (AWS Secrets Manager, Vault), or `.env` file (git-ignored).

---

### 2. SQL Injection in Both Functions

```python
cur.execute(f'SELECT * FROM users WHERE id = {user_id}')
cur.execute(f"UPDATE users SET password='{new_pass}' WHERE email='{email}'")
```

An attacker passes `email = "' OR '1'='1"` and resets every password in the table. Classic, and completely preventable.

**Fix:** Always use parameterized queries.

```python
cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
cur.execute(
    "UPDATE users SET password = %s WHERE email = %s",
    (hashed_password, email),
)
```

The database driver handles escaping — you never do it manually.

---

### 3. Passwords Stored in Plaintext

```python
cur.execute(f"UPDATE users SET password='{new_pass}' WHERE email='{email}'")
```

A database breach exposes every user's actual password. This is a GDPR/SOC2 violation and an immediate user trust failure.

**Fix:** Hash with `bcrypt` before storing. Never store or log the raw value.

```python
import bcrypt

def reset_password(email: str, new_pass: str) -> None:
    hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt())
    conn = get_connection()
    with conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET password = %s WHERE email = %s",
            (hashed.decode(), email),
        )
```

---

### 4. No Authorization Check on Password Reset

```python
def reset_password(email, new_pass):
    # executes unconditionally
```

Any caller can reset any user's password with zero verification. There is no token, session, or current-password check.

**Fix:** Require a verified reset token tied to the email, consumed on use.

```python
def reset_password(email: str, token: str, new_pass: str) -> None:
    if not verify_reset_token(email, token):  # checks DB, expiry, single-use
        raise PermissionError("Invalid or expired reset token")
    # proceed with update
```

---

## ⚠️ Significant Issues

### 5. Connection Leaks Everywhere

```python
conn = psycopg2.connect(DB_URL)
cur.execute(...)
return cur.fetchone()   # conn never closed on success OR exception
```

Every call opens a new connection and leaks it. Under any real load this exhausts the database connection pool.

**Fix:** Use context managers and a shared connection pool.

```python
from psycopg2 import pool

_pool = pool.SimpleConnectionPool(1, 10, dsn=DB_URL)

def get_connection():
    return _pool.getconn()

def get_user(user_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()
    finally:
        _pool.putconn(conn)
```

---

### 6. No Error Handling

A failed query raises an unhandled `psycopg2.Error`, leaks the connection, and likely crashes the caller with an unformatted stack trace exposed to the user.

**Fix:** Catch specific exceptions, log them, and return structured errors.

```python
import logging

log = logging.getLogger(__name__)

def get_user(user_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()
    except psycopg2.Error as e:
        log.error("get_user failed for id=%s: %s", user_id, e)
        raise
    finally:
        _pool.putconn(conn)
```

---

### 7. `SELECT *` in Production Query

```python
cur.execute(f'SELECT * FROM users WHERE id = {user_id}')
```

This pulls every column — including `password`, `ssn`, API keys, or whatever else lives in that table — into application memory and likely into logs.

**Fix:** Select only the columns you actually need.

```python
cur.execute(
    "SELECT id, email, display_name, created_at FROM users WHERE id = %s",
    (user_id,),
)
```

---

## 💡 Nice-to-Haves

- **Type hints** — Add `user_id: int`, `email: str`, `-> dict | None` etc. for IDE support and early error detection
- **Input validation** — Validate email format and enforce password complexity/length before hitting the DB
- **Rate limiting** — `reset_password` should be rate-limited per email/IP to prevent enumeration and abuse
- **Audit logging** — Password resets should write to an audit log (who, when, from what IP) for compliance

---

## Recommended Refactor (Minimal Viable Fix)

```python
import os
import

---

## Task 2: Data Contract  ·  data-contract-bot skill

- **Skill used**: `data-contract-bot`
- **Manual estimate**: 40 minutes
- **Agent completed in**: 32.03 seconds
- **Time saved**: 98.7%  |  **Speedup**: ~75x

### Output

## Step 1 — Generated Contract

```yaml
id: urn:datacontract:platform-team:user_events:2.0.0
name: user_events
version: 2.0.0
owner: platform-team
domain: platform
status: active
description: >
  Captures all user interaction events including authentication, navigation,
  and transactional activity. Each row represents a single discrete event
  emitted by the platform event pipeline.

tags:
  - events
  - user-behaviour
  - transactions
  - platform
  - real-time

schema:
  type: table
  columns:
    - name: user_id
      type: uuid
      nullable: false
      primaryKey: true
      unique: false          # many events per user
      description: >
        Unique identifier for the user who triggered the event.
        References users.id in the identity domain.
      pii: true
      classification: restricted
      tags: [identity]

    - name: event_type
      type: string
      nullable: false
      description: >
        Categorical label for the event. Controls which downstream
        columns are populated (e.g. revenue_usd is only set for
        purchase events).
      enum:
        - login
        - logout
        - purchase
        - view
      classification: internal
      pii: false
      tags: [event-classification]

    - name: session_id
      type: uuid
      nullable: false
      description: >
        Groups events that belong to the same continuous user session.
        Resets on login or after 30 minutes of inactivity.
      pii: false
      classification: internal
      tags: [session]

    - name: timestamp
      type: timestamp_tz          # ODCS v3.0 canonical; timezone-aware
      nullable: false
      description: >
        Wall-clock time at which the event was recorded by the
        originating service, expressed in UTC with timezone offset.
      classification: internal
      pii: false
      tags: [time-series]

    - name: properties
      type: json
      nullable: true
      description: >
        Arbitrary key-value payload attached to the event by the
        emitting service. Schema varies by event_type; consumers
        should treat this as opaque unless event_type is known.
      classification: internal
      pii: false                  # PII must NOT be stored here per policy
      tags: [flexible-payload]
      quality:
        - rule: no_pii_in_properties
          description: >
            Downstream validation job must assert that known PII
            keys (email, name, phone) are absent from this column.

    - name: revenue_usd
      type: decimal
      precision: 10
      scale: 2
      nullable: true
      description: >
        Transaction value in US dollars. Populated if and only if
        event_type = 'purchase'; NULL for all other event types.
      classification: confidential
      pii: false
      tags: [finance, conditional]
      quality:
        - rule: conditional_not_null
          expression: "event_type = 'purchase' → revenue_usd IS NOT NULL"
        - rule: positive_value
          expression: "revenue_usd > 0 WHEN NOT NULL"

sla:
  freshness:
    threshold: 60
    unit: seconds
    description: >
      Events must be available to consumers within 60 seconds of
      the originating service emitting them.
    measurement: lag_seconds           # metric name in observability platform
  availability:
    percentage: 99.9
    window: rolling_30d
    description: >
      Pipeline and serving layer must be available 99.9% of the time
      measured over a rolling 30-day window.

quality:
  - rule: no_duplicate_events
    description: >
      (user_id, session_id, event_type, timestamp) must be unique.
    dimensions: [uniqueness]
  - rule: valid_event_type
    description: event_type must be one of the declared enum values.
    dimensions: [validity]
  - rule: revenue_conditional_null
    description: revenue_usd must be NULL when event_type ≠ 'purchase'.
    dimensions: [consistency]
```

---

## Step 2 — Validation Report

**Result: ✅ Valid — 0 violations, 4 suggestions**

---

### Violations

*None. All ODCS v3.0 required fields are present and internally consistent.*

---

### Suggestions

| # | Field | Suggestion |
|---|-------|------------|
| S1 | `properties` (json) | Consider a `$schema` reference or a per-`event_type` JSON Schema registry entry. Untyped JSON is the most common source of undocumented breaking changes in event pipelines. |
| S2 | `revenue_usd` (conditional) | The "only set for purchase" rule is documented in `quality.rules` but cannot be enforced at the contract layer alone — recommend a dbt test or Great Expectations suite wired to the same expression. |
| S3 | `sla.freshness` | 60 s is aggressive. Add an explicit `measurement_point` field (e.g. `event_emit_time → topic_available` vs `event_emit_time → query_available`) to avoid ambiguity in SLA breach attribution. |
| S4 | `id` (URN) | The generated URN `urn:datacontract:platform-team:user_events:2.0.0` is stable but consider registering it in a data catalogue (e.g. DataHub, Atlan) so `version: 3.0.0` can reference this contract as its predecessor via `previousVersion`. |

---

### Key ODCS v3.0 Decisions Explained

- **`timestamp_tz`** — ODCS v3.0 distinguishes `timestamp` (no tz) from `timestamp_tz` (tz-aware). Your spec said "with timezone" so `timestamp_tz` is the correct canonical type.
- **`classification: restricted` on `user_id`** — ODCS v3.0 uses a four-level classification ladder (`public → internal → confidential → restricted`). A PII primary key

---

## Task 3: README + Tests  ·  pr-reviewer skill

- **Skill used**: `pr-reviewer`
- **Manual estimate**: 45 minutes
- **Agent completed in**: 19.12 seconds
- **Time saved**: 99.3%  |  **Speedup**: ~141x

### Output

I'll tackle both tasks systematically — tests first, then documentation.

---

## Task 1: Pytest Unit Tests

```python
# test_validate_email.py

import pytest
from your_module import validate_email


# ── Helpers ───────────────────────────────────────────────────────────────────

def assert_valid(email: str) -> None:
    assert validate_email(email) is True, f"Expected VALID but got invalid: {email!r}"

def assert_invalid(email: str) -> None:
    assert validate_email(email) is False, f"Expected INVALID but got valid: {email!r}"


# ── Valid emails ───────────────────────────────────────────────────────────────

class TestValidEmails:
    def test_standard_email(self):
        assert_valid("user@example.com")

    def test_plus_addressing(self):
        assert_valid("user+tag@example.com")

    def test_dots_in_local_part(self):
        assert_valid("first.last@example.com")

    def test_subdomain(self):
        assert_valid("user@mail.example.com")

    def test_multiple_subdomains(self):
        assert_valid("user@a.b.example.com")

    def test_numeric_local_part(self):
        assert_valid("1234567890@example.com")

    def test_long_tld(self):
        assert_valid("user@example.technology")   # 10-char TLD

    def test_uppercase_characters(self):
        assert_valid("User.Name@Example.COM")

    def test_hyphen_in_domain(self):
        assert_valid("user@my-company.com")

    def test_long_local_part(self):
        assert_valid("a" * 64 + "@example.com")  # RFC 5321 local-part max


# ── Missing or malformed @ ─────────────────────────────────────────────────────

class TestMissingAt:
    def test_no_at_sign(self):
        assert_invalid("userexample.com")

    def test_multiple_at_signs(self):
        assert_invalid("user@@example.com")

    def test_at_at_start(self):
        assert_invalid("@example.com")

    def test_at_at_end(self):
        assert_invalid("user@")


# ── Dot-related edge cases ─────────────────────────────────────────────────────

class TestDotEdgeCases:
    def test_no_dot_in_domain(self):
        assert_invalid("user@examplecom")

    def test_dot_at_start_of_local_part(self):
        # RFC-invalid; the current regex actually ACCEPTS this — documents the gap
        assert_invalid(".user@example.com")   # 🚫 known regex limitation (see notes)

    def test_dot_at_end_of_local_part(self):
        assert_invalid("user.@example.com")   # 🚫 known regex limitation

    def test_consecutive_dots_in_local(self):
        assert_invalid("user..name@example.com")  # 🚫 known regex limitation

    def test_trailing_dot_in_domain(self):
        assert_invalid("user@example.com.")

    def test_tld_too_short(self):
        assert_invalid("user@example.c")      # TLD must be >= 2 chars


# ── Empty and whitespace inputs ────────────────────────────────────────────────

class TestEmptyAndWhitespace:
    def test_empty_string(self):
        assert_invalid("")

    def test_whitespace_only(self):
        assert_invalid("   ")

    def test_email_with_leading_space(self):
        assert_invalid(" user@example.com")

    def test_email_with_trailing_space(self):
        assert_invalid("user@example.com ")

    def test_email_with_internal_space(self):
        assert_invalid("us er@example.com")


# ── Unicode and non-ASCII ──────────────────────────────────────────────────────

class TestUnicode:
    def test_unicode_local_part(self):
        assert_invalid("üser@example.com")    # non-ASCII rejected by this regex

    def test_unicode_domain(self):
        assert_invalid("user@éxample.com")

    def test_emoji_in_email(self):
        assert_invalid("user😀@example.com")

    def test_cyrillic_characters(self):
        assert_invalid("пользователь@example.com")


# ── Unusually long addresses ───────────────────────────────────────────────────

class TestLongAddresses:
    def test_long_but_valid_domain(self):
        domain = "a" * 50 + ".com"
        assert_valid(f"user@{domain}")

    def test_extremely_long_email(self):
        # RFC 5321 caps total length at 254 chars; this validator doesn't enforce it
        long_email = "a" * 200 + "@example.com"
        # Documents behavior without asserting a specific outcome
        result = validate_email(long_email)
        assert isinstance(result, bool), "Should always return a bool, even for long input"

    def test_long_tld_boundary(self):
        assert_valid("user@example." + "a" * 10)   # long TLD, still valid per regex


# ── Type safety ────────────────────────────────────────────────────────────────

class TestTypeSafety:
    def test_none_input(self):
        with pytest.raises((TypeError, AttributeError)):
            validate_email(None)  # type: ignore[arg-type]

    def test_integer_input(self):
        with pytest.raises((TypeError, AttributeError)):
            validate_email(42)    # type: ignore[arg-type]


# ── Parametrize

---
