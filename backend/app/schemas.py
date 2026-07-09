"""
Pydantic schemas — request/response models, kept separate from the
SQLAlchemy models in models.py.

Naming convention used throughout this file and future schema additions:
    <Entity>Create  — inbound payload for creating a resource
    <Entity>Update   — inbound payload for partial updates
    <Entity>Read     — outbound representation returned to the client
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# bcrypt silently truncates anything past 72 bytes, which means two different
# passwords that share the same first 72 bytes would hash identically and
# both would authenticate. Capping length here (rather than truncating
# server-side) makes that failure mode impossible instead of just hidden.
BCRYPT_MAX_BYTES = 72


class UserCreate(BaseModel):
    """Payload for POST /api/auth/register (T-014)."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=BCRYPT_MAX_BYTES)
    name: str | None = None

    @field_validator("password")
    @classmethod
    def password_must_fit_bcrypt(cls, value: str) -> str:
        # max_length above already caps character count, but multi-byte
        # UTF-8 characters (emoji, accents, etc.) can exceed 72 bytes with
        # fewer than 72 characters, so check the actual encoded length too.
        if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError(
                f"Password must be at most {BCRYPT_MAX_BYTES} bytes when UTF-8 encoded."
            )
        return value


class UserRead(BaseModel):
    """Public representation of a user — never includes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str | None = None
    plan: str
    avatar_url: str | None = None
    created_at: datetime


class LoginRequest(BaseModel):
    """Payload for POST /api/auth/login (T-015)."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Response for POST /api/auth/login (T-015).

    expires_in is seconds-until-expiry, so the client can schedule a
    re-login/refresh prompt without needing to decode the JWT itself.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MessageResponse(BaseModel):
    """Generic status message — used by POST /api/auth/logout (T-016)."""

    message: str