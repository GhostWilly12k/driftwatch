# CognitionTrade — AI Trading Journal

A full-stack AI-powered trading journal: calendar trade history, execution gap analysis, tilt detection, and a multi-agent AI coaching system.

**Status:** Phase 1, Sprint 0 (Environment & Foundation) — in progress. See [CHANGELOG.md](./CHANGELOG.md) for what's actually shipped so far, and `CognitionTrade_Phase1_Agile_Plan_FINAL.docx` for the full sprint plan.

> This README is split in two: **Current Setup**, which reflects exactly what's built and decided as of Sprint 0, and **Full Product Architecture (Roadmap)**, which is the long-range design blueprint for Phase 2 and beyond. Anything in the roadmap section is not implemented yet — don't follow it as setup instructions.

---

## Project Structure

```
cognitiontrade/
├── pages/                  # All HTML pages (frontend, mock-data stage)
│   ├── index.html          # Landing / marketing page
│   ├── login.html          # Sign in page
│   ├── dashboard.html      # Main app dashboard
│   ├── journal.html        # Log a trade
│   ├── trades.html         # Trade history calendar
│   ├── performance.html    # Performance analytics
│   ├── strategy.html       # Execution review / gap analysis
│   ├── researcher.html     # Market briefing (UI shell — backend is Phase 2, out of scope for Phase 1)
│   ├── chat.html           # AI Coach chat (UI shell — backend is Phase 2, out of scope for Phase 1)
│   └── settings.html       # Settings (profile, appearance, etc.)
│
├── css/
│   ├── theme.css           # CSS variables (dark/light tokens) + base reset
│   ├── components.css      # Buttons, cards, tables, forms, calendar, chat, etc.
│   ├── shell.css            # Sidebar, topbar, layout
│   └── landing.css         # Landing page styles
│
├── js/
│   ├── app.js              # Core: theme toggle, auth, shared data (TRADES_BY_DATE)
│   ├── sidebar.js          # Injects shared sidebar HTML on every page
│   ├── charts.js           # All Chart.js instances (equity, monthly, MAE/MFE, sentiment)
│   └── calendar.js         # Calendar render, month navigation, day drill-down
│
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI entry point, CORS, exception handlers, router stubs
│   │   ├── models.py        # SQLAlchemy ORM models (flat file — see note below)
│   │   └── db.py           # Database connection
│   ├── alembic/             # Migrations (initial revision: users, user_settings, trades)
│   ├── requirements.txt
│   └── .env                # Not committed — see Environment Variables below
│
├── assets/                 # Icons, logo, images
└── README.md
```

> **Note on `app/models.py`:** this is deliberately a flat module, not an `app/models/` package. A package directory here caused namespace resolution failures during Sprint 0 (see CHANGELOG 0.1.0 → Fixed). Keep it flat unless you have a specific reason to split it, and if you do split it, test imports carefully first.

---

## Current Setup (Phase 1 / Sprint 0)

These are the actual steps to reproduce the working local environment as of Sprint 0. This supersedes anything about setup found in the Roadmap section further down.

### Prerequisites

- Python 3.11+
- A Supabase project (PostgreSQL 17)
- An Upstash Redis instance
- Node.js only if you want to run the frontend through `npx serve` instead of Python's http.server

### 1. Clone and set up the virtual environment

```bash
git clone https://github.com/GhostWilly12k/driftwatch.git
cd driftwatch/backend

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install fastapi "uvicorn[standard]" sqlalchemy alembic psycopg2-binary python-jose bcrypt redis anthropic
```

### 2. Provision Supabase (PostgreSQL 17)

Create a project at supabase.com. Then, in Project Settings → Database, grab the **connection pooler** string, not the direct connection string — direct connections from local dev hit IPv4/IPv6 resolution issues on some networks. The pooler string uses the `postgres.[project-ref]` username format:

