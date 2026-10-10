"""Password hashing and JWT session helpers."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
JWT_COOKIE_NAME = os.getenv("JWT_COOKIE_NAME", "access_token")

if os.getenv("APP_ENV", "development").lower() == "production" and JWT_SECRET_KEY == "change-me":
    raise RuntimeError("JWT_SECRET_KEY must be configured outside development")

password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class InvalidTokenError(ValueError):
    """Raised when an access token is invalid, expired, or has the wrong type."""


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user_id: str) -> tuple[str, int]:
    expires_in = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM), expires_in


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise InvalidTokenError("Invalid or expired session") from exc
    user_id = payload.get("sub")
    if payload.get("type") != "access" or not isinstance(user_id, str) or not user_id:
        raise InvalidTokenError("Invalid access token")
    return user_id
