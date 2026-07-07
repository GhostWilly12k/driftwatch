# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] - 2026-07-07 (Sprint 0)
### Added
- Initial Alembic migration: users, user_settings, trades tables
- trades table partitioned monthly via pg_partman (extensions.create_parent), maintenance scheduled via pg_cron