```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

Put this in `.env` as `DATABASE_URL`.

> TimescaleDB is **not** used for the `trades` table. Supabase deprecated TimescaleDB support on PostgreSQL 17, so partitioning is done with native Postgres `PARTITION BY RANGE (entered_at)` plus the `pg_partman` extension. See the schema section below and CHANGELOG 0.1.0 for details.

### 3. Provision Upstash Redis

Create a Redis database at upstash.com, copy the `REDIS_URL`, and put it in `.env`.

### 4. Create `.env`

```bash
cp .env.example .env
```

Fill in at minimum:

```
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
REDIS_URL=redis://default:[password]@[endpoint].upstash.io:[port]
JWT_SECRET=<generate a long random string>
ANTHROPIC_API_KEY=<your key>
```

### 5. Run the migration

The initial Alembic migration (creating `users`, `user_settings`, and the partitioned `trades` table) is already written and committed.

```bash
alembic upgrade head
```

If you ever regenerate a migration with `alembic revision --autogenerate`, check the diff before applying it — pg_partman's internal tables (`part_config`, `part_config_sub`) tend to show up as tables autogenerate wants to drop. Remove those lines from the migration file manually; they're pg_partman's own bookkeeping tables, not yours to touch.

### 6. Run the backend

```bash
uvicorn app.main:app --reload
```

Confirm `http://localhost:8000/docs` loads (Swagger UI) and `http://localhost:8000/health` returns OK.

### 7. Run the frontend

```bash
cd ../pages
python3 -m http.server 3000
# or: npx serve .
```

Open `http://localhost:3000/index.html`. All pages currently run on mock data (`TRADES_BY_DATE` in `app.js`, mock `CT.auth`) — wiring to the real API happens sprint-by-sprint per the plan (see "Replacing Mock Data with Real API" below).

---

## Database Schema (Current)

```sql
-- Users
CREATE TABLE users (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email        TEXT UNIQUE NOT NULL,
  name         TEXT,
  plan         TEXT DEFAULT 'starter',
  avatar_url   TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- User Settings
CREATE TABLE user_settings (
  user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
  account_size    NUMERIC DEFAULT 10000,
  risk_per_trade  NUMERIC DEFAULT 1.0,
  daily_max_loss  NUMERIC DEFAULT 200,
  weekly_max_loss NUMERIC DEFAULT 600,
  theme           TEXT DEFAULT 'dark',
  agent_config    JSONB DEFAULT '{}',
  notif_config    JSONB DEFAULT '{}',
  PRIMARY KEY (user_id)
);

-- Trades — native Postgres range partitioning via pg_partman, NOT a TimescaleDB hypertable
CREATE TABLE trades (
  id              UUID DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
  symbol          TEXT NOT NULL,
  direction       TEXT NOT NULL,
  strategy        TEXT,
  entry_price     NUMERIC,
  exit_price      NUMERIC,
  stop_loss       NUMERIC,
  profit_target   NUMERIC,
  planned_entry   NUMERIC,
  planned_stop    NUMERIC,
  quantity        NUMERIC,
  r_result        NUMERIC,
  mae             NUMERIC,
  mfe             NUMERIC,
  mindset         TEXT,
  emotion_pre     JSONB,
  confidence      INTEGER,
  rationale       TEXT,
  post_notes      TEXT,
  chart_url       TEXT,
  psychology_tags JSONB,
  rule_breaks     JSONB,
  entered_at      TIMESTAMPTZ NOT NULL,
  exited_at       TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (id, entered_at)     -- composite PK required by native partitioning
) PARTITION BY RANGE (entered_at);

-- Partitioning managed by pg_partman (extensions schema, not partman)
SELECT extensions.create_parent(
  p_parent_table   => 'public.trades',
  p_control        => 'entered_at',
  p_interval       => '1 month',   -- pg_partman 5.3.1 requires this literal, not 'monthly'
  p_premake        => 4
);

-- Maintenance (creates future partitions on schedule)
CALL extensions.run_maintenance_proc();
-- Scheduled via pg_cron (cron schema, even though the extension itself lives in pg_catalog)
-- e.g. SELECT cron.schedule('partman-maintenance', '0 3 * * *', $$CALL extensions.run_maintenance_proc()$$);

CREATE INDEX ON trades (user_id, entered_at DESC);
```

**Composite key impact:** any table that has a foreign key into `trades` (e.g. `alerts`, `trade_embeddings` — see roadmap below) must carry `entered_at` alongside the trade `id`, since the primary key on `trades` is now `(id, entered_at)` rather than just `id`. Flagged as a downstream item on: T-025, T-032, T-033, T-038, T-065, Milestone 2, and the Risk Register.

Seven monthly partitions plus a default partition are live and verified as of Sprint 0.

`trade_embeddings`, `agent_memory`, and `broker_connections` tables are **not yet migrated** — they belong to the Phase 2 architecture in the Roadmap section.

---

## Environment Variables

