"""
Tests for POST /api/auth/register (T-014).

The DB session is swapped out via FastAPI's dependency override with a
MagicMock, so these tests exercise the endpoint's logic (duplicate-email
check, bcrypt hashing, response shape) without needing a live Postgres
connection. Full integration tests against a real test database land in
T-022 alongside login/logout/me.

Run from backend/:
    pytest tests/test_auth_register.py
"""
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import MagicMock

import bcrypt
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app


def _fake_refresh(user: object) -> None:
    """Simulate what a real DB round-trip populates on db.refresh(user)."""
    if getattr(user, "id", None) is None:
        user.id = uuid.uuid4()  # type: ignore[attr-defined]
    if getattr(user, "created_at", None) is None:
        user.created_at = datetime.now(UTC)  # type: ignore[attr-defined]
    if getattr(user, "plan", None) is None:
        user.plan = "starter"  # type: ignore[attr-defined]


@pytest.fixture
def mock_db() -> MagicMock:
    db = MagicMock()
    db.refresh.side_effect = _fake_refresh
    return db


@pytest.fixture
def client(mock_db: MagicMock) -> Generator[TestClient, None, None]:
    def _get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_register_success(client: TestClient, mock_db: MagicMock) -> None:
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    response = client.post(
        "/api/auth/register",
        json={"email": "trader@example.com", "password": "supersecret1", "name": "Willy"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["email"] == "trader@example.com"
    assert body["name"] == "Willy"
    assert body["plan"] == "starter"
    assert "password" not in body
    assert "password_hash" not in body

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_register_hashes_password_with_bcrypt(client: TestClient, mock_db: MagicMock) -> None:
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    client.post(
        "/api/auth/register",
        json={"email": "hash-check@example.com", "password": "supersecret1"},
    )

    created_user = mock_db.add.call_args[0][0]
    assert created_user.password_hash != "supersecret1"
    assert created_user.password_hash.startswith(("$2a$", "$2b$"))
    assert bcrypt.checkpw(b"supersecret1", created_user.password_hash.encode("utf-8"))


def test_register_rejects_duplicate_email(client: TestClient, mock_db: MagicMock) -> None:
    mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock()

    response = client.post(
        "/api/auth/register",
        json={"email": "existing@example.com", "password": "supersecret1"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    body = response.json()
    assert body["error"]["code"] == "EMAIL_TAKEN"
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_register_rejects_short_password(client: TestClient, mock_db: MagicMock) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "trader@example.com", "password": "short"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    mock_db.add.assert_not_called()

 
def test_register_rejects_password_over_bcrypt_limit(client: TestClient, mock_db: MagicMock) -> None:
    """bcrypt silently truncates passwords over 72 bytes; two different
    passwords sharing the same first 72 bytes would otherwise both
    authenticate. Reject rather than silently truncate (T-014 follow-up)."""
    response = client.post(
        "/api/auth/register",
        json={"email": "trader@example.com", "password": "a" * 100},
    )
 
    assert response.status_code == 422
    mock_db.add.assert_not_called()
 
 
def test_register_accepts_password_at_bcrypt_limit(client: TestClient, mock_db: MagicMock) -> None:
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
 
    response = client.post(
        "/api/auth/register",
        json={"email": "at-limit@example.com", "password": "a" * 72},
    )
 
    assert response.status_code == 201


def test_register_rejects_invalid_email(client: TestClient, mock_db: MagicMock) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "supersecret1"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    mock_db.add.assert_not_called()


def test_register_defaults_name_to_none(client: TestClient, mock_db: MagicMock) -> None:
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    response = client.post(
        "/api/auth/register",
        json={"email": "no-name@example.com", "password": "supersecret1"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] is None