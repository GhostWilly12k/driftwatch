## [Unreleased] - Sprint 1

### Added
- User model extended with `password_hash` column (migration `8f2a1c9d4b6e`, chained after `5b7e604fe446`)
- `app/schemas.py`: `UserCreate`, `UserRead` Pydantic schemas
- `tests/test_user_schemas.py`: 5 unit tests covering validation and ORM-to-schema mapping
- `app/core/db.py`: SQLAlchemy engine, `SessionLocal`, and `get_db` FastAPI dependency
- `app/core/security.py`: bcrypt `hash_password` / `verify_password` helpers (shared with T-015 login)
- `POST /api/auth/register` (T-014): creates a user, hashes password with bcrypt, rejects duplicate emails with 409 `EMAIL_TAKEN`
- `tests/test_auth_register.py`: 6 unit tests covering success, bcrypt hashing, duplicate email, and validation errors (mocked DB session)
- `app/core/security.py`: `create_access_token` — issues a signed JWT (30-day expiry via `JWT_EXPIRE_MINUTES`) using `python-jose`
- `app/schemas.py`: `LoginRequest`, `TokenResponse` Pydantic schemas
- `POST /api/auth/login` (T-015): verifies email/password against the stored bcrypt hash, returns a JWT; unknown email and wrong password return an identical 401 `INVALID_CREDENTIALS` response to prevent user enumeration
- `tests/test_auth_login.py`: 6 unit tests covering successful login + JWT claim contents, wrong password, unknown email, enumeration-safety (identical error bodies), and validation errors (mocked DB session)
- `app/core/redis_client.py`: cached Redis client (`get_redis`) and JWT blocklist helpers `blocklist_token` / `is_token_blocklisted` (Upstash)
- `app/core/security.py`: `decode_access_token` — validates JWT signature and expiry, normalising `jose.JWTError` into a 401 `INVALID_TOKEN` response
- `app/schemas.py`: `MessageResponse` schema
- `POST /api/auth/logout` (T-016): adds the caller's JWT to a Redis blocklist with a TTL matching its remaining lifetime, so the entry self-expires with no cleanup job needed
- `tests/test_auth_logout.py`: 5 unit tests covering successful logout + TTL calculation, missing/malformed Authorization header, expired token, and wrong auth scheme (Redis mocked)
- `app/core/deps.py`: `get_current_user` FastAPI dependency (T-018) — resolves the current `User` from a bearer JWT by decoding it, checking the Redis blocklist, and validating the `sub` claim against the DB; exposes a reusable `CurrentUser` type for future protected routes
- `GET /api/auth/me` (T-017): returns the authenticated user's profile; 401s if the token is missing, malformed, expired, blocklisted (`TOKEN_REVOKED`), has a non-UUID subject (`INVALID_TOKEN`), or no longer maps to a user (`USER_NOT_FOUND`)
- `tests/test_auth_me.py`: 8 unit tests covering success, missing/malformed/expired/wrong-scheme auth, blocklisted tokens, and deleted users (Redis and DB mocked)

### Changed
- `app/core/redis_client.py`: added `socket_connect_timeout`/`socket_timeout` (5s) to the Redis client — a connectivity problem now fails fast with a clear error instead of hanging the request indefinitely

### Fixed
- `app/routers/__inti__.py` typo'd filename corrected to `__init__.py`


## [0.1.0] - 2026-07-07 (Sprint 0)

### Added
- Initial Alembic migration: users, user_settings, trades tables
- trades table partitioned monthly via pg_partman (extensions.create_parent), maintenance scheduled via pg_cron
- FastAPI app skeleton: app/main.py, CORS middleware, global exception handlers, router stubs for auth/trades/agents, /health endpoint
- Vercel frontend deployment of /pages
- pgvector extension enabled on Supabase
- README rewritten: split into "Current Setup (Phase 1/Sprint 0)" and "Full Product Architecture (Roadmap)" to prevent aspirational content from being followed as setup instructions; TimescaleDB references corrected to pg_partman throughout
- MkDocs site initialised (docs-site/), configured with docs_dir pointing at root docs/ as the single content source
- ADR-001: FastAPI over Django REST Framework
- ADR-002: pg_partman over TimescaleDB for trade partitioning (supersedes original plan framing)

### Changed
- TimescaleDB replaced with pg_partman for trades partitioning (Supabase deprecated TimescaleDB on PostgreSQL 17). Downstream tasks flagged for review: T-005, T-025, T-032, T-033, T-038, T-065, Milestone 2, Risk Register
- Tables referencing trades (alerts, trade_embeddings) must include entered_at alongside the trade ID, to satisfy the composite primary key (id, entered_at)

### Fixed
- app/models/ directory caused namespace resolution failures; flattened to app/models.py
- Supabase IPv4/IPv6 connection issue resolved via connection pooler with postgres.[project-ref] username format
- docs/index.md UTF-8 BOM encoding issue (PowerShell `>` redirection writes UTF-16LE) blocking `mkdocs serve`

### Known Issues / Carried Over
- T-009 (GitHub Actions CI: lint + type-check) blocked on an external GitHub issue; not yet resolved as of Sprint 0 close. Task throughput unaffected, so no Risk Register entry opened — rolling into Sprint 1 as an explicit carry-over item.