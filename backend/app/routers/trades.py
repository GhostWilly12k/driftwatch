from fastapi import APIRouter

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("/ping")
async def ping():
    """Stub endpoint to confirm the router is wired up. Replace with real
    trade CRUD + calendar + stats endpoints in Sprint 2."""
    return {"status": "trades router ok"}