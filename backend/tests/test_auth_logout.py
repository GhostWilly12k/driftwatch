"""
Tests for POST /api/auth/logout (T-016).

Logout doesn't touch the database, so unlike test_auth_login.py there's no
get_db override here — instead `app.core.redis_client.blocklist_token` is
patched (via the name imported into app.routers.auth) so these tests verify
the endpoint's logic — token validation, TTL calculation, blocklist call —
without needing a live Redis instance. Full integration tests against a
real test database/Redis land in T-022.

Run from backend/:
    pytest tests/test_auth_logout.py
"""
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app

VALID_SUBJECT = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_blocklist_token(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch the blocklist_token call site in the auth router."""
    mock = MagicMock()
    monkeypatch.setattr("app.routers.auth.blocklist_token", mock)
    return mock


def test_logout_success_blocklists_token(client: TestClient, mock_blocklist_token: MagicMock) -> None:
    token = create_access_token(subject=VALID_SUBJECT)

    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Logged out successfully."}

    mock_blocklist_token.assert_called_once()
    called_token, called_ttl = mock_blocklist_token.call_args[0]
    assert called_token == token
    # TTL should be ~30 days (JWT_EXPIRE_MINUTES), allow a little slack for
    # the time elapsed between token creation and this assertion.
    assert 0 < called_ttl <= 60 * 60 * 24 * 30


def test_logout_rejects_missing_authorization_header(
    client: TestClient, mock_blocklist_token: MagicMock
) -> None:
    response = client.post("/api/auth/logout")

    # fastapi's HTTPBearer (auto_error=True) raises 401 "Not authenticated"
    # for a missing/malformed header in this version — not the 403 used by
    # older FastAPI releases.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    mock_blocklist_token.assert_not_called()


def test_logout_rejects_malformed_token(client: TestClient, mock_blocklist_token: MagicMock) -> None:
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
    mock_blocklist_token.assert_not_called()


def test_logout_rejects_expired_token(client: TestClient, mock_blocklist_token: MagicMock) -> None:
    expired_token = create_access_token(subject=VALID_SUBJECT, expires_minutes=-1)

    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
    mock_blocklist_token.assert_not_called()


def test_logout_rejects_wrong_scheme(client: TestClient, mock_blocklist_token: MagicMock) -> None:
    token = create_access_token(subject=VALID_SUBJECT)

    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Basic {token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    mock_blocklist_token.assert_not_called()