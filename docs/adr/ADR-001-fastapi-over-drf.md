# ADR-001: FastAPI over Django REST Framework

**Date:** 2026-07-08
**Status:** Accepted

## Context

CognitionTrade's backend needs to serve a JSON API for trade CRUD, auth, and — starting Sprint 4 — a multi-agent AI pipeline that calls the Anthropic API asynchronously (chart vision analysis, streaming chat responses in Phase 2). The team is a solo developer working with an AI pair (Claude) across a 6-week, 4-day-a-week sprint schedule, so setup speed and low ceremony matter as much as long-term scalability.

Two realistic options were considered: Django REST Framework (DRF) and FastAPI.

## Decision

Use **FastAPI** as the core backend framework.

Reasons:
- Native `async`/`await` support, which matters once background agent calls (Sprint 4+) and streaming responses (Phase 2 chat) are in play — DRF's sync-first request cycle would require more workarounds.
- Pydantic-based request/response validation is built in, replacing what would otherwise be DRF serializers, with less boilerplate.
- Auto-generated OpenAPI/Swagger docs at `/docs` satisfy the "API Reference" documentation layer (plan §7.1) with zero extra work.
- Smaller framework surface area suits a solo-plus-AI team working in short sprints; no admin site, ORM, or app-registry conventions to learn or fight.

## Consequences

**Easier:**
- Async agent calls and future streaming endpoints require no framework workarounds.
- API reference documentation is free (Swagger UI) and always in sync with the code.
- Faster local setup — fewer moving parts than a Django project.

**Harder:**
- No built-in admin panel — any internal data-inspection tooling has to be built manually or done via a DB GUI (TablePlus/DBeaver, per plan §11).
- No built-in ORM — SQLAlchemy 2.0 + Alembic is used instead, which means migrations and model relationships are the developer's responsibility rather than "the framework's way."
- Smaller batteries-included ecosystem than Django for things like permissions/auth scaffolding — JWT auth (T-013–T-018) is hand-rolled rather than using a mature package like `django-rest-framework-simplejwt`.