| Variable | Used for | Where to get it |
|---|---|---|
| `DATABASE_URL` | Supabase Postgres connection (pooler format) | Supabase → Project Settings → Database |
| `REDIS_URL` | Session blocklist, caching | Upstash → your Redis database |
| `JWT_SECRET` | Signing auth tokens | Generate locally (e.g. `openssl rand -hex 32`) |
| `ANTHROPIC_API_KEY` | AI agent calls (Sprint 4+) | console.anthropic.com |

Keep `.env.example` in sync whenever a new variable is introduced — this is part of the Definition of Done for every task per the plan (§8).

---

## How Pages Are Connected

| From page | Links to |
|-----------|----------|
| `index.html` (landing) | → `login.html` (Get Started / Sign In) |
| `login.html` | → `dashboard.html` (on successful auth) |
| All app pages | ← `sidebar.js` injects the sidebar with correct active state |
| All app pages | → `login.html` (Sign Out button calls `CT.auth.logout()`) |
| Settings | → `login.html` (Sign Out in settings nav) |

**Auth flow:** `CT.auth.requireAuth()` is called at the bottom of every protected page. If there's no session in `localStorage`, it redirects to `login.html`. The mock login currently accepts any email + password — this is replaced by real JWT auth in Sprint 1.

---

## Theme System

- Theme tokens live in `css/theme.css` as CSS custom properties on `[data-theme="dark"]` and `[data-theme="light"]`
- Theme is set on `<html data-theme="...">` and persisted to `localStorage`
- All theme toggles use `data-action="toggle-theme"` — wired automatically by `app.js`
- Charts re-render on theme switch via `CT_Charts.refreshAll()`

---

## Replacing Mock Data with Real API

In `js/app.js`, the `TRADES_BY_DATE` object and `CT.auth` methods are clearly marked for replacement, sprint by sprint per the plan:

```js
// Replace CT.auth.login() with:
const res = await fetch('/api/auth/login', {
  method: 'POST',
  body: JSON.stringify({ email, password }),
  headers: { 'Content-Type': 'application/json' }
});
const { token, user } = await res.json();
localStorage.setItem('ct-session', JSON.stringify({ token, ...user }));

// Replace TRADES_BY_DATE with:
const res = await fetch('/api/trades?month=2026-07', {
  headers: { Authorization: `Bearer ${CT.auth.getUser().token}` }
});
const trades = await res.json();
```

---

## Documentation & Changelog

- **[CHANGELOG.md](./CHANGELOG.md)** — Keep a Changelog format, updated at every Sprint Review. This is the source of truth for what's actually done; if it's not in there, treat it as not shipped yet.
- **ADRs** — `docs/adr/` (to be initialized in Sprint 0 per plan §7.2–7.4). Planned: ADR-001 (FastAPI), ADR-002 (partitioning strategy — update from the original "TimescaleDB" framing to pg_partman), ADR-003 (JWT auth), ADR-004 (LangGraph, Phase 2), ADR-005 (Supabase Storage), ADR-006 (Tactical HUD design system, Sprint 6).
- **Full plan** — `CognitionTrade_Phase1_Agile_Plan_FINAL.docx`, sprints 0–6, tasks, user stories, velocity tracking, risk register.

---

## Team

| Role | Who |
|---|---|
| Product Owner | You |
| Scrum Master | AI (Claude) |
| Developer | You + Claude |

---

---

# Full Product Architecture (Roadmap — Phase 2+)

**Everything below this line is the long-range design blueprint, not the current implementation.** Phase 1 explicitly excludes the Researcher agent, the Performance agent beyond basic R-math, Registrar/full multi-agent synthesis, broker integrations, Celery scheduled tasks, Mem0, and pgvector semantic search in chat (see plan §1.2). Treat this section as a reference for where the project is headed, not as setup instructions.

## Overview

The backend, at full scope, powers 5 concerns:

1. **Auth** — JWT sessions, OAuth
2. **Trade CRUD** — storing, retrieving, updating trades
3. **AI Agents** — 5 LangGraph nodes orchestrated as a multi-agent system
4. **Broker Integrations** — auto-importing trades from IBKR, Schwab, etc.
5. **Reports & Alerts** — scheduled weekly reports, real-time tilt notifications

## Tech Stack (Full Vision)

```
LangGraph          → multi-agent orchestration (graph-based state machine)
LangChain          → LLM wrapper, tool use, memory
Anthropic Claude   → primary LLM for agents
OpenAI GPT-4o      → chart vision / multimodal analysis (or use Claude's vision)
Mem0               → long-term memory layer (compresses old sessions)
LangSmith          → agent observability, tracing, debugging

Supabase           → PostgreSQL hosting + Row-Level Security + Auth helpers
Upstash Redis      → serverless Redis for queues and cache
Railway            → backend deployment
Vercel             → frontend deployment (static HTML/CSS/JS)
Cloudflare R2 / Supabase Storage → chart image uploads
```

## Future Schema Additions

```sql
-- Trade Embeddings (pgvector — semantic search, Phase 2)
CREATE TABLE trade_embeddings (
  trade_id    UUID NOT NULL,
  entered_at  TIMESTAMPTZ NOT NULL,   -- required alongside trade_id (see composite PK note above)
  embedding   VECTOR(1536),
  summary     TEXT,
  FOREIGN KEY (trade_id, entered_at) REFERENCES trades(id, entered_at) ON DELETE CASCADE
);
CREATE INDEX ON trade_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Agent Memory (long-term compressed memory per user)
CREATE TABLE agent_memory (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  memory_type TEXT,
  content     TEXT,
  embedding   VECTOR(1536),
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Broker Connections
CREATE TABLE broker_connections (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
  broker       TEXT NOT NULL,
  credentials  JSONB,
  last_sync    TIMESTAMPTZ,
  is_active    BOOLEAN DEFAULT TRUE,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Alert Log
CREATE TABLE alerts (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  entered_at  TIMESTAMPTZ,            -- required if referencing a specific trade (composite PK)
  alert_type  TEXT NOT NULL,
  payload     JSONB,
  is_read     BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

## Auth (Phase 1, real code lands Sprint 1)

```python
# app/api/auth.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt, bcrypt
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth")
SECRET = os.getenv("JWT_SECRET")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@router.post("/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode({
        "sub": str(user.id),
        "exp": datetime.utcnow() + timedelta(days=30)
    }, SECRET, algorithm="HS256")
    return {"token": token, "user": {"id": user.id, "name": user.name, "email": user.email, "plan": user.plan}}

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    redis.setex(f"blocklist:{token}", 60 * 60 * 24 * 30, "1")
    return {"ok": True}

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(status_code=401)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
```

**OAuth (Google/GitHub):** use `authlib` with FastAPI; on callback, upsert the user and return a JWT as above. (Explicitly de-scoped from Phase 1 per the Risk Register — auth is non-negotiable, OAuth can move to Phase 2 if Sprint 1 runs long.)

## Trade API (Phase 1, real code lands Sprint 2)

```python
# app/api/trades.py

