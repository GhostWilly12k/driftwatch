"""
CognitionTrade API — FastAPI application entrypoint.

Run locally:
    uvicorn app.main:app --reload

Swagger UI: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers import agents, auth, trades

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# --- CORS ---------------------------------------------------------------
# Origins come from CORS_ORIGINS in .env — add the Vercel frontend URL
# there once T-010 is done, and the Railway prod URL when T-071 lands.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Error handlers -------------------------------------------------------
register_exception_handlers(app)

# --- Routers --------------------------------------------------------------
app.include_router(auth.router)
app.include_router(trades.router)
app.include_router(agents.router)


@app.get("/health", tags=["meta"])
async def health_check():
    """Basic liveness check — useful for Railway's health check config (T-070)."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}