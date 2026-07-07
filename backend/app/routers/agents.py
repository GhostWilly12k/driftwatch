from fastapi import APIRouter

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/ping")
async def ping():
    """Stub endpoint to confirm the router is wired up. Replace with real
    Journal Analyst (Sprint 4) and Strategy Coach (Sprint 5) endpoints,
    including GET /api/agents/alerts (T-066)."""
    return {"status": "agents router ok"}