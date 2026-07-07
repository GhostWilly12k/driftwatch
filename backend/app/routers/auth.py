from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/ping")
async def ping():
    """Stub endpoint to confirm the router is wired up. Replace with real
    auth endpoints in Sprint 1: register, login, logout, me."""
    return {"status": "auth router ok"}