"""
Shared FastAPI dependencies for authenticated routes.

get_current_user (T-018) is the single place that turns a raw
"Authorization: Bearer <token>" header into an authenticated User row.
It ties together three pieces built in earlier Sprint 1 tasks:

    1. decode_access_token (T-015/T-016) — validates the JWT's signature
       and expiry, raising 401 INVALID_TOKEN if either check fails.
    2. is_token_blocklisted (T-016) — rejects a token that was already
       logged out, even if it hasn't technically expired yet.
    3. The `sub` claim (the user's id, set by create_access_token in
       T-015) — used to look the user up in the database.

Any route that needs "the current logged-in user" should depend on
CurrentUser (the Annotated alias below) rather than re-implementing this
logic. GET /api/auth/me (T-017) is the first consumer; T-019/T-021's
frontend auth guard and future protected trade/agent endpoints rely on
this same dependency being in place.
"""
import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import UnauthorizedError
from app.core.redis_client import is_token_blocklisted
from app.core.security import decode_access_token
from app.models import User

# Shared across auth.py (logout, me) and any other router that needs the
# raw bearer credentials rather than a resolved User.
bearer_scheme = HTTPBearer(auto_error=True)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    """
    Resolve the requesting user from a bearer JWT (US-004, T-018).

    Raises 401 UNAUTHORIZED (via UnauthorizedError) if the token is
    malformed/expired, has been blocklisted by logout (T-016), its `sub`
    claim isn't a valid user id, or it no longer maps to a user in the
    database. The caller doesn't need to distinguish between these cases —
    only that the request isn't authenticated — but distinct error codes
    are kept for debugging/logging.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if is_token_blocklisted(token):
        raise UnauthorizedError("Token has been revoked.", code="TOKEN_REVOKED")

    raw_subject = payload.get("sub")
    if raw_subject is None:
        raise UnauthorizedError("Token is missing a subject claim.", code="INVALID_TOKEN")

    try:
        user_id = uuid.UUID(raw_subject)
    except (ValueError, AttributeError, TypeError) as exc:
        raise UnauthorizedError("Token subject is not a valid user id.", code="INVALID_TOKEN") from exc

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User account no longer exists.", code="USER_NOT_FOUND")

    return user


# Reusable dependency type — protected routes should prefer this over
# re-declaring Depends(get_current_user) everywhere.
CurrentUser = Annotated[User, Depends(get_current_user)]