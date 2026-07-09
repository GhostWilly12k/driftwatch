from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.redis_client import blocklist_token
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas import LoginRequest, MessageResponse, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])

# HTTPBearer extracts and validates the "Authorization: Bearer <token>"
# header for us; auto_error=True means a missing/malformed header short-
# circuits with a 401 "Not authenticated" before the endpoint body runs.
bearer_scheme = HTTPBearer(auto_error=True)


@router.get("/ping")
async def ping() -> dict[str, str]:
    """Stub endpoint to confirm the router is wired up."""
    return {"status": "auth router ok"}

# Reusable dependency type
DbSession = Annotated[Session, Depends(get_db)] 

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession) -> User:
    """
    Create a new user account (US-001, T-014).

    - Rejects registration if the email is already taken (409 Conflict).
    - Hashes the password with bcrypt before it ever touches the database —
      the plaintext password is never stored or logged.
    """
    existing = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if existing is not None:
        raise ConflictError(
            "An account with this email already exists.",
            code="EMAIL_TAKEN",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    """
    Authenticate a user and issue a JWT (US-002, T-015).

    Returns a 30-day access token (JWT_EXPIRE_MINUTES) on success. On
    failure — whether the email doesn't exist or the password is wrong —
    the response is identical (401, INVALID_CREDENTIALS) so a caller can't
    use this endpoint to enumerate registered email addresses.
    """
    user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if user is None or not verify_password(payload.password, cast(str, user.password_hash)):
        raise UnauthorizedError(
            "Invalid email or password.",
            code="INVALID_CREDENTIALS",
        )

    access_token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> MessageResponse:
    """
    Invalidate the caller's JWT server-side (US-003, T-016).

    JWTs are stateless by design, so "logging out" means adding this
    specific token to a Redis blocklist rather than deleting anything.
    The blocklist entry's TTL is set to the token's own remaining
    lifetime (exp - now), so it self-expires exactly when the token
    would have anyway — no cleanup job needed.

    A malformed, unsigned, or already-expired token is rejected with 401
    before we ever touch Redis. get_current_user (T-018) is what will
    consult this blocklist on every subsequent authenticated request.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    exp = payload.get("exp")
    if exp is None:
        raise UnauthorizedError("Token is missing an expiry claim.", code="INVALID_TOKEN")

    now_ts = int(datetime.now(UTC).timestamp())
    ttl_seconds = int(exp) - now_ts

    blocklist_token(token, ttl_seconds)

    return MessageResponse(message="Logged out successfully.")