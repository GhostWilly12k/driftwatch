"""
Password hashing and JWT helpers.

Kept separate from the auth router so the same functions can be reused
by POST /api/auth/login (T-015), POST /api/auth/logout (T-016), and
later the get_current_user dependency (T-018) without duplicating
hashing/token logic.
"""
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. Never store plain_password itself."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash. Used by T-015 login."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """
    Issue a signed JWT for a successful login (T-015).

    `subject` is the user's id (as a string) and becomes the token's `sub`
    claim — this is what get_current_user (T-018) will look up on
    subsequent requests. Defaults to the 30-day expiry configured in
    settings.JWT_EXPIRE_MINUTES.
    """
    expire_minutes = expires_minutes if expires_minutes is not None else settings.JWT_EXPIRE_MINUTES
    now = datetime.now(UTC)
    to_encode = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    # python-jose ships no type stubs, so jwt.encode() resolves to Any — cast
    # explicitly since this function's contract (and callers) depend on str.
    token: str = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT, returning its claims (T-016, T-018).

    Used by logout to read the `exp` claim (so the blocklist TTL matches
    the token's remaining lifetime) and will be reused by get_current_user
    (T-018) to identify the requesting user. jose.jwt.decode checks the
    signature and expiry automatically — an invalid signature or an
    expired token both raise JWTError, which is normalised here into a
    401 UnauthorizedError so callers don't need to know about jose.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token.", code="INVALID_TOKEN") from exc
    return payload