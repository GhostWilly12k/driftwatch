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

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Payload for POST /api/auth/register (T-014)."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = None


class UserRead(BaseModel):
    """Public representation of a user — never includes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str | None = None
    plan: str
    avatar_url: str | None = None
    created_at: datetime