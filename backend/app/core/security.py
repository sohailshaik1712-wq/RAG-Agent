"""
app/core/security.py
──────────────────────
JWT creation/verification and bcrypt password hashing.
Uses bcrypt directly — passlib is unmaintained and broken with bcrypt >= 4.
"""
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


# ── Passwords ─────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT ───────────────────────────────────────────────────────

TokenType = Literal["access", "refresh"]


def create_token(user_id: str, token_type: TokenType) -> str:
    """
    Creates a signed JWT.
    Access tokens expire in minutes, refresh tokens in days.
    """
    if token_type == "access":
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )

    payload = {
        "sub":  user_id,
        "type": token_type,
        "exp":  expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str, expected_type: TokenType) -> str:
    """
    Decodes and validates a JWT. Returns the user_id (sub claim).
    Raises ValueError if the token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub", "")
        token_type: str = payload.get("type", "")

        if not user_id:
            raise ValueError("Missing subject in token")
        if token_type != expected_type:
            raise ValueError(f"Expected {expected_type} token, got {token_type}")

        return user_id
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")
