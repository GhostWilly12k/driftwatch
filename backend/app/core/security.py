"""
Password hashing helpers built on bcrypt.

Kept separate from the auth router so the same functions can be reused
by POST /api/auth/login (T-015) without duplicating hashing logic.
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. Never store plain_password itself."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash. Used by T-015 login."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))