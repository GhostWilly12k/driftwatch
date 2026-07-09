"""
Tests for POST /api/auth/login (T-015).

Mirrors the mocking pattern from test_auth_register.py: the DB session is
swapped out via FastAPI's dependency override with a MagicMock, so these
tests exercise the endpoint's logic (credential verification, JWT issuance,
generic error on failure) without needing a live Postgres connection.
Full integration tests against a real test database land in T-022.

Run from backend/:
    pytest tests/test_auth_login.py
"""
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import MagicMock

import bcrypt
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.db import get_db
from app.main import app
from app.models import User

PLAIN_PASSWORD = "supersecret1"


def _make_user(email: str = "trader@example.com", password: str = PLAIN_PASSWORD) -> User:
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return User(
        id=uuid.uuid4(),
        email=email,
        password_hash=password_hash,
        name="Willy",
        plan="starter",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(mock_db: MagicMock) -> Generator[TestClient, None, None]:
    def _get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_login_success_returns_jwt(client: TestClient, mock_db: MagicMock) -> None:
    user = _make_user()
    mock_db.execute.return_value.scalar_one_or_none.return_value = user

    response = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": PLAIN_PASSWORD},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.JWT_EXPIRE_MINUTES * 60
    assert "access_token" in body

    decoded = jwt.decode(
        body["access_token"],
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    assert decoded["sub"] == str(user.id)


def test_login_rejects_wrong_password(client: TestClient, mock_db: MagicMock) -> None:
    user = _make_user()
    mock_db.execute.return_value.scalar_one_or_none.return_value = user

    response = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "wrong-password"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_rejects_unknown_email(client: TestClient, mock_db: MagicMock) -> None:
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": PLAIN_PASSWORD},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email_and_wrong_password_return_identical_error(
    client: TestClient, mock_db: MagicMock
) -> None:
    """Prevents user enumeration: a bad email and a bad password must be
    indistinguishable to the caller — same status code, same body."""
    user = _make_user()

    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    unknown_email_response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": PLAIN_PASSWORD},
    )

    mock_db.execute.return_value.scalar_one_or_none.return_value = user
    wrong_password_response = client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "wrong-password"},
    )

    assert unknown_email_response.status_code == wrong_password_response.status_code
    assert unknown_email_response.json() == wrong_password_response.json()


def test_login_rejects_missing_password(client: TestClient, mock_db: MagicMock) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "trader@example.com"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_login_rejects_invalid_email_format(client: TestClient, mock_db: MagicMock) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "not-an-email", "password": PLAIN_PASSWORD},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT