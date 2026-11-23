from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Response
from sqlmodel import Session, select

from src.lib.config import Settings
from src.lib.security import (
    encode_access_token,
    hash_token,
    new_refresh_token,
    verify_password,
    verify_password_dummy,
)
from src.models.identity.refresh_token import RefreshToken
from src.models.identity.user import User
from src.schemas.identity.session import AccessTokenResponse

_LOGIN_DETAIL = "Email or password is incorrect."
_REFRESH_COOKIE = "refresh_token"
_REFRESH_PATH = "/v1/auth"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def authenticate(session: Session, email: str, password: str) -> User:
    user = session.exec(select(User).where(User.email == normalize_email(email))).first()
    if user is None:
        verify_password_dummy(password)
        raise HTTPException(status_code=401, detail=_LOGIN_DETAIL)
    if user.invite_token_hash is not None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail=_LOGIN_DETAIL)
    return user


def issue_tokens(
    session: Session,
    user: User,
    settings: Settings,
) -> tuple[AccessTokenResponse, str]:
    if user.id is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    access, expires_in = encode_access_token(
        settings=settings,
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )
    raw = new_refresh_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    session.commit()
    return (
        AccessTokenResponse(access_token=access, expires_in=expires_in),
        raw,
    )


def rotate_refresh(
    session: Session,
    raw_token: str | None,
    settings: Settings,
) -> tuple[AccessTokenResponse, str]:
    if not raw_token:
        raise HTTPException(status_code=401, detail="Authentication required.")
    stored = session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token))
    ).first()
    now = datetime.now(UTC)
    if stored is None or stored.revoked_at is not None or stored.expires_at <= now:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user = session.get(User, stored.user_id)
    if user is None or user.id is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    stored.revoked_at = now
    session.add(stored)
    session.commit()
    return issue_tokens(session, user, settings)


def revoke_refresh(session: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    stored = session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token))
    ).first()
    if stored is None or stored.revoked_at is not None:
        return
    stored.revoked_at = datetime.now(UTC)
    session.add(stored)
    session.commit()


def set_refresh_cookie(response: Response, raw: str, settings: Settings) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=raw,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=_REFRESH_PATH,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
    )