@router.get("/trades")
async def get_trades(
    month: str = None, symbol: str = None, strategy: str = None,
    limit: int = 100, offset: int = 0,
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    query = db.query(Trade).filter(Trade.user_id == user.id)
    if month:
        year, m = month.split("-")
        query = query.filter(
            extract('year', Trade.entered_at) == int(year),
            extract('month', Trade.entered_at) == int(m)
        )
    return query.order_by(Trade.entered_at.desc()).offset(offset).limit(limit).all()

@router.post("/trades")
async def create_trade(trade: TradeCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = (trade.exit_price - trade.entry_price) / (trade.entry_price - trade.stop_loss)
    db_trade = Trade(**trade.dict(), user_id=user.id, r_result=r)
    db.add(db_trade)
    db.commit()
    background_tasks.add_task(run_post_trade_agents, db_trade.id, user.id)
    return db_trade

@router.get("/trades/calendar")
async def get_calendar_summary(
    year: int, month: int,
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    trades = db.query(Trade).filter(
        Trade.user_id == user.id,
        extract('year', Trade.entered_at) == year,
        extract('month', Trade.entered_at) == month
    ).all()
    by_date = {}
    for t in trades:
        d = t.entered_at.date().isoformat()
        by_date.setdefault(d, {"trades": [], "total_r": 0, "wins": 0, "losses": 0})
        by_date[d]["trades"].append(t)
        by_date[d]["total_r"] += t.r_result or 0
        by_date[d]["wins" if (t.r_result or 0) > 0 else "losses"] += 1
    return by_date
```

## AI Agent System (LangGraph) — Phase 1 delivers Journal Analyst (Sprint 4) and Strategy Coach (Sprint 5) only

Full vision architecture (Performance, Researcher, and Registrar nodes are Phase 2):

```
                    ┌─────────────────────────────────────┐
                    │         SUPERVISOR NODE             │
                    │      (Strategy Coach / Registrar)   │
                    └──────┬──────┬──────┬──────┬────────┘
                           │      │      │      │
               ┌───────────┘  ┌───┘  ┌───┘  ┌──┘
               ▼              ▼      ▼      ▼
        ┌────────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐
        │  Journal   │ │ Perform- │ │Research│ │ Strategy │
        │  Analyst   │ │  ance    │ │  er    │ │  Coach   │
        │(chart+NLP) │ │(R-math)  │ │(news)  │ │(gap+tilt)│
        └────────────┘ └──────────┘ └────────┘ └──────────┘
```

```python
# app/agents/state.py
from typing import TypedDict, List, Optional

class TradeJournalState(TypedDict):
    user_id: str
    trade_id: str
    trade_data: dict

    chart_analysis: Optional[dict]
    psychology_tags: List[str]
    rationale_verified: bool

    r_multiple: float
    expectancy: float
    win_rate: float
    mae_mfe: dict

    market_context: dict
    relevant_news: List[dict]
    sentiment_score: float

    execution_gap: dict
    tilt_detected: bool
    tilt_type: Optional[str]
    recommendations: List[str]

    summary: str
    alerts: List[dict]
    messages: List[dict]
```

```python
# app/agents/graph.py
from langgraph.graph import StateGraph, END
from .nodes import journal_analyst, performance_agent, researcher, strategy_coach, registrar

def build_agent_graph():
    graph = StateGraph(TradeJournalState)
    graph.add_node("journal_analyst",  journal_analyst)
    graph.add_node("performance",      performance_agent)
    graph.add_node("researcher",       researcher)
    graph.add_node("strategy_coach",   strategy_coach)
    graph.add_node("registrar",        registrar)
    graph.set_entry_point("journal_analyst")
    graph.add_edge("journal_analyst", "performance")
    graph.add_edge("journal_analyst", "researcher")
    graph.add_edge("performance",  "strategy_coach")
    graph.add_edge("researcher",   "strategy_coach")
    graph.add_edge("strategy_coach", "registrar")
    graph.add_edge("registrar", END)
    return graph.compile()
```

Node implementations (journal analyst vision + psych tagging, performance R-math, researcher news/sentiment, strategy coach gap/tilt, registrar synthesis) follow the same structure as previously drafted — see git history for the full node code, or ask to have it regenerated against the current schema when Sprint 4/5 begins.

## Natural Language Q&A (AI Coach Chat) — Phase 2

```python
# app/api/agents.py
@router.post("/agents/chat")
async def chat(message: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query_embedding = await get_embedding(message)
    similar_trades  = await vector_search(query_embedding, user.id, limit=10)
    memories        = await get_agent_memories(user.id)
    stats = await compute_user_stats(user.id)

    context = f"""
        You are the AI Coach for trader {user.name}.
        Win rate: {stats['win_rate']}%, Expectancy: {stats['expectancy']}R,
        Total trades: {stats['total_trades']}, Top strategy: {stats['top_strategy']}
        Relevant trade history: {format_trades_for_context(similar_trades)}
        Long-term behavioral memories: {memories}
        Answer concisely and specifically, referencing actual numbers. Max 3 sentences.
    """
    client = anthropic.Anthropic()
    with client.messages.stream(
        model="claude-sonnet-4-6", max_tokens=400, system=context,
        messages=[{"role": "user", "content": message}]
    ) as stream:
        async def event_stream():
            for text in stream.text_stream:
                yield f"data: {json.dumps({'token': text})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")
```

## Broker Integrations — Phase 2, out of Phase 1 scope

```python
# app/services/brokers/ibkr.py
import ib_insync

class IBKRBroker:
    async def fetch_trades(self, account_id: str, since: datetime) -> List[dict]:
        ib = ib_insync.IB()
        await ib.connectAsync('127.0.0.1', 7497, clientId=1)
        trades = await ib.reqExecutionsAsync()
        return [self.normalize_trade(t) for t in trades if t.time >= since]

    def normalize_trade(self, raw) -> dict:
        return {
            "symbol": raw.contract.symbol,
            "direction": "long" if raw.execution.side == "BOT" else "short",
            "entry_price": raw.execution.price,
            "quantity": raw.execution.shares,
            "entered_at": raw.time,
        }
```

```python
# app/services/brokers/schwab.py — OAuth2 + REST
class SchwabBroker:
    BASE_URL = "https://api.schwabapi.com/trader/v1"

    async def fetch_trades(self, access_token: str, since: datetime) -> List[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/accounts/{{accountId}}/orders",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"fromEnteredTime": since.isoformat(), "status": "FILLED"}
            )
            return [self.normalize_trade(o) for o in resp.json()]
```

## Scheduled Tasks (Celery + Redis) — Phase 2, out of Phase 1 scope

```python
# app/tasks.py
from celery import Celery
from celery.schedules import crontab

celery = Celery("cognitiontrade", broker=os.getenv("REDIS_URL"))

@celery.task
def sync_broker_trades(user_id: str, broker: str):
    """Pulls new trades from broker."""

@celery.task
def generate_weekly_report(user_id: str):
    """Runs every Sunday 6pm. Narrative weekly report via Registrar agent."""

@celery.task
def send_premarket_briefing(user_id: str):
    """Runs every trading day at 8:15 AM ET. Researcher agent + push notification."""

celery.conf.beat_schedule = {
    "weekly-reports": {"task": "app.tasks.generate_weekly_report", "schedule": crontab(hour=18, minute=0, day_of_week="sunday")},
    "premarket-briefing": {"task": "app.tasks.send_premarket_briefing", "schedule": crontab(hour=13, minute=15)},
}
```

## Full API Surface (Target, end of Phase 2)

```
POST   /api/auth/login                → returns JWT
POST   /api/auth/logout               → invalidates token
POST   /api/auth/register             → creates account
GET    /api/auth/me                   → current user

GET    /api/trades                    → list trades (with filters)
POST   /api/trades                    → create trade + trigger agents
GET    /api/trades/:id                → single trade with agent analysis
PUT    /api/trades/:id                → update trade
DELETE /api/trades/:id                → delete trade
GET    /api/trades/calendar           → per-day summary for calendar view
GET    /api/trades/stats              → aggregate stats

POST   /api/agents/chat               → streaming AI Coach Q&A          (Phase 2)
POST   /api/agents/analyze            → run full agent pipeline on a trade
GET    /api/agents/alerts             → unread tilt/gap/limit alerts

GET    /api/brokers                   → list connected brokers          (Phase 2)
POST   /api/brokers/connect           → connect a broker (starts OAuth) (Phase 2)
DELETE /api/brokers/:id               → disconnect broker               (Phase 2)
POST   /api/brokers/:id/sync          → manual sync                     (Phase 2)

GET    /api/settings                  → get user settings
PUT    /api/settings                  → update settings
POST   /api/settings/upload-chart     → upload chart, returns URL

GET    /api/reports/weekly            → latest weekly report            (Phase 2)
GET    /api/reports/monthly           → monthly report                 (Phase 2)
```

## Deployment Checklist (Target, Sprint 5)

```bash
cp .env.example .env
# Fill in: DATABASE_URL, REDIS_URL, ANTHROPIC_API_KEY, JWT_SECRET, etc.

alembic upgrade head

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Deploy pages/ folder to Vercel
# Update js/app.js API base URL from '' to the Railway production URL
```

## Key Dependencies (Full Vision — not all installed yet)

```txt
fastapi
uvicorn[standard]
sqlalchemy
alembic
psycopg2-binary
pgvector          # Phase 2
redis
celery            # Phase 2

anthropic
langchain         # Phase 2 (multi-agent orchestration beyond Journal Analyst/Strategy Coach)
langgraph
langsmith         # Phase 2
mem0ai            # Phase 2
openai            # Phase 2, chart vision fallback

python-jose[cryptography]
bcrypt
python-multipart
httpx
boto3             # Phase 2, if S3 is used instead of Supabase Storage
ib_insync         # Phase 2, IBKR broker
```

## Security Notes

- **Never** store raw API keys in the DB — encrypt broker credentials with AES-256 before storage (Phase 2)
- Use **Row-Level Security (RLS)** in Supabase so users can only access their own rows
- Rate-limit the `/api/agents/chat` endpoint once it exists — LLM calls are expensive
- Validate all file uploads (chart images) for type and size before passing to a vision model
- Use **HTTPS only** in production — set `secure=True` on all cookies