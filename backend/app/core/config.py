"""
Application settings, loaded from environment variables (.env).
Keep this the single source of truth for config — routers and
services should import `settings` from here rather than calling
os.getenv() directly.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "CognitionTrade API"
    ENVIRONMENT: str = "development"  # development | production
    DEBUG: bool = True

    # Database (Supabase pooler connection string)
    DATABASE_URL: str

    # Redis (Upstash)
    REDIS_URL: str

    # Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days, per T-015

    # Anthropic (used from Sprint 4 onward — safe to leave unset until then)
    ANTHROPIC_API_KEY: str | None = None

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()