from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.models import User
from app.schemas import UserCreate, UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])


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