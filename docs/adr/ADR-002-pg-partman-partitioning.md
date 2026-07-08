# ADR-002: pg_partman for Trade Time-Series Partitioning

**Date:** 2026-07-08
**Status:** Accepted

> Note: the original plan (§7.4) scoped this ADR as "TimescaleDB for trade time-series storage." That approach was superseded before implementation — this ADR documents the decision as actually built.

## Context

The `trades` table is the highest-write, highest-query-volume table in the schema, and nearly every dashboard, calendar, and stats endpoint filters on `entered_at` by date range. The original plan called for using TimescaleDB hypertables (`create_hypertable`) to get fast time-range queries and automatic chunking.

During Sprint 0 setup (T-005), it was discovered that **Supabase has deprecated TimescaleDB support on PostgreSQL 17** — new projects can't provision it. Since Supabase (PostgreSQL 17) is the committed database platform (see plan §2.1 tech stack), the original TimescaleDB approach is not available and needed to be replaced before any migrations were written, rather than retrofitted later.

## Decision

Use **native PostgreSQL declarative partitioning** (`PARTITION BY RANGE (entered_at)`) on the `trades` table, managed by the **pg_partman** extension for automated partition creation and maintenance, with **pg_cron** scheduling the maintenance call.

Implementation specifics:
- `trades` has a composite primary key `(id, entered_at)` — native partitioning requires the partition key to be part of the primary key.
- Partition creation via `extensions.create_parent(...)` — pg_partman's functions live under the `extensions` schema on Supabase, not `partman`.
- `p_interval => '1 month'` (pg_partman 5.3.1 requires this literal string, not `'monthly'`).
- Maintenance (creating future partitions) runs via `CALL extensions.run_maintenance_proc()`, scheduled with `cron.schedule(...)` (the `cron` schema, even though the extension's own namespace is `pg_catalog`).
- Seven monthly child partitions plus a default partition are live as of Sprint 0.

This was deliberately implemented in Sprint 0, before any application code depends on the `trades` schema, specifically to avoid a much harder migration later once real trade data and multiple dependent tables exist.

## Consequences

**Easier:**
- Query planner can prune partitions on date-range filters (calendar, stats, monthly breakdowns) without any application-level changes.
- Staying on stock PostgreSQL 17 rather than a deprecated extension avoids a forced migration mid-project.
- pg_partman + pg_cron are both available and supported directly on Supabase, so no self-hosted Postgres is needed.

**Harder:**
- Every table with a foreign key into `trades` (`alerts`, `trade_embeddings` — Phase 2) must carry `entered_at` alongside the trade `id`, since the primary key is now composite. This is flagged for review on T-025, T-032, T-033, T-038, T-065, Milestone 2, and the Risk Register.
- Alembic autogenerate treats pg_partman's internal bookkeeping tables (`part_config`, `part_config_sub`) as tables to drop; migration diffs must be checked manually before applying.
- Partition maintenance is an operational dependency now (pg_cron job) rather than something TimescaleDB would have handled implicitly — if the cron job silently fails, new months won't get partitions and writes could start hitting the default partition unnoticed.
