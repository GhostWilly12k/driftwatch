"""
Tests for app/schemas.py — User Pydantic schemas (T-013).

Run from backend/:
    pytest tests/test_user_schemas.py
"""
import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas import UserCreate, UserRead


def test_user_create_valid():
    user = UserCreate(email="trader@example.com", password="supersecret1", name="Willy")
    assert user.email == "trader@example.com"
    assert user.name == "Willy"


def test_user_create_defaults_name_to_none():
    user = UserCreate(email="trader@example.com", password="supersecret1")
    assert user.name is None


def test_user_create_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="supersecret1")


def test_user_create_rejects_short_password():
    with pytest.raises(ValidationError):
        UserCreate(email="trader@example.com", password="short")


def test_user_read_from_attributes():
    """UserRead must be constructible from an ORM-like object (from_attributes)
    and must never expose password_hash, since it isn't a field on the schema."""

    class FakeORMUser:
        id = uuid.uuid4()
        email = "trader@example.com"
        name = "Willy"
        plan = "starter"
        avatar_url = None
        created_at = datetime.now(UTC)
        password_hash = "should-never-appear"

    read_model = UserRead.model_validate(FakeORMUser())
    assert read_model.email == "trader@example.com"
    assert "password_hash" not in read_model.model_dump()