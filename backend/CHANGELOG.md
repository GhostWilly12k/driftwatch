# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] - 2026-07-07 (Sprint 0)

### Added
- Initial Alembic migration: users, user_settings, trades tables
- trades table partitioned monthly via pg_partman (extensions.create_parent), maintenance scheduled via pg_cron
- FastAPI app skeleton: app/main.py, CORS middleware, global exception handlers, router stubs for auth/trades/agents, /health endpoint

### Changed
- TimescaleDB replaced with pg_partman for trades partitioning (Supabase deprecated TimescaleDB on PostgreSQL 17). Downstream tasks flagged for review: T-005, T-025, T-032, T-033, T-038, T-065, Milestone 2, Risk Register
- Tables referencing trades (alerts, trade_embeddings) must include entered_at alongside the trade ID, to satisfy the composite primary key (id, entered_at)

### Fixed
- app/models/ directory caused namespace resolution failures; flattened to app/models.py
- Supabase IPv4/IPv6 connection issue resolved via connection pooler with postgres.[project-ref] username format