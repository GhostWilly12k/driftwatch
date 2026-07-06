# CognitionTrade — AI Trading Journal

A full-stack AI-powered trading journal with 5 specialized agents, calendar trade history, execution gap analysis, tilt detection, and a personalized market briefing.

---

## Project Structure

```
cognitiontrade/
├── pages/                  # All HTML pages
│   ├── index.html          # Landing / marketing page
│   ├── login.html          # Sign in page
│   ├── dashboard.html      # Main app dashboard
│   ├── journal.html        # Log a trade
│   ├── trades.html         # Trade history calendar
│   ├── performance.html    # Performance analytics
│   ├── strategy.html       # Execution review / gap analysis
│   ├── researcher.html     # Market briefing
│   ├── chat.html           # AI Coach chat
│   └── settings.html       # Settings (profile, appearance, etc.)
│
├── css/
│   ├── theme.css           # CSS variables (dark/light tokens) + base reset
│   ├── components.css      # Buttons, cards, tables, forms, calendar, chat, etc.
│   ├── shell.css           # Sidebar, topbar, layout
│   └── landing.css         # Landing page styles
│
├── js/
│   ├── app.js              # Core: theme toggle, auth, shared data (TRADES_BY_DATE)
│   ├── sidebar.js          # Injects shared sidebar HTML on every page
│   ├── charts.js           # All Chart.js instances (equity, monthly, MAE/MFE, sentiment)
│   └── calendar.js         # Calendar render, month navigation, day drill-down
│
├── assets/                 # Icons, logo, images (add as needed)
└── README.md
```

---

## Getting Started (Frontend only)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/cognitiontrade.git
cd cognitiontrade

# No build step needed — open directly in browser
open pages/index.html

# Or serve with any static server:
npx serve pages/
# or
python3 -m http.server 3000 --directory pages/

# Create .venv + install dependencies
python3 -m venv .venv
pip install -r requirements.txt
```

**All pages link to `css/` and `js/` with relative paths** — they work from the `pages/` directory as the root.

---

## How Pages Are Connected

| From page | Links to |
|-----------|----------|
| `index.html` (landing) | → `login.html` (Get Started / Sign In) |
| `login.html` | → `dashboard.html` (on successful auth) |
| All app pages | ← `sidebar.js` injects the sidebar with correct active state |
| All app pages | → `login.html` (Sign Out button calls `CT.auth.logout()`) |
| Settings | → `login.html` (Sign Out in settings nav) |

**Auth flow:** `CT.auth.requireAuth()` is called at the bottom of every protected page. If there's no session in `localStorage`, it redirects to `login.html`. The mock login accepts any email + password.

---

## Theme System

- Theme tokens live in `css/theme.css` as CSS custom properties on `[data-theme="dark"]` and `[data-theme="light"]`
- Theme is set on `<html data-theme="...">` and persisted to `localStorage`
- All theme toggles use `data-action="toggle-theme"` — wired automatically by `app.js`
- Charts re-render on theme switch via `CT_Charts.refreshAll()`

---

## Replacing Mock Data with Real API

In `js/app.js`, the `TRADES_BY_DATE` object and `CT.auth` methods are clearly marked for replacement:

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
const res = await fetch('/api/trades?month=2026-03', {
  headers: { Authorization: `Bearer ${CT.auth.getUser().token}` }
});
const trades = await res.json();
```

---

## Recommended Tech Stack for Backend

See **Backend Implementation** section below.

---

---

# Backend Implementation — Full Blueprint

## Overview

The backend powers 5 main concerns:

1. **Auth** — JWT sessions, OAuth
2. **Trade CRUD** — storing, retrieving, updating trades
3. **AI Agents** — 5 LangGraph nodes orchestrated as a multi-agent system
4. **Broker Integrations** — auto-importing trades from IBKR, Schwab, etc.
5. **Reports & Alerts** — scheduled weekly reports, real-time tilt notifications

---

## Phase 1 — Tech Stack Selection

