"""
Tests for the get_current_user dependency (T-018).

Exercised indirectly through GET /api/auth/me (T-017), since that's the
first real route wired to this dependency — testing through a route
rather than calling get_current_user directly also verifies FastAPI's
dependency wiring (Depends(bearer_scheme), Depends(get_db)) end to end.

Full integration tests against a real test database/Redis land in T-022.

Run from backend/:
    pytest tests/test_auth_me.py
"""
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.core.security import create_access_token
from app.main import app
from app.models import User

VALID_USER_ID = uuid.uuid4()


def _make_user(user_id: uuid.UUID = VALID_USER_ID) -> User:
    return User(
        id=user_id,
        email="trader@example.com",
        password_hash="not-a-real-hash",
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


@pytest.fixture
def mock_not_blocklisted(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Default: no token is blocklisted, unless a test overrides this."""
    mock = MagicMock(return_value=False)
    monkeypatch.setattr("app.core.deps.is_token_blocklisted", mock)
    return mock


def test_valid_token_resolves_user(
    client: TestClient, mock_db: MagicMock, mock_not_blocklisted: MagicMock
) -> None:
    user = _make_user()
    mock_db.execute.return_value.scalar_one_or_none.return_value = user
    token = create_access_token(subject=str(user.id))

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == user.email
    mock_not_blocklisted.assert_called_once_with(token)


def test_missing_authorization_header_is_rejected(
    client: TestClient, mock_db: MagicMock, mock_not_blocklisted: MagicMock
) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    mock_not_blocklisted.assert_not_called()


def test_malformed_token_is_rejected(
    client: TestClient, mock_db: MagicMock, mock_not_blocklisted: MagicMock
) -> None:
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
    mock_not_blocklisted.assert_not_called()


def test_expired_token_is_rejected(
    client: TestClient, mock_db: MagicMock, mock_not_blocklisted: MagicMock
) -> None:
    expired_token = create_access_token(subject=str(VALID_USER_ID), expires_minutes=-1)

    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
    mock_not_blocklisted.assert_not_called()


def test_blocklisted_token_is_rejected(
    client: TestClient, mock_db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.core.deps.is_token_blocklisted", MagicMock(return_value=True))
    token = create_access_token(subject=str(VALID_USER_ID))

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "TOKEN_REVOKED"
    # A revoked token should never reach the DB lookup.
    mock_db.execute.assert_not_called()


def test_token_for_deleted_user_is_rejected(
    client: TestClient, mock_db: MagicMock, mock_not_blocklisted: MagicMock
) -> None:
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    token = create_access_token(subject=str(VALID_USER_ID))

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"


def test_token_with_non_uuid_subject_is_rejected(
    client: TestClient, mock_db: MagicMock, mock_not_blocklisted: MagicMock
) -> None:
    token = create_access_token(subject="not-a-uuid")

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_wrong_scheme_is_rejected(
    client: TestClient, mock_db: MagicMock, mock_not_blocklisted: MagicMock
) -> None:
    token = create_access_token(subject=str(VALID_USER_ID))

    response = client.get("/api/auth/me", headers={"Authorization": f"Basic {token}"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    mock_not_blocklisted.assert_not_called()