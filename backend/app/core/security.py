"""Security utilities: JWT, password hashing, CSRF tokens."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import argon2
import jwt

from app.core.config import get_settings

settings = get_settings()
_ph = argon2.PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1)

# ── Password hashing (Argon2id) ──


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except argon2.exceptions.VerifyMismatchError:
        return False


def check_password_strength(password: str) -> Optional[str]:
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one digit."
    return None


# ── JWT ──


def create_access_token(sub: str, extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": sub,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(sub: str) -> tuple[str, str, datetime]:
    """Return (raw_token, hashed_token, expires_at)."""
    raw = secrets.token_urlsafe(48)
    hashed = hash_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return raw, hashed, expires_at


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


# ── Generic token hashing (for email verification, etc.) ──


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_token() -> tuple[str, str]:
    """Return (raw_token, hashed_token)."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


# ── CSRF ──


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)