### Core Framework
**FastAPI (Python)** — async, fast, auto-generates OpenAPI docs, excellent AI/ML ecosystem.

```
backend/
├── app/
│   ├── main.py             # FastAPI app entry point
│   ├── api/
│   │   ├── auth.py         # /api/auth/* routes
│   │   ├── trades.py       # /api/trades/* routes
│   │   ├── agents.py       # /api/agents/* routes (chat, analysis)
│   │   ├── brokers.py      # /api/brokers/* routes
│   │   └── settings.py     # /api/settings/* routes
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── agents/             # LangGraph agent nodes
│   ├── services/           # Business logic
│   └── db.py               # Database connection
├── alembic/                # Database migrations
├── requirements.txt
└── .env
```

### Database

```
PostgreSQL 17
  + TimescaleDB extension   → time-series trade data, fast date-range queries
  + pgvector extension      → vector embeddings for semantic trade search

Redis 7                     → session cache, real-time alert queues, agent state
```

### AI / Agents

```
LangGraph          → multi-agent orchestration (graph-based state machine)
LangChain          → LLM wrapper, tool use, memory
Anthropic Claude   → primary LLM (claude-sonnet-4-6 for agents)
OpenAI GPT-4o      → chart vision / multimodal analysis (or use Claude's vision)
Mem0               → long-term memory layer (compresses old sessions)
LangSmith          → agent observability, tracing, debugging
```

### Infrastructure

```
Supabase           → PostgreSQL hosting + Row-Level Security + Auth helpers
Upstash Redis      → serverless Redis for queues and cache
Railway / Render   → backend deployment
Vercel             → frontend deployment (static HTML/CSS/JS)
AWS S3 / Cloudflare R2  → chart image uploads
```

---

## Phase 2 — Database Schema

### Core Tables

```sql
-- Users
CREATE TABLE users (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email        TEXT UNIQUE NOT NULL,
  name         TEXT,
  plan         TEXT DEFAULT 'starter',  -- starter | pro | team
  avatar_url   TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- User Settings
CREATE TABLE user_settings (
  user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
  account_size    NUMERIC DEFAULT 10000,
  risk_per_trade  NUMERIC DEFAULT 1.0,    -- percentage
  daily_max_loss  NUMERIC DEFAULT 200,
  weekly_max_loss NUMERIC DEFAULT 600,
  theme           TEXT DEFAULT 'dark',
  agent_config    JSONB DEFAULT '{}',     -- which agents are enabled
  notif_config    JSONB DEFAULT '{}',     -- notification preferences
  PRIMARY KEY (user_id)
);

-- Trades (TimescaleDB hypertable — partitioned by entered_at)
CREATE TABLE trades (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
  symbol          TEXT NOT NULL,
  direction       TEXT NOT NULL,          -- long | short
  strategy        TEXT,
  entry_price     NUMERIC,
  exit_price      NUMERIC,
  stop_loss       NUMERIC,
  profit_target   NUMERIC,
  planned_entry   NUMERIC,
  planned_stop    NUMERIC,
  quantity        NUMERIC,
  r_result        NUMERIC,                -- calculated R-multiple
  mae             NUMERIC,               -- max adverse excursion
  mfe             NUMERIC,               -- max favorable excursion
  mindset         TEXT,                  -- Focused | Impulsive | etc.
  emotion_pre     JSONB,                 -- array of emotion tags
  confidence      INTEGER,              -- 1-10
  rationale       TEXT,                 -- why they took the trade
  post_notes      TEXT,
  chart_url       TEXT,                 -- S3 key for uploaded chart
  psychology_tags JSONB,               -- AI-generated tags
  rule_breaks     JSONB,               -- rule violations detected
  entered_at      TIMESTAMPTZ NOT NULL,
  exited_at       TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Make trades a TimescaleDB hypertable
SELECT create_hypertable('trades', 'entered_at');

-- Index for fast user + date queries
CREATE INDEX ON trades (user_id, entered_at DESC);

-- Trade Embeddings (pgvector — for semantic search)
CREATE TABLE trade_embeddings (
  trade_id    UUID REFERENCES trades(id) ON DELETE CASCADE PRIMARY KEY,
  embedding   VECTOR(1536),             -- OpenAI/Claude embedding
  summary     TEXT                      -- human-readable summary for retrieval
);
CREATE INDEX ON trade_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Agent Memory (long-term compressed memory per user)
CREATE TABLE agent_memory (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  memory_type TEXT,                     -- behavioral | strategy | preference
  content     TEXT,
  embedding   VECTOR(1536),
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Broker Connections
CREATE TABLE broker_connections (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
  broker       TEXT NOT NULL,           -- ibkr | schwab | tdameritrade
  credentials  JSONB,                  -- encrypted API keys/tokens
  last_sync    TIMESTAMPTZ,
  is_active    BOOLEAN DEFAULT TRUE,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Alert Log
CREATE TABLE alerts (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  alert_type  TEXT NOT NULL,           -- tilt | daily_limit | gap | briefing
  payload     JSONB,
  is_read     BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Phase 3 — Auth Implementation

### JWT + OAuth

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
    # Add token to Redis blocklist
    redis.setex(f"blocklist:{token}", 60 * 60 * 24 * 30, "1")
    return {"ok": True}

# Dependency — use on all protected routes
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

**For OAuth (Google/GitHub):** Use `authlib` with FastAPI. On callback, upsert the user in the DB and return a JWT as above.

---

## Phase 4 — Trade API

```python
# app/api/trades.py

