import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from src.lib.config import Settings

_hasher = PasswordHash.recommended()
_DUMMY_HASH = _hasher.hash("not-a-real-password")
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def verify_password_dummy(password: str) -> None:
    _hasher.verify(password, _DUMMY_HASH)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def encode_access_token(
    *,
    settings: Settings,
    user_id: int,
    email: str,
    role: str,
) -> tuple[str, int]:
    expires_in = settings.access_token_minutes * 60
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)
    return token, expires_in


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    decoded: dict[str, Any] = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[_ALGORITHM],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        options={"require": ["exp", "iss", "aud", "sub"]},
    )
    return decoded