@router.get("/trades")
async def get_trades(
    month: str = None,          # "2026-03" — used by calendar
    symbol: str = None,
    strategy: str = None,
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    # 1. Calculate R-multiple
    r = (trade.exit_price - trade.entry_price) / (trade.entry_price - trade.stop_loss)
    
    # 2. Save trade
    db_trade = Trade(**trade.dict(), user_id=user.id, r_result=r)
    db.add(db_trade)
    db.commit()
    
    # 3. Trigger agents asynchronously (Celery task or background task)
    background_tasks.add_task(run_post_trade_agents, db_trade.id, user.id)
    
    return db_trade


@router.get("/trades/calendar")
async def get_calendar_summary(
    year: int, month: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns per-day trade summary for the calendar view."""
    trades = db.query(Trade).filter(
        Trade.user_id == user.id,
        extract('year', Trade.entered_at) == year,
        extract('month', Trade.entered_at) == month
    ).all()
    
    # Group by date
    by_date = {}
    for t in trades:
        d = t.entered_at.date().isoformat()
        if d not in by_date:
            by_date[d] = {"trades": [], "total_r": 0, "wins": 0, "losses": 0}
        by_date[d]["trades"].append(t)
        by_date[d]["total_r"] += t.r_result or 0
        if (t.r_result or 0) > 0:
            by_date[d]["wins"] += 1
        else:
            by_date[d]["losses"] += 1
    
    return by_date
```

---

## Phase 5 — AI Agent System (LangGraph)

This is the core of CognitionTrade. Each agent is a LangGraph node.

### Agent Architecture

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

### State Definition

```python
# app/agents/state.py
from typing import TypedDict, List, Optional
from langgraph.graph import MessagesState

class TradeJournalState(TypedDict):
    # Input
    user_id: str
    trade_id: str
    trade_data: dict          # raw trade object

    # Journal Analyst outputs
    chart_analysis: Optional[dict]   # extracted from chart image
    psychology_tags: List[str]
    rationale_verified: bool

    # Performance Agent outputs
    r_multiple: float
    expectancy: float
    win_rate: float
    mae_mfe: dict

    # Researcher outputs
    market_context: dict
    relevant_news: List[dict]
    sentiment_score: float

    # Strategy Coach outputs
    execution_gap: dict
    tilt_detected: bool
    tilt_type: Optional[str]   # revenge | hesitation | overconfidence
    recommendations: List[str]

    # Final output
    summary: str
    alerts: List[dict]
    messages: List[dict]       # LangGraph message history
```

### Graph Definition

```python
# app/agents/graph.py
from langgraph.graph import StateGraph, END
from .nodes import journal_analyst, performance_agent, researcher, strategy_coach, registrar

def build_agent_graph():
    graph = StateGraph(TradeJournalState)

    # Add nodes
    graph.add_node("journal_analyst",  journal_analyst)
    graph.add_node("performance",      performance_agent)
    graph.add_node("researcher",       researcher)
    graph.add_node("strategy_coach",   strategy_coach)
    graph.add_node("registrar",        registrar)

    # Entry point — always start with journal analyst
    graph.set_entry_point("journal_analyst")

    # After journal analyst, run performance and researcher in parallel
    graph.add_edge("journal_analyst", "performance")
    graph.add_edge("journal_analyst", "researcher")

    # After both finish, strategy coach synthesizes
    graph.add_edge("performance",  "strategy_coach")
    graph.add_edge("researcher",   "strategy_coach")

    # Registrar compiles final report
    graph.add_edge("strategy_coach", "registrar")
    graph.add_edge("registrar", END)

    return graph.compile()
```

### Agent Node Implementations

```python
# app/agents/nodes.py

# ── JOURNAL ANALYST ──
async def journal_analyst(state: TradeJournalState) -> TradeJournalState:
    """Analyzes chart image + rationale text. Tags psychology."""
    
    client = anthropic.Anthropic()
    
    # 1. If chart image exists, use vision to extract levels
    chart_analysis = None
    if state["trade_data"].get("chart_url"):
        image_b64 = await fetch_image_b64(state["trade_data"]["chart_url"])
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_b64}},
                    {"type": "text", "text": f"""
                        Analyze this trading chart. Extract:
                        1. Price levels visible (support, resistance, entry zone)
                        2. Chart patterns present (bull flag, head & shoulders, etc.)
                        3. Indicators visible and their readings
                        4. Does this match the trader's stated rationale: "{state['trade_data']['rationale']}"?
                        
                        Respond as JSON: {{
                          "price_levels": [...],
                          "patterns": [...],
                          "indicators": [...],
                          "rationale_match": true/false,
                          "rationale_score": 0-100,
                          "notes": "..."
                        }}
                    """}
                ]
            }]
        )
        chart_analysis = json.loads(response.content[0].text)

    # 2. NLP on rationale text — extract psychology tags
    psych_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": f"""
            Analyze the trader's pre-trade emotion tags and rationale.
            Emotions: {state['trade_data']['emotion_pre']}
            Rationale: "{state['trade_data']['rationale']}"
            
            Return JSON array of psychology tags from: 
            [Focused, Impulsive, Revenge, FOMO, Hesitant, Overconfident, In the Zone, Anxious, Calm]
            Example: ["FOMO", "Impulsive"]
        """}]
    )
    psychology_tags = json.loads(psych_response.content[0].text)

    return {
        **state,
        "chart_analysis": chart_analysis,
        "psychology_tags": psychology_tags,
        "rationale_verified": chart_analysis.get("rationale_match", True) if chart_analysis else True
    }


# ── PERFORMANCE AGENT ──
async def performance_agent(state: TradeJournalState) -> TradeJournalState:
    """Calculates R-multiple, expectancy, MAE/MFE. Pure math — no LLM needed."""
    
    t = state["trade_data"]
    entry  = float(t["entry_price"])
    exit_p = float(t["exit_price"])
    stop   = float(t["stop_loss"])

    # R-multiple formula
    r = (exit_p - entry) / abs(entry - stop) if entry != stop else 0

    # Fetch last 50 trades from DB for expectancy
    recent_trades = await get_recent_trades(state["user_id"], limit=50)
    wins   = [t for t in recent_trades if t.r_result > 0]
    losses = [t for t in recent_trades if t.r_result <= 0]

    win_rate    = len(wins) / len(recent_trades) if recent_trades else 0
    avg_win_r   = sum(t.r_result for t in wins)   / len(wins)   if wins   else 0
    avg_loss_r  = abs(sum(t.r_result for t in losses) / len(losses)) if losses else 0
    expectancy  = (win_rate * avg_win_r) - ((1 - win_rate) * avg_loss_r)

    return {
        **state,
        "r_multiple": round(r, 2),
        "expectancy": round(expectancy, 3),
        "win_rate": round(win_rate, 3),
        "mae_mfe": {
            "mae": float(t.get("mae", 0)),
            "mfe": float(t.get("mfe", 0))
        }
    }


# ── RESEARCHER ──
async def researcher(state: TradeJournalState) -> TradeJournalState:
    """Fetches market news relevant to the traded symbol."""
    
    symbol = state["trade_data"]["symbol"]
    
    # Fetch from news API (Benzinga / NewsAPI / Alpha Vantage)
    news = await fetch_news(symbol, hours_back=24)
    
    # Score sentiment with Claude
    if news:
        client = anthropic.Anthropic()
        sentiment_resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": f"""
                Rate the overall market sentiment from these headlines for {symbol}.
                Headlines: {[n['title'] for n in news[:5]]}
                Return JSON: {{"score": -1.0 to 1.0, "label": "bullish/bearish/neutral", "key_event": "..."}}
            """}]
        )
        sentiment = json.loads(sentiment_resp.content[0].text)
    else:
        sentiment = {"score": 0, "label": "neutral", "key_event": None}

    return {
        **state,
        "market_context": sentiment,
        "relevant_news": news[:3],
        "sentiment_score": sentiment["score"]
    }


# ── STRATEGY COACH ──
async def strategy_coach(state: TradeJournalState) -> TradeJournalState:
    """Calculates execution gap. Detects tilt patterns."""
    
    t = state["trade_data"]
    
    # Execution gap calculation
    entry_gap   = abs(float(t["entry_price"]) - float(t.get("planned_entry", t["entry_price"])))
    stop_gap    = abs(float(t["stop_loss"])   - float(t.get("planned_stop", t["stop_loss"])))
    planned_r   = abs(float(t.get("planned_entry", t["entry_price"])) - float(t.get("planned_stop", t["stop_loss"])))
    
    execution_gap = {
        "entry_slippage_r": round(entry_gap / planned_r, 3) if planned_r else 0,
        "stop_moved_r":     round(stop_gap  / planned_r, 3) if planned_r else 0,
    }

    # Tilt detection — check recent trade pattern
    recent = await get_recent_trades(state["user_id"], limit=5)
    tilt_detected = False
    tilt_type = None

    if recent:
        last_trade = recent[0]
        # Revenge trading: size increased >20% after a losing trade
        if last_trade.r_result < 0 and float(t.get("quantity", 0)) > float(last_trade.quantity or 0) * 1.2:
            tilt_detected = True
            tilt_type = "revenge"
        # Hesitation: entry more than 0.5R from planned
        elif execution_gap["entry_slippage_r"] > 0.5:
            tilt_detected = True
            tilt_type = "hesitation"

    recommendations = []
    if tilt_detected:
        if tilt_type == "revenge":
            recommendations.append("Your position size increased significantly after a loss. Consider a 15-minute break before your next trade.")
        elif tilt_type == "hesitation":
            recommendations.append("Your entry was 0.5R+ from your planned price. Review this setup's historical win rate to build confidence.")

    return {
        **state,
        "execution_gap": execution_gap,
        "tilt_detected": tilt_detected,
        "tilt_type": tilt_type,
        "recommendations": recommendations
    }


# ── REGISTRAR (Supervisor) ──
async def registrar(state: TradeJournalState) -> TradeJournalState:
    """Synthesizes all agent outputs into a final summary. Handles Q&A."""
    
    client = anthropic.Anthropic()
    
    summary_prompt = f"""
        You are the AI Coach for a trader. Synthesize this trade analysis into a 2-3 sentence 
        coaching summary. Be specific, data-driven, and actionable.
        
        Trade: {state['trade_data']['symbol']} {state['trade_data']['direction']}
        R Result: {state['r_multiple']}R
        Psychology: {state['psychology_tags']}
        Tilt detected: {state['tilt_detected']} ({state['tilt_type']})
        Execution gap: {state['execution_gap']}
        Market context: {state['market_context']}
        Chart verified: {state['rationale_verified']}
        Recommendations: {state['recommendations']}
    """
    
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": summary_prompt}]
    )

    # Build alerts if needed
    alerts = []
    if state["tilt_detected"]:
        alerts.append({"type": "tilt", "severity": "high", "message": f"Tilt pattern detected: {state['tilt_type']}"})

    return {**state, "summary": resp.content[0].text, "alerts": alerts}
```

---

## Phase 6 — Natural Language Q&A (AI Coach Chat)

```python
# app/api/agents.py

@router.post("/agents/chat")
async def chat(
    message: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Natural language Q&A over the user's full trade history."""
    
    # 1. Retrieve relevant memories + similar trades via pgvector
    query_embedding = await get_embedding(message)
    similar_trades  = await vector_search(query_embedding, user.id, limit=10)
    memories        = await get_agent_memories(user.id)
    
    # 2. Compute key stats for context
    stats = await compute_user_stats(user.id)  # win rate, expectancy, etc.
    
    # 3. Build context-rich prompt
    context = f"""
        You are the AI Coach for trader {user.name}. 
        
        Their trading stats (last 90 days):
        - Win rate: {stats['win_rate']}%
        - Expectancy: {stats['expectancy']}R
        - Total trades: {stats['total_trades']}
        - Top strategy: {stats['top_strategy']}
        - Worst time window: {stats['worst_window']}
        - Primary emotional pattern: {stats['primary_bias']}
        
        Relevant trade history:
        {format_trades_for_context(similar_trades)}
        
        Long-term behavioral memories:
        {memories}
        
        Answer the trader's question in a concise, specific, data-driven way.
        Reference actual numbers from their history. Max 3 sentences.
    """
    
    client = anthropic.Anthropic()
    
    # Stream the response for real-time chat feel
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=context,
        messages=[{"role": "user", "content": message}]
    ) as stream:
        # Use FastAPI StreamingResponse
        async def event_stream():
            for text in stream.text_stream:
                yield f"data: {json.dumps({'token': text})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(event_stream(), media_type="text/event-stream")
```

---

## Phase 7 — Broker Integrations

```python
# app/services/brokers/ibkr.py

import ib_insync  # pip install ib_insync

class IBKRBroker:
    async def fetch_trades(self, account_id: str, since: datetime) -> List[dict]:
        ib = ib_insync.IB()
        await ib.connectAsync('127.0.0.1', 7497, clientId=1)
        
        trades = await ib.reqExecutionsAsync()
        return [self.normalize_trade(t) for t in trades if t.time >= since]
    
    def normalize_trade(self, raw) -> dict:
        """Maps IBKR trade format → CognitionTrade trade format."""
        return {
            "symbol": raw.contract.symbol,
            "direction": "long" if raw.execution.side == "BOT" else "short",
            "entry_price": raw.execution.price,
            "quantity": raw.execution.shares,
            "entered_at": raw.time,
        }
```

```python
# app/services/brokers/schwab.py — uses OAuth2 + REST API

class SchwabBroker:
    BASE_URL = "https://api.schwabapi.com/trader/v1"
    
    async def fetch_trades(self, access_token: str, since: datetime) -> List[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/accounts/{{accountId}}/orders",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"fromEnteredTime": since.isoformat(), "status": "FILLED"}
            )
            orders = resp.json()
            return [self.normalize_trade(o) for o in orders]
```

---

## Phase 8 — Scheduled Tasks (Celery + Redis)

```python
# app/tasks.py

from celery import Celery
from celery.schedules import crontab

celery = Celery("cognitiontrade", broker=os.getenv("REDIS_URL"))

@celery.task
def sync_broker_trades(user_id: str, broker: str):
    """Called after trade entry or on schedule. Pulls new trades from broker."""
    # ... fetch + upsert trades

@celery.task
def generate_weekly_report(user_id: str):
    """Runs every Sunday 6pm. Generates narrative weekly report via Registrar agent."""
    # ... run registrar agent with weekly scope

@celery.task
def send_premarket_briefing(user_id: str):
    """Runs every trading day at 8:15 AM ET. Fetches news + VIX for user's watchlist."""
    # ... run researcher agent + push notification

# Scheduler (beat)
celery.conf.beat_schedule = {
    "weekly-reports": {
        "task": "app.tasks.generate_weekly_report",
        "schedule": crontab(hour=18, minute=0, day_of_week="sunday"),
    },
    "premarket-briefing": {
        "task": "app.tasks.send_premarket_briefing",
        "schedule": crontab(hour=13, minute=15),  # 8:15 AM ET = 13:15 UTC
    },
}
```

---

## Phase 9 — API Endpoints Summary

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
GET    /api/trades/stats              → aggregate stats (win rate, expectancy, etc.)

POST   /api/agents/chat               → streaming AI Coach Q&A
POST   /api/agents/analyze            → run full agent pipeline on a trade
GET    /api/agents/alerts             → unread tilt/gap/limit alerts

GET    /api/brokers                   → list connected brokers
POST   /api/brokers/connect           → connect a broker (starts OAuth)
DELETE /api/brokers/:id               → disconnect broker
POST   /api/brokers/:id/sync          → manual sync

GET    /api/settings                  → get user settings
PUT    /api/settings                  → update settings
POST   /api/settings/upload-chart     → upload chart to S3, returns URL

GET    /api/reports/weekly            → latest weekly report
GET    /api/reports/monthly           → monthly report
```

---

## Phase 10 — Deployment Checklist

```bash
# 1. Set environment variables
cp .env.example .env
# Fill in: DATABASE_URL, REDIS_URL, ANTHROPIC_API_KEY,
#          JWT_SECRET, AWS_ACCESS_KEY, BENZINGA_API_KEY, etc.

# 2. Run database migrations
alembic upgrade head

# 3. Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start Celery worker + beat
celery -A app.tasks worker --loglevel=info
celery -A app.tasks beat   --loglevel=info

# 5. Deploy frontend (static)
# Update js/app.js API base URL from '' to 'https://api.yourdomain.com'
# Deploy pages/ folder to Vercel or Netlify

# 6. LangSmith (optional but recommended)
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_langsmith_key
```

---

## Key Dependencies

```txt
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
alembic==1.13.0
psycopg2-binary==2.9.9
pgvector==0.3.2
redis==5.0.8
celery==5.4.0

anthropic==0.34.0
langchain==0.3.0
langgraph==0.2.0
langsmith==0.1.0
mem0ai==0.1.0
openai==1.50.0          # for chart vision fallback

python-jose[cryptography]==3.3.0  # JWT
bcrypt==4.2.0
python-multipart==0.0.12          # file uploads
httpx==0.27.0
boto3==1.35.0                     # S3 chart uploads
ib_insync==0.9.86                 # IBKR broker
```

---

## Security Notes

- **Never** store raw API keys in the DB — encrypt broker credentials with AES-256 before storage
- Use **Row-Level Security (RLS)** in Supabase so users can only access their own rows
- Rate-limit the `/api/agents/chat` endpoint — LLM calls are expensive
- Validate all file uploads (chart images) for type and size before passing to vision model
- Use **HTTPS only** in production — set `secure=True` on all cookies

---

*Built with FastAPI · LangGraph · PostgreSQL/TimescaleDB · pgvector · Claude Sonnet 4.6*
